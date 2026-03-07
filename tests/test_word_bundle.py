from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.word_bundle import derive_word_title, render_safety_word_html, resolve_reference_doc


class TestWordBundle(unittest.TestCase):
    def test_resolve_reference_doc_supports_glob(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "EN-HomePower 2000 Plus User Manual.docx"
            target.write_text("demo", encoding="utf-8")

            resolved = resolve_reference_doc("EN-HomePower*.docx", root=root)
            self.assertEqual(target, resolved)

    def test_derive_word_title_prefers_configured_title(self) -> None:
        title = derive_word_title(
            {"word_title": "|PRODUCT_NAME| Guide"},
            None,
            {"PRODUCT_NAME": "HomePower 2000 Plus"},
            {},
        )
        self.assertEqual("HomePower 2000 Plus Guide", title)

    def test_render_safety_word_html_outputs_headings_and_lists(self) -> None:
        html = render_safety_word_html(
            {
                "title_main": "IMPORTANT SAFETY INFORMATION",
                "warning_title": "WARNING",
                "title_operating": "OPERATING INSTRUCTIONS",
                "lead_top": "Always follow these precautions.",
                "save_title": "SAVE THESE INSTRUCTIONS",
                "top_items": ["Top item"],
                "bottom_items": ["Bottom item"],
            }
        )
        self.assertIn("<h1>IMPORTANT SAFETY INFORMATION</h1>", html)
        self.assertIn("<h2>OPERATING INSTRUCTIONS</h2>", html)
        self.assertIn("<li>Top item</li>", html)


if __name__ == "__main__":
    unittest.main()
