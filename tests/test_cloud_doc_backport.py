#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for tools/cloud_doc_backport.py."""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tools.cloud_doc_backport import (
    _diff_delta_count,
    _parse_table_bindings,
    _run_review_branch,
    _run_review_branch_baseline,
    build_report,
    fetch_doc_text,
    main,
    open_backport_pr_from_manifest,
    parse_blocks,
    select_document_preamble_blocks,
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

    def test_select_document_preamble_blocks_stops_at_first_heading(self) -> None:
        blocks = parse_blocks("Intro\n\n**IMPORTANT**\n\nCopy\n\n# Safety\n\nA\n")

        selected = select_document_preamble_blocks(blocks)

        self.assertIsNotNone(selected)
        self.assertEqual([block.normalized for block in selected or []], ["Intro", "IMPORTANT", "Copy"])

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

    def test_run_review_auto_selects_headingless_preface_preamble(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            review_path = root / "docs" / "_review" / "JE-2000F" / "EU" / "page" / "00_preface.rst"
            review_path.parent.mkdir(parents=True)
            review_path.write_text(
                "\n".join(
                    [
                        "|MANUAL_LANGUAGE_SCOPE|",
                        "",
                        "**IMPORTANT**",
                        "",
                        "English copy.",
                        "",
                        "**UK ВАЖЛИВО**",
                        "",
                        "Ukrainian copy.",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            fetched_path = root / "fetched.md"
            fetched_path.write_text(
                "\n".join(
                    [
                        "English / French / Spanish / German / Italian / Ukrainian",
                        "",
                        "**IMPORTANT**",
                        "",
                        "English copy.",
                        "",
                        "# IMPORTANT SAFETY INFORMATION",
                        "",
                        "Safety copy should stay outside the preface diff.",
                        "",
                        "# APP SETUP",
                        "",
                        "App Setup should stay outside the preface diff.",
                        "",
                    ]
                ),
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
                    "run-preface-preamble",
                    "--out",
                    str(out_dir),
                ]
            )

            self.assertEqual(exit_code, 0)
            diff_payload = json.loads((out_dir / "cloud_doc_backport_report.json").read_text(encoding="utf-8"))
            self.assertEqual(diff_payload["section_selection"]["resolved_title"], "document preamble")
            self.assertTrue(diff_payload["section_selection"]["applied"])
            self.assertNotIn("APP SETUP", json.dumps(diff_payload["deltas"], ensure_ascii=False))
            self.assertNotIn("IMPORTANT SAFETY INFORMATION", json.dumps(diff_payload["deltas"], ensure_ascii=False))
            self.assertEqual(diff_payload["summary"]["change_types"]["delete"], 2)
            run_payload = json.loads((out_dir / "cloud_doc_backport_run.json").read_text(encoding="utf-8"))
            self.assertEqual(run_payload["section_selection"]["resolved_title"], "document preamble")
            self.assertEqual(run_payload["summary"]["review_source_changes"], 2)
            self.assertIn("UK ВАЖЛИВО", json.dumps(run_payload["review_source_changes"], ensure_ascii=False))

    def test_apply_review_write_deletes_unique_safe_review_text(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            review_path = root / "docs" / "_review" / "JE-1000F" / "US" / "page" / "00_preface.rst"
            review_path.parent.mkdir(parents=True)
            review_path.write_text("用户指南\n========\n\n保留内容。\n\n删除这句。\n", encoding="utf-8")
            fetched = "# manual\n\n## 用户指南\n\n保留内容。\n"
            report = build_report(
                run_id="run-review-delete",
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
            self.assertNotIn("删除这句。", review_path.read_text(encoding="utf-8"))
            apply_payload = json.loads((root / "apply" / "cloud_doc_backport_apply.json").read_text(encoding="utf-8"))
            self.assertEqual(apply_payload["summary"]["statuses"]["applied"], 1)
            verify_payload = json.loads((root / "verify" / "cloud_doc_backport_verify.json").read_text(encoding="utf-8"))
            self.assertEqual(verify_payload["summary"]["categories"]["applied_resolved"], 1)

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


class ApplySourceTableCliTest(unittest.TestCase):
    def _write_change_request_report(self, root: Path) -> Path:
        report = {
            "schema_version": "source-table-change-request/v1",
            "run_id": "rr",
            "requests": [
                {
                    "delta_hash": "h1",
                    "table": "Spec_Master",
                    "field": "Value_uk",
                    "record_id": "recAAA",
                    "resolution_status": "resolved",
                    "new_text": "DC 12 В",
                },
                {
                    "delta_hash": "h2",
                    "table": "Localized_Copy",
                    "field": "text_it",
                    "record_id": "recMCS",
                    "resolution_status": "resolved",
                    "new_text": "n",
                },
            ],
        }
        path = root / "cloud_doc_backport_source_table_change_request.json"
        path.write_text(json.dumps(report), encoding="utf-8")
        return path

    def test_dry_run_gates_to_approved_and_resolved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report_path = self._write_change_request_report(root)
            exit_code = main(["apply-source-table", "--report", str(report_path), "--approve", "h1"])
            self.assertEqual(exit_code, 0)
            apply_report = json.loads((root / "cloud_doc_backport_source_table_apply.json").read_text("utf-8"))
            self.assertFalse(apply_report["external_write"])  # dry-run, no write
            actions = {entry["delta_hash"]: entry["action"] for entry in apply_report["plan"]}
            self.assertEqual(actions["h1"], "apply")  # approved + resolved
            self.assertEqual(actions["h2"], "skip")  # not approved

    def test_write_requires_table_binding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report_path = self._write_change_request_report(root)
            exit_code = main(["apply-source-table", "--report", str(report_path), "--approve", "h1", "--write"])
            self.assertEqual(exit_code, 2)  # no --table-binding -> refuse

    def test_parse_table_bindings(self) -> None:
        self.assertEqual(
            _parse_table_bindings(["Manual_Copy_Source=base1:tbl1", "Spec_Master=base2:tbl2"]),
            {"Manual_Copy_Source": ("base1", "tbl1"), "Spec_Master": ("base2", "tbl2")},
        )
        for bad in ["noequals", "T=", "T=baseonly", "=base:tbl"]:
            with self.assertRaises(RuntimeError):
                _parse_table_bindings([bad])

    def _write_report_with_translation(self, root: Path) -> Path:
        report = {
            "schema_version": "source-table-change-request/v1",
            "run_id": "rr",
            "requests": [
                {
                    "delta_hash": "t1",
                    "table": "Localized_Copy",
                    "field": "text_it",
                    "record_id": None,
                    "resolution_status": "translation_abstain",
                    "old_text": "Vecchio",
                    "new_text": "Nuovo",
                    "source_ref": {"table": "Localized_Copy", "copy_key": "k1", "lang": "it", "source_lang": "en"},
                }
            ],
            "translation_suggestions": [
                {"delta_hash": "t1", "copy_key": "k1", "lang": "it", "source_lang": "en", "old_text": "Vecchio", "new_text": "Nuovo"},
            ],
        }
        path = root / "cloud_doc_backport_source_table_change_request.json"
        path.write_text(json.dumps(report), encoding="utf-8")
        return path

    def test_translation_suggestion_dry_run_plans_tm_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report_path = self._write_report_with_translation(root)
            exit_code = main(["apply-source-table", "--report", str(report_path), "--approve", "t1"])
            self.assertEqual(exit_code, 0)
            apply_report = json.loads((root / "cloud_doc_backport_source_table_apply.json").read_text("utf-8"))
            tm = apply_report["translation_apply"]
            self.assertFalse(tm["external_write"])  # dry-run
            self.assertEqual(tm["summary"]["apply"], 1)  # approved translation would be written to TM
            self.assertEqual(tm["plan"][0]["resolution_status"], "deferred")

    def test_tm_write_requires_tm_binding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report_path = self._write_report_with_translation(root)
            exit_code = main(["apply-source-table", "--report", str(report_path), "--approve", "t1", "--tm-write"])
            self.assertEqual(exit_code, 2)  # no --tm-binding -> refuse


class DiffDeltaCountTests(unittest.TestCase):
    def _write_report(self, root, *, applied, total_deltas):
        (root / "cloud_doc_backport_report.json").write_text(
            json.dumps({"summary": {"total_deltas": total_deltas}, "section_selection": {"applied": applied}}),
            encoding="utf-8",
        )

    def test_counts_deltas_when_section_matched(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_report(root, applied=True, total_deltas=31)
            self.assertEqual(_diff_delta_count(root), 31)

    def test_zero_when_section_not_matched(self) -> None:
        # An unmatched page falls back to a whole-doc diff (293 garbage) -> ignored.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_report(root, applied=False, total_deltas=293)
            self.assertEqual(_diff_delta_count(root), 0)

    def test_zero_when_report_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(_diff_delta_count(Path(tmp)), 0)


class RunReviewBranchGuardTests(unittest.TestCase):
    """The no-baseline whole-doc --write guard (stops mass RST-corrupting writes)."""

    def _args(self, **over):
        base = dict(
            worktrees_root=None, lark_cli="lark-cli", identity="user",
            doc_name="manual_je1000f_us_en_1.0",
            cloud_doc="https://test-degwga5x6ex8.feishu.cn/wiki/tok",
            remote="origin", git_bin="git", full_checkout=False,
            seed=False, reseed=False, push=False, write=False, page=None,
            run_id=None, out=None,
        )
        base.update(over)
        return SimpleNamespace(**base)

    def test_whole_doc_write_without_baseline_is_refused(self) -> None:
        import contextlib
        import io

        resolved = {"git_ref": "codex/review-id-x", "review_dir": "docs/_review/JE-1000F/US", "pr_url": None}
        with patch("tools.cloud_doc_backport._fetch_build_table_records", return_value=[]), \
             patch("tools.cloud_doc_backport.match_review_branch_by_name", return_value=resolved), \
             patch("tools.cloud_doc_backport.ensure_review_worktree", return_value="/tmp/wt"), \
             patch("tools.cloud_doc_backport.doc_token", return_value="tok"), \
             patch("tools.cloud_doc_backport.load_baseline", return_value=None):
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                rc = _run_review_branch(self._args(write=True, page=None))
        self.assertEqual(rc, 2)  # refused (caught -> return 2)
        self.assertIn("refusing whole-doc --write", err.getvalue())

    def test_baseline_doc_from_row_is_fetched_and_preferred(self) -> None:
        # A2: when the build-table row has a 基线文档 link, run-review-branch fetches it
        # as R0 and diffs against it — preferred over the on-branch .backport file.
        resolved = {
            "git_ref": "codex/review-id-x", "review_dir": "docs/_review/JE-1000F/US",
            "pr_url": None, "baseline_doc_url": "https://x.feishu.cn/docx/BASELINE_R0",
        }
        captured: dict[str, object] = {}

        def fake_baseline(_args, *, resolved, worktree, review_dir, doc_tok, baseline_text):
            captured["baseline_text"] = baseline_text
            return 0

        with patch("tools.cloud_doc_backport._fetch_build_table_records", return_value=[]), \
             patch("tools.cloud_doc_backport.match_review_branch_by_name", return_value=resolved), \
             patch("tools.cloud_doc_backport.ensure_review_worktree", return_value="/tmp/wt"), \
             patch("tools.cloud_doc_backport.doc_token", return_value="tok"), \
             patch("tools.cloud_doc_backport.fetch_doc_text", return_value="R0 RENDER TEXT") as fetch, \
             patch("tools.cloud_doc_backport.load_baseline") as load_file, \
             patch("tools.cloud_doc_backport._run_review_branch_baseline", side_effect=fake_baseline):
            rc = _run_review_branch(self._args(write=False, page=None))
        self.assertEqual(rc, 0)
        self.assertEqual(captured["baseline_text"], "R0 RENDER TEXT")  # the fetched doc baseline
        fetch.assert_called_once_with("https://x.feishu.cn/docx/BASELINE_R0", lark_cli="lark-cli")
        load_file.assert_not_called()  # the .backport file is NOT consulted when the row has a baseline doc

    def test_dry_run_whole_doc_not_blocked_by_guard(self) -> None:
        # without --write the guard must NOT fire — a no-baseline whole-doc REPORT is fine.
        import contextlib
        import io

        resolved = {"git_ref": "codex/review-id-x", "review_dir": "docs/_review/JE-1000F/US", "pr_url": None}
        with patch("tools.cloud_doc_backport._fetch_build_table_records", return_value=[]), \
             patch("tools.cloud_doc_backport.match_review_branch_by_name", return_value=resolved), \
             patch("tools.cloud_doc_backport.ensure_review_worktree", return_value="/tmp/wt-missing"), \
             patch("tools.cloud_doc_backport.doc_token", return_value="tok"), \
             patch("tools.cloud_doc_backport.load_baseline", return_value=None):
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                _run_review_branch(self._args(write=False, page=None))
        # it fails later (no page dir on the fake worktree), but NOT via the write guard
        self.assertNotIn("refusing whole-doc --write", err.getvalue())


class BaselineDiffTests(unittest.TestCase):
    """Approach C phase 2: diff the cloud-doc against the stored RENDER baseline.

    Both sides are the rendered manual, so only the reviewer's real edits surface —
    no RST-source-vs-rendered storm. Mirrors the JE-1000F EU preface case the
    operator hit: deleting one language block + a small text change should produce a
    couple of deltas, not ~22 mis-paired ones.
    """

    BASELINE = (
        "Preface\n\n"
        "English / French / Spanish / German / Italian / Ukrainian\n\n"
        "IMPORTANT\n\n"
        "Congratulations on your new device.\n"
    )
    # reviewer: drop "Ukrainian" + append "- test" to the IMPORTANT heading
    EDITED = (
        "Preface\n\n"
        "English / French / Spanish / German / Italian\n\n"
        "IMPORTANT - test\n\n"
        "Congratulations on your new device.\n"
    )

    def test_render_vs_render_surfaces_only_the_real_edits(self) -> None:
        report = build_report(
            run_id="baseline-diff",
            doc_type="review",
            doc_url="https://example.feishu.cn/wiki/doc-1",
            baseline_path=Path("docs/_review/JE-1000F/EU/.backport/doc-1.baseline.md"),
            fetched_text=self.EDITED,
            baseline_text=self.BASELINE,
            command=["tools/cloud_doc_backport.py", "run-review-branch", "--baseline-diff"],
            source_path=None,
            section_title=None,
        )
        # whole-doc: no section narrowing happens
        self.assertFalse(report["section_selection"]["applied"])
        # the two real edits — not a markup-mismatch storm
        self.assertEqual(report["result"], "DIFF")
        self.assertLessEqual(report["summary"]["total_deltas"], 3)
        serialized = json.dumps(report["deltas"], ensure_ascii=False)
        self.assertIn("IMPORTANT - test", serialized)
        self.assertNotIn("Ukrainian", report["deltas"][-1].get("new_text", ""))

    def test_identical_baseline_and_cloud_doc_is_no_diff(self) -> None:
        # After seeding (baseline := current cloud-doc), a re-run with no new edit is
        # clean — 0 deltas, not the ~22 garbage the RST-source path reported.
        report = build_report(
            run_id="baseline-diff",
            doc_type="review",
            doc_url="https://example.feishu.cn/wiki/doc-1",
            baseline_path=Path("docs/_review/JE-1000F/EU/.backport/doc-1.baseline.md"),
            fetched_text=self.BASELINE,
            baseline_text=self.BASELINE,
            command=["tools/cloud_doc_backport.py", "run-review-branch", "--baseline-diff"],
            source_path=None,
            section_title=None,
        )
        self.assertEqual(report["result"], "NO_DIFF")
        self.assertEqual(report["summary"]["total_deltas"], 0)

    def test_run_review_branch_baseline_writes_report_and_is_report_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "out"
            args = SimpleNamespace(
                cloud_doc="https://example.feishu.cn/wiki/doc-1",
                run_id="phase2", out=str(out_dir), lark_cli="lark-cli",
                write=True, push=True,  # must be a no-op in baseline mode
            )
            resolved = {"git_ref": "review/JE-1000F-EU", "pr_url": "https://github.com/x/y/pull/1"}
            with patch("tools.cloud_doc_backport.fetch_doc_text", return_value=self.EDITED):
                rc = _run_review_branch_baseline(
                    args, resolved=resolved, worktree=tmp,
                    review_dir="docs/_review/JE-1000F/EU", doc_tok="doc-1",
                    baseline_text=self.BASELINE,
                )
            self.assertEqual(rc, 0)
            report_json = out_dir / "cloud_doc_backport_report.json"
            self.assertTrue(report_json.is_file())
            payload = json.loads(report_json.read_text(encoding="utf-8"))
            self.assertEqual(payload["result"], "DIFF")
            self.assertFalse(payload["section_selection"]["applied"])
            # --write/--push must not have mutated the worktree (report-only)
            backport_dir = Path(tmp) / "docs/_review/JE-1000F/EU/.backport"
            self.assertFalse((backport_dir / "doc-1.baseline.md").exists())


if __name__ == "__main__":
    unittest.main()
