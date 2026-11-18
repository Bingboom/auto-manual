# -*- coding: utf-8 -*-
"""Guards for the nightly content backup, above all its confidentiality boundary.

The product-matrix export carries internal product facts and project numbers.
auto-manual is public and its workflow artifacts are downloadable, so the
export (and the artifact holding it) may only ever run in the private
Hello-Docs repository, and must not echo CLI output into the log.
"""
from __future__ import annotations

import itertools
import re
import unittest
from pathlib import Path

import yaml

from tests.test_helpers import step_uses_action

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "phase2-content-backup.yml"
PRIVATE_GATE = "${{ github.repository == 'Bingboom/Hello-Docs' }}"
EXPORT_IDS = ("export_business", "export_tm", "export_matrix")


_TERM = re.compile(r"^steps\.(\w+)\.outcome (==|!=) '(\w+)'$")
OUTCOMES = ("success", "failure", "skipped")


def _evaluate(condition: str, outcomes: dict[str, str]) -> bool:
    """Evaluate a pure-`&&` or pure-`||` chain of `steps.<id>.outcome ==/!= '<v>'` terms."""
    joiner = "&&" if "&&" in condition else "||"
    results = []
    for term in condition.split(joiner):
        match = _TERM.match(term.strip())
        assert match, f"unsupported condition term: {term!r}"
        step_id, op, value = match.groups()
        results.append((outcomes[step_id] == value) == (op == "=="))
    return all(results) if joiner == "&&" else any(results)


def _load() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


class Phase2ContentBackupWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = _load()
        self.job = self.workflow["jobs"]["backup"]
        self.steps = self.job["steps"]
        self.by_id = {s["id"]: s for s in self.steps if "id" in s}

    def test_triggers_are_schedule_and_dispatch_only(self) -> None:
        # PyYAML reads the bare `on:` key as True.
        triggers = self.workflow.get("on", self.workflow.get(True))
        self.assertEqual({"schedule", "workflow_dispatch"}, set(triggers))

    def test_job_and_matrix_step_are_gated_to_the_private_repository(self) -> None:
        self.assertEqual(PRIVATE_GATE, self.job["if"])
        self.assertEqual(PRIVATE_GATE, self.by_id["export_matrix"]["if"])

    def test_matrix_export_uses_its_manifest_secret_and_withholds_errors(self) -> None:
        run = self.by_id["export_matrix"]["run"]
        self.assertIn("--manifest bitable_schema/product_matrix_base_manifest.json", run)
        self.assertIn("--base-token-env FEISHU_PUBLISHED_DOCS_BASE_TOKEN", run)
        self.assertIn("--label product_matrix", run)
        self.assertIn("--withhold-error-detail", run)
        self.assertIn("--projected-read", run)
        self.assertEqual("${{ secrets.FEISHU_PUBLISHED_DOCS_BASE_TOKEN }}",
                         self.job["env"]["FEISHU_PUBLISHED_DOCS_BASE_TOKEN"])
        self.assertTrue(Path(WORKFLOW.parents[2], "bitable_schema", "product_matrix_base_manifest.json").is_file())

    def test_every_export_keeps_pipefail_and_continue_on_error(self) -> None:
        for step_id in EXPORT_IDS:
            with self.subTest(step=step_id):
                step = self.by_id[step_id]
                self.assertEqual("bash", step["shell"])
                self.assertTrue(step["continue-on-error"])
                self.assertIn("--out backup_out", step["run"])

    def test_sentinel_and_final_failure_watch_every_export(self) -> None:
        failure_steps = [s for s in self.steps if "outcome == 'failure'" in str(s.get("if", ""))]
        recovery = next(s for s in self.steps if s.get("name") == "Close tracking issue on recovery")
        self.assertEqual(2, len(failure_steps))
        for step_id in EXPORT_IDS:
            with self.subTest(step=step_id):
                for step in failure_steps:
                    self.assertIn(f"steps.{step_id}.outcome == 'failure'", step["if"])
                self.assertIn(f"steps.{step_id}.outcome", recovery["if"])

    def test_sentinel_outcome_semantics(self) -> None:
        """Open on any failure; close when every export that ran succeeded, a skipped matrix step included."""
        opener = next(s for s in self.steps if s.get("name") == "Open or update tracking issue on failure")
        closer = next(s for s in self.steps if s.get("name") == "Close tracking issue on recovery")
        for combo in itertools.product(OUTCOMES, repeat=3):
            outcomes = dict(zip(EXPORT_IDS, combo, strict=True))
            with self.subTest(**outcomes):
                business, tm, matrix = combo
                any_failed = "failure" in combo
                self.assertEqual(any_failed, _evaluate(opener["if"], outcomes))
                expected_close = business == "success" and tm == "success" and matrix in ("success", "skipped")
                self.assertEqual(expected_close, _evaluate(closer["if"], outcomes))
                self.assertFalse(any_failed and _evaluate(closer["if"], outcomes))

    def test_one_artifact_with_the_restore_window(self) -> None:
        uploads = [s for s in self.steps if step_uses_action(s, "actions/upload-artifact")]
        self.assertEqual(1, len(uploads))
        self.assertEqual("backup_out/", uploads[0]["with"]["path"])
        self.assertEqual(90, uploads[0]["with"]["retention-days"])


if __name__ == "__main__":
    unittest.main()
