from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from PIL import Image

from tools.render_contract import load_layout_tokens
from tools.rtd import portal as rtd_portal
from tools.rtd.design_assets import ASSET_ROOTS, REGISTRIES, withdrawn_hashes
from tools.rtd.design_print import cmyk_screen, value_text
from tools.rtd.design_system import (
    DesignSystemError, contrast_ratio, design_page_context, design_system_context, inline,
    preview_document, template_context, write_design_system,
)
from tools.rtd.design_system_css import class_names, declared, live_stylesheet_text, parse_css
from tools.utils.path_utils import Paths, repo_root
from tools.web.stylesheets import copy_web_stylesheet


class CssReaderTests(unittest.TestCase):
    CSS = """
    /* a comment { with braces } */
    :root { --hb-paper: #FFFFFF; --hb-font-family: "A", B; }
    #furo-main-content h1, #furo-main-content .hb-h1-pill { font-size: 1rem !important; line-height: 1.1; }
    #furo-main-content :is(.hb-a, .hb-b)::before { background: #00ae58; }
    @media (max-width: 760px) { #furo-main-content h1 { font-size: 0.9rem; } }
    @font-face { font-family: X; src: url("x;y.woff2"); }
    #furo-main-content h1 { font-size: 1.2rem; }
    """

    def test_reads_exact_selectors_in_cascade_order(self):
        rules = parse_css(self.CSS)
        self.assertEqual(declared(rules, "#furo-main-content h1", "font-size"), "1.2rem")
        self.assertEqual(declared(rules, "#furo-main-content .hb-h1-pill", "font-size"), "1rem")
        self.assertEqual(declared(rules, "#furo-main-content h1", "font-size", context="@media (max-width: 760px)"),
                         "0.9rem")
        self.assertEqual(declared(rules, ":root", "--hb-font-family"), '"A", B')
        self.assertEqual(declared(rules, "#furo-main-content :is(.hb-a, .hb-b)::before", "background"), "#00ae58")
        self.assertIsNone(declared(rules, "#furo-main-content h2", "font-size"))
        self.assertTrue({"hb-h1-pill", "hb-a", "hb-b"} <= class_names(rules))
        self.assertFalse(any(rule.selectors == ("@font-face",) for rule in rules))

    def test_live_text_is_the_published_stylesheet(self):
        with TemporaryDirectory() as temp:
            published = copy_web_stylesheet(Path(temp))
            self.assertEqual(live_stylesheet_text(), published.read_text(encoding="utf-8"))


class DesignSystemContextTests(unittest.TestCase):
    def setUp(self):
        self.context = design_system_context(rtd_portal.ASSETS)

    def test_every_value_comes_from_the_live_stylesheet(self):
        rules = parse_css(live_stylesheet_text())
        self.assertGreaterEqual(len(self.context["colors"]), 10)
        for color in self.context["colors"]:
            with self.subTest(color=color["name"]):
                self.assertRegex(color["value"], r"^#[0-9a-f]{3,8}$")
                self.assertIn(color["value"], (declared(rules, color["selector"], color["token"]) or "").lower())
        for style in self.context["type_styles"]:
            with self.subTest(style=style["name"]):
                self.assertTrue(style["desktop"]["font-size"] or style["desktop"]["font-weight"])
                self.assertEqual(style["desktop"]["font-size"], declared(rules, style["selector"], "font-size"))
        self.assertEqual(self.context["paper"], "#ffffff")
        self.assertEqual(self.context["font_family"], declared(rules, ":root", "--hb-font-family"))

    def test_components_have_previews_from_repository_files_only(self):
        items = [item for group in self.context["component_groups"] for item in group["items"]]
        self.assertEqual(self.context["component_count"], len(items))
        self.assertGreaterEqual(len(items), 25)
        preview_dir = rtd_portal.ASSETS / "design_system" / "previews"
        self.assertEqual({item["id"] for item in items}, {path.stem for path in preview_dir.glob("*.html")})
        for item in items:
            with self.subTest(component=item["id"]):
                document = preview_document(item)
                self.assertIn('<main id="furo-main-content"', document)
                self.assertNotRegex(document, r'(?:src|href)="(?:https?:|//|data:|asset:|slot:)')
                self.assertNotIn("Jackery", document)
                self.assertTrue(item["notes"] or item["summary"])
        for source in self.context["assets"].values():
            self.assertTrue(source.is_file(), source)

    def test_template_context_carries_no_paths_or_stylesheet(self):
        page = template_context(self.context)
        self.assertNotIn("assets", page)
        self.assertNotIn("stylesheet", page)
        self.assertEqual(page["stylesheet_sha256"], self.context["stylesheet"]["sha256"])
        self.assertFalse({"tokens_css", "preview"} & set(page["print"]))
        self.assertFalse(any(isinstance(value, Path) for group in page["asset_library"]["groups"]
                             for item in group["items"] for value in item.values()))

    def test_write_places_previews_stylesheet_and_art_beside_the_page(self):
        with TemporaryDirectory() as temp:
            target = write_design_system(Path(temp), rtd_portal.ASSETS, self.context)
            self.assertEqual((target / "web_manual.css").read_text(encoding="utf-8"), live_stylesheet_text())
            self.assertTrue((target / "preview.css").is_file())
            for page in sorted((target / "previews").glob("*.html")) + [target / "print" / "page.html"]:
                for ref in re.findall(r'(?:src|href)="([^"#]+)"', page.read_text(encoding="utf-8")):
                    resolved = (page.parent / ref).resolve()
                    inside = resolved.is_relative_to((Path(temp) / "workspace").resolve())
                    portal_static = ref.startswith("../../../_static/")
                    self.assertTrue(portal_static or (inside and resolved.is_file()), (page.name, ref))
            for group in self.context["asset_library"]["groups"]:
                for item in group["items"]:
                    self.assertTrue((target / "assets" / item["ref"]).is_file(), item["ref"])
            self.assertEqual((target / "print" / "tokens.css").read_text(encoding="utf-8"),
                             self.context["print"]["tokens_css"])


class DesignSystemDriftTests(unittest.TestCase):
    @staticmethod
    def copy_assets(temp: str) -> Path:
        assets = Path(temp) / "assets"
        shutil.copytree(rtd_portal.ASSETS / "design_system", assets / "design_system")
        (assets / "_static").mkdir()
        shutil.copyfile(rtd_portal.ASSETS / "_static" / "manual-locales.css", assets / "_static" / "manual-locales.css")
        return assets

    def test_a_retired_selector_fails_and_the_page_is_skipped(self):
        with TemporaryDirectory() as temp:
            assets = self.copy_assets(temp)
            content = assets / "design_system" / "content.yaml"
            text = content.read_text(encoding="utf-8")
            content.write_text(text.replace('requires: [".hb-warranty-card"]', 'requires: [".hb-retired-card"]', 1),
                               encoding="utf-8")
            with self.assertRaisesRegex(DesignSystemError, "hb-retired-card"):
                design_system_context(assets)
            with patch("sphinx.util.logging.getLogger") as get_logger:
                self.assertIsNone(design_page_context(object(), assets))
            get_logger.return_value.warning.assert_called_once()

    def test_a_missing_asset_or_remote_source_fails(self):
        with TemporaryDirectory() as temp:
            assets = self.copy_assets(temp)
            preview = assets / "design_system" / "previews" / "callout.html"
            original = preview.read_text(encoding="utf-8")
            preview.write_text(original + '<img src="asset:marks/missing.svg" alt="">', encoding="utf-8")
            with self.assertRaisesRegex(DesignSystemError, "missing asset marks/missing.svg"):
                design_system_context(assets)
            preview.write_text(original + '<img src="https://example.com/x.png" alt="">', encoding="utf-8")
            with self.assertRaisesRegex(DesignSystemError, "repository assets"):
                design_system_context(assets)


class AssetLibraryTests(unittest.TestCase):
    def setUp(self):
        self.library = design_system_context(rtd_portal.ASSETS)["asset_library"]
        self.groups = {group["id"]: group for group in self.library["groups"]}

    def test_symbol_groups_split_the_symbol_manifest_and_buttons_list_theirs(self):
        root = repo_root()
        for registry, groups, path_field in (("symbols", ("symbols", "symbols-jp"), "path"),
                                             ("buttons", ("buttons",), "asset")):
            manifest = json.loads((root / REGISTRIES[registry][0]).read_text(encoding="utf-8"))
            expected = sorted(Path(entry[path_field]).name for entry in manifest["assets"])
            listed = sorted(item["name"] for group in groups for item in self.groups[group]["items"])
            self.assertEqual(listed, expected, registry)
        self.assertTrue(all("h1-jp-" in item["name"] or "_gray_jp" in item["name"]
                            for item in self.groups["symbols-jp"]["items"]))

    def test_tiles_describe_the_repository_files(self):
        root = repo_root()
        self.assertEqual(self.library["count"], sum(len(group["items"]) for group in self.library["groups"]))
        for group in self.library["groups"]:
            for item in group["items"]:
                with self.subTest(asset=item["ref"]):
                    folder, name = item["ref"].split("/", 1)
                    source = root / ASSET_ROOTS[folder] / name
                    self.assertTrue(source.is_file())
                    self.assertEqual(item["facts"][0], source.suffix[1:].upper())
                    if source.suffix == ".png":
                        with Image.open(source) as image:
                            width, height = image.size
                            alpha = image.mode in ("RGBA", "LA") or "transparency" in image.info
                        self.assertEqual(item["facts"][2:], [f"{width} × {height} px",
                                                             "含透明通道" if alpha else "无透明通道"])
                    else:
                        text = source.read_text(encoding="utf-8").lower()
                        self.assertTrue(all(color in text for color in item["facts"][2][3:].split(" · ")))
        names = {item["name"] for group in self.library["groups"] for item in group["items"]}
        self.assertNotIn("jackery_logo.png", names)

    def test_no_shown_or_copied_file_carries_a_withdrawn_hash(self):
        withdrawn = withdrawn_hashes(repo_root())
        self.assertTrue(withdrawn)
        for ref, source in design_system_context(rtd_portal.ASSETS)["assets"].items():
            self.assertNotIn(hashlib.sha256(source.read_bytes()).hexdigest(), withdrawn, ref)


class PrintSpecTests(unittest.TestCase):
    def setUp(self):
        self.spec = design_system_context(rtd_portal.ASSETS)["print"]
        self.tokens = load_layout_tokens(Paths(root=repo_root()).layout_params_csv)

    def test_values_come_from_the_layout_table(self):
        for row in self.spec["page"] + [row for group in self.spec["geometry"] for row in group["rows"]]:
            with self.subTest(key=row["key"]):
                self.assertEqual(row["value"], value_text(self.tokens[row["key"]]))
        for row in self.spec["type"]:
            with self.subTest(style=row["prefix"]):
                size = self.tokens[f"{row['prefix']}_font_size"]
                self.assertEqual(row["size"], f"{size.value} {size.unit}")
                self.assertIn(f"font-size:{size.value}{size.unit}", row["sample_style"])
        for color in self.spec["colors"]:
            self.assertEqual(color["chip"], cmyk_screen(self.tokens[color["key"]].value))
        width = self.tokens["page_paperwidth"]
        self.assertIn(f"--page_paperwidth: {width.value}{width.unit};", self.spec["tokens_css"])
        self.assertNotIn("--lang_", self.spec["tokens_css"])

    def test_formatting(self):
        self.assertEqual(cmyk_screen("0,0,0,0.90"), "#1a1a1a")
        self.assertEqual(cmyk_screen("0,0,0,0"), "#ffffff")
        self.assertEqual(value_text(self.tokens["brand_color_branddark"]), "C0 M0 Y0 K90")
        self.assertEqual(value_text(self.tokens["comp_spec_table_left_ratio"]), "31.5%")


class AssetAndPrintDriftTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.assets = DesignSystemDriftTests.copy_assets(self.temp.name)
        self.content = self.assets / "design_system" / "content.yaml"
        self.text = self.content.read_text(encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def assert_fails(self, old: str, new: str, message: str):
        self.assertIn(old, self.text)
        self.content.write_text(self.text.replace(old, new, 1), encoding="utf-8")
        with self.assertRaisesRegex(DesignSystemError, message):
            design_system_context(self.assets)

    def test_a_note_for_a_retired_file_fails(self):
        self.assert_fails("    lcd_parallel.png:", "    lcd_retired.png:", r"lcd_retired\.png.*match no listed file")

    def test_a_missing_or_withdrawn_file_fails(self):
        self.assert_fails("        - latex/icon_clock_3s.png", "        - latex/icon_clock_retired.png",
                          "missing asset latex/icon_clock_retired.png")
        # Withdrawn bytes stay withdrawn whatever folder or name they sit under.
        self.assert_fails("        - cover/support_icon.png",
                          "        - cover/support_icon.png\n        - marks/warning_triangle.png",
                          "marks/warning_triangle.png carries a withdrawn hash")

    def test_a_retired_print_token_or_screen_colour_fails(self):
        self.assert_fails("    page_footskip: ", "    page_footskip_retired: ", "page_footskip_retired")
        self.assert_fails('screen: "--hb-line"', 'screen: "--hb-line-retired"', "--hb-line-retired")

    def test_the_page_preview_may_only_use_defined_tokens(self):
        css = self.assets / "design_system" / "print_page.css"
        css.write_text(css.read_text(encoding="utf-8") + ".x { width: var(--comp_retired); }\n", encoding="utf-8")
        with self.assertRaisesRegex(DesignSystemError, "--comp_retired"):
            design_system_context(self.assets)


class FormattingTests(unittest.TestCase):
    def test_inline_escapes_everything_but_code_strong_and_em(self):
        html = str(inline("<b>x</b> `a<b>` **粗** *you*"))
        self.assertEqual(html, "&lt;b&gt;x&lt;/b&gt; <code>a&lt;b&gt;</code> <strong>粗</strong> <em>you</em>")

    def test_contrast_ratio(self):
        self.assertEqual(contrast_ratio("#343031", "#ffffff"), 13.02)
        self.assertEqual(contrast_ratio("#fff", "#ffffff"), 1.0)
        self.assertIsNone(contrast_ratio("#00ae5840", "#ffffff"))


if __name__ == "__main__":
    unittest.main()
