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
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.cloud_doc_backport_model import _normalize_inline, parse_blocks  # noqa: E402
from tools.utils.path_utils import PathSegments, get_paths, revision_ledger_of  # noqa: E402

LEDGER_SCHEMA_VERSION = 1

LEDGER_FILENAME = "ledger.jsonl"

# Verdict assigned at ingest time; the reconcile step overwrites it once the
# review PR is merged and the final landed text is known.
PENDING_STATUS = "pending"

# Verdicts the reconcile step assigns once the landed text is known.
ACCEPTED_STATUS = "accepted_as_proposed"
REJECTED_STATUS = "rejected"
EDITED_STATUS = "edited_further"
SOURCE_MISSING_STATUS = "source_missing"
# Class-D only: the source-table sync neither wrote nor was declined — it
# abstained (drift, verify failure, dry-run, or unresolved record). Surfaced for
# a human; the row is not yet a clean label.
SOURCE_TABLE_ABSTAINED_STATUS = "source_table_abstained"

# Backport route classes this reconcile step knows how to resolve.
ROUTE_REVIEW = "repo_review_text"
ROUTE_SOURCE_TABLE = "source_table_suggestion"

_MERGE_FIELDS = ("merged_pr", "merged_commit", "merged_at", "reviewer")

# Fuzzy-verdict tuning. Exact containment stays the fast path; the similarity
# layer only decides rows where punctuation / line-break / single-word edits
# broke exact containment. Below MIN_FUZZY_LENGTH the ratio is too noisy to
# trust (a 6-char fragment matches half the document at 0.9), so short needles
# stay containment-only.
SIMILARITY_THRESHOLD = 0.90
MIN_FUZZY_LENGTH = 12


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


def write_ledger(rows: list[dict[str, Any]], ledger_path: Path) -> None:
    """Rewrite the whole ledger from rows (used by reconcile's in-place updates)."""
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _source_haystack(root: Path, source_path: str | None) -> str | None:
    """Return the normalized text of a review source file, or None if absent.

    The source is parsed with the same block parser the backport uses, then each
    block's normalized form is joined, so the comparison runs in the exact text
    space the deltas were derived in (markup, spacing, and image noise removed).
    """
    if not source_path:
        return None
    path = root / source_path
    if not path.exists():
        return None
    blocks = parse_blocks(path.read_text(encoding="utf-8-sig"))
    return " ".join(block.normalized for block in blocks)


def _partial_ratio(needle: str, hay: str) -> float:
    """Best similarity of ``needle`` against any needle-sized window of ``hay``.

    Sliding-window best-alignment ratio (the classic partial-ratio shape):
    anchor candidate windows at each matching block, then score the window with
    a plain ``SequenceMatcher`` ratio. Returns 0.0..1.0.
    """
    if not needle or not hay:
        return 0.0
    if len(needle) > len(hay):
        needle, hay = hay, needle
    anchor = difflib.SequenceMatcher(None, needle, hay, autojunk=False)
    best = 0.0
    for block in anchor.get_matching_blocks():
        start = max(block.b - block.a, 0)
        window = hay[start : start + len(needle)]
        if not window:
            continue
        ratio = difflib.SequenceMatcher(None, needle, window, autojunk=False).ratio()
        if ratio > best:
            best = ratio
        if best >= 0.995:
            break
    return best


def _fuzzy_present(needle: str, haystack: str, threshold: float) -> bool:
    """True when ``needle`` (near-)appears in ``haystack``.

    Exact containment first; the similarity layer only runs for needles long
    enough for the ratio to be meaningful.
    """
    if not needle:
        return False
    if needle in haystack:
        return True
    if len(needle) < MIN_FUZZY_LENGTH:
        return False
    return _partial_ratio(needle, haystack) >= threshold


def classify_verdict(
    row: dict[str, Any],
    haystack: str | None,
    *,
    threshold: float = SIMILARITY_THRESHOLD,
) -> str:
    """Decide what landed for one row, given the merged source's normalized text.

    Works in the normalized text space, with a similarity layer on top of exact
    containment so punctuation / line-break level edits do not misclassify:

    - Deletion proposal (reviewer_text empty): accepted if the machine text is
      gone (exactly and near-exactly), else rejected.
    - Otherwise: accepted if the reviewer's text (near-)appears; else rejected
      if the machine's original text still (near-)appears; else edited_further.

    When both texts near-appear, the higher partial ratio wins, so a reviewer
    edit that landed with a tweaked comma is ``accepted_as_proposed`` rather
    than falling through to the machine text's stale match. Near-match
    acceptance means ``final_text`` (the reviewer's proposal) may differ from
    the landed text by up to ``1 - threshold``.
    """
    if haystack is None:
        return SOURCE_MISSING_STATUS
    reviewer = _normalize_inline(row.get("reviewer_text") or "")
    machine = _normalize_inline(row.get("machine_text") or "")
    if not reviewer:
        return REJECTED_STATUS if _fuzzy_present(machine, haystack, threshold) else ACCEPTED_STATUS
    if reviewer in haystack:
        return ACCEPTED_STATUS
    if machine and machine in haystack:
        return REJECTED_STATUS
    reviewer_ratio = (
        _partial_ratio(reviewer, haystack) if len(reviewer) >= MIN_FUZZY_LENGTH else 0.0
    )
    machine_ratio = (
        _partial_ratio(machine, haystack)
        if machine and len(machine) >= MIN_FUZZY_LENGTH
        else 0.0
    )
    if reviewer_ratio >= threshold and reviewer_ratio >= machine_ratio:
        return ACCEPTED_STATUS
    if machine_ratio >= threshold:
        return REJECTED_STATUS
    return EDITED_STATUS


def _final_text_for(row: dict[str, Any], status: str) -> str | None:
    if status == ACCEPTED_STATUS:
        return row.get("reviewer_text")
    if status == REJECTED_STATUS:
        return row.get("machine_text")
    return None


def _git_merge_meta(root: Path, source_path: str | None) -> dict[str, Any]:
    """Resolve merge metadata for a source file from its last landing commit.

    Reads the newest commit touching ``source_path`` (on the current checkout):
    commit SHA, commit date, author, and the PR number when the squash-merge
    subject carries the conventional ``(#123)`` suffix. Returns {} when git or
    the path is unavailable, so reconcile degrades to unstamped verdicts.
    """
    if not source_path:
        return {}
    try:
        proc = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "log",
                "-1",
                "--format=%H%x1f%cI%x1f%an%x1f%s",
                "--",
                source_path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {}
    line = (proc.stdout or "").strip()
    if proc.returncode != 0 or not line:
        return {}
    parts = line.split("\x1f")
    if len(parts) != 4:
        return {}
    sha, committed_at, author, subject = parts
    pr_match = re.search(r"\(#(\d+)\)", subject)
    return {
        "merged_commit": sha,
        "merged_at": committed_at,
        "reviewer": author,
        "merged_pr": f"#{pr_match.group(1)}" if pr_match else None,
    }


def index_apply_report(apply_report: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    """Index a source_table_sync apply report by delta_hash.

    Both ``plan`` (includes skipped/not-approved entries with their reason) and
    ``applied`` (the entries that reached a write outcome) are keyed; ``applied``
    wins because it carries the authoritative final status.
    """
    index: dict[str, dict[str, Any]] = {}
    if not apply_report:
        return index
    for entry in apply_report.get("plan") or []:
        delta_hash = entry.get("delta_hash")
        if delta_hash:
            index[delta_hash] = entry
    for entry in apply_report.get("applied") or []:
        delta_hash = entry.get("delta_hash")
        if delta_hash:
            index[delta_hash] = entry
    return index


def classify_source_table_verdict(entry: dict[str, Any]) -> str:
    """Map a source_table_sync plan/applied entry to a ledger verdict.

    written/already_applied -> accepted; a human-not-approved skip -> rejected;
    any abstain (drift, verify failure, dry-run ``planned``, unresolved record,
    or a non-approval skip) -> source_table_abstained.
    """
    status = entry.get("status")
    if status in ("written", "already_applied"):
        return ACCEPTED_STATUS
    if status in ("drift_abstained", "verify_failed", "error", "planned"):
        return SOURCE_TABLE_ABSTAINED_STATUS
    if entry.get("action") == "skip":
        if "not approved" in (entry.get("reason") or ""):
            return REJECTED_STATUS
        return SOURCE_TABLE_ABSTAINED_STATUS
    return SOURCE_TABLE_ABSTAINED_STATUS


def reconcile_rows(
    rows: list[dict[str, Any]],
    *,
    root: Path,
    merge_meta: dict[str, Any] | None = None,
    apply_index: dict[str, dict[str, Any]] | None = None,
    force: bool = False,
    auto_merge_meta: bool = False,
) -> dict[str, Any]:
    """Fill verdict + merge fields on pending rows in place, routed by route_class.

    ``repo_review_text`` rows reconcile against the branch ``_review`` text;
    ``source_table_suggestion`` rows reconcile against ``apply_index`` (a
    source_table_sync apply report, keyed by delta_hash). Rows of other route
    classes, and source-table rows with no apply entry yet, are left pending.
    Decided rows are skipped unless ``force``. Returns per-verdict counts.

    With ``auto_merge_meta``, merge metadata for review-route rows is resolved
    from git (the last commit touching each row's source file); explicit
    ``merge_meta`` values win over the resolved ones.
    """
    merge_meta = merge_meta or {}
    apply_index = apply_index or {}
    haystacks: dict[str, str | None] = {}
    git_meta: dict[str, dict[str, Any]] = {}
    counts: dict[str, int] = {}
    reconciled = 0
    for row in rows:
        if not force and row.get("final_status") != PENDING_STATUS:
            continue
        route = row.get("route_class")
        source_path = row.get("source_path")
        if route == ROUTE_SOURCE_TABLE:
            entry = apply_index.get(row.get("delta_hash"))
            if entry is None:
                continue  # no apply outcome yet -> stays pending
            status = classify_source_table_verdict(entry)
        elif route == ROUTE_REVIEW:
            key = source_path or ""
            if key not in haystacks:
                haystacks[key] = _source_haystack(root, source_path)
            status = classify_verdict(row, haystacks[key])
            if status == SOURCE_MISSING_STATUS:
                counts[status] = counts.get(status, 0) + 1
                continue
        else:
            continue  # template / image / needs_human_mapping: not reconciled here
        row["final_status"] = status
        row["final_text"] = _final_text_for(row, status)
        resolved_meta = merge_meta
        if auto_merge_meta and route == ROUTE_REVIEW:
            key = source_path or ""
            if key not in git_meta:
                git_meta[key] = _git_merge_meta(root, source_path)
            resolved_meta = {**git_meta[key], **{k: v for k, v in merge_meta.items() if v is not None}}
        for field in _MERGE_FIELDS:
            if resolved_meta.get(field) is not None:
                row[field] = resolved_meta[field]
        counts[status] = counts.get(status, 0) + 1
        reconciled += 1
    return {"rows_reconciled": reconciled, "verdicts": counts}


def reconcile(
    ledger_path: Path,
    *,
    root: Path,
    merge_meta: dict[str, Any] | None = None,
    apply_report: dict[str, Any] | None = None,
    force: bool = False,
    auto_merge_meta: bool = False,
) -> dict[str, Any]:
    """Load a ledger, reconcile pending rows, write back.

    ``apply_report`` is an optional source_table_sync apply report used to resolve
    ``source_table_suggestion`` (online-table) rows. ``auto_merge_meta`` resolves
    merge metadata from git per source file (explicit ``merge_meta`` wins).
    """
    rows = load_ledger(ledger_path)
    apply_index = index_apply_report(apply_report)
    summary = reconcile_rows(
        rows,
        root=root,
        merge_meta=merge_meta,
        apply_index=apply_index,
        force=force,
        auto_merge_meta=auto_merge_meta,
    )
    if summary["rows_reconciled"]:
        write_ledger(rows, ledger_path)
    summary["ledger"] = str(ledger_path)
    return summary


_DECIDED_STATUSES = (ACCEPTED_STATUS, REJECTED_STATUS, EDITED_STATUS)

# Verdicts where the machine output was changed (the reviewer's text landed, or
# something other than the machine text did) — i.e. a real correction signal.
_CORRECTION_STATUSES = (ACCEPTED_STATUS, EDITED_STATUS)

TM_CANDIDATES_FILENAME = "tm_candidates.jsonl"


def tm_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Project accepted review-prose corrections into TM pair suggestions.

    Emits the exact suggestion shape ``translation_memory_sync.
    apply_translation_suggestions`` consumes (delta_hash / lang / old_text /
    new_text), so the reviewer-corrected sentence pair rides the existing
    approval-gated, exact-or-abstain, GET-verified TM write path instead of a
    new one. Only ``accepted_as_proposed`` review-route rows with a known
    target language and a real text change qualify; ``edited_further`` rows are
    excluded because the landed text is unknown. De-duplicated by
    ``delta_hash`` (the same correction seen in a later run adds nothing).
    """
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        if row.get("final_status") != ACCEPTED_STATUS:
            continue
        if row.get("route_class") != ROUTE_REVIEW:
            continue
        lang = row.get("lang")
        old_text = row.get("machine_text")
        new_text = row.get("final_text") or row.get("reviewer_text")
        delta_hash = row.get("delta_hash")
        if not (lang and delta_hash and old_text and new_text):
            continue
        if _normalize_inline(str(old_text)) == _normalize_inline(str(new_text)):
            continue
        if delta_hash in seen:
            continue
        seen.add(delta_hash)
        candidates.append(
            {
                "delta_hash": delta_hash,
                "copy_key": None,
                "lang": lang,
                "source_lang": None,
                "old_text": old_text,
                "new_text": new_text,
                "routing_hint": "translation_memory",
                "provenance": {
                    "row_key": row.get("row_key"),
                    "run_id": row.get("run_id"),
                    "source_path": row.get("source_path"),
                    "model": row.get("model"),
                    "region": row.get("region"),
                    "merged_pr": row.get("merged_pr"),
                },
            }
        )
    return candidates


def write_tm_candidates(candidates: list[dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for candidate in candidates:
            handle.write(json.dumps(candidate, ensure_ascii=False, sort_keys=True) + "\n")


def load_tm_candidates(path: Path) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            candidates.append(json.loads(line))
    return candidates


def _approved_hashes(approve: list[str] | None, approve_file: Path | None) -> set[str]:
    hashes = {value.strip() for value in (approve or []) if value.strip()}
    if approve_file is not None:
        for line in approve_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                hashes.add(line)
    return hashes


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate the ledger into quality metrics.

    ``acceptance_rate`` is the share of *decided* rows whose proposed reviewer
    correction landed verbatim (``accepted_as_proposed``); it measures how often
    a captured reviewer edit survived to the merged source. ``top_corrected_sources``
    ranks the files where the machine output was changed most often.
    """
    by_status: dict[str, int] = {}
    by_route: dict[str, dict[str, int]] = {}
    corrected_by_source: dict[str, int] = {}
    for row in rows:
        status = row.get("final_status") or PENDING_STATUS
        by_status[status] = by_status.get(status, 0) + 1
        if status in _DECIDED_STATUSES:
            route = row.get("route_class") or "unknown"
            bucket = by_route.setdefault(route, {})
            bucket[status] = bucket.get(status, 0) + 1
        if status in _CORRECTION_STATUSES:
            source = row.get("source_path") or "unknown"
            corrected_by_source[source] = corrected_by_source.get(source, 0) + 1

    decided = sum(by_status.get(status, 0) for status in _DECIDED_STATUSES)
    accepted = by_status.get(ACCEPTED_STATUS, 0)
    route_rates: dict[str, dict[str, Any]] = {}
    for route, bucket in by_route.items():
        route_decided = sum(bucket.values())
        route_rates[route] = {
            **bucket,
            "decided": route_decided,
            "acceptance_rate": (
                round(bucket.get(ACCEPTED_STATUS, 0) / route_decided, 4) if route_decided else None
            ),
        }
    top = sorted(corrected_by_source.items(), key=lambda item: (-item[1], item[0]))
    pending = by_status.get(PENDING_STATUS, 0)
    total = len(rows)
    return {
        "total_rows": total,
        "by_status": by_status,
        "decided": decided,
        # The closed-loop health metric: share of captured corrections that have
        # left ``pending`` (reconciled to any outcome). 0.0 means the ledger is
        # recording but nobody is closing the loop.
        "reflow_rate": round((total - pending) / total, 4) if total else None,
        "acceptance_rate": round(accepted / decided, 4) if decided else None,
        "by_route_class": route_rates,
        "top_corrected_sources": [
            {"source_path": source, "corrections": count} for source, count in top[:20]
        ],
    }


def export_pairs(
    rows: list[dict[str, Any]], *, include_rejected: bool = False
) -> list[dict[str, Any]]:
    """Emit ``machine_text -> final_text`` training pairs from reconciled rows.

    Yields one pair per ``accepted_as_proposed`` row where the text actually
    changed (a genuine correction). With ``include_rejected`` it also emits
    ``rejected`` rows as no-change examples (machine output was kept).
    ``edited_further`` rows are skipped because the landed text is unknown.
    """
    pairs: list[dict[str, Any]] = []
    for row in rows:
        status = row.get("final_status")
        if status == ACCEPTED_STATUS:
            machine = row.get("machine_text")
            final = row.get("final_text")
            if final is None or machine == final:
                continue
        elif status == REJECTED_STATUS and include_rejected:
            machine = row.get("machine_text")
            final = row.get("final_text")
        else:
            continue
        pairs.append(
            {
                "input": machine,
                "target": final,
                "verdict": status,
                "route_class": row.get("route_class"),
                "model": row.get("model"),
                "region": row.get("region"),
                "lang": row.get("lang"),
                "delta_hash": row.get("delta_hash"),
            }
        )
    return pairs


def write_pairs(pairs: list[dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for pair in pairs:
            handle.write(json.dumps(pair, ensure_ascii=False, sort_keys=True) + "\n")


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
    ingest.add_argument(
        "--no-reconcile",
        action="store_true",
        help="Skip the automatic reconcile pass that runs after ingest.",
    )
    ingest.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repo root for the post-ingest reconcile pass (default: repo root).",
    )

    rec = sub.add_parser(
        "reconcile",
        help="Fill verdict/merge fields on pending rows from merged _review text.",
    )
    rec.add_argument(
        "--ledger",
        type=Path,
        default=None,
        help="Ledger JSONL path (default: reports/revision_ledger/ledger.jsonl).",
    )
    rec.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repo root used to resolve each row's source_path (default: repo root).",
    )
    rec.add_argument(
        "--apply-report",
        type=Path,
        default=None,
        help="source_table_sync apply report JSON, used to resolve online-table "
        "(source_table_suggestion) rows.",
    )
    rec.add_argument("--merged-pr", default=None, help="PR reference to stamp on reconciled rows.")
    rec.add_argument("--merged-commit", default=None, help="Merge commit SHA to stamp.")
    rec.add_argument("--merged-at", default=None, help="Merge timestamp to stamp.")
    rec.add_argument("--reviewer", default=None, help="Reviewer identity to stamp.")
    rec.add_argument(
        "--force",
        action="store_true",
        help="Re-evaluate rows that already carry a verdict, not just pending ones.",
    )
    rec.add_argument(
        "--auto",
        action="store_true",
        help="Resolve merge metadata (commit, date, author, PR) from git per "
        "source file; explicit --merged-*/--reviewer values win.",
    )

    stats = sub.add_parser("stats", help="Print quality metrics aggregated from the ledger.")
    stats.add_argument(
        "--ledger",
        type=Path,
        default=None,
        help="Ledger JSONL path (default: reports/revision_ledger/ledger.jsonl).",
    )

    export = sub.add_parser(
        "export",
        help="Export machine_text -> final_text training pairs from reconciled rows.",
    )
    export.add_argument(
        "--ledger",
        type=Path,
        default=None,
        help="Ledger JSONL path (default: reports/revision_ledger/ledger.jsonl).",
    )
    export.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write pairs as JSONL to this path (default: print to stdout).",
    )
    export.add_argument(
        "--include-rejected",
        action="store_true",
        help="Also emit rejected rows as no-change (machine-kept) examples.",
    )

    tmc = sub.add_parser(
        "tm-candidates",
        help="Emit TM pair suggestions from accepted review-prose corrections.",
    )
    tmc.add_argument(
        "--ledger",
        type=Path,
        default=None,
        help="Ledger JSONL path (default: reports/revision_ledger/ledger.jsonl).",
    )
    tmc.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Candidates JSONL path (default: reports/revision_ledger/tm_candidates.jsonl).",
    )

    tma = sub.add_parser(
        "tm-apply",
        help="Apply approved TM pair candidates via the gated TM write path "
        "(dry-run unless --write with --tm-binding).",
    )
    tma.add_argument(
        "--candidates",
        type=Path,
        default=None,
        help="Candidates JSONL (default: reports/revision_ledger/tm_candidates.jsonl).",
    )
    tma.add_argument(
        "--approve",
        action="append",
        default=None,
        help="delta_hash approved by a human (repeatable).",
    )
    tma.add_argument(
        "--approve-file",
        type=Path,
        default=None,
        help="File with one approved delta_hash per line (# comments allowed).",
    )
    tma.add_argument(
        "--tm-binding",
        default=None,
        help="Live Translation_Memory binding BASE:TABLE_ID (required with --write).",
    )
    tma.add_argument("--lark-cli", default="lark-cli", help="lark-cli binary for the live transport.")
    tma.add_argument("--identity", default="bot", help="lark-cli identity for the live transport.")
    tma.add_argument(
        "--write",
        action="store_true",
        help="Perform live TM writes (GET-verified, idempotent). Dry-run without it.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "ingest":
        ledger_path = args.ledger or default_ledger_path()
        summary = ingest_report_file(args.report, ledger_path=ledger_path)
        if not args.no_reconcile:
            # Close the loop opportunistically: every ingest (each backport
            # round) also settles the still-pending rows from earlier rounds
            # against the current checkout, so the ledger reconciles without a
            # separate human-remembered step. The ledger is a local artifact,
            # so this local piggyback — not CI — is the merge-time trigger.
            root = args.root or get_paths().root
            summary["reconcile"] = reconcile(
                ledger_path, root=root, auto_merge_meta=True
            )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    if args.command == "reconcile":
        ledger_path = args.ledger or default_ledger_path()
        root = args.root or get_paths().root
        apply_report = (
            json.loads(args.apply_report.read_text(encoding="utf-8"))
            if args.apply_report is not None
            else None
        )
        merge_meta = {
            "merged_pr": args.merged_pr,
            "merged_commit": args.merged_commit,
            "merged_at": args.merged_at,
            "reviewer": args.reviewer,
        }
        summary = reconcile(
            ledger_path,
            root=root,
            merge_meta=merge_meta,
            apply_report=apply_report,
            force=args.force,
            auto_merge_meta=args.auto,
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    if args.command == "stats":
        ledger_path = args.ledger or default_ledger_path()
        summary = summarize(load_ledger(ledger_path))
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    if args.command == "export":
        ledger_path = args.ledger or default_ledger_path()
        pairs = export_pairs(load_ledger(ledger_path), include_rejected=args.include_rejected)
        if args.out is not None:
            write_pairs(pairs, args.out)
            print(json.dumps({"out": str(args.out), "pairs": len(pairs)}, ensure_ascii=False))
        else:
            for pair in pairs:
                print(json.dumps(pair, ensure_ascii=False, sort_keys=True))
        return 0
    if args.command == "tm-candidates":
        ledger_path = args.ledger or default_ledger_path()
        out_path = args.out or (get_paths().revision_ledger_dir / TM_CANDIDATES_FILENAME)
        candidates = tm_candidates(load_ledger(ledger_path))
        write_tm_candidates(candidates, out_path)
        print(
            json.dumps(
                {"out": str(out_path), "candidates": len(candidates)}, ensure_ascii=False
            )
        )
        return 0
    if args.command == "tm-apply":
        from tools.translation_memory_sync import apply_translation_suggestions

        candidates_path = args.candidates or (
            get_paths().revision_ledger_dir / TM_CANDIDATES_FILENAME
        )
        candidates = load_tm_candidates(candidates_path)
        approved = _approved_hashes(args.approve, args.approve_file)
        transport = None
        if args.write:
            if not args.tm_binding:
                print("revision-ledger: --write requires --tm-binding BASE:TABLE_ID", file=sys.stderr)
                return 2
            from tools.cloud_doc_backport_transports import _tm_transport

            transport = _tm_transport(
                args.tm_binding, lark_cli=args.lark_cli, identity=args.identity
            )
        result = apply_translation_suggestions(
            candidates,
            approved_hashes=approved,
            transport=transport,
            write=bool(args.write),
        )
        result["candidates"] = str(candidates_path)
        result["approved_count"] = len(approved)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
