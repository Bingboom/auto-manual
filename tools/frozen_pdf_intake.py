"""Read fresh PDF text using historical extraction geometry as a recipe only.

The returned mapping supplies ``source``, ``index``, ``locale``, ``records`` and
``front_back`` for the book adapter. No historical text, normalization fixes,
HTML, or cropped images are reused. Approved errata and governed asset binding
are separate downstream steps. ``provenance`` records PDF identity and every
positioned field read; AI identity remains separate from PDF text authority.
"""
from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re

import fitz

from tools.manual_ir.hashing import file_sha256


_SPEC_EDGES = {
    "general": [69.79, 83.03, 96.53, 110.69, 125.53, 139.53, 153.98, 168.19],
    "inputs": [194.8, 209.27, 235.5],
    "outputs": [260.3, 283.06, 298.85, 314.12, 331.3, 346.22, 360.75],
    "operating_temperature": [390.7, 404.92, 417.94],
}
_GEOMETRY_KEYS = {"physical_page", "bbox", "source_region", "mode_index"}
_FAULT_EDGES = [265.944, 277.913, 289.883, 301.852, 313.275, 325.790,
                337.760, 399.793, 438.462, 453.613, 473.349]


def _clean(text):
    return " ".join(text.split())


def _digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_recipe_json(root, relative, manifest=None):
    """Read only a manifest-pinned recipe; historical artwork is never opened."""
    root = Path(root).resolve()
    if manifest is None:
        manifest = json.loads((root / "source_manifest.json").read_text(encoding="utf-8"))
    matches = [entry for entry in manifest["inputs"] if entry["path"] == relative]
    path = (root / relative).resolve()
    if len(matches) != 1 or not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f"unregistered or missing frozen recipe: {relative}")
    raw = path.read_bytes()
    if len(raw) != matches[0]["size"] or hashlib.sha256(raw).hexdigest() != matches[0]["sha256"]:
        raise ValueError(f"frozen recipe changed: {relative}")
    return json.loads(raw.decode("utf-8"))


def _read(root, name, manifest):
    return read_recipe_json(root, f"source/{name}.json", manifest)


def _page_record(page):
    text = page.get_text()
    return {
        "physical_page": page.number + 1,
        "page_size_points": [round(page.rect.width, 3), round(page.rect.height, 3)],
        "text": text, "text_sha256": _digest(text),
        "blocks_visual_order": [
            {"bbox": [round(v, 3) for v in block[:4]], "text": block[4]}
            for block in page.get_text("blocks", sort=True)
            if block[6] == 0 and block[4].strip()
        ],
    }


class _PDFReader:
    def __init__(self, document):
        self.document = document
        self.spans = []
        self.unresolved = []
        self.line_cache = {}

    def _record(self, raw, page, bbox, field, **extra):
        self.spans.append({"field": field, "physical_page": page,
                           "bbox": list(bbox), "raw_text_sha256": _digest(raw), **extra})
        if "\ufffd" in raw:
            self.unresolved.append({"field": field, "physical_page": page,
                                    "bbox": list(bbox), "replacement_character_count": raw.count("\ufffd")})
        return raw

    def box(self, page, bbox, field):
        if not isinstance(page, int) or not 1 <= page <= len(self.document):
            raise ValueError(f"{field}: physical page is outside PDF")
        rectangle = fitz.Rect(bbox)
        if rectangle.is_empty or not self.document[page - 1].rect.contains(rectangle):
            raise ValueError(f"{field}: invalid PDF text rectangle")
        raw = self.document[page - 1].get_textbox(rectangle)
        if not raw.strip():
            raise ValueError(f"{field}: PDF text rectangle is empty")
        return self._record(raw, page, bbox, field)

    def lines(self, page, bbox, field):
        """Select full PDF lines by majority overlap, then read in visual order.

        App recipe rectangles slightly overlap adjacent headings. Whole-block
        selection avoids importing a neighbor's final line or partial glyph.
        Lines also separate a notice label from its shared body text block.
        """
        rectangle = fitz.Rect(bbox)
        if page not in self.line_cache:
            data = self.document[page - 1].get_text("dict", flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES)
            self.line_cache[page] = [line for block in data["blocks"] for line in block.get("lines", [])]
        selected = [line for line in self.line_cache[page]
                    if (rectangle & fitz.Rect(line["bbox"])).get_area() > fitz.Rect(line["bbox"]).get_area() * .5]
        selected.sort(key=lambda line: (line["bbox"][1], line["bbox"][0]))
        if not selected:
            raise ValueError(f"{field}: no PDF text line occupies the recipe rectangle")
        raw = "\n".join("".join(span["text"] for span in line["spans"]).strip() for line in selected)
        return self._record(raw, page, bbox, field, selection="pdf-line-majority-overlap",
                            source_bboxes=[list(line["bbox"]) for line in selected])

    def positioned(self, recipe, *, page=None, field="record"):
        """Retain geometry/structure only; reread every leaf from the open PDF."""
        if isinstance(recipe, list):
            return [self.positioned(value, page=page, field=f"{field}/{i}")
                    for i, value in enumerate(recipe)]
        if not isinstance(recipe, dict):
            raise ValueError(f"{field}: unsupported non-positioned recipe value")
        page = recipe.get("physical_page", page)
        result = {key: value for key, value in recipe.items() if key in _GEOMETRY_KEYS}
        if "bbox" in recipe and ("text" in recipe or "raw_text" in recipe):
            extract = self.lines if field.startswith("app_sections/") else self.box
            raw = extract(page, recipe["bbox"], field)
            return {**result, "physical_page": page, "raw_text": raw, "text": _clean(raw)}
        for key, value in recipe.items():
            if key in _GEOMETRY_KEYS or key in {"visual_recovery", "standard_years", "extension_years"}:
                continue
            if key == "source_button_faces":
                # Button identities are structural identifiers, not caption copy.
                result[key] = list(value)
            elif isinstance(value, (dict, list)):
                result[key] = self.positioned(value, page=page, field=f"{field}/{key}")
            else:
                raise ValueError(f"{field}/{key}: recipe has text without source geometry")
        return result


def _chapter_titles(document, sections):
    by_page = defaultdict(list)
    for section in sections:
        by_page[section["physical_pages"][0]].append(section["id"])
    headings = {}
    for number, section_ids in by_page.items():
        candidates = []
        for block in document[number - 1].get_text(
            "dict", sort=True, flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES,
        )["blocks"]:
            spans = [s for line in block.get("lines", []) for s in line["spans"] if s["text"].strip()]
            # Body chapter headings have the source's 12pt face. Year badges
            # mix font sizes, so they cannot become a false chapter heading.
            if spans and all(abs(s["size"] - 12) < 0.1 for s in spans):
                candidates.append((_clean(" ".join(s["text"] for s in spans)), block["bbox"]))
        if len(candidates) != len(section_ids):
            raise ValueError(f"page {number}: PDF chapter headings disagree with section geometry")
        for section_id, (title, bbox) in zip(section_ids, candidates, strict=True):
            headings[section_id] = {"text": title, "bbox": list(bbox), "physical_page": number}
    return [headings[section["id"]] for section in sections]


def _specifications(reader, number):
    groups = {}
    for group, edges in _SPEC_EDGES.items():
        rows = []
        for index, (top, bottom) in enumerate(zip(edges, edges[1:])):
            rows.append({
                key: _clean(reader.box(number, (left, top - .5, right, bottom + .5),
                                       f"specifications/{group}/{index}/{key}"))
                for key, left, right in (("label", 26, 123.5), ("value", 125, 338))
            })
        groups[group] = rows
    return {"physical_page": number, "groups": groups}


def _faults(reader, number):
    # Fixed ruled-cell geometry, verified across all four source pages. Avoid
    # find_tables: that helper internally rasterizes the page in some versions.
    rows = []
    for index, (top, bottom) in enumerate(zip(_FAULT_EDGES, _FAULT_EDGES[1:])):
        rows.append({key: _clean(reader.box(number, (left, top, right, bottom),
                                           f"troubleshooting/{index}/{key}"))
                     for key, left, right in (("code", 26, 64.18), ("action", 64.18, 338))})
    rows.append({key: _clean(reader.box(number, bbox, f"troubleshooting/10/{key}"))
                 for key, bbox in (("code", (26, 473, 72, 490)), ("action", (74, 473, 338, 490)))})
    if [row["code"] for row in rows] != [f"F{i}" for i in range(10)] + ["FE"]:
        raise ValueError(f"page {number}: troubleshooting code coverage changed")
    return {"physical_page": number, "rows": rows}


def _symbols(reader, recipe, language):
    number = recipe["physical_page"]
    shift = -10 if language == "nl" else 0
    rows = []
    for index, (top, bottom) in enumerate(((390, 414), (414, 440), (440, 465), (465, 490))):
        rows.append({key: _clean(reader.box(number, (left, top + shift, right, bottom + shift),
                                           f"symbols/{index}/{key}"))
                     for key, left, right in (("label", 32, 100), ("meaning", 102, 340))})
    pictograms = []
    for row in recipe["pictograms"]:
        item = {key: row[key] for key in ("icon_id", "meaning_bbox", "icon_bbox")}
        item["meaning"] = _clean(reader.box(recipe["pictogram_page"], row["meaning_bbox"],
                                             f"symbols/pictograms/{row['icon_id']}/meaning"))
        pictograms.append(item)
    return {"physical_page": number, "rows": rows,
            "pictogram_page": recipe["pictogram_page"], "pictograms": pictograms}


def _lcd(reader, recipe):
    rows = []
    for index, row in enumerate(recipe["rows"]):
        item = {key: row[key] for key in ("number", "physical_page", "label_bbox", "meaning_bbox")}
        for key in ("label", "meaning"):
            item[key] = _clean(reader.box(row["physical_page"], row[f"{key}_bbox"], f"lcd/{index}/{key}"))
        item["raw_label"] = item["label"]
        rows.append(item)
    return {"pages": list(recipe["pages"]), "rows": rows}


def _front_back(reader, recipe, language, pdf_hash):
    locale = recipe["locales"][language]
    preface = locale["preface"]
    return {
        "source_sha256": pdf_hash,
        "shared": {key: _page_record(reader.document[value["physical_page"] - 1])
                   for key, value in recipe["shared"].items()},
        "locales": {language: {
            "preface": {"physical_page": preface["physical_page"], "bbox": list(preface["bbox"]),
                        "text": reader.box(preface["physical_page"], preface["bbox"], "preface")},
            "toc_page": locale["toc_page"],
            "toc_shared_page": _page_record(reader.document[locale["toc_page"] - 1]),
        }},
    }


def load_pdf_book(pdf_path: Path, language: str, recipe_root: Path) -> dict:
    """Fresh selectable PDF text plus structural recipes; no writes or images.

    ``recipe_root`` is the historical four-language package directory. Its
    text-bearing values are never used to fill, locate or repair new copy.
    Missing rectangles/headings fail closed rather than falling back to JSON.
    """
    pdf_path, recipe_root = Path(pdf_path).resolve(), Path(recipe_root).resolve()
    manifest = json.loads((recipe_root / "source_manifest.json").read_text(encoding="utf-8"))
    if language not in manifest["target"]["languages"]:
        raise ValueError("language is outside the source geometry recipe")
    old_source = _read(recipe_root, f"{language}_direct_source", manifest)
    sections = [{"id": section["id"], "physical_pages": list(section["physical_pages"])}
                for section in old_source["sections"]]
    pdf_hash = file_sha256(pdf_path)
    with fitz.open(pdf_path) as document:
        if len(document) != manifest["original_source"]["physical_page_count"]:
            raise ValueError("PDF page count disagrees with source geometry recipe")
        reader = _PDFReader(document)
        pages = [{**_page_record(document[recipe["physical_page"] - 1]),
                  "relative_body_page": recipe["relative_body_page"]} for recipe in old_source["pages"]]
        titles = _chapter_titles(document, sections)
        records = {name: reader.positioned(_read(recipe_root, name, manifest)["locales"][language], field=name)
                   for name in ("operation_tables", "warranty_columns", "app_sections")}
        for prefix in ("standard", "extension"):
            raw = records["warranty_columns"]["blocks"][f"{prefix}_heading"]["raw_text"]
            numbers = re.findall(r"^\s*(\d+)\s*$", raw, flags=re.MULTILINE)
            if len(numbers) != 1:
                raise ValueError(f"{prefix}: warranty year is not a unique source line")
            records["warranty_columns"][f"{prefix}_years"] = int(numbers[0])
        records["symbols"] = _symbols(reader, _read(recipe_root, "symbols", manifest)["locales"][language], language)
        records["lcd_indicators"] = _lcd(reader, _read(recipe_root, "lcd_indicators", manifest)["locales"][language])
        for record in records.values():
            record["source_sha256"] = pdf_hash
        source = {
            "schema_version": "je1000f-eu-four-locale-direct-source/v1", "locale": language,
            "source_path": pdf_path.name, "source_sha256": pdf_hash,
            "method": "fresh PyMuPDF PDF text objects; geometry recipe only; no OCR, translation or image extraction",
            "sections": sections, "pages": pages,
            "tables": {
                "troubleshooting": _faults(reader, old_source["tables"]["troubleshooting"]["physical_page"]),
                "specifications": _specifications(reader, old_source["tables"]["specifications"]["physical_page"]),
            },
        }
        front_back = _front_back(reader, _read(recipe_root, "front_back_source", manifest), language, pdf_hash)
        locale = {"label": language, "physical_pages": [pages[0]["physical_page"], pages[-1]["physical_page"]],
                  "titles": [title["text"] for title in titles]}
        provenance = {"pdf": {"filename": pdf_path.name, "sha256": pdf_hash, "page_count": len(document)},
                      "ai": manifest["original_source"], "ai_identity_origin": "historical source manifest",
                      "geometry_recipe_sha256": file_sha256(recipe_root / "source_manifest.json"),
                      "chapter_spans": titles, "text_spans": reader.spans,
                      "unresolved_text": reader.unresolved,
                      "corrections_applied": [], "image_extraction_performed": False}
        ai_path = pdf_path.parent / manifest["original_source"]["filename"]
        if ai_path.is_file():
            if file_sha256(ai_path) != manifest["original_source"]["sha256"]:
                raise ValueError("sibling AI original disagrees with source provenance")
            provenance["ai_identity_origin"] = "verified sibling AI original"
    return {"source": source, "index": {"section_ids": [s["id"] for s in sections], "languages": {language: locale}},
            "locale": locale, "records": records, "front_back": front_back, "provenance": provenance}


__all__ = ["load_pdf_book"]
