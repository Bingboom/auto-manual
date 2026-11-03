"""Derive the JE-1800B JP Web artwork from the frozen PDF and reused shared files.

Run from the repository root after ``extract_text.py``:

    python manual_sources/JE-1800B/JP/ja/git-20261103-754e8c1d-v2/derive_assets.py

``source/asset_recipe.json`` is the reviewed recipe. Panels are complete 3x
renders of the source rectangle (panel backgrounds, leader lines, captions and
phone frames kept). Safety symbols are compared with the source's own vector
paths (``native_symbol_svg``) under the fixed 2% admission; every package symbol
is a byte-identical copy of a shared catalog variant. This script never writes
the shared catalog: a missing variant stops the run. Reused files are copied
byte-identically after a hash check. The symbol admission rows of
``source_manifest.json`` are written from the same recipe and the source text.
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


def glyph_indices(page: fitz.Page, bbox: list[float]) -> list[int]:
    box = fitz.Rect(bbox)
    return [i for i, d in enumerate(page.get_drawings()) if box.contains(d["rect"])]


def caption_text(lines: dict[str, dict], blocks: list[str]) -> str:
    return "".join(line["text"].strip() for block in blocks
                   for key, line in lines.items() if key.startswith(block + "-l"))


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
    for folder in ("shared-lcd", "shared-buttons"):
        (assets / folder).mkdir(parents=True)
    scale = fitz.Matrix(recipe["panel_scale"], recipe["panel_scale"])
    rows = []
    with fitz.open(pdf) as doc:
        for panel in recipe["panels"]:
            page = doc[panel["physical_page"] - 1]
            page.get_pixmap(matrix=scale, clip=fitz.Rect(panel["bbox"]), alpha=False).save(PACKAGE / panel["path"])
        for icon in recipe["native_icons"]:
            page = doc[icon["physical_page"] - 1]
            indices = glyph_indices(page, icon["glyph_bbox"])
            if indices != icon["drawing_indices"]:
                raise ValueError("native icon drawing selection changed: " + icon["path"])
            (PACKAGE / icon["path"]).write_bytes(native_symbol_svg(page, indices, icon["glyph_bbox"]))
        for symbol in recipe["symbols"]:
            page = doc[symbol["physical_page"] - 1]
            indices = glyph_indices(page, symbol["glyph_bbox"])
            native = native_symbol_svg(page, indices, symbol["glyph_bbox"])
            shared = SHARED_SYMBOLS / symbol["shared_path"]
            if not shared.is_file():
                raise ValueError("shared symbol variant missing from the catalog: " + symbol["shared_symbol_key"])
            data = shared.read_bytes()
            try:
                check = compare_symbol(data, shared.suffix, native)
            except ValueError as exc:
                raise ValueError(f"{symbol['path']}: {exc}") from exc
            (PACKAGE / symbol["path"]).write_bytes(data)
            glyph, caption = fitz.Rect(symbol["glyph_bbox"]), fitz.Rect(symbol["caption_bbox"])
            band = glyph | caption
            pixels = page.get_pixmap(matrix=fitz.Matrix(4, 4), clip=caption, alpha=False)
            rows.append({
                "asset_ref": symbol["path"], "asset_sha256": sha256(data),
                "physical_page": symbol["physical_page"], "drawing_indices": indices,
                "glyph_bbox": symbol["glyph_bbox"], "caption_bbox": symbol["caption_bbox"],
                "row_bbox": [band.x0 - 1, band.y0 - 1, band.x1 + 1, band.y1 + 1],
                "caption_text": caption_text(lines, symbol["caption_blocks"]),
                "caption_sha256": sha256(pixels.tobytes("png")),
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
                                       for p in (PACKAGE / "assets").rglob("*") if p.is_file())}, indent=1))


if __name__ == "__main__":
    main()
