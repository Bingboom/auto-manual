"""Derive the JHP-3600A-RC US Web artwork from the frozen PDF and reused files.

Run from the repository root:

    python manual_sources/JHP-3600A-RC/US/en/git-20261027-ab7f7393/derive_assets.py

``source/asset_recipe.json`` is the reviewed recipe. Panels are complete
3x renders of the source rectangle (panel backgrounds, leader lines, captions
and phone frames kept). A panel ``blank`` rectangle covers body copy printed
inside the panel; it is filled with the panel's own surrounding colour and the
copy is rendered as native HTML instead. Native LCD icons keep the original
PDF vector paths through the shared ``native_symbol_svg`` selector, so they
carry no page or cell backdrop. Reused files (LCD icons, key buttons, FCC mark,
shared symbols) are copied byte-identically after a hash check. The symbol
admission rows of ``source_manifest.json`` are written from the same recipe
and the reviewed transcription.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys
from statistics import median

import fitz
from PIL import Image

PACKAGE = Path(__file__).resolve().parent
ROOT = next(parent for parent in PACKAGE.parents if (parent / "build.py").is_file())
sys.path.insert(0, str(ROOT))

from tools.asset_pipeline.native_svg import native_symbol_svg  # noqa: E402
from tools.web.symbol_asset_admission import SCHEMA, compare_symbol  # noqa: E402

SHARED_SYMBOLS = ROOT / "docs/renderers/web/assets/shared/symbols"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def native_svg(page: fitz.Page, bbox: list[float]) -> tuple[bytes, list[int]]:
    box = fitz.Rect(bbox)
    indices = [i for i, d in enumerate(page.get_drawings()) if box.contains(d["rect"])]
    return native_symbol_svg(page, indices, bbox), indices


def caption_pixels(page: fitz.Page, bbox: list[float]) -> str:
    pixels = page.get_pixmap(matrix=fitz.Matrix(4, 4), clip=fitz.Rect(bbox), alpha=False)
    return sha256(pixels.tobytes("png"))


def blank(path: Path, panel: list[float], rects: list[list[float]], scale: float) -> None:
    """Fill each rectangle with the median colour of the pixels just outside it."""
    image = Image.open(path).convert("RGB")
    for rect in rects:
        x0, y0, x1, y1 = (round((value - panel[index % 2]) * scale) for index, value in enumerate(rect))
        x0, y0 = max(x0, 0), max(y0, 0)
        x1, y1 = min(x1, image.width - 1), min(y1, image.height - 1)
        inside = range(image.width), range(image.height)
        ring = [image.getpixel((x, y)) for x in range(x0 - 1, x1 + 2) for y in (y0 - 1, y1 + 1)
                if x in inside[0] and y in inside[1]]
        ring += [image.getpixel((x, y)) for y in range(y0 - 1, y1 + 2) for x in (x0 - 1, x1 + 1)
                 if x in inside[0] and y in inside[1]]
        colour = tuple(int(median(pixel[channel] for pixel in ring)) for channel in range(3))
        image.paste(colour, (x0, y0, x1 + 1, y1 + 1))
    image.save(path)


def derive() -> dict:
    recipe = read(PACKAGE / "source/asset_recipe.json")
    manifest = read(PACKAGE / "source_manifest.json")
    pdf = PACKAGE / manifest["original_source"]["filename"]
    if sha256(pdf.read_bytes()) != recipe["source_sha256"]:
        raise ValueError("authoritative PDF identity changed")
    lines = {line["id"]: line["text"] for page in read(PACKAGE / "source/transcription.json")["pages"]
             for line in page["lines"]}
    assets = PACKAGE / "assets"
    if assets.exists():
        shutil.rmtree(assets)
    assets.mkdir()
    factor = recipe["panel_scale"]
    scale = fitz.Matrix(factor, factor)
    with fitz.open(pdf) as doc:
        for panel in recipe["panels"]:
            page = doc[panel["physical_page"] - 1]
            target = PACKAGE / panel["path"]
            page.get_pixmap(matrix=scale, clip=fitz.Rect(panel["bbox"]), alpha=False).save(target)
            if panel.get("blank"):
                blank(target, panel["bbox"], panel["blank"], factor)
        for icon in recipe["native_icons"]:
            svg, indices = native_svg(doc[icon["physical_page"] - 1], icon["glyph_bbox"])
            if indices != icon["drawing_indices"]:
                raise ValueError("native icon drawing selection changed: " + icon["path"])
            (PACKAGE / icon["path"]).write_bytes(svg)
        rows = []
        for symbol in recipe["symbols"]:
            page = doc[symbol["physical_page"] - 1]
            native, indices = native_svg(page, symbol["glyph_bbox"])
            data = (SHARED_SYMBOLS / symbol["shared_path"]).read_bytes()
            check = compare_symbol(data, Path(symbol["shared_path"]).suffix, native)
            (PACKAGE / symbol["path"]).write_bytes(data)
            glyph, caption = fitz.Rect(symbol["glyph_bbox"]), fitz.Rect(symbol["caption_bbox"])
            band = glyph | caption
            rows.append({
                "asset_ref": symbol["path"], "asset_sha256": sha256(data),
                "physical_page": symbol["physical_page"], "drawing_indices": indices,
                "glyph_bbox": symbol["glyph_bbox"], "caption_bbox": symbol["caption_bbox"],
                "row_bbox": [band.x0 - 1, band.y0 - 1, band.x1 + 1, band.y1 + 1],
                "caption_text": lines[symbol["caption_id"]],
                "caption_sha256": caption_pixels(page, symbol["caption_bbox"]),
                "shared_symbol_key": symbol["shared_symbol_key"], **check,
            })
    for item in recipe["reused"]:
        data = (ROOT / item["from"]).read_bytes()
        if sha256(data) != item["sha256"]:
            raise ValueError("reused asset changed: " + item["from"])
        (PACKAGE / item["path"]).write_bytes(data)
    return {"schema_version": SCHEMA, "locales": {"en": rows}}


def main() -> None:
    admission = derive()
    path = PACKAGE / "source_manifest.json"
    manifest = read(path)
    manifest["symbol_asset_admission"] = admission
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"assets": sorted(p.relative_to(PACKAGE).as_posix()
                                       for p in (PACKAGE / "assets").rglob("*") if p.is_file())}, indent=1))


if __name__ == "__main__":
    main()
