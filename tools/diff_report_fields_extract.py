from __future__ import annotations

import re

from tools.diff_report_fields_shared import _clean_field_text
from tools.diff_report_models import FieldEntry

HEADING_UNDERLINE_RE = re.compile(r"^[=\-~^\"`:#*+]{3,}$")
SPEC_SECTION_RE = re.compile(r"\\specsectiontitle\{(.+?)\}")
HTML_SPEC_SECTION_RE = re.compile(r'<h2[^>]*>(.+?)</h2>', re.IGNORECASE)
PLAIN_COLON_FIELD_RE = re.compile(r"^\s*([A-Za-z0-9][^:]{0,120}?):\s+(.+?)\s*$")
BOLD_COLON_FIELD_RE = re.compile(r"^\s*\*\*(.+?)\*\*\s*(.*)$")
BOLD_FIELD_RE = re.compile(r"\*\*(.+?)\*\*")
ROW_START_RE = re.compile(r"^(?P<indent>\s*)\*\s-\s+(?P<value>.*)$")
CELL_START_RE = re.compile(r"^(?P<indent>\s*)-\s+(?P<value>.*)$")


def _looks_like_heading(lines: list[str], idx: int) -> bool:
    if idx + 1 >= len(lines):
        return False
    title = lines[idx].rstrip()
    underline = lines[idx + 1].strip()
    return bool(title.strip()) and bool(HEADING_UNDERLINE_RE.fullmatch(underline)) and len(underline) >= len(title.strip())


def _consume_list_table(lines: list[str], start_idx: int) -> tuple[list[list[str]], int]:
    table_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())
    idx = start_idx + 1
    rows: list[list[str]] = []
    current_row: list[list[str]] | None = None
    current_cell_idx: int | None = None

    def flush_row() -> None:
        nonlocal current_row, current_cell_idx
        if current_row is None:
            return
        rendered = [" ".join(part for part in cell if part).strip() for cell in current_row]
        rows.append(rendered)
        current_row = None
        current_cell_idx = None

    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())

        if stripped and indent <= table_indent and not stripped.startswith(":"):
            break

        row_match = ROW_START_RE.match(line)
        if row_match and len(row_match.group("indent")) > table_indent:
            flush_row()
            current_row = [[row_match.group("value").strip()]]
            current_cell_idx = 0
            idx += 1
            continue

        cell_match = CELL_START_RE.match(line)
        if cell_match and len(cell_match.group("indent")) > table_indent and current_row is not None:
            current_row.append([cell_match.group("value").strip()])
            current_cell_idx = len(current_row) - 1
            idx += 1
            continue

        if stripped and current_row is not None and current_cell_idx is not None:
            current_row[current_cell_idx].append(stripped)
        idx += 1

    flush_row()
    return rows, idx


def _build_field_entries(section_title: str, key: str, value: str, *, seen: dict[tuple[str, str], int]) -> FieldEntry | None:
    field_key = _clean_field_text(key)
    field_value = _clean_field_text(value)
    normalized_section = _clean_field_text(section_title)
    if not field_key:
        return None

    base = (normalized_section, field_key)
    count = seen.get(base, 0) + 1
    seen[base] = count
    if count > 1:
        field_key = f"{field_key} #{count}"
    return FieldEntry(section_title=normalized_section, field_key=field_key, field_value=field_value)


def extract_field_entries(rst_text: str) -> list[FieldEntry]:
    lines = rst_text.splitlines()
    entries: list[FieldEntry] = []
    current_heading = ""
    idx = 0
    seen: dict[tuple[str, str], int] = {}

    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()

        if _looks_like_heading(lines, idx):
            current_heading = _clean_field_text(lines[idx])
            idx += 2
            continue

        spec_match = SPEC_SECTION_RE.search(line)
        if spec_match:
            current_heading = _clean_field_text(spec_match.group(1))
            idx += 1
            continue

        html_spec_match = HTML_SPEC_SECTION_RE.search(line)
        if html_spec_match:
            current_heading = _clean_field_text(html_spec_match.group(1))
            idx += 1
            continue

        if stripped.startswith(".. list-table::"):
            rows, next_idx = _consume_list_table(lines, idx)
            header_rows = 0
            for probe_idx in range(idx + 1, min(next_idx, idx + 8)):
                option = lines[probe_idx].strip()
                if option.startswith(":header-rows:"):
                    try:
                        header_rows = int(option.split(":", 2)[-1].strip())
                    except ValueError:
                        header_rows = 0
                    break

            for row in rows[header_rows:]:
                cleaned_cells = [_clean_field_text(cell) for cell in row]
                cleaned_cells = [cell for cell in cleaned_cells if cell]
                if not cleaned_cells:
                    continue
                if len(cleaned_cells) == 1:
                    raw_cell = row[0]
                    bold_match = BOLD_FIELD_RE.search(raw_cell)
                    if bold_match:
                        key = bold_match.group(1)
                        value = raw_cell.replace(bold_match.group(0), "", 1)
                    else:
                        key = cleaned_cells[0]
                        value = ""
                else:
                    key = " / ".join(cleaned_cells[:-1])
                    value = cleaned_cells[-1]
                entry = _build_field_entries(current_heading, key, value, seen=seen)
                if entry is not None:
                    entries.append(entry)
            idx = next_idx
            continue

        bold_colon_match = BOLD_COLON_FIELD_RE.match(line)
        if bold_colon_match:
            raw_key = bold_colon_match.group(1).strip()
            remainder = bold_colon_match.group(2).strip()
            if raw_key.endswith(":"):
                entry = _build_field_entries(current_heading, raw_key[:-1].strip(), remainder.lstrip(":").strip(), seen=seen)
                if entry is not None:
                    entries.append(entry)
                idx += 1
                continue
            if remainder.startswith(":"):
                entry = _build_field_entries(current_heading, raw_key, remainder[1:].strip(), seen=seen)
                if entry is not None:
                    entries.append(entry)
                idx += 1
                continue

        colon_match = PLAIN_COLON_FIELD_RE.match(line)
        if colon_match:
            entry = _build_field_entries(current_heading, colon_match.group(1), colon_match.group(2), seen=seen)
            if entry is not None:
                entries.append(entry)

        idx += 1

    return entries
