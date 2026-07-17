"""Detect the template's operation panels in extracted prose blocks.

The V2.0 master renders every operation (power / AC / DC-USB / energy
saving / LED / UPS / charging) as a panel: illustration left, bold
On/Off rows right, an optional "Prerequisite" pill on top. The RST
source carries the same content as ``[prereq body?] [image] [on/off
body]``; this pass rewrites that run into an ``oppanel`` component spec
so the renderer can build the panel instead of a bare image plus loose
text lines.
"""
from __future__ import annotations

import ast
import json
import re

Block = tuple[str, str]

_LABELS = {
    "on", "off", "on/off", "marche", "arrêt", "arret", "marche/arrêt",
    "encender", "apagar", "オン", "オフ", "开", "关", "开启", "关闭",
}
_PREREQ = re.compile(
    r"^\*{0,2}(prerequisite|prérequis|prerequis|requisito previo|前提)\*{0,2}\s*[::]",
    re.I,
)
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
# De-templated preface language tags: the shared template uses
# \HBLangTagLine{FR}{IMPORTANT}; flattened review pages carry
# "**FR IMPORTANT**" (first block may omit the language prefix).
_FLAT_LANGTAG = re.compile(r"^\*\*(?:([A-Z]{2})\s+)?(IMPORTANT\w*)\*\*$")
# Warranty-period cells: "**3 YEARS** **Standard Warranty** <copy>".
_WARRANTY_SPLIT_CELL = re.compile(
    r"^\*\*(\d+)\s+(YEARS?|ANS|AÑOS)\*\*\s*\*\*([^*]+)\*\*\s*(.*)$", re.S)
_WARRANTY_COMBINED_CELL = re.compile(
    r"^\*\*(\d+)\s+(YEARS?|ANS|AÑOS)\s+([^*]+)\*\*\s*(.*)$", re.S)


def _label_of(line: str) -> tuple[str, str] | None:
    """Return (label, trailing instruction) when the line starts a row."""
    plain = _BOLD.sub(r"\1", line).strip()
    head, sep, tail = plain.partition(":")
    candidate = (head if sep else plain).strip().lower()
    if candidate in _LABELS:
        return (head if sep else plain).strip(), tail.strip()
    return None


def _parse_rows_and_tail(
    text: str,
) -> tuple[list[tuple[str, str]] | None, str]:
    """Parse operation rows and preserve a structurally marked prose tail.

    Localized RST line blocks are not guaranteed to keep the operation rows
    and the following standby copy as separate IR paragraphs.  Once two
    complete On/Off rows have been found, a new bold field starts ordinary
    full-width prose rather than extending the second row's narrow text
    column.  Continuation lines inside the two operation rows still work as
    before.
    """
    rows: list[tuple[str, str]] = []
    tail: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if tail:
            tail.append(line)
            continue
        started = _label_of(line)
        if started:
            rows.append(started)
        elif rows and not rows[-1][1]:
            rows[-1] = (rows[-1][0], line)
        elif len(rows) >= 2 and re.match(r"^\*\*[^*]+\*\*", line):
            tail.append(line)
        elif rows:
            rows[-1] = (rows[-1][0], rows[-1][1] + " " + line)
        else:
            return None, ""
    if len(rows) < 2:
        return None, ""
    return rows, "\n".join(tail)


def parse_rows(text: str) -> list[tuple[str, str]] | None:
    """Parse an On/Off body into [(label, instruction), ...] or None."""
    rows, _tail = _parse_rows_and_tail(text)
    return rows


def _parse_warranty_cell(text: str) -> dict[str, str] | None:
    match = _WARRANTY_SPLIT_CELL.match(text.strip())
    if match is None:
        match = _WARRANTY_COMBINED_CELL.match(text.strip())
    if match is None:
        return None
    return {
        "number": match.group(1),
        "unit": match.group(2),
        "label": match.group(3).strip(),
        "text": match.group(4).strip(),
    }


def transform(blocks: list[Block]) -> list[Block]:
    out: list[Block] = []
    i = 0
    while i < len(blocks):
        kind, text = blocks[i]
        if kind == "table":
            try:
                rows = text if isinstance(text, list) else ast.literal_eval(text)
            except (ValueError, SyntaxError):
                rows = None
            if rows and len(rows) == 1 and len(rows[0]) >= 2:
                items = [_parse_warranty_cell(cell) for cell in rows[0]]
                if all(item is not None for item in items):
                    out.append(("component", json.dumps(
                        {"kind": "warrantyyears", "items": items},
                        ensure_ascii=False)))
                    i += 1
                    continue
        if kind == "body":
            tag = _FLAT_LANGTAG.match(text.strip())
            if tag:
                out.append(("component", json.dumps(
                    {"kind": "langtag", "lang": tag.group(1) or "EN",
                     "texts": [tag.group(2)]}, ensure_ascii=False)))
                i += 1
                continue
        if kind == "image" and i + 1 < len(blocks) and blocks[i + 1][0] == "body":
            rows, tail = _parse_rows_and_tail(blocks[i + 1][1])
            if rows:
                prereq = ""
                if out and out[-1][0] == "body" and _PREREQ.match(out[-1][1].strip()):
                    prereq = _BOLD.sub(r"\1", out.pop()[1]).strip()
                out.append(("component", json.dumps(
                    {"kind": "oppanel", "image": text, "prereq": prereq,
                     "rows": rows}, ensure_ascii=False)))
                if tail:
                    out.append(("body", tail))
                i += 2
                continue
        out.append((kind, text))
        i += 1
    return _group_warranty_page(_group_charging_emphasis(out))


def _group_charging_emphasis(blocks: list[Block]) -> list[Block]:
    """Preserve the source's standalone pre-charge emphasis semantically.

    The sentence is localized, so the carrier is detected by structure: a
    fully-strong paragraph after introductory body copy and immediately
    before a notice.  No rendered wording or language title is matched here.
    """
    grouped: list[Block] = []
    for index, (kind, text) in enumerate(blocks):
        next_kind = blocks[index + 1][0] if index + 1 < len(blocks) else ""
        previous_kind = blocks[index - 1][0] if index > 0 else ""
        full_strong = re.fullmatch(r"\*\*[^*]+\*\*", text.strip()) is not None
        if (
            kind == "body"
            and previous_kind == "body"
            and full_strong
            and next_kind == "component"
        ):
            try:
                next_spec = json.loads(blocks[index + 1][1])
            except (TypeError, json.JSONDecodeError):
                next_spec = {}
            if next_spec.get("kind") == "notice":
                grouped.append(("component", json.dumps({
                    "kind": "emphasispill",
                    "texts": [text.strip()[2:-2]],
                }, ensure_ascii=False)))
                continue
        grouped.append((kind, text))
    return grouped


def _group_warranty_page(blocks: list[Block]) -> list[Block]:
    """Turn structurally identified warranty prose into editable components."""
    has_h1 = any(kind == "h1" for kind, _text in blocks)
    has_sections = any(kind == "h2" for kind, _text in blocks)
    has_period_component = False
    for kind, payload in blocks:
        if kind != "component":
            continue
        try:
            spec = json.loads(payload)
        except (TypeError, json.JSONDecodeError):
            continue
        if isinstance(spec, dict) and spec.get("kind") == "warrantyyears":
            has_period_component = True
            break
    if not (has_h1 and has_sections and has_period_component):
        return blocks

    grouped: list[Block] = []
    index = 0
    lead_seen = False
    i = 0
    while i < len(blocks):
        kind, text = blocks[i]
        if kind == "h1":
            grouped.append((kind, text))
            i += 1
            continue
        if kind == "body" and not lead_seen and text.strip().startswith("**"):
            grouped.append(("component", json.dumps({
                "kind": "warrantylead",
                "texts": [text],
            }, ensure_ascii=False)))
            lead_seen = True
            i += 1
            continue
        if kind == "h2":
            index += 1
            section_blocks: list[dict] = []
            i += 1
            while i < len(blocks) and blocks[i][0] not in {"h1", "h2"}:
                child_kind, child_text = blocks[i]
                if child_kind == "component":
                    spec = json.loads(child_text)
                    section_blocks.append({"kind": "component", "spec": spec})
                else:
                    section_blocks.append({"kind": child_kind, "text": child_text})
                i += 1
            grouped.append(("component", json.dumps({
                "kind": "warrantysection",
                "title": text,
                "index": index,
                "blocks": section_blocks,
            }, ensure_ascii=False)))
            continue
        grouped.append(("warrantynote" if lead_seen else kind, text))
        i += 1
    return grouped
