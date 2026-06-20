#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Feishu cloud document backport helpers.

The diff command fetches/reads a Feishu cloud document, normalizes it, compares
it with a baseline, and writes structured JSON + Markdown diff reports.

The apply-template/apply-review commands can turn a diff report into guarded
local source edits. They never edit generated output or Feishu bitable rows.

Review writes funnel through ``run-review-branch`` (render-vs-render diff against a
stored baseline). A direct ``apply-review`` / ``run-review --write`` against the
``_review`` RST *source* is refused (it corrupts RST markup; see
``Backport_Rendered_Baseline_Design.md`` §1) unless ``--allow-rst-baseline`` is set.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.family_scope import build_family_index, classify_family_scope  # noqa: E402
from tools.source_table_sync import (  # noqa: E402
    apply_change_requests,
    build_change_request_report,
    load_change_requests,
    load_sidecar_index,
    load_translation_suggestions,
    write_change_request_report,
    write_source_table_apply_report,
)
from tools.backport_baseline import baseline_rel_path, load_baseline, store_baseline  # noqa: E402
from tools.review_branch_resolver import (  # noqa: E402
    doc_token,
    list_in_review_branches,
    match_review_branch,
    match_review_branch_by_name,
)
from tools.review_worktree import derive_review_source_rel, ensure_review_worktree  # noqa: E402
from tools.token_resolution_map import build_value_index, classify_data_origin  # noqa: E402
from tools.translation_memory_sync import apply_translation_suggestions  # noqa: E402
from tools.utils.path_utils import get_paths  # noqa: E402

REPORT_SCHEMA_VERSION = "cloud-doc-backport-report/v1"
DELTA_SCHEMA_VERSION = "cloud-doc-backport-delta/v1"
APPLY_SCHEMA_VERSION = "cloud-doc-backport-apply/v1"
VERIFY_SCHEMA_VERSION = "cloud-doc-backport-verify/v1"
RUN_SCHEMA_VERSION = "cloud-doc-backport-run/v1"
SOURCE_TABLE_SUGGESTIONS_SCHEMA_VERSION = "cloud-doc-backport-source-table-suggestions/v1"
TEMPLATE_SYNC_PROPOSAL_SCHEMA_VERSION = "cloud-doc-backport-template-sync-proposal/v1"
NORMALIZER_VERSION = "cloud-doc-normalizer/v3"

_SAFE_PATH_CHARS = re.compile(r"[^A-Za-z0-9._-]+")
_LARK_TAG_RE = re.compile(r"</?lark-[^>]*>", re.IGNORECASE)
_TITLE_TAG_RE = re.compile(r"^\s*<title>.*?</title>\s*", re.IGNORECASE | re.DOTALL)
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")
_LIST_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_PLACEHOLDER_RE = re.compile(r"(\{\{[^}]+\}\}|\|[A-Z][A-Z0-9_]+\|)")
_UNIT_VALUE_RE = re.compile(
    r"\b\d+(?:[.,]\d+)?\s?(?:W|V|A|Hz|Wh|kWh|mAh|Ah|degC|°C|%|mm|cm|m|kg|lb)\b",
    re.IGNORECASE,
)
_RST_HEADING_CHARS = {"=": 1, "-": 2, "~": 3, "^": 4, '"': 5, "'": 6}
_RST_HEADING_UNDERLINE_RE = re.compile(r"^\s*([=\-~^\"'])\1{2,}\s*$")
_DOCUMENT_PREAMBLE_SECTION = "__document_preamble__"
_DOCUMENT_PREAMBLE_LABEL = "document preamble"


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


def _utc_now() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _git_ref() -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=get_paths().root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    ref = completed.stdout.strip()
    return ref or None


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
        normalized = _normalize_inline(value)
        if not normalized:
            return
        blocks.append(
            Block(
                kind=kind,
                text=value.strip(),
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
        return source_title, _display_path(source_path).as_posix()
    if _source_path_prefers_document_preamble(source_path, blocks):
        return _DOCUMENT_PREAMBLE_SECTION, _display_path(source_path).as_posix()
    return None, None


def _looks_data_like(*blocks: Block | None) -> bool:
    text = " ".join(block.text for block in blocks if block is not None)
    if any(block and block.kind == "table_row" for block in blocks):
        return True
    return bool(_PLACEHOLDER_RE.search(text) or _UNIT_VALUE_RE.search(text))


def _classify_route(
    doc_type: str,
    old: Block | None,
    new: Block | None,
    data_origin: dict[str, Any] | None = None,
    family_scope: dict[str, Any] | None = None,
) -> tuple[str, str, str]:
    if data_origin is not None:
        # F2: the old text exactly matches a resolved data value, so this is a
        # data-origin (Class D) delta — deterministic, not the heuristic guess.
        if doc_type == "review":
            return (
                "source_table_suggestion",
                "high",
                f"resolved data value from {data_origin.get('table')}",
            )
        return (
            "needs_human_mapping",
            "low",
            "resolved data value in a template-maintenance document",
        )
    if _looks_data_like(old, new):
        if doc_type == "review":
            return (
                "source_table_suggestion",
                "medium",
                "table/value/placeholder-like delta in a review document",
            )
        return (
            "needs_human_mapping",
            "low",
            "data-like delta in a template-maintenance document",
        )
    if doc_type == "review":
        if family_scope is not None and family_scope.get("shared"):
            # F3: the span is identical across the family — template-origin shared
            # content. Flag for a human decision (shared-template change vs
            # target-local override) with blast radius; do not auto-route (R5).
            count = len(family_scope.get("targets") or [])
            return (
                "needs_human_mapping",
                "medium",
                f"span is identical across {count} family target(s): decide shared-template change vs target-local override",
            )
        return ("repo_review_text", "medium", "text delta in a review document")
    return ("repo_template_text", "medium", "text delta in a template document")


def _delta_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _make_delta(
    *,
    run_id: str,
    doc_type: str,
    change_type: str,
    old: Block | None,
    new: Block | None,
    old_index: int | None,
    new_index: int | None,
    baseline_blocks: list[Block],
    fetched_blocks: list[Block],
    value_index: dict[str, Any] | None = None,
    family_index: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data_origin = (
        classify_data_origin(old.text, value_index) if (value_index and old is not None) else None
    )
    family_scope = (
        classify_family_scope(old.text, family_index)
        if (family_index and old is not None and data_origin is None)
        else None
    )
    route_class, confidence, reason = _classify_route(doc_type, old, new, data_origin, family_scope)
    hash_payload = {
        "doc_type": doc_type,
        "change_type": change_type,
        "old": old.normalized if old else None,
        "new": new.normalized if new else None,
        "location": _location(new or old),
    }
    context: dict[str, Any] = {}
    if old_index is not None:
        context["baseline"] = _context(baseline_blocks, old_index)
    if new_index is not None:
        context["fetched"] = _context(fetched_blocks, new_index)
    return {
        "schema_version": DELTA_SCHEMA_VERSION,
        "run_id": run_id,
        "delta_hash": _delta_hash(hash_payload),
        "doc_type": doc_type,
        "change_type": change_type,
        "route_class": route_class,
        "confidence": confidence,
        "classification_reason": reason,
        "source_ref": data_origin,
        "family_scope": family_scope,
        "location": _location(new or old),
        "old_text": old.text if old else None,
        "new_text": new.text if new else None,
        "old_normalized": old.normalized if old else None,
        "new_normalized": new.normalized if new else None,
        "context": context,
    }


def diff_blocks(
    baseline_blocks: list[Block],
    fetched_blocks: list[Block],
    *,
    doc_type: str,
    run_id: str,
    value_index: dict[str, Any] | None = None,
    family_index: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    import difflib

    def diff_key(block: Block) -> str:
        if block.kind == "heading":
            return "heading:" + _section_key(_heading_title(block))
        return block.normalized

    baseline_norm = [diff_key(block) for block in baseline_blocks]
    fetched_norm = [diff_key(block) for block in fetched_blocks]
    matcher = difflib.SequenceMatcher(None, baseline_norm, fetched_norm, autojunk=False)
    deltas: list[dict[str, Any]] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag == "replace":
            old_range = list(range(i1, i2))
            new_range = list(range(j1, j2))
            paired = min(len(old_range), len(new_range))
            for offset in range(paired):
                old_index = old_range[offset]
                new_index = new_range[offset]
                deltas.append(
                    _make_delta(
                        run_id=run_id,
                        doc_type=doc_type,
                        change_type="replace",
                        old=baseline_blocks[old_index],
                        new=fetched_blocks[new_index],
                        old_index=old_index,
                        new_index=new_index,
                        baseline_blocks=baseline_blocks,
                        fetched_blocks=fetched_blocks,
                        value_index=value_index,
                        family_index=family_index,
                    )
                )
            for old_index in old_range[paired:]:
                deltas.append(
                    _make_delta(
                        run_id=run_id,
                        doc_type=doc_type,
                        change_type="delete",
                        old=baseline_blocks[old_index],
                        new=None,
                        old_index=old_index,
                        new_index=None,
                        baseline_blocks=baseline_blocks,
                        fetched_blocks=fetched_blocks,
                        value_index=value_index,
                        family_index=family_index,
                    )
                )
            for new_index in new_range[paired:]:
                deltas.append(
                    _make_delta(
                        run_id=run_id,
                        doc_type=doc_type,
                        change_type="insert",
                        old=None,
                        new=fetched_blocks[new_index],
                        old_index=None,
                        new_index=new_index,
                        baseline_blocks=baseline_blocks,
                        fetched_blocks=fetched_blocks,
                        value_index=value_index,
                        family_index=family_index,
                    )
                )
            continue

        if tag == "delete":
            for old_index in range(i1, i2):
                deltas.append(
                    _make_delta(
                        run_id=run_id,
                        doc_type=doc_type,
                        change_type="delete",
                        old=baseline_blocks[old_index],
                        new=None,
                        old_index=old_index,
                        new_index=None,
                        baseline_blocks=baseline_blocks,
                        fetched_blocks=fetched_blocks,
                        value_index=value_index,
                        family_index=family_index,
                    )
                )
            continue

        if tag == "insert":
            for new_index in range(j1, j2):
                deltas.append(
                    _make_delta(
                        run_id=run_id,
                        doc_type=doc_type,
                        change_type="insert",
                        old=None,
                        new=fetched_blocks[new_index],
                        old_index=None,
                        new_index=new_index,
                        baseline_blocks=baseline_blocks,
                        fetched_blocks=fetched_blocks,
                        value_index=value_index,
                        family_index=family_index,
                    )
                )
    return deltas


def _counter_dict(values: list[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def _source_kind_for_path(path: Path | None, doc_type: str) -> str | None:
    if path is None:
        return None
    parts = path.as_posix().split("/")
    if "templates" in parts:
        return "template"
    if "_review" in parts:
        return "review"
    return doc_type


def _source_target_payload(source_path: Path | None, doc_type: str) -> dict[str, str] | None:
    if source_path is None:
        return None
    return {
        "path": source_path.as_posix(),
        "kind": _source_kind_for_path(source_path, doc_type) or doc_type,
    }


def _selection_payload(selection: SectionSelection) -> dict[str, Any]:
    return {
        "requested_title": selection.requested_title,
        "resolved_title": selection.resolved_title,
        "inferred_from": selection.inferred_from,
        "applied": selection.applied,
        "baseline_found": selection.baseline_found,
        "fetched_found": selection.fetched_found,
        "baseline_blocks_before": selection.baseline_blocks_before,
        "fetched_blocks_before": selection.fetched_blocks_before,
        "baseline_blocks_after": selection.baseline_blocks_after,
        "fetched_blocks_after": selection.fetched_blocks_after,
    }


def _attach_source_evidence(
    deltas: list[dict[str, Any]],
    *,
    source_target: dict[str, str] | None,
    baseline_text: str,
) -> None:
    if source_target is None:
        return
    for delta in deltas:
        old_text = delta.get("old_text")
        old_in_source = bool(isinstance(old_text, str) and old_text and old_text in baseline_text)
        delta["source_evidence"] = {
            **source_target,
            "old_text_in_baseline": old_in_source,
            "repo_write_candidate": delta["route_class"] in {"repo_review_text", "repo_template_text"} and old_in_source,
        }


def build_report(
    *,
    run_id: str,
    doc_type: str,
    doc_url: str,
    baseline_path: Path,
    fetched_text: str,
    baseline_text: str,
    command: list[str],
    source_path: Path | None = None,
    section_title: str | None = None,
    section_inferred_from: str | None = None,
    require_section_match: bool = False,
    value_index: dict[str, Any] | None = None,
    family_index: dict[str, Any] | None = None,
) -> dict[str, Any]:
    baseline_blocks = parse_blocks(baseline_text)
    fetched_blocks = parse_blocks(fetched_text)
    baseline_blocks, fetched_blocks, selection = _apply_section_selection(
        baseline_blocks=baseline_blocks,
        fetched_blocks=fetched_blocks,
        section_title=section_title,
        inferred_from=section_inferred_from,
        require_match=require_section_match,
    )
    deltas = diff_blocks(
        baseline_blocks,
        fetched_blocks,
        doc_type=doc_type,
        run_id=run_id,
        value_index=value_index,
        family_index=family_index,
    )
    source_target = _source_target_payload(source_path, doc_type)
    _attach_source_evidence(deltas, source_target=source_target, baseline_text=baseline_text)
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "run_id": run_id,
        "doc_type": doc_type,
        "doc_url": doc_url,
        "baseline": baseline_path.as_posix(),
        "source_target": source_target,
        "section_selection": _selection_payload(selection),
        "normalizer_version": NORMALIZER_VERSION,
        "result": "DIFF" if deltas else "NO_DIFF",
        "metadata": {
            "generated_at": _utc_now(),
            "git_ref": _git_ref(),
            "command": shlex.join(command),
        },
        "summary": {
            "total_deltas": len(deltas),
            "baseline_blocks": len(baseline_blocks),
            "fetched_blocks": len(fetched_blocks),
            "change_types": _counter_dict([delta["change_type"] for delta in deltas]),
            "route_classes": _counter_dict([delta["route_class"] for delta in deltas]),
            "confidence": _counter_dict([delta["confidence"] for delta in deltas]),
        },
        "deltas": deltas,
    }


def _markdown_cell(value: object) -> str:
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False)
    else:
        text = str(value or "")
    return text.replace("\n", " ").replace("|", "\\|")


def markdown_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    source_target = report.get("source_target") or {}
    section_selection = report.get("section_selection") or {}
    lines = [
        "# Cloud Doc Backport Diff Report",
        "",
        "## Run",
        "",
        f"- Run ID: `{report['run_id']}`",
        f"- Result: `{report['result']}`",
        f"- Doc type: `{report['doc_type']}`",
        f"- Baseline: `{report['baseline']}`",
        f"- Source target: `{source_target.get('path') or '-'}`",
        f"- Normalizer: `{report['normalizer_version']}`",
        f"- Git ref: `{report['metadata'].get('git_ref') or 'unknown'}`",
        f"- Generated at: `{report['metadata']['generated_at']}`",
        f"- Command: `{report['metadata']['command']}`",
        f"- Section: `{section_selection.get('resolved_title') or '-'}`",
        f"- Section applied: `{section_selection.get('applied', False)}`",
        "",
        "## Summary",
        "",
        f"- Total deltas: `{summary['total_deltas']}`",
        f"- Baseline blocks: `{summary['baseline_blocks']}`",
        f"- Fetched blocks: `{summary['fetched_blocks']}`",
        f"- Change types: `{json.dumps(summary['change_types'], ensure_ascii=False)}`",
        f"- Route classes: `{json.dumps(summary['route_classes'], ensure_ascii=False)}`",
        "",
        "## Deltas",
        "",
    ]
    if not report["deltas"]:
        lines.append("No deltas.")
    else:
        lines.extend(
            [
                "| # | Type | Route | Confidence | Location | Old | New |",
                "| ---: | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for index, delta in enumerate(report["deltas"], start=1):
            location = delta["location"]
            heading = " > ".join(location.get("heading_path") or [])
            location_text = f"{location.get('kind', '-')}:L{location.get('line_no', '-')}"
            if heading:
                location_text = f"{heading} / {location_text}"
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(index),
                        _markdown_cell(delta["change_type"]),
                        _markdown_cell(delta["route_class"]),
                        _markdown_cell(delta["confidence"]),
                        _markdown_cell(location_text),
                        _markdown_cell(delta.get("old_text")),
                        _markdown_cell(delta.get("new_text")),
                    ]
                )
                + " |"
            )
    return "\n".join(lines) + "\n"


def write_reports(report: dict[str, Any], out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "cloud_doc_backport_report.json"
    markdown_path = out_dir / "cloud_doc_backport_report.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(markdown_report(report), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def _load_json_file(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(_read_text(path))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON file {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"JSON file must contain an object: {path}")
    return payload


def _resolve_source_path(value: str | None, *, label: str) -> Path:
    if not value:
        raise RuntimeError(f"missing {label}")
    path = Path(value)
    if not path.is_absolute():
        path = get_paths().root / path
    if not path.exists():
        raise RuntimeError(f"{label} does not exist: {value}")
    if not path.is_file():
        raise RuntimeError(f"{label} must be a file: {value}")
    return path


def _validate_apply_source(path: Path, *, kind: str) -> None:
    if path.suffix != ".rst":
        raise RuntimeError(f"{kind} source must be an .rst file: {path}")
    if kind == "template":
        if "templates" not in path.parts:
            raise RuntimeError(f"template source must live under a templates directory: {path}")
        return
    if kind == "review":
        if "_review" not in path.parts:
            raise RuntimeError(f"review source must live under docs/_review: {path}")
        return
    raise RuntimeError(f"unsupported apply source kind: {kind}")


def _apply_skip_reason(delta: dict[str, Any], *, route_class: str) -> str | None:
    if delta.get("route_class") != route_class:
        return f"route_class is {delta.get('route_class') or 'missing'}"
    change_type = delta.get("change_type")
    if change_type not in {"replace", "delete"}:
        return f"change_type is {delta.get('change_type') or 'missing'}"
    old_text = delta.get("old_text")
    new_text = delta.get("new_text")
    if not isinstance(old_text, str) or not old_text:
        return "old_text is missing"
    if change_type == "replace" and (not isinstance(new_text, str) or not new_text):
        return "new_text is missing"
    if change_type == "replace" and old_text == new_text:
        return "old_text and new_text are identical"
    evidence = delta.get("source_evidence")
    if isinstance(evidence, dict) and evidence.get("repo_write_candidate") is False:
        return "delta is not marked as a repo write candidate"
    return None


def _apply_operation(
    *,
    index: int,
    delta: dict[str, Any],
    current_text: str,
    route_class: str,
    source_label: str,
    write: bool,
) -> tuple[dict[str, Any], str]:
    reason = _apply_skip_reason(delta, route_class=route_class)
    base_operation = {
        "index": index,
        "delta_hash": delta.get("delta_hash"),
        "change_type": delta.get("change_type"),
        "route_class": delta.get("route_class"),
        "old_text": delta.get("old_text"),
        "new_text": delta.get("new_text"),
    }
    if reason is not None:
        return {**base_operation, "status": "skipped", "reason": reason, "matches": 0}, current_text

    old_text = str(delta["old_text"])
    change_type = str(delta.get("change_type") or "")
    new_text = "" if change_type == "delete" else str(delta["new_text"])
    matches = current_text.count(old_text)
    if matches == 0:
        return {
            **base_operation,
            "status": "skipped",
            "reason": f"old_text was not found in current {source_label}",
            "matches": matches,
        }, current_text
    if matches > 1:
        return {
            **base_operation,
            "status": "skipped",
            "reason": f"old_text matched more than once in current {source_label}",
            "matches": matches,
        }, current_text

    if write:
        return {
            **base_operation,
            "status": "applied",
            "reason": f"unique {route_class} {'deletion' if change_type == 'delete' else 'replacement'}",
            "matches": matches,
        }, current_text.replace(old_text, new_text, 1)
    return {
        **base_operation,
        "status": "planned",
        "reason": f"unique {route_class} {'deletion' if change_type == 'delete' else 'replacement'}",
        "matches": matches,
    }, current_text


def _refuse_unsafe_review_apply(
    diff_report: dict[str, Any],
    *,
    write: bool,
    allow_rst_baseline: bool,
) -> None:
    """Funnel review ``--write`` through ``run-review-branch`` (render-vs-render).

    A REVIEW diff whose baseline is the ``_review`` RST *source* is the broken
    source-vs-rendered path: the rendered cloud-doc mis-aligns against RST markup
    (``.. raw:: latex``, ``|TOKEN|``, ``| line-blocks``), so it over-reports and a
    ``--write`` corrupts the RST — the root cause the rendered-baseline design fixed
    (``Backport_Rendered_Baseline_Design.md`` §1). Applying it directly with a stray
    ``apply-review`` / ``run-review --write`` is the foot-gun that let an improvising
    agent splatter rendered text across many pages. Refuse it and steer to
    ``run-review-branch``, which diffs the cloud-doc against a stored render baseline
    and applies only clean Class R prose.

    Inert for: dry runs, template reports, render-baseline reports (``.baseline.md``),
    and any caller that passes ``--allow-rst-baseline`` — the ``run-review-branch``
    per-page worker and a deliberate single-page override.
    """
    if not write or allow_rst_baseline:
        return
    if diff_report.get("doc_type") != "review":
        return
    if str(diff_report.get("baseline") or "").endswith(".rst"):
        raise RuntimeError(
            "refusing a review --write against the RST source: the rendered-vs-RST "
            "diff over-reports and writing it corrupts the RST (.. raw:: latex / "
            "|TOKEN| / | line-blocks). Use `run-review-branch --cloud-doc <url> "
            "--doc-name <name> --write`, which diffs the cloud-doc against a render "
            "baseline and applies only clean Class R prose. To force the legacy "
            "single-page path, pass --allow-rst-baseline "
            "(Backport_Rendered_Baseline_Design.md §1)."
        )


def build_guarded_apply_report(
    diff_report: dict[str, Any],
    *,
    expected_doc_type: str,
    expected_source_kind: str,
    route_class: str,
    source_label: str,
    source_path: Path | None = None,
    write: bool = False,
    command: list[str] | None = None,
) -> dict[str, Any]:
    if diff_report.get("schema_version") != REPORT_SCHEMA_VERSION:
        raise RuntimeError("report schema is not cloud-doc-backport-report/v1")
    if diff_report.get("doc_type") != expected_doc_type:
        raise RuntimeError(f"apply-{expected_doc_type} requires a {expected_doc_type} diff report")
    source_target = diff_report.get("source_target")
    if not isinstance(source_target, dict):
        if source_path is None:
            raise RuntimeError("diff report is missing source_target")
        source_target = {"kind": expected_source_kind}
    elif source_target.get("kind") != expected_source_kind:
        raise RuntimeError(f"diff report source_target.kind must be {expected_source_kind}")

    resolved_source = source_path or _resolve_source_path(str(source_target.get("path") or ""), label="source target")
    _validate_apply_source(resolved_source, kind=expected_source_kind)
    original_text = _read_text(resolved_source)
    current_text = original_text
    operations: list[dict[str, Any]] = []
    for index, delta in enumerate(diff_report.get("deltas") or [], start=1):
        if not isinstance(delta, dict):
            operations.append(
                {
                    "index": index,
                    "status": "skipped",
                    "reason": "delta is not an object",
                    "matches": 0,
                }
            )
            continue
        operation, current_text = _apply_operation(
            index=index,
            delta=delta,
            current_text=current_text,
            route_class=route_class,
            source_label=source_label,
            write=write,
        )
        operations.append(operation)

    changed = current_text != original_text
    if write and changed:
        resolved_source.write_text(current_text, encoding="utf-8")

    statuses = _counter_dict([str(operation["status"]) for operation in operations])
    return {
        "schema_version": APPLY_SCHEMA_VERSION,
        "mode": "write" if write else "dry-run",
        "source_target": {
            "path": _display_path(resolved_source).as_posix(),
            "kind": expected_source_kind,
        },
        "diff_report": {
            "run_id": diff_report.get("run_id"),
            "result": diff_report.get("result"),
            "schema_version": diff_report.get("schema_version"),
        },
        "metadata": {
            "generated_at": _utc_now(),
            "git_ref": _git_ref(),
            "command": shlex.join(command or []),
        },
        "summary": {
            "total_operations": len(operations),
            "statuses": statuses,
            "changed": changed,
        },
        "operations": operations,
    }


def build_template_apply_report(
    diff_report: dict[str, Any],
    *,
    source_path: Path | None = None,
    write: bool = False,
    command: list[str] | None = None,
) -> dict[str, Any]:
    return build_guarded_apply_report(
        diff_report,
        expected_doc_type="template",
        expected_source_kind="template",
        route_class="repo_template_text",
        source_label="template",
        source_path=source_path,
        write=write,
        command=command,
    )


def build_review_apply_report(
    diff_report: dict[str, Any],
    *,
    source_path: Path | None = None,
    write: bool = False,
    command: list[str] | None = None,
) -> dict[str, Any]:
    return build_guarded_apply_report(
        diff_report,
        expected_doc_type="review",
        expected_source_kind="review",
        route_class="repo_review_text",
        source_label="review source",
        source_path=source_path,
        write=write,
        command=command,
    )


def markdown_apply_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Cloud Doc Backport Apply Report",
        "",
        "## Run",
        "",
        f"- Mode: `{report['mode']}`",
        f"- Source target: `{report['source_target']['path']}`",
        f"- Changed: `{summary['changed']}`",
        f"- Git ref: `{report['metadata'].get('git_ref') or 'unknown'}`",
        f"- Generated at: `{report['metadata']['generated_at']}`",
        f"- Command: `{report['metadata']['command']}`",
        "",
        "## Summary",
        "",
        f"- Total operations: `{summary['total_operations']}`",
        f"- Statuses: `{json.dumps(summary['statuses'], ensure_ascii=False)}`",
        "",
        "## Operations",
        "",
    ]
    if not report["operations"]:
        lines.append("No operations.")
    else:
        lines.extend(
            [
                "| # | Status | Reason | Matches | Old | New |",
                "| ---: | --- | --- | ---: | --- | --- |",
            ]
        )
        for operation in report["operations"]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(operation["index"]),
                        _markdown_cell(operation.get("status")),
                        _markdown_cell(operation.get("reason")),
                        _markdown_cell(operation.get("matches")),
                        _markdown_cell(operation.get("old_text")),
                        _markdown_cell(operation.get("new_text")),
                    ]
                )
                + " |"
            )
    return "\n".join(lines) + "\n"


def write_apply_report(report: dict[str, Any], out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "cloud_doc_backport_apply.json"
    markdown_path = out_dir / "cloud_doc_backport_apply.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(markdown_apply_report(report), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def _resolve_report_source(
    diff_report: dict[str, Any],
    *,
    expected_doc_type: str,
    expected_source_kind: str,
    source_path: Path | None,
    command_name: str,
) -> Path:
    if diff_report.get("schema_version") != REPORT_SCHEMA_VERSION:
        raise RuntimeError("report schema is not cloud-doc-backport-report/v1")
    if diff_report.get("doc_type") != expected_doc_type:
        raise RuntimeError(f"{command_name} requires a {expected_doc_type} diff report")
    source_target = diff_report.get("source_target")
    if not isinstance(source_target, dict):
        if source_path is None:
            raise RuntimeError("diff report is missing source_target")
        source_target = {"kind": expected_source_kind}
    elif source_target.get("kind") != expected_source_kind:
        raise RuntimeError(f"diff report source_target.kind must be {expected_source_kind}")
    resolved_source = source_path or _resolve_source_path(str(source_target.get("path") or ""), label="source target")
    _validate_apply_source(resolved_source, kind=expected_source_kind)
    return resolved_source


def _verify_delta(index: int, delta: dict[str, Any], current_text: str) -> dict[str, Any]:
    old_text = delta.get("old_text")
    new_text = delta.get("new_text")
    old_matches = current_text.count(old_text) if isinstance(old_text, str) and old_text else 0
    new_matches = current_text.count(new_text) if isinstance(new_text, str) and new_text else 0
    base_result = {
        "index": index,
        "delta_hash": delta.get("delta_hash"),
        "change_type": delta.get("change_type"),
        "route_class": delta.get("route_class"),
        "old_text": old_text,
        "new_text": new_text,
        "location": delta.get("location") or {},
        "source_evidence": delta.get("source_evidence") or {},
    }
    route_class = delta.get("route_class")
    if route_class == "source_table_suggestion":
        return {
            **base_result,
            "category": "source_table_suggestion",
            "status": "reported",
            "reason": "data-like review delta is report-only",
            "old_matches": old_matches,
            "new_matches": new_matches,
        }
    if route_class != "repo_review_text":
        return {
            **base_result,
            "category": "unsafe_or_ambiguous",
            "status": "blocked",
            "reason": f"route_class is {route_class or 'missing'}",
            "old_matches": 0,
            "new_matches": 0,
        }
    change_type = delta.get("change_type")
    if change_type not in {"replace", "delete"}:
        return {
            **base_result,
            "category": "unsafe_or_ambiguous",
            "status": "blocked",
            "reason": f"unsupported review change_type {change_type or 'missing'}",
            "old_matches": 0,
            "new_matches": 0,
        }
    if not isinstance(old_text, str) or not old_text:
        return {
            **base_result,
            "category": "unsafe_or_ambiguous",
            "status": "blocked",
            "reason": "old_text is missing",
            "old_matches": 0,
            "new_matches": 0,
        }
    if change_type == "replace" and (not isinstance(new_text, str) or not new_text):
        return {
            **base_result,
            "category": "unsafe_or_ambiguous",
            "status": "blocked",
            "reason": "new_text is missing",
            "old_matches": 0,
            "new_matches": 0,
        }

    if change_type == "delete":
        if old_matches == 0:
            return {
                **base_result,
                "category": "applied_resolved",
                "status": "resolved",
                "reason": "deleted old_text no longer exists",
                "old_matches": old_matches,
                "new_matches": new_matches,
            }
        if old_matches == 1:
            return {
                **base_result,
                "category": "still_pending",
                "status": "pending",
                "reason": "deleted old_text still exists",
                "old_matches": old_matches,
                "new_matches": new_matches,
            }
        return {
            **base_result,
            "category": "unsafe_or_ambiguous",
            "status": "blocked",
            "reason": "deleted old_text has an ambiguous match count",
            "old_matches": old_matches,
            "new_matches": new_matches,
        }

    if old_matches == 0 and new_matches >= 1:
        return {
            **base_result,
            "category": "applied_resolved",
            "status": "resolved",
            "reason": "old_text no longer exists and new_text is present",
            "old_matches": old_matches,
            "new_matches": new_matches,
        }
    if old_matches == 1 and new_matches == 0:
        return {
            **base_result,
            "category": "still_pending",
            "status": "pending",
            "reason": "old_text still exists and new_text is absent",
            "old_matches": old_matches,
            "new_matches": new_matches,
        }
    return {
        **base_result,
        "category": "unsafe_or_ambiguous",
        "status": "blocked",
        "reason": "current review source contains an ambiguous old/new text state",
        "old_matches": old_matches,
        "new_matches": new_matches,
    }


def _resolve_baseline_text(diff_report: dict[str, Any]) -> str | None:
    """Best-effort read of the diff baseline (for the F5 rebuild+rediff gate)."""
    baseline = diff_report.get("baseline")
    if not isinstance(baseline, str) or not baseline:
        return None
    for candidate in (Path(baseline), get_paths().root / baseline):
        if candidate.exists():
            try:
                return candidate.read_text(encoding="utf-8")
            except OSError:
                return None
    return None


def _rebuild_rediff_gate(
    *, baseline_text: str, edited_text: str, deltas: list[Any], run_id: str
) -> dict[str, Any]:
    """F5: re-diff baseline vs the edited source; the only changes must be the
    intended repo_review_text deltas (no collateral, none missing)."""

    def pair(delta: dict[str, Any]) -> tuple[Any, Any]:
        return (delta.get("old_normalized"), delta.get("new_normalized"))

    expected = {
        pair(delta)
        for delta in deltas
        if isinstance(delta, dict) and delta.get("route_class") == "repo_review_text"
    }
    actual = {
        pair(delta)
        for delta in diff_blocks(
            parse_blocks(baseline_text), parse_blocks(edited_text), doc_type="review", run_id=run_id
        )
    }
    unexpected = sorted(f"{old!r}->{new!r}" for old, new in (actual - expected))
    missing = sorted(f"{old!r}->{new!r}" for old, new in (expected - actual))
    return {
        "skipped": False,
        "passed": not unexpected and not missing,
        "unexpected": unexpected,
        "missing": missing,
    }


def _rebuild_rediff_for_report(diff_report: dict[str, Any], edited_text: str) -> dict[str, Any]:
    baseline = diff_report.get("baseline")
    source_path = (diff_report.get("source_target") or {}).get("path")
    if not baseline or (source_path and baseline == source_path):
        # The baseline is the in-place source (e.g. run-review uses the review
        # source as its own baseline); after apply we can no longer reconstruct the
        # pre-edit text, so the gate is unreliable. It runs only against a distinct
        # baseline snapshot (design §6 Baseline Storage). Skipping is gate-pass.
        return {"skipped": True, "reason": "no distinct baseline snapshot", "passed": True}
    baseline_text = _resolve_baseline_text(diff_report)
    if baseline_text is None:
        return {"skipped": True, "reason": "baseline unavailable", "passed": True}
    return _rebuild_rediff_gate(
        baseline_text=baseline_text,
        edited_text=edited_text,
        deltas=diff_report.get("deltas") or [],
        run_id=str(diff_report.get("run_id") or "verify"),
    )


def build_review_verify_report(
    diff_report: dict[str, Any],
    *,
    source_path: Path | None = None,
    command: list[str] | None = None,
) -> dict[str, Any]:
    resolved_source = _resolve_report_source(
        diff_report,
        expected_doc_type="review",
        expected_source_kind="review",
        source_path=source_path,
        command_name="verify-review",
    )
    current_text = _read_text(resolved_source)
    results: list[dict[str, Any]] = []
    for index, delta in enumerate(diff_report.get("deltas") or [], start=1):
        if isinstance(delta, dict):
            results.append(_verify_delta(index, delta, current_text))
        else:
            results.append(
                {
                    "index": index,
                    "category": "unsafe_or_ambiguous",
                    "status": "blocked",
                    "reason": "delta is not an object",
                    "old_matches": 0,
                    "new_matches": 0,
                }
            )
    categories = _counter_dict([str(result["category"]) for result in results])
    failing_categories = {category: categories.get(category, 0) for category in ("still_pending", "unsafe_or_ambiguous")}
    has_failure = any(count for count in failing_categories.values())
    rebuild_rediff = _rebuild_rediff_for_report(diff_report, current_text)
    source_table_suggestions = [
        result for result in results if result.get("category") == "source_table_suggestion"
    ]
    return {
        "schema_version": VERIFY_SCHEMA_VERSION,
        "result": "FAIL" if has_failure else "PASS",
        "source_target": {
            "path": _display_path(resolved_source).as_posix(),
            "kind": "review",
        },
        "diff_report": {
            "run_id": diff_report.get("run_id"),
            "result": diff_report.get("result"),
            "schema_version": diff_report.get("schema_version"),
        },
        "metadata": {
            "generated_at": _utc_now(),
            "git_ref": _git_ref(),
            "command": shlex.join(command or []),
        },
        "summary": {
            "total_results": len(results),
            "categories": categories,
            "failing_categories": {key: value for key, value in failing_categories.items() if value},
            "source_table_suggestions": len(source_table_suggestions),
            "rebuild_rediff_passed": rebuild_rediff.get("passed"),
        },
        "rebuild_rediff": rebuild_rediff,
        "source_table_suggestions": source_table_suggestions,
        "results": results,
    }


def markdown_verify_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Cloud Doc Backport Verify Report",
        "",
        "## Run",
        "",
        f"- Result: `{report['result']}`",
        f"- Source target: `{report['source_target']['path']}`",
        f"- Git ref: `{report['metadata'].get('git_ref') or 'unknown'}`",
        f"- Generated at: `{report['metadata']['generated_at']}`",
        f"- Command: `{report['metadata']['command']}`",
        "",
        "## Summary",
        "",
        f"- Total results: `{summary['total_results']}`",
        f"- Categories: `{json.dumps(summary['categories'], ensure_ascii=False)}`",
        f"- Failing categories: `{json.dumps(summary['failing_categories'], ensure_ascii=False)}`",
        f"- Source-table suggestions: `{summary['source_table_suggestions']}`",
        "",
        "## Results",
        "",
    ]
    if not report["results"]:
        lines.append("No results.")
    else:
        lines.extend(
            [
                "| # | Category | Status | Reason | Old matches | New matches | Old | New |",
                "| ---: | --- | --- | --- | ---: | ---: | --- | --- |",
            ]
        )
        for result in report["results"]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(result["index"]),
                        _markdown_cell(result.get("category")),
                        _markdown_cell(result.get("status")),
                        _markdown_cell(result.get("reason")),
                        _markdown_cell(result.get("old_matches")),
                        _markdown_cell(result.get("new_matches")),
                        _markdown_cell(result.get("old_text")),
                        _markdown_cell(result.get("new_text")),
                    ]
                )
                + " |"
            )
    suggestions = report.get("source_table_suggestions") or []
    lines.extend(["", "## Source-Table Suggestions", ""])
    if not suggestions:
        lines.append("No source-table suggestions.")
    else:
        lines.extend(
            [
                "| # | Location | Old | New | Evidence |",
                "| ---: | --- | --- | --- | --- |",
            ]
        )
        for suggestion in suggestions:
            location = suggestion.get("location") or {}
            heading = " > ".join(location.get("heading_path") or [])
            location_text = f"{location.get('kind', '-')}:L{location.get('line_no', '-')}"
            if heading:
                location_text = f"{heading} / {location_text}"
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(suggestion.get("index")),
                        _markdown_cell(location_text),
                        _markdown_cell(suggestion.get("old_text")),
                        _markdown_cell(suggestion.get("new_text")),
                        _markdown_cell(suggestion.get("source_evidence")),
                    ]
                )
                + " |"
            )
    return "\n".join(lines) + "\n"


def write_verify_report(report: dict[str, Any], out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "cloud_doc_backport_verify.json"
    markdown_path = out_dir / "cloud_doc_backport_verify.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(markdown_verify_report(report), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def _suggestion_heading_text(suggestion: dict[str, Any]) -> str:
    location = suggestion.get("location") if isinstance(suggestion.get("location"), dict) else {}
    return " > ".join(str(part) for part in (location.get("heading_path") or []) if part)


def _source_table_routing_hint(suggestion: dict[str, Any]) -> dict[str, Any]:
    text = " ".join(
        str(suggestion.get(key) or "") for key in ("old_text", "new_text", "old_normalized", "new_normalized")
    )
    heading = _suggestion_heading_text(suggestion)
    searchable = f"{heading} {text}".lower()
    if _PLACEHOLDER_RE.search(text):
        return {
            "route_key": "placeholder_or_page_value",
            "candidate_source_tables": ["页面占位参数", "Variable_Defaults", "Variable_Lang_Overrides"],
            "confidence": "medium",
            "reason": "placeholder-like token changed in reviewed prose",
        }
    if "troubleshoot" in searchable or "故障" in searchable or "排除" in searchable:
        return {
            "route_key": "troubleshooting_block",
            "candidate_source_tables": ["troubleshooting_blocks", "TROUBLESHOOTING"],
            "confidence": "medium",
            "reason": "suggestion is under a troubleshooting-like heading",
        }
    if "symbol" in searchable or "符号" in searchable or "icon" in searchable or "图标" in searchable:
        return {
            "route_key": "symbol_or_lcd_block",
            "candidate_source_tables": ["symbols_blocks", "lcd_icons"],
            "confidence": "medium",
            "reason": "suggestion is under a symbol/icon-like heading",
        }
    if _UNIT_VALUE_RE.search(text) or "spec" in searchable or "规格" in searchable:
        return {
            "route_key": "spec_or_numeric_value",
            "candidate_source_tables": ["规格参数明细", "Spec_Notes", "Spec_Master read model"],
            "confidence": "medium",
            "reason": "numeric/unit or spec-like value changed",
        }
    location = suggestion.get("location") if isinstance(suggestion.get("location"), dict) else {}
    if location.get("kind") == "table_row":
        return {
            "route_key": "structured_table_row",
            "candidate_source_tables": ["Manual_Copy_Source", "Spec_Notes", "symbols_blocks", "troubleshooting_blocks"],
            "confidence": "low",
            "reason": "review delta came from a table row but no specific table family was inferred",
        }
    return {
        "route_key": "phase2_source_table_review",
        "candidate_source_tables": ["Manual_Copy_Source", "phase2 source tables"],
        "confidence": "low",
        "reason": "data-like review delta needs operator mapping to the source table",
    }


def _operator_locator(suggestion: dict[str, Any]) -> dict[str, Any]:
    location = suggestion.get("location") if isinstance(suggestion.get("location"), dict) else {}
    heading = _suggestion_heading_text(suggestion)
    return {
        "heading_path": location.get("heading_path") or [],
        "heading": heading,
        "line_no": location.get("line_no"),
        "kind": location.get("kind"),
        "old_text": suggestion.get("old_text"),
        "new_text": suggestion.get("new_text"),
    }


def build_source_table_suggestions_report(
    *,
    run_report: dict[str, Any] | None = None,
    diff_report: dict[str, Any] | None = None,
    verify_report: dict[str, Any] | None = None,
    suggestions: list[dict[str, Any]] | None = None,
    command: list[str] | None = None,
) -> dict[str, Any]:
    if suggestions is None:
        if verify_report:
            suggestions = list(verify_report.get("source_table_suggestions") or [])
        elif run_report:
            suggestions = list(run_report.get("source_table_suggestions") or [])
        elif diff_report:
            suggestions = _source_table_suggestions_from_diff(diff_report)
        else:
            suggestions = []
    source_target = (
        (run_report or {}).get("source_target")
        or (verify_report or {}).get("source_target")
        or (diff_report or {}).get("source_target")
    )
    enriched: list[dict[str, Any]] = []
    for fallback_index, suggestion in enumerate(suggestions, start=1):
        if not isinstance(suggestion, dict):
            continue
        routing_hint = _source_table_routing_hint(suggestion)
        enriched.append(
            {
                "index": suggestion.get("index") or fallback_index,
                "delta_hash": suggestion.get("delta_hash"),
                "status": "operator_review_required",
                "external_write": False,
                "routing_hint": routing_hint,
                "operator_locator": _operator_locator(suggestion),
                "old_text": suggestion.get("old_text"),
                "new_text": suggestion.get("new_text"),
                "source_evidence": suggestion.get("source_evidence") or {},
                "reason": suggestion.get("reason") or "data-like review delta is report-only",
            }
        )
    route_counts = _counter_dict([str(item["routing_hint"]["route_key"]) for item in enriched])
    candidate_tables = sorted(
        {
            table
            for item in enriched
            for table in item.get("routing_hint", {}).get("candidate_source_tables", [])
            if table
        }
    )
    run_id = (
        (run_report or {}).get("diff_report", {}).get("run_id")
        or (verify_report or {}).get("diff_report", {}).get("run_id")
        or (diff_report or {}).get("run_id")
    )
    return {
        "schema_version": SOURCE_TABLE_SUGGESTIONS_SCHEMA_VERSION,
        "result": "HAS_SUGGESTIONS" if enriched else "NO_SUGGESTIONS",
        "run_id": run_id,
        "source_target": source_target,
        "metadata": {
            "generated_at": _utc_now(),
            "git_ref": _git_ref(),
            "command": shlex.join(command or []),
        },
        "summary": {
            "total_suggestions": len(enriched),
            "route_keys": route_counts,
            "candidate_source_tables": candidate_tables,
            "external_write": False,
        },
        "operator_contract": {
            "purpose": "Review report-only data-like deltas before updating Feishu phase2 source tables.",
            "external_write": False,
            "next_steps": [
                "Update the appropriate Feishu phase2 source row manually.",
                "Run sync-data for the affected source table.",
                "Run sync-review or the target build/check flow to regenerate the review package.",
            ],
        },
        "suggestions": enriched,
    }


def markdown_source_table_suggestions_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    source_target = report.get("source_target") or {}
    lines = [
        "# Cloud Doc Backport Source-Table Suggestions",
        "",
        "## Contract",
        "",
        "- External write: `False`",
        "- Purpose: review data-like deltas before updating Feishu phase2 source tables.",
        f"- Source target: `{source_target.get('path') or '-'}`",
        f"- Git ref: `{report['metadata'].get('git_ref') or 'unknown'}`",
        f"- Generated at: `{report['metadata']['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- Result: `{report['result']}`",
        f"- Total suggestions: `{summary['total_suggestions']}`",
        f"- Route keys: `{json.dumps(summary['route_keys'], ensure_ascii=False)}`",
        f"- Candidate source tables: `{', '.join(summary['candidate_source_tables']) or '-'}`",
        "",
        "## Suggested Operator Steps",
        "",
    ]
    for step in report["operator_contract"]["next_steps"]:
        lines.append(f"- {step}")
    lines.extend(["", "## Suggestions", ""])
    suggestions = report.get("suggestions") or []
    if not suggestions:
        lines.append("No source-table suggestions.")
        return "\n".join(lines) + "\n"
    lines.extend(
        [
            "| # | Route | Candidate Tables | Confidence | Location | Old | New |",
            "| ---: | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for suggestion in suggestions:
        routing = suggestion.get("routing_hint") or {}
        locator = suggestion.get("operator_locator") or {}
        location_parts = []
        if locator.get("heading"):
            location_parts.append(str(locator.get("heading")))
        if locator.get("kind") or locator.get("line_no"):
            location_parts.append(f"{locator.get('kind', '-')}:L{locator.get('line_no', '-')}")
        lines.append(
            "| "
            + " | ".join(
                [
                    str(suggestion.get("index")),
                    _markdown_cell(routing.get("route_key")),
                    _markdown_cell(", ".join(routing.get("candidate_source_tables") or [])),
                    _markdown_cell(routing.get("confidence")),
                    _markdown_cell(" / ".join(location_parts) or "-"),
                    _markdown_cell(suggestion.get("old_text")),
                    _markdown_cell(suggestion.get("new_text")),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def write_source_table_suggestions_report(report: dict[str, Any], out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "cloud_doc_backport_source_table_suggestions.json"
    markdown_path = out_dir / "cloud_doc_backport_source_table_suggestions.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(markdown_source_table_suggestions_report(report), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def _source_table_suggestions_from_diff(diff_report: dict[str, Any]) -> list[dict[str, Any]]:
    suggestions: list[dict[str, Any]] = []
    for index, delta in enumerate(diff_report.get("deltas") or [], start=1):
        if not isinstance(delta, dict) or delta.get("route_class") != "source_table_suggestion":
            continue
        suggestions.append(
            {
                "index": index,
                "delta_hash": delta.get("delta_hash"),
                "change_type": delta.get("change_type"),
                "route_class": delta.get("route_class"),
                "old_text": delta.get("old_text"),
                "new_text": delta.get("new_text"),
                "location": delta.get("location") or {},
                "source_evidence": delta.get("source_evidence") or {},
                "status": "reported",
                "reason": "data-like review delta is report-only",
            }
        )
    return suggestions


def _template_sync_proposals_from_diff(diff_report: dict[str, Any]) -> list[dict[str, Any]]:
    """F4: report-only proposals for Class T (shared-across-family) review deltas."""
    proposals: list[dict[str, Any]] = []
    for index, delta in enumerate(diff_report.get("deltas") or [], start=1):
        if not isinstance(delta, dict):
            continue
        family_scope = delta.get("family_scope")
        if not (isinstance(family_scope, dict) and family_scope.get("shared")):
            continue
        proposals.append(
            {
                "index": index,
                "delta_hash": delta.get("delta_hash"),
                "change_type": delta.get("change_type"),
                "old_text": delta.get("old_text"),
                "new_text": delta.get("new_text"),
                "location": delta.get("location") or {},
                "family_scope": family_scope,
                "target_templates": list(family_scope.get("targets") or []),
                "post_apply": "rebuild + sync-review the affected family targets, then verify (R7 rebuild+rediff gate)",
                "status": "reported",
                "reason": "span identical across the family - apply as a shared template change after review (R5)",
            }
        )
    return proposals


def build_template_sync_proposal_report(*, diff_report: dict[str, Any], command: list[str]) -> dict[str, Any]:
    proposals = _template_sync_proposals_from_diff(diff_report)
    return {
        "schema_version": TEMPLATE_SYNC_PROPOSAL_SCHEMA_VERSION,
        "run_id": diff_report.get("run_id"),
        "external_write": False,
        "summary": {"proposals": len(proposals)},
        "proposals": proposals,
        "metadata": {
            "generated_at": _utc_now(),
            "git_ref": _git_ref(),
            "command": shlex.join(command),
        },
    }


def markdown_template_sync_proposal_report(report: dict[str, Any]) -> str:
    proposals = report.get("proposals") or []
    lines = [
        "# Template Sync Proposal",
        "",
        f"- Run ID: `{report.get('run_id')}`",
        f"- Proposals: `{report['summary']['proposals']}`",
        "- External write: `false` (report-only; apply via the template-sync role)",
        "",
    ]
    if not proposals:
        lines.append("_No shared-across-family (Class T) deltas in this run._")
        return "\n".join(lines) + "\n"
    lines += ["| # | change | targets | old | new |", "| --- | --- | --- | --- | --- |"]
    for proposal in proposals:
        lines.append(
            "| {index} | {change} | {targets} | {old} | {new} |".format(
                index=proposal.get("index"),
                change=_markdown_cell(proposal.get("change_type")),
                targets=_markdown_cell(", ".join(proposal.get("target_templates") or [])),
                old=_markdown_cell(proposal.get("old_text")),
                new=_markdown_cell(proposal.get("new_text")),
            )
        )
    return "\n".join(lines) + "\n"


def write_template_sync_proposal_report(report: dict[str, Any], out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "cloud_doc_backport_template_sync_proposal.json"
    markdown_path = out_dir / "cloud_doc_backport_template_sync_proposal.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(markdown_template_sync_proposal_report(report), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def _repo_text_changes_from_diff(diff_report: dict[str, Any]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for index, delta in enumerate(diff_report.get("deltas") or [], start=1):
        if not isinstance(delta, dict) or delta.get("route_class") != "repo_review_text":
            continue
        changes.append(
            {
                "index": index,
                "delta_hash": delta.get("delta_hash"),
                "change_type": delta.get("change_type"),
                "route_class": delta.get("route_class"),
                "old_text": delta.get("old_text"),
                "new_text": delta.get("new_text"),
                "location": delta.get("location") or {},
                "source_evidence": delta.get("source_evidence") or {},
                "status": "repo_write_candidate",
            }
        )
    return changes


def _display_report_paths(paths: dict[str, Path]) -> dict[str, str]:
    return {key: _display_path(path).as_posix() for key, path in sorted(paths.items())}


def build_review_run_report(
    diff_report: dict[str, Any],
    *,
    apply_report: dict[str, Any] | None,
    verify_report: dict[str, Any] | None,
    write: bool,
    output_paths: dict[str, Path],
    command: list[str] | None = None,
) -> dict[str, Any]:
    diff_summary = diff_report.get("summary") or {}
    apply_summary = apply_report.get("summary") if apply_report else {}
    verify_summary = verify_report.get("summary") if verify_report else {}
    changed = bool(apply_summary.get("changed")) if isinstance(apply_summary, dict) else False
    verify_result = verify_report.get("result") if verify_report else None
    rebuild_rediff = verify_report.get("rebuild_rediff") if verify_report else None
    rebuild_ok = rebuild_rediff.get("passed", True) if isinstance(rebuild_rediff, dict) else True
    if diff_report.get("result") == "NO_DIFF":
        result = "NO_DIFF"
    elif not write:
        result = "DRY_RUN"
    elif verify_result == "PASS" and rebuild_ok:
        # F5: a write run is PR_READY only when the rebuild+rediff gate confirms the
        # edit reproduces the accepted doc and changes nothing else.
        result = "PR_READY" if changed else "PASS"
    else:
        result = "FAIL"

    if verify_report:
        source_table_suggestions = list(verify_report.get("source_table_suggestions") or [])
    else:
        source_table_suggestions = _source_table_suggestions_from_diff(diff_report)
    review_source_changes = _repo_text_changes_from_diff(diff_report)

    next_actions = {
        "NO_DIFF": ["No source change is needed."],
        "DRY_RUN": ["Review the apply report, then rerun with --write to patch the review source."],
        "PR_READY": ["Open a PR with the changed docs/_review source and attach the run report."],
        "PASS": ["No review-source PR is needed; route source-table suggestions deliberately if any exist."],
        "FAIL": ["Inspect the verify report before opening a PR."],
    }[result]

    return {
        "schema_version": RUN_SCHEMA_VERSION,
        "result": result,
        "mode": "write" if write else "dry-run",
        "source_target": diff_report.get("source_target"),
        "section_selection": diff_report.get("section_selection") or {},
        "diff_report": {
            "run_id": diff_report.get("run_id"),
            "result": diff_report.get("result"),
            "schema_version": diff_report.get("schema_version"),
        },
        "apply_report": {
            "mode": apply_report.get("mode"),
            "schema_version": apply_report.get("schema_version"),
        }
        if apply_report
        else None,
        "verify_report": {
            "result": verify_report.get("result"),
            "schema_version": verify_report.get("schema_version"),
        }
        if verify_report
        else None,
        "metadata": {
            "generated_at": _utc_now(),
            "git_ref": _git_ref(),
            "command": shlex.join(command or []),
        },
        "summary": {
            "total_deltas": int(diff_summary.get("total_deltas") or 0),
            "route_classes": dict(diff_summary.get("route_classes") or {}),
            "apply_statuses": dict(apply_summary.get("statuses") or {}) if isinstance(apply_summary, dict) else {},
            "verify_categories": dict(verify_summary.get("categories") or {})
            if isinstance(verify_summary, dict)
            else {},
            "verify_failing_categories": dict(verify_summary.get("failing_categories") or {})
            if isinstance(verify_summary, dict)
            else {},
            "changed": changed,
            "pr_ready": result == "PR_READY",
            "review_source_changes": len(review_source_changes),
            "source_table_suggestions": len(source_table_suggestions),
        },
        "reports": _display_report_paths(output_paths),
        "next_actions": next_actions,
        "review_source_changes": review_source_changes,
        "source_table_suggestions": source_table_suggestions,
    }


def markdown_review_run_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Cloud Doc Backport Run Report",
        "",
        "## Run",
        "",
        f"- Result: `{report['result']}`",
        f"- Mode: `{report['mode']}`",
        f"- Source target: `{(report.get('source_target') or {}).get('path') or '-'}`",
        f"- Section: `{(report.get('section_selection') or {}).get('resolved_title') or '-'}`",
        f"- Section applied: `{(report.get('section_selection') or {}).get('applied', False)}`",
        f"- Git ref: `{report['metadata'].get('git_ref') or 'unknown'}`",
        f"- Generated at: `{report['metadata']['generated_at']}`",
        f"- Command: `{report['metadata']['command']}`",
        "",
        "## Summary",
        "",
        f"- Total deltas: `{summary['total_deltas']}`",
        f"- Route classes: `{json.dumps(summary['route_classes'], ensure_ascii=False)}`",
        f"- Apply statuses: `{json.dumps(summary['apply_statuses'], ensure_ascii=False)}`",
        f"- Verify categories: `{json.dumps(summary['verify_categories'], ensure_ascii=False)}`",
        f"- Verify failing categories: `{json.dumps(summary['verify_failing_categories'], ensure_ascii=False)}`",
        f"- Changed: `{summary['changed']}`",
        f"- PR ready: `{summary['pr_ready']}`",
        f"- Review-source changes: `{summary['review_source_changes']}`",
        f"- Source-table suggestions: `{summary['source_table_suggestions']}`",
        "",
        "## Reports",
        "",
    ]
    for label, path in report["reports"].items():
        lines.append(f"- {label}: `{path}`")
    lines.extend(["", "## Next Actions", ""])
    for action in report["next_actions"]:
        lines.append(f"- {action}")

    changes = report.get("review_source_changes") or []
    lines.extend(["", "## Review-Source Changes", ""])
    if not changes:
        lines.append("No review-source changes.")
    else:
        lines.extend(
            [
                "| # | Type | Location | Old | New |",
                "| ---: | --- | --- | --- | --- |",
            ]
        )
        for change in changes:
            location = change.get("location") or {}
            heading = " > ".join(location.get("heading_path") or [])
            location_text = f"{location.get('kind', '-')}:L{location.get('line_no', '-')}"
            if heading:
                location_text = f"{heading} / {location_text}"
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(change.get("index")),
                        _markdown_cell(change.get("change_type")),
                        _markdown_cell(location_text),
                        _markdown_cell(change.get("old_text")),
                        _markdown_cell(change.get("new_text")),
                    ]
                )
                + " |"
            )

    suggestions = report.get("source_table_suggestions") or []
    lines.extend(["", "## Source-Table Suggestions", ""])
    if not suggestions:
        lines.append("No source-table suggestions.")
    else:
        lines.extend(
            [
                "| # | Location | Old | New |",
                "| ---: | --- | --- | --- |",
            ]
        )
        for suggestion in suggestions:
            location = suggestion.get("location") or {}
            heading = " > ".join(location.get("heading_path") or [])
            location_text = f"{location.get('kind', '-')}:L{location.get('line_no', '-')}"
            if heading:
                location_text = f"{heading} / {location_text}"
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(suggestion.get("index")),
                        _markdown_cell(location_text),
                        _markdown_cell(suggestion.get("old_text")),
                        _markdown_cell(suggestion.get("new_text")),
                    ]
                )
                + " |"
            )
    return "\n".join(lines) + "\n"


def write_review_run_report(report: dict[str, Any], out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "cloud_doc_backport_run.json"
    markdown_path = out_dir / "cloud_doc_backport_run.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(markdown_review_run_report(report), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def _default_out_dir(run_id: str) -> Path:
    return get_paths().cloud_doc_backport_reports_dir / _safe_path_token(run_id)


def _resolve_existing_path(value: str | None, *, label: str) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = get_paths().root / path
    if not path.exists():
        raise RuntimeError(f"{label} does not exist: {value}")
    if not path.is_file():
        raise RuntimeError(f"{label} must be a file: {value}")
    return path


def _display_path(path: Path) -> Path:
    try:
        return path.relative_to(get_paths().root)
    except ValueError:
        return path


def _resolve_repo_file(root: Path, value: str | None, *, label: str) -> Path:
    if not value:
        raise RuntimeError(f"missing {label}")
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    resolved = path.resolve(strict=False)
    resolved_root = root.resolve(strict=False)
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimeError(f"{label} must live under repo root: {value}") from exc
    if not resolved.exists():
        raise RuntimeError(f"{label} does not exist: {value}")
    if not resolved.is_file():
        raise RuntimeError(f"{label} must be a file: {value}")
    return resolved


def _repo_relative(root: Path, path: Path) -> str:
    return path.resolve(strict=False).relative_to(root.resolve(strict=False)).as_posix()


def _parse_git_status_paths(stdout: str) -> list[str]:
    paths: list[str] = []
    for raw_line in stdout.splitlines():
        if not raw_line.strip():
            continue
        path_text = raw_line[3:].strip() if len(raw_line) > 3 else raw_line.strip()
        if " -> " in path_text:
            path_text = path_text.split(" -> ", 1)[1].strip()
        if path_text:
            paths.append(path_text)
    return paths


def _run_pr_command(command: list[str], *, root: Path, stdin: str | None = None) -> str:
    completed = subprocess.run(
        command,
        cwd=root,
        input=stdin,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(f"{detail or 'command failed'} (exit={completed.returncode}, cmd={shlex.join(command)})")
    return completed.stdout.strip()


def _safe_branch_segment(value: str) -> str:
    return _SAFE_PATH_CHARS.sub("-", value.strip()).strip(".-") or "backport"


def _default_backport_branch_name(manifest: dict[str, Any], manifest_path: Path) -> str:
    source_path = str((manifest.get("source_target") or {}).get("path") or "")
    parts = Path(source_path).parts
    model = "manual"
    region = "review"
    if "_review" in parts:
        index = parts.index("_review")
        if index + 1 < len(parts):
            model = parts[index + 1]
        if index + 2 < len(parts):
            region = parts[index + 2]
    run_token = _safe_branch_segment(manifest_path.parent.name)[-32:]
    return f"review/{_safe_branch_segment(model)}-{_safe_branch_segment(region)}-cloud-doc-backport-{run_token}"


def _validate_open_pr_manifest(manifest: dict[str, Any], *, source_path: Path) -> None:
    if manifest.get("schema_version") != RUN_SCHEMA_VERSION:
        raise RuntimeError("manifest schema is not cloud-doc-backport-run/v1")
    if manifest.get("result") != "PR_READY":
        raise RuntimeError(f"manifest result must be PR_READY, got {manifest.get('result') or '-'}")
    summary = manifest.get("summary") if isinstance(manifest.get("summary"), dict) else {}
    if summary.get("pr_ready") is not True:
        raise RuntimeError("manifest summary.pr_ready must be true")
    if summary.get("changed") is not True:
        raise RuntimeError("manifest summary.changed must be true")
    source_target = manifest.get("source_target") if isinstance(manifest.get("source_target"), dict) else {}
    if source_target.get("kind") != "review":
        raise RuntimeError("manifest source_target.kind must be review")
    _validate_apply_source(source_path, kind="review")


def _pr_body_from_manifest(
    manifest: dict[str, Any],
    *,
    manifest_rel: str,
    source_rel: str,
) -> str:
    summary = manifest.get("summary") if isinstance(manifest.get("summary"), dict) else {}
    reports = manifest.get("reports") if isinstance(manifest.get("reports"), dict) else {}
    lines = [
        "## Summary",
        "",
        "- What changed: Applied accepted Feishu cloud-doc review revisions to the in-review source.",
        f"- Why it changed: `{manifest_rel}` reported `PR_READY` for `{source_rel}`.",
        "",
        "---",
        "",
        "## Change Type",
        "",
        "- [x] Bug fix",
        "- [ ] Feature",
        "- [ ] Refactor",
        "- [ ] Performance",
        "- [ ] Config / schema change",
        "- [ ] Workflow / CI change",
        "",
        "---",
        "",
        "## Impact Surface",
        "",
        "- [ ] CSV schema / structured snapshot",
        "- [ ] Template / page assembly",
        "- [ ] Build entrypoint / CLI",
        "- [x] Review / diff / publish / release flow",
        "- [x] External integrations (Feishu / DingTalk / OpenClaw)",
        "- [ ] Docs / CI / maintainer workflow",
        "",
        "---",
        "",
        "## Anti-Debt Checklist",
        "",
        "- [x] New low-level logic was kept out of `build.py`, `tools/build_docs.py`, and `tools/process_build_queue.py`",
        "- [x] No new config was added only because the model changed",
        "",
        "---",
        "",
        "## Cloud-Doc Backport Manifest",
        "",
        f"- Manifest: `{manifest_rel}`",
        f"- Source: `{source_rel}`",
        f"- Result: `{manifest.get('result') or '-'}`",
        f"- Mode: `{manifest.get('mode') or '-'}`",
        f"- Total deltas: `{summary.get('total_deltas', 0)}`",
        f"- Source-table suggestions: `{summary.get('source_table_suggestions', 0)}`",
        "",
        "Reports remain local evidence and are not committed by this helper:",
    ]
    for label, path in sorted(reports.items()):
        lines.append(f"- {label}: `{path}`")
    lines.extend(
        [
            "",
            "---",
            "",
            "## Validation",
            "",
            "- [ ] `python -m unittest`",
            "- [ ] Additional targeted verification:",
            f"  - `python tools/cloud_doc_backport.py open-pr --manifest {manifest_rel}`",
        ]
    )
    return "\n".join(lines) + "\n"


def open_backport_pr_from_manifest(
    *,
    manifest_path: Path,
    repo_root: Path,
    branch_name: str | None = None,
    base_ref: str = "main",
    git_bin: str = "git",
    gh_bin: str = "gh",
) -> dict[str, Any]:
    root = repo_root.resolve(strict=False)
    manifest_file = _resolve_repo_file(root, str(manifest_path), label="manifest")
    manifest = _load_json_file(manifest_file)
    source_target = manifest.get("source_target") if isinstance(manifest.get("source_target"), dict) else {}
    source_file = _resolve_repo_file(root, str(source_target.get("path") or ""), label="source target")
    _validate_open_pr_manifest(manifest, source_path=source_file)

    manifest_rel = _repo_relative(root, manifest_file)
    source_rel = _repo_relative(root, source_file)
    report_dir_rel = _repo_relative(root, manifest_file.parent)
    status_paths = _parse_git_status_paths(_run_pr_command([git_bin, "status", "--porcelain"], root=root))
    unexpected = [
        path
        for path in status_paths
        if path != source_rel and not path.startswith(f"{report_dir_rel}/")
    ]
    if unexpected:
        raise RuntimeError(
            "refusing to open PR with unrelated working-tree changes: " + ", ".join(unexpected[:5])
        )
    if source_rel not in status_paths:
        raise RuntimeError(f"source target has no working-tree change to commit: {source_rel}")

    current_branch = _run_pr_command([git_bin, "branch", "--show-current"], root=root)
    if current_branch != base_ref:
        raise RuntimeError(f"open-pr must run from {base_ref}; current branch is {current_branch or '-'}")

    resolved_branch = branch_name or _default_backport_branch_name(manifest, manifest_file)
    commit_title = "fix(backport): apply cloud doc review revisions"
    pr_body = _pr_body_from_manifest(manifest, manifest_rel=manifest_rel, source_rel=source_rel)

    _run_pr_command([git_bin, "switch", "-c", resolved_branch], root=root)
    _run_pr_command([git_bin, "add", source_rel], root=root)
    _run_pr_command(
        [
            git_bin,
            "commit",
            "-m",
            commit_title,
            "-m",
            f"Source: {source_rel}\nManifest: {manifest_rel}",
        ],
        root=root,
    )
    commit_sha = _run_pr_command([git_bin, "rev-parse", "HEAD"], root=root)
    _run_pr_command([git_bin, "push", "-u", "origin", resolved_branch], root=root)
    pr_url = _run_pr_command(
        [
            gh_bin,
            "pr",
            "create",
            "--base",
            base_ref,
            "--head",
            resolved_branch,
            "--draft",
            "--title",
            commit_title,
            "--body",
            pr_body,
        ],
        root=root,
    ).splitlines()[-1].strip()
    switch_back_warning = ""
    try:
        _run_pr_command([git_bin, "switch", base_ref], root=root)
    except RuntimeError as exc:
        switch_back_warning = str(exc)
    result = {
        "schema_version": "cloud-doc-backport-pr/v1",
        "result": "PR_OPENED",
        "branch": resolved_branch,
        "base_ref": base_ref,
        "commit": commit_sha,
        "pr_url": pr_url,
        "manifest_path": manifest_rel,
        "source_path": source_rel,
        "source_table_suggestions": int((manifest.get("summary") or {}).get("source_table_suggestions") or 0),
    }
    if switch_back_warning:
        result["warning"] = f"draft PR opened, but switching back to {base_ref} failed: {switch_back_warning}"
    return result


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Feishu cloud-doc backport helpers.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    diff_parser = subparsers.add_parser(
        "diff",
        description="Fetch/read a cloud doc and compare it with a baseline.",
    )
    diff_parser.add_argument("--doc-url", required=True, help="Feishu doc URL or local fixture path")
    diff_parser.add_argument("--baseline", help="baseline markdown/RST file")
    diff_parser.add_argument("--source-path", help="repo source target path; also used as fallback baseline")
    diff_parser.add_argument("--template", help="repo template source path; shortcut for --source-path")
    diff_parser.add_argument("--section-heading", help="heading to compare within both fetched and baseline content")
    diff_parser.add_argument(
        "--no-auto-section",
        action="store_true",
        help="do not infer a section heading from the source target's first heading",
    )
    diff_parser.add_argument("--doc-type", required=True, choices=("review", "template"))
    diff_parser.add_argument("--out", help="output directory for JSON and Markdown reports")
    diff_parser.add_argument("--run-id", default="cloud-doc-backport-local")
    diff_parser.add_argument("--lark-cli", default="lark-cli", help="lark-cli binary for real docs")
    diff_parser.add_argument("--lang", help="value-column lang (e.g. fr) to enable data-origin (Class D) detection")
    diff_parser.add_argument("--data-root", help="phase2 snapshot dir for the token/copy value index (used with --lang)")
    diff_parser.add_argument("--sibling", action="append", default=[], help="sibling target source path for family-scope (R vs T) detection; repeatable")

    apply_parser = subparsers.add_parser(
        "apply-template",
        description="Plan or apply safe template text replacements from a diff report.",
    )
    apply_parser.add_argument("--report", required=True, help="cloud_doc_backport_report.json path")
    apply_parser.add_argument("--source-path", help="optional source template override")
    apply_parser.add_argument("--out", help="output directory for JSON and Markdown apply reports")
    apply_parser.add_argument("--write", action="store_true", help="write safe replacements to the source template")

    apply_review_parser = subparsers.add_parser(
        "apply-review",
        description="Plan or apply safe review text replacements from a diff report.",
    )
    apply_review_parser.add_argument("--report", required=True, help="cloud_doc_backport_report.json path")
    apply_review_parser.add_argument("--source-path", help="optional review source override")
    apply_review_parser.add_argument("--out", help="output directory for JSON and Markdown apply reports")
    apply_review_parser.add_argument("--write", action="store_true", help="write safe replacements to the review source")
    apply_review_parser.add_argument(
        "--allow-rst-baseline",
        action="store_true",
        help="legacy escape hatch: permit --write from a report diffed against the RST source (corrupts markup; prefer run-review-branch)",
    )

    verify_review_parser = subparsers.add_parser(
        "verify-review",
        description="Verify review backport residuals from a diff report against the current review source.",
    )
    verify_review_parser.add_argument("--report", required=True, help="cloud_doc_backport_report.json path")
    verify_review_parser.add_argument("--source-path", help="optional review source override")
    verify_review_parser.add_argument("--out", help="output directory for JSON and Markdown verify reports")

    run_review_parser = subparsers.add_parser(
        "run-review",
        description="Run review cloud-doc diff, guarded apply, and optional residual verify as one workflow.",
    )
    run_review_parser.add_argument("--doc-url", required=True, help="Feishu doc URL or local fixture path")
    run_review_parser.add_argument(
        "--source-path",
        required=True,
        help="docs/_review/... .rst source target; also used as the diff baseline",
    )
    run_review_parser.add_argument("--section-heading", help="heading to compare within fetched and review content")
    run_review_parser.add_argument(
        "--no-auto-section",
        action="store_true",
        help="do not infer a section heading from the review source's first heading",
    )
    run_review_parser.add_argument("--out", help="output directory for all JSON and Markdown reports")
    run_review_parser.add_argument("--run-id", default="cloud-doc-backport-local")
    run_review_parser.add_argument("--lark-cli", default="lark-cli", help="lark-cli binary for real docs")
    run_review_parser.add_argument("--lang", help="value-column lang (e.g. fr) to enable data-origin (Class D) detection")
    run_review_parser.add_argument("--data-root", help="phase2 snapshot dir for the token/copy value index (used with --lang)")
    run_review_parser.add_argument("--sibling", action="append", default=[], help="sibling target source path for family-scope (R vs T) detection; repeatable")
    run_review_parser.add_argument(
        "--write",
        action="store_true",
        help="write safe review replacements, then verify residuals",
    )
    run_review_parser.add_argument(
        "--allow-rst-baseline",
        action="store_true",
        help="legacy escape hatch: permit --write against the RST source (corrupts markup; prefer run-review-branch)",
    )

    open_pr_parser = subparsers.add_parser(
        "open-pr",
        description="Open a draft PR from a PR_READY review backport run manifest.",
    )
    open_pr_parser.add_argument("--manifest", required=True, help="cloud_doc_backport_run.json path")
    open_pr_parser.add_argument("--branch", help="optional PR branch name")
    open_pr_parser.add_argument("--base", default="main", help="base branch; defaults to main")
    open_pr_parser.add_argument("--repo-root", help="repo root override for tests or worktrees")
    open_pr_parser.add_argument("--git-bin", default="git", help="git binary")
    open_pr_parser.add_argument("--gh-bin", default="gh", help="GitHub CLI binary")
    open_pr_parser.add_argument("--json", action="store_true", help="print the PR result as JSON")

    apply_source_table_parser = subparsers.add_parser(
        "apply-source-table",
        description=(
            "Apply HUMAN-APPROVED source-table change requests to Bitable (F6). "
            "Dry-run by default; --write needs --table-binding mappings. Each request "
            "is R9-gated: human approval + exact record_id + content field + idempotent."
        ),
    )
    apply_source_table_parser.add_argument(
        "--report", required=True, help="cloud_doc_backport_source_table_change_request.json path"
    )
    apply_source_table_parser.add_argument(
        "--approve",
        action="append",
        default=[],
        metavar="DELTA_HASH",
        help="a human-approved delta_hash; repeatable. Only these are eligible to write.",
    )
    apply_source_table_parser.add_argument("--out", help="output directory (defaults to the report's directory)")
    apply_source_table_parser.add_argument(
        "--write",
        action="store_true",
        help="actually write approved+resolved requests to Bitable (else dry-run plan only)",
    )
    apply_source_table_parser.add_argument(
        "--table-binding",
        action="append",
        default=[],
        metavar="TABLE=BASE:TABLE_ID",
        help=(
            "writable Feishu binding for a change-request table, e.g. "
            "'Manual_Copy_Source=bascnXXXX:tblYYYY'; repeatable. Required (per table) "
            "with --write. Unmapped tables are skipped safely."
        ),
    )
    apply_source_table_parser.add_argument(
        "--tm-write",
        action="store_true",
        help=(
            "also write approved TRANSLATION suggestions back to the Translation_Memory "
            "(widest blast radius; gated separately from --write). Needs --tm-binding."
        ),
    )
    apply_source_table_parser.add_argument(
        "--tm-binding",
        metavar="BASE:TABLE_ID",
        help="Translation_Memory Feishu binding 'BASE_TOKEN:TABLE_ID'; required with --tm-write",
    )
    apply_source_table_parser.add_argument("--lark-cli", default="lark-cli", help="lark-cli binary for --write")
    apply_source_table_parser.add_argument("--identity", default="bot", help="lark-cli identity for --write")

    resolve_branch_parser = subparsers.add_parser(
        "resolve-review-branch",
        description=(
            "Resolve a Feishu cloud-doc to its in-review branch (Git_ref) + "
            "docs/_review/<model>/<region> path via the Document_link build table. "
            "The review _review tree lives on that branch, not the default branch."
        ),
    )
    resolve_branch_parser.add_argument("--cloud-doc", required=True, help="the edited Feishu cloud-doc URL or doc name (falls back to name -> model+region)")
    resolve_branch_parser.add_argument("--lark-cli", default="lark-cli", help="lark-cli binary")
    resolve_branch_parser.add_argument("--identity", default="bot", help="lark-cli identity (user|bot)")

    run_review_branch_parser = subparsers.add_parser(
        "run-review-branch",
        description=(
            "One-shot branch-targeted backport: resolve the cloud-doc's review branch, "
            "ensure a worktree of it, run-review against its docs/_review file (the "
            "source path is DERIVED, never a template), and optionally push to update "
            "its PR. Dry-run unless --write."
        ),
    )
    run_review_branch_parser.add_argument("--cloud-doc", required=True, help="the edited Feishu cloud-doc URL (used to FETCH the doc content)")
    run_review_branch_parser.add_argument("--doc-name", help="doc name (e.g. manual_je1000f_eu_en_0.8) to resolve the review branch by model+region when the URL is not registered (a 副本/copy)")
    run_review_branch_parser.add_argument("--page", help="a single review page (e.g. 00_preface.rst); omit to diff the WHOLE doc against every docs/_review/<model>/<region>/page/*.rst")
    run_review_branch_parser.add_argument("--write", action="store_true", help="apply edits to the worktree's _review file (else dry-run)")
    run_review_branch_parser.add_argument("--push", action="store_true", help="commit + push the review branch (updates its PR); needs --write")
    run_review_branch_parser.add_argument(
        "--seed",
        action="store_true",
        help="store the current cloud-doc as the render baseline (approach C) instead of diffing — declares the current state as 'already reviewed'. Use only when there are no pending un-backported edits. --push commits it.",
    )
    run_review_branch_parser.add_argument(
        "--reseed",
        action="store_true",
        help="with --seed: overwrite an existing baseline (default refuses to overwrite)",
    )
    run_review_branch_parser.add_argument("--worktrees-root", help="where to create review worktrees (default: ../review-worktrees)")
    run_review_branch_parser.add_argument("--remote", default="origin", help="git remote")
    run_review_branch_parser.add_argument("--git-bin", default="git", help="git binary")
    run_review_branch_parser.add_argument("--full-checkout", action="store_true", help="materialize the whole repo in the worktree (default: sparse, only docs/_review/<model>/<region>)")
    run_review_branch_parser.add_argument("--run-id", default="cloud-doc-backport-branch")
    run_review_branch_parser.add_argument("--out", help="output directory for run-review reports")
    run_review_branch_parser.add_argument("--lark-cli", default="lark-cli", help="lark-cli binary")
    run_review_branch_parser.add_argument("--identity", default="bot", help="lark-cli identity (user|bot)")
    run_review_branch_parser.add_argument(
        "--data-root", default="data/phase2",
        help="structured-content snapshot root for the F2 value-index (classifies a delta as Class D / source-bound when its old text matches a source value); default data/phase2",
    )
    run_review_branch_parser.add_argument(
        "--lang",
        help="value-column lang suffix for the F2 value-index (en/fr/es/de/it/uk/ja/zh/pt-BR); auto-derived from --doc-name when omitted",
    )

    sync_worktrees_parser = subparsers.add_parser(
        "sync-review-worktrees",
        description="Ensure a git worktree exists for every InReview branch in the build table (so a backport always has its docs/_review tree).",
    )
    sync_worktrees_parser.add_argument("--worktrees-root", help="where to create review worktrees (default: ../review-worktrees)")
    sync_worktrees_parser.add_argument("--remote", default="origin", help="git remote")
    sync_worktrees_parser.add_argument("--git-bin", default="git", help="git binary")
    sync_worktrees_parser.add_argument("--full-checkout", action="store_true", help="materialize the whole repo in each worktree (default: sparse, only docs/_review/<model>/<region>)")
    sync_worktrees_parser.add_argument("--lark-cli", default="lark-cli", help="lark-cli binary")
    sync_worktrees_parser.add_argument("--identity", default="bot", help="lark-cli identity (user|bot)")
    return parser.parse_args(argv)


def _run_diff(args: argparse.Namespace, raw_argv: list[str]) -> int:
    run_id = str(args.run_id or "").strip() or "cloud-doc-backport-local"
    out_dir = Path(args.out) if args.out else _default_out_dir(run_id)
    try:
        if args.template and args.source_path:
            raise RuntimeError("--template and --source-path are mutually exclusive")
        if args.template and args.doc_type != "template":
            raise RuntimeError("--template requires --doc-type template")
        source_path = _resolve_existing_path(args.template or args.source_path, label="source target")
        baseline_path = _resolve_existing_path(args.baseline, label="baseline")
        if baseline_path is None:
            baseline_path = source_path
        if baseline_path is None:
            raise RuntimeError("--baseline is required unless --template or --source-path is supplied")
        baseline_text = _read_text(baseline_path)
        fetched_text = fetch_doc_text(args.doc_url, lark_cli=args.lark_cli)
        section_title = str(args.section_heading or "").strip() or None
        section_inferred_from = None
        if section_title is None and source_path is not None and not args.no_auto_section:
            section_title, section_inferred_from = _auto_section_for_source(source_path, _read_text(source_path))
    except (OSError, RuntimeError) as exc:
        print(f"cloud-doc-backport: {exc}", file=sys.stderr)
        return 2
    try:
        report = build_report(
            run_id=run_id,
            doc_type=args.doc_type,
            doc_url=args.doc_url,
            baseline_path=_display_path(baseline_path),
            fetched_text=fetched_text,
            baseline_text=baseline_text,
            command=["tools/cloud_doc_backport.py", *raw_argv],
            source_path=_display_path(source_path) if source_path else None,
            section_title=section_title,
            section_inferred_from=section_inferred_from,
            require_section_match=bool(args.section_heading),
            value_index=_value_index_from_args(args),
            family_index=_family_index_from_args(args),
        )
    except RuntimeError as exc:
        print(f"cloud-doc-backport: {exc}", file=sys.stderr)
        return 2
    written = write_reports(report, out_dir)
    print(f"WROTE {written['json']}")
    print(f"WROTE {written['markdown']}")
    return 0


def _run_apply(
    args: argparse.Namespace,
    raw_argv: list[str],
    *,
    build_apply_report: Any,
) -> int:
    try:
        report_path = _resolve_source_path(args.report, label="diff report")
        source_override = _resolve_source_path(args.source_path, label="source target") if args.source_path else None
        diff_report = _load_json_file(report_path)
        _refuse_unsafe_review_apply(
            diff_report,
            write=bool(args.write),
            allow_rst_baseline=getattr(args, "allow_rst_baseline", False),
        )
        apply_report = build_apply_report(
            diff_report,
            source_path=source_override,
            write=bool(args.write),
            command=["tools/cloud_doc_backport.py", *raw_argv],
        )
    except (OSError, RuntimeError) as exc:
        print(f"cloud-doc-backport: {exc}", file=sys.stderr)
        return 2
    out_dir = Path(args.out) if args.out else report_path.parent
    written = write_apply_report(apply_report, out_dir)
    print(f"WROTE {written['json']}")
    print(f"WROTE {written['markdown']}")
    if args.write and apply_report["summary"]["changed"]:
        print(f"UPDATED {apply_report['source_target']['path']}")
    return 0


def _run_apply_template(args: argparse.Namespace, raw_argv: list[str]) -> int:
    return _run_apply(args, raw_argv, build_apply_report=build_template_apply_report)


def _run_apply_review(args: argparse.Namespace, raw_argv: list[str]) -> int:
    return _run_apply(args, raw_argv, build_apply_report=build_review_apply_report)


def _run_verify_review(args: argparse.Namespace, raw_argv: list[str]) -> int:
    try:
        report_path = _resolve_source_path(args.report, label="diff report")
        source_override = _resolve_source_path(args.source_path, label="source target") if args.source_path else None
        diff_report = _load_json_file(report_path)
        verify_report = build_review_verify_report(
            diff_report,
            source_path=source_override,
            command=["tools/cloud_doc_backport.py", *raw_argv],
        )
    except (OSError, RuntimeError) as exc:
        print(f"cloud-doc-backport: {exc}", file=sys.stderr)
        return 2
    out_dir = Path(args.out) if args.out else report_path.parent
    written = write_verify_report(verify_report, out_dir)
    suggestions_report = build_source_table_suggestions_report(
        diff_report=diff_report,
        verify_report=verify_report,
        command=["tools/cloud_doc_backport.py", *raw_argv],
    )
    suggestions_written = write_source_table_suggestions_report(suggestions_report, out_dir)
    proposal_report = build_template_sync_proposal_report(
        diff_report=diff_report,
        command=["tools/cloud_doc_backport.py", *raw_argv],
    )
    proposal_written = write_template_sync_proposal_report(proposal_report, out_dir)
    print(f"WROTE {written['json']}")
    print(f"WROTE {written['markdown']}")
    print(f"WROTE {suggestions_written['json']}")
    print(f"WROTE {suggestions_written['markdown']}")
    print(f"WROTE {proposal_written['json']}")
    print(f"WROTE {proposal_written['markdown']}")
    return 0 if verify_report["result"] == "PASS" else 1


def _run_review(args: argparse.Namespace, raw_argv: list[str]) -> int:
    run_id = str(args.run_id or "").strip() or "cloud-doc-backport-local"
    out_dir = Path(args.out) if args.out else _default_out_dir(run_id)
    command = ["tools/cloud_doc_backport.py", *raw_argv]
    try:
        source_path = _resolve_source_path(args.source_path, label="source target")
        _validate_apply_source(source_path, kind="review")
        baseline_text = _read_text(source_path)
        fetched_text = fetch_doc_text(args.doc_url, lark_cli=args.lark_cli)
        section_title = str(args.section_heading or "").strip() or None
        section_inferred_from = None
        if section_title is None and not args.no_auto_section:
            section_title, section_inferred_from = _auto_section_for_source(source_path, baseline_text)
        diff_report = build_report(
            run_id=run_id,
            doc_type="review",
            doc_url=args.doc_url,
            baseline_path=_display_path(source_path),
            fetched_text=fetched_text,
            baseline_text=baseline_text,
            command=command,
            source_path=_display_path(source_path),
            section_title=section_title,
            section_inferred_from=section_inferred_from,
            require_section_match=bool(args.section_heading),
            value_index=_value_index_from_args(args),
            family_index=_family_index_from_args(args),
        )
        _refuse_unsafe_review_apply(
            diff_report,
            write=bool(args.write),
            allow_rst_baseline=getattr(args, "allow_rst_baseline", False),
        )
        output_paths = {f"diff_{key}": value for key, value in write_reports(diff_report, out_dir).items()}
        apply_report: dict[str, Any] | None = None
        verify_report: dict[str, Any] | None = None
        if diff_report["summary"]["total_deltas"]:
            apply_report = build_review_apply_report(
                diff_report,
                source_path=source_path,
                write=bool(args.write),
                command=command,
            )
            output_paths.update(
                {f"apply_{key}": value for key, value in write_apply_report(apply_report, out_dir).items()}
            )
            if args.write:
                verify_report = build_review_verify_report(
                    diff_report,
                    source_path=source_path,
                    command=command,
                )
                output_paths.update(
                    {f"verify_{key}": value for key, value in write_verify_report(verify_report, out_dir).items()}
                )
        suggestions_report = build_source_table_suggestions_report(
            diff_report=diff_report,
            verify_report=verify_report,
            command=command,
        )
        output_paths.update(
            {
                f"source_table_suggestions_{key}": value
                for key, value in write_source_table_suggestions_report(suggestions_report, out_dir).items()
            }
        )
        proposal_report = build_template_sync_proposal_report(diff_report=diff_report, command=command)
        output_paths.update(
            {
                f"template_sync_proposal_{key}": value
                for key, value in write_template_sync_proposal_report(proposal_report, out_dir).items()
            }
        )
        sidecar_index = load_sidecar_index(Path(args.data_root)) if getattr(args, "data_root", None) else None
        change_request_report = build_change_request_report(diff_report, sidecar_index=sidecar_index)
        output_paths["source_table_change_request_json"] = write_change_request_report(
            change_request_report, out_dir
        )
        run_report = build_review_run_report(
            diff_report,
            apply_report=apply_report,
            verify_report=verify_report,
            write=bool(args.write),
            output_paths=output_paths,
            command=command,
        )
    except (OSError, RuntimeError) as exc:
        print(f"cloud-doc-backport: {exc}", file=sys.stderr)
        return 2

    run_written = write_review_run_report(run_report, out_dir)
    output_paths.update({f"run_{key}": value for key, value in run_written.items()})
    for label, path in sorted(output_paths.items()):
        print(f"WROTE {path}")
    if args.write and apply_report and apply_report["summary"]["changed"]:
        print(f"UPDATED {apply_report['source_target']['path']}")
    return 1 if run_report["result"] == "FAIL" else 0


def _run_open_pr(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root) if args.repo_root else get_paths().root
    try:
        result = open_backport_pr_from_manifest(
            manifest_path=Path(args.manifest),
            repo_root=repo_root,
            branch_name=str(args.branch or "").strip() or None,
            base_ref=str(args.base or "main").strip() or "main",
            git_bin=str(args.git_bin or "git").strip() or "git",
            gh_bin=str(args.gh_bin or "gh").strip() or "gh",
        )
    except (OSError, RuntimeError) as exc:
        print(f"cloud-doc-backport: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"PR {result['pr_url']}")
        print(f"BRANCH {result['branch']}")
        print(f"COMMIT {result['commit']}")
    return 0


def _parse_table_bindings(specs: list[str]) -> dict[str, tuple[str, str]]:
    """Parse ``--table-binding 'TABLE=BASE:TABLE_ID'`` specs into ``{table: (base, table_id)}``."""
    bindings: dict[str, tuple[str, str]] = {}
    for spec in specs:
        name, sep, rest = str(spec).partition("=")
        base, sep2, table_id = rest.partition(":")
        name, base, table_id = name.strip(), base.strip(), table_id.strip()
        if not (name and sep and sep2 and base and table_id):
            raise RuntimeError(f"--table-binding must look like TABLE=BASE:TABLE_ID, got: {spec!r}")
        bindings[name] = (base, table_id)
    return bindings


def _source_table_transport(bindings: dict[str, tuple[str, str]], *, lark_cli: str, identity: str) -> Any:
    """Build a live F6 transport whose ``binding_for`` resolves only the given tables.

    An unmapped table raises, which ``apply_change_requests`` isolates per-request
    (status ``error``) — so e.g. a derived ``Localized_Copy`` table is skipped safely.
    """
    from tools.feishu_record_transport import SourceTableLarkTransport
    from tools.sync_data import LarkCliSource

    def binding_for(table: str) -> tuple[str, str]:
        try:
            return bindings[table]
        except KeyError:
            raise RuntimeError(f"no writable --table-binding for table {table!r}") from None

    source = LarkCliSource(cli_bin=lark_cli, identity=identity)
    return SourceTableLarkTransport(source=source, binding_for=binding_for)


def _tm_transport(spec: str, *, lark_cli: str, identity: str) -> Any:
    """Build a live Translation_Memory transport from a ``BASE:TABLE_ID`` binding."""
    from tools.feishu_record_transport import TranslationMemoryLarkTransport
    from tools.sync_data import LarkCliSource

    base, sep, table_id = str(spec or "").partition(":")
    base, table_id = base.strip(), table_id.strip()
    if not (sep and base and table_id):
        raise RuntimeError(f"--tm-binding must look like BASE:TABLE_ID, got: {spec!r}")
    source = LarkCliSource(cli_bin=lark_cli, identity=identity)
    return TranslationMemoryLarkTransport(source=source, base_token=base, table_id=table_id)


def _run_apply_source_table(args: argparse.Namespace, raw_argv: list[str]) -> int:
    try:
        report_path = _resolve_source_path(args.report, label="change-request report")
        change_requests, run_id = load_change_requests(report_path)
        approved = {h for h in (args.approve or []) if h}
        transport = None
        if args.write:
            bindings = _parse_table_bindings(args.table_binding or [])
            if not bindings:
                raise RuntimeError("--write requires at least one --table-binding TABLE=BASE:TABLE_ID")
            transport = _source_table_transport(bindings, lark_cli=args.lark_cli, identity=args.identity)
        apply_result = apply_change_requests(
            change_requests,
            approved_hashes=approved,
            transport=transport,
            write=bool(args.write),
        )
        # Translation copy edits abstain at the source boundary; their home is the
        # Translation_Memory. Apply approved ones there, gated SEPARATELY (--tm-write
        # + --tm-binding) since TM is the widest-blast-radius write.
        translation_suggestions = load_translation_suggestions(report_path)
        tm_transport = None
        if args.tm_write:
            if not args.tm_binding:
                raise RuntimeError("--tm-write requires --tm-binding BASE:TABLE_ID")
            tm_transport = _tm_transport(args.tm_binding, lark_cli=args.lark_cli, identity=args.identity)
        tm_apply_result = apply_translation_suggestions(
            translation_suggestions,
            approved_hashes=approved,
            transport=tm_transport,
            write=bool(args.tm_write),
        )
    except (OSError, RuntimeError) as exc:
        print(f"cloud-doc-backport: {exc}", file=sys.stderr)
        return 2
    report = {
        **apply_result,
        "run_id": run_id,
        "approved_count": len(approved),
        "translation_apply": tm_apply_result,
        "command": ["tools/cloud_doc_backport.py", *raw_argv],
    }
    out_dir = Path(args.out) if args.out else report_path.parent
    written = write_source_table_apply_report(report, out_dir)
    print(f"WROTE {written['json']}")
    print(f"WROTE {written['markdown']}")
    summary = report.get("summary") or {}
    tm_summary = tm_apply_result.get("summary") or {}
    print(
        f"APPLY plan: apply {summary.get('apply', 0)} skip {summary.get('skip', 0)} "
        f"| written {summary.get('written', 0)} verify_failed {summary.get('verify_failed', 0)} "
        f"error {summary.get('error', 0)} ({'WRITE' if report.get('external_write') else 'dry-run'})"
    )
    print(
        f"TM plan: apply {tm_summary.get('apply', 0)} skip {tm_summary.get('skip', 0)} "
        f"| written {tm_summary.get('written', 0)} already {tm_summary.get('already', 0)} "
        f"verify_failed {tm_summary.get('verify_failed', 0)} error {tm_summary.get('error', 0)} "
        f"({'WRITE' if tm_apply_result.get('external_write') else 'dry-run'})"
    )
    wrote_with_failures = (report.get("external_write") and (summary.get("verify_failed") or summary.get("error"))) or (
        tm_apply_result.get("external_write") and (tm_summary.get("verify_failed") or tm_summary.get("error"))
    )
    return 1 if wrote_with_failures else 0


def _fetch_build_table_records(lark_cli: str, identity: str) -> list[dict[str, Any]]:
    """Fetch the Document_link build table (文档构建表) records via lark-cli."""
    import os

    from tools.sync_data import LarkCliSource

    base = os.environ.get("FEISHU_PHASE2_BASE_TOKEN", "").strip()
    table = os.environ.get("FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID", "").strip()
    view = os.environ.get("FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID", "").strip() or None
    if not base or not table:
        raise RuntimeError("FEISHU_PHASE2_BASE_TOKEN + FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID are required")
    source = LarkCliSource(cli_bin=lark_cli, identity=identity)
    return source.fetch_records_with_ids(base_token=base, table_id=table, view_id=view)


def _default_worktrees_root() -> Path:
    import os

    env = os.environ.get("AUTO_MANUAL_REVIEW_WORKTREES_ROOT", "").strip()
    return Path(env) if env else (get_paths().root.parent / "review-worktrees")


def _run_resolve_review_branch(args: argparse.Namespace) -> int:
    try:
        result = match_review_branch(args.cloud_doc, _fetch_build_table_records(args.lark_cli, args.identity))
    except (OSError, RuntimeError) as exc:
        print(f"cloud-doc-backport: {exc}", file=sys.stderr)
        return 2
    if result is None:
        print(json.dumps({"resolved": False, "cloud_doc": args.cloud_doc}, ensure_ascii=False))
        return 1
    print(json.dumps({"resolved": True, **result}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _run_sync_review_worktrees(args: argparse.Namespace) -> int:
    worktrees_root = Path(args.worktrees_root) if args.worktrees_root else _default_worktrees_root()
    try:
        branches = list_in_review_branches(_fetch_build_table_records(args.lark_cli, args.identity))
    except (OSError, RuntimeError) as exc:
        print(f"cloud-doc-backport: {exc}", file=sys.stderr)
        return 2
    results: list[dict[str, Any]] = []
    for branch in branches:
        try:
            path = ensure_review_worktree(
                branch["git_ref"],
                worktrees_root=worktrees_root,
                repo_root=get_paths().root,
                remote=args.remote,
                git_bin=args.git_bin,
                sparse_paths=None if args.full_checkout else [branch["review_dir"]],
            )
            results.append({**branch, "worktree": path})
            print(f"WORKTREE {branch['git_ref']} -> {path}")
        except (OSError, RuntimeError) as exc:
            results.append({**branch, "error": str(exc)})
            print(f"cloud-doc-backport: worktree for {branch['git_ref']} failed: {exc}", file=sys.stderr)
    print(json.dumps({"in_review": len(branches), "ensured": sum(1 for r in results if "worktree" in r)}, ensure_ascii=False))
    return 0 if branches and all("worktree" in r for r in results) else (0 if not branches else 1)


def _diff_delta_count(page_out: Path) -> int:
    """Real section-matched delta count from a run-review diff report.

    Counts deltas ONLY when the page's section was actually located in the cloud
    doc (``section_selection.applied``). A page whose section is absent falls back
    to a whole-document diff (every block differs) — a false positive in a
    whole-doc backport — so it is reported as 0.
    """
    try:
        payload = json.loads((page_out / "cloud_doc_backport_report.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0
    if not (payload.get("section_selection") or {}).get("applied"):
        return 0
    return int((payload.get("summary") or {}).get("total_deltas") or 0)


def _backport_pr_branch(git_ref: str, run_id: str) -> str:
    """Name of the sub-branch that carries backport edits as a PR into the review branch."""
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", f"{git_ref}-{run_id}").strip("-")[:80] or "edits"
    return f"backport/{safe}"


_KNOWN_VALUE_LANGS = ("pt-BR", "en", "fr", "es", "de", "it", "uk", "ja", "zh", "ko", "nl", "pl", "sv")


def _lang_from_doc_name(doc_name: str | None) -> str:
    """Best-effort value-column lang from a doc name, e.g. ``manual_je1000f_eu_en_0.8`` -> ``en``."""
    for part in re.split(r"[_\s]+", str(doc_name or "").strip()):
        if part in _KNOWN_VALUE_LANGS:
            return part
    return ""


def _open_backport_pr(
    *, worktree: str, git_ref: str, run_id: str, changed_rels: list[str], git_bin: str, remote: str
) -> tuple[bool, str]:
    """Put the changed ``_review`` pages on a ``backport/`` sub-branch and open a DRAFT
    PR whose base IS the review branch, so the operator verifies before anything lands
    on the review branch. Returns ``(pushed, pr_url)``. The worktree is on the review
    branch on entry and is restored to it on exit."""
    pr_branch = _backport_pr_branch(git_ref, run_id)
    _run_pr_command([git_bin, "switch", "-C", pr_branch], root=Path(worktree))
    try:
        for rel in changed_rels:
            _run_pr_command([git_bin, "add", rel], root=Path(worktree))
        if not _run_pr_command([git_bin, "status", "--porcelain"], root=Path(worktree)).strip():
            return False, ""
        _run_pr_command(
            [git_bin, "commit", "-m", f"backport: review edits for {git_ref} ({run_id})"],
            root=Path(worktree),
        )
        _run_pr_command(
            [git_bin, "push", "--force-with-lease", "-u", remote, pr_branch], root=Path(worktree)
        )
        body = (
            f"Backport of reviewer cloud-doc edits (review-prose / Class R), targeting "
            f"the review branch `{git_ref}`.\n\nChanged pages:\n"
            + "\n".join(f"- `{rel}`" for rel in changed_rels)
            + "\n\nVerify, then merge into the review branch."
        )
        pr_url = _run_pr_command(
            [
                "gh", "pr", "create", "--base", git_ref, "--head", pr_branch,
                "--draft", "--title", f"backport: review edits for {git_ref} ({run_id})",
                "--body", body,
            ],
            root=Path(worktree),
        ).splitlines()[-1].strip()
        return True, pr_url
    finally:
        _run_pr_command([git_bin, "switch", git_ref], root=Path(worktree))


def _run_review_branch(args: argparse.Namespace) -> int:
    worktrees_root = Path(args.worktrees_root) if args.worktrees_root else _default_worktrees_root()
    try:
        records = _fetch_build_table_records(args.lark_cli, args.identity)
        doc_name = (getattr(args, "doc_name", None) or "").strip()
        # Resolve by the doc NAME when given (robust for a 副本 whose URL is not in
        # the build table); else by the cloud-doc URL. The fetch always uses --cloud-doc.
        resolved = match_review_branch_by_name(doc_name, records) if doc_name else match_review_branch(args.cloud_doc, records)
        if resolved is None:
            raise RuntimeError(f"no review branch found for cloud-doc {doc_name or args.cloud_doc}")
        git_ref = resolved["git_ref"]
        review_dir = resolved["review_dir"]
        worktree = ensure_review_worktree(
            git_ref,
            worktrees_root=worktrees_root,
            repo_root=get_paths().root,
            remote=args.remote,
            git_bin=args.git_bin,
            sparse_paths=None if args.full_checkout else [review_dir],
        )
        doc_tok = doc_token(args.cloud_doc)
        if args.seed:
            # Store the current cloud-doc as the render baseline (approach C). Used
            # to declare "the current state is already reviewed"; subsequent backports
            # diff against this. Refuses to clobber an existing baseline unless --reseed.
            if not doc_tok:
                raise RuntimeError("--seed needs a resolvable cloud-doc token in --cloud-doc")
            if load_baseline(worktree, review_dir, doc_tok) is not None and not args.reseed:
                raise RuntimeError("a render baseline already exists for this doc; pass --reseed to overwrite")
            baseline_rel = store_baseline(worktree, review_dir, doc_tok, fetch_doc_text(args.cloud_doc, lark_cli=args.lark_cli))
            pushed = False
            if args.push:
                _run_pr_command([args.git_bin, "add", baseline_rel], root=Path(worktree))
                if _run_pr_command([args.git_bin, "status", "--porcelain", baseline_rel], root=Path(worktree)).strip():
                    _run_pr_command([args.git_bin, "commit", "-m", f"backport: seed render baseline for {git_ref}"], root=Path(worktree))
                    _run_pr_command([args.git_bin, "push"], root=Path(worktree))
                    pushed = True
            print(json.dumps(
                {"seeded": True, "git_ref": git_ref, "baseline": baseline_rel, "worktree": worktree, "pushed": pushed},
                ensure_ascii=False, sort_keys=True,
            ))
            return 0
        # Approach C: diff the cloud-doc against a render baseline (render-vs-render →
        # only the reviewer's real edits) instead of the RST-source-vs-rendered per-page
        # diff. Whole-doc only — the baseline is the whole doc, so --page falls through
        # to the legacy per-page path. Two baseline sources, in order of preference:
        #   1. the 基线文档 doc recorded on the build-table row (a frozen copy made at
        #      build time) — fetched and diffed (the copy-doc baseline model);
        #   2. the on-branch .backport/<doc-token>.baseline.md file (the --seed model).
        baseline_text = None
        baseline_doc_url = (resolved.get("baseline_doc_url") or "").strip()
        if baseline_doc_url and not args.page:
            baseline_text = fetch_doc_text(baseline_doc_url, lark_cli=args.lark_cli)
        elif doc_tok and not args.page:
            baseline_text = load_baseline(worktree, review_dir, doc_tok)
        if baseline_text is not None:
            return _run_review_branch_baseline(
                args, resolved=resolved, worktree=worktree,
                review_dir=review_dir, doc_tok=doc_tok, baseline_text=baseline_text,
            )
        # Safety guard: a whole-doc run with NO render baseline falls back to the
        # per-page RST-source-vs-rendered diff, which over-reports and whose --write
        # would splatter rendered text across many RST pages (corrupting `.. raw::
        # latex` / line-blocks). Refuse the mass write — seed a baseline so the diff
        # is clean (run-review-branch --seed), or target one page with --page.
        if args.write and not args.page:
            raise RuntimeError(
                "refusing whole-doc --write without a render baseline: the per-page "
                "RST-vs-rendered diff over-reports and writing it corrupts the RST "
                "source. Seed a baseline first (run-review-branch --seed) for a clean "
                "diff, or pass --page <file> to write one targeted page."
            )
        # Pages to backport. With --page: that one. Without: every
        # docs/_review/<model>/<region>/page/*.rst (whole-doc diff — find which pages
        # the cloud-doc changed). The source path is always DERIVED from the resolved
        # review dir (template guard), so a backport can only ever write docs/_review.
        if args.page:
            source_rels = [derive_review_source_rel(review_dir, args.page)]
        else:
            page_dir = Path(worktree) / review_dir / "page"
            if not page_dir.is_dir():
                raise RuntimeError(f"no page directory on branch {git_ref}: {review_dir}/page")
            source_rels = [f"{review_dir}/page/{path.name}" for path in sorted(page_dir.glob("*.rst"))]
            if not source_rels:
                raise RuntimeError(f"no .rst pages under {review_dir}/page on branch {git_ref}")
        run_id = str(args.run_id or "").strip() or "cloud-doc-backport-branch"
        out_dir = Path(args.out) if args.out else _default_out_dir(run_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        # Fetch the cloud-doc ONCE; diff every page against this local fixture so a
        # whole-doc backport does not re-fetch per page.
        fixture = out_dir / "cloud_doc_fetched.md"
        fixture.write_text(fetch_doc_text(args.cloud_doc, lark_cli=args.lark_cli), encoding="utf-8")
    except (OSError, RuntimeError) as exc:
        print(f"cloud-doc-backport: {exc}", file=sys.stderr)
        return 2
    print(f"BRANCH {git_ref}  WORKTREE {worktree}  PAGES {len(source_rels)}")
    changed_rels: list[str] = []
    failed = False
    for source_rel in source_rels:
        source_abs = Path(worktree) / source_rel
        if not source_abs.is_file():
            continue
        page_out = out_dir / Path(source_rel).stem
        review_cmd = [
            sys.executable, str(Path(__file__).resolve()), "run-review",
            "--doc-url", str(fixture), "--source-path", str(source_abs),
            "--run-id", f"{run_id}-{Path(source_rel).stem}", "--out", str(page_out), "--lark-cli", args.lark_cli,
            # Internal per-page worker: the source path is DERIVED from the resolved
            # review dir and the whole-doc no-baseline --write is already refused above
            # (#417), so the RST-baseline guard would be redundant here — bypass it.
            "--allow-rst-baseline",
        ]
        if args.write:
            review_cmd.append("--write")
        proc = subprocess.run(review_cmd, cwd=str(get_paths().root), capture_output=True, text=True)
        if proc.returncode not in (0, 1):  # run-review returns 1 only on a FAIL residual result
            failed = True
            print(f"  ERROR {source_rel} (rc {proc.returncode})", file=sys.stderr)
            continue
        deltas = _diff_delta_count(page_out)
        if deltas > 0:
            changed_rels.append(source_rel)
            print(f"  CHANGED {source_rel}  deltas={deltas}")
    pushed = False
    backport_pr_url = ""
    if args.write and args.push and changed_rels:
        try:
            pushed, backport_pr_url = _open_backport_pr(
                worktree=worktree, git_ref=git_ref, run_id=run_id,
                changed_rels=changed_rels, git_bin=args.git_bin, remote=args.remote,
            )
        except (OSError, RuntimeError) as exc:
            print(f"cloud-doc-backport: backport PR into {git_ref} failed: {exc}", file=sys.stderr)
            return 2
    print(json.dumps(
        {"git_ref": git_ref, "worktree": worktree, "pages": len(source_rels),
         "changed": changed_rels, "wrote": bool(args.write), "pushed": pushed,
         "backport_pr_url": backport_pr_url, "review_branch_pr_url": resolved.get("pr_url")},
        ensure_ascii=False, sort_keys=True,
    ))
    return 1 if failed else 0


def _run_review_branch_baseline(
    args: argparse.Namespace,
    *,
    resolved: dict[str, Any],
    worktree: str,
    review_dir: str,
    doc_tok: str,
    baseline_text: str,
) -> int:
    """Approach C phase 2: diff the cloud-doc against the stored render baseline.

    Both sides are the Feishu fetch of the doc (the baseline is the render that was
    pushed / last backported), so the diff is render-vs-render and surfaces only the
    reviewer's real edits — not the RST-source-vs-rendered noise of the per-page path.

    The clean deltas are classified (phase 3): the F2 value-index marks a delta whose
    old text matches a source value as ``source_table_suggestion`` (Class D → write
    back to the source table / TM via the approval-gated ``apply-source-table``, NOT
    the RST), the F3 family-index flags shared-template spans, and the rest are
    ``repo_review_text`` (Class R → the ``_review`` RST). With ``--write`` the Class R
    deltas are applied to the matching ``_review`` page via the guarded apply (only
    unique, safe matches) and ``--push`` opens a PR INTO the review branch; Class D is
    never written to the RST. We never advance the baseline cursor here — that would
    bury un-applied edits below it (design §6).
    """
    git_ref = resolved["git_ref"]
    run_id = str(args.run_id or "").strip() or "cloud-doc-backport-branch"
    out_dir = Path(args.out) if args.out else _default_out_dir(run_id)
    # F2 value-index: derive the value-column lang from --lang, else the doc name.
    if not getattr(args, "lang", None):
        args.lang = _lang_from_doc_name(getattr(args, "doc_name", "") or "")
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        c_now = fetch_doc_text(args.cloud_doc, lark_cli=args.lark_cli)
        baseline_rel = baseline_rel_path(review_dir, doc_tok)
        report = build_report(
            run_id=run_id,
            doc_type="review",
            doc_url=args.cloud_doc,
            baseline_path=Path(baseline_rel),
            fetched_text=c_now,
            baseline_text=baseline_text,
            command=["tools/cloud_doc_backport.py", "run-review-branch", "--baseline-diff"],
            source_path=None,
            section_title=None,
            section_inferred_from=None,
            require_section_match=False,
            value_index=_value_index_from_args(args),
            family_index=_family_index_from_args(args),
        )
    except (OSError, RuntimeError) as exc:
        print(f"cloud-doc-backport: {exc}", file=sys.stderr)
        return 2
    written = write_reports(report, out_dir)
    deltas = report["summary"]["total_deltas"]
    route_classes = report["summary"].get("route_classes") or {}
    source_bound = route_classes.get("source_table_suggestion", 0)
    review_bound = route_classes.get("repo_review_text", 0)
    print(f"BRANCH {git_ref}  WORKTREE {worktree}  BASELINE-DIFF deltas={deltas}  routes={json.dumps(route_classes, ensure_ascii=False)}")
    print(f"WROTE {written['json']}")
    print(f"WROTE {written['markdown']}")
    # Class D (source-bound) goes to the source table / TM (F6), NOT the RST — the diff
    # report IS the apply-source-table input.
    if source_bound:
        print(
            f"ROUTE: {source_bound} source-bound (Class D) delta(s) -> run "
            f"`apply-source-table --report {written['json']}` (approval-gated F6/TM), NOT the _review RST."
        )
    # Class R (review prose): apply the CLEAN deltas to the matching _review page via
    # the guarded apply (only unique, safe matches; ambiguous ones are skipped), then
    # open a PR INTO the review branch. This is the clean write path — it never touches
    # Class D deltas and never writes the per-page RST-vs-rendered garbage.
    changed_rels: list[str] = []
    if args.write and review_bound:
        page_dir = Path(worktree) / review_dir / "page"
        for page in sorted(page_dir.glob("*.rst")):
            apply_rep = build_review_apply_report(
                report, source_path=page, write=True,
                command=["tools/cloud_doc_backport.py", "run-review-branch", "--baseline-apply"],
            )
            if apply_rep["summary"].get("changed"):
                changed_rels.append(f"{review_dir}/page/{page.name}")
                print(f"  APPLIED (Class R) {page.name}")
        if not changed_rels:
            print("NOTE: no review-prose delta matched a _review page uniquely (nothing written; handle manually if needed).")
    pushed = False
    backport_pr_url = ""
    if args.write and args.push and changed_rels:
        try:
            pushed, backport_pr_url = _open_backport_pr(
                worktree=worktree, git_ref=git_ref, run_id=run_id,
                changed_rels=changed_rels, git_bin=args.git_bin, remote=args.remote,
            )
        except (OSError, RuntimeError) as exc:
            print(f"cloud-doc-backport: backport PR into {git_ref} failed: {exc}", file=sys.stderr)
            return 2
    print(json.dumps(
        {"git_ref": git_ref, "worktree": worktree, "mode": "baseline-diff",
         "baseline": baseline_rel, "deltas": deltas, "result": report["result"],
         "route_classes": route_classes, "report": str(written["json"]),
         "source_table_report": str(written["json"]), "changed": changed_rels,
         "wrote": bool(args.write), "pushed": pushed, "backport_pr_url": backport_pr_url,
         "review_branch_pr_url": resolved.get("pr_url")},
        ensure_ascii=False, sort_keys=True,
    ))
    return 0


def _value_index_from_args(args: argparse.Namespace) -> dict[str, Any] | None:
    """Build the token/copy value index when --lang and --data-root are given (F2)."""
    lang = getattr(args, "lang", None)
    data_root = getattr(args, "data_root", None)
    if not lang or not data_root:
        return None
    return build_value_index(Path(data_root), str(lang))


def _family_index_from_args(args: argparse.Namespace) -> dict[str, Any] | None:
    """Build the family-scope index from --sibling source paths (F3)."""
    siblings = getattr(args, "sibling", None) or []
    if not siblings:
        return None
    return build_family_index([Path(path) for path in siblings])


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    args = _parse_args(raw_argv)
    if args.command == "diff":
        return _run_diff(args, raw_argv)
    if args.command == "apply-template":
        return _run_apply_template(args, raw_argv)
    if args.command == "apply-review":
        return _run_apply_review(args, raw_argv)
    if args.command == "verify-review":
        return _run_verify_review(args, raw_argv)
    if args.command == "run-review":
        return _run_review(args, raw_argv)
    if args.command == "open-pr":
        return _run_open_pr(args)
    if args.command == "apply-source-table":
        return _run_apply_source_table(args, raw_argv)
    if args.command == "resolve-review-branch":
        return _run_resolve_review_branch(args)
    if args.command == "run-review-branch":
        return _run_review_branch(args)
    if args.command == "sync-review-worktrees":
        return _run_sync_review_worktrees(args)
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
