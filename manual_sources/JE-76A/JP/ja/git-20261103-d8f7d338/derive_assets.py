"""Derive the JE-76A JP Web artwork from the frozen PDF.

Run from the repository root:

    python manual_sources/JE-76A/JP/ja/git-20261103-d8f7d338/derive_assets.py

``source/asset_recipe.json`` is the reviewed recipe. Panels are complete
3x renders of the source rectangle (leader lines and printed labels kept);
a recipe ``mask`` paints white only a native-text caption that overlaps a
panel corner. Small LCD glyphs and the Li-ion mark keep the original PDF
vector paths through the shared ``native_symbol_svg`` selector, so they carry
no page or cell backdrop. The print has no symbol table, so no symbol
admission rows are written (``symbols`` and ``reused`` are empty after the
inventory in ``source/discovery.md``).
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
from tools.web.symbol_asset_admission import SCHEMA  # noqa: E402


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def native_svg(page: fitz.Page, bbox: list[float]) -> tuple[bytes, list[int]]:
    box = fitz.Rect(bbox)
    indices = [i for i, d in enumerate(page.get_drawings()) if box.contains(d["rect"])]
    return native_symbol_svg(page, indices, bbox), indices


def panel_pixmap(page: fitz.Page, panel: dict, scale: float) -> fitz.Pixmap:
    pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=fitz.Rect(panel["bbox"]), alpha=False)
    for mask in panel.get("mask", []):
        # Pixmap coordinates are page points times scale (the clip keeps its page origin).
        rect = fitz.IRect(*(round(value * scale) for value in mask))
        pixmap.set_rect(rect & pixmap.irect, (255, 255, 255))
    return pixmap


def derive() -> dict:
    recipe = read(PACKAGE / "source/asset_recipe.json")
    manifest = read(PACKAGE / "source_manifest.json")
    pdf = PACKAGE / manifest["original_source"]["filename"]
    if sha256(pdf.read_bytes()) != recipe["source_sha256"]:
        raise ValueError("authoritative PDF identity changed")
    if recipe["symbols"] or recipe["reused"]:
        raise ValueError("this recipe declares no symbol or reused assets")
    assets = PACKAGE / "assets"
    if assets.exists():
        shutil.rmtree(assets)
    assets.mkdir()
    with fitz.open(pdf) as doc:
        for panel in recipe["panels"]:
            page = doc[panel["physical_page"] - 1]
            panel_pixmap(page, panel, recipe["panel_scale"]).save(PACKAGE / panel["path"])
        for icon in recipe["native_icons"]:
            svg, indices = native_svg(doc[icon["physical_page"] - 1], icon["glyph_bbox"])
            if indices != icon["drawing_indices"]:
                raise ValueError("native icon drawing selection changed: " + icon["path"])
            (PACKAGE / icon["path"]).write_bytes(svg)
    return {"schema_version": SCHEMA, "locales": {"ja": []}}


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
