"""Derive the JE-5000A US Web artwork from the frozen PDF and reused files.

Run from the repository root:

    python manual_sources/JE-5000A/US/en/git-20261028-804ebe78/derive_assets.py

``source/asset_recipe.json`` is the reviewed recipe. Panels are complete 3x
renders of the source rectangle (panel backgrounds, leader lines, labels and
phone frames kept). A panel may list ``omit`` rectangles: the text-layer copy
and the vector objects fully inside them (a grey text bubble or pill that the
Web page sets as native text) are removed from an in-memory copy of the page
before rendering; nothing is painted over. Native icons keep the original PDF
vector paths through the shared ``native_symbol_svg`` selector, so they carry
no page or cell backdrop. Reused files are copied byte-identically after a hash
check, and each is bound to its printed glyph by identical vector path data
(``source_manifest.json:artwork_reuse_comparison``).

Symbols and the inline INGESTION HAZARD glyph reuse a shared catalog variant
byte-identically after the fixed 2% comparison with the native paths (all
eight table symbols and the glyph are catalog files; the Open Flame symbol
and the glyph entered the catalog through the shared-symbol PR #1640 from this
PDF). A printed symbol with no passing variant would be ``staged``: its native
paths become the package asset and ``source_manifest.json:staged_shared_symbols``
holds the proposed catalog row, which ``rebuild.py`` admits until the shared
catalog carries it. This script never writes the shared catalog;
``--proposed-dir`` writes each proposed row and SVG for the coordinator's
shared-symbol PR. The symbol admission rows of ``source_manifest.json`` are
written from the same recipe and the reviewed transcription.
"""
from __future__ import annotations

import argparse
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
SOURCE_REF = "manual_sources/JE-5000A/US/en/git-20261028-804ebe78/JE-5000A-US-EN.pdf"
PATH_DATA = re.compile(rb' d="([^"]+)"')
FILL = re.compile(rb'fill="(#[0-9a-fA-F]{6})"')
FILL_TOLERANCE = 24  # of 255 per channel


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def prune_unused_definitions(svg: bytes) -> bytes:
    """Drop page-wide <defs> entries that no retained path references.

    The shared selector copies every clip path of the page. Only unreferenced
    definitions are removed; retained paths, groups, transforms, clips and
    opacity are unchanged.
    """
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


def native_svg(page: fitz.Page, bbox: list[float]) -> tuple[bytes, list[int]]:
    box = fitz.Rect(bbox)
    indices = [i for i, d in enumerate(page.get_drawings()) if box.contains(d["rect"])]
    return native_symbol_svg(page, indices, bbox), indices


def _fills(svg: bytes) -> list[tuple[int, int, int]]:
    values = {bytes.fromhex(v[1:].decode()) for v in FILL.findall(svg)}
    return sorted((v[0], v[1], v[2]) for v in values)


def vector_identity(candidate: bytes, native: bytes) -> dict:
    """Identical glyph geometry: every path's data equals the printed one, in order.

    The page-sized clip rectangle every extraction carries is ignored. The flat
    grey of the reused file may come from a different colour conversion of the
    same print; each fill may differ by at most FILL_TOLERANCE per channel.
    """
    page_rect = PATH_DATA.findall(native)[0]
    paths = [d for d in PATH_DATA.findall(candidate) if d != page_rect]
    source = [d for d in PATH_DATA.findall(native) if d != page_rect]
    fills, printed = _fills(candidate), _fills(native)
    if paths != source or len(fills) != len(printed):
        raise ValueError("reused glyph differs from the printed vector paths")
    delta = max(abs(a - b) for pair in zip(fills, printed, strict=True) for a, b in zip(*pair, strict=True))
    if delta > FILL_TOLERANCE:
        raise ValueError("reused glyph fill differs from the printed grey")
    return {"identical_path_data": True, "paths": len(paths),
            "fills": ["#%02x%02x%02x" % f for f in fills], "printed_fills": ["#%02x%02x%02x" % f for f in printed],
            "max_fill_channel_delta": delta}


def caption_pixels(page: fitz.Page, bbox: list[float]) -> str:
    pixels = page.get_pixmap(matrix=fitz.Matrix(4, 4), clip=fitz.Rect(bbox), alpha=False)
    return sha256(pixels.tobytes("png"))


def render_panel(pdf: Path, panel: dict, scale: fitz.Matrix) -> bytes:
    with fitz.open(pdf) as doc:
        page = doc[panel["physical_page"] - 1]
        # One rectangle per pass: MuPDF judges "fully covered" against a single area.
        for rect in panel.get("omit", []):
            page.add_redact_annot(fitz.Rect(rect), fill=False)
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,
                                  graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED,
                                  text=fitz.PDF_REDACT_TEXT_REMOVE)
        return page.get_pixmap(matrix=scale, clip=fitz.Rect(panel["bbox"]), alpha=False).tobytes("png")


def staged_row(item: dict, data: bytes, source_sha: str) -> dict:
    return {
        "key": item["shared_symbol_key"], "path": item["shared_path"], "sha256": sha256(data),
        "status": "source-bound native variant",
        "provenance": {
            "source": SOURCE_REF, "source_sha256": source_sha,
            "physical_page": item["physical_page"], "drawing_indices": item["drawing_indices"],
            "glyph_bbox": item["glyph_bbox"], "decision": item["staged_decision"],
        },
    }


def derive(proposed_dir: Path | None = None) -> tuple[dict, list[dict], list[dict]]:
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
        (PACKAGE / panel["path"]).write_bytes(render_panel(pdf, panel, scale))
    catalog = {row["key"]: row for row in read(SHARED_SYMBOLS / "manifest.json")["assets"]}
    staged: list[dict] = []
    reuse: list[dict] = []
    rows = []

    def stage(item: dict, data: bytes) -> None:
        row = staged_row(item, data, recipe["source_sha256"])
        if item["shared_symbol_key"] in catalog:
            raise ValueError("staged key already in the shared catalog; bind the catalog file: " + row["key"])
        staged.append(row)
        if proposed_dir is not None:
            proposed_dir.mkdir(parents=True, exist_ok=True)
            (proposed_dir / Path(item["shared_path"]).name).write_bytes(data)

    with fitz.open(pdf) as doc:
        for icon in recipe["native_icons"]:
            svg, indices = native_svg(doc[icon["physical_page"] - 1], icon["glyph_bbox"])
            if indices != icon["drawing_indices"]:
                raise ValueError("native icon drawing selection changed: " + icon["path"])
            (PACKAGE / icon["path"]).write_bytes(prune_unused_definitions(svg))
        for item in recipe["reused"]:
            data = (ROOT / item["from"]).read_bytes()
            native, indices = native_svg(doc[item["physical_page"] - 1], item["glyph_bbox"])
            if indices != item["drawing_indices"]:
                raise ValueError("reused glyph drawing selection changed: " + item["path"])
            reuse.append({"asset_ref": item["path"], "from": item["from"], "sha256": sha256(data),
                          "physical_page": item["physical_page"], "glyph_bbox": item["glyph_bbox"],
                          "drawing_indices": indices, **vector_identity(data, native)})
            (PACKAGE / item["path"]).write_bytes(data)
        mark = recipe["fcc_mark"]
        native, indices = native_svg(doc[mark["physical_page"] - 1], mark["glyph_bbox"])
        if indices != mark["drawing_indices"]:
            raise ValueError("FCC mark drawing selection changed")
        data = (SHARED_SYMBOLS / mark["shared_path"]).read_bytes()
        if catalog[mark["shared_symbol_key"]]["sha256"] != sha256(data):
            raise ValueError("shared FCC mark changed")
        reuse.append({"asset_ref": mark["path"], "from": "docs/renderers/web/assets/shared/symbols/" + mark["shared_path"],
                      "sha256": sha256(data), "physical_page": mark["physical_page"], "glyph_bbox": mark["glyph_bbox"],
                      "drawing_indices": indices, **compare_symbol(data, ".svg", native)})
        (PACKAGE / mark["path"]).write_bytes(data)
        for glyph in recipe["inline_glyphs"]:
            native, indices = native_svg(doc[glyph["physical_page"] - 1], glyph["glyph_bbox"])
            if indices != glyph["drawing_indices"]:
                raise ValueError("inline glyph drawing selection changed: " + glyph["path"])
            if glyph.get("staged"):
                data = prune_unused_definitions(native)
                stage(glyph, data)
            else:
                data = (SHARED_SYMBOLS / glyph["shared_path"]).read_bytes()
                if catalog[glyph["shared_symbol_key"]]["sha256"] != sha256(data):
                    raise ValueError("shared inline glyph changed: " + glyph["shared_path"])
            checks = [{"physical_page": glyph["physical_page"], **compare_symbol(data, ".svg", native)}]
            for other in glyph.get("also_printed", []):
                again, again_indices = native_svg(doc[other["physical_page"] - 1], other["glyph_bbox"])
                if again_indices != other["drawing_indices"]:
                    raise ValueError("inline glyph drawing selection changed on page %d" % other["physical_page"])
                checks.append({"physical_page": other["physical_page"], **compare_symbol(data, ".svg", again)})
            if not glyph.get("staged"):
                reuse.append({"asset_ref": glyph["path"],
                              "from": "docs/renderers/web/assets/shared/symbols/" + glyph["shared_path"],
                              "sha256": sha256(data), "physical_page": glyph["physical_page"],
                              "glyph_bbox": glyph["glyph_bbox"], "drawing_indices": indices,
                              "max_mean_channel_error": max(c["max_mean_channel_error"] for c in checks),
                              "printed_instances": checks})
            (PACKAGE / glyph["path"]).write_bytes(data)
        for symbol in recipe["symbols"]:
            page = doc[symbol["physical_page"] - 1]
            native, indices = native_svg(page, symbol["glyph_bbox"])
            if indices != symbol["drawing_indices"]:
                raise ValueError("symbol drawing selection changed: " + symbol["path"])
            if symbol.get("staged"):
                data = prune_unused_definitions(native)
                stage(symbol, data)
            else:
                data = (SHARED_SYMBOLS / symbol["shared_path"]).read_bytes()
                if catalog[symbol["shared_symbol_key"]]["sha256"] != sha256(data):
                    raise ValueError("shared symbol changed: " + symbol["shared_path"])
            check = compare_symbol(data, Path(symbol["path"]).suffix, native)
            (PACKAGE / symbol["path"]).write_bytes(data)
            glyph_rect, caption = fitz.Rect(symbol["glyph_bbox"]), fitz.Rect(symbol["caption_bbox"])
            band = glyph_rect | caption
            rows.append({
                "asset_ref": symbol["path"], "asset_sha256": sha256(data),
                "physical_page": symbol["physical_page"], "drawing_indices": indices,
                "glyph_bbox": symbol["glyph_bbox"], "caption_bbox": symbol["caption_bbox"],
                "row_bbox": [band.x0 - 1, band.y0 - 1, band.x1 + 1, band.y1 + 1],
                "caption_text": lines[symbol["caption_id"]],
                "caption_sha256": caption_pixels(page, symbol["caption_bbox"]),
                "shared_symbol_key": symbol["shared_symbol_key"], **check,
            })
    if proposed_dir is not None and staged:
        (proposed_dir / "proposed_catalog_rows.json").write_text(
            json.dumps(staged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"schema_version": SCHEMA, "locales": {"en": rows}}, staged, reuse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposed-dir", type=Path,
                        help="write the proposed catalog row and SVG of each staged symbol here")
    args = parser.parse_args()
    admission, staged, reuse = derive(args.proposed_dir)
    path = PACKAGE / "source_manifest.json"
    manifest = read(path)
    manifest["symbol_asset_admission"] = admission
    manifest["staged_shared_symbols"] = staged
    manifest["artwork_reuse_comparison"] = reuse
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"assets": len([p for p in (PACKAGE / "assets").rglob("*") if p.is_file()]),
                      "symbols": [(r["asset_ref"], r["max_mean_channel_error"]) for r in admission["locales"]["en"]],
                      "staged_shared_symbols": [row["key"] for row in staged]}, indent=1))


if __name__ == "__main__":
    main()
