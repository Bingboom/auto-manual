#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for QC_Report writeback (Milestone F, PR F8)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.qc_report import (  # noqa: E402
    build_qc_report_rows,
    load_findings,
    plan_upsert,
    upsert_qc_report,
)


def _finding(finding_hash: str = "fh1", severity: str = "FAIL") -> dict:
    return {
        "run_id": "2026-06-19T00-00-00Z",
        "finding_hash": finding_hash,
        "severity": severity,
        "rule": "english_residue",
        "source_ref": {"kind": "lcd_icon", "table": "lcd_icons_blocks"},
        "record_id": None,
        "resolution_status": "snapshot_only",
        "suggested_action": "Fix the localized source field, then sync and re-run QC.",
    }


class _FakeQcTable:
    def __init__(self, existing: tuple[str, ...] = ()) -> None:
        self.rows: list = []
        self._existing: set[str] = set(existing)
        self._n = 0

    def append_row(self, *, row) -> str:
        self._n += 1
        rid = f"rec{self._n}"
        self.rows.append(row)
        self._existing.add(row.get("finding_hash"))
        return rid

    def list_finding_hashes(self) -> set[str]:
        return set(self._existing)


class BuildRowsTests(unittest.TestCase):
    def test_rows_carry_contract_fields(self) -> None:
        rows = build_qc_report_rows([_finding()])
        row = rows[0]
        for key in ("run_id", "finding_hash", "severity", "rule", "source_ref", "record_id", "suggested_action"):
            self.assertIn(key, row)
        self.assertEqual(row["finding_hash"], "fh1")


class PlanUpsertTests(unittest.TestCase):
    def test_new_row_is_upserted(self) -> None:
        plan = plan_upsert(build_qc_report_rows([_finding()]))
        self.assertEqual(plan[0]["action"], "upsert")

    def test_duplicate_in_batch_is_idempotent(self) -> None:
        plan = plan_upsert(build_qc_report_rows([_finding(), _finding()]))
        self.assertEqual(plan[0]["action"], "upsert")
        self.assertEqual(plan[1]["action"], "skip")
        self.assertIn("idempotent", plan[1]["reason"])

    def test_existing_hash_is_skipped(self) -> None:
        plan = plan_upsert(build_qc_report_rows([_finding()]), existing_hashes={"fh1"})
        self.assertEqual(plan[0]["action"], "skip")
        self.assertIn("already in QC_Report", plan[0]["reason"])

    def test_missing_hash_is_skipped(self) -> None:
        plan = plan_upsert([{"rule": "x"}])
        self.assertEqual(plan[0]["action"], "skip")


class UpsertTests(unittest.TestCase):
    def test_dry_run_plans_without_writing(self) -> None:
        report = upsert_qc_report(build_qc_report_rows([_finding()]))
        self.assertFalse(report["external_write"])
        self.assertEqual(report["summary"]["written"], 0)
        self.assertEqual(report["applied"][0]["status"], "planned")

    def test_write_appends_and_returns_record_id(self) -> None:
        table = _FakeQcTable()
        report = upsert_qc_report(build_qc_report_rows([_finding()]), transport=table, write=True)
        self.assertTrue(report["external_write"])
        self.assertEqual(report["summary"]["written"], 1)
        self.assertEqual(len(table.rows), 1)
        self.assertEqual(report["applied"][0]["record_id"], "rec1")

    def test_write_is_idempotent_against_existing_table(self) -> None:
        table = _FakeQcTable(existing=("fh1",))
        report = upsert_qc_report(build_qc_report_rows([_finding()]), transport=table, write=True)
        self.assertEqual(report["summary"]["written"], 0)
        self.assertEqual(table.rows, [])


class LoadFindingsTests(unittest.TestCase):
    def test_loads_from_findings_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "findings.json"
            path.write_text(json.dumps({"findings": [_finding()]}), encoding="utf-8")
            findings = load_findings(path)
            self.assertEqual(len(findings), 1)


if __name__ == "__main__":
    unittest.main()
