# -*- coding: utf-8 -*-
"""Structure guard for the Milestone K5 queue-failure sentinel.

A queue run that fails must open a tracking Issue on its own (and close it on
the next success of the same title). These tests pin the wiring so a later
workflow edit cannot silently drop the sentinel or its permission.
"""
from __future__ import annotations

import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
ACTION_PATH = REPO_ROOT / ".github" / "actions" / "queue-sentinel-issue" / "action.yml"

# workflow file -> (expected sentinel label, job id)
QUEUE_WORKFLOWS = {
    "feishu-build-queue.yml": ("queue-failure-build", "process-queue"),
    "feishu-draft-build-queue.yml": ("queue-failure-draft", "process-draft-queue"),
    "feishu-start-review.yml": ("queue-failure-start-review", "process-review-start"),
}


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


class SentinelActionTests(unittest.TestCase):
    def test_action_declares_the_contract_inputs(self):
        action = _load(ACTION_PATH)
        self.assertEqual(
            {"job-status", "label", "title", "details"} - set(action["inputs"]), set())
        for name in ("job-status", "label", "title"):
            self.assertTrue(action["inputs"][name].get("required"), name)

    def test_action_opens_on_failure_and_closes_on_success_only(self):
        steps = _load(ACTION_PATH)["runs"]["steps"]
        conditions = [s.get("if", "") for s in steps]
        self.assertTrue(any("== 'failure'" in c for c in conditions),
                        "no open-on-failure step")
        self.assertTrue(any("== 'success'" in c for c in conditions),
                        "no close-on-success step")
        # cancelled runs are not incidents: nothing may trigger on any other status
        for cond in conditions:
            self.assertTrue("== 'failure'" in cond or "== 'success'" in cond, cond)

    def test_failure_body_names_the_writeback_divergence_case(self):
        text = ACTION_PATH.read_text(encoding="utf-8")
        self.assertIn("writeback", text)


class QueueWorkflowWiringTests(unittest.TestCase):
    def _workflow(self, filename: str) -> dict:
        return _load(REPO_ROOT / ".github" / "workflows" / filename)

    def test_every_queue_workflow_wires_the_sentinel(self):
        for filename, (label, job_id) in QUEUE_WORKFLOWS.items():
            with self.subTest(workflow=filename):
                wf = self._workflow(filename)
                self.assertEqual(wf["permissions"].get("issues"), "write",
                                 f"{filename} lacks issues: write")
                steps = wf["jobs"][job_id]["steps"]
                sentinel = [s for s in steps
                            if "queue-sentinel-issue" in str(s.get("uses", ""))]
                self.assertEqual(len(sentinel), 1, f"{filename}: expected one sentinel step")
                step = sentinel[0]
                self.assertEqual(step.get("if"), "always()",
                                 f"{filename}: sentinel must run on every outcome")
                self.assertIs(step, steps[-1],
                              f"{filename}: sentinel must be the last step so it sees the job outcome")
                with_ = step.get("with", {})
                self.assertEqual(with_.get("label"), label)
                self.assertIn("job.status", str(with_.get("job-status")))
                self.assertIn("queue_record_id", str(with_.get("title")),
                              f"{filename}: title must carry the record_id for per-record lifecycle")
                self.assertIn("record_id", str(with_.get("details", "")))

    def test_sentinel_labels_are_distinct(self):
        labels = [label for label, _ in QUEUE_WORKFLOWS.values()]
        self.assertEqual(len(labels), len(set(labels)))


if __name__ == "__main__":
    unittest.main()
