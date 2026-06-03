from __future__ import annotations

import argparse
import io
import itertools
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from tools import queue_execute, queue_query


def _control_layer_side_effect(*, dispatch_payload, status_outcomes):
    """Fake `_run_control_layer_cli`: dispatch returns a fixed payload; each
    status call yields the next entry from `status_outcomes` (a dict is
    returned, an Exception is raised), repeating the last entry once exhausted.
    """
    outcomes = list(status_outcomes)
    state = {"i": 0}

    def _side_effect(repo_root, *cli_args):
        action = cli_args[0] if cli_args else ""
        if action == "dispatch":
            return dict(dispatch_payload)
        if action == "status":
            index = min(state["i"], len(outcomes) - 1)
            state["i"] += 1
            outcome = outcomes[index]
            if isinstance(outcome, Exception):
                raise outcome
            return dict(outcome)
        raise AssertionError(f"unexpected control-layer args: {cli_args}")

    return _side_effect


def _refreshed_draft_row(*, result_is_fresh, freshness_status, result="SUCCESS"):
    base = _draft_row()
    return queue_query.QueueQueryRow(
        **{
            **base.__dict__,
            "result": result,
            "result_is_fresh": result_is_fresh,
            "freshness_status": freshness_status,
        }
    )


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
    document_key: str = '{"id":"recvhoZFKGg7l0"}',
    review_trigger_enabled: bool | None = True,
    task_id: str | None = None,
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
        task_id="JE-1000F_EU___Start Review" if task_id is None else task_id,
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
            "fresh_since": None,
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

        self.assertFalse(resolved_args.document_key)
        self.assertEqual("JE-1000F_EU_Start Review", resolved_args.task_id)
        self.assertEqual("start-review", resolved_args.query_workflow_action)
        self.assertEqual("rec_eu_review", row.record_id)
        self.assertEqual("start-review", queue_execute.dispatch_command_for_row(row))
        queue_execute.ensure_start_review_dispatchable(row)

    def test_select_unique_queue_row_should_resolve_restart_review_phrase(self) -> None:
        resolved_args, row = queue_execute.select_unique_queue_row(
            self._args(query_text="重新开始review JE-2000F_EU"),
            [
                _document_key_start_review_row(
                    record_id="recvlsa1VML5nT",
                    document_key="JE-2000F_EU",
                    task_id="",
                )
            ],
        )

        self.assertEqual("JE-2000F_EU_Start Review", resolved_args.task_id)
        self.assertEqual("start-review", resolved_args.query_workflow_action)
        self.assertEqual("recvlsa1VML5nT", row.record_id)
        self.assertEqual("start-review", queue_execute.dispatch_command_for_row(row))
        queue_execute.ensure_start_review_dispatchable(row)

    def test_start_review_dispatch_should_require_document_key(self) -> None:
        row = _document_key_start_review_row(document_key="")

        with self.assertRaisesRegex(RuntimeError, "without a Document_Key value"):
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
                "freshness_status": "not_requested",
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

    def test_is_terminal_failure_should_detect_terminal_non_success(self) -> None:
        self.assertTrue(queue_execute.is_terminal_failure({"status": "completed", "conclusion": "failure"}))
        self.assertTrue(queue_execute.is_terminal_failure({"failure_message": "缺少规格数据"}))

    def test_is_terminal_failure_should_ignore_pending_or_unknown_status(self) -> None:
        self.assertFalse(queue_execute.is_terminal_failure({"status": "in_progress", "conclusion": ""}))
        self.assertFalse(queue_execute.is_terminal_failure({"status": "", "conclusion": ""}))
        self.assertFalse(queue_execute.is_terminal_failure({"status": "completed", "conclusion": "success"}))

    def _run_queue_execute_with_mocks(
        self,
        *,
        refreshed_row: queue_query.QueueQueryRow,
        dispatch_payload: dict,
        status_outcomes: list,
        json_output: bool = False,
    ) -> str:
        stdout = io.StringIO()
        side_effect = _control_layer_side_effect(
            dispatch_payload=dispatch_payload,
            status_outcomes=status_outcomes,
        )
        with mock.patch.object(queue_execute, "load_config", return_value={}), \
            mock.patch.object(queue_execute, "collect_queue_query_rows", return_value=[_draft_row()]), \
            mock.patch.object(queue_execute, "_refresh_queue_row", return_value=refreshed_row), \
            mock.patch.object(queue_execute, "_run_control_layer_cli", side_effect=side_effect), \
            mock.patch.object(queue_execute.time, "sleep", return_value=None), \
            mock.patch.object(queue_execute.time, "monotonic", side_effect=itertools.count(0, 1000)), \
            redirect_stdout(stdout):
            queue_execute.run_queue_execute(
                self._args(
                    record_id="rec_draft",
                    queue_scope="document-link",
                    wait_timeout_seconds=1,
                    status_poll_seconds=0.5,
                    json=json_output,
                ),
                config_path=Path("config.us.yaml"),
                repo_root=Path("."),
            )
        return stdout.getvalue()

    def test_run_queue_execute_should_not_fail_when_status_read_errors_but_base_is_fresh(self) -> None:
        # JE-1000F_EU symptom: the status read fetch-fails, but the Base row
        # already shows a fresh SUCCESS. queue-execute must trust the Base
        # writeback, not the local read error.
        output = self._run_queue_execute_with_mocks(
            refreshed_row=_refreshed_draft_row(result_is_fresh=True, freshness_status="fresh"),
            dispatch_payload={
                "run_id": "321",
                "run": "https://example.com/run",
                "accepted_at": "2026-05-29T10:00:00+00:00",
            },
            status_outcomes=[RuntimeError("queue-execute control-layer command failed: fetch failed")],
            json_output=True,
        )

        payload = json.loads(output)
        self.assertEqual("rec_draft", payload["record_id"])
        self.assertTrue(payload["result_is_fresh"])

    def test_run_queue_execute_should_not_fail_on_timeout_when_run_still_pending(self) -> None:
        # The wait deadline elapses before a terminal state and the Base row is
        # not fresh yet. This is "still running", not a failure: print the row
        # with its pending freshness instead of raising.
        output = self._run_queue_execute_with_mocks(
            refreshed_row=_refreshed_draft_row(
                result_is_fresh=None,
                freshness_status="writeback_pending",
                result="",
            ),
            dispatch_payload={"run_id": "321", "run": "https://example.com/run"},
            status_outcomes=[{"status": "in_progress", "conclusion": "", "run_id": "321"}],
            json_output=True,
        )

        payload = json.loads(output)
        self.assertEqual("rec_draft", payload["record_id"])
        self.assertEqual("writeback_pending", payload["freshness_status"])

    def test_run_queue_execute_should_fail_on_terminal_failure_when_base_not_fresh(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            self._run_queue_execute_with_mocks(
                refreshed_row=_refreshed_draft_row(
                    result_is_fresh=False,
                    freshness_status="stale_result",
                    result="FAILED",
                ),
                dispatch_payload={"run_id": "321", "run": "https://example.com/run"},
                status_outcomes=[{"status": "completed", "conclusion": "failure", "run_id": "321"}],
            )

        self.assertIn("record_id=rec_draft", str(ctx.exception))

    def test_run_queue_execute_should_trust_fresh_base_over_terminal_failure_status(self) -> None:
        # A terminal failure status must not override a fresh Base SUCCESS (e.g.
        # a prior failed attempt's status lingering while the row is now fresh).
        output = self._run_queue_execute_with_mocks(
            refreshed_row=_refreshed_draft_row(result_is_fresh=True, freshness_status="fresh"),
            dispatch_payload={"run_id": "321", "run": "https://example.com/run"},
            status_outcomes=[{"status": "completed", "conclusion": "failure", "run_id": "321"}],
            json_output=True,
        )

        payload = json.loads(output)
        self.assertTrue(payload["result_is_fresh"])

    def test_select_queue_rows_returns_all_matching_including_untriggered(self) -> None:
        rows = [
            _draft_row("rec_a"),
            queue_query.QueueQueryRow(**{**_draft_row("rec_b").__dict__, "build_trigger_requested": False}),
        ]
        _resolved, matched = queue_execute.select_queue_rows(
            self._args(query_workflow_action="build-draft-package", allow_multiple=True),
            rows,
        )
        # Batch selection keeps the non-triggered row too, so it can be reported
        # as skipped rather than silently dropped.
        self.assertEqual({"rec_a", "rec_b"}, {r.record_id for r in matched})

    def test_dispatch_one_row_skips_untriggered_draft_without_calling_dispatch(self) -> None:
        row = queue_query.QueueQueryRow(**{**_draft_row("rec_us").__dict__, "build_trigger_requested": False})
        with mock.patch.object(queue_execute, "_run_control_layer_cli") as mock_cli:
            result = queue_execute._dispatch_one_row(self._args(), row, repo_root=Path("."), accepted_at="t0")
        mock_cli.assert_not_called()
        self.assertEqual("skipped", result["status"])
        self.assertFalse(result["dispatched"])
        self.assertIn("是否触发文档构建", result["reason"])

    def test_dispatch_one_row_dispatches_triggered_draft(self) -> None:
        with mock.patch.object(
            queue_execute,
            "_run_control_layer_cli",
            return_value={"run_id": "501", "run": "https://example.com/runs/501", "accepted_at": "t1"},
        ) as mock_cli:
            result = queue_execute._dispatch_one_row(self._args(), _draft_row("rec_cn"), repo_root=Path("."), accepted_at="t0")
        mock_cli.assert_called_once()
        self.assertEqual(("dispatch", "build-draft", "rec_cn"), mock_cli.call_args.args[1:])
        self.assertEqual("dispatched", result["status"])
        self.assertTrue(result["dispatched"])
        self.assertEqual("501", result["run_id"])

    def test_run_queue_execute_batch_dispatches_triggered_and_skips_others(self) -> None:
        triggered = queue_query.QueueQueryRow(
            **{**_draft_row("rec_cn").__dict__, "document_id": "JE-1000F_CN_1.3", "build_family": "cn-zh", "build_trigger_requested": True}
        )
        untriggered = queue_query.QueueQueryRow(
            **{**_draft_row("rec_us").__dict__, "document_id": "JE-1000F_US_1.3", "build_family": "us-merged", "build_trigger_requested": False}
        )
        dispatch_calls = []

        def fake_cli(repo_root, *cli_args):
            dispatch_calls.append(cli_args)
            if cli_args and cli_args[0] == "dispatch":
                return {"run_id": "501", "run": "https://example.com/runs/501", "accepted_at": "2026-05-29T11:46:00+00:00"}
            raise AssertionError(f"unexpected control-layer args: {cli_args}")

        stdout = io.StringIO()
        with mock.patch.object(queue_execute, "load_config", return_value={}), \
            mock.patch.object(queue_execute, "collect_queue_query_rows", return_value=[triggered, untriggered]), \
            mock.patch.object(queue_execute, "_run_control_layer_cli", side_effect=fake_cli), \
            redirect_stdout(stdout):
            queue_execute.run_queue_execute(
                self._args(
                    allow_multiple=True,
                    json=True,
                    queue_scope="document-link",
                    query_workflow_action="build-draft-package",
                ),
                config_path=Path("config.us.yaml"),
                repo_root=Path("."),
            )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(2, payload["matched_count"])
        self.assertEqual(1, payload["dispatched_count"])
        self.assertEqual(1, payload["skipped_count"])
        self.assertEqual(0, payload["error_count"])
        # Only the triggered row reaches a real dispatch.
        self.assertEqual([("dispatch", "build-draft", "rec_cn")], dispatch_calls)
        by_id = {r["record_id"]: r for r in payload["results"]}
        self.assertEqual("dispatched", by_id["rec_cn"]["status"])
        self.assertEqual("501", by_id["rec_cn"]["run_id"])
        self.assertEqual("skipped", by_id["rec_us"]["status"])
        self.assertFalse(by_id["rec_us"]["dispatched"])
        self.assertIn("是否触发文档构建", by_id["rec_us"]["reason"])


if __name__ == "__main__":
    unittest.main()
