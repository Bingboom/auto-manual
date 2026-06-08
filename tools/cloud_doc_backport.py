#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Feishu cloud document backport prototype.

P0 only: fetch/read a Feishu cloud document, normalize it, compare it with a
baseline, and write structured JSON + Markdown diff reports. It never edits
repo sources, review bundles, generated output, or Feishu bitable rows.
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
from tools.utils.path_utils import get_paths  # noqa: E402

REPORT_SCHEMA_VERSION = "cloud-doc-backport-report/v1"
DELTA_SCHEMA_VERSION = "cloud-doc-backport-delta/v1"
NORMALIZER_VERSION = "cloud-doc-normalizer/v1"

_SAFE_PATH_CHARS = re.compile(r"[^A-Za-z0-9._-]+")
_LARK_TAG_RE = re.compile(r"</?lark-[^>]*>", re.IGNORECASE)
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")
_LIST_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_PLACEHOLDER_RE = re.compile(r"(\{\{[^}]+\}\}|\|[A-Z][A-Z0-9_]+\|)")
_UNIT_VALUE_RE = re.compile(
    r"\b\d+(?:[.,]\d+)?\s?(?:W|V|A|Hz|Wh|kWh|mAh|Ah|degC|°C|%|mm|cm|m|kg|lb)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Block:
    kind: str
    text: str
    normalized: str
    heading_path: tuple[str, ...]
    line_no: int


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


def _extract_doc_markdown(raw_text: str) -> str:
    """Return lark-cli data.markdown when stdout is the documented JSON envelope."""
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

    markdown = payload.get("markdown")
    if isinstance(markdown, str):
        return markdown
    return raw_text


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
    local_path = _local_doc_path(doc_url)
    if local_path is not None:
        return _extract_doc_markdown(_read_text(local_path))
    if doc_url == "-":
        return _extract_doc_markdown(sys.stdin.read())

    attempts = [
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
    text = text.replace("**", "").replace("__", "")
    text = text.replace("\\n", "\n")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _table_separator(line: str) -> bool:
    return bool(_TABLE_SEPARATOR_RE.match(line))


def parse_blocks(text: str) -> list[Block]:
    """Parse fetched/baseline markdown-ish text into comparable blocks."""
    blocks: list[Block] = []
    heading_stack: list[str] = []
    paragraph_lines: list[str] = []
    paragraph_start = 0

    def current_path() -> tuple[str, ...]:
        return tuple(part for part in heading_stack if part)

    def add_block(kind: str, value: str, line_no: int) -> None:
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
            )
        )

    def flush_paragraph() -> None:
        nonlocal paragraph_lines, paragraph_start
        if paragraph_lines:
            add_block("paragraph", " ".join(paragraph_lines), paragraph_start)
            paragraph_lines = []
            paragraph_start = 0

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = _strip_lark_noise(raw_line).rstrip()
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
            add_block("heading", line.strip(), line_no)
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
    return {
        "kind": block.kind,
        "line_no": block.line_no,
        "heading_path": list(block.heading_path),
    }


def _context(blocks: list[Block], index: int) -> dict[str, str | None]:
    previous_text = blocks[index - 1].text if index > 0 else None
    next_text = blocks[index + 1].text if index + 1 < len(blocks) else None
    return {"previous": previous_text, "next": next_text}


def _looks_data_like(*blocks: Block | None) -> bool:
    text = " ".join(block.text for block in blocks if block is not None)
    if any(block and block.kind == "table_row" for block in blocks):
        return True
    return bool(_PLACEHOLDER_RE.search(text) or _UNIT_VALUE_RE.search(text))


def _classify_route(doc_type: str, old: Block | None, new: Block | None) -> tuple[str, str, str]:
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
) -> dict[str, Any]:
    route_class, confidence, reason = _classify_route(doc_type, old, new)
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
) -> list[dict[str, Any]]:
    import difflib

    baseline_norm = [block.normalized for block in baseline_blocks]
    fetched_norm = [block.normalized for block in fetched_blocks]
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
                    )
                )
    return deltas


def _counter_dict(values: list[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def build_report(
    *,
    run_id: str,
    doc_type: str,
    doc_url: str,
    baseline_path: Path,
    fetched_text: str,
    baseline_text: str,
    command: list[str],
) -> dict[str, Any]:
    baseline_blocks = parse_blocks(baseline_text)
    fetched_blocks = parse_blocks(fetched_text)
    deltas = diff_blocks(
        baseline_blocks,
        fetched_blocks,
        doc_type=doc_type,
        run_id=run_id,
    )
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "run_id": run_id,
        "doc_type": doc_type,
        "doc_url": doc_url,
        "baseline": baseline_path.as_posix(),
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
    lines = [
        "# Cloud Doc Backport Diff Report",
        "",
        "## Run",
        "",
        f"- Run ID: `{report['run_id']}`",
        f"- Result: `{report['result']}`",
        f"- Doc type: `{report['doc_type']}`",
        f"- Baseline: `{report['baseline']}`",
        f"- Normalizer: `{report['normalizer_version']}`",
        f"- Git ref: `{report['metadata'].get('git_ref') or 'unknown'}`",
        f"- Generated at: `{report['metadata']['generated_at']}`",
        f"- Command: `{report['metadata']['command']}`",
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


def _default_out_dir(run_id: str) -> Path:
    return get_paths().cloud_doc_backport_reports_dir / _safe_path_token(run_id)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Feishu cloud-doc backport helpers.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    diff_parser = subparsers.add_parser(
        "diff",
        description="Fetch/read a cloud doc and compare it with a baseline.",
    )
    diff_parser.add_argument("--doc-url", required=True, help="Feishu doc URL or local fixture path")
    diff_parser.add_argument("--baseline", required=True, help="baseline markdown file")
    diff_parser.add_argument("--doc-type", required=True, choices=("review", "template"))
    diff_parser.add_argument("--out", help="output directory for JSON and Markdown reports")
    diff_parser.add_argument("--run-id", default="cloud-doc-backport-local")
    diff_parser.add_argument("--lark-cli", default="lark-cli", help="lark-cli binary for real docs")
    return parser.parse_args(argv)


def _run_diff(args: argparse.Namespace, raw_argv: list[str]) -> int:
    run_id = str(args.run_id or "").strip() or "cloud-doc-backport-local"
    baseline_path = Path(args.baseline)
    out_dir = Path(args.out) if args.out else _default_out_dir(run_id)
    try:
        baseline_text = _read_text(baseline_path)
        fetched_text = fetch_doc_text(args.doc_url, lark_cli=args.lark_cli)
    except (OSError, RuntimeError) as exc:
        print(f"cloud-doc-backport: {exc}", file=sys.stderr)
        return 2
    report = build_report(
        run_id=run_id,
        doc_type=args.doc_type,
        doc_url=args.doc_url,
        baseline_path=baseline_path,
        fetched_text=fetched_text,
        baseline_text=baseline_text,
        command=["tools/cloud_doc_backport.py", *raw_argv],
    )
    written = write_reports(report, out_dir)
    print(f"WROTE {written['json']}")
    print(f"WROTE {written['markdown']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    args = _parse_args(raw_argv)
    if args.command == "diff":
        return _run_diff(args, raw_argv)
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
