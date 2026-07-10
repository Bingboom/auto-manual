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
    return out
