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
            extract = self.lines if recipe.get("selection") == "lines" or field.startswith("app_sections/") else self.box
            raw = extract(page, recipe["bbox"], field)
            return {**result, "physical_page": page, "raw_text": raw, "text": _clean(raw)}
        for key, value in recipe.items():
            if key in _GEOMETRY_KEYS or key in {"visual_recovery", "standard_years", "extension_years", "selection"}:
                continue
            if key == "source_button_faces":
                # Button identities are structural identifiers, not caption copy.
                result[key] = list(value)
            elif isinstance(value, (dict, list)):
                result[key] = self.positioned(value, page=page, field=f"{field}/{key}")
            else:
                raise ValueError(f"{field}/{key}: recipe has text without source geometry")
        return result


def _chapter_titles(document, sections, layout=None):
    by_page = defaultdict(list)
    for section in sections:
        by_page[section["physical_pages"][0]].append(section["id"])
    headings = {}
    for number, section_ids in by_page.items():
        explicit = (layout or {}).get("chapter_heading_bboxes", {})
        if explicit:
            for section_id in section_ids:
                bbox = explicit.get(section_id)
                if bbox is None:
                    raise ValueError(f"missing chapter heading geometry: {section_id}")
                text = _clean(document[number - 1].get_textbox(fitz.Rect(bbox)))
                if not text:
                    raise ValueError(f"empty chapter heading: {section_id}")
                headings[section_id] = {"text": text, "bbox": list(bbox), "physical_page": number}
            continue
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


def _specifications(reader, number, layout=None):
    groups = {}
    layout = layout or {}
    if "cells" in layout:
        for group, records in layout["cells"].items():
            groups[group] = [{key: _clean((reader.lines if record.get("selection", layout.get("selection")) == "lines" else reader.box)(
                              number, record[f"{key}_bbox"],
                              f"specifications/{group}/{index}/{key}"))
                              for key in ("label", "value")}
                             for index, record in enumerate(records)]
        return {"physical_page": number, "groups": groups}
    columns = layout.get("columns", {"label": [26, 123.5], "value": [125, 338]})
    extract = reader.lines if layout.get("selection") == "lines" else reader.box
    for group, edges in layout.get("edges", _SPEC_EDGES).items():
        rows = []
        for index, (top, bottom) in enumerate(zip(edges, edges[1:])):
            rows.append({
                key: _clean(extract(number, (left, top - .5, right, bottom + .5),
                                       f"specifications/{group}/{index}/{key}"))
                for key, (left, right) in columns.items()
            })
        groups[group] = rows
    return {"physical_page": number, "groups": groups}


def _faults(reader, number, layout=None):
    # Fixed ruled-cell geometry, verified across all four source pages. Avoid
    # find_tables: that helper internally rasterizes the page in some versions.
    rows = []
    if layout and "cells" in layout:
        extract = reader.lines if layout.get("selection") == "lines" else reader.box
        rows = [{key: _clean(extract(number, record[f"{key}_bbox"],
                 f"troubleshooting/{index}/{key}")) for key in ("code", "action")}
                for index, record in enumerate(layout["cells"])]
        if [row["code"] for row in rows] != layout["codes"]:
            raise ValueError(f"page {number}: troubleshooting code coverage changed")
        return {"physical_page": number, "rows": rows}
    edges = (layout or {}).get("edges", _FAULT_EDGES)
    for index, (top, bottom) in enumerate(zip(edges, edges[1:])):
        rows.append({key: _clean(reader.box(number, (left, top, right, bottom),
                                           f"troubleshooting/{index}/{key}"))
                     for key, left, right in (("code", 26, 64.18), ("action", 64.18, 338))})
    tail = (layout or {}).get("tail", {"code": (26, 473, 72, 490), "action": (74, 473, 338, 490)})
    rows.append({key: _clean(reader.box(number, bbox, f"troubleshooting/{len(rows)}/{key}"))
                 for key, bbox in tail.items()})
    expected = (layout or {}).get("codes", [f"F{i}" for i in range(10)] + ["FE"])
    if [row["code"] for row in rows] != expected:
        raise ValueError(f"page {number}: troubleshooting code coverage changed")
    return {"physical_page": number, "rows": rows}


def _symbols(reader, recipe, language, layout=None):
    number = recipe["physical_page"]
    shift = -10 if language == "nl" and layout is None else 0
    rows = []
    if layout and "cells" in layout:
        rows = [{key: _clean(reader.box(number, record[f"{key}_bbox"], f"symbols/{index}/{key}"))
                 for key in ("label", "meaning")}
                for index, record in enumerate(layout["cells"])]
    else:
        ranges = (layout or {}).get("rows", ((390, 414), (414, 440), (440, 465), (465, 490)))
        for index, (top, bottom) in enumerate(ranges):
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
            extract = reader.lines if row.get("selection") == "lines" else reader.box
            item[key] = _clean(extract(row["physical_page"], row[f"{key}_bbox"], f"lcd/{index}/{key}"))
        item["raw_label"] = item["label"]
        rows.append(item)
    return {"pages": list(recipe["pages"]), "rows": rows}


def _front_back(reader, recipe, language, pdf_hash, candidate=None):
    locale = recipe["locales"][language]
    preface = locale["preface"]
    if preface.get("status") == "missing-in-source":
        if candidate is None:
            raise ValueError(f"{language}: preface is missing from the source; source recovery requires approval")
        preface_record = {"physical_page": preface["physical_page"], "bbox": list(preface["bbox"]),
                          "status": candidate["status"], "candidate": candidate["content"]}
        if candidate.get("approval"):
            preface_record["approval"] = candidate["approval"]
    else:
        preface_record = {"physical_page": preface["physical_page"], "bbox": list(preface["bbox"]),
                          "text": reader.box(preface["physical_page"], preface["bbox"], "preface")}
    return {
        "source_sha256": pdf_hash,
        "shared": {key: _page_record(reader.document[value["physical_page"] - 1])
                   for key, value in recipe["shared"].items()},
        "locales": {language: {
            "preface": preface_record,
            "toc_page": locale["toc_page"],
            "toc_shared_page": _page_record(reader.document[locale["toc_page"] - 1]),
        }},
    }


def _media_records(reader, layout, sections):
    """Read target media labels from the same native PDF as body copy."""
    media = layout.get("media", {})
    if not media:
        return {}
    pages = {section["id"]: section["physical_pages"][0] for section in sections}
    result = {}
    for section, key in (("in_the_box", "inbox"), ("product_overview", "overview")):
        recipe = media.get(key)
        if not recipe:
            continue
        number = pages[section]
        record = {"physical_page": number,
                  "title": _clean(reader.box(number, recipe["title_bbox"], f"media/{key}/title"))}
        if key == "inbox":
            record["cards"] = [{"id": card["id"], "label": _clean(reader.box(
                number, card["label_bbox"], f"media/inbox/{card['id']}/label"))}
                               for card in recipe["cards"]]
            record["tip"] = {name: _clean(reader.box(number, recipe["tip"][f"{name}_bbox"],
                             f"media/inbox/tip/{name}")) for name in ("label", "body")}
        else:
            record["views"] = {}
            for view_id, view in recipe["views"].items():
                item = {"caption": _clean(reader.box(number, view["caption_bbox"],
                        f"media/overview/{view_id}/caption")), "callouts": {}}
                for callout_id, callout in view["callouts"].items():
                    extract = reader.lines if callout.get("selection") == "lines" else reader.box
                    item["callouts"][callout_id] = {
                        "text": _clean(extract(number, callout["bbox"],
                                f"media/overview/{view_id}/{callout_id}")),
                        "label_only": bool(callout["label_only"]),
                    }
                record["views"][view_id] = item
        result[key] = record
    result["operation_panels"] = {}
    for panel in media.get("operation_panels", []):
        number = panel.get("physical_page", pages["operations"] + panel.get("page_offset", 0))
        copy = panel["copy"]
        def field(name, bbox, selection=None, *, copy=copy, number=number, panel_id=panel["id"]):
            selection = copy.get("selection") if selection is None else selection
            extract = reader.lines if selection == "lines" else reader.box
            return _clean(extract(number, bbox, f"media/operations/{panel_id}/{name}"))
        record = {"physical_page": number, "prerequisite": "", "supporting_copy": [],
                  "mode_label": "", "sos_label": "", "steps": []}
        if "prerequisite_bbox" in copy:
            record["prerequisite"] = field("prerequisite", copy["prerequisite_bbox"])
        for index, bbox in enumerate(copy.get("supporting_copy_bboxes", [])):
            record["supporting_copy"].append(field(f"supporting/{index}", bbox))
        for name in ("mode_label", "sos_label"):
            if f"{name}_bbox" in copy:
                record[name] = field(name, copy[f"{name}_bbox"])
        for step in copy["steps"]:
            parts = [{"role": part["role"], "text": field(
                f"steps/{step['id']}/{index}", part["bbox"], part.get("selection"))}
                     for index, part in enumerate(step["parts"])]
            record["steps"].append({"id": step["id"], "parts": parts})
        result["operation_panels"][panel["id"]] = record
    return result


def _target_layout(recipe_root, manifest, language):
    path = "source/target_layout.json"
    if not any(entry["path"] == path for entry in manifest["inputs"]):
        return None
    layout = read_recipe_json(recipe_root, path, manifest)
    if layout.get("schema_version") != "frozen-pdf-target-layout/v1" or layout.get("target") != {
        key: manifest["target"][key] for key in ("model", "region")
    }:
        raise ValueError("target layout identity disagrees with source manifest")
    return {**layout, **layout.get("locales", {}).get(language, {})}


def _reference_captions(reader, figures):
    captions = {}
    for figure in figures:
        slug = figure["slug"]
        if slug in captions:
            raise ValueError(f"duplicate native reference captions: {slug}")
        number = figure["physical_page"]
        labels = []
        for index, item in enumerate(figure["labels"]):
            extract = reader.lines if item.get("selection") == "lines" else reader.box
            value = _clean(extract(number, item["bbox"], f"reference_captions/{slug}/{index}"))
            if not value:
                raise ValueError(f"empty native reference caption: {slug}/{index}")
            labels.append({"text": value, "bbox": list(item["bbox"])})
        if not labels:
            raise ValueError(f"missing native reference captions: {slug}")
        captions[slug] = {"physical_page": number, "labels": labels}
    return captions


def _target_safety(reader, safety, sections):
    number = sections[0]["physical_pages"][0]
    record = {name: _clean(reader.box(number, safety[f"{name}_bbox"], f"safety/{name}"))
              for name in ("warning", "lead", "intro", "precautions",
                           "maintenance_heading", "maintenance_body")}
    record["precautions"] = [value.strip() for value in record["precautions"].split("•")[1:]]
    if len(record["precautions"]) != safety["expected_precautions"]:
        raise ValueError("safety precautions disagree with target source recipe")
    return record


def _target_records(reader, layout, sections):
    records = {"media": _media_records(reader, layout, sections)}
    controls = layout.get("app", {}).get("control_labels")
    if controls:
        records["app_control_labels"] = {"rows": [{
            "role": item["role"],
            "text": _clean(reader.box(item["page"], item["bbox"], f"app/control_labels/{index}")),
            "physical_page": item["page"], "bbox": list(item["bbox"]),
        } for index, item in enumerate(controls)]}
    if layout.get("reference_captions"):
        records["reference_captions"] = _reference_captions(reader, layout["reference_captions"])
    if layout.get("native_body_headings"):
        records["native_body_headings"] = {"rows": [{
            "section_id": item["section_id"], "physical_page": item["physical_page"],
            "block_bbox": list(item["block_bbox"]),
            "heading": _clean(reader.lines(item["physical_page"], item["heading_bbox"],
                                     f"native_body_headings/{index}")),
            "level": item["level"],
        } for index, item in enumerate(layout["native_body_headings"])]}
    if layout.get("safety"):
        records["safety"] = _target_safety(reader, layout["safety"], sections)
    return records


def _target_table_headers(reader, layout, source, records):
    headers = {}
    for kind, boxes in layout.get("table_headers", {}).items():
        number = (records["symbols"]["physical_page"] if kind == "symbols" else
                  source["tables"][kind]["physical_page"])
        headers[kind] = [_clean(reader.box(number, bbox, f"table_headers/{kind}/{index}"))
                         for index, bbox in enumerate(boxes)]
    return headers


def _preface_candidate(recipe_root, manifest, layout, language):
    binding = (layout or {}).get("preface_candidate")
    if not binding:
        return None
    status = binding.get("status")
    if status not in {"preview-only-pending-review", "operator-approved"}:
        raise ValueError("preface candidate has no supported review status")
    candidate = read_recipe_json(recipe_root, binding["path"], manifest)[language]
    if not candidate.get("heading") or not candidate.get("paragraphs") or any(
            not row.get("text") for row in candidate["paragraphs"]):
        raise ValueError("incomplete preface candidate")
    if status == "preview-only-pending-review":
        if any(row.get("status") not in {"shared-copy-candidate", "pending-legal-subject-review"}
               for row in candidate["paragraphs"]):
            raise ValueError("pending preface paragraph has unsupported status")
        return {"status": status, "content": candidate}
    approval = binding.get("approval")
    if (not isinstance(approval, dict) or
            not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(approval.get("date", ""))) or
            not all(str(approval.get(key, "")).strip() for key in ("instruction", "scope"))):
        raise ValueError("approved preface requires dated operator decision")
    if any(row.get("status") != "operator-approved" or row.get("operator_decision") != approval
           for row in candidate["paragraphs"]):
        raise ValueError("approved preface paragraphs disagree with operator decision")
    return {"status": status, "approval": approval, "content": candidate}


def _warranty_years(records):
    for prefix in ("standard", "extension"):
        raw = records["warranty_columns"]["blocks"][f"{prefix}_heading"]["raw_text"]
        numbers = re.findall(r"^\s*(\d+)\s*$", raw, flags=re.MULTILINE)
        if len(numbers) != 1:
            raise ValueError(f"{prefix}: warranty year is not a unique source line")
        records["warranty_columns"][f"{prefix}_years"] = int(numbers[0])


def _verify_sibling_ai(pdf_path, original, provenance):
    ai_path = pdf_path.parent / original["filename"]
    if not ai_path.is_file():
        return
    if file_sha256(ai_path) != original["sha256"]:
        raise ValueError("sibling AI original disagrees with source provenance")
    provenance["ai_identity_origin"] = "verified sibling AI original"


def load_pdf_book(pdf_path: Path, language: str, recipe_root: Path) -> dict:
    """Fresh selectable PDF text plus structural recipes; no writes or images.

    ``recipe_root`` is the historical four-language package directory. Its
    text-bearing values are never used to fill, locate or repair new copy.
    Missing rectangles/headings fail closed rather than falling back to JSON.
    """
    pdf_path, recipe_root = Path(pdf_path).resolve(), Path(recipe_root).resolve()
    manifest = json.loads((recipe_root / "source_manifest.json").read_text(encoding="utf-8"))
    layout = _target_layout(recipe_root, manifest, language)
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
        titles = _chapter_titles(document, sections, layout)
        records = {name: reader.positioned(_read(recipe_root, name, manifest)["locales"][language], field=name)
                   for name in ("operation_tables", "warranty_columns", "app_sections")}
        _warranty_years(records)
        records["symbols"] = _symbols(reader, _read(recipe_root, "symbols", manifest)["locales"][language], language,
                                      (layout or {}).get("symbol_layout"))
        records["lcd_indicators"] = _lcd(reader, _read(recipe_root, "lcd_indicators", manifest)["locales"][language])
        if layout:
            records.update(_target_records(reader, layout, sections))
        for record in records.values():
            record["source_sha256"] = pdf_hash
        source = {
            "schema_version": (layout or {}).get("direct_source_schema", "je1000f-eu-four-locale-direct-source/v1"), "locale": language,
            "source_path": pdf_path.name, "source_sha256": pdf_hash,
            "method": "fresh PyMuPDF PDF text objects; geometry recipe only; no OCR, translation or image extraction",
            "sections": sections, "pages": pages,
            "tables": {
                "troubleshooting": _faults(reader, old_source["tables"]["troubleshooting"]["physical_page"],
                                           (layout or {}).get("troubleshooting")),
                "specifications": _specifications(reader, old_source["tables"]["specifications"]["physical_page"],
                                                  (layout or {}).get("specifications")),
            },
        }
        if layout and layout.get("table_headers"):
            source["table_headers"] = _target_table_headers(reader, layout, source, records)
        preface_candidate = _preface_candidate(recipe_root, manifest, layout, language)
        front_back = _front_back(reader, _read(recipe_root, "front_back_source", manifest), language,
                                 pdf_hash, preface_candidate)
        locale = {"label": language, "physical_pages": [pages[0]["physical_page"], pages[-1]["physical_page"]],
                  "titles": [title["text"] for title in titles]}
        provenance = {"pdf": {"filename": pdf_path.name, "sha256": pdf_hash, "page_count": len(document)},
                      "ai": manifest["original_source"], "ai_identity_origin": "historical source manifest",
                      "geometry_recipe_sha256": file_sha256(recipe_root / "source_manifest.json"),
                      "chapter_spans": titles, "text_spans": reader.spans,
                      "unresolved_text": reader.unresolved,
                      "corrections_applied": [], "image_extraction_performed": False}
        pending = list((layout or {}).get("pending_source_review", []))
        if preface_candidate and preface_candidate["status"] == "preview-only-pending-review":
            pending.append("preface")
        if pending:
            provenance["pending_source_review"] = sorted(set(pending))
        _verify_sibling_ai(pdf_path, manifest["original_source"], provenance)
    return {"source": source, "index": {"section_ids": [s["id"] for s in sections], "languages": {language: locale}},
            "locale": locale, "records": records, "front_back": front_back, "provenance": provenance,
            "target_layout": layout}


__all__ = ["load_pdf_book"]
