"""Derive the JE-2000C JP Web artwork from the frozen PDF and reused files.

Run from the repository root:

    python manual_sources/JE-2000C/JP/ja/git-20261103-88b78332/derive_assets.py

``source/asset_recipe.json`` is the reviewed recipe. Panels are complete
3x renders of the source rectangle (frames, leader lines, captions and phone
frames kept). Native icons keep the original PDF vector paths through the
shared ``native_symbol_svg`` selector, so they carry no page or cell backdrop.
Reused files are copied byte-identically after a hash check. Every safety
symbol reuses an existing shared catalog variant that passes the fixed 2%
admission against this PDF; nothing is written to the shared catalog.
The symbol admission rows of ``source_manifest.json`` are written from the
same recipe and the transcription.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys

import fitz

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


def derive() -> dict:
    recipe = read(PACKAGE / "source/asset_recipe.json")
    manifest = read(PACKAGE / "source_manifest.json")
    pdf = PACKAGE / manifest["original_source"]["filename"]
    if sha256(pdf.read_bytes()) != recipe["source_sha256"]:
        raise ValueError("authoritative PDF identity changed")
    lines = {line["id"]: line for page in read(PACKAGE / "source/transcription.json")["pages"]
             for line in page["lines"]}
    assets = PACKAGE / "assets"
    if assets.exists():
        shutil.rmtree(assets)
    assets.mkdir()
    scale = fitz.Matrix(recipe["panel_scale"], recipe["panel_scale"])
    with fitz.open(pdf) as doc:
        for panel in recipe["panels"]:
            page = doc[panel["physical_page"] - 1]
            page.get_pixmap(matrix=scale, clip=fitz.Rect(panel["bbox"]), alpha=False).save(PACKAGE / panel["path"])
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
            check = compare_symbol(data, ".svg", native)
            (PACKAGE / symbol["path"]).write_bytes(data)
            line = lines[symbol["caption_id"]]
            caption_bbox = line["native"][0]["bbox"]
            glyph, caption = fitz.Rect(symbol["glyph_bbox"]), fitz.Rect(caption_bbox)
            band = glyph | caption
            rows.append({
                "asset_ref": symbol["path"], "asset_sha256": sha256(data),
                "physical_page": symbol["physical_page"], "drawing_indices": indices,
                "glyph_bbox": symbol["glyph_bbox"], "caption_bbox": caption_bbox,
                "row_bbox": [band.x0 - 1, band.y0 - 1, band.x1 + 1, band.y1 + 1],
                "caption_text": line["text"],
                "caption_sha256": caption_pixels(page, caption_bbox),
                "shared_symbol_key": symbol["shared_symbol_key"], **check,
            })
    for item in recipe["reused"]:
        data = (ROOT / item["from"]).read_bytes()
        if sha256(data) != item["sha256"]:
            raise ValueError("reused asset changed: " + item["from"])
        (PACKAGE / item["path"]).write_bytes(data)
    return {"schema_version": SCHEMA, "locales": {"ja": rows}}


def main() -> None:
    admission = derive()
    path = PACKAGE / "source_manifest.json"
    manifest = read(path)
    manifest["symbol_asset_admission"] = admission
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"assets": sorted(p.relative_to(PACKAGE).as_posix()
                                       for p in (PACKAGE / "assets").rglob("*") if p.is_file()),
                      "symbols": [{"ref": r["asset_ref"], "error": r["max_mean_channel_error"]}
                                  for r in admission["locales"]["ja"]]}, indent=1))


if __name__ == "__main__":
    main()
