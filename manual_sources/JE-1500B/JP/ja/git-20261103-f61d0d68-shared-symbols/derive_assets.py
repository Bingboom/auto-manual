"""Derive the JE-1500B JP Web artwork from the frozen PDF and reused repository files.

Run from the repository root:

    python manual_sources/JE-1500B/JP/ja/git-20261103-f61d0d68-shared-symbols/derive_assets.py

``source/asset_recipe.json`` is the reviewed recipe. Panels are complete
3x renders of the source rectangle (leader lines, captions, frames and X
marks kept). Two panels share their rectangle with a native text line (the
chapter title beside the overview detail circle, the last body line beside
the SolarSaga 80 label); the recipe names those glyph areas as ``masks`` and
they are painted white, so no body text is duplicated as an image. The new
icons are the original PDF vector paths: every ``get_drawings()`` path inside
the reviewed glyph box, written with its own fill/stroke and nothing else, so
they carry no page or cell backdrop (the LCD icons and the Li-ion 20 mark keep
the direct path writer of the released git-20261103-f61d0d68 version, so their
bytes are unchanged). Reused files are copied byte-identically after a hash
check, and each LCD icon is compared with the vector paths it stands for at the
fixed 2% symbol tolerance.

The printed 絵表示の説明 symbol table binds each row to the canonical of its
operator-confirmed shared symbol group (``docs/renderers/web/assets/shared/
symbols/manifest.json:canonical_groups``). The shared catalog file is copied
byte-identically; the shared ``native_symbol_svg`` selector (fixed in #1659)
rebuilds the row's source reference, and the measured difference is recorded.
Symbol admission in ``rebuild.py`` releases a confirmed group's canonical for a
row whose source-verified caption the group lists. Nothing is written to the
shared library.
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
from tools.web.shared_symbol_assets import canonical_groups, shared_symbol_file  # noqa: E402
from tools.web.symbol_asset_admission import SCHEMA, _symbol_error, compare_symbol  # noqa: E402

LANGUAGE = "ja"


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


def panel_png(page: fitz.Page, panel: dict, scale: fitz.Matrix) -> bytes:
    """Complete source rectangle; reviewed masks blank a neighbouring native text line."""
    pixmap = page.get_pixmap(matrix=scale, clip=fitz.Rect(panel["bbox"]), alpha=False)
    for mask in panel.get("masks", []):
        area = (fitz.Rect(mask) * scale).irect & pixmap.irect
        if area.is_empty:
            raise ValueError("panel mask outside its panel: " + panel["path"])
        pixmap.set_rect(area, (255, 255, 255))
    return pixmap.tobytes("png")


def derive() -> dict:
    recipe = read(PACKAGE / "source/asset_recipe.json")
    manifest = read(PACKAGE / "source_manifest.json")
    pdf = PACKAGE / manifest["original_source"]["filename"]
    if sha256(pdf.read_bytes()) != recipe["source_sha256"]:
        raise ValueError("authoritative PDF identity changed")
    lines = {line["id"]: line["text"] for page in read(PACKAGE / "source/transcription.json")["pages"]
             for line in page["lines"]}
    groups = canonical_groups()
    assets = PACKAGE / "assets"
    if assets.exists():
        shutil.rmtree(assets)
    assets.mkdir()
    scale = fitz.Matrix(recipe["panel_scale"], recipe["panel_scale"])
    reuse_checks = {}
    with fitz.open(pdf) as doc:
        for panel in recipe["panels"]:
            (PACKAGE / panel["path"]).write_bytes(panel_png(doc[panel["physical_page"] - 1], panel, scale))
        for icon in recipe["native_icons"]:
            svg = drawing_svg(doc[icon["physical_page"] - 1], icon["drawing_indices"], icon["glyph_bbox"])
            (PACKAGE / icon["path"]).write_bytes(svg)
        for item in recipe["reused"]:
            data = (ROOT / item["from"]).read_bytes()
            if sha256(data) != item["sha256"]:
                raise ValueError("reused asset changed: " + item["from"])
            check = item["source_check"]
            native = drawing_svg(doc[check["physical_page"] - 1], check["drawing_indices"], check["glyph_bbox"])
            reuse_checks[item["path"]] = compare_symbol(data, Path(item["from"]).suffix, native)
            (PACKAGE / item["path"]).write_bytes(data)
        rows = []
        for symbol in recipe["symbols"]:
            group, role = groups[symbol["shared_symbol_key"]]
            if (group["id"], role, group["status"]) != (symbol["canonical_group"], "canonical", "operator-confirmed"):
                raise ValueError("symbol row must bind its confirmed group's canonical: " + symbol["path"])
            shared = shared_symbol_file(symbol["shared_symbol_key"])
            if shared.relative_to(shared.parents[1]).as_posix() != symbol["shared_path"]:
                raise ValueError("shared symbol path changed: " + symbol["shared_symbol_key"])
            page = doc[symbol["physical_page"] - 1]
            reference = native_symbol_svg(page, symbol["drawing_indices"], symbol["glyph_bbox"])
            data = shared.read_bytes()
            (PACKAGE / symbol["path"]).write_bytes(data)
            glyph, caption = fitz.Rect(symbol["glyph_bbox"]), fitz.Rect(symbol["caption_bbox"])
            band = glyph | caption
            pixels = page.get_pixmap(matrix=fitz.Matrix(4, 4), clip=caption, alpha=False)
            rows.append({
                "asset_ref": symbol["path"], "asset_sha256": sha256(data),
                "physical_page": symbol["physical_page"], "drawing_indices": symbol["drawing_indices"],
                "glyph_bbox": symbol["glyph_bbox"], "caption_bbox": symbol["caption_bbox"],
                "row_bbox": [band.x0 - 1, band.y0 - 1, band.x1 + 1, band.y1 + 1],
                "caption_text": lines[symbol["caption_id"]],
                "caption_sha256": sha256(pixels.tobytes("png")),
                "shared_symbol_key": symbol["shared_symbol_key"],
                "canonical_group": group["id"], "canonical_decision": group["decision"],
                "max_mean_channel_error": round(_symbol_error(data, shared.suffix, reference), 6),
            })
    print(json.dumps({"reuse_checks": reuse_checks,
                      "symbols": {r["asset_ref"]: [r["canonical_group"], r["max_mean_channel_error"]] for r in rows}}))
    return {"schema_version": SCHEMA, "locales": {LANGUAGE: rows}}


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
