"""Derive the JE-1000D US Web artwork from the frozen PDF and reused shared files.

Run from the repository root:

    python manual_sources/JE-1000D/US/en/git-20261027-10d15090/derive_assets.py

``source/asset_recipe.json`` is the reviewed recipe. Panels are complete
3x renders of the source rectangle (leader lines, captions and phone frames
kept); where an adjacent heading's text falls inside a panel rectangle, the
recipe lists its rectangle under ``redact_text`` and only that text is
removed from an in-memory copy of the page (art untouched). Native icons
keep the original PDF vector paths through the shared ``native_symbol_svg``
selector, so they carry no page or cell backdrop. Reused files are copied
byte-identically after a hash check, and each is compared once more with the
native PDF paths it stands for at the fixed symbol tolerance; the comparison
is recorded in ``source_manifest.json:artwork_reuse_comparison``.

The printed manual has no symbol table, so ``recipe["symbols"]`` is empty and
the symbol admission written to the manifest has no rows. The symbol branch
and ``--write-shared`` (add a missing catalog file once; every other run only
verifies it) are kept from the JE-1000D JP edition so a later source with a
symbol table uses the same path.
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
LANGUAGE = "en"


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


def render_panel(pdf: Path, panel: dict, scale: fitz.Matrix) -> fitz.Pixmap:
    # A fresh in-memory copy per panel: redactions never touch the stored PDF.
    with fitz.open(pdf) as doc:
        page = doc[panel["physical_page"] - 1]
        if panel.get("redact_text"):
            for rect in panel["redact_text"]:
                page.add_redact_annot(fitz.Rect(rect))
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,
                                  graphics=fitz.PDF_REDACT_LINE_ART_NONE)
        return page.get_pixmap(matrix=scale, clip=fitz.Rect(panel["bbox"]), alpha=False)


def derive(write_shared: bool = False) -> tuple[dict, list[dict]]:
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
    scale = fitz.Matrix(recipe["panel_scale"], recipe["panel_scale"])
    for panel in recipe["panels"]:
        render_panel(pdf, panel, scale).save(PACKAGE / panel["path"])
    rows, reuse = [], []
    with fitz.open(pdf) as doc:
        for icon in recipe["native_icons"]:
            svg, indices = native_svg(doc[icon["physical_page"] - 1], icon["glyph_bbox"])
            if indices != icon["drawing_indices"]:
                raise ValueError("native icon drawing selection changed: " + icon["path"])
            (PACKAGE / icon["path"]).write_bytes(svg)
        for item in recipe["reused"]:
            data = (ROOT / item["from"]).read_bytes()
            if sha256(data) != item["sha256"]:
                raise ValueError("reused asset changed: " + item["from"])
            (PACKAGE / item["path"]).write_bytes(data)
            for bound in (item, item.get("also_bound")):
                if not bound:
                    continue
                native, indices = native_svg(doc[bound["physical_page"] - 1], bound["glyph_bbox"])
                check = compare_symbol(data, Path(item["path"]).suffix, native)
                reuse.append({"asset_ref": item["path"], "from": item["from"], "sha256": item["sha256"],
                              "physical_page": bound["physical_page"], "glyph_bbox": bound["glyph_bbox"],
                              "drawing_indices": indices, **check})
        for symbol in recipe["symbols"]:
            page = doc[symbol["physical_page"] - 1]
            native, indices = native_svg(page, symbol["glyph_bbox"])
            shared = SHARED_SYMBOLS / symbol["shared_path"]
            if not symbol.get("reuse"):
                if write_shared and not shared.exists():
                    shared.write_bytes(native)
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
                "caption_text": lines[symbol["caption_id"]],
                "caption_sha256": caption_pixels(page, symbol["caption_bbox"]),
                "shared_symbol_key": symbol["shared_symbol_key"], **check,
            })
    return {"schema_version": SCHEMA, "locales": {LANGUAGE: rows}}, reuse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-shared", action="store_true",
                        help="add missing new native symbol variants to the shared catalog")
    admission, reuse = derive(parser.parse_args().write_shared)
    path = PACKAGE / "source_manifest.json"
    manifest = read(path)
    manifest["symbol_asset_admission"] = admission
    manifest["artwork_reuse_comparison"] = reuse
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"assets": sorted(p.relative_to(PACKAGE).as_posix()
                                       for p in (PACKAGE / "assets").rglob("*") if p.is_file()),
                      "reuse": [(r["asset_ref"], r["max_mean_channel_error"]) for r in reuse]}, indent=1))


if __name__ == "__main__":
    main()
