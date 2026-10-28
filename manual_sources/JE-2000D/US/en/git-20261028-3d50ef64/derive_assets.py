"""Derive the JE-2000D US en Web artwork from the frozen PDF and reused files.

Run from the repository root:

    python manual_sources/JE-2000D/US/en/git-20261028-3d50ef64/derive_assets.py

``source/asset_recipe.json`` is the reviewed recipe. The PDF is outlined (no
text layer). New panels are complete 3x renders of the source rectangle
(leader lines, captions and frames kept); ``omit_native_copy`` removes only
outlined source copy that sits inside a panel rectangle but is native HTML on
the Web (line art fully covered by the rectangle is removed from an in-memory
copy; the stored PDF is never written). ``reused_panels`` are complete panels
of the same-generation JE-1000D US package whose art is the same as this
source: each is copied byte-identically after a hash check and compared with a
3x render of this PDF's rectangle (mean channel error at ``panel_tolerance``).
``reused`` glyphs (LCD icons, certification marks) are copied byte-identically
and compared with the native PDF paths they stand for at the fixed symbol
tolerance. ``native_icons`` keep the original PDF vector paths through the
shared ``native_symbol_svg`` selector. Every comparison is recorded in
``source_manifest.json:artwork_reuse_comparison``.

The printed manual has no symbol table, so ``recipe["symbols"]`` is empty and
the symbol admission written to the manifest has no rows. ``--write-shared``
is kept from the precedent so a later source with a symbol table uses the
same path; it must not be used without operator approval.
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
    # A fresh in-memory copy per panel: omissions never touch the stored PDF.
    with fitz.open(pdf) as doc:
        page = doc[panel["physical_page"] - 1]
        omissions = panel.get("omit_native_copy", [])
        for omission in omissions:
            if not fitz.Rect(panel["bbox"]).intersects(fitz.Rect(omission["bbox"])):
                raise ValueError("omission outside its panel: " + panel["path"])
            page.add_redact_annot(fitz.Rect(omission["bbox"]), fill=False)
        if omissions:
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,
                                  graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED,
                                  text=fitz.PDF_REDACT_TEXT_NONE)
        for edge in panel.get("mask_foreign_edge", []):
            # A neighbouring panel's stroke that only grazes this rectangle's edge is painted
            # over with the page white (the page has no background object).
            if not fitz.Rect(panel["bbox"]).intersects(fitz.Rect(edge["bbox"])):
                raise ValueError("edge mask outside its panel: " + panel["path"])
            page.draw_rect(fitz.Rect(edge["bbox"]), color=None, fill=(1, 1, 1), overlay=True)
        return page.get_pixmap(matrix=scale, clip=fitz.Rect(panel["bbox"]), alpha=False)


def panel_error(pixmap: fitz.Pixmap, data: bytes) -> float:
    """Mean channel error (0-1) between a source rectangle render and a reused panel file."""
    reused = fitz.Pixmap(data)
    if reused.alpha:
        reused = fitz.Pixmap(reused, 0)
    if (reused.width, reused.height, reused.n) != (pixmap.width, pixmap.height, pixmap.n):
        raise ValueError("reused panel size differs from the source rectangle render")
    total = sum(abs(a - b) for a, b in zip(pixmap.samples, reused.samples, strict=True))
    return round(total / (len(pixmap.samples) * 255), 6)


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
    for item in recipe["reused_panels"]:
        data = (ROOT / item["from"]).read_bytes()
        if sha256(data) != item["sha256"]:
            raise ValueError("reused panel changed: " + item["from"])
        error = panel_error(render_panel(pdf, item, scale), data)
        if error > recipe["panel_tolerance"]:
            raise ValueError("reused panel differs from the source rectangle: " + item["path"])
        (PACKAGE / item["path"]).write_bytes(data)
        reuse.append({"asset_ref": item["path"], "from": item["from"], "sha256": item["sha256"],
                      "physical_page": item["physical_page"], "bbox": item["bbox"], "comparison": "panel-render",
                      "max_mean_channel_error": error})
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
                              "drawing_indices": indices, "comparison": "native-glyph", **check})
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
