"""Resolve portable inline-image references for production and flow stories."""
from __future__ import annotations

from tools.rst_inline import IMAGE

from .primitives import image_cell_content


def prepare_inline_images(text: str, ctx, *, tid: str, size: float = 10.0) -> tuple[str, dict[str, str]]:
    replacements: dict[str, str] = {}
    matches = list(IMAGE.finditer(text))
    for index, match in enumerate(matches):
        asset = ctx.resolve_bundle_image(match.group(2))
        if asset is None:
            raise FileNotFoundError(f"inline image is unavailable: {match.group(2)}")
        width, height = ctx.art_frame_size(asset, size)
        if height > size:
            width, height = width * size / height, size
        # Protect the whole marker before CJK font-run segmentation.
        token = f"HBINLINEIMAGE{index}TOKEN"
        text = text.replace(match.group(0), token, 1)
        replacements[token] = image_cell_content(
            f"{tid}_inline_{index}", asset, width, height,
        )
    return text, replacements
