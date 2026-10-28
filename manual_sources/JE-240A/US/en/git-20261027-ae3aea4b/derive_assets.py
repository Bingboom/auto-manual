"""Derive the JE-240A US English Web artwork from the frozen PDF and reused shared files.

Run from the repository root:

    python manual_sources/JE-240A/US/en/git-20261027-ae3aea4b/derive_assets.py

``source/asset_recipe.json`` is the reviewed recipe. Panels are complete
3x renders of the source rectangle (leader lines, captions and phone frames
kept). The PDF is one outlined Illustrator artboard whose path stream the
shared native-SVG selector cannot map, so the four LCD glyphs without a shared
match are rendered from the same source rectangle with the page left
transparent (``alpha=True``): only the source glyph paints pixels, nothing is
repainted or keyed out. Reused files are copied byte-identically after a hash
check. The print has no symbol table.
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


def derive() -> None:
    recipe = read(PACKAGE / "source/asset_recipe.json")
    manifest = read(PACKAGE / "source_manifest.json")
    pdf = PACKAGE / manifest["original_source"]["filename"]
    if sha256(pdf.read_bytes()) != recipe["source_sha256"]:
        raise ValueError("authoritative PDF identity changed")
    assets = PACKAGE / "assets"
    if assets.exists():
        shutil.rmtree(assets)
    (assets / "shared-lcd").mkdir(parents=True)
    with fitz.open(pdf) as doc:
        scale = fitz.Matrix(recipe["panel_scale"], recipe["panel_scale"])
        for panel in recipe["panels"]:
            page = doc[panel["physical_page"] - 1]
            page.get_pixmap(matrix=scale, clip=fitz.Rect(panel["bbox"]), alpha=False).save(PACKAGE / panel["path"])
        scale = fitz.Matrix(recipe["icon_scale"], recipe["icon_scale"])
        for icon in recipe["transparent_icons"]:
            page = doc[icon["physical_page"] - 1]
            pixmap = page.get_pixmap(matrix=scale, clip=fitz.Rect(icon["bbox"]), alpha=True)
            border = [pixmap.pixel(x, y)[3] for x in range(pixmap.width) for y in (0, pixmap.height - 1)]
            if any(border):
                raise ValueError("icon rectangle cuts a source glyph or backdrop: " + icon["path"])
            pixmap.save(PACKAGE / icon["path"])
    for item in recipe["reused"]:
        data = (ROOT / item["from"]).read_bytes()
        if sha256(data) != item["sha256"]:
            raise ValueError("reused asset changed: " + item["from"])
        (PACKAGE / item["path"]).write_bytes(data)


def main() -> None:
    derive()
    print(json.dumps({"assets": sorted(p.relative_to(PACKAGE).as_posix()
                                       for p in (PACKAGE / "assets").rglob("*") if p.is_file())}, indent=1))


if __name__ == "__main__":
    main()
