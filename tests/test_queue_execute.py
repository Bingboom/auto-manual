from __future__ import annotations

import argparse
import json
import unittest

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

    def test_select_unique_queue_row_should_raise_for_ambiguous_matches(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            queue_execute.select_unique_queue_row(
                self._args(document_id="JE-1000F_US_en_0.3"),
                [_draft_row("rec_a"), _draft_row("rec_b")],
            )

        self.assertIn("multiple matching queue rows", str(ctx.exception))

    def test_dispatch_command_for_row_should_map_draft(self) -> None:
        self.assertEqual("build-draft", queue_execute.dispatch_command_for_row(_draft_row()))

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
