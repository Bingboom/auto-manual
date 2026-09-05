"""RST table parsing helpers for the IDML prepared-bundle extractor."""
from __future__ import annotations

import re
import unicodedata

_SEP_SEGMENT_RE = re.compile(r"^[=+-]+$")


def _is_table_rule(line: str) -> bool:
    return bool(re.fullmatch(r"\+[=+-]+\+", line.strip()))


def _clean_grid_segment(segment: str) -> tuple[str, bool]:
    text = segment.strip()
    is_rule = bool(_SEP_SEGMENT_RE.fullmatch(text))
    return ("" if is_rule else text, is_rule)


def parse_grid_table(grid: list[str]) -> list[list[str]]:
    """Parse an rst grid table block into row cell-text lists.

    The prepared bundle occasionally uses partial horizontal rules inside a
    grid row to express a row span. IDML's simple table renderer has no row-span
    support, so split that into an extra row and drop the rule glyphs instead
    of treating them as body copy.
    """
    border = grid[0]
    cols = [m.start() for m in re.finditer(r"\+", border)]
    if len(cols) < 2:
        return []
    rows: list[list[str]] = []
    current: list[list[str]] | None = None
    for line in grid:
        # RST borders measure display columns: Japanese glyphs occupy two.
        # A padding slot after a wide glyph lets existing border offsets slice
        # cells without consuming the next column.
        line = "".join(ch + ("\0" if unicodedata.east_asian_width(ch) in "WF" else "")
                       for ch in line)
        stripped = line.strip()
        if _is_table_rule(stripped):
            if current is not None:
                rows.append([" ".join(part for part in cell if part).strip()
                             for cell in current])
            current = None
            continue
        if not stripped.startswith(("|", "+")):
            continue
        if current is None:
            current = [[] for _ in range(len(cols) - 1)]
        split_after_line = False
        for ci in range(len(cols) - 1):
            a, b = cols[ci] + 1, cols[ci + 1]
            text, is_rule = _clean_grid_segment(line[a:b].replace("\0", "") if a < len(line) else "")
            split_after_line = split_after_line or is_rule
            if text:
                current[ci].append(text)
        if split_after_line:
            rows.append([" ".join(part for part in cell if part).strip()
                         for cell in current])
            current = None
    return [r for r in rows if any(r)]


def parse_list_table(body: list[str]) -> list[list[str]]:
    """Parse a list-table directive body into row cell-text lists."""
    def join_cell(parts: list[str]) -> str:
        if any(part.lstrip().startswith("|") for part in parts):
            return "\n".join(
                part.lstrip()[1:].lstrip()
                if part.lstrip().startswith("|")
                else part.strip()
                for part in parts
                if part.strip()
            ).strip()
        if any(part.startswith("- ") for part in parts):
            return "\n".join(part for part in parts if part).strip()
        return " ".join(part for part in parts if part).strip()

    rows: list[list[str]] = []
    row: list[str] | None = None
    cell: list[str] | None = None
    cell_marker_column: int | None = None

    def flush_cell() -> None:
        nonlocal cell
        if row is not None and cell is not None:
            row.append(join_cell(cell))
        cell = None

    for raw in body:
        line = raw.strip()
        if not line or line.startswith(":"):
            continue
        row_match = re.match(
            r"^(?P<prefix>[ \t]*\*[ \t]+)-(?:[ \t]?(?P<text>.*))?$",
            raw,
        )
        if row_match:
            flush_cell()
            row = []
            rows.append(row)
            cell = [(row_match.group("text") or "").strip()]
            cell_marker_column = len(row_match.group("prefix").expandtabs(8))
            continue

        cell_match = re.match(
            r"^(?P<indent>[ \t]*)-(?:[ \t]?(?P<text>.*))?$",
            raw,
        )
        if cell_match and row is not None and cell_marker_column is not None:
            marker_column = len(cell_match.group("indent").expandtabs(8))
            text = (cell_match.group("text") or "").strip()
            if marker_column == cell_marker_column:
                flush_cell()
                cell = [text]
            elif marker_column > cell_marker_column and cell is not None:
                cell.append(f"- {text}".rstrip())
            elif cell is not None:
                cell.append(line)
            continue

        if cell is not None:
            cell.append(line)

    flush_cell()
    return [r for r in rows if any(r)]
