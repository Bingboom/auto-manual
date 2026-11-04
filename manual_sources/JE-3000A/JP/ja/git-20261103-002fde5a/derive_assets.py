"""Derive the JE-3000A JP Web artwork from the frozen PDF and reused repository files.

Run from the repository root:

    python manual_sources/JE-3000A/JP/ja/git-20261103-002fde5a/derive_assets.py

``source/asset_recipe.json`` is the reviewed recipe. Panels are complete 3x
renders of the source rectangle (frames, leader lines, captions and cross
marks kept). ``native_icons`` keep the original PDF vector paths through the
shared ``native_symbol_svg`` selector (no page or cell backdrop).

``reused`` LCD glyphs are copied byte-identically from approved packages after
a hash check, and only when the fixed 2% glyph comparison against this PDF's
native paths passes. Safety symbols reuse shared-catalog variants; each row
passes the fixed 2% comparison, or, for the canonical of an operator-confirmed
canonical group, is admitted through the group's registered caption exactly as
``tools.web.symbol_asset_admission`` does. This script never writes the shared
catalog. The symbol admission rows and the reuse comparison rows of
``source_manifest.json`` are written from the same recipe and the reviewed
transcription.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import xml.etree.ElementTree as ET

import fitz

PACKAGE = Path(__file__).resolve().parent
ROOT = next(parent for parent in PACKAGE.parents if (parent / "build.py").is_file())
sys.path.insert(0, str(ROOT))

from tools.asset_pipeline.native_svg import native_symbol_svg  # noqa: E402
from tools.web.shared_symbol_assets import canonical_groups  # noqa: E402
from tools.web.symbol_asset_admission import SCHEMA, _canonical_release, compare_symbol  # noqa: E402

SHARED_SYMBOLS = ROOT / "docs/renderers/web/assets/shared/symbols"
SVG = "{http://www.w3.org/2000/svg}"
ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
ET.register_namespace("inkscape", "http://www.inkscape.org/namespaces/inkscape")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def prune_unused_definitions(svg: bytes) -> bytes:
    """Drop page-wide <defs> entries that no retained path references."""
    root = ET.fromstring(svg)
    defs = list(root.iter(SVG + "defs"))
    pattern = re.compile(r"url\(#([^)]+)\)")

    def references(node: ET.Element) -> set[str]:
        found: set[str] = set()
        for element in node.iter():
            for key, value in element.attrib.items():
                found.update(pattern.findall(value))
                if key.endswith("href") and value.startswith("#"):
                    found.add(value[1:])
        return found

    body = ET.Element("body")
    body.extend(child for child in root if child.tag != SVG + "defs")
    wanted = references(body)
    by_id = {child.get("id"): child for d in defs for child in d if child.get("id")}
    pending = list(wanted)
    while pending:
        node = by_id.get(pending.pop())
        if node is not None:
            for ref in references(node) - wanted:
                wanted.add(ref)
                pending.append(ref)
    for d in defs:
        for child in list(d):
            if child.get("id") not in wanted:
                d.remove(child)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def native_svg(page: fitz.Page, bbox: list[float], expected: list[int], label: str) -> bytes:
    box = fitz.Rect(bbox)
    indices = [i for i, d in enumerate(page.get_drawings()) if box.contains(d["rect"])]
    if indices != expected:
        raise ValueError("native drawing selection changed: " + label)
    return native_symbol_svg(page, indices, bbox)


def caption_pixels(page: fitz.Page, bbox: list[float]) -> str:
    pixels = page.get_pixmap(matrix=fitz.Matrix(4, 4), clip=fitz.Rect(bbox), alpha=False)
    return sha256(pixels.tobytes("png"))


def admit(groups: dict, key: str, caption: str, data: bytes, native: bytes) -> dict:
    """The fixed 2% comparison, else the canonical-group release the admission gate applies."""
    try:
        return compare_symbol(data, ".svg", native)
    except ValueError:
        released = _canonical_release(groups, {"shared_symbol_key": key}, caption, "ja", data, ".svg", native)
        if released is None:
            raise
        return released


def derive() -> tuple[list[dict], list[dict]]:
    recipe = read(PACKAGE / "source/asset_recipe.json")
    manifest = read(PACKAGE / "source_manifest.json")
    pdf = PACKAGE / manifest["original_source"]["filename"]
    if sha256(pdf.read_bytes()) != recipe["source_sha256"]:
        raise ValueError("authoritative PDF identity changed")
    lines = {line["id"]: line["text"] for page in read(PACKAGE / "source/transcription.json")["pages"]
             for line in page["lines"]}
    catalog = {row["key"]: row for row in read(SHARED_SYMBOLS / "manifest.json")["assets"]}
    groups = canonical_groups()
    assets = PACKAGE / "assets"
    if assets.exists():
        shutil.rmtree(assets)
    assets.mkdir()
    scale = fitz.Matrix(recipe["panel_scale"], recipe["panel_scale"])
    reuse_rows, symbol_rows = [], []
    with fitz.open(pdf) as doc:
        for panel in recipe["panels"]:
            page = doc[panel["physical_page"] - 1]
            page.get_pixmap(matrix=scale, clip=fitz.Rect(panel["bbox"]), alpha=False).save(PACKAGE / panel["path"])
        for icon in recipe["native_icons"]:
            svg = native_svg(doc[icon["physical_page"] - 1], icon["glyph_bbox"], icon["drawing_indices"], icon["path"])
            (PACKAGE / icon["path"]).write_bytes(prune_unused_definitions(svg))
        for item in recipe["reused"]:
            data = (ROOT / item["from"]).read_bytes()
            if sha256(data) != item["sha256"]:
                raise ValueError("reused asset changed: " + item["from"])
            for check in [item["source_check"], *item.get("also_checks", [])]:
                native = native_svg(doc[check["physical_page"] - 1], check["glyph_bbox"], check["drawing_indices"],
                                    item["path"])
                reuse_rows.append({"asset_ref": item["path"], "from": item["from"], "sha256": item["sha256"],
                                   "physical_page": check["physical_page"], "glyph_bbox": check["glyph_bbox"],
                                   "drawing_indices": check["drawing_indices"],
                                   **compare_symbol(data, Path(item["from"]).suffix, native)})
            (PACKAGE / item["path"]).write_bytes(data)
        for symbol in recipe["symbols"]:
            page = doc[symbol["physical_page"] - 1]
            native = native_svg(page, symbol["glyph_bbox"], symbol["drawing_indices"], symbol["path"])
            row = catalog[symbol["shared_symbol_key"]]
            if row["path"] != symbol["shared_path"]:
                raise ValueError("shared symbol path changed: " + symbol["shared_symbol_key"])
            data = (SHARED_SYMBOLS / symbol["shared_path"]).read_bytes()
            if sha256(data) != row["sha256"]:
                raise ValueError("shared symbol bytes changed: " + symbol["shared_symbol_key"])
            check = admit(groups, symbol["shared_symbol_key"], lines[symbol["caption_id"]], data, native)
            (PACKAGE / symbol["path"]).write_bytes(data)
            glyph, caption = fitz.Rect(symbol["glyph_bbox"]), fitz.Rect(symbol["caption_bbox"])
            band = glyph | caption
            symbol_rows.append({
                "asset_ref": symbol["path"], "asset_sha256": sha256(data),
                "physical_page": symbol["physical_page"], "drawing_indices": symbol["drawing_indices"],
                "glyph_bbox": symbol["glyph_bbox"], "caption_bbox": symbol["caption_bbox"],
                "row_bbox": [band.x0 - 1, band.y0 - 1, band.x1 + 1, band.y1 + 1],
                "caption_text": lines[symbol["caption_id"]],
                "caption_sha256": caption_pixels(page, symbol["caption_bbox"]),
                "shared_symbol_key": symbol["shared_symbol_key"], **check,
            })
    return reuse_rows, symbol_rows


def main() -> None:
    reuse_rows, symbol_rows = derive()
    path = PACKAGE / "source_manifest.json"
    manifest = read(path)
    manifest["symbol_asset_admission"] = {"schema_version": SCHEMA, "locales": {"ja": symbol_rows}}
    manifest["artwork_reuse_comparison"] = reuse_rows
    manifest.pop("symbol_admission_blocker", None)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"assets": sorted(p.relative_to(PACKAGE).as_posix()
                                       for p in (PACKAGE / "assets").rglob("*") if p.is_file()),
                      "reuse": [(r["asset_ref"], r["max_mean_channel_error"]) for r in reuse_rows],
                      "symbols": [(r["asset_ref"], r["shared_symbol_key"], r["max_mean_channel_error"],
                                   r.get("canonical_group")) for r in symbol_rows]}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
