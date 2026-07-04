from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import flow_dashboard


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _ledger_row(**overrides: object) -> dict:
    row = {
        "delta_hash": overrides.get("delta_hash", "hash-1"),
        "final_status": "pending",
        "generated_at": "2026-07-03T10:00:00+00:00",
        "machine_text": "旧文案",
        "reviewer_text": "新文案",
        "run_id": "run-1",
    }
    row.update(overrides)
    return row


class TestRevisionMetrics(unittest.TestCase):
    def test_reflow_metrics_empty_ledger_reports_no_data(self) -> None:
        metrics = flow_dashboard.reflow_metrics([], missing=[])
        self.assertEqual({m["status"] for m in metrics}, {"no_data"})

    def test_reflow_rate_counts_accepted_over_total(self) -> None:
        rows = [
            _ledger_row(delta_hash="a", final_status="accepted"),
            _ledger_row(delta_hash="b", final_status="accepted"),
            _ledger_row(delta_hash="c", final_status="pending"),
            _ledger_row(delta_hash="d", final_status="rejected"),
        ]
        ops, value = flow_dashboard.reflow_metrics(rows, missing=[])
        self.assertEqual(ops["key"], "reflow_rate")
        self.assertEqual(ops["value"], 0.5)
        self.assertEqual(value["value"], 4)
        self.assertEqual(ops["monthly"], {"2026-07": 4})

    def test_ledger_merge_dedupes_by_delta_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger_a = Path(tmp) / "a.jsonl"
            ledger_b = Path(tmp) / "b.jsonl"
            _write_jsonl(ledger_a, [_ledger_row(delta_hash="x"), _ledger_row(delta_hash="y")])
            _write_jsonl(ledger_b, [_ledger_row(delta_hash="y"), _ledger_row(delta_hash="z")])
            rows, missing = flow_dashboard.load_revision_ledgers([ledger_a, ledger_b])
        self.assertEqual(len(rows), 3)
        self.assertEqual(missing, [])

    def test_missing_ledger_paths_are_reported_not_fatal(self) -> None:
        rows, missing = flow_dashboard.load_revision_ledgers([Path("/nonexistent/ledger.jsonl")])
        self.assertEqual(rows, [])
        self.assertEqual(len(missing), 1)

    def test_second_revision_rate_flags_repeated_targets(self) -> None:
        rows = [
            _ledger_row(delta_hash="a", machine_text="同一句", run_id="run-1"),
            _ledger_row(delta_hash="b", machine_text="同一句", run_id="run-2"),
            _ledger_row(delta_hash="c", machine_text="另一句", run_id="run-1"),
        ]
        metric = flow_dashboard.second_revision_metric(rows)
        self.assertEqual(metric["value"], 0.5)
        self.assertEqual(metric["detail"]["runs"], 2)


class TestArtifactMetrics(unittest.TestCase):
    def test_audited_pdf_metric_counts_distinct_pdfs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.jsonl"
            _write_jsonl(
                ledger,
                [
                    {"pdf": "a.pdf", "findings": 3, "recorded_at": "2026-07-03T10:00:00+00:00"},
                    {"pdf": "a.pdf", "findings": 1, "recorded_at": "2026-07-04T10:00:00+00:00"},
                    {"pdf": "b.pdf", "findings": 2, "recorded_at": "2026-08-01T10:00:00+00:00"},
                ],
            )
            metric = flow_dashboard.audited_pdf_metric(ledger)
        self.assertEqual(metric["value"], 2)
        self.assertEqual(metric["detail"]["findings_total"], 6)
        self.assertEqual(metric["monthly"], {"2026-07": 2, "2026-08": 1})

    def test_audited_pdf_metric_without_ledger_is_no_data(self) -> None:
        metric = flow_dashboard.audited_pdf_metric(Path("/nonexistent/ledger.jsonl"))
        self.assertEqual(metric["status"], "no_data")

    def test_coverage_metric_reads_family_configs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            configs = Path(tmp)
            (configs / "config.us.yaml").write_text(
                "build:\n  languages: [en, fr]\n  targets:\n"
                "    - model: JE-1000F\n      region: US\n",
                encoding="utf-8",
            )
            (configs / "config.kr.yaml").write_text(
                "build:\n  languages: [ko]\n  targets:\n"
                "    - model: JE-1000F\n      region: KR\n",
                encoding="utf-8",
            )
            metric = flow_dashboard.coverage_metric(configs)
        self.assertEqual(metric["detail"]["models"], ["JE-1000F"])
        self.assertEqual(metric["detail"]["regions"], ["KR", "US"])
        self.assertEqual(metric["detail"]["languages"], ["en", "fr", "ko"])

    def test_time_saved_needs_baseline_without_operator_number(self) -> None:
        metric = flow_dashboard.time_saved_metric(Path("/nonexistent"), None)
        self.assertEqual(metric["status"], "needs_baseline")

    def test_tm_candidates_metric_counts_jsonl_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger_dir = Path(tmp)
            _write_jsonl(ledger_dir / "tm_candidates.jsonl", [{"a": 1}, {"b": 2}])
            metric = flow_dashboard.tm_candidates_metric(ledger_dir)
        self.assertEqual(metric["value"], 2)


class TestDashboardAssembly(unittest.TestCase):
    def test_build_dashboard_splits_faces_and_renders_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            configs = root / "configs"
            configs.mkdir()
            (configs / "config.us.yaml").write_text(
                "build:\n  languages: [en]\n  targets:\n"
                "    - model: JE-1000F\n      region: US\n",
                encoding="utf-8",
            )
            revision = root / "reports" / "revision_ledger" / "ledger.jsonl"
            _write_jsonl(revision, [_ledger_row(final_status="accepted")])
            dashboard = flow_dashboard.build_dashboard(
                base_root=root,
                revision_ledgers=[revision],
                tm_ledger=root / "missing-tm.jsonl",
                pdf_ledger=root / "missing-pdf.jsonl",
                configs_dir=configs,
                baseline_hours=None,
                generated_at="2026-07-03T12:00:00+00:00",
            )
        ops_keys = [m["key"] for m in dashboard["faces"]["ops"]]
        value_keys = [m["key"] for m in dashboard["faces"]["value"]]
        self.assertIn("reflow_rate", ops_keys)
        self.assertIn("template_corpus_coverage", ops_keys)
        self.assertIn("audited_pdf_count", value_keys)
        self.assertIn("time_saved", value_keys)
        markdown = flow_dashboard.render_markdown(dashboard)
        self.assertIn("运营面", markdown)
        self.assertIn("价值面", markdown)
        self.assertIn("暂无数据", markdown)
        self.assertIn("100.0%", markdown)  # reflow rate: 1 accepted / 1 total


if __name__ == "__main__":
    unittest.main()
