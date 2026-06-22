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
    _auto_sibling_rels,
    _backport_pr_branch,
    _diff_delta_count,
    _family_index_from_args,
    _parse_table_bindings,
    _heading_text_key,
    _rebuild_rediff_for_report,
    _rebuild_rediff_gate,
    _review_block_is_plain,
    _rst_display_width,
    _resolve_backport_data_root,
    _resolve_review_branch_siblings,
    _run_review_branch,
    _run_review_branch_baseline,
    build_report,
    build_review_apply_report,
    build_review_verify_report,
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

            exit_code = main(["apply-review", "--report", str(report_path), "--write", "--allow-rst-baseline"])

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

    def test_apply_review_write_refuses_rst_source_baseline(self) -> None:
        import contextlib
        import io

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            review_path = root / "docs" / "_review" / "JE-1000F" / "US" / "page" / "00_preface.rst"
            review_path.parent.mkdir(parents=True)
            original = "用户指南\n========\n\n原始内容。\n"
            review_path.write_text(original, encoding="utf-8")
            report = build_report(
                run_id="apply-review-guard",
                doc_type="review",
                doc_url="fixture.md",
                baseline_path=review_path,  # .rst source baseline -> the broken rendered-vs-RST path
                fetched_text="# manual\n\n## 用户指南\n\n修改内容。\n",
                baseline_text=original,
                command=["tools/cloud_doc_backport.py", "diff"],
                source_path=review_path,
                section_title="用户指南",
            )
            out_dir = root / "out"
            report_path = out_dir / "cloud_doc_backport_report.json"
            out_dir.mkdir()
            report_path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")

            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                exit_code = main(["apply-review", "--report", str(report_path), "--write"])

            self.assertEqual(exit_code, 2)
            self.assertIn("run-review-branch", err.getvalue())
            self.assertEqual(review_path.read_text(encoding="utf-8"), original)
            self.assertFalse((out_dir / "cloud_doc_backport_apply.json").exists())

    def test_apply_review_write_allows_render_baseline_report(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            review_path = root / "docs" / "_review" / "JE-1000F" / "US" / "page" / "00_preface.rst"
            review_path.parent.mkdir(parents=True)
            review_path.write_text("用户指南\n========\n\n原始内容。\n", encoding="utf-8")
            # A render-baseline report (.baseline.md baseline, no source_target) is the clean
            # run-review-branch output; apply-review must accept it WITHOUT --allow-rst-baseline.
            report = build_report(
                run_id="apply-review-render-baseline",
                doc_type="review",
                doc_url="https://example.feishu.cn/docx/doc123",
                baseline_path=Path("docs/_review/JE-1000F/US/.backport/doc123.baseline.md"),
                fetched_text="# manual\n\n## 用户指南\n\n修改内容。\n",
                baseline_text="# manual\n\n## 用户指南\n\n原始内容。\n",
                command=["tools/cloud_doc_backport.py", "run-review-branch", "--baseline-diff"],
                source_path=None,
                section_title=None,
            )
            out_dir = root / "out"
            report_path = out_dir / "cloud_doc_backport_report.json"
            out_dir.mkdir()
            report_path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")

            exit_code = main(
                ["apply-review", "--report", str(report_path), "--source-path", str(review_path), "--write"]
            )

            self.assertEqual(exit_code, 0)
            self.assertIn("修改内容。", review_path.read_text(encoding="utf-8"))
            payload = json.loads((out_dir / "cloud_doc_backport_apply.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"]["statuses"]["applied"], 1)

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

            apply_exit = main(["apply-review", "--report", str(report_path), "--write", "--allow-rst-baseline", "--out", str(root / "apply")])
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

            apply_exit = main(["apply-review", "--report", str(report_path), "--write", "--allow-rst-baseline", "--out", str(root / "apply")])
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
                    "--allow-rst-baseline",
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
                    "--allow-rst-baseline",
                ]
            )

            self.assertEqual(exit_code, 1)
            self.assertNotIn("修改内容。", review_path.read_text(encoding="utf-8"))
            payload = json.loads((out_dir / "cloud_doc_backport_run.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["result"], "FAIL")
            self.assertEqual(payload["summary"]["apply_statuses"]["skipped"], 1)
            self.assertEqual(payload["summary"]["verify_failing_categories"]["unsafe_or_ambiguous"], 1)
            self.assertFalse(payload["summary"]["pr_ready"])

    def test_run_review_write_refuses_rst_source_baseline(self) -> None:
        import contextlib
        import io

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            review_path = root / "docs" / "_review" / "JE-1000F" / "US" / "page" / "00_preface.rst"
            review_path.parent.mkdir(parents=True)
            original = "用户指南\n========\n\n原始内容。\n"
            review_path.write_text(original, encoding="utf-8")
            fetched_path = root / "fetched.md"
            fetched_path.write_text("# manual\n\n## 用户指南\n\n修改内容。\n", encoding="utf-8")
            out_dir = root / "out"

            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                exit_code = main(
                    [
                        "run-review",
                        "--doc-url",
                        str(fetched_path),
                        "--source-path",
                        str(review_path),
                        "--out",
                        str(out_dir),
                        "--write",
                    ]
                )

            self.assertEqual(exit_code, 2)
            self.assertIn("run-review-branch", err.getvalue())
            self.assertEqual(review_path.read_text(encoding="utf-8"), original)
            self.assertFalse((out_dir / "cloud_doc_backport_report.json").exists())

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
                    "new_value": "DC 12 В",
                },
                {
                    "delta_hash": "h2",
                    "table": "Localized_Copy",
                    "field": "text_it",
                    "record_id": "recMCS",
                    "resolution_status": "resolved",
                    "new_text": "n",
                    "new_value": "n",
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


class BackportPrBranchTests(unittest.TestCase):
    def test_sanitizes_review_ref_into_a_backport_subbranch(self) -> None:
        # the write-back goes on a backport/ sub-branch, PR'd INTO the review branch
        name = _backport_pr_branch("codex/review-id-recvfw0zg4pzxs", "run-1")
        self.assertTrue(name.startswith("backport/"))
        self.assertNotIn("/", name[len("backport/"):])  # the ref's slash is flattened
        self.assertIn("recvfw0zg4pzxs", name)


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

        def fake_baseline(_args, *, resolved, worktree, review_dir, doc_tok, baseline_text, baseline_from_seed):
            captured["baseline_text"] = baseline_text
            captured["baseline_from_seed"] = baseline_from_seed
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
        self.assertFalse(captured["baseline_from_seed"])  # copy-doc baseline is frozen, never advanced locally

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


class RunReviewBranchFamilyScopeTests(unittest.TestCase):
    """F3 / Class T: run-review-branch auto-resolves the page_shared/<lang> shared
    templates as family-scope siblings, so a reviewer's shared-template prose delta is
    flagged Class T (template-sync proposal) instead of written as target-local Class R."""

    def _args(self, **over):
        base = dict(
            worktrees_root=None, lark_cli="lark-cli", identity="user",
            doc_name="manual_je1000f_us_en_1.0",
            cloud_doc="https://test-degwga5x6ex8.feishu.cn/wiki/tok",
            remote="origin", git_bin="git", full_checkout=False,
            seed=False, reseed=False, push=False, write=False, page=None,
            run_id="t", out=None, lang=None, data_root=None,
            sibling=[], no_auto_sibling=False,
        )
        base.update(over)
        return SimpleNamespace(**base)

    def test_auto_sibling_rels_resolves_shared_templates_per_language(self) -> None:
        en = _auto_sibling_rels("en")
        self.assertTrue(en, "page_shared/en should hold shared templates")
        self.assertTrue(all(p.startswith("docs/templates/page_shared/en/") for p in en))
        self.assertTrue(all(not Path(p).is_absolute() for p in en))  # clean repo-relative labels
        # single-region languages have no page_shared surface -> Class T never fires
        self.assertEqual(_auto_sibling_rels("ja"), [])
        self.assertEqual(_auto_sibling_rels("zh"), [])
        self.assertEqual(_auto_sibling_rels(""), [])

    def test_resolve_siblings_explicit_wins(self) -> None:
        explicit = ["docs/templates/page_us-en/safety_en.rst"]
        args = self._args(sibling=list(explicit), lang="en")
        self.assertEqual(_resolve_review_branch_siblings(args), explicit)

    def test_resolve_siblings_no_auto_disables(self) -> None:
        args = self._args(sibling=[], no_auto_sibling=True, lang="en")
        self.assertEqual(_resolve_review_branch_siblings(args), [])

    def test_resolve_siblings_auto_when_empty(self) -> None:
        out = _resolve_review_branch_siblings(self._args(sibling=[], lang="en"))
        self.assertTrue(out)
        self.assertTrue(all(p.startswith("docs/templates/page_shared/en/") for p in out))

    def test_family_index_resolves_relative_sibling_with_clean_label(self) -> None:
        rel = "docs/templates/page_shared/en/00_preface.rst"
        index = _family_index_from_args(SimpleNamespace(sibling=[rel]))
        self.assertTrue(index, "the relative shared-template path was read & indexed against the repo root")
        labels = {label for labels in index.values() for label in labels}
        self.assertEqual(labels, {rel})  # the relative string stays the blast-radius label

    def test_family_index_none_without_siblings(self) -> None:
        self.assertIsNone(_family_index_from_args(SimpleNamespace(sibling=[])))
        self.assertIsNone(_family_index_from_args(SimpleNamespace()))

    def test_run_review_branch_forwards_auto_siblings_to_per_page_worker(self) -> None:
        captured: list[list[str]] = []

        def fake_run(cmd, **_kw):
            captured.append(cmd)
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as wt:
            page_dir = Path(wt) / "docs/_review/JE-1000F/US/page"
            page_dir.mkdir(parents=True)
            (page_dir / "00_preface.rst").write_text("Hello\n", encoding="utf-8")
            resolved = {"git_ref": "review/JE-1000F-US", "review_dir": "docs/_review/JE-1000F/US", "pr_url": None}
            args = self._args(write=False, page=None, out=str(Path(wt) / "out"))
            with patch("tools.cloud_doc_backport._fetch_build_table_records", return_value=[]), \
                 patch("tools.cloud_doc_backport.match_review_branch_by_name", return_value=resolved), \
                 patch("tools.cloud_doc_backport.ensure_review_worktree", return_value=wt), \
                 patch("tools.cloud_doc_backport.doc_token", return_value="tok"), \
                 patch("tools.cloud_doc_backport.load_baseline", return_value=None), \
                 patch("tools.cloud_doc_backport.fetch_doc_text", return_value="EDITED"), \
                 patch("tools.cloud_doc_backport.subprocess.run", side_effect=fake_run):
                rc = _run_review_branch(args)
        self.assertIn(rc, (0, 1))
        self.assertTrue(captured, "the per-page run-review worker should have been invoked")
        cmd = captured[0]
        self.assertIn("--sibling", cmd)
        sib_values = [cmd[i + 1] for i, tok in enumerate(cmd) if tok == "--sibling"]
        self.assertTrue(
            any(s.startswith("docs/templates/page_shared/en/") for s in sib_values),
            f"expected auto-resolved page_shared/en siblings, got {sib_values}",
        )


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

    def test_image_reference_noise_is_normalized_away(self) -> None:
        # Feishu re-hosts + re-describes every image per doc, so the editable doc and
        # its baseline copy have different `![alt](token)` for the SAME image. Those
        # must NOT register as deltas — only the real text edits should. (夏冰's case:
        # 52 deltas where 50 were image noise + 2 real text edits.)
        baseline = (
            "Ports\n\n"
            "| ![an AI description of the port image](https://x.feishu.cn/img/TOKEN_A) |\n\n"
            "<table><tbody><tr><td><img name=\"a.png\" alt=\"desc A\" src=\"https://x/img/TOKEN_C\"/></td><td>LCD SCREEN</td></tr></tbody></table>\n\n"
            "USB-C 100 W Output\n\n"
            "FR IMPORTANT\n"
        )
        edited = (
            "Ports\n\n"
            "| ![a totally different re-generated description](https://x.feishu.cn/img/TOKEN_B) |\n\n"
            "<table><tbody><tr><td><img name=\"b.png\" alt=\"freshly re-generated desc\" src=\"https://x/img/TOKEN_D\"/></td><td>LCD SCREEN</td></tr></tbody></table>\n\n"
            "USB-C 100 W Output test\n\n"
            "FR IMPORTANT test\n"
        )
        report = build_report(
            run_id="img-norm", doc_type="review", doc_url="https://x.feishu.cn/wiki/d",
            baseline_path=Path("b.md"), fetched_text=edited, baseline_text=baseline,
            command=["t"], source_path=None, section_title=None,
        )
        # only the two text edits — the image line (different token + alt) is dropped
        self.assertEqual(report["summary"]["total_deltas"], 2)
        changed = {(d.get("old_text"), d.get("new_text")) for d in report["deltas"]}
        self.assertIn(("USB-C 100 W Output", "USB-C 100 W Output test"), changed)
        self.assertIn(("FR IMPORTANT", "FR IMPORTANT test"), changed)
        # no delta is an image line: the token/alt never appears in any old/new text
        for delta in report["deltas"]:
            self.assertNotIn("TOKEN_", (delta.get("old_text") or "") + (delta.get("new_text") or ""))
            self.assertNotIn("![", (delta.get("old_text") or "") + (delta.get("new_text") or ""))

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

    def test_baseline_diff_routes_source_value_vs_review_prose(self) -> None:
        # phase 3: the baseline diff classifies deltas — a table/spec value goes to the
        # source table (Class D, source_table_suggestion → apply-source-table/F6, NOT
        # the RST); a plain prose edit stays review text (Class R, repo_review_text).
        baseline = "# Output Ports\n\nKeep this section handy.\n\n| **USB-C 100 W Output** | 100 W |\n"
        edited = "# Output Ports\n\nKeep this section nearby.\n\n| **USB-C 100 W Output test** | 100 W |\n"
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "out"
            args = SimpleNamespace(
                cloud_doc="https://example.feishu.cn/wiki/doc-2", run_id="p3",
                out=str(out_dir), lark_cli="lark-cli", write=False, push=False,
                doc_name="manual_je1000f_us_en_1.0", lang=None, data_root="data/phase2",
            )
            with patch("tools.cloud_doc_backport.fetch_doc_text", return_value=edited):
                rc = _run_review_branch_baseline(
                    args, resolved={"git_ref": "review/JE-1000F-US", "pr_url": None},
                    worktree=tmp, review_dir="docs/_review/JE-1000F/US", doc_tok="doc-2",
                    baseline_text=baseline,
                )
            self.assertEqual(rc, 0)
            routes = json.loads((out_dir / "cloud_doc_backport_report.json").read_text(encoding="utf-8"))["summary"]["route_classes"]
            self.assertIn("source_table_suggestion", routes)  # the table value -> source (not RST)
            self.assertIn("repo_review_text", routes)  # the prose edit -> _review

    def test_baseline_diff_write_applies_class_r_prose_to_page(self) -> None:
        # --write: a Class R (review-prose) delta is applied to the matching _review
        # page via the guarded apply; Class D is NOT written to the RST.
        with tempfile.TemporaryDirectory() as tmp:
            page_dir = Path(tmp) / "docs/_review/JE-1000F/US/page"
            page_dir.mkdir(parents=True)
            preface = page_dir / "00_preface.rst"
            preface.write_text("**FR IMPORTANT**\n\nKeep this manual handy.\n", encoding="utf-8")
            out_dir = Path(tmp) / "out"
            args = SimpleNamespace(
                cloud_doc="https://example.feishu.cn/wiki/doc-3", run_id="p3w",
                out=str(out_dir), lark_cli="lark-cli", write=True, push=False,
                doc_name="manual_je1000f_us_en_1.0", lang=None, data_root="data/phase2",
                git_bin="git", remote="origin",
            )
            edited = "**FR IMPORTANT test**\n\nKeep this manual handy.\n"
            with patch("tools.cloud_doc_backport.fetch_doc_text", return_value=edited):
                rc = _run_review_branch_baseline(
                    args, resolved={"git_ref": "review/JE-1000F-US", "pr_url": None},
                    worktree=tmp, review_dir="docs/_review/JE-1000F/US", doc_tok="doc-3",
                    baseline_text="**FR IMPORTANT**\n\nKeep this manual handy.\n",
                )
            self.assertEqual(rc, 0)
            # the Class R edit landed in the page RST (guarded apply matched the prose)
            self.assertIn("FR IMPORTANT test", preface.read_text(encoding="utf-8"))

    def test_seed_baseline_cursor_advances_on_full_apply(self) -> None:
        # design §6: on a FULL apply (all deltas pure Class R, all applied) against a
        # .backport/ SEED baseline, advance the cursor -> rewrite the seed to C_now so the
        # next run diffs only NEW edits. (The copy-doc model never advances locally.)
        with tempfile.TemporaryDirectory() as tmp:
            page_dir = Path(tmp) / "docs/_review/JE-1000F/US/page"
            page_dir.mkdir(parents=True)
            preface = page_dir / "00_preface.rst"
            preface.write_text("**FR IMPORTANT**\n\nKeep this manual handy.\n", encoding="utf-8")
            out_dir = Path(tmp) / "out"
            args = SimpleNamespace(
                cloud_doc="https://example.feishu.cn/wiki/doc-seed", run_id="seed-adv",
                out=str(out_dir), lark_cli="lark-cli", write=True, push=False,
                doc_name="manual_je1000f_us_en_1.0", lang=None, data_root=None,
                git_bin="git", remote="origin",
            )
            edited = "**FR IMPORTANT test**\n\nKeep this manual handy.\n"
            with patch("tools.cloud_doc_backport.fetch_doc_text", return_value=edited):
                rc = _run_review_branch_baseline(
                    args, resolved={"git_ref": "review/JE-1000F-US", "pr_url": None},
                    worktree=tmp, review_dir="docs/_review/JE-1000F/US", doc_tok="doc-seed",
                    baseline_text="**FR IMPORTANT**\n\nKeep this manual handy.\n",
                    baseline_from_seed=True,
                )
            self.assertEqual(rc, 0)
            self.assertIn("FR IMPORTANT test", preface.read_text(encoding="utf-8"))
            # the seed baseline advanced to C_now (the edited render)
            seed = Path(tmp) / "docs/_review/JE-1000F/US/.backport/doc-seed.baseline.md"
            self.assertTrue(seed.is_file())
            self.assertIn("FR IMPORTANT test", seed.read_text(encoding="utf-8"))

    def test_seed_baseline_cursor_not_advanced_on_partial_apply(self) -> None:
        # a pending Class D (source-value) delta means NOT every edit was resolved, so the
        # seed cursor must NOT advance (else the un-applied Class D edit is buried, §6).
        with tempfile.TemporaryDirectory() as tmp:
            page_dir = Path(tmp) / "docs/_review/JE-1000F/US/page"
            page_dir.mkdir(parents=True)
            preface = page_dir / "00_preface.rst"
            preface.write_text("**FR IMPORTANT**\n\nKeep this manual handy.\n", encoding="utf-8")
            out_dir = Path(tmp) / "out"
            args = SimpleNamespace(
                cloud_doc="https://example.feishu.cn/wiki/doc-seed2", run_id="seed-part",
                out=str(out_dir), lark_cli="lark-cli", write=True, push=False,
                doc_name="manual_je1000f_us_en_1.0", lang=None, data_root="data/phase2",
                git_bin="git", remote="origin",
            )
            baseline = "**FR IMPORTANT**\n\nKeep this manual handy.\n\n| **USB-C 100 W Output** | 100 W |\n"
            edited = "**FR IMPORTANT test**\n\nKeep this manual handy.\n\n| **USB-C 100 W Output test** | 100 W |\n"
            with patch("tools.cloud_doc_backport.fetch_doc_text", return_value=edited):
                rc = _run_review_branch_baseline(
                    args, resolved={"git_ref": "review/JE-1000F-US", "pr_url": None},
                    worktree=tmp, review_dir="docs/_review/JE-1000F/US", doc_tok="doc-seed2",
                    baseline_text=baseline,
                    baseline_from_seed=True,
                )
            self.assertEqual(rc, 0)
            routes = json.loads((out_dir / "cloud_doc_backport_report.json").read_text(encoding="utf-8"))["summary"]["route_classes"]
            self.assertIn("source_table_suggestion", routes)  # a pending Class D delta exists
            # partial apply -> the seed cursor stays put (nothing buried)
            seed = Path(tmp) / "docs/_review/JE-1000F/US/.backport/doc-seed2.baseline.md"
            self.assertFalse(seed.exists())

    def test_baseline_diff_uses_value_index_for_deterministic_class_d(self) -> None:
        # F2 wiring: with a synced data-root, a PROSE copy value the heuristic would NOT
        # flag (no digits/units) is still routed Class D because it matches the value-index.
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "phase2"
            data_root.mkdir()
            (data_root / "Localized_Copy.csv").write_text(
                "copy_key,Source_lang,text_en\nguide.title,en,Operation Guide\n", encoding="utf-8"
            )
            page_dir = Path(tmp) / "docs/_review/JE-1000F/US/page"
            page_dir.mkdir(parents=True)
            (page_dir / "00_preface.rst").write_text("Operation Guide\n", encoding="utf-8")
            out_dir = Path(tmp) / "out"
            args = SimpleNamespace(
                cloud_doc="https://example.feishu.cn/wiki/doc-f2", run_id="f2",
                out=str(out_dir), lark_cli="lark-cli", write=False, push=False,
                doc_name="manual_je1000f_us_en_1.0", lang=None, data_root=str(data_root),
                git_bin="git", remote="origin",
            )
            with patch("tools.cloud_doc_backport.fetch_doc_text", return_value="Operation Manual\n"):
                rc = _run_review_branch_baseline(
                    args, resolved={"git_ref": "review/JE-1000F-US", "pr_url": None},
                    worktree=tmp, review_dir="docs/_review/JE-1000F/US", doc_tok="doc-f2",
                    baseline_text="Operation Guide\n",
                )
            self.assertEqual(rc, 0)
            routes = json.loads((out_dir / "cloud_doc_backport_report.json").read_text(encoding="utf-8"))["summary"]["route_classes"]
            # Class D via the value-index — a heuristic alone would leave this prose as repo_review_text
            self.assertIn("source_table_suggestion", routes)


class ResolveBackportDataRootTests(unittest.TestCase):
    """F2 snapshot-root resolution for run-review-branch (explicit, smart default, absent)."""

    def test_explicit_passthrough(self) -> None:
        self.assertEqual(_resolve_backport_data_root("/some/snapshot"), "/some/snapshot")

    def test_defaults_to_repo_phase2_when_spec_master_synced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data" / "phase2").mkdir(parents=True)
            (root / "data" / "phase2" / "Spec_Master.csv").write_text("document_key\n", encoding="utf-8")
            with patch("tools.cloud_doc_backport.get_paths", return_value=SimpleNamespace(root=root)):
                self.assertEqual(_resolve_backport_data_root(None), str(root / "data" / "phase2"))

    def test_none_when_phase2_unsynced(self) -> None:
        # data/phase2 without Spec_Master.csv (the gitignored sync artifact is absent)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data" / "phase2").mkdir(parents=True)
            with patch("tools.cloud_doc_backport.get_paths", return_value=SimpleNamespace(root=root)):
                self.assertIsNone(_resolve_backport_data_root(None))


class RebuildRediffBlessedGateTests(unittest.TestCase):
    """R7: the rebuild+rediff idempotency gate fires in the blessed run-review-branch
    write path (was inert before), and on run-review's in-place baseline."""

    @staticmethod
    def _final_json(captured: str) -> dict:
        for line in reversed(captured.splitlines()):
            line = line.strip()
            if line.startswith("{"):
                return json.loads(line)
        raise AssertionError("no JSON object in output")

    def test_inplace_baseline_override_runs_gate_instead_of_skipping(self) -> None:
        report = {
            "run_id": "t",
            "baseline": "docs/_review/JE-1000F/US/page/00_preface.rst",
            "source_target": {"path": "docs/_review/JE-1000F/US/page/00_preface.rst"},
            "deltas": [{
                "route_class": "repo_review_text",
                "old_normalized": "Old line", "new_normalized": "New line", "delta_hash": "h1",
            }],
        }
        # no override: baseline == source -> skip (gate-pass), the prior behavior
        skipped = _rebuild_rediff_for_report(report, "New line\n")
        self.assertTrue(skipped["skipped"])
        # in-memory pre-edit baseline supplied -> the gate runs; a clean apply passes
        ran = _rebuild_rediff_for_report(report, "New line\n", baseline_text_override="Old line\n")
        self.assertFalse(ran.get("skipped", False))
        self.assertTrue(ran["passed"])
        # a collateral change (not among the intended deltas) is caught
        collateral = _rebuild_rediff_for_report(report, "New line\n\nStray addition\n", baseline_text_override="Old line\n")
        self.assertFalse(collateral["passed"])
        self.assertTrue(collateral["unexpected"])

    def test_verify_report_threads_inmemory_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            page_dir = Path(tmp) / "docs/_review/JE-1000F/US/page"
            page_dir.mkdir(parents=True)
            src = page_dir / "00_preface.rst"
            src.write_text("New line\n", encoding="utf-8")  # the post-apply source
            report = build_report(
                run_id="t", doc_type="review", doc_url="fixture",
                baseline_path=src, fetched_text="New line\n", baseline_text="Old line\n",
                command=["x"], source_path=src, section_title=None,
                section_inferred_from=None, require_section_match=False,
            )
            verify = build_review_verify_report(report, source_path=src, baseline_text="Old line\n")
            self.assertFalse(verify["rebuild_rediff"].get("skipped", False))  # ran, did not skip
            self.assertTrue(verify["rebuild_rediff"]["passed"])

    def _baseline_args(self, tmp, **over):
        base = dict(
            cloud_doc="https://example.feishu.cn/wiki/doc-r7", run_id="r7",
            out=str(Path(tmp) / "out"), lark_cli="lark-cli", write=True, push=False,
            doc_name="manual_je1000f_us_en_1.0", lang=None, data_root=None,
            git_bin="git", remote="origin",
        )
        base.update(over)
        return SimpleNamespace(**base)

    def test_blessed_baseline_path_runs_gate_and_passes_on_clean_apply(self) -> None:
        import contextlib
        import io

        with tempfile.TemporaryDirectory() as tmp:
            page_dir = Path(tmp) / "docs/_review/JE-1000F/US/page"
            page_dir.mkdir(parents=True)
            (page_dir / "00_preface.rst").write_text("**FR IMPORTANT**\n\nKeep this manual handy.\n", encoding="utf-8")
            out = io.StringIO()
            with patch("tools.cloud_doc_backport.fetch_doc_text", return_value="**FR IMPORTANT test**\n\nKeep this manual handy.\n"):
                with contextlib.redirect_stdout(out):
                    rc = _run_review_branch_baseline(
                        self._baseline_args(tmp),
                        resolved={"git_ref": "review/JE-1000F-US", "pr_url": None},
                        worktree=tmp, review_dir="docs/_review/JE-1000F/US", doc_tok="doc-r7",
                        baseline_text="**FR IMPORTANT**\n\nKeep this manual handy.\n",
                    )
            self.assertEqual(rc, 0)
            payload = self._final_json(out.getvalue())
            self.assertTrue(payload["rebuild_rediff"]["passed"])  # the gate ran and passed

    def test_blessed_baseline_path_gate_failure_blocks_push(self) -> None:
        import contextlib
        import io

        opened: list[bool] = []

        def fake_open_pr(**_kw):
            opened.append(True)
            return True, "https://example/pr"

        with tempfile.TemporaryDirectory() as tmp:
            page_dir = Path(tmp) / "docs/_review/JE-1000F/US/page"
            page_dir.mkdir(parents=True)
            (page_dir / "00_preface.rst").write_text("**FR IMPORTANT**\n\nKeep this manual handy.\n", encoding="utf-8")
            args = self._baseline_args(tmp, push=True)
            err = io.StringIO()
            with patch("tools.cloud_doc_backport.fetch_doc_text", return_value="**FR IMPORTANT test**\n\nKeep this manual handy.\n"), \
                 patch("tools.cloud_doc_backport._rebuild_rediff_gate", return_value={"passed": False, "unexpected": ["x->y"], "missing": []}), \
                 patch("tools.cloud_doc_backport._open_backport_pr", side_effect=fake_open_pr):
                with contextlib.redirect_stderr(err):
                    rc = _run_review_branch_baseline(
                        args, resolved={"git_ref": "review/JE-1000F-US", "pr_url": None},
                        worktree=tmp, review_dir="docs/_review/JE-1000F/US", doc_tok="doc-r7b",
                        baseline_text="**FR IMPORTANT**\n\nKeep this manual handy.\n",
                    )
            self.assertEqual(rc, 1)  # gate failed -> non-zero
            self.assertEqual(opened, [])  # push was refused
            self.assertIn("gate FAILED", err.getvalue())


class BaselineArtifactEmissionTests(unittest.TestCase):
    """The blessed baseline path emits the actionable Class D / Class T artifacts
    (change-request, template-sync proposal, suggestions) — not just the diff report —
    so apply-source-table and the template-sync role have something to consume."""

    @staticmethod
    def _final_json(captured: str) -> dict:
        for line in reversed(captured.splitlines()):
            line = line.strip()
            if line.startswith("{"):
                return json.loads(line)
        raise AssertionError("no JSON object in output")

    def _args(self, tmp, **over):
        base = dict(
            cloud_doc="https://example.feishu.cn/wiki/doc-art", run_id="art",
            out=str(Path(tmp) / "out"), lark_cli="lark-cli", write=False, push=False,
            doc_name="manual_je1000f_us_en_1.0", lang=None, data_root=None,
            git_bin="git", remote="origin",
        )
        base.update(over)
        return SimpleNamespace(**base)

    def test_baseline_path_emits_actionable_artifacts(self) -> None:
        import contextlib
        import io

        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "docs/_review/JE-1000F/US/page").mkdir(parents=True)
            out = io.StringIO()
            with patch("tools.cloud_doc_backport.fetch_doc_text", return_value="Keep this manual handy edited.\n"):
                with contextlib.redirect_stdout(out):
                    rc = _run_review_branch_baseline(
                        self._args(tmp),
                        resolved={"git_ref": "review/JE-1000F-US", "pr_url": None},
                        worktree=tmp, review_dir="docs/_review/JE-1000F/US", doc_tok="doc-art",
                        baseline_text="Keep this manual handy.\n",
                    )
            self.assertEqual(rc, 0)
            out_dir = Path(tmp) / "out"
            # the change-request report (apply-source-table input) and the template-sync
            # proposal are written — not just the diff report
            self.assertTrue((out_dir / "cloud_doc_backport_source_table_change_request.json").is_file())
            self.assertTrue((out_dir / "cloud_doc_backport_template_sync_proposal.json").is_file())
            self.assertTrue((out_dir / "cloud_doc_backport_source_table_suggestions.json").is_file())
            payload = self._final_json(out.getvalue())
            # the JSON points apply-source-table at the change-request report, not the diff report
            self.assertTrue(payload["source_table_change_request"].endswith("cloud_doc_backport_source_table_change_request.json"))
            self.assertIn("template_sync_proposal", payload)
            self.assertNotIn("source_table_report", payload)  # the misleading diff-report alias is gone

    def test_baseline_path_class_t_delta_becomes_proposal(self) -> None:
        import contextlib
        import io

        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "docs/_review/JE-1000F/US/page").mkdir(parents=True)
            sibling = Path(tmp) / "sibling.rst"
            sibling.write_text("Shared safety note\n", encoding="utf-8")  # same line as the baseline
            out = io.StringIO()
            args = self._args(tmp, sibling=[str(sibling)])
            with patch("tools.cloud_doc_backport.fetch_doc_text", return_value="Shared safety note revised\n"):
                with contextlib.redirect_stdout(out):
                    _run_review_branch_baseline(
                        args, resolved={"git_ref": "review/JE-1000F-US", "pr_url": None},
                        worktree=tmp, review_dir="docs/_review/JE-1000F/US", doc_tok="doc-art2",
                        baseline_text="Shared safety note\n",
                    )
            payload = self._final_json(out.getvalue())
            # the delta's old text is shared with the sibling -> Class T -> a template-sync proposal
            self.assertGreaterEqual(payload["template_sync_proposals"], 1)
            proposal = json.loads((Path(tmp) / "out" / "cloud_doc_backport_template_sync_proposal.json").read_text(encoding="utf-8"))
            self.assertGreaterEqual(proposal["summary"]["proposals"], 1)


class ClassRBlockApplyTests(unittest.TestCase):
    """Class R deterministic apply: literal-first (markup-preserving) with a block fallback
    for reST headings / role-bearing / soft-wrapped prose the literal match can't reach.
    Three guards: unique block hit, plain-block isomorphism, R7 rebuild+rediff gate."""

    def test_rst_display_width_cjk_vs_ascii(self) -> None:
        self.assertEqual(_rst_display_width("添加设备"), 8)   # 4 CJK chars = 8 columns
        self.assertEqual(_rst_display_width("Setup"), 5)      # ASCII = char count
        self.assertEqual(_rst_display_width("添加设备 X"), 10)  # mixed (8 + space + X)

    def test_heading_text_key_strips_markdown_hashes(self) -> None:
        self.assertEqual(_heading_text_key("## 添加设备"), "添加设备")
        self.assertEqual(_heading_text_key("# 添加设备"), "添加设备")  # level-agnostic
        self.assertEqual(_heading_text_key("Plain title"), "Plain title")

    def test_review_block_is_plain_accepts_plain_rejects_markup(self) -> None:
        from tools.cloud_doc_backport import Block

        def para(text: str, norm: str) -> Block:
            return Block(kind="paragraph", text=text, normalized=norm, heading_path=(), line_no=1)

        self.assertTrue(_review_block_is_plain("纯文本说明。\n", para("纯文本说明。", "纯文本说明。")))
        self.assertFalse(_review_block_is_plain("按 **OK** 键。\n", para("按 **OK** 键。", "按 OK 键。")))
        self.assertFalse(_review_block_is_plain("按 :guilabel:`OK` 键。\n", para("按 :guilabel:`OK` 键。", "按 :guilabel:`OK` 键。")))
        self.assertFalse(_review_block_is_plain("电压 |VOLT| 值。\n", para("电压 |VOLT| 值。", "电压 |VOLT| 值。")))

    def _report(self, tmp, src, baseline_md, fetched_md):
        page_dir = Path(tmp) / "docs/_review/JE-1000F/US/page"
        page_dir.mkdir(parents=True, exist_ok=True)
        preface = page_dir / "00_preface.rst"
        preface.write_text(src, encoding="utf-8")
        report = build_report(
            run_id="t", doc_type="review", doc_url="fixture",
            baseline_path=preface, fetched_text=fetched_md, baseline_text=baseline_md,
            command=["x"], source_path=preface, section_title=None,
            section_inferred_from=None, require_section_match=False,
        )
        return report, preface

    def test_heading_edit_applies_via_block_fallback_and_recomputes_underline(self) -> None:
        # reST heading (rendered `## X` vs source `X\n===`) never byte-matches literally; the
        # block fallback rewrites the title AND the underline (to the new title's DISPLAY width).
        with tempfile.TemporaryDirectory() as tmp:
            report, preface = self._report(
                tmp,
                src="添加设备\n========\n\n正文保持不变。\n",
                baseline_md="## 添加设备\n\n正文保持不变。\n",
                fetched_md="## 添加新设备\n\n正文保持不变。\n",
            )
            ap = build_review_apply_report(report, source_path=preface, write=True, command=["x"])
            self.assertEqual(ap["summary"]["statuses"].get("applied"), 1)
            out = preface.read_text(encoding="utf-8")
            self.assertIn("添加新设备\n" + "=" * 10 + "\n", out)  # 5 CJK chars = 10 cols, char preserved
            self.assertIn("正文保持不变。", out)  # body untouched

    def test_heading_edit_not_found_abstains(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report, preface = self._report(
                tmp,
                src="其他标题\n========\n\n正文。\n",
                baseline_md="## 添加设备\n\n正文。\n",
                fetched_md="## 增加设备\n\n正文。\n",
            )
            ap = build_review_apply_report(report, source_path=preface, write=True, command=["x"])
            self.assertFalse(ap["summary"]["changed"])
            self.assertEqual(preface.read_text(encoding="utf-8"), "其他标题\n========\n\n正文。\n")

    def test_heading_edit_ambiguous_abstains(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report, preface = self._report(
                tmp,
                src="添加设备\n========\n\n中段。\n\n添加设备\n========\n\n尾段。\n",
                baseline_md="## 添加设备\n\n中段。\n\n## 添加设备\n\n尾段。\n",
                fetched_md="## 增加设备\n\n中段。\n\n## 添加设备\n\n尾段。\n",
            )
            ap = build_review_apply_report(report, source_path=preface, write=True, command=["x"])
            self.assertFalse(ap["summary"]["changed"])  # title appears twice -> abstain

    def test_literal_path_preserves_inline_markup(self) -> None:
        # Same-form markup (**bold** is identical in markdown and reST) stays on the literal
        # path so the markup is preserved (new_text, not new_normalized).
        with tempfile.TemporaryDirectory() as tmp:
            report, preface = self._report(
                tmp,
                src="**重要** 提示。\n",
                baseline_md="**重要** 提示。\n",
                fetched_md="**重要** 安全提示。\n",
            )
            ap = build_review_apply_report(report, source_path=preface, write=True, command=["x"])
            self.assertEqual(ap["summary"]["statuses"].get("applied"), 1)
            self.assertIn("**重要** 安全提示。", preface.read_text(encoding="utf-8"))  # ** kept

    def test_rebuild_rediff_gate_matches_heading_on_title(self) -> None:
        # The expected delta carries markdown `## X` while the reST source re-diff yields `# X`;
        # the gate must compare headings on TITLE only, else every heading write fails the gate.
        deltas = [{
            "route_class": "repo_review_text", "change_type": "replace",
            "old_normalized": "## 添加设备", "new_normalized": "## 增加设备",
            "location": {"kind": "heading"},
        }]
        gate = _rebuild_rediff_gate(
            baseline_text="添加设备\n========\n", edited_text="增加设备\n========\n",
            deltas=deltas, run_id="t",
        )
        self.assertTrue(gate["passed"])
        self.assertEqual(gate["unexpected"], [])
        self.assertEqual(gate["missing"], [])

    def test_run_review_branch_heading_edit_opens_backport_pr(self) -> None:
        # End-to-end: a heading edit now lands (changed != []) so the existing PR path fires.
        import contextlib
        import io

        opened: dict = {}

        def fake_open_pr(**kw):
            opened.update(kw)
            return True, "https://github.com/x/y/pull/99"

        with tempfile.TemporaryDirectory() as tmp:
            page_dir = Path(tmp) / "docs/_review/JE-1000F/US/page"
            page_dir.mkdir(parents=True)
            (page_dir / "00_preface.rst").write_text("添加设备\n========\n\n正文。\n", encoding="utf-8")
            args = SimpleNamespace(
                cloud_doc="https://example.feishu.cn/wiki/doc-h", run_id="he2e",
                out=str(Path(tmp) / "out"), lark_cli="lark-cli", write=True, push=True,
                doc_name="manual_je1000f_us_en_1.0", lang=None, data_root=None,
                git_bin="git", remote="origin",
            )
            out = io.StringIO()
            with patch("tools.cloud_doc_backport.fetch_doc_text", return_value="## 增加设备\n\n正文。\n"), \
                 patch("tools.cloud_doc_backport._open_backport_pr", side_effect=fake_open_pr):
                with contextlib.redirect_stdout(out):
                    rc = _run_review_branch_baseline(
                        args, resolved={"git_ref": "review/JE-1000F-US", "pr_url": None},
                        worktree=tmp, review_dir="docs/_review/JE-1000F/US", doc_tok="doc-h",
                        baseline_text="## 添加设备\n\n正文。\n",
                    )
            self.assertEqual(rc, 0)
            payload = [json.loads(ln) for ln in out.getvalue().splitlines() if ln.strip().startswith("{")][-1]
            self.assertEqual(payload["changed"], ["docs/_review/JE-1000F/US/page/00_preface.rst"])
            self.assertTrue(payload["rebuild_rediff"]["passed"])
            self.assertEqual(payload["backport_pr_url"], "https://github.com/x/y/pull/99")
            self.assertEqual(opened.get("git_ref"), "review/JE-1000F-US")
            self.assertIn("增加设备", (page_dir / "00_preface.rst").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
