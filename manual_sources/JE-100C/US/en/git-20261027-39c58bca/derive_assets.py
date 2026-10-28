"""Derive the JE-100C US English Web artwork from the frozen PDF and reused shared files.

Run from the repository root:

    python manual_sources/JE-100C/US/en/git-20261027-39c58bca/derive_assets.py

``source/asset_recipe.json`` is the reviewed recipe. Panels are complete
3x renders of the source rectangle (panel backgrounds, leader lines, captions
and phone frames kept). Symbols keep the original PDF vector paths through the
shared ``native_symbol_svg`` selector, so they carry no page or cell backdrop. Reused files are copied byte-identically after a hash check.
New symbol variants live in the shared catalog; ``--write-shared`` adds a
missing catalog file once, and every other run only verifies it.
The symbol admission rows of ``source_manifest.json`` are written from the
same recipe and the reviewed transcription.
"""
from __future__ import annotations

import argparse
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


def add_catalog_entry(symbol: dict, data: bytes, indices: list[int], source_sha256: str) -> None:
    """Append-only shared catalog row for a new source-bound native variant."""
    path = SHARED_SYMBOLS / "manifest.json"
    catalog = read(path)
    if any(row["key"] == symbol["shared_symbol_key"] for row in catalog["assets"]):
        raise ValueError("shared symbol key already exists: " + symbol["shared_symbol_key"])
    catalog["assets"].append({
        "key": symbol["shared_symbol_key"], "path": symbol["shared_path"], "sha256": sha256(data),
        "status": "source-bound native variant",
        "provenance": {
            "source": (PACKAGE / "JE-100C-US-EN.pdf").relative_to(ROOT).as_posix(),
            "source_sha256": source_sha256, "physical_page": symbol["physical_page"],
            "drawing_indices": indices, "glyph_bbox": symbol["glyph_bbox"],
            "decision": symbol["decision"],
        },
    })
    path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def derive(write_shared: bool = False) -> dict:
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
    (assets / "shared-lcd").mkdir(parents=True)
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
            shared = SHARED_SYMBOLS / symbol["shared_path"]
            if not symbol.get("reuse"):
                if write_shared and not shared.exists():
                    shared.write_bytes(native)
                    add_catalog_entry(symbol, native, indices, recipe["source_sha256"])
                if shared.read_bytes() != native:
                    raise ValueError("shared native symbol differs from source paths: " + symbol["shared_path"])
            data = shared.read_bytes()
            check = compare_symbol(data, shared.suffix, native)
            (PACKAGE / symbol["path"]).write_bytes(data)
            glyph, caption = fitz.Rect(symbol["glyph_bbox"]), fitz.Rect(symbol["caption_bbox"])
            band = glyph | caption
            rows.append({
                "asset_ref": symbol["path"], "asset_sha256": sha256(data),
                "physical_page": symbol["physical_page"], "drawing_indices": indices,
                "glyph_bbox": symbol["glyph_bbox"], "caption_bbox": symbol["caption_bbox"],
                "row_bbox": [band.x0 - 1, band.y0 - 1, band.x1 + 1, band.y1 + 1],
                "caption_text": " ".join(lines[key] for key in symbol["caption_ids"]),
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-shared", action="store_true",
                        help="add missing new native symbol variants to the shared catalog")
    admission = derive(parser.parse_args().write_shared)
    path = PACKAGE / "source_manifest.json"
    manifest = read(path)
    manifest["symbol_asset_admission"] = admission
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"assets": sorted(p.relative_to(PACKAGE).as_posix()
                                       for p in (PACKAGE / "assets").rglob("*") if p.is_file())}, indent=1))


if __name__ == "__main__":
    main()
