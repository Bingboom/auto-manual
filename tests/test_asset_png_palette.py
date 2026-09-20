from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image

from tools.asset_pipeline.extract import (
    PALETTE_ERROR_CHANNEL,
    PALETTE_ERROR_PIXEL_SHARE,
    _write_png,
)
from tools.asset_pipeline.models import ArtifactValidationError


class FakePixmap:
    """The narrow surface `_write_png` uses from a PyMuPDF pixmap."""

    def __init__(self, image: Image.Image, *, alpha: bool = False, n: int = 3) -> None:
        self.width, self.height = image.size
        self.samples = image.tobytes()
        self.alpha = alpha
        self.n = n
        self.xres = self.yres = 96
        self.saved_to: str | None = None

    def save(self, path: str) -> None:
        self.saved_to = path
        Image.frombytes("RGB", (self.width, self.height), self.samples).save(path)


def _line_art(width: int = 120, height: int = 90) -> Image.Image:
    """Flat fills plus a soft stroke — the shape these manual panels actually have."""
    image = Image.new("RGB", (width, height), (255, 255, 255))
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            if 30 <= x < 90 and 20 <= y < 70:
                pixels[x, y] = (214, 214, 216)
            if x in (30, 89) or y in (20, 69):
                pixels[x, y] = (40, 40, 44)
    return image


def _wide_gamut(width: int = 120, height: int = 90) -> Image.Image:
    """A smooth two-axis ramp: no small palette can carry it without banding."""
    image = Image.new("RGB", (width, height))
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            pixels[x, y] = (x * 2 % 256, y * 2 % 256, (x + y) % 256)
    return image


class WritePngTests(unittest.TestCase):
    def test_without_a_palette_the_pixmap_writes_itself(self) -> None:
        with TemporaryDirectory() as td:
            destination = Path(td) / "panel.png"
            pixmap = FakePixmap(_line_art())

            _write_png(pixmap, destination, palette_colors=None)

            self.assertEqual(str(destination), pixmap.saved_to)
            with Image.open(destination) as written:
                self.assertEqual("RGB", written.mode)

    def test_a_palette_writes_an_indexed_png(self) -> None:
        with TemporaryDirectory() as td:
            destination = Path(td) / "panel.png"
            source = _line_art()

            _write_png(FakePixmap(source), destination, palette_colors=256)

            with Image.open(destination) as written:
                self.assertEqual("P", written.mode)
                self.assertEqual(source.size, written.size)

    def test_line_art_survives_the_palette_unchanged(self) -> None:
        """Few enough colours to be exactly representable, so nothing may move."""
        with TemporaryDirectory() as td:
            destination = Path(td) / "panel.png"
            source = _line_art()

            _write_png(FakePixmap(source), destination, palette_colors=256)

            with Image.open(destination) as written:
                self.assertEqual(source.tobytes(), written.convert("RGB").tobytes())

    def test_a_palette_too_small_for_the_artwork_is_refused(self) -> None:
        with TemporaryDirectory() as td:
            destination = Path(td) / "panel.png"

            with self.assertRaisesRegex(ArtifactValidationError, "palette_colors=2 moves"):
                _write_png(FakePixmap(_wide_gamut()), destination, palette_colors=2)

            self.assertFalse(destination.exists())

    def test_the_refusal_reports_what_it_measured(self) -> None:
        with TemporaryDirectory() as td:
            with self.assertRaises(ArtifactValidationError) as caught:
                _write_png(FakePixmap(_wide_gamut()), Path(td) / "p.png", palette_colors=2)

            message = str(caught.exception)
            self.assertIn(f"{PALETTE_ERROR_CHANNEL}/255", message)
            self.assertIn(f"{PALETTE_ERROR_PIXEL_SHARE:.2%}", message)
            self.assertIn("worst channel error", message)

    def test_a_pixmap_with_alpha_is_refused(self) -> None:
        with TemporaryDirectory() as td:
            pixmap = FakePixmap(_line_art(), alpha=True, n=4)

            with self.assertRaisesRegex(ArtifactValidationError, "opaque RGB pixmap"):
                _write_png(pixmap, Path(td) / "p.png", palette_colors=256)


if __name__ == "__main__":
    unittest.main()
