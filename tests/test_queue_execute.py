from __future__ import annotations

import argparse
import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from tools import queue_execute, queue_query


def _draft_row(record_id: str = "rec_draft") -> queue_query.QueueQueryRow:
    return queue_query.QueueQueryRow(
        queue_scope="document-link",
        record_id=record_id,
        document_id="JE-1000F_US_en_0.3",
        document_key="JE-1000F_US",
        build_family="us-en",
        lang="en",
        version="0.3",
        workflow_action="Build Draft Package",
        normalized_workflow_action="draft",
        git_ref="codex/review-id-recvfw0zg4pzxs",
        document_link="https://example.com/doc.docx",
        document_directory="/tmp/doc.docx",
        result="SUCCESS",
        pr_url="",
        review_status="",
        review_trigger_enabled=None,
        build_trigger_requested=True,
        immediate_build=True,
        initial_result="",
        remarks="",
    )


def _publish_row(record_id: str = "rec_publish") -> queue_query.QueueQueryRow:
    return queue_query.QueueQueryRow(
        queue_scope="document-link",
        record_id=record_id,
        document_id="JE-1000F_US_0.3",
        document_key="JE-1000F_US",
        build_family="us-merged",
        lang="",
        version="0.3",
        workflow_action="Publish",
        normalized_workflow_action="publish",
        git_ref="codex/review-id-recvfw0zg4pzxs",
        document_link="https://example.com/publish.docx",
        document_directory="/tmp/publish.docx",
        result="SUCCESS",
        pr_url="",
        review_status="",
        review_trigger_enabled=None,
        build_trigger_requested=True,
        immediate_build=True,
        initial_result="",
        remarks="",
    )


def _completed_start_review_row(record_id: str = "rec_review") -> queue_query.QueueQueryRow:
    return queue_query.QueueQueryRow(
        queue_scope="review-init",
        record_id=record_id,
        document_id="JE-1000F_JP_0.6",
        document_key="JE-1000F_JP",
        build_family="jp-ja",
        lang="ja",
        version="0.6",
        workflow_action="Start Review",
        normalized_workflow_action="start_review",
        git_ref="codex/review-je-1000f-jp",
        document_link="",
        document_directory="",
        result="",
        pr_url="https://github.com/Bingboom/auto-manual/pull/120",
        review_status="InReview",
        review_trigger_enabled=False,
        build_trigger_requested=None,
        immediate_build=None,
        initial_result="",
        remarks="",
    )


def _document_key_start_review_row(
    record_id: str = "rec_eu_review",
    *,
    document_key: str = "JE-1000F_EU",
    review_trigger_enabled: bool | None = True,
) -> queue_query.QueueQueryRow:
    return queue_query.QueueQueryRow(
        queue_scope="review-init",
        record_id=record_id,
        document_id="",
        document_key=document_key,
        build_family="",
        lang="",
        version="",
        workflow_action="Start Review",
        normalized_workflow_action="start_review",
        git_ref="",
        document_link="",
        document_directory="",
        result="",
        pr_url="",
        review_status="NotStarted",
        review_trigger_enabled=review_trigger_enabled,
        build_trigger_requested=None,
        immediate_build=None,
        initial_result="",
        remarks="",
        task_id="JE-1000F_EU___Start Review",
    )


class TestQueueExecute(unittest.TestCase):
    def _args(self, **overrides) -> argparse.Namespace:
        payload = {
            "query_text": None,
            "record_id": None,
            "document_id": None,
            "document_key": None,
            "build_family": None,
            "lang": None,
            "document_version": None,
            "query_workflow_action": None,
            "git_ref_contains": None,
            "result_contains": None,
            "limit": 10,
            "json": False,
            "queue_scope": "all",
            "wait_for_completion": True,
            "wait_timeout_seconds": 420,
            "status_poll_seconds": 3.0,
            "confirm_publish": False,
        }
        payload.update(overrides)
        return argparse.Namespace(**payload)

    def test_select_unique_queue_row_should_use_document_id_first_inference(self) -> None:
        resolved_args, row = queue_execute.select_unique_queue_row(
            self._args(query_text="请帮我构建 JE-1000F_US_en_0.3，并返回 Build Draft Package 记录。"),
            [_draft_row()],
        )

        self.assertEqual("JE-1000F_US_en_0.3", resolved_args.document_id)
        self.assertEqual("build-draft-package", resolved_args.query_workflow_action)
        self.assertEqual("rec_draft", row.record_id)

    def test_select_unique_queue_row_should_resolve_spaced_document_id_requests(self) -> None:
        resolved_args, row = queue_execute.select_unique_queue_row(
            self._args(query_text="帮我生成 JE-1000F US en 0.3 草稿"),
            [_draft_row()],
        )

        self.assertEqual("JE-1000F_US_en_0.3", resolved_args.document_id)
        self.assertEqual("build-draft-package", resolved_args.query_workflow_action)
        self.assertEqual("rec_draft", row.record_id)

    def test_select_unique_queue_row_should_resolve_document_key_only_start_review(self) -> None:
        resolved_args, row = queue_execute.select_unique_queue_row(
            self._args(query_text="review JE-1000F_EU"),
            [_document_key_start_review_row()],
        )

        self.assertEqual("JE-1000F_EU", resolved_args.document_key)
        self.assertEqual("start-review", resolved_args.query_workflow_action)
        self.assertEqual("rec_eu_review", row.record_id)
        self.assertEqual("start-review", queue_execute.dispatch_command_for_row(row))
        queue_execute.ensure_start_review_dispatchable(row)

    def test_start_review_dispatch_should_require_document_key(self) -> None:
        row = _document_key_start_review_row(document_key="")

        with self.assertRaisesRegex(RuntimeError, "without a usable Document_Key"):
            queue_execute.ensure_start_review_dispatchable(row)

    def test_start_review_dispatch_should_require_review_checkbox(self) -> None:
        row = _document_key_start_review_row(review_trigger_enabled=False)

        with self.assertRaisesRegex(RuntimeError, "not pending"):
            queue_execute.ensure_start_review_dispatchable(row)

    def test_select_unique_queue_row_should_raise_for_ambiguous_matches(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            queue_execute.select_unique_queue_row(
                self._args(document_id="JE-1000F_US_en_0.3"),
                [_draft_row("rec_a"), _draft_row("rec_b")],
            )

        self.assertIn("multiple matching queue rows", str(ctx.exception))

    def test_dispatch_command_for_row_should_map_draft(self) -> None:
        self.assertEqual("build-draft", queue_execute.dispatch_command_for_row(_draft_row()))

    def test_dispatch_command_for_row_should_map_publish(self) -> None:
        self.assertEqual("publish", queue_execute.dispatch_command_for_row(_publish_row()))

    def test_completed_start_review_row_should_not_require_dispatch(self) -> None:
        row = _completed_start_review_row()

        self.assertTrue(queue_execute.is_completed_start_review_row(row))
        queue_execute.ensure_start_review_dispatchable(row)

    def test_run_queue_execute_should_skip_completed_start_review_dispatch(self) -> None:
        row = _completed_start_review_row()
        stdout = io.StringIO()

        with mock.patch.object(queue_execute, "load_config", return_value={}), \
            mock.patch.object(queue_execute, "collect_queue_query_rows", return_value=[row]), \
            mock.patch.object(queue_execute, "_run_control_layer_cli") as mock_cli, \
            redirect_stdout(stdout):
            queue_execute.run_queue_execute(
                self._args(
                    record_id=row.record_id,
                    queue_scope="review-init",
                    query_workflow_action="start-review",
                    json=True,
                ),
                config_path=Path("config.us.yaml"),
                repo_root=Path("."),
            )

        mock_cli.assert_not_called()
        payload = json.loads(stdout.getvalue())
        self.assertEqual("rec_review", payload["record_id"])
        self.assertEqual("codex/review-je-1000f-jp", payload["git_ref"])
        self.assertEqual("InReview", payload["review_status"])
        self.assertEqual("https://github.com/Bingboom/auto-manual/pull/120", payload["pr_url"])

    def test_parse_control_layer_output_should_extract_key_values(self) -> None:
        payload = queue_execute.parse_control_layer_output(
            "Build Draft Package\nrecord_id: rec_draft\nrun_id: 12345\nrun: https://example.com/run\nDispatch accepted."
        )

        self.assertEqual("Build Draft Package", payload["workflow_name"])
        self.assertEqual("rec_draft", payload["record_id"])
        self.assertEqual("12345", payload["run_id"])
        self.assertEqual("https://example.com/run", payload["run"])
        self.assertIn("Dispatch accepted.", payload["notes"])

    def test_render_queue_execute_result_should_emit_expected_json(self) -> None:
        rendered = queue_execute.render_queue_execute_result(_draft_row(), as_json=True)
        payload = json.loads(rendered)

        self.assertEqual(
            {
                "record_id": "rec_draft",
                "git_ref": "codex/review-id-recvfw0zg4pzxs",
                "result": "SUCCESS",
                "document_link": "https://example.com/doc.docx",
            },
            payload,
        )

    def test_is_successful_status_should_only_accept_success_like_conclusions(self) -> None:
        self.assertTrue(queue_execute.is_successful_status({"conclusion": "success"}))
        self.assertFalse(queue_execute.is_successful_status({"conclusion": "failure"}))
        self.assertFalse(queue_execute.is_successful_status({"status": "completed"}))

    def test_has_structured_failure_should_detect_failure_message(self) -> None:
        self.assertTrue(queue_execute.has_structured_failure({"failure_message": "缺少规格数据"}))
        self.assertFalse(queue_execute.has_structured_failure({"failure_message": ""}))

    def test_ensure_publish_confirmation_should_require_explicit_flag(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            queue_execute.ensure_publish_confirmation(self._args(), _publish_row())

        self.assertIn("--confirm-publish", str(ctx.exception))
        queue_execute.ensure_publish_confirmation(self._args(confirm_publish=True), _publish_row())

    def test_ensure_build_trigger_requested_should_reject_unchecked_draft_row(self) -> None:
        row = queue_query.QueueQueryRow(
            **{
                **_draft_row("rec_unchecked").__dict__,
                "build_trigger_requested": False,
            }
        )

        with self.assertRaises(RuntimeError) as ctx:
            queue_execute.ensure_build_trigger_requested(row)

        self.assertIn("是否触发文档构建", str(ctx.exception))
        self.assertIn("rec_unchecked", str(ctx.exception))

    def test_build_queue_execute_failure_message_should_prefer_structured_failure_summary(self) -> None:
        message = queue_execute.build_queue_execute_failure_message(
            row=_draft_row("rec_review"),
            status_payload={
                "conclusion": "failure",
                "run_id": "1001",
                "run": "https://github.com/example/actions/runs/1001",
                "failure_message": "缺少 JE-1000F_CN 的规格数据，无法进入 review。",
                "failure_next_step": "请先补齐 JE-1000F_CN 在 Spec_Master 中的规格数据，再重试。",
            },
            dispatch_payload={},
        )

        self.assertIn("缺少 JE-1000F_CN 的规格数据，无法进入 review。", message)
        self.assertIn("请先补齐 JE-1000F_CN 在 Spec_Master 中的规格数据，再重试。", message)
        self.assertIn("record_id=rec_review", message)
        self.assertIn("run_id=1001", message)


if __name__ == "__main__":
    unittest.main()
