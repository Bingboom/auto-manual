from __future__ import annotations

import argparse
import json
import unittest
from unittest import mock

from tools import queue_query


class TestQueueQuery(unittest.TestCase):
    def _args(self, **overrides) -> argparse.Namespace:
        payload = {
            "query_text": None,
            "queue_scope": "all",
            "record_id": None,
            "task_id": None,
            "task_id_prefix": None,
            "document_id": None,
            "document_key": None,
            "document_keys": None,
            "build_family": None,
            "lang": None,
            "langs": None,
            "document_version": None,
            "market_group": None,
            "query_workflow_action": None,
            "git_ref_contains": None,
            "result_contains": None,
            "fresh_since": None,
            "latest_per_document_key": False,
            "allow_multiple": False,
            "limit": 10,
            "json": False,
        }
        payload.update(overrides)
        return argparse.Namespace(**payload)

    def _row(self, record_id: str, **overrides) -> queue_query.QueueQueryRow:
        payload = {
            "queue_scope": "document-link",
            "record_id": record_id,
            "document_id": f"JE-1000F_EU_en_1.{record_id[-1:]}",
            "document_key": "JE-1000F_EU_en",
            "build_family": "eu-en",
            "lang": "en",
            "version": "1.0",
            "workflow_action": "Build Draft Package",
            "normalized_workflow_action": "draft",
            "git_ref": "codex/review",
            "document_link": "https://example.com/doc.docx",
            "document_directory": "",
            "result": "SUCCESS",
            "pr_url": "",
            "review_status": "",
            "review_trigger_enabled": None,
            "build_trigger_requested": True,
            "immediate_build": True,
            "initial_result": "",
            "remarks": "",
        }
        payload.update(overrides)
        return queue_query.QueueQueryRow(**payload)

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

    def test_filter_queue_query_rows_should_match_task_id(self) -> None:
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
                result="SUCCESS",
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
            self._args(task_id="JE-1000F_US_0.3_Build Draft Package"),
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

    def test_filter_queue_query_rows_should_match_document_key_only_start_review_task(self) -> None:
        rows = [
            queue_query.QueueQueryRow(
                queue_scope="review-init",
                record_id="rec_eu_review",
                document_id="",
                document_key="JE-1000F_EU",
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
                review_trigger_enabled=True,
                build_trigger_requested=None,
                immediate_build=None,
                initial_result="",
                remarks="",
                task_id="JE-1000F_EU___Start Review",
            )
        ]

        filtered = queue_query.filter_queue_query_rows(
            self._args(task_id="JE-1000F_EU_Start Review", query_workflow_action="start-review"),
            rows,
        )

        self.assertEqual(["rec_eu_review"], [row.record_id for row in filtered])

    def test_infer_queue_query_from_text_should_prefer_document_id(self) -> None:
        inferred = queue_query.infer_queue_query_from_text(
            "请帮我查 JE-1000F_US_0.3 的 Build Draft Package 记录。先不要触发 workflow。"
        )

        self.assertEqual("JE-1000F_US_0.3_Build Draft Package", inferred.task_id)
        self.assertEqual("JE-1000F_US_0.3", inferred.document_id)
        self.assertEqual("", inferred.document_key)
        self.assertEqual("build-draft-package", inferred.query_workflow_action)
        self.assertEqual("document-link", inferred.queue_scope)

    def test_infer_queue_query_from_text_should_parse_explicit_task_id(self) -> None:
        inferred = queue_query.infer_queue_query_from_text("执行 JE-1000F_US_1.0_Start Review")

        self.assertEqual("JE-1000F_US_1.0_Start Review", inferred.task_id)
        self.assertEqual("JE-1000F_US_1.0", inferred.document_id)
        self.assertEqual("start-review", inferred.query_workflow_action)
        self.assertEqual("review-init", inferred.queue_scope)

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

    def test_infer_queue_query_from_text_should_parse_document_key_only_start_review(self) -> None:
        inferred = queue_query.infer_queue_query_from_text("review JE-1000F_EU")

        self.assertEqual("", inferred.document_id)
        self.assertEqual("JE-1000F_EU", inferred.document_key)
        self.assertEqual((), inferred.document_keys)
        self.assertEqual("JE-1000F_EU_Start Review", inferred.task_id)
        self.assertEqual("start-review", inferred.query_workflow_action)
        self.assertEqual("review-init", inferred.queue_scope)

    def test_infer_queue_query_from_text_should_parse_multi_document_key_start_review_batch(self) -> None:
        inferred = queue_query.infer_queue_query_from_text(
            "开始review JE-1000F_CN\nJE-1000F_US\nJE-1000F_JP\nJE-1000F_EU"
        )

        self.assertEqual("", inferred.document_id)
        self.assertEqual("", inferred.document_key)
        self.assertEqual("", inferred.task_id)
        self.assertEqual(("JE-1000F_CN", "JE-1000F_US", "JE-1000F_JP", "JE-1000F_EU"), inferred.document_keys)
        self.assertEqual("start-review", inferred.query_workflow_action)
        self.assertEqual("review-init", inferred.queue_scope)
        self.assertTrue(inferred.allow_multiple)

    def test_filter_queue_query_rows_should_match_multi_document_key_start_review_batch(self) -> None:
        rows = [
            self._row(
                f"rec_{key.rsplit('_', 1)[1].lower()}",
                queue_scope="review-init",
                document_id="",
                document_key=key,
                build_family="",
                lang="",
                version="",
                workflow_action="Start Review",
                normalized_workflow_action="start_review",
                result="",
                review_status="NotStarted",
                review_trigger_enabled=True,
                build_trigger_requested=None,
                immediate_build=None,
            )
            for key in ("JE-1000F_CN", "JE-1000F_US", "JE-1000F_JP", "JE-1000F_EU")
        ]
        rows.append(
            self._row(
                "rec_other",
                queue_scope="review-init",
                document_id="",
                document_key="JE-2000E_CN",
                build_family="",
                lang="",
                version="",
                workflow_action="Start Review",
                normalized_workflow_action="start_review",
                result="",
                review_status="NotStarted",
                review_trigger_enabled=True,
                build_trigger_requested=None,
                immediate_build=None,
            )
        )

        resolved_args = queue_query.apply_inferred_queue_query(
            self._args(query_text="开始review JE-1000F_CN\nJE-1000F_US\nJE-1000F_JP\nJE-1000F_EU")
        )
        filtered = queue_query.filter_queue_query_rows(resolved_args, rows)

        self.assertEqual(["rec_cn", "rec_us", "rec_jp", "rec_eu"], [row.record_id for row in filtered])

    def test_infer_queue_query_from_text_should_parse_all_eu_draft_copy_batch(self) -> None:
        for query_text in [
            "输出JE-1000F的所有欧规说明书文案",
            "构建JE-1000F的所有欧规说明书文案",
            "构建JE-1000F的欧规说明书文案",
            "创建JE-1000F的欧规文案",
            "基于配置构建JE-1000F的欧规",
            "构建最新符合构建要求的JE-1000F的所有欧规说明书文案",
        ]:
            with self.subTest(query_text=query_text):
                inferred = queue_query.infer_queue_query_from_text(query_text)

                self.assertEqual("", inferred.document_id)
                self.assertEqual("", inferred.document_key)
                self.assertEqual("JE-1000F_EU_", inferred.task_id_prefix)
                self.assertEqual("EU", inferred.market_group)
                self.assertEqual("build-draft-package", inferred.query_workflow_action)
                self.assertEqual("document-link", inferred.queue_scope)
                self.assertTrue(inferred.allow_multiple)

    def test_infer_queue_query_from_text_should_treat_market_version_as_config_batch(self) -> None:
        inferred = queue_query.infer_queue_query_from_text("构建 JE-1000F_EU_1.0 的欧规说明书文案")

        self.assertEqual("", inferred.document_id)
        self.assertEqual("", inferred.document_key)
        self.assertEqual("JE-1000F_EU_", inferred.task_id_prefix)
        self.assertEqual("1.0", inferred.document_version)
        self.assertEqual("build-draft-package", inferred.query_workflow_action)
        self.assertEqual("document-link", inferred.queue_scope)
        self.assertTrue(inferred.allow_multiple)

    def test_infer_queue_query_from_text_should_parse_chinese_language_batch(self) -> None:
        inferred = queue_query.infer_queue_query_from_text("构建 JE-1000F 的英语和法语说明书文案")

        self.assertEqual("JE-1000F_", inferred.task_id_prefix)
        self.assertEqual(("en", "fr"), inferred.langs)
        self.assertEqual("build-draft-package", inferred.query_workflow_action)
        self.assertTrue(inferred.allow_multiple)

    def test_infer_queue_query_from_text_should_treat_model_copy_as_market_wildcard_batch(self) -> None:
        for query_text in [
            "构建JE-1000F说明书文案",
            "基于配置构建JE-1000F说明书文案",
        ]:
            with self.subTest(query_text=query_text):
                inferred = queue_query.infer_queue_query_from_text(query_text)

                self.assertEqual("", inferred.document_id)
                self.assertEqual("", inferred.document_key)
                self.assertEqual("JE-1000F_", inferred.task_id_prefix)
                self.assertEqual("", inferred.market_group)
                self.assertEqual("build-draft-package", inferred.query_workflow_action)
                self.assertEqual("document-link", inferred.queue_scope)
                self.assertTrue(inferred.allow_multiple)

    def test_filter_queue_query_rows_should_match_task_id_prefix_and_triggered_draft_rows(self) -> None:
        rows = [
            queue_query.QueueQueryRow(
                queue_scope="document-link",
                record_id="rec_eu_en",
                document_id="JE-1000F_EU_en_0.5",
                document_key="JE-1000F_EU",
                build_family="eu-en",
                lang="en",
                version="0.5",
                workflow_action="Build Draft Package",
                normalized_workflow_action="draft",
                git_ref="codex/review-eu",
                document_link="",
                document_directory="",
                result="",
                pr_url="",
                review_status="",
                review_trigger_enabled=None,
                build_trigger_requested=True,
                immediate_build=True,
                initial_result="",
                remarks="",
                task_id="JE-1000F_EU_en_0.5_Build Draft Package",
            ),
            queue_query.QueueQueryRow(
                queue_scope="document-link",
                record_id="rec_eu_fr_unchecked",
                document_id="JE-1000F_EU_fr_0.5",
                document_key="JE-1000F_EU",
                build_family="eu-fr",
                lang="fr",
                version="0.5",
                workflow_action="Build Draft Package",
                normalized_workflow_action="draft",
                git_ref="codex/review-eu",
                document_link="",
                document_directory="",
                result="",
                pr_url="",
                review_status="",
                review_trigger_enabled=None,
                build_trigger_requested=False,
                immediate_build=True,
                initial_result="",
                remarks="",
                task_id="JE-1000F_EU_fr_0.5_Build Draft Package",
            ),
            queue_query.QueueQueryRow(
                queue_scope="document-link",
                record_id="rec_us",
                document_id="JE-1000F_US_en_0.5",
                document_key="JE-1000F_US",
                build_family="us-en",
                lang="en",
                version="0.5",
                workflow_action="Build Draft Package",
                normalized_workflow_action="draft",
                git_ref="codex/review-us",
                document_link="",
                document_directory="",
                result="",
                pr_url="",
                review_status="",
                review_trigger_enabled=None,
                build_trigger_requested=True,
                immediate_build=True,
                initial_result="",
                remarks="",
                task_id="JE-1000F_US_en_0.5_Build Draft Package",
            ),
        ]

        filtered = queue_query.filter_queue_query_rows(
            self._args(
                query_text="输出JE-1000F的所有欧规说明书文案",
                task_id_prefix="JE-1000F_EU_",
                query_workflow_action="build-draft-package",
                allow_multiple=True,
            ),
            rows,
        )

        self.assertEqual(["rec_eu_en"], [row.record_id for row in filtered])

    def test_filter_queue_query_rows_should_not_collapse_latest_batch_draft_by_document_key(self) -> None:
        rows = []
        for lang in ("fr", "es", "de", "it"):
            rows.append(
                queue_query.QueueQueryRow(
                    queue_scope="document-link",
                    record_id=f"rec_eu_{lang}",
                    document_id=f"JE-1000F_EU_{lang}_0.7",
                    document_key="JE-1000F_EU",
                    build_family=f"eu-{lang}",
                    lang=lang,
                    version="0.7",
                    workflow_action="Build Draft Package",
                    normalized_workflow_action="draft",
                    git_ref="codex/review-eu",
                    document_link="",
                    document_directory="",
                    result="",
                    pr_url="",
                    review_status="",
                    review_trigger_enabled=None,
                    build_trigger_requested=True,
                    immediate_build=True,
                    initial_result="",
                    remarks="",
                    task_id=f"JE-1000F_EU_{lang}_0.7_Build Draft Package",
                )
            )

        filtered = queue_query.filter_queue_query_rows(
            self._args(
                query_text="构建最新符合构建要求的JE-1000F的所有欧规说明书文案",
                task_id_prefix="JE-1000F_EU_",
                query_workflow_action="build-draft-package",
                allow_multiple=True,
                latest_per_document_key=True,
            ),
            rows,
        )

        self.assertEqual(["rec_eu_fr", "rec_eu_es", "rec_eu_de", "rec_eu_it"], [row.record_id for row in filtered])

    def test_filter_queue_query_rows_should_match_model_wildcard_triggered_draft_rows(self) -> None:
        rows = [
            queue_query.QueueQueryRow(
                queue_scope="document-link",
                record_id="rec_eu_en",
                document_id="JE-1000F_EU_en_1.0",
                document_key="JE-1000F_EU",
                build_family="eu-en",
                lang="en",
                version="1.0",
                workflow_action="Build Draft Package",
                normalized_workflow_action="draft",
                git_ref="codex/review-eu",
                document_link="",
                document_directory="",
                result="",
                pr_url="",
                review_status="",
                review_trigger_enabled=None,
                build_trigger_requested=True,
                immediate_build=True,
                initial_result="",
                remarks="",
                task_id="JE-1000F_EU_en_1.0_Build Draft Package",
            ),
            queue_query.QueueQueryRow(
                queue_scope="document-link",
                record_id="rec_us",
                document_id="JE-1000F_US_1.0",
                document_key="JE-1000F_US",
                build_family="us-merged",
                lang="",
                version="1.0",
                workflow_action="Build Draft Package",
                normalized_workflow_action="draft",
                git_ref="codex/review-us",
                document_link="",
                document_directory="",
                result="",
                pr_url="",
                review_status="",
                review_trigger_enabled=None,
                build_trigger_requested=True,
                immediate_build=True,
                initial_result="",
                remarks="",
                task_id="JE-1000F_US_1.0_Build Draft Package",
            ),
            queue_query.QueueQueryRow(
                queue_scope="document-link",
                record_id="rec_unchecked",
                document_id="JE-1000F_JP_1.0",
                document_key="JE-1000F_JP",
                build_family="jp-ja",
                lang="ja",
                version="1.0",
                workflow_action="Build Draft Package",
                normalized_workflow_action="draft",
                git_ref="codex/review-jp",
                document_link="",
                document_directory="",
                result="",
                pr_url="",
                review_status="",
                review_trigger_enabled=None,
                build_trigger_requested=False,
                immediate_build=True,
                initial_result="",
                remarks="",
                task_id="JE-1000F_JP_1.0_Build Draft Package",
            ),
            queue_query.QueueQueryRow(
                queue_scope="document-link",
                record_id="rec_other_model",
                document_id="JE-2000F_EU_en_1.0",
                document_key="JE-2000F_EU",
                build_family="eu-en",
                lang="en",
                version="1.0",
                workflow_action="Build Draft Package",
                normalized_workflow_action="draft",
                git_ref="codex/review-other",
                document_link="",
                document_directory="",
                result="",
                pr_url="",
                review_status="",
                review_trigger_enabled=None,
                build_trigger_requested=True,
                immediate_build=True,
                initial_result="",
                remarks="",
                task_id="JE-2000F_EU_en_1.0_Build Draft Package",
            ),
        ]

        filtered = queue_query.filter_queue_query_rows(
            self._args(
                query_text="构建JE-1000F说明书文案",
                task_id_prefix="JE-1000F_",
                query_workflow_action="build-draft-package",
                allow_multiple=True,
            ),
            rows,
        )

        self.assertEqual(["rec_eu_en", "rec_us"], [row.record_id for row in filtered])

    def test_filter_queue_query_rows_should_not_default_limit_config_batches_to_ten(self) -> None:
        rows = []
        for index in range(12):
            rows.append(
                queue_query.QueueQueryRow(
                    queue_scope="document-link",
                    record_id=f"rec_{index}",
                    document_id=f"JE-1000F_EU_en_{index}.0",
                    document_key="JE-1000F_EU",
                    build_family="eu-en",
                    lang="en",
                    version=f"{index}.0",
                    workflow_action="Build Draft Package",
                    normalized_workflow_action="draft",
                    git_ref="codex/review-eu",
                    document_link="",
                    document_directory="",
                    result="",
                    pr_url="",
                    review_status="",
                    review_trigger_enabled=None,
                    build_trigger_requested=True,
                    immediate_build=True,
                    initial_result="",
                    remarks="",
                    task_id=f"JE-1000F_EU_en_{index}.0_Build Draft Package",
                )
            )

        filtered = queue_query.filter_queue_query_rows(
            self._args(
                query_text="构建JE-1000F说明书文案",
                task_id_prefix="JE-1000F_",
                query_workflow_action="build-draft-package",
                allow_multiple=True,
            ),
            rows,
        )

        self.assertEqual([f"rec_{index}" for index in range(12)], [row.record_id for row in filtered])

    def test_filter_queue_query_rows_should_match_config_batch_version(self) -> None:
        rows = []
        for version in ("0.7", "1.0"):
            for lang in ("en", "fr"):
                rows.append(
                    queue_query.QueueQueryRow(
                        queue_scope="document-link",
                        record_id=f"rec_eu_{lang}_{version}",
                        document_id=f"JE-1000F_EU_{lang}_{version}",
                        document_key="JE-1000F_EU",
                        build_family=f"eu-{lang}",
                        lang=lang,
                        version=version,
                        workflow_action="Build Draft Package",
                        normalized_workflow_action="draft",
                        git_ref="codex/review-eu",
                        document_link="",
                        document_directory="",
                        result="",
                        pr_url="",
                        review_status="",
                        review_trigger_enabled=None,
                        build_trigger_requested=True,
                        immediate_build=True,
                        initial_result="",
                        remarks="",
                        task_id=f"JE-1000F_EU_{lang}_{version}_Build Draft Package",
                    )
                )

        filtered = queue_query.filter_queue_query_rows(
            self._args(
                query_text="构建 JE-1000F_EU_1.0 的欧规说明书文案",
                task_id_prefix="JE-1000F_EU_",
                document_version="1.0",
                query_workflow_action="build-draft-package",
                allow_multiple=True,
            ),
            rows,
        )

        self.assertEqual(["rec_eu_en_1.0", "rec_eu_fr_1.0"], [row.record_id for row in filtered])

    def test_filter_queue_query_rows_should_match_multi_language_selector(self) -> None:
        rows = []
        for lang in ("en", "fr", "es"):
            rows.append(
                queue_query.QueueQueryRow(
                    queue_scope="document-link",
                    record_id=f"rec_eu_{lang}",
                    document_id=f"JE-1000F_EU_{lang}_1.0",
                    document_key="JE-1000F_EU",
                    build_family=f"eu-{lang}",
                    lang=lang,
                    version="1.0",
                    workflow_action="Build Draft Package",
                    normalized_workflow_action="draft",
                    git_ref="codex/review-eu",
                    document_link="",
                    document_directory="",
                    result="",
                    pr_url="",
                    review_status="",
                    review_trigger_enabled=None,
                    build_trigger_requested=True,
                    immediate_build=True,
                    initial_result="",
                    remarks="",
                    task_id=f"JE-1000F_EU_{lang}_1.0_Build Draft Package",
                )
            )

        filtered = queue_query.filter_queue_query_rows(
            self._args(
                query_workflow_action="build-draft-package",
                task_id_prefix="JE-1000F_EU_",
                langs="en,fr",
                allow_multiple=True,
            ),
            rows,
        )

        self.assertEqual(["rec_eu_en", "rec_eu_fr"], [row.record_id for row in filtered])

    def test_filter_queue_query_rows_should_mark_stale_and_fresh_results(self) -> None:
        rows = [
            queue_query.QueueQueryRow(
                queue_scope="document-link",
                record_id="rec_old",
                document_id="JE-1000F_EU_en_1.0",
                document_key="JE-1000F_EU",
                build_family="eu-en",
                lang="en",
                version="1.0",
                workflow_action="Build Draft Package",
                normalized_workflow_action="draft",
                git_ref="codex/review-eu",
                document_link="",
                document_directory="",
                result="FAILED | version=1.0 | workflow_action=Build Draft Package | built_at=2026-05-04T10:00:00+00:00 | old failure",
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
                record_id="rec_new",
                document_id="JE-1000F_EU_fr_1.0",
                document_key="JE-1000F_EU",
                build_family="eu-fr",
                lang="fr",
                version="1.0",
                workflow_action="Build Draft Package",
                normalized_workflow_action="draft",
                git_ref="codex/review-eu",
                document_link="",
                document_directory="",
                result="SUCCESS | version=1.0 | workflow_action=Build Draft Package | built_at=2026-05-04T10:05:00+00:00",
                pr_url="",
                review_status="",
                review_trigger_enabled=None,
                build_trigger_requested=True,
                immediate_build=True,
                initial_result="",
                remarks="",
            ),
        ]

        filtered = queue_query.filter_queue_query_rows(
            self._args(fresh_since="2026-05-04T10:02:00+00:00"),
            rows,
        )

        self.assertEqual("stale_result", filtered[0].freshness_status)
        self.assertFalse(filtered[0].result_is_fresh)
        self.assertEqual("fresh_success", filtered[1].freshness_status)
        self.assertTrue(filtered[1].result_is_fresh)

    def test_filter_queue_query_rows_should_mark_writeback_pending_after_start(self) -> None:
        row = queue_query.QueueQueryRow(
            queue_scope="document-link",
            record_id="rec_started",
            document_id="JE-1000F_EU_en_1.0",
            document_key="JE-1000F_EU",
            build_family="eu-en",
            lang="en",
            version="1.0",
            workflow_action="Build Draft Package",
            normalized_workflow_action="draft",
            git_ref="codex/review-eu",
            document_link="",
            document_directory="",
            result="",
            pr_url="",
            review_status="",
            review_trigger_enabled=None,
            build_trigger_requested=True,
            immediate_build=True,
            initial_result="",
            remarks="",
            build_started_at="2026-05-04T10:03:00+00:00",
        )

        filtered = queue_query.filter_queue_query_rows(
            self._args(fresh_since="2026-05-04T10:02:00+00:00"),
            [row],
        )

        self.assertEqual("writeback_pending", filtered[0].freshness_status)
        self.assertIsNone(filtered[0].result_is_fresh)

    def test_infer_queue_query_from_text_should_parse_start_review_and_build_family(self) -> None:
        inferred = queue_query.infer_queue_query_from_text("开始 review JE-1000F us-merged")

        self.assertEqual("", inferred.document_id)
        self.assertEqual("us-merged", inferred.build_family)
        self.assertEqual("start-review", inferred.query_workflow_action)
        self.assertEqual("review-init", inferred.queue_scope)

    def test_infer_queue_query_from_text_should_treat_built_links_as_latest_successes(self) -> None:
        inferred = queue_query.infer_queue_query_from_text("构建好的文档链接发我")

        self.assertEqual("success", inferred.result_contains)
        self.assertTrue(inferred.latest_per_document_key)
        self.assertEqual("document-link", inferred.queue_scope)
        self.assertEqual("", inferred.query_workflow_action)

    def test_apply_inferred_queue_query_should_treat_built_link_inventory_as_full_success_list(self) -> None:
        resolved = queue_query.apply_inferred_queue_query(
            self._args(query_text="当前所有已构建文档链接")
        )

        self.assertEqual("document-link", resolved.queue_scope)
        self.assertEqual("success", resolved.result_contains)
        self.assertFalse(resolved.latest_per_document_key)
        self.assertFalse(resolved.query_workflow_action)
        self.assertEqual(200, resolved.limit)

    def test_apply_inferred_queue_query_should_fill_record_id_from_text(self) -> None:
        resolved = queue_query.apply_inferred_queue_query(
            self._args(query_text="这个好了没 record_id rec_context")
        )

        self.assertEqual("rec_context", resolved.record_id)

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

    def test_filter_queue_query_rows_should_return_latest_success_per_document_key(self) -> None:
        rows = [
            queue_query.QueueQueryRow(
                queue_scope="document-link",
                record_id="rec_eu_old",
                document_id="JE-1000F_EU_1.0",
                document_key="JE-1000F_EU",
                build_family="eu-merged",
                lang="",
                version="1.0",
                workflow_action="Build Draft Package",
                normalized_workflow_action="draft",
                git_ref="codex/review-old",
                document_link="https://example.com/eu-1.0.docx",
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
                record_id="rec_eu_new",
                document_id="JE-1000F_EU_1.1",
                document_key="JE-1000F_EU",
                build_family="eu-merged",
                lang="",
                version="1.1",
                workflow_action="Build Draft Package",
                normalized_workflow_action="draft",
                git_ref="codex/review-new",
                document_link="https://example.com/eu-1.1.docx",
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
                record_id="rec_cn_old",
                document_id="JE-1000F_CN_1.0",
                document_key="JE-1000F_CN",
                build_family="cn-zh",
                lang="zh",
                version="1.0",
                workflow_action="Build Draft Package",
                normalized_workflow_action="draft",
                git_ref="codex/review-old",
                document_link="https://example.com/cn-1.0.docx",
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
                record_id="rec_cn_new",
                document_id="JE-1000F_CN_1.1",
                document_key="JE-1000F_CN",
                build_family="cn-zh",
                lang="zh",
                version="1.1",
                workflow_action="Build Draft Package",
                normalized_workflow_action="draft",
                git_ref="codex/review-new",
                document_link="https://example.com/cn-1.1.docx",
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
        ]

        filtered = queue_query.filter_queue_query_rows(
            self._args(query_text="构建好的文档链接发我", result_contains="success", latest_per_document_key=True),
            rows,
        )

        self.assertEqual(["rec_eu_new", "rec_cn_new"], [row.record_id for row in filtered])

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
        self.assertEqual(1, payload["returned_count"])
        self.assertEqual(1, payload["matched_count"])
        self.assertFalse(payload["truncated"])
        self.assertEqual("rec_draft", payload["rows"][0]["record_id"])

    def test_query_queue_rows_should_report_truncation_metadata(self) -> None:
        rows = [self._row(f"rec_{index}") for index in range(12)]

        result = queue_query.query_queue_rows(self._args(limit=10), rows)
        rendered = queue_query.render_queue_query_rows(result.rows, as_json=True, query_result=result)
        payload = json.loads(rendered)

        self.assertEqual(12, result.matched_count)
        self.assertEqual(10, result.returned_count)
        self.assertTrue(result.truncated)
        self.assertEqual(12, payload["matched_count"])
        self.assertEqual(10, payload["returned_count"])
        self.assertTrue(payload["truncated"])

    def test_build_review_init_rows_should_skip_non_start_review_actions(self) -> None:
        cfg = {}
        raw_records = [
            {
                "record_id": "rec_publish",
                "fields": {
                    "Document_ID": "JE-1000F_US_0.3",
                    "Document_Key": "JE-1000F_US",
                    "Build_family": "us-merged",
                    "Lang": "en",
                    "Version": "0.3",
                    "Workflow_action": "Publish",
                },
            },
            {
                "record_id": "rec_review",
                "fields": {
                    "Document_ID": "JE-1000F_US_0.3",
                    "Document_Key": "JE-1000F_US",
                    "Build_family": "us-merged",
                    "Lang": "en",
                    "Version": "0.3",
                    "Workflow_action": "Start Review",
                },
            },
        ]

        source = mock.Mock()
        source.fetch_records_with_ids.return_value = raw_records

        with mock.patch.object(queue_query, "collect_review_start_preflight_errors", return_value=[]), \
             mock.patch.object(queue_query, "resolve_review_init_binding", return_value=mock.Mock(base_token="app", table_id="tbl", view_id="vew")), \
             mock.patch.object(queue_query, "cli_bin", return_value="lark-cli"), \
             mock.patch.object(queue_query, "phase2_identity", return_value="bot"), \
             mock.patch.object(queue_query, "LarkCliSource", return_value=source):
            rows = queue_query._build_review_init_rows(cfg)

        self.assertEqual(["rec_review"], [row.record_id for row in rows])


if __name__ == "__main__":
    unittest.main()
