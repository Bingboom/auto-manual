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


def _eu_draft_row(lang: str, record_id: str | None = None) -> queue_query.QueueQueryRow:
    return queue_query.QueueQueryRow(
        queue_scope="document-link",
        record_id=record_id or f"rec_eu_{lang}",
        document_id=f"JE-1000F_EU_{lang}_0.5",
        document_key="JE-1000F_EU",
        build_family=f"eu-{lang}",
        lang=lang,
        version="0.5",
        workflow_action="Build Draft Package",
        normalized_workflow_action="draft",
        git_ref="codex/review-id-recvfw0zg4pzxs",
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
        market_group="EU",
    )


def _model_draft_row(market: str, *, lang: str = "", record_id: str | None = None) -> queue_query.QueueQueryRow:
    normalized_market = market.upper()
    document_id = f"JE-1000F_{normalized_market}_{lang}_1.0" if lang else f"JE-1000F_{normalized_market}_1.0"
    family_suffix = lang or "merged"
    return queue_query.QueueQueryRow(
        queue_scope="document-link",
        record_id=record_id or f"rec_{normalized_market.lower()}_{lang or 'merged'}",
        document_id=document_id,
        document_key=f"JE-1000F_{normalized_market}",
        build_family=f"{normalized_market.lower()}-{family_suffix}",
        lang=lang,
        version="1.0",
        workflow_action="Build Draft Package",
        normalized_workflow_action="draft",
        git_ref=f"codex/review-{normalized_market.lower()}",
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
        task_id=f"{document_id}_Build Draft Package",
        market_group=normalized_market,
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


def _document_key_review_row(
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


class TestQueueResolveAction(unittest.TestCase):
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
            "limit": 10,
            "json": False,
            "confirm_publish": False,
            "allow_multiple": False,
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

    def test_resolve_queue_action_should_resolve_document_key_only_start_review(self) -> None:
        resolution = queue_resolve_action.resolve_queue_action(
            self._args(query_text="review JE-1000F_EU"),
            [_document_key_review_row()],
        )

        self.assertEqual("resolved", resolution.resolution_status)
        self.assertEqual("start_review", resolution.action_name)
        self.assertEqual("start-review", resolution.dispatch_command)
        self.assertTrue(resolution.ready)
        self.assertEqual("rec_eu_review", resolution.row["record_id"])
        self.assertEqual("JE-1000F_EU_Start Review", resolution.selectors["task_id"])
        self.assertNotIn("document_key", resolution.selectors)

    def test_resolve_queue_action_should_resolve_restart_review_phrase(self) -> None:
        resolution = queue_resolve_action.resolve_queue_action(
            self._args(query_text="重新开始review JE-2000F_EU"),
            [
                _document_key_review_row(
                    record_id="recvlsa1VML5nT",
                    document_key="JE-2000F_EU",
                    task_id="",
                )
            ],
        )

        self.assertEqual("resolved", resolution.resolution_status)
        self.assertEqual("start_review", resolution.action_name)
        self.assertEqual("start-review", resolution.dispatch_command)
        self.assertTrue(resolution.ready)
        self.assertEqual("recvlsa1VML5nT", resolution.row["record_id"])
        self.assertEqual("JE-2000F_EU_Start Review", resolution.selectors["task_id"])

    def test_resolve_queue_action_should_resolve_pt_br_document_key_start_review(self) -> None:
        resolution = queue_resolve_action.resolve_queue_action(
            self._args(query_text="开始review JE-1500D_pt-BR"),
            [
                _document_key_review_row(
                    record_id="recvkaCD74mZ4z",
                    document_key="JE-1500D_pt-BR",
                    task_id="",
                )
            ],
        )

        self.assertEqual("resolved", resolution.resolution_status)
        self.assertEqual("start_review", resolution.action_name)
        self.assertEqual("start-review", resolution.dispatch_command)
        self.assertTrue(resolution.ready)
        self.assertEqual("recvkaCD74mZ4z", resolution.row["record_id"])
        self.assertEqual("JE-1500D_pt-BR_Start Review", resolution.selectors["task_id"])

    def test_resolve_queue_action_should_resolve_multi_document_key_start_review_batch(self) -> None:
        rows = [
            _document_key_review_row(
                record_id=f"rec_{key.rsplit('_', 1)[1].lower()}",
                document_key=key,
            )
            for key in ("JE-1000F_CN", "JE-1000F_US", "JE-1000F_JP", "JE-1000F_EU")
        ]
        rows.append(_document_key_review_row(record_id="rec_other", document_key="JE-2000E_CN"))

        resolution = queue_resolve_action.resolve_queue_action(
            self._args(query_text="开始review JE-1000F_CN\nJE-1000F_US\nJE-1000F_JP\nJE-1000F_EU"),
            rows,
        )

        self.assertEqual("resolved_batch", resolution.resolution_status)
        self.assertEqual("start_review", resolution.action_name)
        self.assertEqual("start-review", resolution.dispatch_command)
        self.assertEqual(4, resolution.matched_count)
        self.assertTrue(resolution.ready)
        self.assertEqual(
            "JE-1000F_CN,JE-1000F_US,JE-1000F_JP,JE-1000F_EU",
            resolution.selectors["document_keys"],
        )
        self.assertEqual(["rec_cn", "rec_us", "rec_jp", "rec_eu"], [row.record_id for row in resolution.candidates])

    def test_resolve_queue_action_should_resolve_multi_start_review_document_ids(self) -> None:
        rows = [
            queue_query.QueueQueryRow(
                queue_scope="review-init",
                record_id=f"rec_{key.rsplit('_', 1)[1].lower()}",
                document_id=key,
                document_key='{"id":"recLinkedDocument"}',
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
                task_id=f"{key}_Start Review",
            )
            for key in ("JE-1000F_CN", "JE-1000F_US", "JE-1000F_JP", "JE-1000F_EU", "JE-1000F_pt-BR")
        ]

        resolution = queue_resolve_action.resolve_queue_action(
            self._args(query_text="开始review JE-1000F_CN\nJE-1000F_US\nJE-1000F_JP\nJE-1000F_EU\nJE-1000F_pt-BR"),
            rows,
        )

        self.assertEqual("resolved_batch", resolution.resolution_status)
        self.assertEqual(5, resolution.matched_count)
        self.assertEqual(
            ["rec_cn", "rec_us", "rec_jp", "rec_eu", "rec_pt-br"],
            [row.record_id for row in resolution.candidates],
        )

    def test_resolve_queue_action_should_require_document_key_for_start_review(self) -> None:
        resolution = queue_resolve_action.resolve_queue_action(
            self._args(record_id="rec_missing_key", query_workflow_action="start-review"),
            [_document_key_review_row("rec_missing_key", document_key="")],
        )

        self.assertEqual("missing_required_field", resolution.resolution_status)
        self.assertEqual("start_review", resolution.action_name)
        self.assertIn("Document_Key", resolution.missing_fields)
        self.assertFalse(resolution.ready)

    def test_resolve_queue_action_should_require_review_checkbox_for_start_review(self) -> None:
        resolution = queue_resolve_action.resolve_queue_action(
            self._args(query_text="review JE-1000F_EU"),
            [_document_key_review_row(review_trigger_enabled=False)],
        )

        self.assertEqual("missing_required_field", resolution.resolution_status)
        self.assertEqual("start_review", resolution.action_name)
        self.assertIn("是否进入Review", resolution.missing_fields)
        self.assertFalse(resolution.ready)

    def test_resolve_queue_action_should_treat_draft_status_phrase_as_query(self) -> None:
        resolution = queue_resolve_action.resolve_queue_action(
            self._args(query_text="JE-1000F US 草稿包好了没"),
            [_draft_row()],
        )

        self.assertEqual("resolved", resolution.resolution_status)
        self.assertEqual("query_status", resolution.action_name)
        self.assertIsNone(resolution.dispatch_command)
        self.assertEqual("rec_draft", resolution.row["record_id"])

    def test_resolve_queue_action_should_treat_build_result_lookup_as_query(self) -> None:
        resolution = queue_resolve_action.resolve_queue_action(
            self._args(query_text="查 JE-1000F_US_en_0.3 的构建结果"),
            [_draft_row()],
        )

        self.assertEqual("resolved", resolution.resolution_status)
        self.assertEqual("query_status", resolution.action_name)
        self.assertIsNone(resolution.dispatch_command)
        self.assertEqual("rec_draft", resolution.row["record_id"])

    def test_resolve_queue_action_should_treat_cannot_find_success_as_query(self) -> None:
        resolution = queue_resolve_action.resolve_queue_action(
            self._args(query_text="明明就构建成功了 为什么你查不到"),
            [_draft_row()],
        )

        self.assertEqual("resolved", resolution.resolution_status)
        self.assertEqual("query_status", resolution.action_name)
        self.assertIsNone(resolution.dispatch_command)

    def test_resolve_queue_action_should_return_batch_for_built_link_inventory(self) -> None:
        resolution = queue_resolve_action.resolve_queue_action(
            self._args(query_text="当前所有已构建文档链接"),
            [_draft_row(), _publish_row()],
        )

        self.assertEqual("resolved_batch", resolution.resolution_status)
        self.assertEqual("query_status", resolution.action_name)
        self.assertEqual(2, resolution.matched_count)
        self.assertIsNone(resolution.dispatch_command)
        self.assertEqual("https://example.com/doc.docx", resolution.candidates[0].document_link)

    def test_resolve_queue_action_should_keep_direct_draft_command_executable(self) -> None:
        resolution = queue_resolve_action.resolve_queue_action(
            self._args(query_text="帮我生成 JE-1000F US en 0.3 草稿包"),
            [_draft_row()],
        )

        self.assertEqual("resolved", resolution.resolution_status)
        self.assertEqual("build_draft_package", resolution.action_name)
        self.assertEqual("build-draft", resolution.dispatch_command)

    def test_resolve_queue_action_should_keep_build_and_return_result_executable(self) -> None:
        resolution = queue_resolve_action.resolve_queue_action(
            self._args(
                query_text=(
                    "请帮我构建 JE-1000F_US_en_0.3，并返回 Build Draft Package 记录。"
                    "只返回 record_id、Git_ref、构建结果、Document link。"
                )
            ),
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

    def test_resolve_queue_action_should_allow_batch_draft_for_all_eu_copy(self) -> None:
        for query_text in [
            "输出JE-1000F的所有欧规说明书文案",
            "构建JE-1000F的所有欧规说明书文案",
            "构建JE-1000F的欧规说明书文案",
            "创建JE-1000F的欧规文案",
            "基于配置构建JE-1000F的欧规",
            "构建最新符合构建要求的JE-1000F的所有欧规说明书文案",
        ]:
            with self.subTest(query_text=query_text):
                resolution = queue_resolve_action.resolve_queue_action(
                    self._args(query_text=query_text),
                    [
                        _eu_draft_row("en"),
                        _eu_draft_row("fr"),
                        _eu_draft_row("es"),
                        _eu_draft_row("de"),
                        _eu_draft_row("it"),
                    ],
                )

                self.assertEqual("resolved_batch", resolution.resolution_status)
                self.assertEqual("build_draft_package", resolution.action_name)
                self.assertTrue(resolution.ready)
                self.assertEqual(5, resolution.matched_count)
                self.assertEqual("build-draft", resolution.dispatch_command)
                self.assertEqual(["en", "fr", "es", "de", "it"], [candidate.lang for candidate in resolution.candidates])

    def test_resolve_queue_action_should_use_task_id_prefix_for_package_build(self) -> None:
        rows = [
            queue_query.QueueQueryRow(
                queue_scope="document-link",
                record_id=f"rec_eu_{lang}",
                document_id=f"JE-2000E_EU_{lang}_0.1",
                document_key='{"id":"linked-document-key"}',
                build_family=f"eu-{lang}",
                lang=lang,
                version="0.1",
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
                task_id=f"JE-2000E_EU_{lang}_0.1",
                market_group="EU",
            )
            for lang in ("en", "fr")
        ]
        rows.append(_model_draft_row("US", lang="en", record_id="rec_us_en"))

        resolution = queue_resolve_action.resolve_queue_action(
            self._args(query_text="触发 JE-2000E_EU 欧规整包构建"),
            rows,
        )

        self.assertEqual("resolved_batch", resolution.resolution_status)
        self.assertEqual("build_draft_package", resolution.action_name)
        self.assertTrue(resolution.ready)
        self.assertEqual("JE-2000E_EU_", resolution.selectors["task_id_prefix"])
        self.assertNotIn("document_key", resolution.selectors)
        self.assertEqual(["rec_eu_en", "rec_eu_fr"], [candidate.record_id for candidate in resolution.candidates])

    def test_resolve_queue_action_should_not_clarify_all_eu_copy_request(self) -> None:
        rows = [
            queue_query.QueueQueryRow(
                queue_scope="document-link",
                record_id=f"rec_eu_{lang}",
                document_id=f"JE-2000E_EU_{lang}_0.1",
                document_key='{"id":"linked-document-key"}',
                build_family=f"eu-{lang}",
                lang=lang,
                version="0.1",
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
                task_id=f"JE-2000E_EU_{lang}_0.1_Build Draft Package",
                market_group="EU",
            )
            for lang in ("en", "fr", "es", "de", "it", "uk")
        ]

        resolution = queue_resolve_action.resolve_queue_action(
            self._args(query_text="构建JE-2000E_EU的所有欧规文案"),
            rows,
        )

        self.assertEqual("resolved_batch", resolution.resolution_status)
        self.assertEqual("build_draft_package", resolution.action_name)
        self.assertTrue(resolution.ready)
        self.assertEqual(6, resolution.matched_count)
        self.assertEqual("JE-2000E_EU_", resolution.selectors["task_id_prefix"])
        self.assertNotIn("document_key", resolution.selectors)

    def test_resolve_queue_action_should_allow_model_wildcard_batch_draft(self) -> None:
        resolution = queue_resolve_action.resolve_queue_action(
            self._args(query_text="构建JE-1000F说明书文案"),
            [
                _model_draft_row("EU", lang="en", record_id="rec_eu_en"),
                _model_draft_row("EU", lang="fr", record_id="rec_eu_fr"),
                _model_draft_row("US", record_id="rec_us"),
            ],
        )

        self.assertEqual("resolved_batch", resolution.resolution_status)
        self.assertEqual("build_draft_package", resolution.action_name)
        self.assertTrue(resolution.ready)
        self.assertEqual(3, resolution.matched_count)
        self.assertEqual("build-draft", resolution.dispatch_command)
        self.assertEqual(["rec_eu_en", "rec_eu_fr", "rec_us"], [candidate.record_id for candidate in resolution.candidates])

    def test_resolve_queue_action_should_allow_language_filtered_batch_draft(self) -> None:
        resolution = queue_resolve_action.resolve_queue_action(
            self._args(query_text="构建 JE-1000F 的英语和法语说明书文案"),
            [
                _model_draft_row("EU", lang="en", record_id="rec_eu_en"),
                _model_draft_row("EU", lang="fr", record_id="rec_eu_fr"),
                _model_draft_row("EU", lang="es", record_id="rec_eu_es"),
            ],
        )

        self.assertEqual("resolved_batch", resolution.resolution_status)
        self.assertEqual(["rec_eu_en", "rec_eu_fr"], [candidate.record_id for candidate in resolution.candidates])
        self.assertEqual("en,fr", resolution.selectors["langs"])

    def test_resolve_queue_action_should_filter_untriggered_batch_rows(self) -> None:
        blocked = _eu_draft_row("en", "rec_blocked")
        blocked = queue_query.QueueQueryRow(
            **{
                **blocked.__dict__,
                "build_trigger_requested": False,
            }
        )

        resolution = queue_resolve_action.resolve_queue_action(
            self._args(query_text="输出JE-1000F的所有欧规说明书文案"),
            [blocked, _eu_draft_row("fr")],
        )

        self.assertEqual("resolved", resolution.resolution_status)
        self.assertEqual("rec_eu_fr", resolution.row["record_id"])

    def test_resolve_queue_action_should_report_untriggered_exact_draft_row(self) -> None:
        blocked = _eu_draft_row("en", "rec_blocked")
        blocked = queue_query.QueueQueryRow(
            **{
                **blocked.__dict__,
                "build_trigger_requested": False,
            }
        )

        resolution = queue_resolve_action.resolve_queue_action(
            self._args(
                task_id="JE-1000F_EU_en_0.5_Build Draft Package",
                query_workflow_action="build-draft-package",
            ),
            [blocked],
        )

        self.assertEqual("missing_required_field", resolution.resolution_status)
        self.assertIn("是否触发文档构建", resolution.missing_fields)

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
