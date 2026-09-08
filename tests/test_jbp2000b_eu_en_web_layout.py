from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "docs" / "renderers" / "contracts" / "web_manual.css"
WARRANTY = ROOT / "docs" / "templates" / "page_bp" / "en-web" / "eu_warranty.rst"


class Jbp2000bEuEnWebLayoutTests(unittest.TestCase):
    def test_published_page_eight_layout_is_scoped_to_frozen_target_art(self) -> None:
        css = CSS.read_text(encoding="utf-8")

        for asset in ("lcd.png", "power.png", "lcd_control.png"):
            with self.subTest(asset=asset):
                self.assertIn(
                    f'assets/jbp2000b_eu_en/{asset}',
                    css,
                )
        self.assertIn("> table.lcd-text-only", css)
        self.assertIn("> table.manual-callout-table", css)
        self.assertIn("> p:last-child", css)

    def test_warranty_badge_labels_do_not_embed_a_separator(self) -> None:
        warranty = WARRANTY.read_text(encoding="utf-8")

        self.assertIn("**3 YEARS** **Standard Warranty**", warranty)
        self.assertIn("**2 YEARS** **Extended Warranty**", warranty)
        self.assertNotIn("YEARS —", warranty)


if __name__ == "__main__":
    unittest.main()
