from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from tools.source_intake_model import normalize_space


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")


@dataclass(frozen=True)
class MarkdownTable:
    headers: tuple[str, ...]
    rows: tuple[dict[str, str], ...]
    heading_path: tuple[str, ...]
    start_line: int


def _split_markdown_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def _clean_cell(value: str) -> str:
    text = str(value or "").strip()
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    return normalize_space(text)


def parse_markdown_tables(text: str) -> list[MarkdownTable]:
    """Parse simple pipe-style Markdown tables with their current heading path."""
    lines = text.splitlines()
    tables: list[MarkdownTable] = []
    heading_stack: list[str] = []
    index = 0
    while index < len(lines):
        raw_line = lines[index]
        heading = _HEADING_RE.match(raw_line.strip())
        if heading:
            level = len(heading.group(1))
            title = normalize_space(heading.group(2).strip("# "))
            heading_stack = heading_stack[: level - 1]
            heading_stack.append(title)
            index += 1
            continue

        if (
            "|" in raw_line
            and index + 1 < len(lines)
            and _TABLE_SEPARATOR_RE.match(lines[index + 1])
        ):
            headers = tuple(_clean_cell(cell) for cell in _split_markdown_row(raw_line))
            start_line = index + 1
            index += 2
            parsed_rows: list[dict[str, str]] = []
            while index < len(lines) and "|" in lines[index].strip():
                cells = [_clean_cell(cell) for cell in _split_markdown_row(lines[index])]
                if len(cells) < len(headers):
                    cells.extend([""] * (len(headers) - len(cells)))
                parsed_rows.append(dict(zip(headers, cells[: len(headers)])))
                index += 1
            if headers and parsed_rows:
                tables.append(
                    MarkdownTable(
                        headers=headers,
                        rows=tuple(parsed_rows),
                        heading_path=tuple(part for part in heading_stack if part),
                        start_line=start_line,
                    )
                )
            continue

        index += 1
    return tables


def pdf_to_text(path: str) -> str:
    """Extract the text layer of a 产品规格书 PDF via ``pdftotext``.

    Spec sheets are vector/text PDFs; the text layer (label line then value
    line(s)) is what the rule engine parses. Raises a clear error when the file
    has no usable text layer (scanned image) or is not a real PDF.
    """
    import shutil
    import subprocess

    if not shutil.which("pdftotext"):
        raise RuntimeError("pdftotext not found (install poppler) to read PDF spec sheets")
    proc = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True)
    text = proc.stdout or ""
    if not text.strip():
        raise RuntimeError(
            f"no extractable text in {path} (scanned/encrypted PDF?): {(proc.stderr or '').strip()[:120]}"
        )
    return text


def read_input_text(source: str, *, lark_cli: str = "lark-cli") -> str:
    """Read a local Markdown/PDF file, stdin, or a Feishu/Lark doc (backport fetcher)."""
    if source == "-":
        import sys

        return sys.stdin.read()

    from pathlib import Path

    path = Path(source)
    if path.exists():
        if path.suffix.lower() == ".pdf":
            return pdf_to_text(str(path))
        return path.read_text(encoding="utf-8-sig")

    from tools.cloud_doc_backport_model import fetch_doc_text

    return fetch_doc_text(source, lark_cli=lark_cli)


def table_payload(table: MarkdownTable) -> dict[str, Any]:
    return {
        "headers": list(table.headers),
        "heading_path": list(table.heading_path),
        "start_line": table.start_line,
        "row_count": len(table.rows),
    }
