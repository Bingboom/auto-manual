#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Revision ledger: accumulate reviewer-correction records from backport runs.

The cloud-doc backport (``tools/cloud_doc_backport.py``) already classifies every
reviewer edit into a structured delta (machine text -> reviewer text, with route
class, location, and confidence). Those reports are written per run and then
scattered. This module collects them into a single append-only ledger so the
"machine produced X -> a human corrected it to Y" signal is no longer thrown
away after each review.

MVP scope (ingest only):

- Read one backport diff report (the dict written by
  ``cloud_doc_backport_reports.build_report``) and turn each delta into one ledger
  row.
- Append rows to ``reports/revision_ledger/ledger.jsonl`` (JSON Lines), de-duped
  by ``row_key`` so re-ingesting the same report is a no-op (idempotent).
- Leave the human-verdict fields (``final_status`` / ``final_text`` / merge
  metadata) as ``pending``. A later ``reconcile`` step fills them in from the
  merged ``docs/_review`` text; see ``code-as-doc`` follow-up.

This module only reads existing reports and appends to a new file. It does not
touch source tables, templates, or the review bundle, and it does not change any
backport behaviour.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.utils.path_utils import PathSegments, get_paths, revision_ledger_of  # noqa: E402

LEDGER_SCHEMA_VERSION = 1

LEDGER_FILENAME = "ledger.jsonl"

# Verdict assigned at ingest time; the reconcile step overwrites it once the
# review PR is merged and the final landed text is known.
PENDING_STATUS = "pending"


def default_ledger_path(base_root: Path | None = None) -> Path:
    """Return the canonical ledger file path under ``reports/revision_ledger``."""
    if base_root is None:
        return get_paths().revision_ledger_dir / LEDGER_FILENAME
    return revision_ledger_of(base_root) / LEDGER_FILENAME


def _target_from_source_path(source_path: str | None) -> dict[str, str | None]:
    """Best-effort (model, region, lang) parse from a review source path.

    Review sources live under ``docs/_review/<model>/<region>/<lang>/...``; the
    segments right after ``_review`` carry the target identity. Anything that does
    not match that layout (e.g. a template source) yields ``None`` fields rather
    than a guess.
    """
    empty: dict[str, str | None] = {"model": None, "region": None, "lang": None}
    if not source_path:
        return empty
    parts = Path(source_path).as_posix().split("/")
    if PathSegments.REVIEW not in parts:
        return empty
    after = parts[parts.index(PathSegments.REVIEW) + 1 :]
    keys = ("model", "region", "lang")
    return {key: (after[i] if i < len(after) else None) for i, key in enumerate(keys)}


def _row_key(run_id: str | None, delta: dict[str, Any]) -> str:
    """Stable per-row identity used for idempotent de-duplication.

    Scoped to the run so re-ingesting the same report never duplicates rows,
    while the same correction observed in a later run is kept as a new row.
    """
    delta_hash = delta.get("delta_hash")
    discriminator = delta_hash if delta_hash else f"idx:{delta.get('index')}"
    return f"{run_id or 'unknown-run'}:{discriminator}"


def delta_to_row(report: dict[str, Any], delta: dict[str, Any]) -> dict[str, Any]:
    """Project one backport delta + its report header into a ledger row."""
    metadata = report.get("metadata") or {}
    source_target = report.get("source_target") or {}
    source_path = source_target.get("path")
    location = delta.get("location") or {}
    target = _target_from_source_path(source_path)
    return {
        "ledger_schema_version": LEDGER_SCHEMA_VERSION,
        "row_key": _row_key(report.get("run_id"), delta),
        "delta_hash": delta.get("delta_hash"),
        "run_id": report.get("run_id"),
        "generated_at": metadata.get("generated_at"),
        "git_ref": metadata.get("git_ref"),
        "doc_type": report.get("doc_type"),
        "doc_url": report.get("doc_url"),
        "model": target["model"],
        "region": target["region"],
        "lang": target["lang"],
        "source_path": source_path,
        "block_kind": location.get("kind"),
        "heading_path": location.get("heading_path") or [],
        "line_no": location.get("line_no"),
        "change_type": delta.get("change_type"),
        "route_class": delta.get("route_class"),
        "confidence": delta.get("confidence"),
        "semantic_review_required": delta.get("semantic_review_required"),
        # The flywheel signal: what the machine produced vs what the reviewer wrote.
        "machine_text": delta.get("old_text"),
        "reviewer_text": delta.get("new_text"),
        "source_evidence": delta.get("source_evidence") or {},
        # Human verdict — populated later by reconcile, pending until the PR merges.
        "final_status": PENDING_STATUS,
        "final_text": None,
        "merged_pr": None,
        "merged_commit": None,
        "merged_at": None,
        "reviewer": None,
    }


def load_ledger(ledger_path: Path) -> list[dict[str, Any]]:
    """Read all rows from a JSONL ledger; returns [] if the file is absent."""
    if not ledger_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def existing_row_keys(ledger_path: Path) -> set[str]:
    return {row.get("row_key") for row in load_ledger(ledger_path) if row.get("row_key")}


def ingest_report(report: dict[str, Any], *, ledger_path: Path) -> dict[str, Any]:
    """Append the report's deltas to the ledger, skipping already-present rows.

    Returns a small summary dict: how many deltas were seen, written, and
    skipped as duplicates.
    """
    deltas = report.get("deltas") or []
    seen_keys = existing_row_keys(ledger_path)
    new_rows: list[dict[str, Any]] = []
    skipped = 0
    for delta in deltas:
        row = delta_to_row(report, delta)
        if row["row_key"] in seen_keys:
            skipped += 1
            continue
        seen_keys.add(row["row_key"])
        new_rows.append(row)

    if new_rows:
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with ledger_path.open("a", encoding="utf-8") as handle:
            for row in new_rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    return {
        "ledger": str(ledger_path),
        "run_id": report.get("run_id"),
        "deltas_seen": len(deltas),
        "rows_written": len(new_rows),
        "rows_skipped": skipped,
    }


def ingest_report_file(report_path: Path, *, ledger_path: Path) -> dict[str, Any]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise ValueError(f"report {report_path} is not a JSON object")
    return ingest_report(report, ledger_path=ledger_path)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="revision_ledger",
        description="Accumulate reviewer-correction records from backport reports.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser(
        "ingest",
        help="Append a backport diff report's deltas to the revision ledger.",
    )
    ingest.add_argument(
        "--report",
        required=True,
        type=Path,
        help="Path to a backport diff report JSON (build_report output).",
    )
    ingest.add_argument(
        "--ledger",
        type=Path,
        default=None,
        help="Ledger JSONL path (default: reports/revision_ledger/ledger.jsonl).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "ingest":
        ledger_path = args.ledger or default_ledger_path()
        summary = ingest_report_file(args.report, ledger_path=ledger_path)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
