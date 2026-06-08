#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for tools/cloud_doc_backport.py."""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.cloud_doc_backport import (
    build_report,
    fetch_doc_text,
    main,
    parse_blocks,
)


FIXTURES = Path(__file__).parent / "fixtures" / "cloud_doc_backport"


class CloudDocBackportTest(unittest.TestCase):
    def test_fetch_doc_text_reads_local_fixture_path(self) -> None:
        text = fetch_doc_text(str(FIXTURES / "fetched.md"))

        self.assertIn("2200 W", text)

    def test_fetch_doc_text_extracts_lark_cli_json_markdown(self) -> None:
        payload = {
            "ok": True,
            "data": {
                "doc_id": "doc-1",
                "markdown": "# Safety\n\n- Read all instructions.\n",
                "title": "manual",
            },
        }
        completed = subprocess.CompletedProcess(
            args=["lark-cli", "docs", "+fetch", "--doc", "https://example.feishu.cn/wiki/doc-1"],
            returncode=0,
            stdout=json.dumps(payload),
            stderr="",
        )

        with patch("tools.cloud_doc_backport.subprocess.run", return_value=completed):
            text = fetch_doc_text("https://example.feishu.cn/wiki/doc-1")

        self.assertEqual(text, "# Safety\n\n- Read all instructions.\n")

    def test_parse_blocks_strips_lark_tags_and_keeps_structure(self) -> None:
        text = (FIXTURES / "fetched.md").read_text(encoding="utf-8")
        blocks = parse_blocks(text)

        self.assertEqual(blocks[0].kind, "heading")
        self.assertEqual(blocks[0].normalized, "# Safety")
        self.assertTrue(any(block.kind == "table_row" for block in blocks))
        self.assertTrue(any(block.kind == "list_item" for block in blocks))

    def test_build_report_classifies_review_prose_and_data_like_deltas(self) -> None:
        baseline = (FIXTURES / "baseline.md").read_text(encoding="utf-8")
        fetched = (FIXTURES / "fetched.md").read_text(encoding="utf-8")

        report = build_report(
            run_id="run-1",
            doc_type="review",
            doc_url=str(FIXTURES / "fetched.md"),
            baseline_path=FIXTURES / "baseline.md",
            fetched_text=fetched,
            baseline_text=baseline,
            command=["tools/cloud_doc_backport.py", "diff"],
        )

        self.assertEqual(report["schema_version"], "cloud-doc-backport-report/v1")
        self.assertEqual(report["result"], "DIFF")
        self.assertEqual(report["summary"]["total_deltas"], 2)
        self.assertEqual(report["summary"]["route_classes"]["source_table_suggestion"], 1)
        self.assertEqual(report["summary"]["route_classes"]["repo_review_text"], 1)
        table_delta = next(
            delta for delta in report["deltas"] if delta["route_class"] == "source_table_suggestion"
        )
        self.assertEqual(table_delta["change_type"], "replace")
        self.assertIn("1500 W", table_delta["old_text"])
        self.assertIn("2200 W", table_delta["new_text"])

    def test_build_report_classifies_template_data_like_delta_as_human_mapping(self) -> None:
        baseline = (FIXTURES / "baseline.md").read_text(encoding="utf-8")
        fetched = (FIXTURES / "fetched.md").read_text(encoding="utf-8")

        report = build_report(
            run_id="run-1",
            doc_type="template",
            doc_url=str(FIXTURES / "fetched.md"),
            baseline_path=FIXTURES / "baseline.md",
            fetched_text=fetched,
            baseline_text=baseline,
            command=["tools/cloud_doc_backport.py", "diff"],
        )

        self.assertEqual(report["summary"]["route_classes"]["needs_human_mapping"], 1)
        self.assertEqual(report["summary"]["route_classes"]["repo_template_text"], 1)

    def test_main_writes_json_and_markdown_reports(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td)
            exit_code = main(
                [
                    "diff",
                    "--doc-url",
                    str(FIXTURES / "fetched_prose.md"),
                    "--baseline",
                    str(FIXTURES / "baseline.md"),
                    "--doc-type",
                    "review",
                    "--run-id",
                    "run-main",
                    "--out",
                    str(out_dir),
                ]
            )

            self.assertEqual(exit_code, 0)
            json_path = out_dir / "cloud_doc_backport_report.json"
            markdown_path = out_dir / "cloud_doc_backport_report.md"
            self.assertTrue(json_path.exists())
            self.assertTrue(markdown_path.exists())
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["run_id"], "run-main")
            self.assertEqual(payload["summary"]["total_deltas"], 1)
            self.assertEqual(payload["deltas"][0]["route_class"], "repo_review_text")
            markdown = markdown_path.read_text(encoding="utf-8")
            self.assertIn("# Cloud Doc Backport Diff Report", markdown)
            self.assertIn("repo_review_text", markdown)

    def test_report_is_no_diff_for_identical_content(self) -> None:
        baseline = (FIXTURES / "baseline.md").read_text(encoding="utf-8")
        report = build_report(
            run_id="run-1",
            doc_type="template",
            doc_url=str(FIXTURES / "baseline.md"),
            baseline_path=FIXTURES / "baseline.md",
            fetched_text=baseline,
            baseline_text=baseline,
            command=["tools/cloud_doc_backport.py", "diff"],
        )

        self.assertEqual(report["result"], "NO_DIFF")
        self.assertEqual(report["summary"]["total_deltas"], 0)
        self.assertEqual(report["deltas"], [])


if __name__ == "__main__":
    unittest.main()
