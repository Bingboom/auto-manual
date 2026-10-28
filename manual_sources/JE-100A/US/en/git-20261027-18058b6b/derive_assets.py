"""Derive the JE-100A US English Web artwork from the frozen PDF and reused shared files.

Run from the repository root:

    python manual_sources/JE-100A/US/en/git-20261027-18058b6b/derive_assets.py

``source/asset_recipe.json`` is the reviewed recipe. Panels are complete
3x renders of the source rectangle (leader lines and captions kept). The PDF is
one outlined Illustrator artboard whose paths the shared native-SVG selector
cannot map, so the small LCD icons are 6x renders of the glyph rectangle with a
real alpha channel: the page draws no background there, so only the glyph's own
paths are painted and nothing is keyed out or repainted. Reused files are copied
byte-identically after a hash check.
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


def transparent_icon(page: fitz.Page, bbox: list[float], scale: float) -> fitz.Pixmap:
    pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=fitz.Rect(bbox), alpha=True)
    alpha = pixmap.samples[3::4]
    w, h = pixmap.width, pixmap.height
    border = [alpha[x] for x in range(w)] + [alpha[(h - 1) * w + x] for x in range(w)]
    border += [alpha[y * w] for y in range(h)] + [alpha[y * w + w - 1] for y in range(h)]
    if max(border) > 8 or min(alpha) != 0:
        raise ValueError("icon rectangle is not on a transparent page area: " + str(bbox))
    return pixmap


def derive() -> list[str]:
    recipe = read(PACKAGE / "source/asset_recipe.json")
    manifest = read(PACKAGE / "source_manifest.json")
    pdf = PACKAGE / manifest["original_source"]["filename"]
    if sha256(pdf.read_bytes()) != recipe["source_sha256"]:
        raise ValueError("authoritative PDF identity changed")
    assets = PACKAGE / "assets"
    if assets.exists():
        shutil.rmtree(assets)
    (assets / "shared-lcd").mkdir(parents=True)
    scale = fitz.Matrix(recipe["panel_scale"], recipe["panel_scale"])
    with fitz.open(pdf) as doc:
        for panel in recipe["panels"]:
            page = doc[panel["physical_page"] - 1]
            page.get_pixmap(matrix=scale, clip=fitz.Rect(panel["bbox"]), alpha=False).save(PACKAGE / panel["path"])
        for icon in recipe["alpha_icons"]:
            transparent_icon(doc[icon["physical_page"] - 1], icon["bbox"], recipe["icon_scale"]).save(PACKAGE / icon["path"])
    for item in recipe["reused"]:
        data = (ROOT / item["from"]).read_bytes()
        if sha256(data) != item["sha256"]:
            raise ValueError("reused asset changed: " + item["from"])
        (PACKAGE / item["path"]).write_bytes(data)
    return sorted(p.relative_to(PACKAGE).as_posix() for p in assets.rglob("*") if p.is_file())


if __name__ == "__main__":
    print(json.dumps({"assets": derive()}, indent=1))
