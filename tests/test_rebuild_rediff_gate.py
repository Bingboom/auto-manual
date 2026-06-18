#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the rebuild+rediff idempotency gate (Milestone F, PR F5)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.cloud_doc_backport import (  # noqa: E402
    _rebuild_rediff_gate,
    build_review_run_report,
)


def _review_delta(old: str, new: str) -> dict:
    return {"route_class": "repo_review_text", "old_normalized": old, "new_normalized": new}


class RebuildRediffGateTests(unittest.TestCase):
    def test_clean_apply_passes(self) -> None:
        gate = _rebuild_rediff_gate(
            baseline_text="Old line\n",
            edited_text="New line\n",
            deltas=[_review_delta("Old line", "New line")],
            run_id="t",
        )
        self.assertTrue(gate["passed"])
        self.assertEqual(gate["unexpected"], [])
        self.assertEqual(gate["missing"], [])

    def test_collateral_change_is_unexpected(self) -> None:
        gate = _rebuild_rediff_gate(
            baseline_text="Old line\n",
            edited_text="New line\n\nStray addition\n",
            deltas=[_review_delta("Old line", "New line")],
            run_id="t",
        )
        self.assertFalse(gate["passed"])
        self.assertTrue(gate["unexpected"])

    def test_unapplied_review_delta_is_missing(self) -> None:
        gate = _rebuild_rediff_gate(
            baseline_text="Old line\n",
            edited_text="Old line\n",  # not applied
            deltas=[_review_delta("Old line", "New line")],
            run_id="t",
        )
        self.assertFalse(gate["passed"])
        self.assertTrue(gate["missing"])

    def test_deferred_class_d_delta_does_not_count_as_missing(self) -> None:
        # A non-repo_review_text delta is intentionally deferred -> not expected.
        gate = _rebuild_rediff_gate(
            baseline_text="Old line\n",
            edited_text="Old line\n",
            deltas=[{"route_class": "source_table_suggestion", "old_normalized": "Old line", "new_normalized": "New"}],
            run_id="t",
        )
        self.assertTrue(gate["passed"])


class PrReadyGateTests(unittest.TestCase):
    def _run_result(self, rebuild_passed: bool) -> str:
        report = build_review_run_report(
            {"result": "DIFF", "run_id": "t", "summary": {}, "source_target": {}},
            apply_report={"summary": {"changed": True}},
            verify_report={"result": "PASS", "rebuild_rediff": {"passed": rebuild_passed}},
            write=True,
            output_paths={},
            command=["x"],
        )
        return report["result"]

    def test_pr_ready_requires_gate_pass(self) -> None:
        self.assertEqual(self._run_result(True), "PR_READY")

    def test_gate_failure_blocks_pr_ready(self) -> None:
        self.assertEqual(self._run_result(False), "FAIL")


if __name__ == "__main__":
    unittest.main()
