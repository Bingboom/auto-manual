#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TM pre-translation hit-rate ledger.

Each ``lark-tm-translation-preprocess`` run already writes a per-run
``*.report.json`` (change list + counters) and then scatters it. This module
accumulates those runs into a single JSONL ledger under
``reports/tm_hit_rate/ledger.jsonl`` so the hit rate — matched translation
units / total translation units — has a baseline and a trend, instead of being
a one-off number nobody can compare.

Scope: pure stdlib on purpose. The preprocess script runs in its own skill
environment (lxml et al.); this module must import cleanly from any Python so
the script can append to the ledger best-effort, and the repo test suite can
cover the logic without the skill's dependencies.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.utils.path_utils import get_paths, tm_hit_rate_of  # noqa: E402

LEDGER_SCHEMA_VERSION = 1

LEDGER_FILENAME = "ledger.jsonl"


def default_ledger_path(base_root: Path | None = None) -> Path:
    if base_root is None:
        return get_paths().tm_hit_rate_dir / LEDGER_FILENAME
    return tm_hit_rate_of(base_root) / LEDGER_FILENAME


def _run_key(report: dict[str, Any]) -> str:
    """Stable identity for one preprocess run, for idempotent re-ingest.

    Derived from the run's own content (documents, language pair, counters,
    change fingerprints) so re-ingesting the same report is a no-op while a
    genuine re-run of the same document lands as a new row.
    """
    changes = report.get("changes") or []
    fingerprint = json.dumps(
        {
            "input": report.get("input_docx"),
            "output": report.get("output_docx"),
            "pair": f"{report.get('source_lang')}->{report.get('target_lang')}",
            "units_total": report.get("units_total"),
            "units_matched": report.get("units_matched"),
            "change_count": report.get("change_count"),
            "changes": [
                (change.get("source"), change.get("row_key"))
                if isinstance(change, dict)
                else str(change)
                for change in changes[:50]
            ],
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha1(fingerprint.encode("utf-8")).hexdigest()


def entry_from_report(report: dict[str, Any], *, recorded_at: str | None = None) -> dict[str, Any]:
    """Project one preprocess report into a ledger entry.

    ``units_total`` / ``units_matched`` come from the preprocess counters;
    reports written before those counters existed yield ``hit_rate: null``
    rather than a fabricated number.
    """
    units_total = report.get("units_total")
    units_matched = report.get("units_matched")
    hit_rate: float | None = None
    if isinstance(units_total, int) and isinstance(units_matched, int) and units_total > 0:
        hit_rate = round(units_matched / units_total, 4)
    return {
        "ledger_schema_version": LEDGER_SCHEMA_VERSION,
        "run_key": _run_key(report),
        "recorded_at": recorded_at
        or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "input_docx": report.get("input_docx"),
        "output_docx": report.get("output_docx"),
        "source_lang": report.get("source_lang"),
        "target_lang": report.get("target_lang"),
        "units_total": units_total,
        "units_matched": units_matched,
        "hit_rate": hit_rate,
        "change_count": report.get("change_count"),
    }


def load_ledger(ledger_path: Path) -> list[dict[str, Any]]:
    if not ledger_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def ingest_report(
    report: dict[str, Any], *, ledger_path: Path, recorded_at: str | None = None
) -> dict[str, Any]:
    """Append one run's entry to the ledger; re-ingesting the same run is a no-op."""
    entry = entry_from_report(report, recorded_at=recorded_at)
    existing = {row.get("run_key") for row in load_ledger(ledger_path)}
    if entry["run_key"] in existing:
        return {"ledger": str(ledger_path), "written": 0, "skipped": 1, "entry": entry}
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    return {"ledger": str(ledger_path), "written": 1, "skipped": 0, "entry": entry}


def ingest_report_file(
    report_path: Path, *, ledger_path: Path, recorded_at: str | None = None
) -> dict[str, Any]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise ValueError(f"report {report_path} is not a JSON object")
    return ingest_report(report, ledger_path=ledger_path, recorded_at=recorded_at)


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate the ledger: overall and per language-pair hit rate.

    Only rows with counters participate in the rate; counter-less legacy rows
    are reported separately so they cannot silently skew the baseline.
    """
    overall_total = 0
    overall_matched = 0
    without_counters = 0
    by_pair: dict[str, dict[str, int]] = {}
    for row in rows:
        units_total = row.get("units_total")
        units_matched = row.get("units_matched")
        if not isinstance(units_total, int) or not isinstance(units_matched, int):
            without_counters += 1
            continue
        pair = f"{row.get('source_lang')}->{row.get('target_lang')}"
        bucket = by_pair.setdefault(pair, {"runs": 0, "units_total": 0, "units_matched": 0})
        bucket["runs"] += 1
        bucket["units_total"] += units_total
        bucket["units_matched"] += units_matched
        overall_total += units_total
        overall_matched += units_matched

    pair_rates: dict[str, dict[str, Any]] = {}
    for pair, bucket in sorted(by_pair.items()):
        pair_rates[pair] = {
            **bucket,
            "hit_rate": (
                round(bucket["units_matched"] / bucket["units_total"], 4)
                if bucket["units_total"]
                else None
            ),
        }
    return {
        "runs": len(rows),
        "runs_without_counters": without_counters,
        "units_total": overall_total,
        "units_matched": overall_matched,
        "hit_rate": round(overall_matched / overall_total, 4) if overall_total else None,
        "by_language_pair": pair_rates,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="tm_hit_rate",
        description="Accumulate TM pre-translation hit rates from preprocess reports.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="Append one preprocess report's run to the ledger.")
    ingest.add_argument("--report", required=True, type=Path, help="Preprocess *.report.json path.")
    ingest.add_argument(
        "--ledger",
        type=Path,
        default=None,
        help="Ledger JSONL path (default: reports/tm_hit_rate/ledger.jsonl).",
    )

    stats = sub.add_parser("stats", help="Print overall and per-language-pair hit rates.")
    stats.add_argument(
        "--ledger",
        type=Path,
        default=None,
        help="Ledger JSONL path (default: reports/tm_hit_rate/ledger.jsonl).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    ledger_path = args.ledger or default_ledger_path()
    if args.command == "ingest":
        summary = ingest_report_file(args.report, ledger_path=ledger_path)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    if args.command == "stats":
        print(json.dumps(summarize(load_ledger(ledger_path)), ensure_ascii=False, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
