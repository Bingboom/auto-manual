"""Shared interpretation of spec footnote references for CSV and IDML readers.

Row selection, localized copy and output escaping remain caller policies.
"""
from __future__ import annotations


_CIRCLED_NUMBER_MARKERS = {
    1: "①", 2: "②", 3: "③", 4: "④", 5: "⑤",
    6: "⑥", 7: "⑦", 8: "⑧", 9: "⑨", 10: "⑩",
}


def footnote_marker_for_order(order: float) -> str:
    normalized = int(order)
    if normalized <= 0:
        return ""
    return _CIRCLED_NUMBER_MARKERS.get(normalized, f"({normalized})")


def parse_footnote_refs(value: str) -> list[str]:
    refs: list[str] = []
    for token in (value or "").split(","):
        item = token.strip()
        if item and item not in refs:
            refs.append(item)
    return refs


def append_footnote_markers(text: str, refs: list[str], marker_by_id: dict[str, str]) -> str:
    if not text:
        return text
    markers = "".join(marker_by_id.get(ref, "") for ref in refs if marker_by_id.get(ref, ""))
    if not markers:
        return text
    return f"{text}{markers}"


