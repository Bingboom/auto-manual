#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Text model + parsing + section selection for cloud-doc backport.

The foundation layer (debt-paydown D2-3): the Block model, document fetch/
normalization, markdown->block parsing, and section selection. Imports only
stdlib + path_utils, so the routing/apply/CLI layers can import Block & friends
from here without an import cycle. Re-exported by cloud_doc_backport.
"""
from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.utils.path_utils import get_paths  # noqa: E402


_SAFE_PATH_CHARS = re.compile(r"[^A-Za-z0-9._-]+")

_LARK_TAG_RE = re.compile(r"</?lark-[^>]*>", re.IGNORECASE)

_FEISHU_TEXT_TAG_RE = re.compile(r"</?text\b[^>]*>", re.IGNORECASE)

_TITLE_TAG_RE = re.compile(r"^\s*<title>.*?</title>\s*", re.IGNORECASE | re.DOTALL)

_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)

_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")

_LIST_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")

_RST_HEADING_CHARS = {"=": 1, "-": 2, "~": 3, "^": 4, '"': 5, "'": 6}

_RST_HEADING_UNDERLINE_RE = re.compile(r"^\s*([=\-~^\"'])\1{2,}\s*$")

_DOCUMENT_PREAMBLE_SECTION = "__document_preamble__"

_DOCUMENT_PREAMBLE_LABEL = "document preamble"

_IMAGE_SENTINELS = ("![image]", "<img>")

@dataclass(frozen=True)
class Block:
    kind: str
    text: str
    normalized: str
    heading_path: tuple[str, ...]
    line_no: int
    heading_level: int | None = None

@dataclass(frozen=True)
class SectionSelection:
    requested_title: str | None
    resolved_title: str | None
    inferred_from: str | None
    applied: bool
    baseline_found: bool
    fetched_found: bool
    baseline_blocks_before: int
    fetched_blocks_before: int
    baseline_blocks_after: int
    fetched_blocks_after: int

def _is_document_preamble_section(section_title: str | None) -> bool:
    return section_title == _DOCUMENT_PREAMBLE_SECTION

def _safe_path_token(value: str) -> str:
    token = _SAFE_PATH_CHARS.sub("-", value.strip()).strip(".-")
    return token or "cloud-doc-backport"

def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")

def _strip_document_title(text: str) -> str:
    return _TITLE_TAG_RE.sub("", text, count=1)

def _extract_doc_markdown(raw_text: str) -> str:
    """Return Markdown from plain text or the lark-cli JSON envelope."""
    stripped = raw_text.lstrip()
    if not stripped.startswith("{"):
        return raw_text
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        return raw_text
    if not isinstance(payload, dict):
        return raw_text

    data = payload.get("data")
    if isinstance(data, dict):
        markdown = data.get("markdown")
        if isinstance(markdown, str):
            return markdown

        document = data.get("document")
        if isinstance(document, dict):
            content = document.get("content")
            if isinstance(content, str):
                return _strip_document_title(content)

    markdown = payload.get("markdown")
    if isinstance(markdown, str):
        return markdown
    return raw_text

def _unwrap_markdown_link(value: str) -> str:
    text = str(value or "").strip()
    match = re.fullmatch(r"\[[^\]]*\]\((https?://[^)]+)\)", text)
    return match.group(1) if match else text

def _local_doc_path(doc_url: str) -> Path | None:
    if doc_url == "-":
        return None
    if doc_url.startswith("file://"):
        return Path(doc_url.removeprefix("file://"))
    path = Path(doc_url)
    if path.exists():
        return path
    return None

def fetch_doc_text(doc_url: str, *, lark_cli: str = "lark-cli") -> str:
    """Fetch a cloud doc, or read a local fixture when doc_url is a file path."""
    doc_url = _unwrap_markdown_link(doc_url)
    local_path = _local_doc_path(doc_url)
    if local_path is not None:
        return _extract_doc_markdown(_read_text(local_path))
    if doc_url == "-":
        return _extract_doc_markdown(sys.stdin.read())

    attempts = [
        [
            lark_cli,
            "docs",
            "+fetch",
            "--api-version",
            "v2",
            "--doc",
            doc_url,
            "--doc-format",
            "markdown",
        ],
        [lark_cli, "docs", "+fetch", "--doc", doc_url, "--doc-format", "markdown"],
        [lark_cli, "docs", "+fetch", "--doc", doc_url],
        [lark_cli, "docs", "+fetch", doc_url],
    ]
    errors: list[str] = []
    for command in attempts:
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except OSError as exc:
            errors.append(f"{shlex.join(command)} -> {exc}")
            continue
        if completed.returncode == 0 and completed.stdout.strip():
            return _extract_doc_markdown(completed.stdout)
        errors.append(
            f"{shlex.join(command)} -> exit {completed.returncode}: "
            f"{(completed.stderr or completed.stdout).strip()}"
        )
    raise RuntimeError("failed to fetch Feishu cloud doc:\n" + "\n".join(errors))

def _strip_lark_noise(text: str) -> str:
    text = _HTML_COMMENT_RE.sub("", text)
    text = _LARK_TAG_RE.sub("", text)
    # Feishu review highlights arrive as inline <text bgcolor="..."> metadata.
    # They mark what a reviewer selected; they are not source content.
    text = _FEISHU_TEXT_TAG_RE.sub("", text)
    text = text.replace("\u200b", "").replace("\ufeff", "")
    return text

def _normalize_inline(text: str) -> str:
    text = _strip_lark_noise(text)
    # Collapse image references to a stable placeholder. Feishu hosts each doc's
    # images under its own token and re-generates the alt description per import, so
    # two fetches of the "same" doc (e.g. an editable doc vs its baseline copy) have
    # different image markup for every image — pure noise that swamps the real text
    # edits. Treating every image as a placeholder drops that noise (the trade-off: a
    # genuine image *swap* in the same position is no longer flagged). Cover BOTH the
    # markdown form `![alt](token)` and the HTML `<img name alt src=token>` form that
    # Feishu emits for images inside tables.
    text = re.sub(r"!\[[^\]]*\](?:\([^)]*\))?", "![image]", text)
    text = re.sub(r"<img\b[^>]*/?>", "<img>", text)
    text = text.replace("**", "").replace("__", "")
    text = text.replace("\\n", "\n")
    text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def _table_separator(line: str) -> bool:
    return bool(_TABLE_SEPARATOR_RE.match(line))

def _rst_heading_level(line: str) -> int | None:
    match = _RST_HEADING_UNDERLINE_RE.match(line.strip())
    if not match:
        return None
    return _RST_HEADING_CHARS.get(match.group(1))

def _preprocessed_lines(text: str) -> list[tuple[int, str]]:
    """Convert simple RST headings to markdown headings while preserving line numbers."""
    raw_lines = text.splitlines()
    converted: list[tuple[int, str]] = []
    index = 0
    while index < len(raw_lines):
        line = _strip_lark_noise(raw_lines[index]).rstrip()
        if index + 1 < len(raw_lines):
            next_line = _strip_lark_noise(raw_lines[index + 1]).rstrip()
            heading_level = _rst_heading_level(next_line)
            title = _normalize_inline(line)
            if heading_level is not None and title and len(next_line.strip()) >= max(3, len(title) // 2):
                converted.append((index + 1, f"{'#' * heading_level} {title}"))
                index += 2
                continue
        converted.append((index + 1, line))
        index += 1
    return converted

def parse_blocks(text: str) -> list[Block]:
    """Parse fetched/baseline markdown-ish text into comparable blocks."""
    blocks: list[Block] = []
    heading_stack: list[str] = []
    paragraph_lines: list[str] = []
    paragraph_start = 0

    def current_path() -> tuple[str, ...]:
        return tuple(part for part in heading_stack if part)

    def add_block(kind: str, value: str, line_no: int, *, heading_level: int | None = None) -> None:
        cleaned = _strip_lark_noise(value).strip()
        normalized = _normalize_inline(cleaned)
        if not normalized:
            return
        blocks.append(
            Block(
                kind=kind,
                text=cleaned,
                normalized=normalized,
                heading_path=current_path(),
                line_no=line_no,
                heading_level=heading_level,
            )
        )

    def flush_paragraph() -> None:
        nonlocal paragraph_lines, paragraph_start
        if paragraph_lines:
            add_block("paragraph", " ".join(paragraph_lines), paragraph_start)
            paragraph_lines = []
            paragraph_start = 0

    for line_no, line in _preprocessed_lines(text):
        if not line.strip():
            flush_paragraph()
            continue

        heading = _HEADING_RE.match(line.strip())
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            title = _normalize_inline(heading.group(2))
            heading_stack = heading_stack[: level - 1]
            heading_stack.append(title)
            add_block("heading", line.strip(), line_no, heading_level=level)
            continue

        stripped = line.strip()
        if stripped.startswith("|") and "|" in stripped[1:]:
            flush_paragraph()
            if not _table_separator(stripped):
                add_block("table_row", stripped, line_no)
            continue

        if _LIST_RE.match(stripped):
            flush_paragraph()
            add_block("list_item", stripped, line_no)
            continue

        if not paragraph_lines:
            paragraph_start = line_no
        paragraph_lines.append(stripped)

    flush_paragraph()
    return blocks

def _location(block: Block | None) -> dict[str, Any]:
    if block is None:
        return {}
    location = {
        "kind": block.kind,
        "line_no": block.line_no,
        "heading_path": list(block.heading_path),
    }
    if block.heading_level is not None:
        location["heading_level"] = block.heading_level
    return location

def _context(blocks: list[Block], index: int) -> dict[str, str | None]:
    previous_text = blocks[index - 1].text if index > 0 else None
    next_text = blocks[index + 1].text if index + 1 < len(blocks) else None
    return {"previous": previous_text, "next": next_text}

def _heading_title(block: Block) -> str:
    if block.kind != "heading":
        return ""
    heading = _HEADING_RE.match(block.text.strip())
    if heading:
        return _normalize_inline(heading.group(2))
    return _normalize_inline(block.text)

def _section_key(title: str) -> str:
    return _normalize_inline(title).casefold()

def first_heading_title(blocks: list[Block]) -> str | None:
    for block in blocks:
        if block.kind == "heading":
            title = _heading_title(block)
            if title:
                return title
    return None

def select_section_blocks(blocks: list[Block], title: str) -> list[Block] | None:
    """Return a heading section and its content, stopping at the next peer heading."""
    title_key = _section_key(title)
    for start, block in enumerate(blocks):
        if block.kind != "heading" or _section_key(_heading_title(block)) != title_key:
            continue
        level = block.heading_level or max(1, len(block.heading_path))
        end = len(blocks)
        for index in range(start + 1, len(blocks)):
            candidate = blocks[index]
            if candidate.kind == "heading" and (candidate.heading_level or 1) <= level:
                end = index
                break
        return blocks[start:end]
    return None

def select_document_preamble_blocks(blocks: list[Block]) -> list[Block] | None:
    """Return the leading content before the first heading.

    Some generated review pages, notably ``00_preface.rst``, intentionally have
    no page title. When comparing that single source file with a full cloud
    document, the matching scope is the document lead-in before the first cloud
    heading, not the entire manual.
    """
    preamble: list[Block] = []
    for block in blocks:
        if block.kind == "heading":
            break
        preamble.append(block)
    return preamble if preamble else None

def _apply_section_selection(
    *,
    baseline_blocks: list[Block],
    fetched_blocks: list[Block],
    section_title: str | None,
    inferred_from: str | None,
    require_match: bool,
) -> tuple[list[Block], list[Block], SectionSelection]:
    baseline_before = len(baseline_blocks)
    fetched_before = len(fetched_blocks)
    if not section_title:
        selection = SectionSelection(
            requested_title=None,
            resolved_title=None,
            inferred_from=None,
            applied=False,
            baseline_found=False,
            fetched_found=False,
            baseline_blocks_before=baseline_before,
            fetched_blocks_before=fetched_before,
            baseline_blocks_after=baseline_before,
            fetched_blocks_after=fetched_before,
        )
        return baseline_blocks, fetched_blocks, selection

    if _is_document_preamble_section(section_title):
        selected_baseline = select_document_preamble_blocks(baseline_blocks)
        selected_fetched = select_document_preamble_blocks(fetched_blocks)
        resolved_title = _DOCUMENT_PREAMBLE_LABEL
    else:
        selected_baseline = select_section_blocks(baseline_blocks, section_title)
        selected_fetched = select_section_blocks(fetched_blocks, section_title)
        resolved_title = section_title
    baseline_found = selected_baseline is not None
    fetched_found = selected_fetched is not None
    if require_match and not (baseline_found and fetched_found):
        missing = []
        if not baseline_found:
            missing.append("baseline")
        if not fetched_found:
            missing.append("fetched")
        raise RuntimeError(f"section heading {section_title!r} was not found in: {', '.join(missing)}")

    applied = baseline_found and fetched_found
    if applied:
        baseline_blocks = selected_baseline or baseline_blocks
        fetched_blocks = selected_fetched or fetched_blocks

    selection = SectionSelection(
        requested_title=section_title if inferred_from is None and not _is_document_preamble_section(section_title) else None,
        resolved_title=resolved_title,
        inferred_from=inferred_from,
        applied=applied,
        baseline_found=baseline_found,
        fetched_found=fetched_found,
        baseline_blocks_before=baseline_before,
        fetched_blocks_before=fetched_before,
        baseline_blocks_after=len(baseline_blocks),
        fetched_blocks_after=len(fetched_blocks),
    )
    return baseline_blocks, fetched_blocks, selection

def _source_path_prefers_document_preamble(source_path: Path | None, blocks: list[Block]) -> bool:
    if source_path is None:
        return False
    if any(block.kind == "heading" for block in blocks):
        return False
    stem = source_path.stem.casefold()
    return stem in {"00_preface", "preface"} or stem.endswith("_preface")

def _auto_section_for_source(source_path: Path | None, source_text: str) -> tuple[str | None, str | None]:
    if source_path is None:
        return None, None
    blocks = parse_blocks(source_text)
    source_title = first_heading_title(blocks)
    if source_title:
        return source_title, _report_path_text(source_path)
    if _source_path_prefers_document_preamble(source_path, blocks):
        return _DOCUMENT_PREAMBLE_SECTION, _report_path_text(source_path)
    return None, None

def _display_path(path: Path) -> Path:
    try:
        return path.relative_to(get_paths().root)
    except ValueError:
        return path

def _report_path_text(path: Path) -> str:
    display = _display_path(path)
    return str(display) if display.is_absolute() else display.as_posix()
