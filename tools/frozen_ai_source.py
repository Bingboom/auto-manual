"""Positioned AI extraction adapter; emits semantics, never finished Web HTML."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
import re
import shutil

from tools.frozen_ai_flow import callout, cell, heading, is_heading, node, paragraph, prose, scroll_table, squash, text
from tools.frozen_ai_media_components import app_nodes, figure_node
from tools.frozen_ai_table_components import (
    auto_resume_flow, lcd_mode_flow, symbol_signal_flow, warranty_flow,
)
from tools.manual_ir.hashing import file_sha256
from tools.manual_ir.components import component_flow_node
from tools.component_specs.key_combinations import key_combinations_component_spec


def _key(value):
    return re.sub(r"\W+", "", squash(value), flags=re.UNICODE).casefold()


def _positioned_headers(book, kind, boxes):
    number = (book.records["symbols"]["physical_page"] if kind == "symbols" else
              book.source["tables"][kind]["physical_page"])
    blocks = book.page(number)["blocks_visual_order"]
    values = []
    for bbox in boxes:
        selected = [squash(block["text"]) for block in blocks
                    if bbox[0] <= block["bbox"][0] < bbox[2]
                    and bbox[1] <= block["bbox"][1] < bbox[3]]
        if not selected:
            raise ValueError(f"{kind}: header source rectangle is empty")
        values.append(" ".join(selected))
    return values


def _in_box(block, bbox):
    x, y = block["bbox"][:2]
    return bbox[0] <= x < bbox[2] and bbox[1] <= y < bbox[3]


def _positioned_callouts(book, blocks, number, labels):
    result, consumed = {}, set()
    for recipe in (getattr(book, "target_layout", None) or {}).get("callout_regions", []):
        if recipe["physical_page"] != number:
            continue
        label_indexes = [i for i, block in enumerate(blocks)
                         if _in_box(block, recipe["label_bbox"])]
        if len(label_indexes) != 1:
            raise ValueError(f"page {number}: native notice label is not unique")
        label_index = label_indexes[0]
        label = squash(blocks[label_index]["text"])
        if label.casefold() not in labels:
            raise ValueError(f"page {number}: native notice label is unknown")
        body_indexes = []
        for bbox in recipe["body_bboxes"]:
            matched = [i for i, block in enumerate(blocks)
                       if i != label_index and _in_box(block, bbox)]
            if not matched:
                raise ValueError(f"page {number}: native notice body rectangle is empty")
            body_indexes.extend(matched)
        indexes = {label_index, *body_indexes}
        if len(indexes) != 1 + len(body_indexes) or indexes & consumed:
            raise ValueError(f"page {number}: native notice regions overlap")
        body = [node for i in sorted(body_indexes)
                for node in prose(book.correct(squash(blocks[i]["text"]))) ]
        result[min(indexes)] = callout(label, body, variant=labels[label.casefold()],
                                       language=book.language,
                                       source_ref=f"{book.language}/page-{number}/notice-{label_index}")
        consumed.update(indexes)
    return result, consumed


def _adjacent_notice_candidates(blocks, index, consumed):
    label = blocks[index]
    _, y0, x1, y1 = label["bbox"]
    candidates = [(j, b) for j, b in enumerate(blocks) if j != index and j not in consumed
                  and b["bbox"][0] >= x1 + 2 and b["bbox"][1] <= y1 + 2
                  and b["bbox"][3] >= y0 - 2]
    if not candidates:
        return []
    last = max(b["bbox"][3] for _, b in candidates)
    for j, block in enumerate(blocks):
        if j not in consumed and j not in {k for k, _ in candidates} and block["bbox"][0] >= x1 + 2 and 0 <= block["bbox"][1] - last <= 4:
            candidates.append((j, block))
            last = block["bbox"][3]
    return candidates


def _inferred_callouts(book, blocks, number, labels, result, consumed):
    for index, label in enumerate(blocks):
        if index in consumed:
            continue
        value = squash(label["text"])
        lines = [line.strip() for line in label["text"].splitlines() if line.strip()]
        if len(lines) > 1 and lines[-1].casefold() in labels:
            notice = lines[-1]
            body = prose(book.correct(squash("\n".join(lines[:-1]))))
            result[index] = callout(notice, body, variant=labels[notice.casefold()], language=book.language,
                                    source_ref=f"{book.language}/page-{number}/notice-{index}")
            consumed.add(index)
            continue
        if value.casefold() not in labels or label["bbox"][0] > 90:
            continue
        candidates = _adjacent_notice_candidates(blocks, index, consumed)
        if not candidates:
            continue
        indexes = {index, *(j for j, _ in candidates)}
        if indexes & consumed:
            raise ValueError(f"overlapping notice source on page {number}")
        body = [n for _, b in sorted(candidates) for n in prose(book.correct(squash(b["text"])))]
        result[min(indexes)] = callout(value, body, variant=labels[value.casefold()], language=book.language,
                                       source_ref=f"{book.language}/page-{number}/notice-{index}")
        consumed.update(indexes)
    return result, consumed


class FrozenBook:
    """Interpret the already approved extraction and explicit source errata."""

    def __init__(self, source_root: Path, output: Path, language: str):
        self.source_root, self.output, self.language = source_root.resolve(), output.resolve(), language
        self.manifest = self.read("source_manifest.json")
        self.target = self.manifest["target"]
        if language not in self.target["languages"]:
            raise ValueError("language is outside the frozen source target")
        self.hashes: dict[str, str] = {}
        for entry in self.manifest["inputs"]:
            path = (self.source_root / entry["path"]).resolve()
            if (not path.is_relative_to(self.source_root) or not path.is_file()
                    or file_sha256(path) != entry["sha256"] or path.stat().st_size != entry["size"]):
                raise ValueError(f"frozen source changed: {entry['path']}")
        self.source = self.read(f"source/{language}_direct_source.json")
        self.index = self.read("source/section_index.json")
        self.locale = self.index["languages"][language]
        self.errata = self.read("source/errata.json")
        self.records = {name: self.read(f"source/{name}.json")["locales"][language]
                        for name in ("symbols", "lcd_indicators", "operation_tables", "warranty_columns", "app_sections")}
        self.front_back = self.read("source/front_back_source.json")
        expected = self.manifest["original_source"]["sha256"]
        if self.source["source_sha256"] != expected or self.front_back["source_sha256"] != expected:
            raise ValueError("extraction original-source identity disagrees")
        self.figures = self.read(f"source/{language}_figure_manifest.json")["figures"]
        self.art = {}
        for figure in self.figures:
            path = f"figures/{language}/{Path(figure['path']).name}"
            digest = figure["sha256"]
            for entry in self.errata["entries"]:
                for correction in entry.get("asset_corrections", []):
                    if correction["raw_asset"]["path"] == path:
                        if digest != correction["raw_asset"]["sha256"]:
                            raise ValueError("erratum does not match the original artwork")
                        path, digest = (correction["corrected_web_asset"][k] for k in ("path", "sha256"))
            self.art[figure["slug"]] = {"asset_ref": self.asset(path, digest), "sha256": digest}
        self.icon_refs = [self.asset(f"figures/{language}/{Path(row['icon_path']).name}", row["icon_sha256"])
                          for row in self.records["symbols"]["pictograms"]]

    def read(self, path):
        return json.loads((self.source_root / path).read_text(encoding="utf-8"))

    def asset(self, relative, expected):
        source = (self.source_root / relative).resolve()
        if not source.is_relative_to(self.source_root) or file_sha256(source) != expected:
            raise ValueError(f"asset changed: {relative}")
        destination = f"assets/{expected[:12]}_{source.name}"
        path = self.output / destination
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, path)
        self.hashes[destination] = expected
        return destination

    def correct(self, value):
        for entry in self.errata["entries"]:
            if entry["locale"] == self.language:
                if value == entry["source_text"] or entry["id"].endswith("USB-C"):
                    value = value.replace(entry["source_text"], entry["corrected_text"])
        return value

    def figure(self, figure):
        art = self.art[figure["slug"]]
        title = self.locale["titles"][self.index["section_ids"].index(figure["section_id"])]
        return figure_node(asset_ref=art["asset_ref"], content_sha256=art["sha256"],
                           reference_id=figure["slug"], alt=f"{title}: {figure['slug'].replace('_', ' ')}",
                           language=self.language, source_ref=f"{self.language}/page-{figure['physical_page']}/{figure['slug']}")

    def page(self, number):
        return next(page for page in self.source["pages"] if page["physical_page"] == number)

    def starts(self):
        starts = []
        for section_id, title in zip(self.index["section_ids"], self.locale["titles"]):
            page_no = next(s["physical_pages"][0] for s in self.source["sections"] if s["id"] == section_id)
            matches = [(page_no, b["bbox"][1], section_id) for b in self.page(page_no)["blocks_visual_order"]
                       if _key(b["text"]) == _key(title)]
            if not matches:
                raise ValueError(f"missing section heading: {section_id}")
            starts.append(min(matches))
        if starts != sorted(starts):
            raise ValueError("section order disagrees with source")
        return starts

    def headers(self, kind):
        extracted = self.source.get("table_headers", {}).get(kind)
        if extracted:
            return list(extracted)
        boxes = (getattr(self, "target_layout", None) or {}).get("table_headers", {}).get(kind)
        if boxes:
            return _positioned_headers(self, kind, boxes)
        if kind == "symbols":
            number = self.records["symbols"]["physical_page"]
            return next([squash(s) for s in b["text"].splitlines()]
                        for b in self.page(number)["blocks_visual_order"]
                        if 365 <= b["bbox"][1] < 390 and len(b["text"].splitlines()) == 2)
        record = self.source["tables"][kind]
        blocks = self.page(record["physical_page"])["blocks_visual_order"]
        if kind == "troubleshooting":
            return next([squash(s) for s in b["text"].splitlines()] for b in blocks if 250 <= b["bbox"][1] < 260)
        return [squash(next(b["text"] for b in blocks if low <= b["bbox"][1] < high and is_heading(b["text"])))
                for low, high in ((50, 70), (175, 195), (235, 260), (370, 392))]

    def footnotes(self):
        page = self.page(self.source["tables"]["specifications"]["physical_page"])
        bbox = (getattr(self, "target_layout", None) or {}).get("specification_footnotes_bbox")
        if bbox:
            blocks = sorted((b for b in page["blocks_visual_order"]
                             if bbox[0] <= b["bbox"][0] < bbox[2]
                             and bbox[1] <= b["bbox"][1] < bbox[3]),
                            key=lambda b: (b["bbox"][1], b["bbox"][0]))
            if not blocks:
                raise ValueError("specification footnotes rectangle is empty")
            notes = [squash(b["text"]) for b in blocks]
            if notes and notes[0].startswith("※") and re.search(r"\s®\s®$", notes[0]):
                value = re.sub(r"\s®\s®$", "", notes[0])
                if value.count("USB Type-C") != 1 or value.count("USB-C") != 1:
                    raise ValueError("ambiguous native USB trademark glyph positions")
                notes[0] = value.replace("USB Type-C", "USB Type-C®", 1).replace("USB-C", "USB-C®", 1)
            return [paragraph(value) for value in notes]
        blocks = sorted((b for b in page["blocks_visual_order"] if 420 <= b["bbox"][1] < 490),
                        key=lambda b: (b["bbox"][1], b["bbox"][0]))
        notes = []
        for block in blocks:
            value = squash(block["text"])
            if value.startswith(("※", "①")):
                notes.append(value)
            elif notes:
                notes[-1] += " " + value
        notes[0] = re.sub(r"\s*®\s*®\s*$", "", notes[0])
        notes[0] = notes[0].replace("USB Type-C", "USB Type-C®", 1).replace("USB-C", "USB-C®", 1)
        return [paragraph(value) for value in notes]

    def special(self, section):
        args = {"language": self.language, "source_ref": f"{self.language}/{section}"}
        title = self.locale["titles"][self.index["section_ids"].index(section)]
        if section == "symbols":
            return symbol_signal_flow(self.records["symbols"], headings=self.headers("symbols"),
                                      accessibility_label=title, **args)
        if section == "warranty":
            record = deepcopy(self.records["warranty_columns"])
            for block in record["blocks"].values():
                if "text" in block:
                    block["text"] = self.correct(block["text"])
            return warranty_flow(record, **args)
        if section == "app_setup":
            return list(app_nodes(self.records["app_sections"], self.art, **args))
        if section == "lcd_display":
            figure = next(f for f in self.figures if f["slug"] == "lcd_display")
            rows = [[cell(str(row["number"]), header=True),
                     node("table_cell", [node("strong", [text(row["label"])]), node("line_break"), text(row["meaning"])], header=False)]
                    for row in self.records["lcd_indicators"]["rows"]]
            # lcd-text-only is a four-column legacy contract that hides its
            # first two columns. This source has a numbered, two-column legend.
            return [self.figure(figure), scroll_table(rows)]
        return []

    def operation(self, part):
        record = self.records["operation_tables"][part]
        if part == "lcd_mode":
            return lcd_mode_flow(record, artwork_ref=self.art["lcd_mode_art"]["asset_ref"],
                                 accessibility_label=self.locale["titles"][4], language=self.language,
                                 source_ref=f"{self.language}/operations/lcd_mode")
        result = [heading(squash(record["heading"]["text"]))]
        if part == "restore":
            result.append(paragraph(squash(record["intro"]["text"])))
            result.extend(auto_resume_flow(record, language=self.language,
                                           source_ref=f"{self.language}/operations/restore"))
        else:
            rows = []
            for row in record["rows"]:
                buttons = " + ".join(self.correct(squash(b["text"])) for b in row["buttons"])
                rows.append([buttons, squash(row["operation"]["text"]), squash(row["function"]["text"])])
            spec = key_combinations_component_spec(
                headers=[squash(h["text"]) for h in record["headers"]], rows=rows,
                source_ref=f"{self.language}/operations/shortcuts", language=self.language,
            )
            result.append(component_flow_node(spec, root=True))
        return result

    def callouts(self, blocks, number):
        """Bind left-hand notice labels to their adjacent source body rectangles."""
        labels = {row["label"].casefold(): variant for row, variant in zip(self.records["symbols"]["rows"], ("warning", "caution", "note", "tip"))}
        result, consumed = _positioned_callouts(self, blocks, number, labels)
        return _inferred_callouts(self, blocks, number, labels, result, consumed)
