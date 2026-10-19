"""Preserve HTML table coordinates and spans for grounded manual queries."""
from __future__ import annotations

import re

from bs4 import Comment, NavigableString, Tag

_BREAKS = {"p", "div", "li", "dt", "dd", "figcaption", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}


def list_entries(node: Tag):
    """Resolve authored numbering once for standalone and embedded lists."""
    items = node.find_all("li", recursive=False)
    reversed_order = node.has_attr("reversed")
    raw = str(node.get("start", len(items) if reversed_order else 1))
    if not re.fullmatch(r"-?\d+", raw):
        raise ValueError("Invalid authored list start")
    number = int(raw)
    for item in items:
        raw = str(item.get("value", number))
        if not re.fullmatch(r"-?\d+", raw):
            raise ValueError("Invalid authored list item number")
        number = int(raw)
        yield number, item
        number += -1 if reversed_order else 1


def _text_parts(node):
    if isinstance(node, Comment):
        return
    if isinstance(node, NavigableString):
        yield re.sub(r"\s+", " ", str(node))
        return
    if node.name == "br":
        yield "\n"
        return
    if node.name in {"ol", "ul"}:
        for number, item in list_entries(node):
            body = "".join(part for child in item.children for part in _text_parts(child)).strip()
            yield "\n" + (f"{number}. " if node.name == "ol" else "• ") + body
        yield "\n"
        return
    if node.name in _BREAKS:
        yield "\n"
    for child in node.children:
        yield from _text_parts(child)
    if node.name in _BREAKS:
        yield "\n"


def content_text(node: Tag) -> str:
    """Keep line/paragraph boundaries; inline styling never enters the payload."""
    raw = "".join(_text_parts(node))
    return "\n".join(re.sub(r"[ \t]+", " ", line).strip() for line in raw.splitlines() if line.strip())


def _span(cell: Tag, name: str) -> int:
    raw = str(cell.get(name, "1"))
    if not raw.isdecimal() or not 1 <= int(raw) <= 64:
        raise ValueError(f"Unsupported table {name}: {raw}")
    return int(raw)


def _cell(cell: Tag, column: int) -> dict:
    text = content_text(cell)
    alts = [str(image.get("alt") or "").strip() for image in cell.find_all("img")]
    # Icon-only cells still have their source-authored name; never infer OCR.
    if not text:
        text = " / ".join(alt for alt in alts if alt)
    result = {"text": text, "column": column, "header": cell.name == "th",
              "rowspan": _span(cell, "rowspan"), "colspan": _span(cell, "colspan")}
    if alts:
        result.update(image_alts=alts, image_text_coverage="alt_only_no_ocr")
    return result


def table_block(table: Tag) -> dict:
    """Expose raw cells and an expanded grid, so a merged label stays attached."""
    if table.find("table") is not None:
        raise ValueError("Nested knowledge tables require an explicit semantic adapter")
    rows = []
    occupied: dict[tuple[int, int], str] = {}
    tags = [row for row in table.find_all("tr") if row.find_parent("table") is table]
    if not tags or len(tags) > 1000:
        raise ValueError("Knowledge table requires 1–1000 rows")
    for row_number, row in enumerate(tags):
        cells = []
        column = 0
        for tag in row.find_all(["td", "th"], recursive=False):
            while (row_number, column) in occupied:
                column += 1
            cell = _cell(tag, column)
            if column + cell["colspan"] > 64 or row_number + cell["rowspan"] > len(tags):
                raise ValueError("Table span exceeds its row/column boundary")
            for r in range(row_number, row_number + cell["rowspan"]):
                for c in range(column, column + cell["colspan"]):
                    if (r, c) in occupied:
                        raise ValueError("Overlapping table spans")
                    occupied[r, c] = cell["text"]
            cells.append(cell)
            column += cell["colspan"]
        rows.append(cells)
    width = max((c + 1 for _, c in occupied), default=0)
    grid = [[occupied.get((r, c), "") for c in range(width)] for r in range(len(rows))]
    text = "\n".join(" | ".join(value.replace("\n", "; ") for value in row) for row in grid)
    return {"type": "table", "rows": rows, "grid": grid, "text": text}
