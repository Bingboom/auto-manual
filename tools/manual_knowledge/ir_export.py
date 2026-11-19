"""All-region ManualIR v2 native knowledge corpus and observation exporter."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import hashlib
import html as html_lib
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterator, Mapping, Sequence

from bs4 import BeautifulSoup

from tools import lang_registry
from tools.check.docs_capability import load_capabilities
from tools.corpus.discover import SUPPORTED_IR_SCHEMA_VERSION, default_scan_roots
from tools.manual_ir.flow import flow_nodes_to_html
from tools.manual_knowledge.carriers import (
    COMPLIANCE_TITLE,
    HOUSEHOLD_WASTE,
    LEGISLATION,
    MARK,
    MARKING_ICONS,
    SAFETY_TITLE,
    SYMBOL_TITLE,
    Carrier,
)
from tools.manual_knowledge.export import SCHEMA as CORPUS_SCHEMA
from tools.manual_knowledge.html import identity
from tools.manual_knowledge.identity import callout_severity, variant_identity
from tools.manual_knowledge.observe import (
    FEATURE_SOURCE,
    GENERATOR_VERSION as OBS_GENERATOR_VERSION,
    SCHEMA as OBS_SCHEMA,
    build_observations,
    content_sha256,
    judge_previous,
    summarize,
)
from tools.manual_knowledge.relations import build_relations
from tools.manual_knowledge.tables import table_block
from tools.utils.path_utils import PathSegments, repo_root

IR_GENERATOR_VERSION = "manual-knowledge-ir/1.0"
IR_MACHINE_SURFACE: dict[str, str] = {
    "source_kind": "manual_ir_v2",
    "generation_mode": "same_source_native",
    "target_mode": "same_source_native",
    "generator_version": IR_GENERATOR_VERSION,
}

_CJK_SEVERITY: dict[str, str] = {
    "警告": "warning",
    "危険": "warning",
    "위험": "warning",
    "경고": "warning",
    "危险": "warning",
    "危險": "warning",
    "danger": "warning",
    "peligro": "warning",
    "注意": "caution",
    "ご注意": "caution",
    "小心": "caution",
    "주의": "caution",
    "注記": "note",
    "メモ": "note",
    "注": "note",
    "備考": "note",
    "補足": "note",
    "注釈": "note",
    "説明": "note",
    "說明": "note",
    "说明": "note",
    "备注": "note",
    "備註": "note",
    "重要": "note",
    "참고": "note",
    "중요": "note",
    "ヒント": "tip",
    "提示": "tip",
    "팁": "tip",
}

_IR_COMPLIANCE_TITLE = re.compile(
    r"規格|適合|규정|준수|法规|法規|合规|合規|認証|인증|\b(?:FCC|PSE|KC|TELEC|UL|CCC|BSMI|NCC)\b"
)
_IR_SAFETY_TITLE = re.compile(
    r"安全|注意事項|注意事[項项]|安全上の注意|安全上のご注意|안전|주의사항"
)
_IR_SYMBOL_TITLE = re.compile(r"記号|絵表示|기호|符号|符號|圖示")
_IR_MARK = re.compile(r"\b(?:PSE|KC|TELEC|UL|CCC|BSMI|NCC|VCCI|ISED|METI)\b")
_SIGNAL_PREFIX = re.compile(r"^\W*([^\W\d_:：\s]+(?:\s+[^\W\d_:：\s]+)?)\s*[:：]\s*")
_BARE_SIGNAL = re.compile(r"^\W*([^\W\d_]+)\s+(?=\S)")
_DECORATIVE_CLASSES = frozenset({
    "headerlink",
    "manual-callout-label-sizer",
    "hb-signal-icon",
    "hb-composite-stage",
    "hb-leader-layer",
    "hb-operation-step-marker",
    "manual-feedback",
    "product-voc",
})
_HIDDEN_STYLE_RE = re.compile(r"(?:^|;)\s*(?:display\s*:\s*none|visibility\s*:\s*hidden)\b", re.I)
_BREAK_KINDS = frozenset({
    "paragraph",
    "group",
    "heading",
    "definition_term",
    "definition_description",
    "caption",
    "list_item",
    "table_row",
})
_PARA_KINDS = frozenset({"paragraph", "preformatted", "definition_term", "definition_description", "caption"})
_GROUP_KINDS = frozenset({"group", "section", "quote", "blockquote", "figure", "definition_list"})
_INLINE_KINDS = frozenset({"text", "strong", "emphasis", "inline_group", "line_break", "link"})

_IR_CJK_TOPICS: dict[str, re.Pattern[str]] = {
    "electrical_shock": re.compile(r"感電|触电|觸電|감전"),
    "charging": re.compile(r"充電|充电|충전"),
    "storage_transport": re.compile(r"保管|輸送|存放|运输|運輸|보관|운송"),
    "disposal": re.compile(r"廃棄|废弃|廢棄|폐기"),
    "children": re.compile(r"子供|お子様|子ども|儿童|兒童|어린이"),
    "fire": re.compile(r"火災|発火|火灾|火源|화재|발화"),
    "water": re.compile(r"水|濡|湿気|液体|물|습기"),
    "disassembly": re.compile(r"分解|修理|拆卸|拆解|분해|수리"),
    "temperature": re.compile(r"温度|溫度|高温|高溫|低温|低溫|온도"),
    "battery": re.compile(r"バッテリー|電池|电池|배터리"),
    "grounding": re.compile(r"アース|接地|접지"),
    "pv_input": re.compile(r"ソーラー|太陽光|太阳能|太陽能|태양광"),
    "app_wireless": re.compile(r"アプリ|無線|无线|앱|무선"),
    "connection": re.compile(r"接続|插头|连接|連接|연결|플러그"),
}


def ir_callout_severity(label: str) -> str:
    """Resolve localized EU and CJK/KR callout labels without guessing icon-only labels."""
    cleaned = label.strip().lstrip("*").strip().rstrip(":：").strip()
    if not cleaned:
        return "unknown"
    eu_severity = callout_severity(cleaned)
    if eu_severity != "unknown":
        return eu_severity
    return _CJK_SEVERITY.get(cleaned.casefold(), "unknown")


def ir_section_kind(title: str) -> str | None:
    """Classify EU, US, and CJK/KR section headings into compliance, safety, or symbols."""
    if COMPLIANCE_TITLE.search(title) or _IR_COMPLIANCE_TITLE.search(title):
        return "compliance"
    if SAFETY_TITLE.search(title) or _IR_SAFETY_TITLE.search(title):
        return "safety"
    if SYMBOL_TITLE.search(title) or _IR_SYMBOL_TITLE.search(title):
        return "symbols"
    return None


def ir_legislation(text: str) -> list[str]:
    """Extract EU and all-region regulatory marks/legislation codes as written."""
    matches = LEGISLATION.findall(text) + MARK.findall(text) + _IR_MARK.findall(text)
    return sorted({" ".join(m.split()) for m in matches})


def ir_cjk_topics(text: str) -> list[str]:
    """Return CJK/KR topic tags matched in ``text``."""
    return [topic for topic, pattern in _IR_CJK_TOPICS.items() if pattern.search(text)]


def _first_str(mapping: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        val = mapping.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return ""


def _normalize_whitespace(text: str) -> str:
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _strip_html(raw: str) -> str:
    if "<" not in raw and "&" not in raw:
        return _normalize_whitespace(raw)
    if "<" not in raw:
        return _normalize_whitespace(html_lib.unescape(raw))
    soup = BeautifulSoup(raw, "html.parser")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    return _normalize_whitespace(soup.get_text(" "))


def _html_attrs(node: Mapping[str, Any]) -> Mapping[str, Any]:
    pres = node.get("presentation")
    if not isinstance(pres, Mapping):
        return {}
    html_info = pres.get("html")
    if not isinstance(html_info, Mapping):
        return {}
    attrs = html_info.get("attributes")
    return attrs if isinstance(attrs, Mapping) else {}


def _presentation_classes(node: Mapping[str, Any]) -> tuple[str, ...]:
    raw = _html_attrs(node).get("class")
    if isinstance(raw, list):
        return tuple(str(item).strip() for item in raw if str(item).strip())
    if isinstance(raw, str):
        return tuple(part for part in raw.split() if part)
    return ()


def _is_hidden(node: Mapping[str, Any]) -> bool:
    if node.get("hidden") is True:
        return True
    attrs = _html_attrs(node)
    if not attrs:
        return False
    classes = set(_presentation_classes(node))
    if "hidden" in attrs or bool(classes & _DECORATIVE_CLASSES):
        return True
    return bool(_HIDDEN_STYLE_RE.search(str(attrs.get("style") or "")))


def _inline_parts(node: Mapping[str, Any]) -> Iterator[str]:
    if _is_hidden(node):
        return
    kind = str(node.get("kind") or "")
    if kind == "text":
        yield re.sub(r"\s+", " ", str(node.get("text") or ""))
        return
    if kind == "comment":
        return
    if kind == "line_break":
        yield "\n"
        return
    if kind in _BREAK_KINDS:
        yield "\n"
    for child in node.get("children") or ():
        if isinstance(child, Mapping):
            yield from _inline_parts(child)
    if kind in _BREAK_KINDS:
        yield "\n"


def _flow_text(node: Mapping[str, Any]) -> str:
    return _normalize_whitespace("".join(_inline_parts(node)))


def _collect_images(node: Mapping[str, Any]) -> list[str]:
    if _is_hidden(node):
        return []
    if node.get("kind") == "image":
        return [str(node.get("alt") or "").strip()]
    alts: list[str] = []
    for child in node.get("children") or ():
        if isinstance(child, Mapping):
            alts.extend(_collect_images(child))
    return alts


@dataclass
class _SectionAccumulator:
    doc_key: str
    sections: list[dict[str, Any]] = field(default_factory=list)
    current: dict[str, Any] = field(
        default_factory=lambda: {"title": "Manual introduction", "level": 1, "anchor": "", "page_id": "", "blocks": []}
    )
    headings_count: int = 0
    images_count: int = 0
    images_with_alt_count: int = 0
    components_count: int = 0
    _seen_ids: Counter[str] = field(default_factory=Counter)

    def _next_section_id(self, anchor: str, page_id: str) -> str:
        raw_key = f"{self.doc_key}#{anchor or page_id}"
        base = identity(raw_key)
        count = self._seen_ids[base]
        self._seen_ids[base] += 1
        return base if count == 0 else identity(f"{raw_key}:{count}")

    def flush(self) -> None:
        if not self.current["blocks"]:
            return
        sec_id = self._next_section_id(self.current["anchor"], self.current["page_id"])
        default_ref = f"{self.current['page_id']}#{self.current['anchor']}" if self.current["anchor"] else self.current["page_id"]
        for index, block in enumerate(self.current["blocks"]):
            block["block_id"] = f"{sec_id}:{index}"
            if not block.get("source_ref"):
                block["source_ref"] = default_ref
        self.sections.append({
            "id": sec_id,
            "level": self.current["level"],
            "title": self.current["title"],
            "blocks": self.current["blocks"],
        })

    def start_section(self, title: str, level: int, anchor: str, page_id: str) -> None:
        self.flush()
        self.current = {"title": title, "level": level, "anchor": anchor, "page_id": page_id, "blocks": []}

    def add_block(self, block: dict[str, Any], *, source_ref: str, component_id: str | None = None) -> None:
        if source_ref and not block.get("source_ref"):
            block["source_ref"] = source_ref
        if component_id:
            block["component_id"] = component_id
        self.current["blocks"].append(block)

    def record_image_alts(self, alts: Sequence[str]) -> None:
        for alt in alts:
            self.images_count += 1
            if alt.strip():
                self.images_with_alt_count += 1

    def add_image(self, alt: str, *, source_ref: str, component_id: str | None = None) -> None:
        cleaned = alt.strip()
        self.record_image_alts((cleaned,))
        self.add_block(
            {"type": "image", "text": cleaned, "evidence_kind": "image_alt", "transcribed": False},
            source_ref=source_ref,
            component_id=component_id,
        )

    def coverage(self) -> dict[str, int]:
        blocks = [b for sec in self.sections for b in sec["blocks"]]
        counts = Counter(b["type"] for b in blocks)
        return {
            "sections": len(self.sections),
            "blocks": len(blocks),
            "headings": self.headings_count,
            "paragraphs": counts.get("paragraph", 0),
            "lists": counts.get("list", 0),
            "tables": counts.get("table", 0),
            "callouts": counts.get("callout", 0),
            "images": self.images_count,
            "images_with_alt": self.images_with_alt_count,
            "components": self.components_count,
        }


def _int_or(value: Any, default: int) -> int:
    if isinstance(value, bool):
        return default
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default


def _list_item_children(item: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [c for c in (item.get("children") or ()) if isinstance(c, Mapping)]


def _format_list_item(item: Mapping[str, Any], ordered: bool, number: int) -> dict[str, Any]:
    children = _list_item_children(item)
    nested = [_list_block_from_flow(c) for c in children if c.get("kind") == "list"]
    non_nested = [c for c in children if c.get("kind") != "list"]
    text = _normalize_whitespace("".join("".join(_inline_parts(c)) for c in non_nested))
    return {"text": text, "children": nested, "number": number if ordered else None}


def _list_block_from_flow(node: Mapping[str, Any]) -> dict[str, Any]:
    ordered = bool(node.get("ordered"))
    reversed_order = bool(node.get("reversed"))
    raw_items = [c for c in (node.get("children") or ()) if isinstance(c, Mapping) and c.get("kind") == "list_item"]
    number = _int_or(node.get("start"), len(raw_items) if reversed_order else 1)
    start = str(number)
    items: list[dict[str, Any]] = []
    for item in raw_items:
        items.append(_format_list_item(item, ordered, number))
        number += -1 if reversed_order else 1
    lines: list[str] = []
    for it in items:
        prefix = f"{it['number']}. " if ordered else "• "
        child_txt = "".join("\n" + ch["text"] for ch in it["children"])
        lines.append(prefix + it["text"] + child_txt)
    return {"type": "list", "ordered": ordered, "start": start, "reversed": reversed_order, "items": items, "text": "\n".join(lines)}


def _collect_table_rows(node: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows: list[Mapping[str, Any]] = []
    for child in node.get("children") or ():
        if not isinstance(child, Mapping):
            continue
        kind = child.get("kind")
        if kind == "table_row":
            rows.append(child)
        elif kind in {"table_head", "table_body", "table_foot"}:
            rows.extend(_collect_table_rows(child))
    return rows


def _table_cell_dict(cell: Mapping[str, Any], column: int, acc: _SectionAccumulator) -> dict[str, Any]:
    alts = _collect_images(cell)
    acc.record_image_alts(alts)
    text = _flow_text(cell) or " / ".join(alt for alt in alts if alt)
    rowspan = max(1, min(64, _int_or(cell.get("row_span", cell.get("rowspan")), 1)))
    colspan = max(1, min(64, _int_or(cell.get("column_span", cell.get("colspan")), 1)))
    result: dict[str, Any] = {
        "text": text,
        "column": column,
        "header": bool(cell.get("header")),
        "rowspan": rowspan,
        "colspan": colspan,
    }
    if alts:
        result["image_alts"] = alts
        result["image_text_coverage"] = "alt_only_no_ocr"
    return result


def _mark_occupied(occupied: dict[tuple[int, int], str], row_idx: int, col: int, cell: Mapping[str, Any]) -> None:
    for r in range(row_idx, row_idx + cell["rowspan"]):
        for c in range(col, col + cell["colspan"]):
            occupied.setdefault((r, c), str(cell["text"]))


def _table_from_flow(node: Mapping[str, Any], acc: _SectionAccumulator) -> dict[str, Any] | None:
    raw_rows = _collect_table_rows(node)
    if not raw_rows:
        return None
    rows: list[list[dict[str, Any]]] = []
    occupied: dict[tuple[int, int], str] = {}
    for row_idx, raw_row in enumerate(raw_rows):
        cells: list[dict[str, Any]] = []
        col = 0
        for child in raw_row.get("children") or ():
            if not isinstance(child, Mapping) or child.get("kind") != "table_cell":
                continue
            while (row_idx, col) in occupied:
                col += 1
            cell = _table_cell_dict(child, col, acc)
            _mark_occupied(occupied, row_idx, col, cell)
            cells.append(cell)
            col += cell["colspan"]
        rows.append(cells)
    width = max((c + 1 for _, c in occupied), default=0)
    grid = [[occupied.get((r, c), "") for c in range(width)] for r in range(len(rows))]
    text = "\n".join(" | ".join(val.replace("\n", "; ") for val in row) for row in grid)
    return {"type": "table", "rows": rows, "grid": grid, "text": text}


def _grid_cell_entry(cell: Mapping[str, Any], col: int) -> dict[str, Any]:
    alts = [str(a).strip() for a in (cell.get("image_alts") or []) if str(a).strip()]
    text = _normalize_whitespace(str(cell.get("text") or "")) or " / ".join(alts)
    entry: dict[str, Any] = {
        "text": text,
        "column": col,
        "header": bool(cell.get("header")),
        "rowspan": 1,
        "colspan": 1,
    }
    if alts:
        entry["image_alts"] = alts
        entry["image_text_coverage"] = "alt_only_no_ocr"
    return entry


def _make_table_from_grid(raw_rows: Sequence[Sequence[dict[str, Any]]]) -> dict[str, Any] | None:
    if not raw_rows:
        return None
    rows: list[list[dict[str, Any]]] = []
    grid: list[list[str]] = []
    for raw_row in raw_rows:
        row_cells = [_grid_cell_entry(cell, col) for col, cell in enumerate(raw_row)]
        rows.append(row_cells)
        grid.append([str(c["text"]) for c in row_cells])
    text = "\n".join(" | ".join(val.replace("\n", "; ") for val in row) for row in grid)
    return {"type": "table", "rows": rows, "grid": grid, "text": text}


def _slot_map(component_spec: Mapping[str, Any]) -> dict[str, Any]:
    raw_slots = component_spec.get("slots")
    if isinstance(raw_slots, Mapping):
        return dict(raw_slots)
    mapped: dict[str, Any] = {}
    if isinstance(raw_slots, Sequence):
        for slot in raw_slots:
            if isinstance(slot, Mapping) and slot.get("role"):
                mapped[str(slot["role"])] = slot.get("content")
    return mapped


def _callout_from_table_flow(node: Mapping[str, Any]) -> dict[str, Any] | None:
    rows = _collect_table_rows(node)
    if not rows:
        return None
    cells = [c for c in (rows[0].get("children") or ()) if isinstance(c, Mapping) and c.get("kind") == "table_cell"]
    if len(cells) < 2:
        return None
    label = _flow_text(cells[0]) or " / ".join(a for a in _collect_images(cells[0]) if a)
    body = _flow_text(cells[1])
    if not label and not body:
        return None
    return {
        "type": "callout",
        "label": label,
        "body": body,
        "severity": ir_callout_severity(label),
        "text": f"{label}: {body}" if label and body else (body or label),
    }


def _extract_callout_component(
    node: Mapping[str, Any],
    slots: Mapping[str, Any],
    comp_id: str,
    acc: _SectionAccumulator,
    *,
    source_ref: str,
) -> None:
    label = _strip_html(str(slots.get("label") or ""))
    body = _strip_html(str(slots.get("body") or ""))
    carrier_flow = node.get("carrier_flow")
    if (not label or not body) and isinstance(carrier_flow, Sequence):
        for carrier_node in carrier_flow:
            if isinstance(carrier_node, Mapping) and carrier_node.get("kind") == "table":
                parsed = _callout_from_table_flow(carrier_node)
                if parsed:
                    label = label or str(parsed["label"])
                    body = body or str(parsed["body"])
                    break
    acc.add_block(
        {
            "type": "callout",
            "label": label,
            "body": body,
            "severity": ir_callout_severity(label),
            "text": f"{label}: {body}" if label and body else (body or label),
        },
        source_ref=source_ref,
        component_id=comp_id,
    )


def _header_row_cells(headers: Any) -> list[dict[str, Any]]:
    if not isinstance(headers, Sequence) or isinstance(headers, (str, bytes)):
        return []
    out: list[dict[str, Any]] = []
    for h in headers:
        raw = _first_str(h, "content_text", "content_html", "text") if isinstance(h, Mapping) else str(h)
        out.append({"text": _strip_html(raw), "header": True})
    return out


def _symbol_panel_rows(panels: Any, acc: _SectionAccumulator) -> list[list[dict[str, Any]]]:
    grid_rows: list[list[dict[str, Any]]] = []
    if not isinstance(panels, Sequence) or isinstance(panels, (str, bytes)):
        return grid_rows
    for panel in panels:
        if not isinstance(panel, Sequence):
            continue
        for entry in panel:
            if not isinstance(entry, Mapping):
                continue
            alt = _strip_html(_first_str(entry, "icon_alt", "label"))
            meaning = _strip_html(_first_str(entry, "meaning_text", "meaning_html", "text"))
            acc.record_image_alts((alt,))
            c0: dict[str, Any] = {"text": alt}
            if alt:
                c0["image_alts"] = [alt]
            grid_rows.append([c0, {"text": meaning}])
    return grid_rows


def _symbol_dict_rows(rows: Any, acc: _SectionAccumulator) -> list[list[dict[str, Any]]]:
    grid_rows: list[list[dict[str, Any]]] = []
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return grid_rows
    for entry in rows:
        if not isinstance(entry, Mapping):
            continue
        label = _strip_html(_first_str(entry, "label", "icon_alt"))
        meaning = _strip_html(_first_str(entry, "meaning_text", "meaning_html", "text"))
        alt = _strip_html(str(entry.get("icon_alt") or ""))
        if alt:
            acc.record_image_alts((alt,))
        c0: dict[str, Any] = {"text": label}
        if alt:
            c0["image_alts"] = [alt]
        grid_rows.append([c0, {"text": meaning}])
    return grid_rows


def _extract_symbol_component(
    slots: Mapping[str, Any],
    comp_id: str,
    acc: _SectionAccumulator,
    *,
    source_ref: str,
) -> None:
    grid_rows: list[list[dict[str, Any]]] = []
    hdr = _header_row_cells(slots.get("headers"))
    if hdr:
        grid_rows.append(hdr)
    grid_rows.extend(_symbol_panel_rows(slots.get("panels"), acc))
    grid_rows.extend(_symbol_dict_rows(slots.get("rows"), acc))
    tbl = _make_table_from_grid(grid_rows)
    if tbl is not None:
        acc.add_block(tbl, source_ref=source_ref, component_id=comp_id)


def _spec_row_to_cells(row: Any) -> list[dict[str, Any]] | None:
    if isinstance(row, Mapping):
        label = _strip_html(str(row.get("label") or ""))
        vals = [
            _strip_html(str(v.get("text") or "")) if isinstance(v, Mapping) else _strip_html(str(v))
            for v in (row.get("values") or ())
        ]
        return [{"text": label, "header": True}, *({"text": v} for v in vals)]
    if isinstance(row, Sequence) and not isinstance(row, (str, bytes)):
        return [{"text": _strip_html(str(c))} for c in row]
    return None


def _extract_spec_slots(
    slots: Mapping[str, Any],
    comp_id: str,
    acc: _SectionAccumulator,
    *,
    source_ref: str,
) -> None:
    title = _strip_html(_first_str(slots, "section_title", "title"))
    if title:
        acc.add_block({"type": "heading", "level": 3, "text": title, "anchor": ""}, source_ref=source_ref, component_id=comp_id)
    grid_rows: list[list[dict[str, Any]]] = []
    hdr = _header_row_cells(slots.get("headers"))
    if hdr:
        grid_rows.append(hdr)
    for row in slots.get("rows") or ():
        if cells := _spec_row_to_cells(row):
            grid_rows.append(cells)
    tbl = _make_table_from_grid(grid_rows)
    if tbl is not None:
        acc.add_block(tbl, source_ref=source_ref, component_id=comp_id)


def _lcd_icon_row_cells(row: Mapping[str, Any], acc: _SectionAccumulator) -> list[dict[str, Any]]:
    alt = _strip_html(str(row.get("icon_alt") or ""))
    if alt:
        acc.record_image_alts((alt,))
    c0: dict[str, Any] = {"text": _strip_html(str(row.get("number_text") or alt))}
    if alt:
        c0["image_alts"] = [alt]
    return [c0, {"text": _strip_html(str(row.get("name_text") or ""))}, {"text": _strip_html(str(row.get("description_text") or ""))}]


def _row_dict_to_cells(row: Mapping[str, Any], acc: _SectionAccumulator) -> list[dict[str, Any]]:
    if "code_text" in row or "measures_text" in row:
        return [{"text": _strip_html(str(row.get("code_text") or ""))}, {"text": _strip_html(str(row.get("measures_text") or ""))}]
    if "name_text" in row or "description_text" in row:
        return _lcd_icon_row_cells(row, acc)
    return [{"text": _strip_html(str(v))} for v in row.values() if isinstance(v, str) and v.strip()]


def _group_slot_rows(groups: Any) -> list[list[dict[str, Any]]]:
    out: list[list[dict[str, Any]]] = []
    if not isinstance(groups, Sequence):
        return out
    for group in groups:
        if not isinstance(group, Mapping):
            continue
        state = _strip_html(str(group.get("state_text") or ""))
        for act in group.get("actions") or ():
            if isinstance(act, Mapping):
                out.append([
                    {"text": state},
                    {"text": _strip_html(str(act.get("action_text") or ""))},
                    {"text": _strip_html(str(act.get("description_text") or ""))},
                ])
    return out


def _condition_slot_rows(conditions: Any) -> list[list[dict[str, Any]]]:
    out: list[list[dict[str, Any]]] = []
    if not isinstance(conditions, Sequence):
        return out
    for col in conditions:
        if isinstance(col, Sequence) and not isinstance(col, (str, bytes)):
            out.extend([{"text": _strip_html(str(cond))}] for cond in col)
    return out


def _extract_table_slots(
    slots: Mapping[str, Any],
    comp_id: str,
    acc: _SectionAccumulator,
    *,
    source_ref: str,
) -> None:
    grid_rows: list[list[dict[str, Any]]] = []
    hdr = _header_row_cells(slots.get("headers"))
    if hdr:
        grid_rows.append(hdr)
    grid_rows.extend(_condition_slot_rows(slots.get("conditions")))
    grid_rows.extend(_group_slot_rows(slots.get("groups")))
    for row in slots.get("rows") or ():
        if isinstance(row, Mapping):
            cells = _row_dict_to_cells(row, acc)
            if cells:
                grid_rows.append(cells)
        elif isinstance(row, Sequence) and not isinstance(row, (str, bytes)):
            grid_rows.append([
                {"text": _strip_html(_first_str(c, "text", "html")) if isinstance(c, Mapping) else _strip_html(str(c))}
                for c in row
            ])
    tbl = _make_table_from_grid(grid_rows)
    if tbl is not None:
        acc.add_block(tbl, source_ref=source_ref, component_id=comp_id)


def _warranty_period_text(period: Mapping[str, Any]) -> str:
    parts = [str(period.get(k) or "").strip() for k in ("label", "number", "unit", "body_text")]
    return _strip_html(" — ".join(p for p in parts if p))


def _extract_warranty_slots(
    slots: Mapping[str, Any],
    comp_id: str,
    acc: _SectionAccumulator,
    *,
    source_ref: str,
) -> None:
    if title := _strip_html(str(slots.get("title") or "")):
        acc.add_block({"type": "heading", "level": 3, "text": title, "anchor": ""}, source_ref=source_ref, component_id=comp_id)
    for key in ("lead", "local_note"):
        if val := _strip_html(str(slots.get(key) or "")):
            acc.add_block({"type": "paragraph", "text": val}, source_ref=source_ref, component_id=comp_id)
    for blk in slots.get("blocks") or ():
        if isinstance(blk, Mapping) and (txt := _strip_html(_first_str(blk, "text", "html"))):
            acc.add_block({"type": "paragraph", "text": txt}, source_ref=source_ref, component_id=comp_id)
    for period in slots.get("periods") or ():
        if isinstance(period, Mapping) and (txt := _warranty_period_text(period)):
            acc.add_block({"type": "paragraph", "text": txt}, source_ref=source_ref, component_id=comp_id)


def _extract_step_slots(steps: Any, comp_id: str, acc: _SectionAccumulator, *, source_ref: str) -> None:
    for step in steps or ():
        if not isinstance(step, Mapping):
            continue
        raw_parts = [_strip_html(_first_str(p, "text", "html")) for p in (step.get("parts") or ()) if isinstance(p, Mapping)]
        if line := " ".join(p for p in raw_parts if p):
            acc.add_block({"type": "paragraph", "text": line}, source_ref=source_ref, component_id=comp_id)


def _extract_view_slots(views: Any, comp_id: str, acc: _SectionAccumulator, *, source_ref: str) -> None:
    for view in views or ():
        if not isinstance(view, Mapping):
            continue
        if alt := _strip_html(str(view.get("alt") or "")):
            acc.add_image(alt, source_ref=source_ref, component_id=comp_id)
        for callout in view.get("callouts") or ():
            if not isinstance(callout, Mapping):
                continue
            body = [_strip_html(str(b)) for b in (callout.get("body") or ())]
            if txt := " ".join(p for p in [_strip_html(str(callout.get("label") or "")), *body] if p):
                acc.add_block({"type": "paragraph", "text": txt}, source_ref=source_ref, component_id=comp_id)


def _extract_operation_overview_slots(
    slots: Mapping[str, Any],
    comp_id: str,
    acc: _SectionAccumulator,
    *,
    source_ref: str,
) -> None:
    _extract_step_slots(slots.get("steps"), comp_id, acc, source_ref=source_ref)
    _extract_view_slots(slots.get("views"), comp_id, acc, source_ref=source_ref)


def _extract_generic_slots(
    slots: Mapping[str, Any],
    comp_id: str,
    acc: _SectionAccumulator,
    *,
    source_ref: str,
) -> None:
    if "panels" in slots or comp_id in {"HB-TABLE-SYMBOL-SIGNAL", "HB-TABLE-SYMBOL-ICON", "HB-SYMBOL-PAIR-TABLE"}:
        _extract_symbol_component(slots, comp_id, acc, source_ref=source_ref)
        return
    if comp_id in {"HB-TABLE-SPEC", "HB-SPEC-TABLE"}:
        _extract_spec_slots(slots, comp_id, acc, source_ref=source_ref)
        return
    if comp_id.startswith("HB-WARRANTY-"):
        _extract_warranty_slots(slots, comp_id, acc, source_ref=source_ref)
        return
    if any(k in slots for k in ("rows", "conditions", "groups")):
        _extract_table_slots(slots, comp_id, acc, source_ref=source_ref)
        return
    _extract_operation_overview_slots(slots, comp_id, acc, source_ref=source_ref)
    for key in ("supporting_copy", "items", "body_blocks", "opening_copy"):
        val = slots.get(key)
        if not isinstance(val, Sequence) or isinstance(val, (str, bytes)):
            continue
        for entry in val:
            raw = _first_str(entry, "text", "html") if isinstance(entry, Mapping) else str(entry)
            if txt := _strip_html(raw):
                acc.add_block({"type": "paragraph", "text": txt}, source_ref=source_ref, component_id=comp_id)


def _fallback_html_component(
    node: Mapping[str, Any],
    comp_id: str,
    acc: _SectionAccumulator,
    *,
    source_ref: str,
) -> None:
    carrier = node.get("carrier_flow")
    if not isinstance(carrier, Sequence) or not carrier:
        return
    try:
        rendered = flow_nodes_to_html(list(carrier))
    except ValueError:
        return
    soup = BeautifulSoup(rendered, "html.parser")
    for tbl in soup.find_all("table"):
        if tbl.find("table") is None and tbl.find("tr") is not None:
            acc.add_block(table_block(tbl), source_ref=source_ref, component_id=comp_id)
            tbl.decompose()
    for p in soup.find_all("p"):
        if txt := _normalize_whitespace(p.get_text(" ")):
            acc.add_block({"type": "paragraph", "text": txt}, source_ref=source_ref, component_id=comp_id)


def _extract_component(
    node: Mapping[str, Any],
    acc: _SectionAccumulator,
    *,
    page_heading_level: int,
    page_id: str,
    source_ref: str,
) -> None:
    acc.components_count += 1
    comp_spec = node.get("component_spec")
    if not isinstance(comp_spec, Mapping):
        return
    comp_id = str(comp_spec.get("component_id") or "").strip()
    comp_ref = str(comp_spec.get("source_ref") or source_ref)
    slots = _slot_map(comp_spec)
    if comp_id == "HB-CALLOUT-STRIP":
        _extract_callout_component(node, slots, comp_id, acc, source_ref=comp_ref)
        return
    carrier_flow = node.get("carrier_flow")
    if isinstance(carrier_flow, Sequence) and carrier_flow:
        before = len(acc.current["blocks"]) + len(acc.sections)
        for child in carrier_flow:
            if isinstance(child, Mapping):
                _walk_node(child, acc, page_heading_level=page_heading_level, page_id=page_id, source_ref=comp_ref, component_id=comp_id)
        if len(acc.current["blocks"]) + len(acc.sections) == before:
            _fallback_html_component(node, comp_id, acc, source_ref=comp_ref)
        return
    _extract_generic_slots(slots, comp_id, acc, source_ref=comp_ref)


def _callout_dict(label: str, body: str) -> dict[str, Any]:
    text = f"{label}: {body}" if label and body else (body or label)
    return {"type": "callout", "label": label, "body": body, "severity": ir_callout_severity(label), "text": text}


def _callout_from_group(children: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    if not children:
        return None
    label = _flow_text(children[0])
    body = _normalize_whitespace("\n".join(_flow_text(c) for c in children[1:]))
    return _callout_dict(label, body) if (label or body) else None


def _walk_group(
    node: Mapping[str, Any],
    acc: _SectionAccumulator,
    *,
    page_heading_level: int,
    page_id: str,
    source_ref: str,
    component_id: str | None,
) -> None:
    classes = set(_presentation_classes(node))
    children = [c for c in (node.get("children") or ()) if isinstance(c, Mapping)]
    if classes & {"admonition", "hb-inbox-tip"}:
        if callout := _callout_from_group(children):
            acc.add_block(callout, source_ref=source_ref, component_id=component_id)
            return
    if children and all(c.get("kind") in _INLINE_KINDS for c in children):
        if txt := _flow_text(node):
            acc.add_block({"type": "paragraph", "text": txt}, source_ref=source_ref, component_id=component_id)
        return
    for child in children:
        _walk_node(child, acc, page_heading_level=page_heading_level, page_id=page_id, source_ref=source_ref, component_id=component_id)


def _walk_heading(
    node: Mapping[str, Any],
    acc: _SectionAccumulator,
    *,
    page_heading_level: int,
    page_id: str,
    source_ref: str,
    component_id: str | None,
) -> None:
    acc.headings_count += 1
    level = _int_or(node.get("level"), 1)
    title = _flow_text(node)
    anchor = str(node.get("anchor") or "").strip()
    if level <= page_heading_level:
        acc.start_section(title or "Untitled", level, anchor, page_id)
    elif title:
        acc.add_block({"type": "heading", "level": level, "text": title, "anchor": anchor}, source_ref=source_ref, component_id=component_id)


def _walk_table_node(
    node: Mapping[str, Any],
    acc: _SectionAccumulator,
    *,
    source_ref: str,
    component_id: str | None,
) -> None:
    classes = set(_presentation_classes(node))
    if classes & {"manual-callout-table", "hb-inbox-tip"}:
        callout = _callout_from_table_flow(node)
        if callout is not None:
            acc.add_block(callout, source_ref=source_ref, component_id=component_id)
            return
    tbl = _table_from_flow(node, acc)
    if tbl is not None:
        acc.add_block(tbl, source_ref=source_ref, component_id=component_id)


def _walk_leaf_node(
    node: Mapping[str, Any],
    kind: str,
    acc: _SectionAccumulator,
    *,
    source_ref: str,
    component_id: str | None,
) -> bool:
    if kind in {"admonition", "callout"}:
        label = _strip_html(_first_str(node, "label", "title"))
        body = _strip_html(str(node.get("body") or "")) or _flow_text(node)
        acc.add_block(_callout_dict(label, body), source_ref=source_ref, component_id=component_id)
        return True
    if kind == "list":
        acc.add_block(_list_block_from_flow(node), source_ref=source_ref, component_id=component_id)
        for alt in _collect_images(node):
            acc.add_image(alt, source_ref=source_ref, component_id=component_id)
        return True
    if kind == "image":
        acc.add_image(str(node.get("alt") or ""), source_ref=source_ref, component_id=component_id)
        return True
    if kind in _PARA_KINDS:
        if text := _flow_text(node):
            acc.add_block({"type": "paragraph", "text": text}, source_ref=source_ref, component_id=component_id)
        for alt in _collect_images(node):
            acc.add_image(alt, source_ref=source_ref, component_id=component_id)
        return True
    if kind == "text":
        if text := _normalize_whitespace(str(node.get("text") or "")):
            acc.add_block({"type": "paragraph", "text": text}, source_ref=source_ref, component_id=component_id)
        return True
    return False


def _walk_node(
    node: Mapping[str, Any],
    acc: _SectionAccumulator,
    *,
    page_heading_level: int,
    page_id: str,
    source_ref: str,
    component_id: str | None = None,
) -> None:
    if _is_hidden(node):
        return
    kind = str(node.get("kind") or "")
    if kind == "heading":
        _walk_heading(node, acc, page_heading_level=page_heading_level, page_id=page_id, source_ref=source_ref, component_id=component_id)
    elif kind == "component":
        _extract_component(node, acc, page_heading_level=page_heading_level, page_id=page_id, source_ref=source_ref)
    elif kind == "table":
        _walk_table_node(node, acc, source_ref=source_ref, component_id=component_id)
    elif kind in _GROUP_KINDS:
        _walk_group(node, acc, page_heading_level=page_heading_level, page_id=page_id, source_ref=source_ref, component_id=component_id)
    elif not _walk_leaf_node(node, kind, acc, source_ref=source_ref, component_id=component_id):
        for child in node.get("children") or ():
            if isinstance(child, Mapping):
                _walk_node(child, acc, page_heading_level=page_heading_level, page_id=page_id, source_ref=source_ref, component_id=component_id)


def _block_flow_items(blk: Mapping[str, Any], page_ref: str) -> list[tuple[Mapping[str, Any], str]]:
    ref = str(blk.get("source_ref") or page_ref)
    payload = blk.get("payload")
    if isinstance(payload, Mapping):
        if "kind" in payload:
            return [(payload, ref)]
        nodes = payload.get("nodes")
        if isinstance(nodes, Sequence):
            return [(n, ref) for n in nodes if isinstance(n, Mapping)]
    elif isinstance(payload, Sequence) and not isinstance(payload, (str, bytes)):
        return [(n, ref) for n in payload if isinstance(n, Mapping)]
    if isinstance(blk.get("kind"), str) and blk["kind"] != "flow":
        return [(blk, ref)]
    return []


def _page_flow_items(page: Mapping[str, Any]) -> list[tuple[Mapping[str, Any], str]]:
    page_ref = str(page.get("source_ref") or page.get("page_id") or "")
    items: list[tuple[Mapping[str, Any], str]] = []
    blocks = page.get("blocks")
    if isinstance(blocks, Sequence):
        for blk in blocks:
            if isinstance(blk, Mapping):
                items.extend(_block_flow_items(blk, page_ref))
    flow = page.get("flow")
    if isinstance(flow, Sequence):
        for n in flow:
            if isinstance(n, Mapping):
                items.append((n, str(n.get("source_ref") or page_ref)))
    return items


def _min_heading_level(nodes: Sequence[Mapping[str, Any]]) -> int:
    levels: list[int] = []
    for n in nodes:
        if _is_hidden(n):
            continue
        if n.get("kind") == "heading":
            levels.append(_int_or(n.get("level"), 1))
        for child in n.get("children") or ():
            if isinstance(child, Mapping) and child.get("kind") == "heading" and not _is_hidden(child):
                levels.append(_int_or(child.get("level"), 1))
    return min(levels, default=1)


def extract_ir_sections(ir_payload: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Directly extract auto-manual-knowledge/v1 sections and coverage from manual-ir/v2."""
    doc_key = f"{ir_payload.get('model') or ''}:{ir_payload.get('region') or ''}:{ir_payload.get('language') or ''}"
    acc = _SectionAccumulator(doc_key=doc_key)
    for page in ir_payload.get("pages") or ():
        if not isinstance(page, Mapping):
            continue
        page_id = str(page.get("page_id") or "")
        flow_items = _page_flow_items(page)
        page_level = _min_heading_level([node for node, _ in flow_items])
        for node, ref in flow_items:
            _walk_node(node, acc, page_heading_level=page_level, page_id=page_id, source_ref=ref)
    acc.flush()
    return acc.sections, acc.coverage()


def _normalize_lang(raw_lang: str) -> str:
    cleaned = raw_lang.strip().replace("_", "-")
    canonical = lang_registry.canonical_language(cleaned)
    if canonical:
        return canonical
    primary = cleaned.split("-")[0]
    return lang_registry.canonical_language(primary) or cleaned


def _is_candidate_path(rel_path: str) -> bool:
    return any("candidate" in part.casefold() for part in Path(rel_path).parts)


@dataclass(frozen=True)
class _IRBundle:
    rel_path: str
    model: str
    region: str
    lang: str
    declared_lang: str
    publication_eligible: bool
    file_sha256: str
    content_sha256: str
    payload: dict[str, Any]

    @property
    def variant_key(self) -> str:
        return f"{self.model}/{self.region}/{self.lang}"

    @property
    def rank(self) -> tuple[int, int, str]:
        return (1 if self.publication_eligible else 0, 0 if _is_candidate_path(self.rel_path) else 1, self.rel_path)


def _display_rel(path: Path, root: Path) -> str:
    resolved = path.resolve()
    root_resolved = root.resolve()
    if resolved.is_relative_to(root_resolved):
        return resolved.relative_to(root_resolved).as_posix()
    return resolved.as_posix()


def _load_bundle(path: Path, *, root: Path) -> _IRBundle | None:
    try:
        raw_bytes = path.read_bytes()
        payload = json.loads(raw_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or payload.get("schema_version") != SUPPORTED_IR_SCHEMA_VERSION:
        return None
    model = str(payload.get("model") or "").strip()
    region = str(payload.get("region") or "").strip()
    declared_lang = str(payload.get("language") or "").strip()
    if not model or not region or not declared_lang or not isinstance(payload.get("pages"), list):
        return None
    raw_meta = payload.get("metadata")
    meta: Mapping[str, Any] = raw_meta if isinstance(raw_meta, Mapping) else {}
    file_sha = hashlib.sha256(raw_bytes).hexdigest()
    return _IRBundle(
        rel_path=_display_rel(path, root),
        model=model,
        region=region,
        lang=_normalize_lang(declared_lang),
        declared_lang=declared_lang,
        publication_eligible=bool(meta.get("publication_eligible") is True),
        file_sha256=file_sha,
        content_sha256=str(payload.get("content_sha256") or file_sha),
        payload=payload,
    )


def _collect_ir_paths(scan_roots: Sequence[Path]) -> list[Path]:
    paths: list[Path] = []
    for scan_root in scan_roots:
        if scan_root.is_file() and scan_root.name == "manual.ir.json":
            paths.append(scan_root)
        elif scan_root.is_dir():
            paths.extend(sorted(scan_root.rglob("manual.ir.json")))
    return sorted(paths)


def _scan_bundles(
    *,
    scan_roots: Sequence[Path],
    root: Path,
    region: str | None,
    model: str | None,
    publication_eligible_only: bool,
) -> list[_IRBundle]:
    bundles: list[_IRBundle] = []
    seen: set[Path] = set()
    for path in _collect_ir_paths(scan_roots):
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        bundle = _load_bundle(resolved, root=root)
        if bundle is None:
            continue
        if region and bundle.region.casefold() != region.strip().casefold():
            continue
        if model and bundle.model.casefold() != model.strip().casefold():
            continue
        if publication_eligible_only and not bundle.publication_eligible:
            continue
        bundles.append(bundle)
    return bundles


def _deduplicate_bundles(bundles: Sequence[_IRBundle]) -> tuple[list[_IRBundle], list[str]]:
    grouped: dict[str, list[_IRBundle]] = {}
    for bundle in bundles:
        grouped.setdefault(bundle.variant_key, []).append(bundle)
    selected: list[_IRBundle] = []
    skipped: list[str] = []
    for variant_key in sorted(grouped):
        candidates = sorted(grouped[variant_key], key=lambda b: b.rank, reverse=True)
        selected.append(candidates[0])
        skipped.extend(b.rel_path for b in candidates[1:])
    return selected, sorted(skipped)


def _build_document(bundle: _IRBundle, *, published_at: str) -> dict[str, Any]:
    raw_meta = bundle.payload.get("metadata")
    meta: Mapping[str, Any] = raw_meta if isinstance(raw_meta, Mapping) else {}
    name = str(meta.get("product_name") or "").strip() or bundle.model
    version = str(meta.get("revision") or meta.get("version") or "ir-v2").strip() or "ir-v2"
    sections, coverage = extract_ir_sections(bundle.payload)
    return {
        "id": f"ir:{bundle.model}:{bundle.region}:{bundle.lang}",
        "model": bundle.model,
        "region": bundle.region,
        "name": name,
        "url": bundle.rel_path,
        "lang": bundle.lang,
        "declared_lang": bundle.declared_lang,
        "language_scope": "single",
        "version": version,
        "html_sha256": bundle.file_sha256,
        "ir_sha256": bundle.file_sha256,
        "ir_content_sha256": bundle.content_sha256,
        "sections": sections,
        "coverage": coverage,
        **variant_identity(model=bundle.model, region=bundle.region, lang=bundle.lang, version=version),
        "machine_surface": dict(IR_MACHINE_SURFACE),
        "source": {
            "route": Path(bundle.rel_path).parent.as_posix(),
            "html_sha256": bundle.file_sha256,
            "ir_sha256": bundle.file_sha256,
            "ir_content_sha256": bundle.content_sha256,
            "release_path": "manual_ir_v2",
            "authority": "approved" if bundle.publication_eligible else "working_tree",
            "published_at": published_at,
        },
    }


def make_ir_corpus(
    *,
    roots: Sequence[Path] = (),
    region: str | None = None,
    model: str | None = None,
    publication_eligible_only: bool = False,
    published_at: str = "ir-v2",
    source_sha256: str = "",
    repo_root_path: Path | None = None,
) -> dict[str, Any]:
    """Build an all-region auto-manual-knowledge/v1 corpus directly from manual-ir/v2 bundles."""
    root = (repo_root_path or repo_root()).resolve()
    scan_roots = tuple(roots) if roots else default_scan_roots(root)
    bundles = _scan_bundles(
        scan_roots=scan_roots,
        root=root,
        region=region,
        model=model,
        publication_eligible_only=publication_eligible_only,
    )
    chosen, skipped_duplicates = _deduplicate_bundles(bundles)
    documents = [_build_document(bundle, published_at=published_at) for bundle in chosen]
    resolved_sha = source_sha256 or hashlib.sha256(
        "\n".join(f"{d['url']}:{d['ir_sha256']}" for d in documents).encode("utf-8")
    ).hexdigest()
    corpus_region = region.strip().upper() if region and region.strip() else "ALL"
    return {
        "schema": CORPUS_SCHEMA,
        "source_sha256": resolved_sha,
        "published_at": published_at,
        "region": corpus_region,
        "regions": sorted({d["region"] for d in documents}),
        "documents": documents,
        "skipped_duplicates": skipped_duplicates,
        "counts": {
            "models": len({d["model"] for d in documents}),
            "editions": len(documents),
            "sections": sum(len(d["sections"]) for d in documents),
        },
    }


def _text_label(cell: Mapping[str, Any]) -> str | None:
    alts = " / ".join(str(alt) for alt in (cell.get("image_alts") or ()) if alt)
    text = str(cell.get("text") or "").strip()
    return text if text and not (alts and text == alts) else None


def is_ir_legend(table: Mapping[str, Any]) -> bool:
    """Return True for signal-word legend tables in EU, US, or CJK/KR languages."""
    severities: set[str] = set()
    for row in table.get("rows") or ():
        if not row:
            continue
        label = _text_label(row[0])
        if not label:
            continue
        sev = ir_callout_severity(re.sub(r"^\W+", "", label))
        if sev != "unknown":
            severities.add(sev)
    return len(severities) >= 2


def _signal_from_text(text: str) -> str | None:
    sev = ir_callout_severity(re.sub(r"^\W+", "", text))
    return None if sev == "unknown" else sev


def _signal_prefix(text: str) -> re.Match[str] | None:
    match = _SIGNAL_PREFIX.match(text)
    if match is None and (bare := _BARE_SIGNAL.match(text)) and bare.group(1).isupper():
        return bare
    return match


def _ir_plain_carriers(text: str, kind: str | None, index: int | None) -> Iterator[Carrier]:
    if ir_legislation(text):
        yield Carrier("compliance", None, text, index, "extract.compliance_legislation")
    elif kind == "compliance":
        yield Carrier("compliance", None, text, index, "extract.compliance_section")
    elif kind == "safety":
        yield Carrier("safety", None, text, index, "extract.safety_section")


def _ir_symbol_row(row: Sequence[Mapping[str, Any]], rest: str, index: int) -> Iterator[Carrier]:
    if not row[0].get("image_alts"):
        joined = "\n".join(str(c.get("text") or "") for c in row if str(c.get("text") or "").strip())
        yield Carrier("safety", None, joined, index, "extract.symbol_row")
        return
    name = str(row[0].get("text") or "").strip()
    icon = name if name and name != rest.strip() else None
    if (icon and re.sub(r"[\s-]+", "_", icon.casefold()) in MARKING_ICONS) or HOUSEHOLD_WASTE.search(rest):
        yield Carrier("compliance", icon, rest, index, "extract.marking_symbol")
    elif ir_legislation(rest):
        yield Carrier("compliance", icon, rest, index, "extract.compliance_legislation")
    else:
        yield Carrier("safety", icon, rest, index, "extract.symbol_row")


def _ir_paragraph_carriers(block: Mapping[str, Any], kind: str | None) -> Iterator[Carrier]:
    text = str(block.get("text") or "")
    match = _signal_prefix(text)
    if ir_legislation(text):
        yield from _ir_plain_carriers(text, kind, None)
    elif match and (sev := _signal_from_text(match.group(1))) and text[match.end():].strip():
        yield Carrier("warning", match.group(1), text[match.end():].strip(), None, "extract.signal_paragraph", sev)
    else:
        yield from _ir_plain_carriers(text, kind, None)


def _join_cells(cells: Sequence[Mapping[str, Any]]) -> str:
    return "\n".join(str(c.get("text") or "") for c in cells if str(c.get("text") or "").strip())


def _ir_table_row_carriers(row: Sequence[Mapping[str, Any]], kind: str | None, idx: int) -> Iterator[Carrier]:
    if not row or all(cell.get("header") for cell in row):
        return
    label = _text_label(row[0])
    rest = _join_cells(row[1:])
    if label and rest and not ir_legislation(rest):
        if sev := _signal_from_text(label):
            yield Carrier("warning", label, rest, idx, "extract.signal_row", sev)
            return
    if kind == "symbols" and rest:
        yield from _ir_symbol_row(row, rest, idx)
        return
    yield from _ir_plain_carriers(_join_cells(row), kind, idx)


def _ir_table_carriers(block: Mapping[str, Any], kind: str | None) -> Iterator[Carrier]:
    if is_ir_legend(block):
        return
    for idx, row in enumerate(block.get("rows") or ()):
        yield from _ir_table_row_carriers(row, kind, idx)


def _ir_block_carriers(block: Mapping[str, Any], kind: str | None) -> Iterator[Carrier]:
    btype = block.get("type")
    if btype == "callout":
        label = str(block.get("label") or "")
        yield Carrier("warning", label, str(block.get("body") or ""), None, "extract.callout", ir_callout_severity(label))
    elif btype == "paragraph":
        yield from _ir_paragraph_carriers(block, kind)
    elif btype == "list":
        for idx, item in enumerate(block.get("items") or ()):
            text = "\n".join([str(item.get("text") or "")] + [str(ch.get("text") or "") for ch in (item.get("children") or ())])
            yield from _ir_plain_carriers(text, kind, idx)
    elif btype == "table":
        yield from _ir_table_carriers(block, kind)


def _observed_context(document: Mapping[str, Any], features: Mapping[str, Mapping[str, bool]]) -> dict[str, Any]:
    source = document.get("source") or {}
    feature = features.get(f"{document['model']}_{document['region']}")
    return {
        "model": document["model"],
        "region": document["region"],
        "language": document["language"],
        "language_status": document["language_status"],
        "revision": document["revision"],
        "revision_kind": document["revision_kind"],
        "release_path": source.get("release_path"),
        "authority": source.get("authority"),
        "feature": dict(feature) if feature is not None else "unknown",
    }


def _enrich_item_topics(item: dict[str, Any], combined: str) -> None:
    existing_topics = list(item.get("topic") or [])
    extra_topics = [t for t in ir_cjk_topics(combined) if t not in existing_topics]
    if not extra_topics:
        return
    item["topic"] = existing_topics + extra_topics
    method = item.setdefault("method", {})
    rules = list(method.get("rules") or [])
    for t in extra_topics:
        rule = f"topic.{t}"
        if rule not in rules:
            rules.append(rule)
    method["rules"] = rules


def _enrich_item(item: dict[str, Any]) -> dict[str, Any]:
    combined = f"{item.get('label') or ''}\n{item.get('text') or ''}"
    _enrich_item_topics(item, combined)
    flags = [f for f in (item.get("review_flags") or []) if not (f == "topic_unknown" and item["topic"])]
    if item.get("category") == "warning" and item.get("severity") == "unknown" and item.get("label"):
        resolved = ir_callout_severity(str(item["label"]))
        if resolved != "unknown":
            item["severity"] = resolved
            flags = [f for f in flags if f != "severity_unknown"]
    item["review_flags"] = sorted(flags)
    if item.get("category") == "compliance":
        item["legislation"] = ir_legislation(str(item.get("text") or ""))
    return item


def _make_item(
    document: Mapping[str, Any],
    section: Mapping[str, Any],
    block: Mapping[str, Any],
    carrier: Carrier,
    context: Mapping[str, Any],
) -> dict[str, Any]:
    flags = ["topic_unknown"]
    if carrier.category == "warning" and carrier.severity == "unknown":
        flags.append("severity_unknown")
    if document["language"] == "multi":
        flags.append("language_multi")
    item: dict[str, Any] = {
        "category": carrier.category,
        "topic": [],
        "severity": carrier.severity,
        "label": carrier.label,
        "text": carrier.text,
        "content_sha256": content_sha256(carrier.label or "", carrier.text),
        "variant_key": document["variant_key"],
        "manual_variant_id": document["manual_variant_id"],
        "observed_context": dict(context),
        "source": {
            "section_id": section["id"],
            "section_title": section["title"],
            "block_id": block["block_id"],
            "block_type": block["type"],
            "item_index": carrier.item_index,
            "source_ref": block["source_ref"],
            "html_sha256": document["html_sha256"],
        },
        "status": "extracted",
        "review_flags": sorted(flags),
        "method": {"generator": OBS_GENERATOR_VERSION, "rules": [carrier.rule]},
    }
    if carrier.category == "compliance":
        item["applicability"] = "unknown"
        item["legislation"] = ir_legislation(carrier.text)
    return _enrich_item(item)


def _index_base_items(
    corpus: Mapping[str, Any],
    base_items: Sequence[dict[str, Any]],
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    legend_block_ids: set[tuple[str, str]] = {
        (doc["variant_key"], blk["block_id"])
        for doc in corpus.get("documents") or ()
        for sec in doc.get("sections") or ()
        for blk in sec.get("blocks") or ()
        if blk.get("type") == "table" and is_ir_legend(blk)
    }
    by_block: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in base_items:
        block_key = (item["variant_key"], item["source"]["block_id"])
        if block_key not in legend_block_ids:
            by_block[block_key].append(_enrich_item(item))
    return by_block


def _merge_document_items(
    doc: Mapping[str, Any],
    by_block: Mapping[tuple[str, str], list[dict[str, Any]]],
    features: Mapping[str, Mapping[str, bool]],
) -> list[dict[str, Any]]:
    context = _observed_context(doc, features)
    merged: list[dict[str, Any]] = []
    seen_slots: set[tuple[str, str, int | None]] = set()
    for sec in doc.get("sections") or ():
        sec_kind = ir_section_kind(str(sec.get("title") or ""))
        for blk in sec.get("blocks") or ():
            for existing in by_block.get((doc["variant_key"], blk["block_id"]), ()):
                slot = (doc["variant_key"], blk["block_id"], existing["source"]["item_index"])
                if slot not in seen_slots:
                    seen_slots.add(slot)
                    merged.append(existing)
            for carrier in _ir_block_carriers(blk, sec_kind):
                slot = (doc["variant_key"], blk["block_id"], carrier.item_index)
                if slot not in seen_slots:
                    seen_slots.add(slot)
                    merged.append(_make_item(doc, sec, blk, carrier, context))
    return merged


def build_ir_observations(
    corpus: dict[str, Any],
    corpus_bytes: bytes | None = None,
    features: dict[str, dict[str, bool]] | None = None,
    *,
    repo_root_path: Path | None = None,
) -> dict[str, Any]:
    """Build auto-manual-knowledge-observations/v1 with CJK/KR/US regulatory and topic enrichment."""
    raw_bytes = corpus_bytes if corpus_bytes is not None else json.dumps(corpus, ensure_ascii=False, sort_keys=True).encode("utf-8")
    root = (repo_root_path or repo_root()).resolve()
    feat = features if features is not None else load_capabilities(root / PathSegments.DATA)
    base = build_observations(corpus, raw_bytes, feat)
    by_block = _index_base_items(corpus, base["items"])
    merged: list[dict[str, Any]] = []
    for doc in corpus.get("documents") or ():
        merged.extend(_merge_document_items(doc, by_block, feat))

    counts: Counter[tuple[str, str, str]] = Counter()
    for item in merged:
        key = (item["variant_key"], item["category"], item["content_sha256"])
        item["knowledge_id"] = f"kn:{key[0]}:{key[1]}:{key[2][:16]}:{counts[key]}"
        counts[key] += 1

    relations = build_relations(corpus, merged, OBS_GENERATOR_VERSION)
    return {
        "schema": OBS_SCHEMA,
        "generator_version": OBS_GENERATOR_VERSION,
        "region": corpus["region"],
        "source_sha256": corpus["source_sha256"],
        "published_at": corpus["published_at"],
        "corpus_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "feature_source": FEATURE_SOURCE,
        "items": merged,
        "relations": relations,
        "summary": summarize(corpus, merged, relations),
    }


def _write_json_atomic(destination: Path, payload: Mapping[str, Any]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_suffix(".json.tmp")
    tmp.write_bytes((json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=1) + "\n").encode("utf-8"))
    tmp.replace(destination)


def export_ir_knowledge(
    *,
    roots: Sequence[Path] = (),
    region: str | None = None,
    model: str | None = None,
    publication_eligible_only: bool = False,
    output_corpus: Path | None = None,
    output_observations: Path | None = None,
    previous_observations: Path | None = None,
    repo_root_path: Path | None = None,
) -> dict[str, Any]:
    """Run all-region ManualIR v2 corpus + observations export and return summary metadata."""
    root = (repo_root_path or repo_root()).resolve()
    corpus = make_ir_corpus(
        roots=roots,
        region=region,
        model=model,
        publication_eligible_only=publication_eligible_only,
        repo_root_path=root,
    )
    corpus_bytes = (json.dumps(corpus, ensure_ascii=False, sort_keys=True, indent=1) + "\n").encode("utf-8")
    observations = build_ir_observations(corpus, corpus_bytes=corpus_bytes, repo_root_path=root)

    if output_corpus is not None:
        _write_json_atomic(output_corpus, corpus)
    if output_observations is not None:
        _write_json_atomic(output_observations, observations)

    obs_summary = {k: v for k, v in observations["summary"].items() if k != "items_by_variant"}
    summary: dict[str, Any] = {
        "status": "ok",
        "region": corpus["region"],
        "regions": corpus["regions"],
        "counts": corpus["counts"],
        "skipped_duplicates_count": len(corpus["skipped_duplicates"]),
        "observation_summary": obs_summary,
    }
    if output_corpus is not None:
        summary["corpus_path"] = str(output_corpus)
    if output_observations is not None:
        summary["observations_path"] = str(output_observations)
    if previous_observations is not None:
        previous = json.loads(previous_observations.read_text(encoding="utf-8"))
        summary["previous"] = judge_previous(previous, observations["items"], corpus)
    return summary


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for all-region ManualIR v2 knowledge export and observation."""
    parser = argparse.ArgumentParser(description="Export all-region ManualIR v2 knowledge corpus and observations")
    parser.add_argument("--root", action="append", type=Path, dest="roots", default=[], help="IR scan root (repeatable)")
    parser.add_argument("--region", default=None, help="Filter by region (e.g. US, EU, JP, KR, CN)")
    parser.add_argument("--model", default=None, help="Filter by model")
    parser.add_argument("--publication-eligible-only", action="store_true", help="Include only publication_eligible bundles")
    parser.add_argument("--output-corpus", type=Path, default=None, help="Write manual-knowledge.json corpus to path")
    parser.add_argument("--output-observations", type=Path, default=None, help="Write manual-observations.json to path")
    parser.add_argument("--previous-observations", type=Path, default=None, help="Earlier observation artifact to judge")
    args = parser.parse_args(argv)

    summary = export_ir_knowledge(
        roots=args.roots,
        region=args.region,
        model=args.model,
        publication_eligible_only=args.publication_eligible_only,
        output_corpus=args.output_corpus,
        output_observations=args.output_observations,
        previous_observations=args.previous_observations,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
