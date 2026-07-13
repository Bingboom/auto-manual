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
_WARRANTY_CELL = re.compile(
    r"^\*\*(\d+)\s+(YEARS?|ANS|AÑOS)\*\*\s*\*\*([^*]+)\*\*\s*(.*)$", re.S)


def _label_of(line: str) -> tuple[str, str] | None:
    """Return (label, trailing instruction) when the line starts a row."""
    plain = _BOLD.sub(r"\1", line).strip()
    head, sep, tail = plain.partition(":")
    candidate = (head if sep else plain).strip().lower()
    if candidate in _LABELS:
        return (head if sep else plain).strip(), tail.strip()
    return None


def parse_rows(text: str) -> list[tuple[str, str]] | None:
    """Parse an On/Off body into [(label, instruction), ...] or None."""
    rows: list[tuple[str, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        started = _label_of(line)
        if started:
            rows.append(started)
        elif rows and not rows[-1][1]:
            rows[-1] = (rows[-1][0], line)
        elif rows:
            rows[-1] = (rows[-1][0], rows[-1][1] + " " + line)
        else:
            return None
    return rows if len(rows) >= 2 else None


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
                matches = [_WARRANTY_CELL.match(c.strip()) for c in rows[0]]
                if all(matches):
                    items = [{"number": m.group(1), "unit": m.group(2),
                              "label": m.group(3).strip(),
                              "text": m.group(4).strip()} for m in matches]
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
            rows = parse_rows(blocks[i + 1][1])
            if rows:
                prereq = ""
                if out and out[-1][0] == "body" and _PREREQ.match(out[-1][1].strip()):
                    prereq = _BOLD.sub(r"\1", out.pop()[1]).strip()
                out.append(("component", json.dumps(
                    {"kind": "oppanel", "image": text, "prereq": prereq,
                     "rows": rows}, ensure_ascii=False)))
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
    """Turn the English warranty prose into editable visual components."""
    if not any(kind == "h1" and text.strip().casefold() == "warranty"
               for kind, text in blocks):
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
