from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import tm_hit_rate


def _report(**overrides: object) -> dict:
    report = {
        "input_docx": "/work/manual_en.docx",
        "output_docx": "/work/manual_ko.docx",
        "source_lang": "en",
        "target_lang": "ko",
        "change_count": 3,
        "units_total": 40,
        "units_matched": 25,
        "hit_rate": 0.625,
        "changes": [
            {"mode": "full", "source": "Charge the battery.", "row_key": "tm-1"},
            {"mode": "full", "source": "Do not cover the vents.", "row_key": "tm-2"},
            {"mode": "split", "source": "Two sentences. Here.", "matched_units": []},
        ],
    }
    report.update(overrides)
    return report


class TestEntryFromReport(unittest.TestCase):
    def test_entry_carries_counters_and_rate(self) -> None:
        entry = tm_hit_rate.entry_from_report(_report(), recorded_at="2026-07-02T00:00:00+00:00")
        self.assertEqual(entry["units_total"], 40)
        self.assertEqual(entry["units_matched"], 25)
        self.assertEqual(entry["hit_rate"], 0.625)
        self.assertEqual(entry["source_lang"], "en")
        self.assertEqual(entry["target_lang"], "ko")
        self.assertEqual(entry["recorded_at"], "2026-07-02T00:00:00+00:00")
        self.assertTrue(entry["run_key"])

    def test_legacy_report_without_counters_yields_null_rate(self) -> None:
        report = _report()
        for key in ("units_total", "units_matched", "hit_rate"):
            report.pop(key)
        entry = tm_hit_rate.entry_from_report(report)
        self.assertIsNone(entry["hit_rate"])
        self.assertIsNone(entry["units_total"])

    def test_rate_recomputed_from_counters_not_trusted_from_report(self) -> None:
        entry = tm_hit_rate.entry_from_report(_report(hit_rate=0.99))
        self.assertEqual(entry["hit_rate"], 0.625)

    def test_zero_units_yields_null_rate(self) -> None:
        entry = tm_hit_rate.entry_from_report(_report(units_total=0, units_matched=0))
        self.assertIsNone(entry["hit_rate"])


class TestIngest(unittest.TestCase):
    def test_ingest_appends_one_entry(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "ledger.jsonl"
            summary = tm_hit_rate.ingest_report(_report(), ledger_path=ledger)
            self.assertEqual(summary["written"], 1)
            rows = tm_hit_rate.load_ledger(ledger)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["hit_rate"], 0.625)

    def test_reingest_same_report_is_noop(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "ledger.jsonl"
            tm_hit_rate.ingest_report(_report(), ledger_path=ledger)
            summary = tm_hit_rate.ingest_report(_report(), ledger_path=ledger)
            self.assertEqual(summary["written"], 0)
            self.assertEqual(summary["skipped"], 1)
            self.assertEqual(len(tm_hit_rate.load_ledger(ledger)), 1)

    def test_different_run_lands_as_new_row(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "ledger.jsonl"
            tm_hit_rate.ingest_report(_report(), ledger_path=ledger)
            tm_hit_rate.ingest_report(
                _report(units_matched=30, hit_rate=0.75), ledger_path=ledger
            )
            self.assertEqual(len(tm_hit_rate.load_ledger(ledger)), 2)


class TestSummarize(unittest.TestCase):
    def test_overall_and_per_pair_rates(self) -> None:
        rows = [
            {"source_lang": "en", "target_lang": "ko", "units_total": 40, "units_matched": 25},
            {"source_lang": "en", "target_lang": "ko", "units_total": 10, "units_matched": 10},
            {"source_lang": "en", "target_lang": "de", "units_total": 50, "units_matched": 20},
        ]
        summary = tm_hit_rate.summarize(rows)
        self.assertEqual(summary["runs"], 3)
        self.assertEqual(summary["units_total"], 100)
        self.assertEqual(summary["units_matched"], 55)
        self.assertEqual(summary["hit_rate"], 0.55)
        self.assertEqual(summary["by_language_pair"]["en->ko"]["hit_rate"], 0.7)
        self.assertEqual(summary["by_language_pair"]["en->de"]["hit_rate"], 0.4)

    def test_counterless_rows_are_reported_not_averaged(self) -> None:
        rows = [
            {"source_lang": "en", "target_lang": "ko", "units_total": 10, "units_matched": 5},
            {"source_lang": "en", "target_lang": "ko"},
        ]
        summary = tm_hit_rate.summarize(rows)
        self.assertEqual(summary["runs_without_counters"], 1)
        self.assertEqual(summary["hit_rate"], 0.5)

    def test_empty_ledger(self) -> None:
        summary = tm_hit_rate.summarize([])
        self.assertIsNone(summary["hit_rate"])
        self.assertEqual(summary["runs"], 0)


class TestCli(unittest.TestCase):
    def test_cli_ingest_then_stats(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            report_path = Path(td) / "run.report.json"
            report_path.write_text(json.dumps(_report()), encoding="utf-8")
            ledger = Path(td) / "ledger.jsonl"
            rc = tm_hit_rate.main(
                ["ingest", "--report", str(report_path), "--ledger", str(ledger)]
            )
            self.assertEqual(rc, 0)
            self.assertEqual(tm_hit_rate.main(["stats", "--ledger", str(ledger)]), 0)
            self.assertEqual(len(tm_hit_rate.load_ledger(ledger)), 1)


if __name__ == "__main__":
    unittest.main()
