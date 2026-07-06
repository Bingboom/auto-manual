"""RST table parsing helpers for the IDML prepared-bundle extractor."""
from __future__ import annotations

import re

_SEP_SEGMENT_RE = re.compile(r"^[=+-]+$")


def _is_table_rule(line: str) -> bool:
    return bool(re.fullmatch(r"\+[=+-]+\+", line.strip()))


def _clean_grid_segment(segment: str) -> tuple[str, bool]:
    text = segment.strip().strip("|").strip()
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
        stripped = line.strip()
        if _is_table_rule(stripped):
            if current is not None:
                rows.append([" ".join(part for part in cell if part).strip()
                             for cell in current])
            current = None
            continue
        if not stripped.startswith("|"):
            continue
        if current is None:
            current = [[] for _ in range(len(cols) - 1)]
        split_after_line = False
        for ci in range(len(cols) - 1):
            a, b = cols[ci] + 1, cols[ci + 1]
            text, is_rule = _clean_grid_segment(line[a:b] if a < len(line) else "")
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
    rows: list[list[str]] = []
    cell: list[str] | None = None
    for raw in body:
        line = raw.strip()
        if not line or line.startswith(":"):
            continue
        m = re.match(r"\*\s+-\s?(.*)", line)
        if m:
            rows.append([])
            cell = [m.group(1).strip()]
            rows[-1].append("")
        elif line.startswith("- ") and rows:
            if cell is not None:
                rows[-1][-1] = " ".join(x for x in cell if x).strip()
            cell = [line[2:].strip()]
            rows[-1].append("")
        elif cell is not None:
            cell.append(line)
        if cell is not None and rows:
            rows[-1][-1] = " ".join(x for x in cell if x).strip()
    return [r for r in rows if any(r)]
