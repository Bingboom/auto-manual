"""Derive the JE-2000C US/en Web artwork from the frozen PDF and reused shared files.

Run from the repository root:

    python manual_sources/JE-2000C/US/en/git-20261027-c357f54d/derive_assets.py

``source/asset_recipe.json`` is the reviewed recipe. Panels are complete
3x renders of the source rectangle (frames, leader lines and captions kept).
The seven LCD description icons are 8x renders of their own glyph rectangle
with a real alpha channel: the PDF draws no backdrop under them, so they carry
no page or cell background. The shared ``native_symbol_svg`` selector cannot
map this PDF (its page SVG has one more visible path than the drawing list),
so the icons are transparent PNG renders instead of SVG paths. Reused files are
copied byte-identically after a hash check. This manual has no symbol table,
so there is no symbol admission.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

import fitz

PACKAGE = Path(__file__).resolve().parent
ROOT = next(parent for parent in PACKAGE.parents if (parent / "build.py").is_file())


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def derive() -> list[str]:
    recipe = read(PACKAGE / "source/asset_recipe.json")
    manifest = read(PACKAGE / "source_manifest.json")
    pdf = PACKAGE / manifest["original_source"]["filename"]
    if sha256(pdf.read_bytes()) != recipe["source_sha256"]:
        raise ValueError("authoritative PDF identity changed")
    assets = PACKAGE / "assets"
    if assets.exists():
        shutil.rmtree(assets)
    assets.mkdir()
    panel = fitz.Matrix(recipe["panel_scale"], recipe["panel_scale"])
    icon = fitz.Matrix(recipe["icon_scale"], recipe["icon_scale"])
    with fitz.open(pdf) as doc:
        for row in recipe["panels"]:
            page = doc[row["physical_page"] - 1]
            page.get_pixmap(matrix=panel, clip=fitz.Rect(row["bbox"]), alpha=False).save(PACKAGE / row["path"])
        for row in recipe["native_icons"]:
            page = doc[row["physical_page"] - 1]
            pixmap = page.get_pixmap(matrix=icon, clip=fitz.Rect(row["glyph_bbox"]), alpha=True)
            if min(pixmap.samples[3::4]) != 0:
                raise ValueError("LCD icon has no transparent margin: " + row["path"])
            pixmap.save(PACKAGE / row["path"])
    for row in recipe["reused"]:
        data = (ROOT / row["from"]).read_bytes()
        if sha256(data) != row["sha256"]:
            raise ValueError("reused asset changed: " + row["from"])
        (PACKAGE / row["path"]).write_bytes(data)
    return sorted(p.relative_to(PACKAGE).as_posix() for p in assets.rglob("*") if p.is_file())


def main() -> None:
    print(json.dumps({"assets": derive()}, indent=1))


if __name__ == "__main__":
    main()
