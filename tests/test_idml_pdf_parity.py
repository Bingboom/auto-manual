from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools.idml_pdf_parity import _parse_pdfinfo, _selected_pages, _visual_metrics


class IdmlPdfParityTests(unittest.TestCase):
    def test_pdfinfo_contract(self) -> None:
        info = _parse_pdfinfo("Pages: 60\nPage size: 368.787 x 524.693 pts\n")

        self.assertEqual(60, info["page_count"])
        self.assertEqual(368.787, info["page_width_pt"])
        self.assertEqual(524.693, info["page_height_pt"])

    def test_page_selector_supports_last_and_deduplicates(self) -> None:
        self.assertEqual([1, 3, 60], _selected_pages("1,3,last,3", 60))
        self.assertEqual([1, 2, 3], _selected_pages("all", 3))

    def test_visual_metrics_distinguish_identical_and_changed_pages(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            white = root / "white.png"
            changed = root / "changed.png"
            Image.new("L", (10, 10), 255).save(white)
            image = Image.new("L", (10, 10), 255)
            image.putpixel((0, 0), 0)
            image.save(changed)

            identical = _visual_metrics(white, white)
            delta = _visual_metrics(white, changed)

        self.assertEqual(0.0, identical["mean_absolute_difference"])
        self.assertGreater(delta["mean_absolute_difference"], 0.0)
        self.assertEqual(0.01, delta["changed_pixel_ratio"])


if __name__ == "__main__":
    unittest.main()
