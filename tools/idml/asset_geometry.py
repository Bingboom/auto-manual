"""Asset-dimension helpers kept outside the load-bearing XML primitives."""
from __future__ import annotations

from pathlib import Path


def fitted_art_size(asset: Path, width: float) -> tuple[float, float]:
    """Return width plus an aspect-ratio-preserving raster/PDF height."""
    if asset.suffix.casefold() == ".pdf":
        try:
            import fitz

            with fitz.open(asset) as document:
                rect = document[0].rect
                if rect.width > 0:
                    return width, width * rect.height / rect.width
        except Exception:
            pass
    try:
        from PIL import Image

        with Image.open(asset) as image:
            image_width, image_height = image.size
        if image_width > 0:
            return width, width * image_height / image_width
    except Exception:
        pass
    return width, width * 0.62


__all__ = ["fitted_art_size"]
