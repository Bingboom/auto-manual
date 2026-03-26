from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ManualHtmlAssetsTests(unittest.TestCase):
    def test_conf_base_should_include_manual_html_assets(self) -> None:
        text = (ROOT / "docs" / "conf_base.py").read_text(encoding="utf-8")

        self.assertIn("html_theme = \"furo\"", text)
        self.assertIn("hb_manual.css", text)
        self.assertIn("hb_paged.css", text)
        self.assertIn("hb_manual.js", text)
        self.assertIn("hb_paged.js", text)

    def test_manual_css_should_hide_furo_chrome_in_manual_preview_mode(self) -> None:
        text = (ROOT / "docs" / "_static" / "hb_manual.css").read_text(encoding="utf-8")

        self.assertIn("body.hb-manual-switcher-body .sidebar-drawer", text)
        self.assertIn("body.hb-manual-switcher-body .toc-drawer", text)
        self.assertIn("body.hb-manual-switcher-body .article-container", text)
        self.assertIn("body.hb-manual-switcher-body #furo-main-content", text)


if __name__ == "__main__":
    unittest.main()
