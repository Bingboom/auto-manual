#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guarded review/template apply (Class R write-back) for cloud-doc backport.

D2-6. The literal-first + block-fallback RST rewrite + guards + apply-report
builders. Imports the model + shared util; re-exported by cloud_doc_backport.
"""
from __future__ import annotations

import re
import shlex
import sys
import unicodedata
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.cloud_doc_backport_model import (  # noqa: E402
    Block,
    _HEADING_RE,
    _RST_HEADING_UNDERLINE_RE,
    _display_path,
    _normalize_inline,
    _read_text,
    parse_blocks,
)
from tools.cloud_doc_backport_util import (  # noqa: E402
    APPLY_SCHEMA_VERSION,
    REPORT_SCHEMA_VERSION,
    _counter_dict,
    _git_ref,
    _resolve_source_path,
    _utc_now,
    _validate_apply_source,
)


_REVIEW_MARKUP_ROLE_RE = re.compile(r":[\w][\w+.-]*:")

def _rst_display_width(text: str) -> int:
    """reST/docutils measures heading underlines in display COLUMNS, not characters
    (`添加设备` is 4 chars but 8 columns). Wide/Fullwidth code points count as 2."""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)

def _heading_text_key(text: str) -> str:
    """Normalized heading TITLE (markdown ``#`` prefix stripped), level-agnostic.

    A reST source heading parses (via ``_preprocessed_lines``) to ``# title`` while the
    cloud-doc delta carries ``## title`` — matching on the title alone makes the level
    difference irrelevant (the reST source level stays authoritative)."""
    match = _HEADING_RE.match((text or "").strip())
    return _normalize_inline(match.group(2)) if match else _normalize_inline(text or "")

def _match_review_block(
    source_text: str, delta: dict[str, Any]
) -> tuple[Block | None, int | None, str | None]:
    """Find the UNIQUE source block a review delta refers to.

    Returns ``(block, next_block_line_no, None)`` on a unique hit (the next block's 1-based
    line_no bounds the span, or None at EOF), else ``(None, None, abstain_reason)``."""
    kind = str(((delta.get("location") or {}).get("kind")) or "")
    blocks = parse_blocks(source_text)
    if kind == "heading":
        want = _heading_text_key(str(delta.get("old_normalized") or ""))
        candidates = [b for b in blocks if b.kind == "heading" and _heading_text_key(b.text) == want]
        label = "review heading title"
    else:
        want = _normalize_inline(str(delta.get("old_normalized") or ""))
        candidates = [b for b in blocks if b.kind == kind and b.normalized == want]
        label = "old_normalized"
    if not want:
        return None, None, "delta old_normalized is empty"
    if len(candidates) == 1:
        block = candidates[0]
        idx = blocks.index(block)
        next_line_no = blocks[idx + 1].line_no if idx + 1 < len(blocks) else None
        return block, next_line_no, None
    if not candidates:
        return None, None, f"no review block matched {label}"
    return None, None, f"{label} matched {len(candidates)} review blocks ambiguously"

def _review_block_span(
    source_lines: list[str], block: Block, next_line_no: int | None
) -> tuple[int, int]:
    """Half-open [start, end) 0-based source-line range the block occupies.

    A reST heading spans the title line + its underline; a paragraph runs to the next
    block's start (or EOF), trailing blank lines trimmed. ``block.line_no`` is 1-based."""
    start = max(0, block.line_no - 1)
    if block.kind == "heading":
        nxt = start + 1
        if nxt < len(source_lines) and _RST_HEADING_UNDERLINE_RE.match(source_lines[nxt].strip()):
            return start, nxt + 1
        return start, start + 1
    end = (next_line_no - 1) if next_line_no else len(source_lines)
    end = min(max(end, start + 1), len(source_lines))
    while end > start + 1 and not source_lines[end - 1].strip():
        end -= 1
    return start, end

def _review_block_is_plain(span_text: str, block: Block) -> bool:
    """A block is loss-free rewritable iff its RAW source carries no reST markup that
    ``_normalize_inline`` discarded (so a normalized-level old->new is a faithful source
    rewrite). ``_normalize_inline`` does NOT strip backticks / ``:roles:`` / ``|subs|``, so
    those are guarded explicitly. For a heading only the title text must be plain (the
    underline is structural)."""
    if block.kind == "heading":
        first = span_text.splitlines()[0].strip() if span_text.strip() else ""
        return "**" not in first and "`" not in first and not _REVIEW_MARKUP_ROLE_RE.search(first)
    collapsed = re.sub(r"\s+", " ", span_text).strip()
    return (
        collapsed == block.normalized
        and "**" not in span_text
        and "__" not in span_text
        and "`" not in span_text
        and "|" not in span_text
        and not _REVIEW_MARKUP_ROLE_RE.search(span_text)
        and not span_text.lstrip().startswith(".. ")
        and "<" not in span_text
        and span_text[:1] not in (" ", "\t")
    )

def _minimal_diff_rewrite(body: str, old_norm: str, new_norm: str) -> str | None:
    """Apply only the segment the reviewer changed (``old_norm`` → ``new_norm``) to the
    SOURCE ``body``, so chars the normalize would rewrite (CJK quotes, ``**``, images)
    OUTSIDE the changed segment are preserved. Deterministic: a concrete changed segment
    must be plain (appears verbatim) and occur exactly once in the source, or be a pure
    head/tail insertion; otherwise None (abstain). This is what lets a reviewer's "append
    a few words" edit land on a paragraph that happens to contain CJK quotes."""
    # common prefix / suffix on the NORMALIZED strings -> the minimal changed segment
    p = 0
    while p < len(old_norm) and p < len(new_norm) and old_norm[p] == new_norm[p]:
        p += 1
    s = 0
    while s < (len(old_norm) - p) and s < (len(new_norm) - p) and old_norm[-1 - s] == new_norm[-1 - s]:
        s += 1
    mid_old = old_norm[p : len(old_norm) - s]
    mid_new = new_norm[p : len(new_norm) - s]
    # never write a normalize placeholder back into the source
    if "![image]" in mid_new or "<img>" in mid_new:
        return None
    if mid_old:
        # a concrete changed/deleted segment: it must be plain (no normalize-rewritten char,
        # so it appears verbatim in the source) AND occur exactly once -> loss-free + unique.
        if body.count(mid_old) != 1:
            return None
        return body.replace(mid_old, mid_new, 1)
    # pure insertion (old is a prefix or a suffix of new)
    if not mid_new:
        return None
    if s == 0:
        return body + mid_new  # appended at the tail
    if p == 0:
        return mid_new + body  # inserted at the head
    return None  # wedged between two kept segments -> abstain (can't place it deterministically)

def _rewrite_review_block(
    source_text: str, block: Block, delta: dict[str, Any], start: int, end: int
) -> str | None:
    """Return the full source text with the block rewritten per the delta, or None to
    abstain. Headings rewrite the title + a display-width underline (the title must be
    plain); paragraphs apply a minimal-diff rewrite that preserves untouched source chars;
    ``list_item`` is out of scope in v1."""
    if block.kind == "list_item":
        return None
    lines = source_text.splitlines(keepends=True)
    if start >= len(lines):
        return None
    newline = "\r\n" if lines[start].endswith("\r\n") else "\n"
    change_type = str(delta.get("change_type") or "")
    span_text = "".join(lines[start:end])

    if block.kind == "heading":
        # never delete a heading via prose; a marked-up title is not loss-free rewritable
        if change_type == "delete" or not _review_block_is_plain(span_text, block):
            return None
        new_title = _heading_text_key(str(delta.get("new_normalized") or ""))
        old_title = _heading_text_key(str(delta.get("old_normalized") or ""))
        if not new_title:
            return None
        underline = lines[start + 1].strip() if (end - start) >= 2 and start + 1 < len(lines) else ""
        match = _RST_HEADING_UNDERLINE_RE.match(underline)
        char = match.group(1) if match else "="
        width = max(_rst_display_width(new_title), _rst_display_width(old_title))
        return "".join(lines[:start] + [f"{new_title}{newline}", f"{char * width}{newline}"] + lines[end:])

    # paragraph: delete removes the span; otherwise minimal-diff so untouched chars survive
    if change_type == "delete":
        tail = end
        if tail < len(lines) and not lines[tail].strip():
            tail += 1  # consume one trailing blank line
        return "".join(lines[:start] + lines[tail:])
    body = span_text.rstrip("\r\n")
    trail = span_text[len(body):] or newline
    new_body = _minimal_diff_rewrite(
        body, str(delta.get("old_normalized") or ""), str(delta.get("new_normalized") or "")
    )
    if new_body is None or new_body == body:
        return None
    return "".join(lines[:start] + [new_body + trail] + lines[end:])

def _apply_review_block_operation(
    *, delta: dict[str, Any], current_text: str, write: bool, base_operation: dict[str, Any]
) -> tuple[dict[str, Any], str]:
    """Deterministic Class R apply for one delta: block match + plain guard + rewrite."""
    block, next_line_no, reason = _match_review_block(current_text, delta)
    if block is None:
        return {**base_operation, "status": "skipped", "reason": reason, "matches": 0}, current_text
    lines = current_text.splitlines(keepends=True)
    start, end = _review_block_span(lines, block, next_line_no)
    rewritten = _rewrite_review_block(current_text, block, delta, start, end)
    if rewritten is None or rewritten == current_text:
        return (
            {
                **base_operation,
                "status": "skipped",
                "reason": "review block edit not loss-free rewritable (markup / ambiguous / list_item)",
                "matches": 1,
            },
            current_text,
        )
    verb = "deletion" if str(delta.get("change_type")) == "delete" else "replacement"
    if write:
        return {**base_operation, "status": "applied", "reason": f"unique repo_review_text {verb}", "matches": 1}, rewritten
    return {**base_operation, "status": "planned", "reason": f"unique repo_review_text {verb}", "matches": 1}, current_text

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
        # Class R: the literal (markup-preserving) match failed — the reviewer's edit is a
        # reST heading (rendered `## X` vs source `X\n===`) or a soft-wrapped / role-bearing
        # paragraph that never byte-matches. Fall back to a deterministic block-level match +
        # line_no-anchored rewrite (unique hit + plain-block guard). Other route_classes keep
        # the literal-only behavior.
        if route_class == "repo_review_text":
            return _apply_review_block_operation(
                delta=delta, current_text=current_text, write=write, base_operation=base_operation
            )
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
