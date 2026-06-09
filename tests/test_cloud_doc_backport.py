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
    open_backport_pr_from_manifest,
    parse_blocks,
    select_section_blocks,
)


FIXTURES = Path(__file__).parent / "fixtures" / "cloud_doc_backport"


class CloudDocBackportTest(unittest.TestCase):
    def test_fetch_doc_text_reads_local_fixture_path(self) -> None:
        text = fetch_doc_text(str(FIXTURES / "fetched.md"))

        self.assertIn("2200 W", text)

    def test_fetch_doc_text_extracts_legacy_lark_json_markdown(self) -> None:
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

    def test_fetch_doc_text_extracts_v2_document_content_and_strips_title(self) -> None:
        payload = {
            "ok": True,
            "data": {
                "document": {
                    "document_id": "doc-1",
                    "revision_id": 12,
                    "content": "<title>manual</title>\n\n# Safety\n\n- Read all instructions.\n",
                },
                "log_id": "log-1",
            },
        }
        completed = subprocess.CompletedProcess(
            args=["lark-cli", "docs", "+fetch"],
            returncode=0,
            stdout=json.dumps(payload),
            stderr="",
        )
        calls: list[list[str]] = []

        def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            calls.append(command)
            return completed

        with patch("tools.cloud_doc_backport.subprocess.run", side_effect=fake_run):
            text = fetch_doc_text("https://example.feishu.cn/wiki/doc-1")

        self.assertEqual(text, "# Safety\n\n- Read all instructions.\n")
        self.assertEqual(
            calls[0],
            [
                "lark-cli",
                "docs",
                "+fetch",
                "--api-version",
                "v2",
                "--doc",
                "https://example.feishu.cn/wiki/doc-1",
                "--doc-format",
                "markdown",
            ],
        )

    def test_parse_blocks_strips_lark_tags_and_keeps_structure(self) -> None:
        text = (FIXTURES / "fetched.md").read_text(encoding="utf-8")
        blocks = parse_blocks(text)

        self.assertEqual(blocks[0].kind, "heading")
        self.assertEqual(blocks[0].normalized, "# Safety")
        self.assertTrue(any(block.kind == "table_row" for block in blocks))
        self.assertTrue(any(block.kind == "list_item" for block in blocks))

    def test_parse_blocks_converts_rst_headings_for_source_matching(self) -> None:
        blocks = parse_blocks("用户指南\n========\n\n原始内容。\n")

        self.assertEqual(blocks[0].kind, "heading")
        self.assertEqual(blocks[0].normalized, "# 用户指南")
        self.assertEqual(blocks[0].heading_level, 1)
        self.assertEqual(blocks[1].heading_path, ("用户指南",))

    def test_select_section_blocks_stops_at_next_peer_heading(self) -> None:
        blocks = parse_blocks("# manual\n\n## 用户指南\n\nA\n\n## 其他\n\nB\n")

        selected = select_section_blocks(blocks, "用户指南")

        self.assertIsNotNone(selected)
        self.assertEqual([block.normalized for block in selected or []], ["## 用户指南", "A"])

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

    def test_main_uses_template_as_fallback_baseline_and_auto_section(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            template_path = root / "docs" / "templates" / "page_zh" / "00_preface.rst"
            template_path.parent.mkdir(parents=True)
            template_path.write_text("用户指南\n========\n\n原始内容。\n", encoding="utf-8")
            fetched_path = root / "fetched.md"
            fetched_path.write_text(
                "# manual\n\n## 用户指南\n\n修改内容。\n\n## 其他章节\n\n这段不应该进入 diff。\n",
                encoding="utf-8",
            )
            out_dir = root / "out"

            exit_code = main(
                [
                    "diff",
                    "--doc-url",
                    str(fetched_path),
                    "--template",
                    str(template_path),
                    "--doc-type",
                    "template",
                    "--run-id",
                    "run-template",
                    "--out",
                    str(out_dir),
                ]
            )

            self.assertEqual(exit_code, 0)
            payload = json.loads((out_dir / "cloud_doc_backport_report.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["baseline"], str(template_path))
            self.assertEqual(payload["source_target"]["path"], str(template_path))
            self.assertEqual(payload["source_target"]["kind"], "template")
            self.assertTrue(payload["section_selection"]["applied"])
            self.assertEqual(payload["section_selection"]["resolved_title"], "用户指南")
            self.assertEqual(payload["summary"]["fetched_blocks"], 2)
            self.assertEqual(payload["summary"]["total_deltas"], 1)
            self.assertNotIn("其他章节", json.dumps(payload["deltas"], ensure_ascii=False))

    def test_main_fails_when_explicit_section_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            baseline_path = root / "baseline.rst"
            baseline_path.write_text("用户指南\n========\n\n原始内容。\n", encoding="utf-8")
            fetched_path = root / "fetched.md"
            fetched_path.write_text("# manual\n\n## 用户指南\n\n修改内容。\n", encoding="utf-8")

            exit_code = main(
                [
                    "diff",
                    "--doc-url",
                    str(fetched_path),
                    "--baseline",
                    str(baseline_path),
                    "--doc-type",
                    "template",
                    "--section-heading",
                    "不存在",
                    "--out",
                    str(root / "out"),
                ]
            )

            self.assertEqual(exit_code, 2)

    def test_apply_template_dry_run_plans_only_safe_template_text(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            template_path = root / "docs" / "templates" / "page_zh" / "00_preface.rst"
            template_path.parent.mkdir(parents=True)
            template_path.write_text(
                "用户指南\n========\n\n原始内容。\n\n|PRODUCT_NAME| 1500 W\n",
                encoding="utf-8",
            )
            fetched = "# manual\n\n## 用户指南\n\n修改内容。\n\n|PRODUCT_NAME| 2200 W\n"
            report = build_report(
                run_id="run-apply",
                doc_type="template",
                doc_url="fixture.md",
                baseline_path=template_path,
                fetched_text=fetched,
                baseline_text=template_path.read_text(encoding="utf-8"),
                command=["tools/cloud_doc_backport.py", "diff"],
                source_path=template_path,
                section_title="用户指南",
            )
            out_dir = root / "out"
            report_path = out_dir / "cloud_doc_backport_report.json"
            out_dir.mkdir()
            report_path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")

            exit_code = main(["apply-template", "--report", str(report_path)])

            self.assertEqual(exit_code, 0)
            self.assertIn("原始内容。", template_path.read_text(encoding="utf-8"))
            payload = json.loads((out_dir / "cloud_doc_backport_apply.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["mode"], "dry-run")
            self.assertEqual(payload["summary"]["statuses"]["planned"], 1)
            self.assertEqual(payload["summary"]["statuses"]["skipped"], 1)
            skipped = next(operation for operation in payload["operations"] if operation["status"] == "skipped")
            self.assertIn("needs_human_mapping", skipped["reason"])

    def test_apply_template_write_updates_unique_safe_replacements(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            template_path = root / "docs" / "templates" / "page_zh" / "00_preface.rst"
            template_path.parent.mkdir(parents=True)
            template_path.write_text("用户指南\n========\n\n原始内容。\n", encoding="utf-8")
            fetched = "# manual\n\n## 用户指南\n\n修改内容。\n"
            report = build_report(
                run_id="run-write",
                doc_type="template",
                doc_url="fixture.md",
                baseline_path=template_path,
                fetched_text=fetched,
                baseline_text=template_path.read_text(encoding="utf-8"),
                command=["tools/cloud_doc_backport.py", "diff"],
                source_path=template_path,
                section_title="用户指南",
            )
            out_dir = root / "out"
            report_path = out_dir / "cloud_doc_backport_report.json"
            out_dir.mkdir()
            report_path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")

            exit_code = main(["apply-template", "--report", str(report_path), "--write"])

            self.assertEqual(exit_code, 0)
            self.assertIn("修改内容。", template_path.read_text(encoding="utf-8"))
            payload = json.loads((out_dir / "cloud_doc_backport_apply.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["mode"], "write")
            self.assertEqual(payload["summary"]["statuses"]["applied"], 1)
            self.assertTrue(payload["summary"]["changed"])

    def test_apply_review_dry_run_plans_only_safe_review_text(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            review_path = root / "docs" / "_review" / "JE-1000F" / "US" / "page" / "00_preface.rst"
            review_path.parent.mkdir(parents=True)
            review_path.write_text(
                "用户指南\n========\n\n原始内容。\n\n持续功率 1500 W\n",
                encoding="utf-8",
            )
            fetched = "# manual\n\n## 用户指南\n\n修改内容。\n\n持续功率 2200 W\n"
            report = build_report(
                run_id="run-review-apply",
                doc_type="review",
                doc_url="fixture.md",
                baseline_path=review_path,
                fetched_text=fetched,
                baseline_text=review_path.read_text(encoding="utf-8"),
                command=["tools/cloud_doc_backport.py", "diff"],
                source_path=review_path,
                section_title="用户指南",
            )
            out_dir = root / "out"
            report_path = out_dir / "cloud_doc_backport_report.json"
            out_dir.mkdir()
            report_path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")

            exit_code = main(["apply-review", "--report", str(report_path)])

            self.assertEqual(exit_code, 0)
            self.assertIn("原始内容。", review_path.read_text(encoding="utf-8"))
            payload = json.loads((out_dir / "cloud_doc_backport_apply.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["mode"], "dry-run")
            self.assertEqual(payload["source_target"]["kind"], "review")
            self.assertEqual(payload["summary"]["statuses"]["planned"], 1)
            self.assertEqual(payload["summary"]["statuses"]["skipped"], 1)
            skipped = next(operation for operation in payload["operations"] if operation["status"] == "skipped")
            self.assertIn("source_table_suggestion", skipped["reason"])

    def test_apply_review_write_updates_unique_safe_replacements(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            review_path = root / "docs" / "_review" / "JE-1000F" / "US" / "page" / "00_preface.rst"
            review_path.parent.mkdir(parents=True)
            review_path.write_text("用户指南\n========\n\n原始内容。\n", encoding="utf-8")
            fetched = "# manual\n\n## 用户指南\n\n修改内容。\n"
            report = build_report(
                run_id="run-review-write",
                doc_type="review",
                doc_url="fixture.md",
                baseline_path=review_path,
                fetched_text=fetched,
                baseline_text=review_path.read_text(encoding="utf-8"),
                command=["tools/cloud_doc_backport.py", "diff"],
                source_path=review_path,
                section_title="用户指南",
            )
            out_dir = root / "out"
            report_path = out_dir / "cloud_doc_backport_report.json"
            out_dir.mkdir()
            report_path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")

            exit_code = main(["apply-review", "--report", str(report_path), "--write"])

            self.assertEqual(exit_code, 0)
            self.assertIn("修改内容。", review_path.read_text(encoding="utf-8"))
            payload = json.loads((out_dir / "cloud_doc_backport_apply.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["mode"], "write")
            self.assertEqual(payload["summary"]["statuses"]["applied"], 1)
            self.assertTrue(payload["summary"]["changed"])

    def test_apply_review_accepts_source_path_for_legacy_report_without_source_target(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            review_path = root / "docs" / "_review" / "JE-1000F" / "US" / "page" / "00_preface.rst"
            review_path.parent.mkdir(parents=True)
            review_path.write_text("用户指南\n========\n\n原始内容。\n", encoding="utf-8")
            fetched = "# manual\n\n## 用户指南\n\n修改内容。\n"
            report = build_report(
                run_id="run-review-legacy",
                doc_type="review",
                doc_url="fixture.md",
                baseline_path=review_path,
                fetched_text=fetched,
                baseline_text=review_path.read_text(encoding="utf-8"),
                command=["tools/cloud_doc_backport.py", "diff"],
                section_title="用户指南",
            )
            report.pop("source_target", None)
            out_dir = root / "out"
            report_path = out_dir / "cloud_doc_backport_report.json"
            out_dir.mkdir()
            report_path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")

            exit_code = main(["apply-review", "--report", str(report_path), "--source-path", str(review_path)])

            self.assertEqual(exit_code, 0)
            payload = json.loads((out_dir / "cloud_doc_backport_apply.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["source_target"]["kind"], "review")
            self.assertEqual(payload["summary"]["statuses"]["planned"], 1)

    def test_verify_review_fails_when_safe_review_text_is_still_pending(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            review_path = root / "docs" / "_review" / "JE-1000F" / "US" / "page" / "00_preface.rst"
            review_path.parent.mkdir(parents=True)
            review_path.write_text(
                "用户指南\n========\n\n原始内容。\n\n持续功率 1500 W\n",
                encoding="utf-8",
            )
            fetched = "# manual\n\n## 用户指南\n\n修改内容。\n\n持续功率 2200 W\n"
            report = build_report(
                run_id="run-review-verify-pending",
                doc_type="review",
                doc_url="fixture.md",
                baseline_path=review_path,
                fetched_text=fetched,
                baseline_text=review_path.read_text(encoding="utf-8"),
                command=["tools/cloud_doc_backport.py", "diff"],
                source_path=review_path,
                section_title="用户指南",
            )
            out_dir = root / "out"
            report_path = out_dir / "cloud_doc_backport_report.json"
            out_dir.mkdir()
            report_path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")

            exit_code = main(["verify-review", "--report", str(report_path)])

            self.assertEqual(exit_code, 1)
            payload = json.loads((out_dir / "cloud_doc_backport_verify.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["result"], "FAIL")
            self.assertEqual(payload["summary"]["categories"]["still_pending"], 1)
            self.assertEqual(payload["summary"]["categories"]["source_table_suggestion"], 1)
            self.assertEqual(payload["summary"]["failing_categories"]["still_pending"], 1)
            self.assertEqual(payload["summary"]["source_table_suggestions"], 1)
            self.assertEqual(payload["source_table_suggestions"][0]["old_matches"], 1)
            self.assertIn("持续功率 2200 W", payload["source_table_suggestions"][0]["new_text"])
            suggestions = json.loads(
                (out_dir / "cloud_doc_backport_source_table_suggestions.json").read_text(encoding="utf-8")
            )
            self.assertEqual(suggestions["schema_version"], "cloud-doc-backport-source-table-suggestions/v1")
            self.assertEqual(suggestions["result"], "HAS_SUGGESTIONS")
            self.assertFalse(suggestions["summary"]["external_write"])
            self.assertEqual(suggestions["suggestions"][0]["routing_hint"]["route_key"], "spec_or_numeric_value")
            self.assertIn("规格参数明细", suggestions["suggestions"][0]["routing_hint"]["candidate_source_tables"])

    def test_verify_review_passes_after_safe_review_text_is_applied(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            review_path = root / "docs" / "_review" / "JE-1000F" / "US" / "page" / "00_preface.rst"
            review_path.parent.mkdir(parents=True)
            review_path.write_text(
                "用户指南\n========\n\n原始内容。\n\n持续功率 1500 W\n",
                encoding="utf-8",
            )
            fetched = "# manual\n\n## 用户指南\n\n修改内容。\n\n持续功率 2200 W\n"
            report = build_report(
                run_id="run-review-verify-pass",
                doc_type="review",
                doc_url="fixture.md",
                baseline_path=review_path,
                fetched_text=fetched,
                baseline_text=review_path.read_text(encoding="utf-8"),
                command=["tools/cloud_doc_backport.py", "diff"],
                source_path=review_path,
                section_title="用户指南",
            )
            out_dir = root / "out"
            report_path = out_dir / "cloud_doc_backport_report.json"
            out_dir.mkdir()
            report_path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")

            apply_exit = main(["apply-review", "--report", str(report_path), "--write", "--out", str(root / "apply")])
            verify_exit = main(["verify-review", "--report", str(report_path), "--out", str(root / "verify")])

            self.assertEqual(apply_exit, 0)
            self.assertEqual(verify_exit, 0)
            payload = json.loads((root / "verify" / "cloud_doc_backport_verify.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["result"], "PASS")
            self.assertEqual(payload["summary"]["categories"]["applied_resolved"], 1)
            self.assertEqual(payload["summary"]["categories"]["source_table_suggestion"], 1)
            self.assertEqual(payload["summary"]["failing_categories"], {})
            self.assertEqual(payload["summary"]["source_table_suggestions"], 1)

    def test_run_review_dry_run_writes_manifest_without_editing_source(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            review_path = root / "docs" / "_review" / "JE-1000F" / "US" / "page" / "00_preface.rst"
            review_path.parent.mkdir(parents=True)
            review_path.write_text(
                "用户指南\n========\n\n原始内容。\n\n持续功率 1500 W\n",
                encoding="utf-8",
            )
            fetched_path = root / "fetched.md"
            fetched_path.write_text(
                "# manual\n\n## 用户指南\n\n修改内容。\n\n持续功率 2200 W\n",
                encoding="utf-8",
            )
            out_dir = root / "out"

            exit_code = main(
                [
                    "run-review",
                    "--doc-url",
                    str(fetched_path),
                    "--source-path",
                    str(review_path),
                    "--run-id",
                    "run-review-dry",
                    "--out",
                    str(out_dir),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertIn("原始内容。", review_path.read_text(encoding="utf-8"))
            self.assertTrue((out_dir / "cloud_doc_backport_report.json").exists())
            self.assertTrue((out_dir / "cloud_doc_backport_apply.json").exists())
            self.assertTrue((out_dir / "cloud_doc_backport_source_table_suggestions.json").exists())
            self.assertFalse((out_dir / "cloud_doc_backport_verify.json").exists())
            payload = json.loads((out_dir / "cloud_doc_backport_run.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], "cloud-doc-backport-run/v1")
            self.assertEqual(payload["result"], "DRY_RUN")
            self.assertFalse(payload["summary"]["changed"])
            self.assertFalse(payload["summary"]["pr_ready"])
            self.assertEqual(payload["summary"]["apply_statuses"]["planned"], 1)
            self.assertEqual(payload["summary"]["apply_statuses"]["skipped"], 1)
            self.assertEqual(payload["summary"]["source_table_suggestions"], 1)
            self.assertIn("source_table_suggestions_markdown", payload["reports"])
            suggestions = json.loads(
                (out_dir / "cloud_doc_backport_source_table_suggestions.json").read_text(encoding="utf-8")
            )
            self.assertEqual(suggestions["summary"]["total_suggestions"], 1)
            self.assertEqual(suggestions["suggestions"][0]["status"], "operator_review_required")
            self.assertFalse(suggestions["suggestions"][0]["external_write"])

    def test_run_review_write_applies_verifies_and_marks_pr_ready(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            review_path = root / "docs" / "_review" / "JE-1000F" / "US" / "page" / "00_preface.rst"
            review_path.parent.mkdir(parents=True)
            review_path.write_text(
                "用户指南\n========\n\n原始内容。\n\n持续功率 1500 W\n",
                encoding="utf-8",
            )
            fetched_path = root / "fetched.md"
            fetched_path.write_text(
                "# manual\n\n## 用户指南\n\n修改内容。\n\n持续功率 2200 W\n",
                encoding="utf-8",
            )
            out_dir = root / "out"

            exit_code = main(
                [
                    "run-review",
                    "--doc-url",
                    str(fetched_path),
                    "--source-path",
                    str(review_path),
                    "--run-id",
                    "run-review-write",
                    "--out",
                    str(out_dir),
                    "--write",
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertIn("修改内容。", review_path.read_text(encoding="utf-8"))
            self.assertTrue((out_dir / "cloud_doc_backport_report.json").exists())
            self.assertTrue((out_dir / "cloud_doc_backport_apply.json").exists())
            self.assertTrue((out_dir / "cloud_doc_backport_verify.json").exists())
            payload = json.loads((out_dir / "cloud_doc_backport_run.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["result"], "PR_READY")
            self.assertTrue(payload["summary"]["changed"])
            self.assertTrue(payload["summary"]["pr_ready"])
            self.assertEqual(payload["summary"]["apply_statuses"]["applied"], 1)
            self.assertEqual(payload["summary"]["verify_categories"]["applied_resolved"], 1)
            self.assertEqual(payload["summary"]["source_table_suggestions"], 1)

    def test_run_review_write_fails_when_residuals_are_ambiguous(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            review_path = root / "docs" / "_review" / "JE-1000F" / "US" / "page" / "00_preface.rst"
            review_path.parent.mkdir(parents=True)
            review_path.write_text("用户指南\n========\n\n原始内容。\n\n其他\n========\n\n原始内容。\n", encoding="utf-8")
            fetched_path = root / "fetched.md"
            fetched_path.write_text("# manual\n\n## 用户指南\n\n修改内容。\n", encoding="utf-8")
            out_dir = root / "out"

            exit_code = main(
                [
                    "run-review",
                    "--doc-url",
                    str(fetched_path),
                    "--source-path",
                    str(review_path),
                    "--run-id",
                    "run-review-fail",
                    "--out",
                    str(out_dir),
                    "--write",
                ]
            )

            self.assertEqual(exit_code, 1)
            self.assertNotIn("修改内容。", review_path.read_text(encoding="utf-8"))
            payload = json.loads((out_dir / "cloud_doc_backport_run.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["result"], "FAIL")
            self.assertEqual(payload["summary"]["apply_statuses"]["skipped"], 1)
            self.assertEqual(payload["summary"]["verify_failing_categories"]["unsafe_or_ambiguous"], 1)
            self.assertFalse(payload["summary"]["pr_ready"])

    def test_open_pr_from_manifest_creates_draft_pr_for_pr_ready_review_source(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            review_path = root / "docs" / "_review" / "JE-1000F" / "US" / "page" / "00_preface.rst"
            review_path.parent.mkdir(parents=True)
            review_path.write_text("修改内容。\n", encoding="utf-8")
            manifest_path = root / "reports" / "cloud_doc_backport" / "run-1" / "cloud_doc_backport_run.json"
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": "cloud-doc-backport-run/v1",
                        "result": "PR_READY",
                        "mode": "write",
                        "source_target": {
                            "path": "docs/_review/JE-1000F/US/page/00_preface.rst",
                            "kind": "review",
                        },
                        "summary": {
                            "total_deltas": 2,
                            "changed": True,
                            "pr_ready": True,
                            "source_table_suggestions": 1,
                        },
                        "reports": {
                            "run_markdown": "reports/cloud_doc_backport/run-1/cloud_doc_backport_run.md",
                        },
                    }
                ),
                encoding="utf-8",
            )
            calls: list[list[str]] = []

            def fake_run(command: list[str], *, root: Path, stdin: str | None = None) -> str:
                del root, stdin
                calls.append(command)
                if command[:3] == ["git", "status", "--porcelain"]:
                    return "\n".join(
                        [
                            " M docs/_review/JE-1000F/US/page/00_preface.rst",
                            "?? reports/cloud_doc_backport/run-1/cloud_doc_backport_run.json",
                        ]
                    )
                if command[:3] == ["git", "branch", "--show-current"]:
                    return "main"
                if command[:3] == ["git", "rev-parse", "HEAD"]:
                    return "abc123"
                if command[:3] == ["gh", "pr", "create"]:
                    return "https://github.com/Bingboom/auto-manual/pull/999"
                return ""

            with patch("tools.cloud_doc_backport._run_pr_command", side_effect=fake_run):
                result = open_backport_pr_from_manifest(
                    manifest_path=manifest_path,
                    repo_root=root,
                    git_bin="git",
                    gh_bin="gh",
                )

            self.assertEqual(result["result"], "PR_OPENED")
            self.assertEqual(result["pr_url"], "https://github.com/Bingboom/auto-manual/pull/999")
            self.assertEqual(result["source_table_suggestions"], 1)
            self.assertIn(
                [
                    "git",
                    "switch",
                    "-c",
                    "review/JE-1000F-US-cloud-doc-backport-run-1",
                ],
                calls,
            )
            self.assertIn(["git", "add", "docs/_review/JE-1000F/US/page/00_preface.rst"], calls)
            pr_create_call = next(command for command in calls if command[:3] == ["gh", "pr", "create"])
            self.assertIn("--draft", pr_create_call)
            self.assertIn("reports/cloud_doc_backport/run-1/cloud_doc_backport_run.json", "\n".join(pr_create_call))

    def test_open_pr_from_manifest_refuses_unrelated_worktree_changes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            review_path = root / "docs" / "_review" / "JE-1000F" / "US" / "page" / "00_preface.rst"
            review_path.parent.mkdir(parents=True)
            review_path.write_text("修改内容。\n", encoding="utf-8")
            manifest_path = root / "reports" / "cloud_doc_backport" / "run-1" / "cloud_doc_backport_run.json"
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": "cloud-doc-backport-run/v1",
                        "result": "PR_READY",
                        "mode": "write",
                        "source_target": {
                            "path": "docs/_review/JE-1000F/US/page/00_preface.rst",
                            "kind": "review",
                        },
                        "summary": {"changed": True, "pr_ready": True},
                    }
                ),
                encoding="utf-8",
            )

            def fake_run(command: list[str], *, root: Path, stdin: str | None = None) -> str:
                del root, stdin
                if command[:3] == ["git", "status", "--porcelain"]:
                    return "\n".join(
                        [
                            " M docs/_review/JE-1000F/US/page/00_preface.rst",
                            " M README.md",
                        ]
                    )
                return "main"

            with patch("tools.cloud_doc_backport._run_pr_command", side_effect=fake_run):
                with self.assertRaisesRegex(RuntimeError, "unrelated working-tree changes"):
                    open_backport_pr_from_manifest(manifest_path=manifest_path, repo_root=root)

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
