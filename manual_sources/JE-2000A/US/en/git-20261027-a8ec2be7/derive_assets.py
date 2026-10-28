"""Derive the JE-2000A US en Web artwork from the frozen PDF.

Run from the repository root:

    python manual_sources/JE-2000A/US/en/git-20261027-a8ec2be7/derive_assets.py

``source/asset_recipe.json`` is the reviewed recipe. Panels are complete
3x renders of the source rectangle (leader lines, captions, frames and X marks
kept). ``omit_native_copy`` removes only outlined source copy that sits inside
a panel rectangle but is native HTML on the Web (a redaction on an in-memory
copy; the stored PDF is never written). LCD and troubleshooting icons are
8x renders of the native PDF glyph paths with the PDF's own transparency: the
page has no background object, so the PNG alpha channel is real and carries
no cell or page backdrop. The shared ``native_symbol_svg`` selector cannot map
this PDF (its SVG export holds clip paths outside ``<defs>``), so icons are
not SVG; the reviewed drawing indices are still checked on every run.

The manual has no safety-symbol table. Recipe ``symbols`` stays supported for
a later source revision: a symbol bound to an existing shared catalog variant
(``reuse``) is copied byte-identically; a new one is staged in the package
and as a proposed catalog row under ``--proposed-dir``; ``--write-shared``
adds it to the shared catalog only after operator approval. The symbol
admission rows of ``source_manifest.json`` are written from the same recipe.
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


class Drawings:
    """One get_drawings() pass per page: every page repeats the shared content stream."""

    def __init__(self, doc: fitz.Document) -> None:
        self.doc, self.cache = doc, {}

    def inside(self, page_number: int, bbox: list[float]) -> list[int]:
        if page_number not in self.cache:
            self.cache[page_number] = self.doc[page_number - 1].get_drawings()
        box = fitz.Rect(bbox)
        return [i for i, d in enumerate(self.cache[page_number]) if box.contains(d["rect"])]


def render_panel(pdf: Path, doc: fitz.Document, panel: dict, scale: fitz.Matrix) -> None:
    omissions = panel.get("omit_native_copy", [])
    if not omissions:
        page = doc[panel["physical_page"] - 1]
        page.get_pixmap(matrix=scale, clip=fitz.Rect(panel["bbox"]), alpha=False).save(PACKAGE / panel["path"])
        return
    with fitz.open(pdf) as scratch:
        page = scratch[panel["physical_page"] - 1]
        for omission in omissions:
            if not fitz.Rect(panel["bbox"]).intersects(fitz.Rect(omission["bbox"])):
                raise ValueError("omission outside its panel: " + panel["path"])
            page.add_redact_annot(fitz.Rect(omission["bbox"]), fill=False)
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,
                              graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED,
                              text=fitz.PDF_REDACT_TEXT_NONE)
        page.get_pixmap(matrix=scale, clip=fitz.Rect(panel["bbox"]), alpha=False).save(PACKAGE / panel["path"])


def caption_pixels(page: fitz.Page, bbox: list[float]) -> str:
    pixels = page.get_pixmap(matrix=fitz.Matrix(4, 4), clip=fitz.Rect(bbox), alpha=False)
    return sha256(pixels.tobytes("png"))


def symbol_rows(doc: fitz.Document, drawings: Drawings, recipe: dict, lines: dict, write_shared: bool,
                proposed: Path | None) -> list[dict]:
    rows = []
    for symbol in recipe["symbols"]:
        page = doc[symbol["physical_page"] - 1]
        indices = drawings.inside(symbol["physical_page"], symbol["glyph_bbox"])
        native = native_symbol_svg(page, indices, symbol["glyph_bbox"])
        shared = SHARED_SYMBOLS / symbol["shared_path"]
        if symbol.get("reuse"):
            data = shared.read_bytes()
        else:
            # New variant: staged in the package; the catalog is touched only on --write-shared.
            data = native
            if proposed is not None:
                proposed.mkdir(parents=True, exist_ok=True)
                (proposed / shared.name).write_bytes(native)
                (proposed / (shared.stem + ".row.json")).write_text(json.dumps(
                    {"key": symbol["shared_symbol_key"], "path": symbol["shared_path"], "sha256": sha256(native),
                     "source": {"pdf_sha256": recipe["source_sha256"], "physical_page": symbol["physical_page"],
                                "drawing_indices": indices, "glyph_bbox": symbol["glyph_bbox"]},
                     "status": "proposed-pending-operator-approval"}, indent=1) + "\n", encoding="utf-8")
            if write_shared and not shared.exists():
                shared.write_bytes(native)
            if shared.exists() and shared.read_bytes() != native:
                raise ValueError("shared native symbol differs from source paths: " + symbol["shared_path"])
        check = compare_symbol(data, Path(symbol["path"]).suffix, native)
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
    return rows


def derive(write_shared: bool = False, proposed: Path | None = None) -> dict:
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
    (assets / "icons").mkdir(parents=True)
    scale = fitz.Matrix(recipe["panel_scale"], recipe["panel_scale"])
    icon_scale = fitz.Matrix(recipe["icon_scale"], recipe["icon_scale"])
    with fitz.open(pdf) as doc:
        drawings = Drawings(doc)
        for panel in recipe["panels"]:
            render_panel(pdf, doc, panel, scale)
        for icon in recipe["native_icons"]:
            if drawings.inside(icon["physical_page"], icon["glyph_bbox"]) != icon["drawing_indices"]:
                raise ValueError("native icon drawing selection changed: " + icon["path"])
            page = doc[icon["physical_page"] - 1]
            pixmap = page.get_pixmap(matrix=icon_scale, clip=fitz.Rect(icon["glyph_bbox"]), alpha=True)
            alpha = pixmap.samples[3::4]
            if min(alpha) != 0 or not any(alpha):
                raise ValueError("icon has no transparent margin or no ink: " + icon["path"])
            pixmap.save(PACKAGE / icon["path"])
        rows = symbol_rows(doc, drawings, recipe, lines, write_shared, proposed)
    for item in recipe["reused"]:
        data = (ROOT / item["from"]).read_bytes()
        if sha256(data) != item["sha256"]:
            raise ValueError("reused asset changed: " + item["from"])
        (PACKAGE / item["path"]).write_bytes(data)
    return {"schema_version": SCHEMA, "locales": {LANGUAGE: rows}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write-shared", action="store_true",
                        help="add missing new native symbol variants to the shared catalog (operator-approved only)")
    parser.add_argument("--proposed-dir", type=Path, default=None,
                        help="also write staged new symbol variants and proposed catalog rows here")
    args = parser.parse_args()
    admission = derive(args.write_shared, args.proposed_dir)
    path = PACKAGE / "source_manifest.json"
    manifest = read(path)
    manifest["symbol_asset_admission"] = admission
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"assets": sorted(p.relative_to(PACKAGE).as_posix()
                                       for p in (PACKAGE / "assets").rglob("*") if p.is_file())}, indent=1))


if __name__ == "__main__":
    main()
