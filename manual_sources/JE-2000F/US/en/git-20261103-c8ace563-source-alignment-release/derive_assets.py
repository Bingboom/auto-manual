"""Derive the JE-2000F US en Web artwork from the frozen PDF and reused files.

Run from the repository root:

    python manual_sources/JE-2000F/US/en/git-20261028-c8ace563/derive_assets.py

``source/asset_recipe.json`` is the reviewed recipe. Panels are 3x renders of
the source rectangle (panel backgrounds, leader lines, labels and phone frames
kept). Where a panel also holds body copy, the recipe's ``strip`` rectangles
remove only the vector paths they fully cover (the copy and its text box) on an
in-memory copy of the page before rendering; that copy is native Web text and
the stored PDF is never written. Icons with no existing file within the fixed
2% comparison keep the original PDF vector paths through the shared
``native_symbol_svg`` selector (``native_icons``). ``compared_reuse`` rows are
existing files (same-model JP buttons and in-box art, LCD icons of earlier
packages, the shared FCC mark): each is copied byte-identically after a hash
check and must still pass the fixed comparison against this PDF's own glyph
paths. Safety symbols are byte copies of existing shared catalog variants that
pass the fixed symbol admission; no catalog file is added. The symbol admission
rows of ``source_manifest.json`` are written from the same recipe and the
reviewed transcription.
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


class Drawings:
    """One get_drawings() pass per page."""

    def __init__(self, doc: fitz.Document) -> None:
        self.doc, self.cache = doc, {}

    def inside(self, page_number: int, bbox: list[float]) -> list[int]:
        if page_number not in self.cache:
            self.cache[page_number] = self.doc[page_number - 1].get_drawings()
        box = fitz.Rect(bbox)
        return [i for i, d in enumerate(self.cache[page_number]) if box.contains(d["rect"])]

    def native(self, row: dict) -> bytes:
        indices = self.inside(row["physical_page"], row["glyph_bbox"])
        if indices != row["drawing_indices"]:
            raise ValueError("native drawing selection changed: " + row["path"])
        return native_symbol_svg(self.doc[row["physical_page"] - 1], indices, row["glyph_bbox"])


def caption_pixels(page: fitz.Page, bbox: list[float]) -> str:
    pixels = page.get_pixmap(matrix=fitz.Matrix(4, 4), clip=fitz.Rect(bbox), alpha=False)
    return sha256(pixels.tobytes("png"))


def render_panel(doc: fitz.Document, panel: dict, scale: fitz.Matrix) -> fitz.Pixmap:
    if not panel.get("strip"):
        return doc[panel["physical_page"] - 1].get_pixmap(matrix=scale, clip=fitz.Rect(panel["bbox"]), alpha=False)
    with fitz.open() as single:
        single.insert_pdf(doc, from_page=panel["physical_page"] - 1, to_page=panel["physical_page"] - 1)
        page = single[0]
        for rect in panel["strip"]:
            if not fitz.Rect(panel["bbox"]).contains(fitz.Rect(rect)):
                raise ValueError("strip outside its panel: " + panel["path"])
            page.add_redact_annot(fitz.Rect(rect), fill=False)
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, text=fitz.PDF_REDACT_TEXT_NONE,
                              graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED)
        return page.get_pixmap(matrix=scale, clip=fitz.Rect(panel["bbox"]), alpha=False)


def derive() -> tuple[dict, dict]:
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
    comparisons = {}
    with fitz.open(pdf) as doc:
        drawings = Drawings(doc)
        for panel in recipe["panels"]:
            render_panel(doc, panel, scale).save(PACKAGE / panel["path"])
        for icon in recipe["native_icons"]:
            (PACKAGE / icon["path"]).write_bytes(drawings.native(icon))
        for item in recipe["compared_reuse"]:
            data = (ROOT / item["from"]).read_bytes()
            if sha256(data) != item["sha256"]:
                raise ValueError("reused asset changed: " + item["from"])
            check = compare_symbol(data, Path(item["path"]).suffix, drawings.native(item))
            comparisons[item["path"]] = check["max_mean_channel_error"]
            (PACKAGE / item["path"]).write_bytes(data)
        rows = []
        for symbol in recipe["symbols"]:
            page = doc[symbol["physical_page"] - 1]
            indices = drawings.inside(symbol["physical_page"], symbol["glyph_bbox"])
            native = native_symbol_svg(page, indices, symbol["glyph_bbox"])
            data = (SHARED_SYMBOLS / symbol["shared_path"]).read_bytes()
            check = compare_symbol(data, Path(symbol["shared_path"]).suffix, native)
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
    return {"schema_version": SCHEMA, "locales": {"en": rows}}, comparisons


def main() -> None:
    admission, comparisons = derive()
    path = PACKAGE / "source_manifest.json"
    manifest = read(path)
    manifest["symbol_asset_admission"] = admission
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"assets": sorted(p.relative_to(PACKAGE).as_posix()
                                       for p in (PACKAGE / "assets").rglob("*") if p.is_file()),
                      "compared_reuse_max_mean_channel_error": comparisons}, indent=1))


if __name__ == "__main__":
    main()
