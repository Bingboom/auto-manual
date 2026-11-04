"""Derive the JE-3000B US Web artwork from the frozen PDF and reused repository files.

Run from the repository root:

    python manual_sources/JE-3000B/US/en/git-20261028-bd8a8296/derive_assets.py

``source/asset_recipe.json`` is the reviewed recipe. Panels are complete 3x
renders of the source rectangle (panel backgrounds, leader lines, labels and
phone frames kept). A panel may list ``omit`` rectangles: the vector objects
fully inside them (a grey text bubble or pill, or a printed instruction that
the Web page sets as native text) are removed from an in-memory copy of the
page before rendering; nothing is painted over.

``reused`` LCD icons are copied byte-identically from approved same-generation
packages after a hash check, and only when the fixed 2% glyph comparison
against this PDF's native paths passes. The key-combination buttons have no
reusable variant within 2%, so they keep the original PDF vector paths through
the shared ``native_symbol_svg`` selector (no page or cell backdrop). The FCC
mark reuses the shared catalog variant after the same comparison.

No safety-symbol table is printed, so ``symbol_asset_admission`` covers zero
rows; nothing is added to the shared symbol catalog by this script.
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
from tools.web.symbol_asset_admission import SCHEMA, compare_symbol  # noqa: E402

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


def render_panel(pdf: Path, panel: dict, scale: fitz.Matrix) -> bytes:
    with fitz.open(pdf) as doc:
        page = doc[panel["physical_page"] - 1]
        # One rectangle per pass: MuPDF judges "fully covered" against a single area.
        for rect in panel.get("omit", []):
            page.add_redact_annot(fitz.Rect(rect), fill=False)
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,
                                  graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED,
                                  text=fitz.PDF_REDACT_TEXT_NONE)
        return page.get_pixmap(matrix=scale, clip=fitz.Rect(panel["bbox"]), alpha=False).tobytes("png")


def derive() -> list[dict]:
    recipe = read(PACKAGE / "source/asset_recipe.json")
    manifest = read(PACKAGE / "source_manifest.json")
    pdf = PACKAGE / manifest["original_source"]["filename"]
    if sha256(pdf.read_bytes()) != recipe["source_sha256"]:
        raise ValueError("authoritative PDF identity changed")
    assets = PACKAGE / "assets"
    if assets.exists():
        shutil.rmtree(assets)
    assets.mkdir()
    scale = fitz.Matrix(recipe["panel_scale"], recipe["panel_scale"])
    for panel in recipe["panels"]:
        (PACKAGE / panel["path"]).write_bytes(render_panel(pdf, panel, scale))
    reuse_rows = []
    with fitz.open(pdf) as doc:
        for icon in recipe["native_icons"]:
            svg = native_svg(doc[icon["physical_page"] - 1], icon["glyph_bbox"], icon["drawing_indices"], icon["path"])
            (PACKAGE / icon["path"]).write_bytes(prune_unused_definitions(svg))
        for item in recipe["reused"]:
            data = (ROOT / item["from"]).read_bytes()
            if sha256(data) != item["sha256"]:
                raise ValueError("reused asset changed: " + item["from"])
            native = native_svg(doc[item["physical_page"] - 1], item["glyph_bbox"], item["drawing_indices"],
                                item["path"])
            check = compare_symbol(data, Path(item["from"]).suffix, native)
            (PACKAGE / item["path"]).write_bytes(data)
            reuse_rows.append({"asset_ref": item["path"], "from": item["from"], "sha256": item["sha256"],
                               "physical_page": item["physical_page"], "drawing_indices": item["drawing_indices"],
                               **check})
        mark = recipe["fcc_mark"]
        native = native_svg(doc[mark["physical_page"] - 1], mark["glyph_bbox"], mark["drawing_indices"], "FCC mark")
        keys = {row["key"]: row for row in read(SHARED_SYMBOLS / "manifest.json")["assets"]}
        data = (SHARED_SYMBOLS / mark["shared_path"]).read_bytes()
        if keys[mark["shared_symbol_key"]]["sha256"] != sha256(data):
            raise ValueError("shared FCC mark changed")
        check = compare_symbol(data, ".svg", native)
        (PACKAGE / mark["path"]).write_bytes(data)
        reuse_rows.append({"asset_ref": mark["path"], "from": "docs/renderers/web/assets/shared/symbols/"
                           + mark["shared_path"], "sha256": sha256(data), "physical_page": mark["physical_page"],
                           "drawing_indices": mark["drawing_indices"], "shared_symbol_key": mark["shared_symbol_key"],
                           **check})
    if recipe["symbols"]:
        raise ValueError("this manual prints no safety-symbol table")
    return reuse_rows


def main() -> None:
    reuse_rows = derive()
    path = PACKAGE / "source_manifest.json"
    manifest = read(path)
    manifest["symbol_asset_admission"] = {"schema_version": SCHEMA, "locales": {"en": []}}
    manifest["artwork_reuse_comparison"] = reuse_rows
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"assets": sorted(p.relative_to(PACKAGE).as_posix()
                                       for p in (PACKAGE / "assets").rglob("*") if p.is_file()),
                      "reuse": [(r["asset_ref"], r["max_mean_channel_error"]) for r in reuse_rows]}, indent=1))


if __name__ == "__main__":
    main()
