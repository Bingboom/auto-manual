from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ManualHtmlAssetsTests(unittest.TestCase):
    def test_conf_base_should_include_manual_html_assets(self) -> None:
        text = (ROOT / "docs" / "conf_base.py").read_text(encoding="utf-8")

        self.assertIn("html_theme = \"furo\"", text)
        self.assertIn("hb_manual.css", text)
        self.assertIn("hb_manual.js", text)
        self.assertNotIn("hb_paged.css", text)
        self.assertNotIn("hb_paged.js", text)
        self.assertIn("_assets/templates/word_template/common_assets/operation/lcd_mode.png", text)

    def test_latex_theme_should_load_multirow_for_merged_table_cells(self) -> None:
        text = (ROOT / "docs" / "renderers" / "latex" / "theme.tex").read_text(encoding="utf-8")

        self.assertIn(r"\usepackage{multirow}", text)

    def test_manual_css_should_hide_furo_chrome_in_manual_preview_mode(self) -> None:
        text = (ROOT / "docs" / "_static" / "hb_manual.css").read_text(encoding="utf-8")

        self.assertIn("body.hb-manual-switcher-body .sidebar-drawer", text)
        self.assertIn("body.hb-manual-switcher-body .toc-drawer", text)
        self.assertIn("body.hb-manual-switcher-body .article-container", text)
        self.assertIn('body.hb-manual-switcher-body :is(#furo-main-content, .body[role="main"])', text)

    def test_manual_css_should_define_reading_surface_rules(self) -> None:
        text = (ROOT / "docs" / "_static" / "hb_manual.css").read_text(encoding="utf-8")

        self.assertIn(':is(#furo-main-content, .body[role="main"]) h1', text)
        self.assertIn(':is(#furo-main-content, .body[role="main"]) h2:not(.hb-subbar):not(.hb-spec-section)', text)
        self.assertIn(':is(#furo-main-content, .body[role="main"]) h2:not(.hb-subbar):not(.hb-spec-section)::before', text)
        self.assertIn(':is(#furo-main-content, .body[role="main"]) h3::before', text)
        self.assertIn("> a.reference.internal.image-reference", text)
        self.assertIn(".table-wrapper.docutils", text)
        self.assertIn(".hb-preface__block", text)
        self.assertIn(".hb-manual-toc", text)

    def test_manual_js_should_promote_preface_into_cards(self) -> None:
        text = (ROOT / "docs" / "_static" / "hb_manual.js").read_text(encoding="utf-8")

        self.assertIn("initPrefaceLayout", text)
        self.assertIn("initManualSidebar", text)
        self.assertIn("manualContentRoot", text)
        self.assertIn('.body[role="main"]', text)
        self.assertIn('document.body.classList.contains("hb-manual-switcher-body")', text)
        self.assertIn("hb-preface__block", text)
        self.assertIn("hb-manual-toc__link", text)
        self.assertIn("FR IMPORTANT", text)
        self.assertIn("ES IMPORTANTE", text)


if __name__ == "__main__":
    unittest.main()
