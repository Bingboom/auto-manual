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
from tools.rtd.design_assets import ASSET_ROOTS, REGISTRIES, tile_name, withdrawn_hashes
from tools.rtd.design_content import load_content
from tools.rtd.design_print import cmyk_screen, value_text
from tools.rtd.design_system import (
    DesignSystemError, contrast_grade, contrast_ratio, design_page_context, design_system_context, inline,
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
        shutil.copyfile(rtd_portal.ASSETS / "_static" / "manual-reader.css", assets / "_static" / "manual-reader.css")
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
        page_rows = [row for figure in self.spec["page"] for row in figure["rows"]]
        for row in page_rows + [row for group in self.spec["geometry"] for row in group["rows"]]:
            with self.subTest(key=row["key"]):
                self.assertEqual(row["value"], value_text(self.tokens[row["key"]]))
        for figure in self.spec["page"]:
            values = [self.tokens[row["key"]].value for row in figure["rows"]]
            self.assertTrue(figure["value"].startswith(values[0]) and figure["value"].endswith(" mm"), figure)
            self.assertTrue(all(value in figure["value"] for value in values), figure)
        for row in self.spec["type"]:
            with self.subTest(style=row["prefix"]):
                size = self.tokens[f"{row['prefix']}_font_size"]
                self.assertEqual(row["size"], f"{size.value} {size.unit}")
                self.assertNotIn("sample_style", row)  # pt sizes on a screen would pass for print sizes
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
        self.assert_fails("keys: [page_footskip]", "keys: [page_footskip_retired]", "page_footskip_retired")
        self.assert_fails('screen: "--hb-line"', 'screen: "--hb-line-retired"', "--hb-line-retired")

    def test_an_unknown_colour_group_a_retired_style_id_or_an_untitled_rule_fails(self):
        self.assert_fails("    group: lamp\n", "    group: lamps\n", "group must be one of")
        self.assert_fails("  lamp: 指示灯\n", "  lamp: 指示灯\n  extra: 额外\n", "colour group extra lists no colour")
        self.assert_fails("style_id: HB-TABLE-SPEC\n", "style_id: HB-TABLE-RETIRED\n",
                          "HB-TABLE-RETIRED is not in the manual style contract")
        self.assert_fails('    - "**先盘点。** ', '    - "先盘点。', "needs a")

    def test_the_page_preview_may_only_use_defined_tokens(self):
        css = self.assets / "design_system" / "print_page.css"
        css.write_text(css.read_text(encoding="utf-8") + ".x { width: var(--comp_retired); }\n", encoding="utf-8")
        with self.assertRaisesRegex(DesignSystemError, "--comp_retired"):
            design_system_context(self.assets)


class InnerTabTests(unittest.TestCase):
    """The 2026-11 inner tabs: grouped, graded colours; linked components; asset uses; the print page card."""

    @classmethod
    def setUpClass(cls):
        cls.context = design_system_context(rtd_portal.ASSETS)
        cls.items = [item for group in cls.context["component_groups"] for item in group["items"]]
        cls.tiles = [tile for group in cls.context["asset_library"]["groups"] for tile in group["items"]]

    def test_colours_are_grouped_in_content_order_and_marked_on_paper(self):
        groups = self.context["color_groups"]
        self.assertEqual([group["id"] for group in groups], list(load_content(rtd_portal.ASSETS)["color_groups"]))
        listed = [color for group in groups for color in group["colors"]]
        self.assertEqual(sorted(color["index"] for color in listed), list(range(1, len(self.context["colors"]) + 1)))
        inks: dict[str, list[str]] = {}
        for ink in self.context["print"]["colors"]:
            inks.setdefault(ink["screen"], []).append(ink["swatch"])
        for color in listed:
            with self.subTest(color=color["name"]):
                ground = color["value"] == self.context["paper"]
                self.assertEqual(color["grade"]["label"], "底色" if ground else contrast_grade(color["contrast"])["label"])
                self.assertEqual([ink["swatch"] for ink in color["inks"]], inks.get(color["token"], []))
                if color["token"].startswith("--"):
                    self.assertEqual(color["label"], color["token"])
                else:
                    self.assertRegex(color["label"], rf"^{color['token']} · \.hb-[a-z-]+$")
        named = {color["name"]: color for color in listed}
        self.assertEqual([ink["swatch"] for ink in named["正文"]["inks"]], ["TextGray", "TextK90"])

    def test_components_link_their_style_definition(self):
        contract = Paths(root=repo_root()).manual_style_contract
        lines = contract.read_text(encoding="utf-8").splitlines()
        linked = 0
        for item in self.items:
            with self.subTest(component=item["id"]):
                match = re.match(r"HB-[A-Z0-9-]+", item["style_id"])
                if match is None:
                    self.assertIsNone(item["style_href"])
                    continue
                page, line = item["style_href"].split("#L")
                self.assertTrue(page.endswith("/blob/main/" + contract.relative_to(repo_root()).as_posix()), page)
                self.assertEqual(lines[int(line) - 1], f"  {match.group(0)}:")
                linked += 1
        self.assertGreater(linked, 20)

    def test_an_asset_lists_the_components_whose_previews_show_it(self):
        users: dict[str, set[str]] = {}
        for item in self.items:
            for ref in re.findall(r'src="\.\./assets/([^"]+)"', item["markup"]):
                users.setdefault(ref, set()).add(item["title"])
        for tile in self.tiles:
            with self.subTest(asset=tile["ref"]):
                self.assertEqual(len(tile["used_in"]), len(set(tile["used_in"])))
                self.assertEqual(set(tile["used_in"]), users.get(tile["ref"], set()))
        self.assertTrue(any(tile["used_in"] for tile in self.tiles))
        self.assertEqual(len({tile["slug"] for tile in self.tiles}), len(self.tiles))

    def test_tiles_name_files_short_and_the_rules_keep_their_titles(self):
        self.assertEqual(tile_name("symbol_warning_triangle.svg"), "warning_triangle")
        self.assertEqual(tile_name("lcd_transfer-switch.png"), "lcd_transfer-switch")
        self.assertEqual(tile_name("symbol_je2000e-eu-batch1465-pt-general_warning.svg"), "…1465-pt-general_warning")
        self.assertTrue(all(len(tile["short"]) <= 24 for tile in self.tiles))
        steps = self.context["asset_library"]["steps"]
        self.assertTrue(steps)
        for step in steps:
            self.assertTrue(str(step["text"]).startswith(f"<strong>{step['title']}"), step["title"])

    def test_the_print_page_is_drawn_to_scale_and_ten_styles_lead(self):
        spec = self.context["print"]
        tokens = load_layout_tokens(Paths(root=repo_root()).layout_params_csv)

        def mm(key: str) -> float:
            return float(tokens[key].value)

        width, height = mm("page_paperwidth"), mm("page_paperheight")
        drawing = spec["drawing"]
        self.assertEqual(drawing["text"]["top"], f"{mm('page_margin_top') / height * 100:.2f}%")
        self.assertEqual(drawing["text"]["left"], f"{mm('page_margin_left') / width * 100:.2f}%")
        baseline = height - mm("page_margin_bottom") + mm("page_footskip")
        self.assertEqual(drawing["foot"], f"{baseline / height * 100:.2f}%")
        self.assertEqual(drawing["folio"], f"{(baseline - mm('page_footer_raise')) / height * 100:.2f}%")
        lead = [row["prefix"] for row in spec["type"] if row["lead"]]
        self.assertEqual(len(lead), 10)
        self.assertTrue({"type_h1", "type_body", "page_footer"} <= set(lead))
        self.assertEqual(spec["geometry_count"], sum(len(group["rows"]) for group in spec["geometry"]))
        self.assertTrue(spec["overrides"])


class FormattingTests(unittest.TestCase):
    def test_inline_escapes_everything_but_code_strong_and_em(self):
        html = str(inline("<b>x</b> `a<b>` **粗** *you*"))
        self.assertEqual(html, "&lt;b&gt;x&lt;/b&gt; <code>a&lt;b&gt;</code> <strong>粗</strong> <em>you</em>")

    def test_contrast_grade(self):
        self.assertEqual([contrast_grade(ratio)["label"] for ratio in (13.02, 7.0, 6.99, 4.5, 4.49, 3.0, 2.99, 1.0, None)],
                         ["AAA", "AAA", "AA", "AA", "大字 AA", "大字 AA", "装饰", "装饰", "半透明"])

    def test_contrast_ratio(self):
        self.assertEqual(contrast_ratio("#343031", "#ffffff"), 13.02)
        self.assertEqual(contrast_ratio("#fff", "#ffffff"), 1.0)
        self.assertIsNone(contrast_ratio("#00ae5840", "#ffffff"))


if __name__ == "__main__":
    unittest.main()
