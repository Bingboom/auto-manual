from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import revision_ledger


def _report(**overrides: object) -> dict:
    report = {
        "schema_version": 1,
        "run_id": "run-123",
        "doc_type": "review",
        "doc_url": "https://example.invalid/doc",
        "source_target": {
            "path": "docs/_review/JE-1000F/US/en/page/01_overview.rst",
            "kind": "review",
        },
        "result": "DIFF",
        "metadata": {"generated_at": "2026-06-28T00:00:00Z", "git_ref": "abc1234"},
        "deltas": [
            {
                "index": 0,
                "delta_hash": "hash-a",
                "change_type": "modify",
                "route_class": "repo_review_text",
                "old_text": "Charge the battery.",
                "new_text": "Charge the battery fully before first use.",
                "location": {
                    "kind": "paragraph",
                    "line_no": 12,
                    "heading_path": ["Getting Started"],
                },
                "source_evidence": {},
                "confidence": "high",
                "semantic_review_required": False,
            }
        ],
    }
    report.update(overrides)
    return report


class TestRevisionLedgerIngest(unittest.TestCase):
    def test_ingest_writes_one_row_per_delta_with_flywheel_fields(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "ledger.jsonl"
            summary = revision_ledger.ingest_report(_report(), ledger_path=ledger)

            self.assertEqual(summary["rows_written"], 1)
            self.assertEqual(summary["deltas_seen"], 1)
            rows = revision_ledger.load_ledger(ledger)
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row["machine_text"], "Charge the battery.")
            self.assertEqual(row["reviewer_text"], "Charge the battery fully before first use.")
            self.assertEqual(row["route_class"], "repo_review_text")
            self.assertEqual(row["change_type"], "modify")
            self.assertEqual(row["final_status"], revision_ledger.PENDING_STATUS)
            self.assertIsNone(row["final_text"])

    def test_ingest_parses_model_region_lang_from_source_path(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "ledger.jsonl"
            revision_ledger.ingest_report(_report(), ledger_path=ledger)
            row = revision_ledger.load_ledger(ledger)[0]
            self.assertEqual(row["model"], "JE-1000F")
            self.assertEqual(row["region"], "US")
            self.assertEqual(row["lang"], "en")

    def test_ingest_is_idempotent_on_repeated_runs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "ledger.jsonl"
            revision_ledger.ingest_report(_report(), ledger_path=ledger)
            second = revision_ledger.ingest_report(_report(), ledger_path=ledger)

            self.assertEqual(second["rows_written"], 0)
            self.assertEqual(second["rows_skipped"], 1)
            self.assertEqual(len(revision_ledger.load_ledger(ledger)), 1)

    def test_same_correction_in_a_new_run_is_kept_as_new_row(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "ledger.jsonl"
            revision_ledger.ingest_report(_report(), ledger_path=ledger)
            revision_ledger.ingest_report(_report(run_id="run-456"), ledger_path=ledger)
            rows = revision_ledger.load_ledger(ledger)
            self.assertEqual(len(rows), 2)
            self.assertEqual({r["run_id"] for r in rows}, {"run-123", "run-456"})

    def test_no_diff_report_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "ledger.jsonl"
            summary = revision_ledger.ingest_report(
                _report(result="NO_DIFF", deltas=[]), ledger_path=ledger
            )
            self.assertEqual(summary["rows_written"], 0)
            self.assertFalse(ledger.exists())

    def test_delta_without_hash_still_keyed_by_index(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "ledger.jsonl"
            report = _report()
            report["deltas"][0].pop("delta_hash")
            revision_ledger.ingest_report(report, ledger_path=ledger)
            row = revision_ledger.load_ledger(ledger)[0]
            self.assertEqual(row["row_key"], "run-123:idx:0")
            # Re-ingest stays idempotent even without a delta_hash.
            second = revision_ledger.ingest_report(report, ledger_path=ledger)
            self.assertEqual(second["rows_written"], 0)

    def test_non_review_source_path_yields_null_target(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "ledger.jsonl"
            report = _report()
            report["source_target"]["path"] = "docs/templates/page_shared/en/safety.rst"
            revision_ledger.ingest_report(report, ledger_path=ledger)
            row = revision_ledger.load_ledger(ledger)[0]
            self.assertIsNone(row["model"])
            self.assertIsNone(row["region"])
            self.assertIsNone(row["lang"])

    def test_ingest_report_file_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            report_path = Path(td) / "report.json"
            report_path.write_text(json.dumps(_report()), encoding="utf-8")
            ledger = Path(td) / "ledger.jsonl"
            summary = revision_ledger.ingest_report_file(report_path, ledger_path=ledger)
            self.assertEqual(summary["rows_written"], 1)


class TestRevisionLedgerCli(unittest.TestCase):
    def test_cli_ingest_command(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            report_path = Path(td) / "report.json"
            report_path.write_text(json.dumps(_report()), encoding="utf-8")
            ledger = Path(td) / "ledger.jsonl"
            rc = revision_ledger.main(
                ["ingest", "--report", str(report_path), "--ledger", str(ledger)]
            )
            self.assertEqual(rc, 0)
            self.assertEqual(len(revision_ledger.load_ledger(ledger)), 1)


if __name__ == "__main__":
    unittest.main()
