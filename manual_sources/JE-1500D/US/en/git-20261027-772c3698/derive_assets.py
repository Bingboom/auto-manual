"""Derive the JE-1500D US Web artwork from the frozen PDF and reused shared files.

Run from the repository root:

    python manual_sources/JE-1500D/US/en/git-20261027-772c3698/derive_assets.py

``source/asset_recipe.json`` is the reviewed recipe. Panels are complete 3x
renders of the source rectangle (panel backgrounds, leader lines, labels and
phone frames kept). A panel may list ``omit`` rectangles: the vector objects
fully inside them (a grey text bubble or pill that the Web page sets as native
text) are removed from an in-memory copy of the page before rendering; nothing
is painted over. Native icons and symbols keep the original PDF vector paths
through the shared ``native_symbol_svg`` selector, so they carry no page or cell
backdrop. Reused files are copied byte-identically after a hash check.

Symbols reuse a shared catalog variant that passes the fixed 2% comparison. A
printed symbol with no passing variant is ``staged``: its native paths are the
package asset and ``source_manifest.json:staged_shared_symbols`` holds the
proposed catalog row. Until the operator approves it, ``rebuild.py`` admits it
against that staged row. ``--proposed-dir`` writes the proposed row and SVG for
review; ``--write-shared`` (after approval) adds the SVG and row to the shared
catalog once, after which the symbol is checked like any catalog variant.
The symbol admission rows of ``source_manifest.json`` are written from the same
recipe and the reviewed transcription.
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
SOURCE_REF = "manual_sources/JE-1500D/US/en/git-20261027-772c3698/JE-1500D-US-EN.pdf"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class CachedPage:
    """One page whose drawing list and SVG are read once.

    Every page of this PDF carries the whole 187,134-path artboard (clipped per
    page), so the shared selector is given the same page data without
    re-parsing it for every glyph.
    """

    def __init__(self, page: fitz.Page) -> None:
        self.rect = page.rect
        self._drawings = page.get_drawings()
        self._svg = page.get_svg_image(text_as_path=False)

    def get_drawings(self) -> list[dict]:
        return self._drawings

    def get_svg_image(self, text_as_path: bool = False) -> str:
        return self._svg


def prune_unused_definitions(svg: bytes) -> bytes:
    """Drop page-wide <defs> entries that no retained path references.

    The shared selector copies every clip path and mask of the 187,134-path
    page (about 0.44 MB per glyph). Only unreferenced definitions are removed;
    retained paths, groups, transforms, clips and opacity are unchanged.
    """
    root = ET.fromstring(svg)
    defs = [d for d in root.iter(SVG + "defs")]
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


def native_svg(page: CachedPage, bbox: list[float]) -> tuple[bytes, list[int]]:
    box = fitz.Rect(bbox)
    indices = [i for i, d in enumerate(page.get_drawings()) if box.contains(d["rect"])]
    return native_symbol_svg(page, indices, bbox), indices


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
                                  text=fitz.PDF_REDACT_TEXT_NONE)
        return page.get_pixmap(matrix=scale, clip=fitz.Rect(panel["bbox"]), alpha=False).tobytes("png")


def catalog() -> dict:
    return read(SHARED_SYMBOLS / "manifest.json")


def staged_row(symbol: dict, data: bytes) -> dict:
    return {
        "key": symbol["shared_symbol_key"], "path": symbol["shared_path"], "sha256": sha256(data),
        "status": "source-bound native variant",
        "provenance": {
            "source": SOURCE_REF, "source_sha256": read(PACKAGE / "source/asset_recipe.json")["source_sha256"],
            "physical_page": symbol["physical_page"], "drawing_indices": symbol["drawing_indices"],
            "glyph_bbox": symbol["glyph_bbox"],
            "decision": symbol["staged_decision"],
        },
    }


def derive(write_shared: bool = False, proposed_dir: Path | None = None) -> tuple[dict, list[dict]]:
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
    (assets / "shared-buttons").mkdir(parents=True)
    scale = fitz.Matrix(recipe["panel_scale"], recipe["panel_scale"])
    for panel in recipe["panels"]:
        (PACKAGE / panel["path"]).write_bytes(render_panel(pdf, panel, scale))
    keys = {row["key"]: row for row in catalog()["assets"]}
    staged: list[dict] = []
    with fitz.open(pdf) as doc:
        pages: dict[int, CachedPage] = {}

        def cached(number: int) -> CachedPage:
            if number not in pages:
                pages[number] = CachedPage(doc[number - 1])
            return pages[number]

        for icon in recipe["native_icons"]:
            svg, indices = native_svg(cached(icon["physical_page"]), icon["glyph_bbox"])
            if indices != icon["drawing_indices"]:
                raise ValueError("native icon drawing selection changed: " + icon["path"])
            (PACKAGE / icon["path"]).write_bytes(prune_unused_definitions(svg))
        mark = recipe["fcc_mark"]
        native, indices = native_svg(cached(mark["physical_page"]), mark["glyph_bbox"])
        if indices != mark["drawing_indices"]:
            raise ValueError("FCC mark drawing selection changed")
        data = (SHARED_SYMBOLS / mark["shared_path"]).read_bytes()
        if keys[mark["shared_symbol_key"]]["sha256"] != sha256(data):
            raise ValueError("shared FCC mark changed")
        compare_symbol(data, ".svg", native)
        (PACKAGE / mark["path"]).write_bytes(data)
        rows = []
        for symbol in recipe["symbols"]:
            page = doc[symbol["physical_page"] - 1]
            native, indices = native_svg(cached(symbol["physical_page"]), symbol["glyph_bbox"])
            if indices != symbol["drawing_indices"]:
                raise ValueError("symbol drawing selection changed: " + symbol["path"])
            shared = SHARED_SYMBOLS / symbol["shared_path"]
            if symbol.get("staged"):
                candidate = prune_unused_definitions(native)
                row = staged_row(symbol, candidate)
                if write_shared and symbol["shared_symbol_key"] not in keys:
                    if shared.exists():
                        raise ValueError("refusing to overwrite an existing shared file: " + symbol["shared_path"])
                    shared.write_bytes(candidate)
                    path = SHARED_SYMBOLS / "manifest.json"
                    data_manifest = read(path)
                    data_manifest["assets"].append(row)
                    path.write_text(json.dumps(data_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                    keys[row["key"]] = row
                if symbol["shared_symbol_key"] in keys and shared.read_bytes() != candidate:
                    raise ValueError("shared native symbol differs from source paths: " + symbol["shared_path"])
                if symbol["shared_symbol_key"] not in keys:
                    staged.append(row)
                    if proposed_dir is not None:
                        proposed_dir.mkdir(parents=True, exist_ok=True)
                        (proposed_dir / Path(symbol["shared_path"]).name).write_bytes(candidate)
                        (proposed_dir / "proposed_catalog_row.json").write_text(
                            json.dumps(row, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                data = candidate
            else:
                data = shared.read_bytes()
                if keys[symbol["shared_symbol_key"]]["sha256"] != sha256(data):
                    raise ValueError("shared symbol changed: " + symbol["shared_path"])
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
    for item in recipe["reused"]:
        data = (ROOT / item["from"]).read_bytes()
        if sha256(data) != item["sha256"]:
            raise ValueError("reused asset changed: " + item["from"])
        (PACKAGE / item["path"]).write_bytes(data)
    return {"schema_version": SCHEMA, "locales": {"en": rows}}, staged


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-shared", action="store_true",
                        help="after operator approval: add staged native symbol variants to the shared catalog")
    parser.add_argument("--proposed-dir", type=Path,
                        help="write the proposed catalog row and SVG of each staged symbol here")
    args = parser.parse_args()
    admission, staged = derive(args.write_shared, args.proposed_dir)
    path = PACKAGE / "source_manifest.json"
    manifest = read(path)
    manifest["symbol_asset_admission"] = admission
    manifest["staged_shared_symbols"] = staged
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"assets": sorted(p.relative_to(PACKAGE).as_posix()
                                       for p in (PACKAGE / "assets").rglob("*") if p.is_file()),
                      "staged_shared_symbols": [row["key"] for row in staged]}, indent=1))


if __name__ == "__main__":
    main()
