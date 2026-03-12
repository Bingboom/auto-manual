from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

from tools.word_bundle import derive_word_title, render_safety_word_html, resolve_reference_doc
from tools.word_bundle_html import _inject_img_dimensions


class TestWordBundle(unittest.TestCase):
    def test_inject_img_dimensions_should_add_proportional_height_for_local_png(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            image_path = root / "demo.png"
            image_path.write_bytes(
                b"\x89PNG\r\n\x1a\n"
                + b"\x00\x00\x00\rIHDR"
                + struct.pack(">II", 620, 486)
            )

            html = f'<img src="{image_path.resolve().as_uri()}" style="width: 40px;" />'
            out = _inject_img_dimensions(html)

            self.assertIn('width="40"', out)
            self.assertIn('height="31"', out)

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
