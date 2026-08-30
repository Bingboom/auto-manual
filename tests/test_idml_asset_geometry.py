"""Both branches of the art-sizing helper, including the PyMuPDF-less host.

`art_frame_size` used to apply a fixed 0.62 heuristic to every PDF, because
PIL cannot open one. It now measures the real page box through PyMuPDF, which
is a change to a shared default that no test pinned and that behaves
differently depending on whether PyMuPDF is installed. CI always installs it
(requirements.lock), so the fallback is the branch most likely to rot.
"""
from __future__ import annotations

import builtins
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tools.idml.asset_geometry import fitted_art_size


ROOT = Path(__file__).resolve().parents[1]


def _one_page_pdf(directory: Path, width: float, height: float) -> Path:
    try:
        import fitz
    except ImportError:  # pragma: no cover - exercised only on a bare host
        raise unittest.SkipTest("PyMuPDF is required to author the fixture")
    path = directory / "fixture.pdf"
    document = fitz.open()
    document.new_page(width=width, height=height)
    document.save(path)
    document.close()
    return path


class FittedArtSizeTests(unittest.TestCase):
    def test_pdf_height_follows_the_real_page_box(self) -> None:
        with TemporaryDirectory() as tmp:
            asset = _one_page_pdf(Path(tmp), 300.0, 90.0)

            self.assertEqual((100.0, 30.0), fitted_art_size(asset, 100.0))

    def test_a_host_without_pymupdf_degrades_to_the_documented_heuristic(self) -> None:
        """No PyMuPDF must mean the pre-existing 0.62 default, not a crash.

        PIL raises UnidentifiedImageError on a PDF, which the helper's bare
        except absorbs, so the only correct outcome is the heuristic.
        """
        with TemporaryDirectory() as tmp:
            asset = _one_page_pdf(Path(tmp), 300.0, 90.0)
            real_import = builtins.__import__

            def without_fitz(name, *args, **kwargs):
                if name == "fitz":
                    raise ImportError("no module named 'fitz'")
                return real_import(name, *args, **kwargs)

            saved = sys.modules.pop("fitz", None)
            try:
                with patch.object(builtins, "__import__", without_fitz):
                    self.assertEqual((100.0, 62.0), fitted_art_size(asset, 100.0))
            finally:
                if saved is not None:
                    sys.modules["fitz"] = saved

    def test_raster_sizing_is_unchanged_by_the_pdf_branch(self) -> None:
        from PIL import Image

        asset = ROOT / "docs" / "renderers" / "latex" / "assets" / "warning_lockup.png"
        with Image.open(asset) as image:
            image_width, image_height = image.size

        self.assertEqual(
            (100.0, 100.0 * image_height / image_width),
            fitted_art_size(asset, 100.0),
        )

    def test_an_unopenable_asset_falls_back_instead_of_raising(self) -> None:
        """A path that resolves to nothing openable must not abort a build."""
        self.assertEqual((100.0, 62.0), fitted_art_size(ROOT, 100.0))


if __name__ == "__main__":
    unittest.main()
