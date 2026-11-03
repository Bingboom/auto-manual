"""Derive the JE-3000A JP Web artwork from the frozen PDF and reused repository files.

Run from the repository root:

    python manual_sources/JE-3000A/JP/ja/git-20261103-002fde5a/derive_assets.py

``source/asset_recipe.json`` is the reviewed recipe. Panels are complete 3x
renders of the source rectangle (frames, leader lines, captions and cross
marks kept). The Li-ion 20 mark is the original PDF vector paths: every
``get_drawings()`` path inside the reviewed glyph box, written with its own
fill/stroke and nothing else, so it carries no page or cell backdrop.

The shared ``native_symbol_svg`` selector cannot be used on this PDF: every
page carries the whole 23,397-path artboard, and MuPDF's whole-page SVG holds
fill/stroke pairs whose closures differ, so its drawing-to-path mapping
refuses every page ("native PDF fill/stroke SVG mapping is unsupported").
The same writer the JE-1500B US package uses (``drawing_svg``) is therefore
the reference for the fixed 2% comparison here; ``derive`` records the
selector's refusal verbatim in ``source_manifest.json:symbol_admission_blocker``.

Reused LCD files are copied byte-identically after a hash check and compared
with the vector paths they stand for at the fixed 2% tolerance. Safety
symbols bind existing shared variants only; nothing is written to the shared
catalog. A symbol with no admitted shared variant keeps the source's own
vector paths as a package-local file and is listed as pending.
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
from tools.web.symbol_asset_admission import SCHEMA, _symbol_error, compare_symbol  # noqa: E402

SHARED_SYMBOLS = ROOT / "docs/renderers/web/assets/shared/symbols"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _num(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _colour(rgb: tuple[float, ...]) -> str:
    return "#" + "".join(f"{round(max(0.0, min(1.0, c)) * 255):02x}" for c in rgb)


def _path_data(drawing: dict) -> str:
    out: list[str] = []
    end = None

    def move(point: fitz.Point) -> None:
        if end is None or abs(point.x - end.x) > 1e-3 or abs(point.y - end.y) > 1e-3:
            out.append(f"M{_num(point.x)} {_num(point.y)}")

    for item in drawing["items"]:
        kind = item[0]
        if kind == "l":
            move(item[1])
            out.append(f"L{_num(item[2].x)} {_num(item[2].y)}")
            end = item[2]
        elif kind == "c":
            move(item[1])
            out.append("C" + " ".join(f"{_num(p.x)} {_num(p.y)}" for p in item[2:5]))
            end = item[4]
        elif kind == "re":
            rect = item[1]
            out.append(f"M{_num(rect.x0)} {_num(rect.y0)}H{_num(rect.x1)}V{_num(rect.y1)}H{_num(rect.x0)}Z")
            end = None
        elif kind == "qu":
            quad = item[1]
            out.append("M" + "L".join(f"{_num(p.x)} {_num(p.y)}" for p in (quad.ul, quad.ur, quad.lr, quad.ll)) + "Z")
            end = None
        else:
            raise ValueError("unsupported PDF drawing item: " + kind)
    if drawing.get("closePath"):
        out.append("Z")
    return "".join(out)


def drawing_svg(page: fitz.Page, indices: list[int], bbox: list[float]) -> bytes:
    """Write the original vector paths inside ``bbox``; the selection must be complete."""
    drawings = page.get_drawings()
    box = fitz.Rect(bbox)
    if box.is_empty or not page.rect.contains(box):
        raise ValueError("glyph bounds outside source page")
    inside = [i for i, d in enumerate(drawings) if box.contains(d["rect"])]
    if not indices or indices != inside:
        raise ValueError("glyph selection must include every drawing inside its bounds")
    parts = []
    for index in indices:
        drawing = drawings[index]
        attrs = {"d": _path_data(drawing), "fill": "none"}
        if drawing["type"] in ("f", "fs") and drawing.get("fill") is not None:
            attrs["fill"] = _colour(drawing["fill"])
            if drawing.get("fill_opacity", 1) != 1:
                attrs["fill-opacity"] = _num(drawing["fill_opacity"])
            if drawing.get("even_odd"):
                attrs["fill-rule"] = "evenodd"
        if drawing["type"] in ("s", "fs") and drawing.get("color") is not None:
            attrs["stroke"] = _colour(drawing["color"])
            attrs["stroke-width"] = _num(drawing.get("width") or 1)
            if drawing.get("stroke_opacity", 1) != 1:
                attrs["stroke-opacity"] = _num(drawing["stroke_opacity"])
            caps = drawing.get("lineCap") or (0,)
            attrs["stroke-linecap"] = ("butt", "round", "square")[int(caps[0])]
            attrs["stroke-linejoin"] = ("miter", "round", "bevel")[int(drawing.get("lineJoin") or 0)]
        parts.append("<path " + " ".join(f'{key}="{value}"' for key, value in attrs.items()) + "/>")
    return ('<?xml version="1.0" encoding="utf-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="{_num(box.x0)} {_num(box.y0)} {_num(box.width)} {_num(box.height)}" '
            f'width="{_num(box.width)}" height="{_num(box.height)}">' + "".join(parts) + "</svg>\n").encode()


def selection(page: fitz.Page, bbox: list[float]) -> list[int]:
    box = fitz.Rect(bbox)
    return [i for i, d in enumerate(page.get_drawings()) if box.contains(d["rect"])]


def caption_pixels(page: fitz.Page, bbox: list[float]) -> str:
    pixels = page.get_pixmap(matrix=fitz.Matrix(4, 4), clip=fitz.Rect(bbox), alpha=False)
    return sha256(pixels.tobytes("png"))


def selector_refusal(page: fitz.Page, bbox: list[float]) -> str:
    """The shared selector's verdict on this page, recorded verbatim."""
    try:
        native_symbol_svg(page, selection(page, bbox), bbox)
    except ValueError as exc:
        return str(exc)
    return ""


def derive() -> tuple[dict, dict, dict]:
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
    reuse_checks: dict[str, list[dict]] = {}
    rows, pending = [], []
    with fitz.open(pdf) as doc:
        for panel in recipe["panels"]:
            page = doc[panel["physical_page"] - 1]
            page.get_pixmap(matrix=scale, clip=fitz.Rect(panel["bbox"]), alpha=False).save(PACKAGE / panel["path"])
        for icon in recipe["native_icons"]:
            svg = drawing_svg(doc[icon["physical_page"] - 1], icon["drawing_indices"], icon["glyph_bbox"])
            (PACKAGE / icon["path"]).write_bytes(svg)
        for item in recipe["reused"]:
            data = (ROOT / item["from"]).read_bytes()
            if sha256(data) != item["sha256"]:
                raise ValueError("reused asset changed: " + item["from"])
            checks = []
            for check in [item["source_check"], *item.get("also_checks", [])]:
                native = drawing_svg(doc[check["physical_page"] - 1], check["drawing_indices"], check["glyph_bbox"])
                checks.append(compare_symbol(data, Path(item["from"]).suffix, native))
            reuse_checks[item["path"]] = checks
            (PACKAGE / item["path"]).write_bytes(data)
        blocker = {}
        for symbol in recipe["symbols"]:
            page = doc[symbol["physical_page"] - 1]
            indices = selection(page, symbol["glyph_bbox"])
            native = drawing_svg(page, indices, symbol["glyph_bbox"])
            refusal = selector_refusal(page, symbol["glyph_bbox"])
            if refusal:
                blocker.setdefault(refusal, []).append(symbol["path"])
            glyph, caption = fitz.Rect(symbol["glyph_bbox"]), fitz.Rect(symbol["caption_bbox"])
            band = glyph | caption
            row = {
                "asset_ref": symbol["path"], "physical_page": symbol["physical_page"], "drawing_indices": indices,
                "glyph_bbox": symbol["glyph_bbox"], "caption_bbox": symbol["caption_bbox"],
                "row_bbox": [band.x0 - 1, band.y0 - 1, band.x1 + 1, band.y1 + 1],
                "caption_text": lines[symbol["caption_id"]],
                "caption_sha256": caption_pixels(page, symbol["caption_bbox"]),
            }
            if symbol["shared_symbol_key"]:
                data = (SHARED_SYMBOLS / symbol["shared_path"]).read_bytes()
                check = compare_symbol(data, Path(symbol["shared_path"]).suffix, native)
                row.update(asset_sha256=sha256(data), shared_symbol_key=symbol["shared_symbol_key"], **check)
                rows.append(row)
            else:
                data = native
                closest = min((_symbol_error(p.read_bytes(), p.suffix, native), p.name)
                              for p in sorted((SHARED_SYMBOLS / "native-v1").glob("*.svg")))
                row.update(asset_sha256=sha256(data), shared_symbol_key=None,
                           closest_shared_file=closest[1], closest_mean_channel_error=round(closest[0], 6),
                           pending=symbol["pending"])
                pending.append(row)
                rows.append(row)
            (PACKAGE / symbol["path"]).write_bytes(data)
    print(json.dumps({"reuse_checks": reuse_checks}, indent=1))
    admission = {"schema_version": SCHEMA, "locales": {"ja": rows}}
    blocker_record = {
        "status": "pending-coordinator",
        "selector": "tools.asset_pipeline.native_svg.native_symbol_svg (used by tools.web.symbol_asset_admission)",
        "refusals": [{"message": message, "rows": paths} for message, paths in blocker.items()],
        "local_reference": "derive_assets.drawing_svg (original get_drawings() paths, fixed 2% compare_symbol)",
        "pending_rows": [row["asset_ref"] for row in pending],
    }
    return admission, blocker_record, reuse_checks


def main() -> None:
    admission, blocker, _ = derive()
    path = PACKAGE / "source_manifest.json"
    manifest = read(path)
    manifest["symbol_asset_admission"] = admission
    manifest["symbol_admission_blocker"] = blocker
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"assets": sorted(p.relative_to(PACKAGE).as_posix()
                                       for p in (PACKAGE / "assets").rglob("*") if p.is_file()),
                      "blocker": blocker}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
