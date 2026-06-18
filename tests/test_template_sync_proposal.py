#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the template_sync_proposal report (Milestone F, PR F4)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.cloud_doc_backport import (  # noqa: E402
    build_template_sync_proposal_report,
    diff_blocks,
    markdown_template_sync_proposal_report,
    parse_blocks,
    write_template_sync_proposal_report,
)
from tools.family_scope import build_family_index  # noqa: E402


def _diff_report_with_shared_delta(tmp: str) -> dict:
    (Path(tmp) / "fr.rst").write_text("Shared safety note\n", encoding="utf-8")
    (Path(tmp) / "de.rst").write_text("Shared safety note\n", encoding="utf-8")
    family_index = build_family_index({"fr": Path(tmp) / "fr.rst", "de": Path(tmp) / "de.rst"})
    deltas = diff_blocks(
        parse_blocks("Shared safety note\n"),
        parse_blocks("Changed safety note\n"),
        doc_type="review",
        run_id="t",
        family_index=family_index,
    )
    return {"run_id": "t", "deltas": deltas}


class TemplateSyncProposalTests(unittest.TestCase):
    def test_shared_delta_becomes_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_template_sync_proposal_report(
                diff_report=_diff_report_with_shared_delta(tmp), command=["x"]
            )
            self.assertEqual(report["summary"]["proposals"], 1)
            self.assertFalse(report["external_write"])
            proposal = report["proposals"][0]
            self.assertEqual(proposal["target_templates"], ["de", "fr"])
            self.assertEqual(proposal["old_text"], "Shared safety note")
            self.assertIn("delta_hash", proposal)
            self.assertIn("post_apply", proposal)

    def test_no_shared_delta_yields_empty_proposal(self) -> None:
        # A plain delta with no family_scope -> no proposals.
        deltas = diff_blocks(
            parse_blocks("Target only line\n"),
            parse_blocks("Changed line\n"),
            doc_type="review",
            run_id="t",
        )
        report = build_template_sync_proposal_report(
            diff_report={"run_id": "t", "deltas": deltas}, command=["x"]
        )
        self.assertEqual(report["summary"]["proposals"], 0)

    def test_markdown_renders_for_empty_and_nonempty(self) -> None:
        empty = build_template_sync_proposal_report(diff_report={"run_id": "t", "deltas": []}, command=["x"])
        self.assertIn("No shared-across-family", markdown_template_sync_proposal_report(empty))
        with tempfile.TemporaryDirectory() as tmp:
            report = build_template_sync_proposal_report(
                diff_report=_diff_report_with_shared_delta(tmp), command=["x"]
            )
            md = markdown_template_sync_proposal_report(report)
            self.assertIn("Template Sync Proposal", md)
            self.assertIn("de, fr", md)

    def test_write_emits_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_template_sync_proposal_report(
                diff_report=_diff_report_with_shared_delta(tmp), command=["x"]
            )
            out = Path(tmp) / "out"
            written = write_template_sync_proposal_report(report, out)
            self.assertTrue(written["json"].exists())
            self.assertTrue(written["markdown"].exists())


if __name__ == "__main__":
    unittest.main()
