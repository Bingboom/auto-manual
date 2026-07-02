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


def _source_table_report(**overrides: object) -> dict:
    report = _report()
    delta = report["deltas"][0]
    delta["route_class"] = "source_table_suggestion"
    delta["old_text"] = "230V"
    delta["new_text"] = "240V"
    report.update(overrides)
    return report


def _apply_report(*, plan: list | None = None, applied: list | None = None) -> dict:
    return {"plan": plan or [], "applied": applied or []}


class TestRevisionLedgerSourceTableReconcile(unittest.TestCase):
    def _ingest_source_table(self, root: Path) -> Path:
        ledger = root / "ledger.jsonl"
        revision_ledger.ingest_report(_source_table_report(), ledger_path=ledger)
        return ledger

    def test_written_to_table_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ledger = self._ingest_source_table(root)
            report = _apply_report(applied=[{"delta_hash": "hash-a", "status": "written"}])
            summary = revision_ledger.reconcile(ledger, root=root, apply_report=report)
            self.assertEqual(summary["rows_reconciled"], 1)
            row = revision_ledger.load_ledger(ledger)[0]
            self.assertEqual(row["final_status"], revision_ledger.ACCEPTED_STATUS)
            self.assertEqual(row["final_text"], "240V")

    def test_already_applied_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ledger = self._ingest_source_table(root)
            report = _apply_report(applied=[{"delta_hash": "hash-a", "status": "already_applied"}])
            revision_ledger.reconcile(ledger, root=root, apply_report=report)
            row = revision_ledger.load_ledger(ledger)[0]
            self.assertEqual(row["final_status"], revision_ledger.ACCEPTED_STATUS)

    def test_not_approved_skip_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ledger = self._ingest_source_table(root)
            report = _apply_report(
                plan=[{"delta_hash": "hash-a", "action": "skip", "reason": "not approved by a human"}]
            )
            revision_ledger.reconcile(ledger, root=root, apply_report=report)
            row = revision_ledger.load_ledger(ledger)[0]
            self.assertEqual(row["final_status"], revision_ledger.REJECTED_STATUS)
            self.assertEqual(row["final_text"], "230V")

    def test_drift_abstained_is_source_table_abstained(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ledger = self._ingest_source_table(root)
            report = _apply_report(applied=[{"delta_hash": "hash-a", "status": "drift_abstained"}])
            revision_ledger.reconcile(ledger, root=root, apply_report=report)
            row = revision_ledger.load_ledger(ledger)[0]
            self.assertEqual(row["final_status"], revision_ledger.SOURCE_TABLE_ABSTAINED_STATUS)
            self.assertIsNone(row["final_text"])

    def test_abstain_skip_reason_is_source_table_abstained(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ledger = self._ingest_source_table(root)
            report = _apply_report(
                plan=[{"delta_hash": "hash-a", "action": "skip", "reason": "record_id unresolved (exact-or-abstain)"}]
            )
            revision_ledger.reconcile(ledger, root=root, apply_report=report)
            row = revision_ledger.load_ledger(ledger)[0]
            self.assertEqual(row["final_status"], revision_ledger.SOURCE_TABLE_ABSTAINED_STATUS)

    def test_missing_from_apply_report_stays_pending(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ledger = self._ingest_source_table(root)
            summary = revision_ledger.reconcile(ledger, root=root, apply_report=_apply_report())
            self.assertEqual(summary["rows_reconciled"], 0)
            row = revision_ledger.load_ledger(ledger)[0]
            self.assertEqual(row["final_status"], revision_ledger.PENDING_STATUS)

    def test_applied_status_wins_over_plan(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ledger = self._ingest_source_table(root)
            report = _apply_report(
                plan=[{"delta_hash": "hash-a", "action": "apply", "value": "240V"}],
                applied=[{"delta_hash": "hash-a", "status": "written"}],
            )
            revision_ledger.reconcile(ledger, root=root, apply_report=report)
            row = revision_ledger.load_ledger(ledger)[0]
            self.assertEqual(row["final_status"], revision_ledger.ACCEPTED_STATUS)

    def test_mixed_ledger_routes_each_class_to_its_source(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_review(root, "Charge the battery fully before first use.\n")
            ledger = root / "ledger.jsonl"
            # Class R row (review text) and Class D row (online table), distinct hashes.
            revision_ledger.ingest_report(_report(), ledger_path=ledger)
            st = _source_table_report(run_id="run-st")
            st["deltas"][0]["delta_hash"] = "hash-st"
            revision_ledger.ingest_report(st, ledger_path=ledger)
            report = _apply_report(applied=[{"delta_hash": "hash-st", "status": "written"}])
            summary = revision_ledger.reconcile(ledger, root=root, apply_report=report)
            self.assertEqual(summary["rows_reconciled"], 2)
            by_hash = {r["delta_hash"]: r for r in revision_ledger.load_ledger(ledger)}
            self.assertEqual(by_hash["hash-a"]["final_status"], revision_ledger.ACCEPTED_STATUS)
            self.assertEqual(by_hash["hash-st"]["final_status"], revision_ledger.ACCEPTED_STATUS)

    def test_cli_reconcile_with_apply_report(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ledger = root / "ledger.jsonl"
            report_path = root / "report.json"
            report_path.write_text(json.dumps(_source_table_report()), encoding="utf-8")
            revision_ledger.main(["ingest", "--report", str(report_path), "--ledger", str(ledger)])
            apply_path = root / "apply.json"
            apply_path.write_text(
                json.dumps(_apply_report(applied=[{"delta_hash": "hash-a", "status": "written"}])),
                encoding="utf-8",
            )
            rc = revision_ledger.main(
                ["reconcile", "--ledger", str(ledger), "--root", str(root), "--apply-report", str(apply_path)]
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


class TestRevisionLedgerSimilarityVerdict(unittest.TestCase):
    """Fuzzy layer: punctuation/line-break edits must not misclassify."""

    def test_reviewer_text_with_punctuation_tweak_is_accepted(self) -> None:
        # Landed text differs from the proposal by one comma: exact containment
        # fails, the similarity layer should still call it accepted.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_review(root, "Charge the battery fully, before first use.\n")
            ledger = root / "ledger.jsonl"
            revision_ledger.ingest_report(_report(), ledger_path=ledger)
            revision_ledger.reconcile(ledger, root=root)
            row = revision_ledger.load_ledger(ledger)[0]
            self.assertEqual(row["final_status"], revision_ledger.ACCEPTED_STATUS)

    def test_machine_text_with_tiny_tweak_is_rejected(self) -> None:
        # The machine text survived with a trailing-word tweak and the reviewer
        # proposal is nowhere: near-match on machine text -> rejected.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_review(root, "Please charge the battery now.\n")
            report = _report()
            report["deltas"][0]["old_text"] = "Please charge the battery."
            report["deltas"][0]["new_text"] = "Top up the cells before initial operation."
            ledger = root / "ledger.jsonl"
            revision_ledger.ingest_report(report, ledger_path=ledger)
            revision_ledger.reconcile(ledger, root=root)
            row = revision_ledger.load_ledger(ledger)[0]
            self.assertEqual(row["final_status"], revision_ledger.REJECTED_STATUS)

    def test_short_needle_stays_containment_only(self) -> None:
        # Below MIN_FUZZY_LENGTH the ratio is noise; a near-miss short string
        # must not fuzzy-accept.
        row = {"reviewer_text": "AC 100W", "machine_text": "AC 200W"}
        haystack = "the port supports ac 150w output"
        self.assertEqual(
            revision_ledger.classify_verdict(row, haystack),
            revision_ledger.EDITED_STATUS,
        )

    def test_deletion_proposal_with_near_present_machine_text_is_rejected(self) -> None:
        row = {"reviewer_text": "", "machine_text": "Never cover the vents while charging."}
        haystack = "warning: never cover the vents, while charging."
        normalized_hay = haystack  # already lowercase/plain
        self.assertEqual(
            revision_ledger.classify_verdict(row, normalized_hay),
            revision_ledger.REJECTED_STATUS,
        )


def _git(root: Path, *args: str, env: dict | None = None) -> None:
    import subprocess

    base_env = {
        "GIT_AUTHOR_NAME": "Rev Reviewer",
        "GIT_AUTHOR_EMAIL": "rev@example.invalid",
        "GIT_COMMITTER_NAME": "Rev Reviewer",
        "GIT_COMMITTER_EMAIL": "rev@example.invalid",
        "PATH": __import__("os").environ.get("PATH", ""),
        "HOME": __import__("os").environ.get("HOME", ""),
    }
    if env:
        base_env.update(env)
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, env=base_env)


class TestRevisionLedgerAutoMergeMeta(unittest.TestCase):
    def test_auto_reconcile_stamps_commit_author_and_pr(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_review(root, "Charge the battery fully before first use.\n")
            _git(root, "init", "-q")
            _git(root, "add", ".")
            _git(root, "commit", "-q", "-m", "feat(review): land reviewer edits (#742)")
            ledger = root / "ledger.jsonl"
            revision_ledger.ingest_report(_report(), ledger_path=ledger)
            summary = revision_ledger.reconcile(ledger, root=root, auto_merge_meta=True)
            self.assertEqual(summary["rows_reconciled"], 1)
            row = revision_ledger.load_ledger(ledger)[0]
            self.assertEqual(row["final_status"], revision_ledger.ACCEPTED_STATUS)
            self.assertEqual(row["merged_pr"], "#742")
            self.assertEqual(row["reviewer"], "Rev Reviewer")
            self.assertTrue(row["merged_commit"])
            self.assertTrue(row["merged_at"])

    def test_explicit_merge_meta_wins_over_auto(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_review(root, "Charge the battery fully before first use.\n")
            _git(root, "init", "-q")
            _git(root, "add", ".")
            _git(root, "commit", "-q", "-m", "feat(review): land reviewer edits (#742)")
            ledger = root / "ledger.jsonl"
            revision_ledger.ingest_report(_report(), ledger_path=ledger)
            revision_ledger.reconcile(
                ledger,
                root=root,
                merge_meta={"merged_pr": "#900"},
                auto_merge_meta=True,
            )
            row = revision_ledger.load_ledger(ledger)[0]
            self.assertEqual(row["merged_pr"], "#900")
            self.assertEqual(row["reviewer"], "Rev Reviewer")

    def test_auto_without_git_repo_still_reconciles_unstamped(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_review(root, "Charge the battery fully before first use.\n")
            ledger = root / "ledger.jsonl"
            revision_ledger.ingest_report(_report(), ledger_path=ledger)
            summary = revision_ledger.reconcile(ledger, root=root, auto_merge_meta=True)
            self.assertEqual(summary["rows_reconciled"], 1)
            row = revision_ledger.load_ledger(ledger)[0]
            self.assertEqual(row["final_status"], revision_ledger.ACCEPTED_STATUS)
            self.assertIsNone(row["merged_commit"])


class TestRevisionLedgerIngestPiggyback(unittest.TestCase):
    def test_cli_ingest_runs_reconcile_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_review(root, "Charge the battery fully before first use.\n")
            report_path = root / "report.json"
            report_path.write_text(json.dumps(_report()), encoding="utf-8")
            ledger = root / "ledger.jsonl"
            rc = revision_ledger.main(
                [
                    "ingest",
                    "--report",
                    str(report_path),
                    "--ledger",
                    str(ledger),
                    "--root",
                    str(root),
                ]
            )
            self.assertEqual(rc, 0)
            row = revision_ledger.load_ledger(ledger)[0]
            self.assertEqual(row["final_status"], revision_ledger.ACCEPTED_STATUS)

    def test_cli_ingest_no_reconcile_leaves_rows_pending(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_review(root, "Charge the battery fully before first use.\n")
            report_path = root / "report.json"
            report_path.write_text(json.dumps(_report()), encoding="utf-8")
            ledger = root / "ledger.jsonl"
            rc = revision_ledger.main(
                [
                    "ingest",
                    "--report",
                    str(report_path),
                    "--ledger",
                    str(ledger),
                    "--root",
                    str(root),
                    "--no-reconcile",
                ]
            )
            self.assertEqual(rc, 0)
            row = revision_ledger.load_ledger(ledger)[0]
            self.assertEqual(row["final_status"], revision_ledger.PENDING_STATUS)


class TestTmCandidates(unittest.TestCase):
    @staticmethod
    def _accepted_row(**overrides: object) -> dict:
        row = {
            "final_status": revision_ledger.ACCEPTED_STATUS,
            "route_class": revision_ledger.ROUTE_REVIEW,
            "lang": "ko",
            "delta_hash": "hash-tm-1",
            "machine_text": "기계 번역 문장.",
            "reviewer_text": "검토자가 고친 문장.",
            "final_text": "검토자가 고친 문장.",
            "row_key": "run-1:hash-tm-1",
            "run_id": "run-1",
            "source_path": "docs/_review/JE-1000F/KR/ko/page/x.rst",
            "model": "JE-1000F",
            "region": "KR",
            "merged_pr": "#600",
        }
        row.update(overrides)
        return row

    def test_accepted_row_becomes_suggestion_shaped_candidate(self) -> None:
        candidates = revision_ledger.tm_candidates([self._accepted_row()])
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["delta_hash"], "hash-tm-1")
        self.assertEqual(candidate["lang"], "ko")
        self.assertEqual(candidate["old_text"], "기계 번역 문장.")
        self.assertEqual(candidate["new_text"], "검토자가 고친 문장.")
        self.assertEqual(candidate["routing_hint"], "translation_memory")
        self.assertEqual(candidate["provenance"]["merged_pr"], "#600")

    def test_filters_non_qualifying_rows(self) -> None:
        rows = [
            self._accepted_row(final_status=revision_ledger.EDITED_STATUS),
            self._accepted_row(route_class=revision_ledger.ROUTE_SOURCE_TABLE),
            self._accepted_row(lang=None),
            self._accepted_row(delta_hash=None),
            self._accepted_row(final_text="기계 번역 문장.", machine_text="기계 번역 문장."),
        ]
        self.assertEqual(revision_ledger.tm_candidates(rows), [])

    def test_dedupes_by_delta_hash(self) -> None:
        rows = [self._accepted_row(), self._accepted_row(row_key="run-2:hash-tm-1", run_id="run-2")]
        self.assertEqual(len(revision_ledger.tm_candidates(rows)), 1)

    def test_candidates_ride_the_gated_apply_path(self) -> None:
        from tools.translation_memory_sync import apply_translation_suggestions

        candidates = revision_ledger.tm_candidates([self._accepted_row()])
        unapproved = apply_translation_suggestions(
            candidates, approved_hashes=set(), transport=None, write=False
        )
        self.assertEqual(unapproved["summary"]["apply"], 0)
        approved = apply_translation_suggestions(
            candidates, approved_hashes={"hash-tm-1"}, transport=None, write=False
        )
        self.assertEqual(approved["summary"]["apply"], 1)
        self.assertFalse(approved["external_write"])

    def test_cli_tm_candidates_then_dry_run_apply(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "ledger.jsonl"
            revision_ledger.write_ledger([self._accepted_row()], ledger)
            out = Path(td) / "tm_candidates.jsonl"
            rc = revision_ledger.main(
                ["tm-candidates", "--ledger", str(ledger), "--out", str(out)]
            )
            self.assertEqual(rc, 0)
            self.assertEqual(len(revision_ledger.load_tm_candidates(out)), 1)
            rc = revision_ledger.main(
                ["tm-apply", "--candidates", str(out), "--approve", "hash-tm-1"]
            )
            self.assertEqual(rc, 0)

    def test_cli_tm_apply_write_requires_binding(self) -> None:
        import contextlib
        import io

        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "tm_candidates.jsonl"
            revision_ledger.write_tm_candidates(
                revision_ledger.tm_candidates([self._accepted_row()]), out
            )
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                rc = revision_ledger.main(
                    ["tm-apply", "--candidates", str(out), "--approve", "hash-tm-1", "--write"]
                )
            self.assertEqual(rc, 2)
            self.assertIn("--tm-binding", stderr.getvalue())


class TestRevisionLedgerReflowRate(unittest.TestCase):
    def test_reflow_rate_counts_rows_that_left_pending(self) -> None:
        rows = [
            {"final_status": revision_ledger.ACCEPTED_STATUS},
            {"final_status": revision_ledger.REJECTED_STATUS},
            {"final_status": revision_ledger.PENDING_STATUS},
            {"final_status": revision_ledger.PENDING_STATUS},
        ]
        summary = revision_ledger.summarize(rows)
        self.assertEqual(summary["reflow_rate"], 0.5)

    def test_reflow_rate_empty_ledger_is_none(self) -> None:
        self.assertIsNone(revision_ledger.summarize([])["reflow_rate"])


if __name__ == "__main__":
    unittest.main()
