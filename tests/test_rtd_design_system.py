from __future__ import annotations

from pathlib import Path
import re
import shutil
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tools.rtd import portal as rtd_portal
from tools.rtd.design_system import (
    DesignSystemError, contrast_ratio, design_page_context, design_system_context, inline,
    preview_document, template_context, write_design_system,
)
from tools.rtd.design_system_css import class_names, declared, live_stylesheet_text, parse_css
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

    def test_write_places_previews_stylesheet_and_art_beside_the_page(self):
        with TemporaryDirectory() as temp:
            target = write_design_system(Path(temp), rtd_portal.ASSETS, self.context)
            self.assertEqual((target / "web_manual.css").read_text(encoding="utf-8"), live_stylesheet_text())
            self.assertTrue((target / "preview.css").is_file())
            for page in sorted((target / "previews").glob("*.html")):
                for ref in re.findall(r'(?:src|href)="([^"#]+)"', page.read_text(encoding="utf-8")):
                    resolved = (page.parent / ref).resolve()
                    inside = resolved.is_relative_to((Path(temp) / "workspace").resolve())
                    portal_static = ref.startswith("../../../_static/")
                    self.assertTrue(portal_static or (inside and resolved.is_file()), (page.name, ref))


class DesignSystemDriftTests(unittest.TestCase):
    def copy_assets(self, temp: str) -> Path:
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
            with self.assertRaisesRegex(DesignSystemError, "missing preview asset"):
                design_system_context(assets)
            preview.write_text(original + '<img src="https://example.com/x.png" alt="">', encoding="utf-8")
            with self.assertRaisesRegex(DesignSystemError, "repository assets"):
                design_system_context(assets)


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
