from __future__ import annotations

import argparse
import json
import unittest

from tools import queue_query


class TestQueueQuery(unittest.TestCase):
    def _args(self, **overrides) -> argparse.Namespace:
        payload = {
            "query_text": None,
            "queue_scope": "all",
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
        }
        payload.update(overrides)
        return argparse.Namespace(**payload)

    def test_filter_queue_query_rows_should_match_document_link_filters(self) -> None:
        rows = [
            queue_query.QueueQueryRow(
                queue_scope="document-link",
                record_id="rec_draft",
                document_id="JE-1000F_US_0.3",
                document_key="JE-1000F_US",
                build_family="us-merged",
                lang="en",
                version="0.3",
                workflow_action="Build Draft Package",
                normalized_workflow_action="draft",
                git_ref="codex/review-id-recvfw0zg4pzxs",
                document_link="",
                document_directory="",
                result="SUCCESS",
                pr_url="",
                review_status="",
                review_trigger_enabled=None,
                build_trigger_requested=True,
                immediate_build=True,
                initial_result="",
                remarks="",
            ),
            queue_query.QueueQueryRow(
                queue_scope="document-link",
                record_id="rec_publish",
                document_id="JE-1000F_US_0.3",
                document_key="JE-1000F_US",
                build_family="us-merged",
                lang="en",
                version="0.3",
                workflow_action="Publish",
                normalized_workflow_action="publish",
                git_ref="codex/review-id-recvfw0zg4pzxs",
                document_link="https://example.com/doc",
                document_directory="/tmp/doc.docx",
                result="FAILED | sphinx-build exploded",
                pr_url="",
                review_status="",
                review_trigger_enabled=None,
                build_trigger_requested=False,
                immediate_build=False,
                initial_result="",
                remarks="",
            ),
        ]

        filtered = queue_query.filter_queue_query_rows(
            self._args(
                document_id="JE-1000F_US_0.3",
                query_workflow_action="build-draft-package",
                git_ref_contains="recvfw0zg4pzxs",
            ),
            rows,
        )

        self.assertEqual(["rec_draft"], [row.record_id for row in filtered])

    def test_filter_queue_query_rows_should_normalize_start_review_alias(self) -> None:
        rows = [
            queue_query.QueueQueryRow(
                queue_scope="review-init",
                record_id="rec_review",
                document_id="JE-1000F_US_0.3",
                document_key="JE-1000F_US",
                build_family="us-merged",
                lang="en",
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
        ]

        filtered = queue_query.filter_queue_query_rows(
            self._args(query_workflow_action="start-review"),
            rows,
        )

        self.assertEqual(["rec_review"], [row.record_id for row in filtered])

    def test_infer_queue_query_from_text_should_prefer_document_id(self) -> None:
        inferred = queue_query.infer_queue_query_from_text(
            "请帮我查 JE-1000F_US_0.3 的 Build Draft Package 记录。先不要触发 workflow。"
        )

        self.assertEqual("JE-1000F_US_0.3", inferred.document_id)
        self.assertEqual("", inferred.document_key)
        self.assertEqual("build-draft-package", inferred.query_workflow_action)
        self.assertEqual("document-link", inferred.queue_scope)

    def test_infer_queue_query_from_text_should_parse_spaced_document_id(self) -> None:
        inferred = queue_query.infer_queue_query_from_text("帮我生成 JE-1000F US en 0.3 草稿")

        self.assertEqual("JE-1000F_US_en_0.3", inferred.document_id)
        self.assertEqual("", inferred.document_key)
        self.assertEqual("build-draft-package", inferred.query_workflow_action)
        self.assertEqual("document-link", inferred.queue_scope)

    def test_infer_queue_query_from_text_should_parse_document_key_for_link_queries(self) -> None:
        inferred = queue_query.infer_queue_query_from_text("把 JE-1000F US 最新链接发我")

        self.assertEqual("", inferred.document_id)
        self.assertEqual("JE-1000F_US", inferred.document_key)
        self.assertEqual("", inferred.query_workflow_action)
        self.assertEqual("document-link", inferred.queue_scope)

    def test_infer_queue_query_from_text_should_parse_start_review_and_build_family(self) -> None:
        inferred = queue_query.infer_queue_query_from_text("开始 review JE-1000F us-merged")

        self.assertEqual("", inferred.document_id)
        self.assertEqual("us-merged", inferred.build_family)
        self.assertEqual("start-review", inferred.query_workflow_action)
        self.assertEqual("review-init", inferred.queue_scope)

    def test_apply_inferred_queue_query_should_not_override_explicit_filters(self) -> None:
        resolved = queue_query.apply_inferred_queue_query(
            self._args(
                query_text="请帮我查 JE-1000F_US_0.3 的 Build Draft Package 记录。",
                document_id="MANUAL_OVERRIDE",
                query_workflow_action="publish",
            )
        )

        self.assertEqual("MANUAL_OVERRIDE", resolved.document_id)
        self.assertEqual("publish", resolved.query_workflow_action)

    def test_apply_inferred_queue_query_should_fill_failure_reason_filters(self) -> None:
        resolved = queue_query.apply_inferred_queue_query(
            self._args(query_text="为什么 JE-1000F US 0.3 构建失败")
        )

        self.assertEqual("JE-1000F_US_0.3", resolved.document_id)
        self.assertEqual("fail", resolved.result_contains)
        self.assertEqual("document-link", resolved.queue_scope)

    def test_render_queue_query_rows_should_emit_json_payload(self) -> None:
        rows = [
            queue_query.QueueQueryRow(
                queue_scope="document-link",
                record_id="rec_draft",
                document_id="JE-1000F_US_0.3",
                document_key="JE-1000F_US",
                build_family="us-merged",
                lang="en",
                version="0.3",
                workflow_action="Build Draft Package",
                normalized_workflow_action="draft",
                git_ref="codex/review-id-recvfw0zg4pzxs",
                document_link="https://example.com/doc",
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
        ]

        rendered = queue_query.render_queue_query_rows(rows, as_json=True)
        payload = json.loads(rendered)

        self.assertEqual(1, payload["count"])
        self.assertEqual("rec_draft", payload["rows"][0]["record_id"])


if __name__ == "__main__":
    unittest.main()
