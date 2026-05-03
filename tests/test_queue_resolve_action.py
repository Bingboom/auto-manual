from __future__ import annotations

import argparse
import json
import unittest

from tools import queue_query, queue_resolve_action


def _draft_row(record_id: str = "rec_draft", *, git_ref: str = "codex/review-id-recvfw0zg4pzxs") -> queue_query.QueueQueryRow:
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
        git_ref=git_ref,
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


def _publish_row(record_id: str = "rec_publish", *, git_ref: str = "codex/review-id-recvfw0zg4pzxs") -> queue_query.QueueQueryRow:
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
        git_ref=git_ref,
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


def _review_row(record_id: str = "rec_review") -> queue_query.QueueQueryRow:
    return queue_query.QueueQueryRow(
        queue_scope="review-init",
        record_id=record_id,
        document_id="JE-1000F_US_0.3",
        document_key="JE-1000F_US",
        build_family="us-merged",
        lang="",
        version="0.3",
        workflow_action="Start Review",
        normalized_workflow_action="start_review",
        git_ref="",
        document_link="",
        document_directory="",
        result="",
        pr_url="",
        review_status="NotStarted",
        review_trigger_enabled=True,
        build_trigger_requested=None,
        immediate_build=None,
        initial_result="",
        remarks="",
    )


class TestQueueResolveAction(unittest.TestCase):
    def _args(self, **overrides) -> argparse.Namespace:
        payload = {
            "query_text": None,
            "queue_scope": "all",
            "record_id": None,
            "task_id": None,
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
            "confirm_publish": False,
        }
        payload.update(overrides)
        return argparse.Namespace(**payload)

    def test_resolve_queue_action_should_resolve_query_status_when_no_write_action_is_requested(self) -> None:
        resolution = queue_resolve_action.resolve_queue_action(
            self._args(document_id="JE-1000F_US_en_0.3"),
            [_draft_row()],
        )

        self.assertEqual("resolved", resolution.resolution_status)
        self.assertEqual("query_status", resolution.action_name)
        self.assertTrue(resolution.ready)
        self.assertIsNone(resolution.dispatch_command)
        self.assertEqual("rec_draft", resolution.row["record_id"])

    def test_resolve_queue_action_should_resolve_start_review(self) -> None:
        resolution = queue_resolve_action.resolve_queue_action(
            self._args(query_text="开始 review JE-1000F us-merged"),
            [_review_row()],
        )

        self.assertEqual("resolved", resolution.resolution_status)
        self.assertEqual("start_review", resolution.action_name)
        self.assertEqual("start-review", resolution.dispatch_command)
        self.assertTrue(resolution.ready)

    def test_resolve_queue_action_should_treat_draft_status_phrase_as_query(self) -> None:
        resolution = queue_resolve_action.resolve_queue_action(
            self._args(query_text="JE-1000F US 草稿包好了没"),
            [_draft_row()],
        )

        self.assertEqual("resolved", resolution.resolution_status)
        self.assertEqual("query_status", resolution.action_name)
        self.assertIsNone(resolution.dispatch_command)
        self.assertEqual("rec_draft", resolution.row["record_id"])

    def test_resolve_queue_action_should_keep_direct_draft_command_executable(self) -> None:
        resolution = queue_resolve_action.resolve_queue_action(
            self._args(query_text="帮我生成 JE-1000F US en 0.3 草稿包"),
            [_draft_row()],
        )

        self.assertEqual("resolved", resolution.resolution_status)
        self.assertEqual("build_draft_package", resolution.action_name)
        self.assertEqual("build-draft", resolution.dispatch_command)

    def test_resolve_queue_action_should_use_task_id_to_disambiguate_actions(self) -> None:
        resolution = queue_resolve_action.resolve_queue_action(
            self._args(task_id="JE-1000F_US_en_0.3_Build Draft Package"),
            [_draft_row(), _publish_row()],
        )

        self.assertEqual("resolved", resolution.resolution_status)
        self.assertEqual("rec_draft", resolution.row["record_id"])

    def test_resolve_queue_action_should_require_publish_confirmation(self) -> None:
        resolution = queue_resolve_action.resolve_queue_action(
            self._args(document_id="JE-1000F_US_0.3", query_workflow_action="publish"),
            [_publish_row()],
        )

        self.assertEqual("confirmation_required", resolution.resolution_status)
        self.assertEqual("publish", resolution.action_name)
        self.assertEqual("publish", resolution.dispatch_command)
        self.assertFalse(resolution.ready)
        self.assertTrue(resolution.requires_confirmation)

    def test_resolve_queue_action_should_resolve_publish_with_confirmation(self) -> None:
        resolution = queue_resolve_action.resolve_queue_action(
            self._args(document_id="JE-1000F_US_0.3", query_workflow_action="publish", confirm_publish=True),
            [_publish_row()],
        )

        self.assertEqual("resolved", resolution.resolution_status)
        self.assertEqual("publish", resolution.action_name)
        self.assertTrue(resolution.ready)

    def test_resolve_queue_action_should_report_missing_required_git_ref(self) -> None:
        resolution = queue_resolve_action.resolve_queue_action(
            self._args(document_id="JE-1000F_US_en_0.3", query_workflow_action="build-draft-package"),
            [_draft_row(git_ref="")],
        )

        self.assertEqual("missing_required_field", resolution.resolution_status)
        self.assertIn("git_ref", resolution.missing_fields)
        self.assertFalse(resolution.ready)

    def test_resolve_queue_action_should_report_ambiguous_targets(self) -> None:
        resolution = queue_resolve_action.resolve_queue_action(
            self._args(document_id="JE-1000F_US_en_0.3"),
            [_draft_row("rec_a"), _draft_row("rec_b")],
        )

        self.assertEqual("ambiguous_target", resolution.resolution_status)
        self.assertEqual(2, resolution.matched_count)
        self.assertEqual(["rec_a", "rec_b"], [candidate.record_id for candidate in resolution.candidates])

    def test_resolve_queue_action_should_report_target_not_found(self) -> None:
        resolution = queue_resolve_action.resolve_queue_action(
            self._args(record_id="rec_missing", query_workflow_action="start-review"),
            [_review_row()],
        )

        self.assertEqual("target_not_found", resolution.resolution_status)
        self.assertEqual("start_review", resolution.action_name)
        self.assertFalse(resolution.ready)

    def test_render_queue_action_resolution_should_emit_json_payload(self) -> None:
        rendered = queue_resolve_action.render_queue_action_resolution(
            queue_resolve_action.resolve_queue_action(
                self._args(document_id="JE-1000F_US_en_0.3"),
                [_draft_row()],
            ),
            as_json=True,
        )
        payload = json.loads(rendered)

        self.assertEqual("resolved", payload["resolution_status"])
        self.assertEqual("query_status", payload["action_name"])
        self.assertEqual("rec_draft", payload["row"]["record_id"])


if __name__ == "__main__":
    unittest.main()
