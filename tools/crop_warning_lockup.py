#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Remove white background -> transparent PNG, then crop with asymmetric padding.
- Crops to content bbox
- Keeps extra space on the LEFT (KEEP_LEFT)
- Adds small padding on other sides (PAD_OTHER)
"""

from pathlib import Path
from PIL import Image
import numpy as np

INPUT = Path("docs/latex_theme/assets/warning_lockup.jpg")
OUTPUT = Path("docs/latex_theme/assets/warning_lockup_trans_keep_left.png")

WHITE_THRESHOLD = 245  # higher -> keep more near-white pixels (less aggressive)
KEEP_LEFT = 80        # pixels to KEEP on the left side (increase if you want more front whitespace)
PAD_OTHER = 6          # padding for top/right/bottom after cropping (pixels)


def remove_white_background(img: Image.Image) -> Image.Image:
    img = img.convert("RGBA")
    data = np.array(img)

    r, g, b, a = data.T
    white = (r > WHITE_THRESHOLD) & (g > WHITE_THRESHOLD) & (b > WHITE_THRESHOLD)
    data[..., 3][white.T] = 0

    return Image.fromarray(data)


def crop_keep_left(img: Image.Image) -> Image.Image:
    bbox = img.getbbox()
    if not bbox:
        return img

    x0, y0, x1, y1 = bbox
    w, h = img.size

    # Expand bbox:
    # - Keep extra left whitespace (KEEP_LEFT)
    # - Add small padding on other sides (PAD_OTHER)
    new_x0 = max(0, x0 - KEEP_LEFT)
    new_y0 = max(0, y0 - PAD_OTHER)
    new_x1 = min(w, x1 + PAD_OTHER)
    new_y1 = min(h, y1 + PAD_OTHER)

    return img.crop((new_x0, new_y0, new_x1, new_y1))


def main():
    if not INPUT.exists():
        raise FileNotFoundError(f"Input not found: {INPUT}")

    img = Image.open(INPUT)
    img = remove_white_background(img)
    img = crop_keep_left(img)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUTPUT)
    print(f"✔ Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
