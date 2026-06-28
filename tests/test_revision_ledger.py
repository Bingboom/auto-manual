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


_REVIEW_REL = "docs/_review/JE-1000F/US/en/page/01_overview.rst"


def _write_review(root: Path, body: str) -> None:
    path = root / _REVIEW_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


class TestRevisionLedgerReconcile(unittest.TestCase):
    def _ingest(self, root: Path, report: dict | None = None) -> Path:
        ledger = root / "ledger.jsonl"
        revision_ledger.ingest_report(report or _report(), ledger_path=ledger)
        return ledger

    def test_reviewer_text_present_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_review(root, "Charge the battery fully before first use.\n")
            ledger = self._ingest(root)
            summary = revision_ledger.reconcile(
                ledger, root=root, merge_meta={"merged_pr": "#499"}
            )
            self.assertEqual(summary["rows_reconciled"], 1)
            row = revision_ledger.load_ledger(ledger)[0]
            self.assertEqual(row["final_status"], revision_ledger.ACCEPTED_STATUS)
            self.assertEqual(row["final_text"], "Charge the battery fully before first use.")
            self.assertEqual(row["merged_pr"], "#499")

    def test_machine_text_still_present_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_review(root, "Charge the battery.\n")
            ledger = self._ingest(root)
            revision_ledger.reconcile(ledger, root=root)
            row = revision_ledger.load_ledger(ledger)[0]
            self.assertEqual(row["final_status"], revision_ledger.REJECTED_STATUS)
            self.assertEqual(row["final_text"], "Charge the battery.")

    def test_neither_text_present_is_edited_further(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_review(root, "Top up the cells before initial operation.\n")
            ledger = self._ingest(root)
            revision_ledger.reconcile(ledger, root=root)
            row = revision_ledger.load_ledger(ledger)[0]
            self.assertEqual(row["final_status"], revision_ledger.EDITED_STATUS)
            self.assertIsNone(row["final_text"])

    def test_missing_source_stays_pending(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)  # no review file written
            ledger = self._ingest(root)
            summary = revision_ledger.reconcile(ledger, root=root)
            self.assertEqual(summary["rows_reconciled"], 0)
            self.assertEqual(summary["verdicts"].get(revision_ledger.SOURCE_MISSING_STATUS), 1)
            row = revision_ledger.load_ledger(ledger)[0]
            self.assertEqual(row["final_status"], revision_ledger.PENDING_STATUS)

    def test_reconcile_is_idempotent_and_skips_decided_rows(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_review(root, "Charge the battery fully before first use.\n")
            ledger = self._ingest(root)
            revision_ledger.reconcile(ledger, root=root)
            # Source now changes, but a decided row must not be re-evaluated.
            _write_review(root, "Charge the battery.\n")
            second = revision_ledger.reconcile(ledger, root=root)
            self.assertEqual(second["rows_reconciled"], 0)
            row = revision_ledger.load_ledger(ledger)[0]
            self.assertEqual(row["final_status"], revision_ledger.ACCEPTED_STATUS)

    def test_force_re_evaluates_decided_rows(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_review(root, "Charge the battery fully before first use.\n")
            ledger = self._ingest(root)
            revision_ledger.reconcile(ledger, root=root)
            _write_review(root, "Charge the battery.\n")
            forced = revision_ledger.reconcile(ledger, root=root, force=True)
            self.assertEqual(forced["rows_reconciled"], 1)
            row = revision_ledger.load_ledger(ledger)[0]
            self.assertEqual(row["final_status"], revision_ledger.REJECTED_STATUS)

    def test_deletion_proposal_accepted_when_text_gone(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_review(root, "Unrelated content only.\n")
            report = _report()
            report["deltas"][0]["change_type"] = "delete"
            report["deltas"][0]["new_text"] = ""
            ledger = self._ingest(root, report)
            revision_ledger.reconcile(ledger, root=root)
            row = revision_ledger.load_ledger(ledger)[0]
            self.assertEqual(row["final_status"], revision_ledger.ACCEPTED_STATUS)

    def test_cli_reconcile_command(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_review(root, "Charge the battery fully before first use.\n")
            report_path = root / "report.json"
            report_path.write_text(json.dumps(_report()), encoding="utf-8")
            ledger = root / "ledger.jsonl"
            revision_ledger.main(["ingest", "--report", str(report_path), "--ledger", str(ledger)])
            rc = revision_ledger.main(
                ["reconcile", "--ledger", str(ledger), "--root", str(root), "--merged-pr", "#499"]
            )
            self.assertEqual(rc, 0)
            row = revision_ledger.load_ledger(ledger)[0]
            self.assertEqual(row["final_status"], revision_ledger.ACCEPTED_STATUS)


def _row(**overrides: object) -> dict:
    row = {
        "final_status": revision_ledger.ACCEPTED_STATUS,
        "route_class": "repo_review_text",
        "source_path": _REVIEW_REL,
        "machine_text": "old",
        "final_text": "new",
        "reviewer_text": "new",
        "model": "JE-1000F",
        "region": "US",
        "lang": "en",
        "delta_hash": "h",
    }
    row.update(overrides)
    return row


class TestRevisionLedgerStats(unittest.TestCase):
    def test_summarize_counts_and_acceptance_rate(self) -> None:
        rows = [
            _row(final_status=revision_ledger.ACCEPTED_STATUS),
            _row(final_status=revision_ledger.REJECTED_STATUS),
            _row(final_status=revision_ledger.EDITED_STATUS),
            _row(final_status=revision_ledger.PENDING_STATUS),
        ]
        summary = revision_ledger.summarize(rows)
        self.assertEqual(summary["total_rows"], 4)
        self.assertEqual(summary["decided"], 3)
        self.assertEqual(summary["by_status"][revision_ledger.ACCEPTED_STATUS], 1)
        self.assertAlmostEqual(summary["acceptance_rate"], round(1 / 3, 4))

    def test_summarize_per_route_class_and_top_sources(self) -> None:
        rows = [
            _row(route_class="repo_review_text", source_path="a.rst"),
            _row(route_class="repo_review_text", source_path="a.rst"),
            _row(
                route_class="repo_template_text",
                source_path="b.rst",
                final_status=revision_ledger.REJECTED_STATUS,
            ),
        ]
        summary = revision_ledger.summarize(rows)
        self.assertEqual(summary["by_route_class"]["repo_review_text"]["acceptance_rate"], 1.0)
        self.assertEqual(summary["by_route_class"]["repo_template_text"]["acceptance_rate"], 0.0)
        self.assertEqual(summary["top_corrected_sources"][0], {"source_path": "a.rst", "corrections": 2})

    def test_summarize_empty_ledger(self) -> None:
        summary = revision_ledger.summarize([])
        self.assertEqual(summary["total_rows"], 0)
        self.assertIsNone(summary["acceptance_rate"])


class TestRevisionLedgerExport(unittest.TestCase):
    def test_export_emits_accepted_correction_pairs_only(self) -> None:
        rows = [
            _row(final_status=revision_ledger.ACCEPTED_STATUS, machine_text="x", final_text="y"),
            _row(final_status=revision_ledger.REJECTED_STATUS, machine_text="x", final_text="x"),
            _row(final_status=revision_ledger.EDITED_STATUS, machine_text="x", final_text=None),
            _row(final_status=revision_ledger.PENDING_STATUS),
        ]
        pairs = revision_ledger.export_pairs(rows)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["input"], "x")
        self.assertEqual(pairs[0]["target"], "y")
        self.assertEqual(pairs[0]["verdict"], revision_ledger.ACCEPTED_STATUS)

    def test_export_skips_accepted_noop_pairs(self) -> None:
        rows = [_row(final_status=revision_ledger.ACCEPTED_STATUS, machine_text="same", final_text="same")]
        self.assertEqual(revision_ledger.export_pairs(rows), [])

    def test_export_include_rejected_adds_no_change_examples(self) -> None:
        rows = [_row(final_status=revision_ledger.REJECTED_STATUS, machine_text="x", final_text="x")]
        pairs = revision_ledger.export_pairs(rows, include_rejected=True)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["verdict"], revision_ledger.REJECTED_STATUS)

    def test_cli_stats_and_export(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "ledger.jsonl"
            revision_ledger.write_ledger(
                [_row(final_status=revision_ledger.ACCEPTED_STATUS, machine_text="x", final_text="y")],
                ledger,
            )
            self.assertEqual(revision_ledger.main(["stats", "--ledger", str(ledger)]), 0)
            out = Path(td) / "pairs.jsonl"
            rc = revision_ledger.main(
                ["export", "--ledger", str(ledger), "--out", str(out)]
            )
            self.assertEqual(rc, 0)
            exported = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(exported[0]["target"], "y")


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
