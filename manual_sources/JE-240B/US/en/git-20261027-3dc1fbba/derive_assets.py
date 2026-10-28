"""Derive the JE-240B US English Web artwork from the frozen PDF and reused shared files.

Run from the repository root:

    python manual_sources/JE-240B/US/en/git-20261027-3dc1fbba/derive_assets.py

``source/asset_recipe.json`` is the reviewed recipe. ``panels`` are complete
3x renders of the source rectangle (panel backgrounds, leader lines and
captions kept). ``redacted_panels`` are the same complete renders after
removing only the line art lying entirely inside their ``omit`` rectangles
(printed text pills whose copy is native Web text) from an in-memory copy of
the PDF. ``lcd_icons`` are rasterised from the source vector drawings inside
the glyph box only, with their clip groups, on a transparent background.
Nothing is repainted. Reused files are copied
byte-identically after a hash check, symbols from the shared catalog.

This PDF is a single-artboard export: an off-page path closes one subpath with
``Z`` and its fill/stroke twin with an explicit line to the origin, which the
shared ``native_symbol_svg`` maps since PR #1632. Symbol admission rows carry
the measured comparison against those native paths.
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


def _f(value: float) -> str:
    return f"{value:.4f}"


def _path_ops(drawing: dict) -> list[str]:
    """PDF path operators for one get_drawings(extended=True) record, subpaths kept."""
    ops: list[str] = []
    last = None
    for item in drawing.get("items", []):
        op = item[0]
        if op == "re":
            r = item[1]
            ops.append(f"{_f(r.x0)} {_f(r.y0)} {_f(r.width)} {_f(r.height)} re")
            last = None
            continue
        if op == "qu":
            q = item[1]
            points = [q.ul, q.ur, q.lr, q.ll]
            ops.append(f"{_f(points[0].x)} {_f(points[0].y)} m "
                       + " ".join(f"{_f(p.x)} {_f(p.y)} l" for p in points[1:]) + " h")
            last = None
            continue
        start = item[1]
        if last is None or abs(start.x - last.x) > 1e-4 or abs(start.y - last.y) > 1e-4:
            if last is not None and drawing.get("closePath"):
                ops.append("h")
            ops.append(f"{_f(start.x)} {_f(start.y)} m")
        if op == "l":
            ops.append(f"{_f(item[2].x)} {_f(item[2].y)} l")
            last = item[2]
        elif op == "c":
            ops.append(" ".join(f"{_f(p.x)} {_f(p.y)}" for p in item[2:5]) + " c")
            last = item[4]
        else:
            raise ValueError("unsupported source drawing item: " + op)
    if drawing.get("closePath"):
        ops.append("h")
    return ops


def source_drawings_png(page: fitz.Page, drawings: list[dict], bbox: list[float],
                        scale: float) -> tuple[bytes, int]:
    """Rasterise only the source drawings inside bbox, with their clips, on a transparent page."""
    box = fitz.Rect(bbox)
    selected = []
    for drawing in drawings:
        if drawing["type"] not in ("f", "s", "fs", "clip"):
            continue
        rect = fitz.Rect(drawing["scissor"] if drawing["type"] == "clip" else drawing["rect"])
        if box.contains(rect):
            selected.append(drawing)
    out = fitz.open()
    target = out.new_page(width=page.rect.width, height=page.rect.height)
    stream = [f"1 0 0 -1 0 {_f(page.rect.height)} cm"]
    open_clips: list[int] = []
    for drawing in selected:
        level = drawing.get("level", 0)
        while open_clips and open_clips[-1] >= level:
            stream.append("Q")
            open_clips.pop()
        if drawing["type"] == "clip":
            stream += ["q", *_path_ops(drawing), ("W*" if drawing.get("even_odd") else "W") + " n"]
            open_clips.append(level)
            continue
        if drawing.get("fill_opacity", 1) not in (None, 1) or drawing.get("stroke_opacity", 1) not in (None, 1):
            raise ValueError("transparent source drawing is not supported")
        stream.append("q")
        if drawing.get("fill"):
            stream.append(" ".join(_f(c) for c in drawing["fill"]) + " rg")
        if drawing.get("color"):
            stream.append(" ".join(_f(c) for c in drawing["color"]) + " RG")
        if drawing.get("width"):
            stream.append(f"{_f(drawing['width'])} w")
        stream += _path_ops(drawing)
        even = drawing.get("even_odd")
        stream += [{"f": "f*" if even else "f", "s": "S", "fs": "B*" if even else "B"}[drawing["type"]], "Q"]
    stream += ["Q"] * len(open_clips)
    xref = out.get_new_xref()
    out.update_object(xref, "<<>>")
    out.update_stream(xref, "\n".join(stream).encode())
    target.set_contents(xref)
    pixmap = target.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=True, clip=box)
    return pixmap.tobytes("png"), len(selected)


def caption_pixels(page: fitz.Page, bbox: list[float]) -> str:
    pixels = page.get_pixmap(matrix=fitz.Matrix(4, 4), clip=fitz.Rect(bbox), alpha=False)
    return sha256(pixels.tobytes("png"))


def derive() -> dict:
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
    with fitz.open(pdf) as doc:
        extended: dict[int, list[dict]] = {}

        def drawings_of(number: int) -> list[dict]:
            if number not in extended:
                extended[number] = doc[number - 1].get_drawings(extended=True)
            return extended[number]

        for panel in recipe["panels"]:
            page = doc[panel["physical_page"] - 1]
            page.get_pixmap(matrix=scale, clip=fitz.Rect(panel["bbox"]), alpha=False).save(PACKAGE / panel["path"])
        with fitz.open(pdf) as edited:
            for panel in recipe["redacted_panels"]:
                page = edited[panel["physical_page"] - 1]
                for rect in panel["omit"]:
                    page.add_redact_annot(fitz.Rect(rect), fill=False)
                page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, text=fitz.PDF_REDACT_TEXT_NONE,
                                      graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED)
                page.get_pixmap(matrix=scale, clip=fitz.Rect(panel["bbox"]), alpha=False).save(PACKAGE / panel["path"])
        for icon in recipe["lcd_icons"]:
            number = icon["physical_page"]
            data, count = source_drawings_png(doc[number - 1], drawings_of(number), icon["glyph_bbox"], 8)
            if not count:
                raise ValueError("LCD icon box holds no source drawing: " + icon["path"])
            (PACKAGE / icon["path"]).write_bytes(data)
        rows = []
        plain: dict[int, list[dict]] = {}
        for symbol in recipe["symbols"]:
            page = doc[symbol["physical_page"] - 1]
            box = fitz.Rect(symbol["glyph_bbox"])
            if symbol["physical_page"] not in plain:
                plain[symbol["physical_page"]] = page.get_drawings()
            indices = [i for i, d in enumerate(plain[symbol["physical_page"]]) if box.contains(d["rect"])]
            data = (SHARED_SYMBOLS / symbol["shared_path"]).read_bytes()
            check = compare_symbol(data, Path(symbol["shared_path"]).suffix,
                                   native_symbol_svg(page, indices, symbol["glyph_bbox"]))
            (PACKAGE / symbol["path"]).write_bytes(data)
            glyph, caption = box, fitz.Rect(symbol["caption_bbox"])
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
    admission = derive()
    path = PACKAGE / "source_manifest.json"
    manifest = read(path)
    manifest["symbol_asset_admission"] = admission
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"assets": sorted(p.relative_to(PACKAGE).as_posix()
                                       for p in (PACKAGE / "assets").rglob("*") if p.is_file())}, indent=1))


if __name__ == "__main__":
    main()
