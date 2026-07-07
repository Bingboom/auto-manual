from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

from tools import process_build_queue
from tools import process_build_queue_main
from tests.test_helpers import temp_test_root


class TestProcessBuildQueue(unittest.TestCase):
    def test_config_path_in_repo_root_should_preserve_configs_dir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            worktree = root / ".tmp" / "process-build-queue-worktrees" / "main"
            config_path = root / "configs" / "config.eu.yaml"

            resolved = process_build_queue._config_path_in_repo_root(config_path, repo_root=worktree)

        self.assertEqual(worktree / "configs" / "config.eu.yaml", resolved)

    def test_resolve_docs_dir_for_config_should_keep_configs_dir_repo_relative(self) -> None:
        with tempfile.TemporaryDirectory() as td, mock.patch.object(process_build_queue, "ROOT", Path(td)):
            root = Path(td)
            config_path = root / "configs" / "config.eu.yaml"

            docs_dir = process_build_queue._resolve_docs_dir_for_config(
                config_path,
                {"paths": {"docs_dir": "docs"}},
            )

        self.assertEqual((root / "docs").resolve(strict=False), docs_dir.resolve(strict=False))

    def test_cli_main_should_resolve_relative_paths_and_normalize_record_id(self) -> None:
        with temp_test_root() as root:
            seen: dict[str, object] = {}

            exit_code = process_build_queue_main.run_main(
                [
                    "--config",
                    "config.us.yaml",
                    "--data-root",
                    "data/phase2",
                    "--dry-run",
                    "--record-id",
                    " rec_123 ",
                ],
                parse_args=process_build_queue.parse_args,
                repo_root=root,
                load_config=lambda path: {"build": {"default_region": "US"}},
                resolve_phase2_export_root=lambda cfg, *, repo_root, data_root: repo_root / str(data_root),
                process_build_queue=lambda **kwargs: seen.update(kwargs) or 0,
            )

        self.assertEqual(0, exit_code)
        self.assertEqual(root / "config.us.yaml", seen["config_path"])
        self.assertEqual(str(root / "data" / "phase2"), seen["data_root"])
        self.assertTrue(seen["dry_run"])
        self.assertEqual("rec_123", seen["record_id"])

    def test_cli_main_should_return_exit_code_one_for_runtime_errors(self) -> None:
        with temp_test_root() as root:
            exit_code = process_build_queue_main.run_main(
                ["--config", "config.us.yaml"],
                parse_args=process_build_queue.parse_args,
                repo_root=root,
                load_config=lambda path: {},
                resolve_phase2_export_root=lambda cfg, *, repo_root, data_root: repo_root / "data" / "phase2",
                process_build_queue=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("queue boom")),
            )

        self.assertEqual(1, exit_code)

    def test_pending_queue_records_should_flatten_select_values_and_filter_y_rows(self) -> None:
        records = process_build_queue.pending_queue_records(
            [
                {
                    "record_id": "rec_enabled",
                    "fields": {
                        process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_en_1.0",
                        process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                        process_build_queue.VERSION_FIELD: ["1.0"],
                        process_build_queue.LANG_FIELD: ["en"],
                        process_build_queue.BUILD_FAMILY_FIELD: ["us-en"],
                        process_build_queue.WORKFLOW_ACTION_FIELD: ["Build Draft Package"],
                        process_build_queue.DOC_PHASE_FIELD: ["Draft"],
                        process_build_queue.GIT_REF_FIELD: ["codex/review-je-1000f-us-en-1-0"],
                        process_build_queue.TRIGGER_FIELD: ["Y"],
                        process_build_queue.IMMEDIATE_TRIGGER_FIELD: False,
                    },
                },
                {
                    "record_id": "rec_disabled",
                    "fields": {
                        process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_fr_1.0",
                        process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                        process_build_queue.VERSION_FIELD: ["1.0"],
                        process_build_queue.LANG_FIELD: ["fr"],
                        process_build_queue.DOC_PHASE_FIELD: ["Publish"],
                        process_build_queue.TRIGGER_FIELD: ["已构建"],
                        process_build_queue.IMMEDIATE_TRIGGER_FIELD: False,
                    },
                },
            ]
        )

        self.assertEqual(1, len(records))
        self.assertEqual("rec_enabled", records[0].record_id)
        self.assertEqual("JE-1000F_US", records[0].document_key)
        self.assertEqual("1.0", records[0].version)
        self.assertEqual("en", records[0].lang)
        self.assertEqual("us-en", records[0].build_family)
        self.assertEqual("Build Draft Package", records[0].workflow_action)
        self.assertEqual("Draft", records[0].doc_phase)
        self.assertEqual("codex/review-je-1000f-us-en-1-0", records[0].git_ref)

    def test_pending_queue_records_should_accept_object_style_feishu_values(self) -> None:
        records = process_build_queue.pending_queue_records(
            [
                {
                    "record_id": "rec_object_enabled",
                    "fields": {
                        process_build_queue.DOCUMENT_ID_FIELD: {"text": "JE-1000F_US_en_1.0"},
                        process_build_queue.DOCUMENT_KEY_FIELD: {"text": "JE-1000F_US"},
                        process_build_queue.VERSION_FIELD: [{"text": "1.0"}],
                        process_build_queue.LANG_FIELD: [{"text": "en"}],
                        process_build_queue.BUILD_FAMILY_FIELD: [{"text": "us-merged"}],
                        process_build_queue.WORKFLOW_ACTION_FIELD: [{"text": "Build Draft Package"}],
                        process_build_queue.DOC_PHASE_FIELD: [{"text": "Draft"}],
                        process_build_queue.GIT_REF_FIELD: [{"text": "codex/review-id-recvfw0zg4pzxs"}],
                        process_build_queue.TRIGGER_FIELD: [{"text": "Y"}],
                        process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    },
                }
            ]
        )

        self.assertEqual(1, len(records))
        self.assertEqual("rec_object_enabled", records[0].record_id)
        self.assertEqual("Build Draft Package", records[0].workflow_action)
        self.assertEqual("Y", records[0].trigger_value)
        self.assertTrue(records[0].immediate_trigger_value)

    def test_pending_queue_records_should_accept_dingtalk_session_key_alias(self) -> None:
        records = process_build_queue.pending_queue_records(
            [
                {
                    "record_id": "rec_dingtalk_alias",
                    "fields": {
                        process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_en_1.0",
                        process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                        process_build_queue.VERSION_FIELD: ["1.0"],
                        process_build_queue.BUILD_FAMILY_FIELD: ["us-merged"],
                        process_build_queue.WORKFLOW_ACTION_FIELD: ["Publish"],
                        process_build_queue.GIT_REF_FIELD: ["codex/review-id-recvfw0zg4pzxs"],
                        process_build_queue.TRIGGER_FIELD: ["Y"],
                        process_build_queue.UPLOAD_DINGTALK_FIELD: True,
                        "DingTalk_session_key": "alice",
                    },
                }
            ]
        )

        self.assertEqual(1, len(records))
        self.assertEqual("alice", records[0].operator_union_id)

    def test_pending_queue_records_should_not_accept_immediate_checkbox_without_trigger(self) -> None:
        records = process_build_queue.pending_queue_records(
            [
                {
                    "record_id": "rec_immediate",
                    "fields": {
                        process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_en_1.0",
                        process_build_queue.DOCUMENT_KEY_FIELD: [{"id": "recvfw0zG4PzxS"}],
                        process_build_queue.VERSION_FIELD: ["1.0"],
                        process_build_queue.LANG_FIELD: ["en"],
                        process_build_queue.WORKFLOW_ACTION_FIELD: ["Build Draft Package"],
                        process_build_queue.DOC_PHASE_FIELD: ["Draft"],
                        process_build_queue.TRIGGER_FIELD: ["已构建"],
                        process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    },
                }
            ]
        )

        self.assertEqual([], records)

    def test_pending_queue_records_should_accept_triggered_row_with_immediate_checkbox(self) -> None:
        records = process_build_queue.pending_queue_records(
            [
                {
                    "record_id": "rec_immediate",
                    "fields": {
                        process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_en_1.0",
                        process_build_queue.DOCUMENT_KEY_FIELD: [{"id": "recvfw0zG4PzxS"}],
                        process_build_queue.VERSION_FIELD: ["1.0"],
                        process_build_queue.LANG_FIELD: ["en"],
                        process_build_queue.WORKFLOW_ACTION_FIELD: ["Build Draft Package"],
                        process_build_queue.DOC_PHASE_FIELD: ["Draft"],
                        process_build_queue.TRIGGER_FIELD: ["Y"],
                        process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    },
                }
            ]
        )

        self.assertEqual(1, len(records))
        self.assertTrue(records[0].immediate_trigger_value)
        self.assertEqual("Draft", records[0].doc_phase)

    def test_pending_immediate_queue_records_should_keep_only_triggered_immediate_rows(self) -> None:
        records = process_build_queue.pending_immediate_queue_records(
            [
                {
                    "record_id": "rec_immediate",
                    "fields": {
                        process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_en_1.0",
                        process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                        process_build_queue.VERSION_FIELD: ["1.0"],
                        process_build_queue.LANG_FIELD: ["en"],
                        process_build_queue.WORKFLOW_ACTION_FIELD: ["Build Draft Package"],
                        process_build_queue.DOC_PHASE_FIELD: ["Draft"],
                        process_build_queue.TRIGGER_FIELD: ["Y"],
                        process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    },
                },
                {
                    "record_id": "rec_non_immediate",
                    "fields": {
                        process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_fr_1.0",
                        process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                        process_build_queue.VERSION_FIELD: ["1.0"],
                        process_build_queue.LANG_FIELD: ["fr"],
                        process_build_queue.WORKFLOW_ACTION_FIELD: ["Build Draft Package"],
                        process_build_queue.DOC_PHASE_FIELD: ["Draft"],
                        process_build_queue.TRIGGER_FIELD: ["Y"],
                        process_build_queue.IMMEDIATE_TRIGGER_FIELD: False,
                    },
                },
            ]
        )

        self.assertEqual(["rec_immediate"], [record.record_id for record in records])

    def test_select_pending_queue_records_should_filter_by_workflow_action(self) -> None:
        records = process_build_queue.select_pending_queue_records(
            [
                {
                    "record_id": "rec_draft",
                    "fields": {
                        process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_en_1.0",
                        process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                        process_build_queue.VERSION_FIELD: ["1.0"],
                        process_build_queue.LANG_FIELD: ["en"],
                        process_build_queue.WORKFLOW_ACTION_FIELD: ["Build Draft Package"],
                        process_build_queue.DOC_PHASE_FIELD: ["Draft"],
                        process_build_queue.TRIGGER_FIELD: ["Y"],
                        process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    },
                },
                {
                    "record_id": "rec_publish",
                    "fields": {
                        process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_JP_ja_1.0",
                        process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_JP",
                        process_build_queue.VERSION_FIELD: ["1.0"],
                        process_build_queue.LANG_FIELD: ["ja"],
                        process_build_queue.WORKFLOW_ACTION_FIELD: ["Publish"],
                        process_build_queue.DOC_PHASE_FIELD: ["Publish"],
                        process_build_queue.TRIGGER_FIELD: ["Y"],
                        process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    },
                },
            ],
            workflow_action="draft",
        )

        self.assertEqual(["rec_draft"], [record.record_id for record in records])

    def test_select_pending_queue_records_should_reject_targeted_untriggered_row(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            process_build_queue.select_pending_queue_records(
                [
                    {
                        "record_id": "rec_untriggered",
                        "fields": {
                            process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_EU_fr_0.6",
                            process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_EU",
                            process_build_queue.VERSION_FIELD: ["0.6"],
                            process_build_queue.LANG_FIELD: ["fr"],
                            process_build_queue.BUILD_FAMILY_FIELD: "eu-fr",
                            process_build_queue.WORKFLOW_ACTION_FIELD: ["Build Draft Package"],
                            process_build_queue.TRIGGER_FIELD: ["已构建"],
                            process_build_queue.IMMEDIATE_TRIGGER_FIELD: False,
                        },
                    }
                ],
                workflow_action="draft",
                record_id="rec_untriggered",
            )

        self.assertIn("rec_untriggered", str(ctx.exception))
        self.assertIn("是否触发文档构建", str(ctx.exception))

    def test_select_pending_queue_records_should_match_object_style_workflow_action(self) -> None:
        records = process_build_queue.select_pending_queue_records(
            [
                {
                    "record_id": "rec_draft_object",
                    "fields": {
                        process_build_queue.DOCUMENT_ID_FIELD: {"text": "JE-1000F_US_en_1.0"},
                        process_build_queue.DOCUMENT_KEY_FIELD: {"text": "JE-1000F_US"},
                        process_build_queue.VERSION_FIELD: [{"text": "1.0"}],
                        process_build_queue.LANG_FIELD: [{"text": "en"}],
                        process_build_queue.WORKFLOW_ACTION_FIELD: [{"text": "Build Draft Package"}],
                        process_build_queue.TRIGGER_FIELD: [{"text": "Y"}],
                        process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    },
                },
                {
                    "record_id": "rec_publish_object",
                    "fields": {
                        process_build_queue.DOCUMENT_ID_FIELD: {"text": "JE-1000F_JP_ja_1.0"},
                        process_build_queue.DOCUMENT_KEY_FIELD: {"text": "JE-1000F_JP"},
                        process_build_queue.VERSION_FIELD: [{"text": "1.0"}],
                        process_build_queue.LANG_FIELD: [{"text": "ja"}],
                        process_build_queue.WORKFLOW_ACTION_FIELD: [{"text": "Publish"}],
                        process_build_queue.TRIGGER_FIELD: [{"text": "Y"}],
                        process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    },
                },
            ],
            workflow_action="draft",
        )

        self.assertEqual(["rec_draft_object"], [record.record_id for record in records])

    def test_select_pending_queue_records_should_match_object_style_publish_action(self) -> None:
        records = process_build_queue.select_pending_queue_records(
            [
                {
                    "record_id": "rec_draft_object",
                    "fields": {
                        process_build_queue.DOCUMENT_ID_FIELD: {"text": "JE-1000F_US_en_1.0"},
                        process_build_queue.DOCUMENT_KEY_FIELD: {"text": "JE-1000F_US"},
                        process_build_queue.VERSION_FIELD: [{"text": "1.0"}],
                        process_build_queue.LANG_FIELD: [{"text": "en"}],
                        process_build_queue.WORKFLOW_ACTION_FIELD: [{"text": "Build Draft Package"}],
                        process_build_queue.TRIGGER_FIELD: [{"text": "Y"}],
                        process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    },
                },
                {
                    "record_id": "rec_publish_object",
                    "fields": {
                        process_build_queue.DOCUMENT_ID_FIELD: {"text": "JE-1000F_JP_ja_1.0"},
                        process_build_queue.DOCUMENT_KEY_FIELD: {"text": "JE-1000F_JP"},
                        process_build_queue.VERSION_FIELD: [{"text": "1.0"}],
                        process_build_queue.LANG_FIELD: [{"text": "ja"}],
                        process_build_queue.WORKFLOW_ACTION_FIELD: [{"text": "Publish"}],
                        process_build_queue.TRIGGER_FIELD: [{"text": "Y"}],
                        process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    },
                },
            ],
            workflow_action="publish",
        )

        self.assertEqual(["rec_publish_object"], [record.record_id for record in records])

    def test_select_pending_queue_records_should_skip_start_review_rows_in_shared_view(self) -> None:
        records = process_build_queue.select_pending_queue_records(
            [
                {
                    "record_id": "rec_start_review",
                    "fields": {
                        process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_JP_ja_1.0",
                        process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_JP",
                        process_build_queue.VERSION_FIELD: ["1.0"],
                        process_build_queue.LANG_FIELD: ["ja"],
                        process_build_queue.WORKFLOW_ACTION_FIELD: ["Start Review"],
                        process_build_queue.TRIGGER_FIELD: ["Y"],
                        process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    },
                },
                {
                    "record_id": "rec_publish",
                    "fields": {
                        process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_JP_ja_1.0",
                        process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_JP",
                        process_build_queue.VERSION_FIELD: ["1.0"],
                        process_build_queue.LANG_FIELD: ["ja"],
                        process_build_queue.WORKFLOW_ACTION_FIELD: ["Publish"],
                        process_build_queue.TRIGGER_FIELD: ["Y"],
                        process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    },
                },
            ]
        )

        self.assertEqual(["rec_publish"], [record.record_id for record in records])

    def test_select_pending_queue_records_should_filter_by_record_id(self) -> None:
        records = process_build_queue.select_pending_queue_records(
            [
                {
                    "record_id": "rec_a",
                    "fields": {
                        process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_en_1.0",
                        process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                        process_build_queue.VERSION_FIELD: ["1.0"],
                        process_build_queue.LANG_FIELD: ["en"],
                        process_build_queue.WORKFLOW_ACTION_FIELD: ["Build Draft Package"],
                        process_build_queue.DOC_PHASE_FIELD: ["Draft"],
                        process_build_queue.TRIGGER_FIELD: ["Y"],
                        process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    },
                },
                {
                    "record_id": "rec_b",
                    "fields": {
                        process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_fr_1.0",
                        process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                        process_build_queue.VERSION_FIELD: ["1.0"],
                        process_build_queue.LANG_FIELD: ["fr"],
                        process_build_queue.WORKFLOW_ACTION_FIELD: ["Build Draft Package"],
                        process_build_queue.DOC_PHASE_FIELD: ["Draft"],
                        process_build_queue.TRIGGER_FIELD: ["Y"],
                        process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    },
                },
            ],
            record_id="rec_b",
        )

        self.assertEqual(["rec_b"], [record.record_id for record in records])

    def test_normalize_doc_phase_should_accept_draft_and_publish_aliases(self) -> None:
        self.assertEqual("draft", process_build_queue.normalize_doc_phase("Draft"))
        self.assertEqual("draft", process_build_queue.normalize_doc_phase("review"))
        self.assertEqual("draft", process_build_queue.normalize_doc_phase("Draft Package"))
        self.assertEqual("draft", process_build_queue.normalize_doc_phase("Build Draft Package"))
        self.assertEqual("publish", process_build_queue.normalize_doc_phase("Publish"))
        self.assertIsNone(process_build_queue.normalize_doc_phase(""))

    def test_normalize_workflow_action_should_accept_canonical_labels(self) -> None:
        self.assertEqual("draft", process_build_queue.normalize_workflow_action("Build Draft Package"))
        self.assertEqual("draft", process_build_queue.normalize_workflow_action("build-draft-package"))
        self.assertEqual("publish", process_build_queue.normalize_workflow_action("Publish"))
        self.assertIsNone(process_build_queue.normalize_workflow_action(""))

    def test_normalize_doc_phase_should_reject_unknown_value(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "Doc_phase must map to Build Draft Package or Publish"):
            process_build_queue.normalize_doc_phase("staging")

    def test_resolve_queue_workflow_action_should_use_workflow_action_and_require_it(self) -> None:
        record = process_build_queue.QueueRecord(
            record_id="rec_1",
            document_id="JE-1000F_US_en_1.0",
            document_key="JE-1000F_US",
            version="1.0",
            lang="en",
            workflow_action="Build Draft Package",
            doc_phase="Draft",
        )
        self.assertEqual("draft", process_build_queue.resolve_queue_workflow_action(record))

        conflicting_doc_phase_record = process_build_queue.QueueRecord(
            record_id="rec_2",
            document_id="JE-1000F_US_en_1.0",
            document_key="JE-1000F_US",
            version="1.0",
            lang="en",
            workflow_action="Publish",
            doc_phase="Draft",
        )
        self.assertEqual("publish", process_build_queue.resolve_queue_workflow_action(conflicting_doc_phase_record))

        missing_workflow_action_record = process_build_queue.QueueRecord(
            record_id="rec_3",
            document_id="JE-1000F_US_en_1.0",
            document_key="JE-1000F_US",
            version="1.0",
            lang="en",
            workflow_action="",
            doc_phase="Draft",
        )
        with self.assertRaisesRegex(RuntimeError, "Workflow_action is required for queue record rec_3"):
            process_build_queue.resolve_queue_workflow_action(missing_workflow_action_record)

    def test_queue_record_uses_legacy_doc_phase_should_always_be_false(self) -> None:
        legacy_record = process_build_queue.QueueRecord(
            record_id="rec_legacy",
            document_id="JE-1000F_US_en_1.0",
            document_key="JE-1000F_US",
            version="1.0",
            lang="en",
            workflow_action="",
            doc_phase="Draft",
        )
        canonical_record = process_build_queue.QueueRecord(
            record_id="rec_new",
            document_id="JE-1000F_US_en_1.0",
            document_key="JE-1000F_US",
            version="1.0",
            lang="en",
            workflow_action="Build Draft Package",
            doc_phase="Draft",
        )

        self.assertFalse(process_build_queue.queue_record_uses_legacy_doc_phase(legacy_record))
        self.assertFalse(process_build_queue.queue_record_uses_legacy_doc_phase(canonical_record))

    def test_validate_queue_record_group_should_reject_mixed_force_phase2_refresh_values(self) -> None:
        record_a = process_build_queue.QueueRecord(
            record_id="rec_a",
            document_id="JE-1000F_US_1.0",
            document_key="JE-1000F_US",
            version="1.0",
            lang="",
            build_family="us-merged",
            workflow_action="Build Draft Package",
            git_ref="codex/review-je-1000f-us",
            force_phase2_refresh_value=True,
        )
        record_b = process_build_queue.QueueRecord(
            record_id="rec_b",
            document_id="JE-1000F_US_1.0",
            document_key="JE-1000F_US",
            version="1.0",
            lang="",
            build_family="us-merged",
            workflow_action="Build Draft Package",
            git_ref="codex/review-je-1000f-us",
            force_phase2_refresh_value=False,
        )

        with self.assertRaisesRegex(RuntimeError, "是否强制刷新数据"):
            process_build_queue.validate_queue_record_group([record_a, record_b])

    def test_validate_queue_record_group_should_reject_mixed_upload_dingtalk_values(self) -> None:
        record_a = process_build_queue.QueueRecord(
            record_id="rec_a",
            document_id="JE-1000F_US_1.0",
            document_key="JE-1000F_US",
            version="1.0",
            lang="",
            build_family="us-merged",
            workflow_action="Build Draft Package",
            git_ref="codex/review-je-1000f-us",
            upload_dingtalk_value=True,
        )
        record_b = process_build_queue.QueueRecord(
            record_id="rec_b",
            document_id="JE-1000F_US_1.0",
            document_key="JE-1000F_US",
            version="1.0",
            lang="",
            build_family="us-merged",
            workflow_action="Build Draft Package",
            git_ref="codex/review-je-1000f-us",
            upload_dingtalk_value=False,
        )

        with self.assertRaisesRegex(RuntimeError, "是否上传钉钉"):
            process_build_queue.validate_queue_record_group([record_a, record_b])

    def test_validate_queue_record_group_should_reject_mixed_dingtalk_target_node_urls(self) -> None:
        record_a = process_build_queue.QueueRecord(
            record_id="rec_a",
            document_id="JE-1000F_US_1.0",
            document_key="JE-1000F_US",
            version="1.0",
            lang="",
            build_family="us-merged",
            workflow_action="Build Draft Package",
            git_ref="codex/review-je-1000f-us",
            upload_dingtalk_value=True,
            dingtalk_target_node_url="https://alidocs.dingtalk.com/i/nodes/nodeA",
        )
        record_b = process_build_queue.QueueRecord(
            record_id="rec_b",
            document_id="JE-1000F_US_1.0",
            document_key="JE-1000F_US",
            version="1.0",
            lang="",
            build_family="us-merged",
            workflow_action="Build Draft Package",
            git_ref="codex/review-je-1000f-us",
            upload_dingtalk_value=True,
            dingtalk_target_node_url="https://alidocs.dingtalk.com/i/nodes/nodeB",
        )

        with self.assertRaisesRegex(RuntimeError, "DingTalk_target_node_url"):
            process_build_queue.validate_queue_record_group([record_a, record_b])

    def test_validate_queue_record_group_should_reject_mixed_operator_union_ids(self) -> None:
        record_a = process_build_queue.QueueRecord(
            record_id="rec_a",
            document_id="JE-1000F_US_1.0",
            document_key="JE-1000F_US",
            version="1.0",
            lang="",
            build_family="us-merged",
            workflow_action="Build Draft Package",
            git_ref="codex/review-je-1000f-us",
            upload_dingtalk_value=True,
            operator_union_id="union_a",
        )
        record_b = process_build_queue.QueueRecord(
            record_id="rec_b",
            document_id="JE-1000F_US_1.0",
            document_key="JE-1000F_US",
            version="1.0",
            lang="",
            build_family="us-merged",
            workflow_action="Build Draft Package",
            git_ref="codex/review-je-1000f-us",
            upload_dingtalk_value=True,
            operator_union_id="union_b",
        )

        with self.assertRaisesRegex(RuntimeError, "operator_union_id"):
            process_build_queue.validate_queue_record_group([record_a, record_b])

    def test_build_document_for_task_should_use_review_source_for_draft_phase(self) -> None:
        commands: list[list[str]] = []
        with tempfile.TemporaryDirectory() as td:
            word_path = Path(td) / "docs" / "_build" / "JE-1000F" / "US" / "en" / "word" / "manual_je1000f_us_en.docx"
            md_path = Path(td) / "docs" / "_build" / "JE-1000F" / "US" / "en" / "md" / "manual_je1000f_us_en.md"
            word_path.parent.mkdir(parents=True, exist_ok=True)
            word_path.write_bytes(b"docx")
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text("# Manual\n", encoding="utf-8")

            with mock.patch.object(
                process_build_queue,
                "_run_command",
                side_effect=lambda cmd, **kwargs: commands.append(cmd),
            ), mock.patch.object(
                process_build_queue,
                "resolve_word_output_path_for_target",
                return_value=word_path,
            ) as resolve_word_mock, mock.patch.object(
                process_build_queue,
                "resolve_md_output_path_for_target",
                return_value=md_path,
            ) as resolve_md_mock:
                resolved_path = process_build_queue.build_document_for_task(
                    config_path=Path("configs/config.us-en.yaml"),
                    model="JE-1000F",
                    region="US",
                    data_root="data/phase2",
                    doc_phase="Draft",
                    lang="en",
                    version="0.2",
                )
                self.assertTrue(resolved_path.word_output_path.exists())

        self.assertEqual(word_path.with_name("manual_je1000f_us_en_0.2.docx"), resolved_path.word_output_path)
        self.assertEqual(md_path.with_name("manual_je1000f_us_en_0.2.md"), resolved_path.md_output_path)
        self.assertEqual(resolved_path.word_output_path, resolved_path.upload_output_path)
        self.assertIsNone(resolved_path.pdf_output_path)
        self.assertEqual(3, len(commands))
        self.assertEqual("check", commands[0][2])
        self.assertIn("--lang", commands[0])
        self.assertEqual("en", commands[0][commands[0].index("--lang") + 1])
        self.assertIn("--source", commands[0])
        self.assertIn("review", commands[0])
        self.assertEqual("word", commands[1][2])
        self.assertIn("--lang", commands[1])
        self.assertEqual("en", commands[1][commands[1].index("--lang") + 1])
        self.assertIn("--source", commands[1])
        self.assertIn("review", commands[1])
        self.assertIn("--no-clean", commands[1])
        self.assertEqual("md", commands[2][2])
        self.assertIn("--lang", commands[2])
        self.assertEqual("en", commands[2][commands[2].index("--lang") + 1])
        self.assertIn("--source", commands[2])
        self.assertIn("review", commands[2])
        self.assertIn("--no-clean", commands[2])
        resolve_word_mock.assert_called_once_with(
            config_path=Path("configs/config.us-en.yaml"),
            model="JE-1000F",
            region="US",
            lang="en",
        )
        resolve_md_mock.assert_called_once_with(
            config_path=Path("configs/config.us-en.yaml"),
            model="JE-1000F",
            region="US",
            lang="en",
        )

    def test_resolve_word_output_path_should_preserve_pt_br_language_component(self) -> None:
        with temp_test_root() as root:
            config_path = root / "config.pt-br.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "build:",
                        "  default_region: pt-BR",
                        "  languages: [en, pt-BR]",
                        "  include_lang_in_output_path: false",
                        "  word_output: manual_{model_slug}_{region_slug}_{lang_slug}.docx",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with mock.patch.object(process_build_queue, "ROOT", root):
                word_path = process_build_queue.resolve_word_output_path_for_target(
                    config_path=config_path,
                    model="JE-1500D",
                    region="pt-BR",
                    lang="br",
                )
                english_word_path = process_build_queue.resolve_word_output_path_for_target(
                    config_path=config_path,
                    model="JE-1500D",
                    region="pt-BR",
                    lang="en",
                )

        self.assertEqual(
            root / "docs" / "_build" / "JE-1500D" / "pt-BR" / "pt-BR" / "word" / "manual_je1500d_ptbr_br.docx",
            word_path,
        )
        self.assertEqual(
            root / "docs" / "_build" / "JE-1500D" / "pt-BR" / "en" / "word" / "manual_je1500d_ptbr_en.docx",
            english_word_path,
        )

    def test_build_document_for_task_should_build_from_main_workspace_overlay_review_content_and_stage_output_under_host_repo(self) -> None:
        commands: list[tuple[list[str], Path]] = []
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            main_worktree = root / ".tmp" / "process-build-queue-worktrees" / "main"
            review_worktree = root / ".tmp" / "process-build-queue-worktrees" / "codex-review-us-en"
            host_config_path = root / "config.us-en.yaml"
            main_worktree_config_path = main_worktree / "config.us-en.yaml"
            main_worktree_word_path = (
                main_worktree / "docs" / "_build" / "JE-1000F" / "US" / "en" / "word" / "manual_je1000f_us_en.docx"
            )
            main_worktree_pdf_path = (
                main_worktree / "docs" / "_build" / "JE-1000F" / "US" / "en" / "pdf" / "manual_je1000f_us_en.pdf"
            )
            main_worktree_md_path = (
                main_worktree / "docs" / "_build" / "JE-1000F" / "US" / "en" / "md" / "manual_je1000f_us_en.md"
            )
            main_worktree_html_dir = main_worktree / "docs" / "_build" / "JE-1000F" / "US" / "en" / "html"
            host_config_path.write_text("build: {}\n", encoding="utf-8")
            main_worktree_config_path.parent.mkdir(parents=True, exist_ok=True)
            main_worktree_config_path.write_text("build: {}\n", encoding="utf-8")
            main_worktree_word_path.parent.mkdir(parents=True, exist_ok=True)
            main_worktree_word_path.write_bytes(b"docx")
            main_worktree_pdf_path.parent.mkdir(parents=True, exist_ok=True)
            main_worktree_pdf_path.write_bytes(b"pdf")
            main_worktree_md_path.parent.mkdir(parents=True, exist_ok=True)
            main_worktree_md_path.write_text("# Manual\n", encoding="utf-8")
            main_worktree_html_dir.mkdir(parents=True, exist_ok=True)
            (main_worktree_html_dir / "index.html").write_text("<html>published</html>\n", encoding="utf-8")
            (root / "data" / "phase2").mkdir(parents=True, exist_ok=True)
            (root / "data" / "phase2" / "Spec_Master.csv").write_text("fresh-main-data\n", encoding="utf-8")
            (review_worktree / "docs" / "_review" / "JE-1000F" / "US").mkdir(parents=True, exist_ok=True)
            (review_worktree / "docs" / "_review" / "JE-1000F" / "US" / "marker.rst").write_text(
                "review-content\n",
                encoding="utf-8",
            )
            (review_worktree / "data" / "phase2").mkdir(parents=True, exist_ok=True)
            (review_worktree / "data" / "phase2" / "Spec_Master.csv").write_text("stale-review-data\n", encoding="utf-8")

            with mock.patch.object(process_build_queue, "ROOT", root), mock.patch.object(
                process_build_queue,
                "_prepare_git_ref_worktree",
                side_effect=[main_worktree, review_worktree],
            ) as prepare_mock, mock.patch.object(
                process_build_queue,
                "_remove_worktree",
            ) as remove_mock, mock.patch.object(
                process_build_queue,
                "_run_command",
                side_effect=lambda cmd, **kwargs: commands.append((cmd, kwargs.get("cwd"))),
            ), mock.patch.object(
                process_build_queue,
                "resolve_word_output_path_for_target",
                return_value=main_worktree_word_path,
            ), mock.patch.object(
                process_build_queue,
                "resolve_pdf_output_path_for_target",
                return_value=main_worktree_pdf_path,
            ), mock.patch.object(
                process_build_queue,
                "resolve_md_output_path_for_target",
                return_value=main_worktree_md_path,
            ), mock.patch.object(
                process_build_queue,
                "resolve_html_output_dir_for_target",
                return_value=main_worktree_html_dir,
            ):
                resolved_path = process_build_queue.build_document_for_task(
                    config_path=host_config_path,
                    model="JE-1000F",
                    region="US",
                    data_root="data/phase2",
                    doc_phase="Publish",
                    version="0.2",
                    git_ref="codex/review-us-en",
                )
                self.assertTrue(resolved_path.word_output_path.exists())
                self.assertTrue(resolved_path.upload_output_path.exists())
                self.assertEqual(
                    "review-content\n",
                    (main_worktree / "docs" / "_review" / "JE-1000F" / "US" / "marker.rst").read_text(encoding="utf-8"),
                )
                self.assertEqual(
                    "fresh-main-data\n",
                    (main_worktree / "data" / "phase2" / "Spec_Master.csv").read_text(encoding="utf-8"),
                )

        self.assertEqual(
            root / "reports" / "releases" / "JE-1000F" / "US" / "en" / "versions" / "0.2" / "manual_je1000f_us_en_publish_0.2.docx",
            resolved_path.word_output_path,
        )
        self.assertEqual(
            root / "reports" / "releases" / "JE-1000F" / "US" / "en" / "versions" / "0.2" / "manual_je1000f_us_en_publish_0.2.pdf",
            resolved_path.upload_output_path,
        )
        self.assertEqual(
            root / "reports" / "releases" / "JE-1000F" / "US" / "en" / "versions" / "0.2" / "manual_je1000f_us_en_publish_0.2.md",
            resolved_path.md_output_path,
        )
        self.assertEqual(2, len(commands))
        self.assertEqual("publish", commands[0][0][2])
        self.assertEqual(main_worktree, commands[0][1])
        self.assertEqual("html", commands[1][0][2])
        self.assertEqual(main_worktree, commands[1][1])
        self.assertEqual([mock.call("main"), mock.call("codex/review-us-en")], prepare_mock.call_args_list)
        self.assertEqual([mock.call(review_worktree), mock.call(main_worktree)], remove_mock.call_args_list)

    def test_build_document_for_task_should_preserve_configs_path_in_git_ref_worktree(self) -> None:
        commands: list[tuple[list[str], Path]] = []
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            main_worktree = root / ".tmp" / "process-build-queue-worktrees" / "main"
            review_worktree = root / ".tmp" / "process-build-queue-worktrees" / "codex-review-eu"
            host_config_path = root / "configs" / "config.eu.yaml"
            main_worktree_config_path = main_worktree / "configs" / "config.eu.yaml"
            main_worktree_word_path = (
                main_worktree / "docs" / "_build" / "JE-2000F" / "EU" / "word" / "manual_je2000f_eu.docx"
            )
            main_worktree_md_path = (
                main_worktree / "docs" / "_build" / "JE-2000F" / "EU" / "md" / "manual_je2000f_eu.md"
            )
            staged_word_path = root / "docs" / "_build" / "JE-2000F" / "EU" / "word" / "manual_je2000f_eu_0.1.docx"
            staged_md_path = root / "docs" / "_build" / "JE-2000F" / "EU" / "md" / "manual_je2000f_eu_0.1.md"
            host_config_path.parent.mkdir(parents=True, exist_ok=True)
            host_config_path.write_text("build: {}\n", encoding="utf-8")
            main_worktree_config_path.parent.mkdir(parents=True, exist_ok=True)
            main_worktree_config_path.write_text("build: {}\n", encoding="utf-8")
            main_worktree_word_path.parent.mkdir(parents=True, exist_ok=True)
            main_worktree_word_path.write_bytes(b"docx")
            main_worktree_md_path.parent.mkdir(parents=True, exist_ok=True)
            main_worktree_md_path.write_text("# Manual\n", encoding="utf-8")
            (root / "data" / "phase2").mkdir(parents=True, exist_ok=True)
            (root / "data" / "phase2" / "Spec_Master.csv").write_text("fresh-main-data\n", encoding="utf-8")
            (review_worktree / "docs" / "_review" / "JE-2000F" / "EU").mkdir(parents=True, exist_ok=True)
            (review_worktree / "docs" / "_review" / "JE-2000F" / "EU" / "marker.rst").write_text(
                "review-content\n",
                encoding="utf-8",
            )

            with mock.patch.object(process_build_queue, "ROOT", root), mock.patch.object(
                process_build_queue,
                "_prepare_git_ref_worktree",
                side_effect=[main_worktree, review_worktree],
            ), mock.patch.object(
                process_build_queue,
                "_remove_worktree",
            ), mock.patch.object(
                process_build_queue,
                "_run_command",
                side_effect=lambda cmd, **kwargs: commands.append((cmd, kwargs.get("cwd"))),
            ), mock.patch.object(
                process_build_queue,
                "resolve_word_output_path_for_target",
                return_value=main_worktree_word_path,
            ), mock.patch.object(
                process_build_queue,
                "resolve_md_output_path_for_target",
                return_value=main_worktree_md_path,
            ), mock.patch.object(
                process_build_queue,
                "_stage_draft_word_output_to_host_repo",
                return_value=staged_word_path,
            ), mock.patch.object(
                process_build_queue,
                "_stage_draft_md_output_to_host_repo",
                return_value=staged_md_path,
            ):
                process_build_queue.build_document_for_task(
                    config_path=host_config_path,
                    model="JE-2000F",
                    region="EU",
                    data_root="data/phase2",
                    doc_phase="Draft",
                    version="0.1",
                    git_ref="codex/review-eu",
                )

        self.assertEqual(3, len(commands))
        check_command, check_cwd = commands[0]
        self.assertEqual(main_worktree, check_cwd)
        self.assertIn(str(main_worktree / "configs" / "config.eu.yaml"), check_command)
        self.assertNotIn(str(main_worktree / "config.eu.yaml"), check_command)

    def test_build_document_for_task_should_copy_absolute_repo_data_root_into_git_ref_worktree(self) -> None:
        commands: list[tuple[list[str], Path]] = []
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source_data_root = root / "data" / "phase2"
            main_worktree = root / ".tmp" / "process-build-queue-worktrees" / "main"
            review_worktree = root / ".tmp" / "process-build-queue-worktrees" / "codex-review-us-en"
            host_config_path = root / "config.us-en.yaml"
            main_worktree_config_path = main_worktree / "config.us-en.yaml"
            main_worktree_word_path = (
                main_worktree / "docs" / "_build" / "JE-1000F" / "US" / "en" / "word" / "manual_je1000f_us_en.docx"
            )
            main_worktree_md_path = (
                main_worktree / "docs" / "_build" / "JE-1000F" / "US" / "en" / "md" / "manual_je1000f_us_en.md"
            )
            staged_word_path = root / "docs" / "_build" / "JE-1000F" / "US" / "en" / "word" / "manual_je1000f_us_en_0.3.docx"
            staged_md_path = root / "docs" / "_build" / "JE-1000F" / "US" / "en" / "md" / "manual_je1000f_us_en_0.3.md"
            host_config_path.write_text("build: {}\n", encoding="utf-8")
            main_worktree_config_path.parent.mkdir(parents=True, exist_ok=True)
            main_worktree_config_path.write_text("build: {}\n", encoding="utf-8")
            main_worktree_word_path.parent.mkdir(parents=True, exist_ok=True)
            main_worktree_word_path.write_bytes(b"docx")
            main_worktree_md_path.parent.mkdir(parents=True, exist_ok=True)
            main_worktree_md_path.write_text("# Manual\n", encoding="utf-8")
            source_data_root.mkdir(parents=True, exist_ok=True)
            (source_data_root / "Spec_Master.csv").write_text("fresh-host-data\n", encoding="utf-8")
            (source_data_root / "_attachments" / "lcd_icons").mkdir(parents=True, exist_ok=True)
            (source_data_root / "_attachments" / "lcd_icons" / "1_Wi-Fi_token.png").write_bytes(b"png")
            (main_worktree / "data" / "phase2").mkdir(parents=True, exist_ok=True)
            (main_worktree / "data" / "phase2" / "Spec_Master.csv").write_text("stale-worktree-data\n", encoding="utf-8")
            (review_worktree / "docs" / "_review" / "JE-1000F" / "US").mkdir(parents=True, exist_ok=True)
            (review_worktree / "docs" / "_review" / "JE-1000F" / "US" / "marker.rst").write_text(
                "review-content\n",
                encoding="utf-8",
            )

            with mock.patch.object(process_build_queue, "ROOT", root), mock.patch.object(
                process_build_queue,
                "_prepare_git_ref_worktree",
                side_effect=[main_worktree, review_worktree],
            ), mock.patch.object(
                process_build_queue,
                "_remove_worktree",
            ), mock.patch.object(
                process_build_queue,
                "_run_command",
                side_effect=lambda cmd, **kwargs: commands.append((cmd, kwargs.get("cwd"))),
            ), mock.patch.object(
                process_build_queue,
                "resolve_word_output_path_for_target",
                return_value=main_worktree_word_path,
            ), mock.patch.object(
                process_build_queue,
                "resolve_md_output_path_for_target",
                return_value=main_worktree_md_path,
            ), mock.patch.object(
                process_build_queue,
                "_stage_draft_word_output_to_host_repo",
                return_value=staged_word_path,
            ), mock.patch.object(
                process_build_queue,
                "_stage_draft_md_output_to_host_repo",
                return_value=staged_md_path,
            ):
                resolved_path = process_build_queue.build_document_for_task(
                    config_path=host_config_path,
                    model="JE-1000F",
                    region="US",
                    data_root=str(source_data_root),
                    doc_phase="Draft",
                    version="0.3",
                    git_ref="codex/review-us-en",
                )
                self.assertEqual(staged_word_path, resolved_path.word_output_path)
                self.assertEqual(staged_md_path, resolved_path.md_output_path)
                self.assertEqual(
                    "review-content\n",
                    (main_worktree / "docs" / "_review" / "JE-1000F" / "US" / "marker.rst").read_text(encoding="utf-8"),
                )
                self.assertEqual(
                    "fresh-host-data\n",
                    (main_worktree / "data" / "phase2" / "Spec_Master.csv").read_text(encoding="utf-8"),
                )
                self.assertTrue((main_worktree / "data" / "phase2" / "_attachments" / "lcd_icons" / "1_Wi-Fi_token.png").exists())

        expected_data_root = str(main_worktree / "data" / "phase2")
        self.assertEqual(3, len(commands))
        for command, cwd in commands:
            self.assertEqual(main_worktree, cwd)
            data_root_index = command.index("--data-root")
            self.assertEqual(expected_data_root, command[data_root_index + 1])

    def test_build_document_for_task_should_use_publish_action_for_publish_phase(self) -> None:
        commands: list[list[str]] = []
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_path = root / "config.ja.yaml"
            word_path = root / "docs" / "_build" / "JE-1000F" / "JP" / "word" / "manual_je1000f_jp.docx"
            pdf_path = root / "docs" / "_build" / "JE-1000F" / "JP" / "pdf" / "manual_je1000f_jp.pdf"
            md_path = root / "docs" / "_build" / "JE-1000F" / "JP" / "md" / "manual_je1000f_jp.md"
            html_dir = root / "docs" / "_build" / "JE-1000F" / "JP" / "html"
            config_path.write_text("build:\n  languages: [ja]\n", encoding="utf-8")
            word_path.parent.mkdir(parents=True, exist_ok=True)
            word_path.write_bytes(b"docx")
            pdf_path.parent.mkdir(parents=True, exist_ok=True)
            pdf_path.write_bytes(b"pdf")
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text("# Manual\n", encoding="utf-8")
            html_dir.mkdir(parents=True, exist_ok=True)
            (html_dir / "index.html").write_text("<html>publish</html>\n", encoding="utf-8")

            with mock.patch.object(process_build_queue, "ROOT", root), mock.patch.object(
                process_build_queue,
                "_run_command",
                side_effect=lambda cmd, **kwargs: commands.append(cmd),
            ), mock.patch.object(
                process_build_queue,
                "resolve_word_output_path_for_target",
                return_value=word_path,
            ), mock.patch.object(
                process_build_queue,
                "resolve_pdf_output_path_for_target",
                return_value=pdf_path,
            ), mock.patch.object(
                process_build_queue,
                "resolve_md_output_path_for_target",
                return_value=md_path,
            ), mock.patch.object(
                process_build_queue,
                "resolve_html_output_dir_for_target",
                return_value=html_dir,
            ):
                resolved_path = process_build_queue.build_document_for_task(
                    config_path=config_path,
                    model="JE-1000F",
                    region="JP",
                    data_root="data/phase2",
                    doc_phase="Publish",
                    version="1.0",
                )
                self.assertTrue(resolved_path.word_output_path.exists())
                self.assertTrue(resolved_path.upload_output_path.exists())

        self.assertEqual(
            root / "reports" / "releases" / "JE-1000F" / "JP" / "ja" / "versions" / "1.0" / "manual_je1000f_jp_publish_1.0.docx",
            resolved_path.word_output_path,
        )
        self.assertEqual(
            root / "reports" / "releases" / "JE-1000F" / "JP" / "ja" / "versions" / "1.0" / "manual_je1000f_jp_publish_1.0.pdf",
            resolved_path.upload_output_path,
        )
        self.assertEqual(
            root / "reports" / "releases" / "JE-1000F" / "JP" / "ja" / "versions" / "1.0" / "manual_je1000f_jp_publish_1.0.md",
            resolved_path.md_output_path,
        )
        self.assertEqual(2, len(commands))
        self.assertEqual("publish", commands[0][2])
        self.assertEqual("html", commands[1][2])
        self.assertIn("--data-root", commands[0])

    def test_write_publish_release_metadata_should_write_latest_and_version_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_path = root / "config.us-en.yaml"
            config_path.write_text("build:\n  languages: [en]\n  include_lang_in_output_path: true\n", encoding="utf-8")
            word_output_path = root / "reports" / "releases" / "JE-1000F" / "US" / "en" / "versions" / "0.2" / "manual_je1000f_us_en_publish_0.2.docx"
            pdf_output_path = root / "reports" / "releases" / "JE-1000F" / "US" / "en" / "versions" / "0.2" / "manual_je1000f_us_en_publish_0.2.pdf"
            md_output_path = root / "reports" / "releases" / "JE-1000F" / "US" / "en" / "versions" / "0.2" / "manual_je1000f_us_en_publish_0.2.md"
            html_dir = root / "reports" / "releases" / "JE-1000F" / "US" / "en" / "latest" / "html"
            word_output_path.parent.mkdir(parents=True, exist_ok=True)
            html_dir.mkdir(parents=True, exist_ok=True)
            word_output_path.write_bytes(b"docx")
            pdf_output_path.write_bytes(b"pdf")
            md_output_path.write_text("# Manual\n", encoding="utf-8")
            (html_dir / "index.html").write_text("<html>published</html>\n", encoding="utf-8")

            with mock.patch.object(process_build_queue, "ROOT", root):
                latest_meta = process_build_queue.write_publish_release_metadata(
                    config_path=config_path,
                    model="JE-1000F",
                    region="US",
                    version="0.2",
                    git_ref="codex/review-us-en",
                    built_at=datetime(2026, 4, 4, 12, 0, 0),
                    word_output_path=word_output_path,
                    pdf_output_path=pdf_output_path,
                    md_output_path=md_output_path,
                    html_dir=html_dir,
                    document_link_url="https://example.feishu.cn/wiki/token_123",
                    queue_record_ids=("rec_publish_1", "rec_publish_2"),
                )

            self.assertEqual(
                root / "reports" / "releases" / "JE-1000F" / "US" / "en" / "latest" / "publish_meta.json",
                latest_meta,
            )
            payload = process_build_queue.json.loads(latest_meta.read_text(encoding="utf-8"))
            self.assertEqual("JE-1000F", payload["model"])
            self.assertEqual("US", payload["region"])
            self.assertEqual("en", payload["lang"])
            self.assertEqual("0.2", payload["version"])
            self.assertEqual("https://example.feishu.cn/wiki/token_123", payload["document_link_url"])
            self.assertEqual(
                "reports/releases/JE-1000F/US/en/versions/0.2/manual_je1000f_us_en_publish_0.2.pdf",
                payload["pdf_output_path"],
            )
            self.assertEqual(
                "reports/releases/JE-1000F/US/en/versions/0.2/manual_je1000f_us_en_publish_0.2.md",
                payload["md_output_path"],
            )
            self.assertEqual(
                "reports/releases/JE-1000F/US/en/latest/html/index.html",
                payload["html_index"],
            )
            self.assertEqual(["rec_publish_1", "rec_publish_2"], payload["queue_record_ids"])

    def test_versioned_word_output_path_should_preserve_original_when_version_missing(self) -> None:
        path = Path("docs/_build/JE-1000F/US/en/word/manual_je1000f_us_en.docx")

        resolved = process_build_queue._versioned_word_output_path(path, version="")

        self.assertEqual(path, resolved)

    def test_versioned_word_output_path_should_append_sanitized_version(self) -> None:
        path = Path("docs/_build/JE-1000F/US/en/word/manual_je1000f_us_en.docx")

        resolved = process_build_queue._versioned_word_output_path(path, version="V 0.2 / RC1")

        self.assertEqual(
            Path("docs/_build/JE-1000F/US/en/word/manual_je1000f_us_en_V-0.2-RC1.docx"),
            resolved,
        )

    def test_versioned_word_output_path_should_insert_publish_before_version(self) -> None:
        path = Path("docs/_build/JE-1000F/US/en/word/manual_je1000f_us_en.docx")

        resolved = process_build_queue._versioned_word_output_path(
            path,
            version="0.2",
            doc_phase="publish",
        )

        self.assertEqual(
            Path("docs/_build/JE-1000F/US/en/word/manual_je1000f_us_en_publish_0.2.docx"),
            resolved,
        )

    def test_versioned_pdf_output_path_should_insert_publish_before_version(self) -> None:
        path = Path("docs/_build/JE-1000F/US/en/pdf/manual_je1000f_us_en.pdf")

        resolved = process_build_queue._versioned_pdf_output_path(
            path,
            version="0.2",
            doc_phase="publish",
        )

        self.assertEqual(
            Path("docs/_build/JE-1000F/US/en/pdf/manual_je1000f_us_en_publish_0.2.pdf"),
            resolved,
        )

    def test_versioned_md_output_path_should_insert_publish_before_version(self) -> None:
        path = Path("docs/_build/JE-1000F/US/en/md/manual_je1000f_us_en.md")

        resolved = process_build_queue._versioned_md_output_path(
            path,
            version="0.2",
            doc_phase="publish",
        )

        self.assertEqual(
            Path("docs/_build/JE-1000F/US/en/md/manual_je1000f_us_en_publish_0.2.md"),
            resolved,
        )

    def test_sync_phase2_snapshot_before_queue_should_call_build_py_sync_data(self) -> None:
        commands: list[list[str]] = []

        with mock.patch.object(process_build_queue, "_run_command", side_effect=lambda cmd: commands.append(cmd)):
            process_build_queue.sync_phase2_snapshot_before_queue(
                config_path=Path("config.yaml"),
                data_root="data/phase2",
            )

        self.assertEqual(1, len(commands))
        self.assertEqual("sync-data", commands[0][2])
        self.assertIn("--data-root", commands[0])
        self.assertIn("data/phase2", commands[0])

    def test_upload_word_to_drive_should_upload_file_and_resolve_url(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            word_path = root / "docs" / "_build" / "JE-1000F" / "US" / "en" / "word" / "manual_je1000f_us_en.docx"
            word_path.parent.mkdir(parents=True, exist_ok=True)
            word_path.write_bytes(b"docx")
            observed_args: list[list[str]] = []

            def fake_run(*, cli_bin: str, args: list[str]) -> dict[str, object]:
                self.assertEqual("lark-cli", cli_bin)
                observed_args.append(args)
                if args[:2] == ["drive", "+upload"]:
                    return {"ok": True, "data": {"file_token": "file_token_123"}}
                return {
                    "code": 0,
                    "data": {
                        "metas": [
                            {
                                "doc_token": "file_token_123",
                                "url": "https://test-degwga5x6ex8.feishu.cn/file/file_token_123",
                            }
                        ]
                    },
                }

            with mock.patch.object(process_build_queue, "ROOT", root), mock.patch.object(
                process_build_queue,
                "_run_lark_cli_json",
                side_effect=fake_run,
            ):
                file_token, drive_url = process_build_queue.upload_word_to_drive(
                    cli_bin="lark-cli",
                    word_output_path=word_path,
                    identity="bot",
                )

        self.assertEqual("file_token_123", file_token)
        self.assertEqual("https://test-degwga5x6ex8.feishu.cn/file/file_token_123", drive_url)
        self.assertEqual(2, len(observed_args))
        self.assertEqual(["drive", "+upload"], observed_args[0][:2])
        self.assertIn("bot", observed_args[0])
        self.assertEqual(["drive", "metas", "batch_query"], observed_args[1][:3])
        self.assertFalse(Path(observed_args[0][5]).is_absolute())
        self.assertEqual("manual_je1000f_us_en.docx", observed_args[0][7])

    def test_import_markdown_to_cloud_doc_should_call_drive_import_and_parse_url(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            md_path = root / "docs" / "_build" / "JE-1000F" / "US" / "en" / "md" / "manual_je1000f_us_en.md"
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text("# Manual\n", encoding="utf-8")
            observed_args: list[list[str]] = []

            def fake_run(*, cli_bin: str, args: list[str]) -> dict[str, object]:
                self.assertEqual("lark-cli", cli_bin)
                observed_args.append(args)
                return {
                    "code": 0,
                    "data": {
                        "ticket": {
                            "token": "doc_token_123",
                            "url": "https://test-degwga5x6ex8.feishu.cn/docx/doc_token_123",
                        }
                    },
                }

            with mock.patch.object(process_build_queue, "ROOT", root), mock.patch.object(
                process_build_queue,
                "_run_lark_cli_json",
                side_effect=fake_run,
            ):
                token, cloud_doc_url = process_build_queue.import_markdown_to_cloud_doc(
                    cli_bin="lark-cli",
                    markdown_output_path=md_path,
                    identity="bot",
                )

        self.assertEqual("doc_token_123", token)
        self.assertEqual("https://test-degwga5x6ex8.feishu.cn/docx/doc_token_123", cloud_doc_url)
        self.assertEqual(1, len(observed_args))
        self.assertEqual(["drive", "+import"], observed_args[0][:2])
        self.assertIn("--file", observed_args[0])
        self.assertIn("--type", observed_args[0])
        self.assertEqual("docx", observed_args[0][observed_args[0].index("--type") + 1])
        self.assertFalse(Path(observed_args[0][observed_args[0].index("--file") + 1]).is_absolute())

    def test_resolve_wiki_destination_should_default_to_parent_of_document_link_bitable(self) -> None:
        binding = process_build_queue.DocumentLinkBinding(
            base_token_env="BASE_TOKEN",
            table_id_env="DOCUMENT_LINK_TABLE",
            view_id_env="DOCUMENT_LINK_VIEW",
            wiki_parent_token_env=None,
            base_token="app_token",
            table_id="tbl_document_link",
            view_id="vew_document_link",
            wiki_parent_token=None,
        )

        with mock.patch.object(
            process_build_queue,
            "get_wiki_node",
            return_value={
                "space_id": "space_123",
                "node_token": "wiki_current",
                "parent_node_token": "wiki_parent",
            },
        ) as get_node_mock:
            destination = process_build_queue.resolve_wiki_destination(
                cli_bin="lark-cli",
                identity="bot",
                binding=binding,
            )

        self.assertEqual("space_123", destination.space_id)
        self.assertEqual("wiki_parent", destination.parent_wiki_token)
        get_node_mock.assert_called_once_with(
            cli_bin="lark-cli",
            identity="bot",
            token="app_token",
            obj_type="bitable",
        )

    def test_move_drive_file_to_wiki_should_return_wiki_url_from_async_task(self) -> None:
        observed_args: list[list[str]] = []

        def fake_run(*, cli_bin: str, args: list[str]) -> dict[str, object]:
            self.assertEqual("lark-cli", cli_bin)
            observed_args.append(args)
            if args[:3] == ["api", "POST", "/open-apis/wiki/v2/spaces/space_123/nodes/move_docs_to_wiki"]:
                return {"code": 0, "data": {"task_id": "task_123"}}
            return {
                "code": 0,
                "data": {
                    "task": {
                        "task_id": "task_123",
                        "move_result": [
                            {
                                "status": 0,
                                "status_msg": "success",
                                "node": {"node_token": "wiki_token_123"},
                            }
                        ],
                    }
                },
            }

        with mock.patch.object(process_build_queue, "_run_lark_cli_json", side_effect=fake_run), mock.patch.object(
            process_build_queue.time,
            "sleep",
        ):
            wiki_url = process_build_queue.move_drive_file_to_wiki(
                cli_bin="lark-cli",
                identity="bot",
                file_token="file_token_123",
                drive_url="https://test-degwga5x6ex8.feishu.cn/file/file_token_123",
                destination=process_build_queue.WikiDestination(
                    space_id="space_123",
                    parent_wiki_token="wiki_parent",
                ),
            )

        self.assertEqual("https://test-degwga5x6ex8.feishu.cn/wiki/wiki_token_123", wiki_url)
        self.assertEqual(["api", "POST", "/open-apis/wiki/v2/spaces/space_123/nodes/move_docs_to_wiki"], observed_args[0][:3])
        self.assertEqual(["api", "GET", "/open-apis/wiki/v2/tasks/task_123"], observed_args[1][:3])
        self.assertEqual("--params", observed_args[1][3])
        self.assertIn("move", observed_args[1][4])

    def test_command_failure_message_should_extract_lark_permission_context(self) -> None:
        message = process_build_queue._command_failure_message(
            ["lark-cli", "api", "POST", "/open-apis/wiki/v2/spaces/space_123/nodes/move_docs_to_wiki"],
            stdout="",
            stderr='{"ok":false,"identity":"user","error":{"type":"permission","code":99991679,"message":"Permission denied [99991679]","detail":{"permission_violations":[{"subject":"wiki:wiki"},{"subject":"wiki:node:move"}]}}}',
            returncode=1,
        )

        self.assertIn("permission", message)
        self.assertIn("Permission denied [99991679]", message)
        self.assertIn("subjects=wiki:wiki,wiki:node:move", message)

    def test_process_build_queue_should_build_and_write_back_success(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "cli_bin": "lark-cli",
                    "base_token_env": "BASE_TOKEN",
                    "document_link": {
                        "table_id_env": "DOCUMENT_LINK_TABLE",
                        "view_id_env": "DOCUMENT_LINK_VIEW",
                    },
                }
            }
        }
        binding = process_build_queue.DocumentLinkBinding(
            base_token_env="BASE_TOKEN",
            table_id_env="DOCUMENT_LINK_TABLE",
            view_id_env="DOCUMENT_LINK_VIEW",
            wiki_parent_token_env=None,
            base_token="app_token",
            table_id="tbl_document_link",
            view_id="vew_document_link",
            wiki_parent_token=None,
        )
        raw_records = [
            {
                "record_id": "rec_1",
                "fields": {
                    process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_en_1.0",
                    process_build_queue.DOCUMENT_KEY_FIELD: [{"id": "recvfw0zG4PzxS"}],
                    process_build_queue.VERSION_FIELD: ["1.0"],
                    process_build_queue.LANG_FIELD: ["en"],
                    process_build_queue.WORKFLOW_ACTION_FIELD: ["Build Draft Package"],
                    process_build_queue.DOC_PHASE_FIELD: ["Draft"],
                    process_build_queue.GIT_REF_FIELD: ["codex/review-je-1000f-us-en"],
                    process_build_queue.BUILD_STARTED_AT_FIELD: None,
                    process_build_queue.TRIGGER_FIELD: ["Y"],
                    process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    process_build_queue.FORCE_PHASE2_REFRESH_FIELD: False,
                    process_build_queue.DATA_SYNC_FIELD: "",
                },
            }
        ]
        captured_upserts: list[dict[str, object]] = []
        with tempfile.TemporaryDirectory() as td:
            generated_path = (
                Path(td) / "docs" / "_build" / "JE-1000F" / "US" / "en" / "word" / "manual_je1000f_us_en.docx"
            )
            build_document_mock = mock.Mock(return_value=generated_path)
            sync_mock = mock.Mock()

            class FakeSource:
                def fetch_records_with_ids(self, **_: object) -> list[dict[str, object]]:
                    return raw_records

                def upsert_record(self, **kwargs: object) -> dict[str, object]:
                    captured_upserts.append(kwargs)
                    return {"ok": True}

            with mock.patch.object(process_build_queue, "collect_queue_preflight_errors", return_value=[]), mock.patch.object(
                process_build_queue,
                "resolve_document_link_binding",
                return_value=binding,
            ), mock.patch.object(process_build_queue, "LarkCliSource", return_value=FakeSource()), mock.patch.object(
                process_build_queue,
                "sync_phase2_snapshot_before_queue",
                sync_mock,
            ), mock.patch.object(
                process_build_queue,
                "resolve_config_path_for_task",
                return_value=Path("configs/config.us-en.yaml"),
            ), mock.patch.object(
                process_build_queue,
                "build_document_for_task",
                build_document_mock,
            ), mock.patch.object(
                process_build_queue,
                "upload_word_to_drive",
                return_value=("file_token_123", "https://test-degwga5x6ex8.feishu.cn/file/file_token_123"),
            ), mock.patch.object(
                process_build_queue,
                "resolve_wiki_destination",
                return_value=process_build_queue.WikiDestination(
                    space_id="space_123",
                    parent_wiki_token="wiki_parent",
                ),
            ), mock.patch.object(
                process_build_queue,
                "move_drive_file_to_wiki",
                return_value="https://test-degwga5x6ex8.feishu.cn/wiki/wiki_token_123",
            ), mock.patch.object(
                process_build_queue,
                "_phase2_identity",
                return_value="bot",
            ):
                exit_code = process_build_queue.process_build_queue(
                    cfg=cfg,
                    config_path=Path("config.yaml"),
                    data_root="data/phase2",
                    dry_run=False,
                )

        self.assertEqual(0, exit_code)
        self.assertEqual(2, len(captured_upserts))
        self.assertEqual("rec_1", captured_upserts[0]["record_id"])
        started_payload = captured_upserts[0]["record"]
        self.assertIsInstance(started_payload, dict)
        self.assertIn(process_build_queue.BUILD_STARTED_AT_FIELD, started_payload)
        self.assertIn("RUNNING", started_payload[process_build_queue.RESULT_FIELD])
        self.assertIn("workflow_action=Build Draft Package", started_payload[process_build_queue.RESULT_FIELD])
        self.assertEqual("rec_1", captured_upserts[1]["record_id"])
        record_payload = captured_upserts[1]["record"]
        self.assertIsInstance(record_payload, dict)
        self.assertEqual(["已构建"], record_payload[process_build_queue.TRIGGER_FIELD])
        self.assertEqual(
            generated_path.resolve(strict=False).as_posix(),
            record_payload[process_build_queue.DOCUMENT_DIRECTORY_FIELD],
        )
        self.assertEqual(
            "https://test-degwga5x6ex8.feishu.cn/wiki/wiki_token_123",
            record_payload[process_build_queue.DOCUMENT_LINK_FIELD],
        )
        self.assertFalse(record_payload[process_build_queue.IMMEDIATE_TRIGGER_FIELD])
        self.assertFalse(record_payload[process_build_queue.FORCE_PHASE2_REFRESH_FIELD])
        self.assertEqual("skipped", record_payload[process_build_queue.DATA_SYNC_FIELD])
        self.assertIn("data_sync=skipped", record_payload[process_build_queue.RESULT_FIELD])
        self.assertIn("workflow_action=Build Draft Package", record_payload[process_build_queue.RESULT_FIELD])
        build_document_mock.assert_called_once_with(
            config_path=Path("configs/config.us-en.yaml"),
            model="JE-1000F",
            region="US",
            data_root="data/phase2",
            doc_phase="draft",
            lang="en",
            version="1.0",
            git_ref="codex/review-je-1000f-us-en",
        )
        sync_mock.assert_not_called()

    def test_process_build_queue_should_import_markdown_when_cloud_doc_field_exists(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "cli_bin": "lark-cli",
                    "base_token_env": "BASE_TOKEN",
                    "document_link": {
                        "table_id_env": "DOCUMENT_LINK_TABLE",
                        "view_id_env": "DOCUMENT_LINK_VIEW",
                    },
                }
            }
        }
        binding = process_build_queue.DocumentLinkBinding(
            base_token_env="BASE_TOKEN",
            table_id_env="DOCUMENT_LINK_TABLE",
            view_id_env="DOCUMENT_LINK_VIEW",
            wiki_parent_token_env=None,
            base_token="app_token",
            table_id="tbl_document_link",
            view_id="vew_document_link",
            wiki_parent_token=None,
        )
        raw_records = [
            {
                "record_id": "rec_cloud_doc",
                "fields": {
                    process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_en_1.0",
                    process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                    process_build_queue.VERSION_FIELD: ["1.0"],
                    process_build_queue.LANG_FIELD: ["en"],
                    process_build_queue.WORKFLOW_ACTION_FIELD: ["Build Draft Package"],
                    process_build_queue.GIT_REF_FIELD: ["codex/review-je-1000f-us-en"],
                    process_build_queue.BUILD_STARTED_AT_FIELD: None,
                    process_build_queue.TRIGGER_FIELD: ["Y"],
                    process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    process_build_queue.FORCE_PHASE2_REFRESH_FIELD: False,
                    process_build_queue.DATA_SYNC_FIELD: "",
                    process_build_queue.FEISHU_CLOUD_DOC_FIELD: "",
                },
            }
        ]
        captured_upserts: list[dict[str, object]] = []
        cloud_import_calls: list[dict[str, object]] = []
        with tempfile.TemporaryDirectory() as td:
            word_path = Path(td) / "manual.docx"
            md_path = Path(td) / "manual.md"
            word_path.write_bytes(b"docx")
            md_path.write_text("# Manual\n", encoding="utf-8")

            class FakeSource:
                def fetch_records_with_ids(self, **_: object) -> list[dict[str, object]]:
                    return raw_records

                def upsert_record(self, **kwargs: object) -> dict[str, object]:
                    captured_upserts.append(kwargs)
                    return {"ok": True}

            def fake_import_markdown_to_cloud_doc(**kwargs: object) -> tuple[str, str]:
                cloud_import_calls.append(kwargs)
                return "doc_token_123", "https://test-degwga5x6ex8.feishu.cn/docx/doc_token_123"

            finalize_calls: list[dict[str, object]] = []

            def fake_finalize_cloud_doc(**kwargs: object) -> str:
                # Keep the leaf test hermetic (no real lark-cli grant/move); just
                # record the args the leaf passes and echo the import URL back.
                finalize_calls.append(kwargs)
                return str(kwargs["cloud_doc_url"])

            with mock.patch.object(process_build_queue, "collect_queue_preflight_errors", return_value=[]), mock.patch.object(
                process_build_queue,
                "resolve_document_link_binding",
                return_value=binding,
            ), mock.patch.object(process_build_queue, "LarkCliSource", return_value=FakeSource()), mock.patch.object(
                process_build_queue,
                "build_document_for_task",
                return_value=process_build_queue.BuiltDocumentOutputs(
                    word_output_path=word_path,
                    upload_output_path=word_path,
                    md_output_path=md_path,
                ),
            ), mock.patch.object(
                process_build_queue,
                "resolve_artifact_destination",
                return_value=process_build_queue.WikiDestination(
                    space_id="space_123",
                    parent_wiki_token="wiki_parent",
                ),
            ), mock.patch.object(
                process_build_queue,
                "publish_word_artifact",
                return_value=process_build_queue.ArtifactPublishResult(
                    provider="lark_drive",
                    reference_id="file_token_123",
                    latest_link_url="https://test-degwga5x6ex8.feishu.cn/file/file_token_123",
                    document_link_url="https://test-degwga5x6ex8.feishu.cn/wiki/wiki_token_123",
                    status_notes=("published_artifact=docx",),
                ),
            ), mock.patch.object(
                process_build_queue,
                "import_markdown_to_cloud_doc",
                side_effect=fake_import_markdown_to_cloud_doc,
            ), mock.patch.object(
                process_build_queue,
                "finalize_cloud_doc",
                side_effect=fake_finalize_cloud_doc,
            ), mock.patch.object(
                process_build_queue,
                "_phase2_identity",
                return_value="bot",
            ):
                exit_code = process_build_queue.process_build_queue(
                    cfg=cfg,
                    config_path=Path("configs/config.us.yaml"),
                    data_root="data/phase2",
                    dry_run=False,
                )

        self.assertEqual(0, exit_code)
        # two imports: the editable cloud doc + the frozen baseline (same markdown)
        self.assertEqual(2, len(cloud_import_calls))
        self.assertEqual(md_path, cloud_import_calls[0]["markdown_output_path"])
        self.assertEqual(md_path, cloud_import_calls[1]["markdown_output_path"])
        # the editable 飞书云文档 keeps the default (markdown stem) name; the frozen
        # baseline is suffixed _基线<YYYYMMDD> so the two are distinguishable in the node
        self.assertIsNone(cloud_import_calls[0].get("doc_name"))
        baseline_name = str(cloud_import_calls[1]["doc_name"])
        self.assertTrue(baseline_name.startswith(f"{md_path.stem}_基线"))
        baseline_date = baseline_name.rsplit("_基线", 1)[1]
        self.assertTrue(baseline_date.isdigit() and len(baseline_date) == 8)
        success_payload = captured_upserts[-1]["record"]
        self.assertIsInstance(success_payload, dict)
        self.assertEqual(
            "https://test-degwga5x6ex8.feishu.cn/docx/doc_token_123",
            success_payload[process_build_queue.FEISHU_CLOUD_DOC_FIELD],
        )
        # the baseline doc link is recorded in the 基线文档 field for backport to diff against
        self.assertEqual(
            "https://test-degwga5x6ex8.feishu.cn/docx/doc_token_123",
            success_payload[process_build_queue.BASELINE_DOC_FIELD],
        )
        self.assertIn("cloud_doc=ok", success_payload[process_build_queue.RESULT_FIELD])
        self.assertIn("baseline_doc=ok", success_payload[process_build_queue.RESULT_FIELD])
        # finalize runs twice: the editable doc (grant) + the baseline (grant=False)
        self.assertEqual(2, len(finalize_calls))
        self.assertEqual("doc_token_123", finalize_calls[0]["cloud_doc_token"])
        self.assertEqual(
            "https://test-degwga5x6ex8.feishu.cn/docx/doc_token_123",
            finalize_calls[0]["cloud_doc_url"],
        )
        self.assertEqual("space_123", finalize_calls[0]["destination"].space_id)
        self.assertNotEqual(False, finalize_calls[0].get("grant", True))  # editable: granted
        self.assertEqual(False, finalize_calls[1]["grant"])  # baseline: not granted

    def test_process_build_queue_should_fail_when_cloud_doc_import_fails_and_preserve_artifact_link(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "cli_bin": "lark-cli",
                    "base_token_env": "BASE_TOKEN",
                    "document_link": {
                        "table_id_env": "DOCUMENT_LINK_TABLE",
                        "view_id_env": "DOCUMENT_LINK_VIEW",
                    },
                }
            }
        }
        binding = process_build_queue.DocumentLinkBinding(
            base_token_env="BASE_TOKEN",
            table_id_env="DOCUMENT_LINK_TABLE",
            view_id_env="DOCUMENT_LINK_VIEW",
            wiki_parent_token_env=None,
            base_token="app_token",
            table_id="tbl_document_link",
            view_id="vew_document_link",
            wiki_parent_token=None,
        )
        raw_records = [
            {
                "record_id": "rec_cloud_doc_failed",
                "fields": {
                    process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_en_1.0",
                    process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                    process_build_queue.VERSION_FIELD: ["1.0"],
                    process_build_queue.LANG_FIELD: ["en"],
                    process_build_queue.WORKFLOW_ACTION_FIELD: ["Build Draft Package"],
                    process_build_queue.GIT_REF_FIELD: ["codex/review-je-1000f-us-en"],
                    process_build_queue.TRIGGER_FIELD: ["Y"],
                    process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    process_build_queue.FORCE_PHASE2_REFRESH_FIELD: False,
                    process_build_queue.DATA_SYNC_FIELD: "",
                    process_build_queue.FEISHU_CLOUD_DOC_FIELD: "",
                },
            }
        ]
        captured_upserts: list[dict[str, object]] = []
        with tempfile.TemporaryDirectory() as td:
            word_path = Path(td) / "manual.docx"
            md_path = Path(td) / "manual.md"
            word_path.write_bytes(b"docx")
            md_path.write_text("# Manual\n", encoding="utf-8")

            class FakeSource:
                def fetch_records_with_ids(self, **_: object) -> list[dict[str, object]]:
                    return raw_records

                def upsert_record(self, **kwargs: object) -> dict[str, object]:
                    captured_upserts.append(kwargs)
                    return {"ok": True}

            with mock.patch.object(process_build_queue, "collect_queue_preflight_errors", return_value=[]), mock.patch.object(
                process_build_queue,
                "resolve_document_link_binding",
                return_value=binding,
            ), mock.patch.object(process_build_queue, "LarkCliSource", return_value=FakeSource()), mock.patch.object(
                process_build_queue,
                "build_document_for_task",
                return_value=process_build_queue.BuiltDocumentOutputs(
                    word_output_path=word_path,
                    upload_output_path=word_path,
                    md_output_path=md_path,
                ),
            ), mock.patch.object(
                process_build_queue,
                "resolve_artifact_destination",
                return_value=process_build_queue.WikiDestination(
                    space_id="space_123",
                    parent_wiki_token="wiki_parent",
                ),
            ), mock.patch.object(
                process_build_queue,
                "publish_word_artifact",
                return_value=process_build_queue.ArtifactPublishResult(
                    provider="lark_drive",
                    reference_id="file_token_123",
                    latest_link_url="https://test-degwga5x6ex8.feishu.cn/file/file_token_123",
                    document_link_url="https://test-degwga5x6ex8.feishu.cn/wiki/wiki_token_123",
                    status_notes=("published_artifact=docx",),
                ),
            ), mock.patch.object(
                process_build_queue,
                "import_markdown_to_cloud_doc",
                side_effect=RuntimeError("cloud import failed"),
            ), mock.patch.object(
                process_build_queue,
                "_phase2_identity",
                return_value="bot",
            ):
                exit_code = process_build_queue.process_build_queue(
                    cfg=cfg,
                    config_path=Path("configs/config.us.yaml"),
                    data_root="data/phase2",
                    dry_run=False,
                )

        self.assertEqual(1, exit_code)
        failure_payload = captured_upserts[-1]["record"]
        self.assertIsInstance(failure_payload, dict)
        self.assertIn("FAILED", failure_payload[process_build_queue.RESULT_FIELD])
        self.assertIn("cloud import failed", failure_payload[process_build_queue.RESULT_FIELD])
        self.assertEqual(
            "https://test-degwga5x6ex8.feishu.cn/file/file_token_123",
            failure_payload[process_build_queue.DOCUMENT_LINK_FIELD],
        )
        self.assertIn("latest_drive_link_preserved", failure_payload[process_build_queue.RESULT_FIELD])

    def test_process_build_queue_should_preserve_drive_link_when_wiki_move_fails(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "cli_bin": "lark-cli",
                    "base_token_env": "BASE_TOKEN",
                    "document_link": {
                        "table_id_env": "DOCUMENT_LINK_TABLE",
                        "view_id_env": "DOCUMENT_LINK_VIEW",
                    },
                }
            }
        }
        binding = process_build_queue.DocumentLinkBinding(
            base_token_env="BASE_TOKEN",
            table_id_env="DOCUMENT_LINK_TABLE",
            view_id_env="DOCUMENT_LINK_VIEW",
            wiki_parent_token_env=None,
            base_token="app_token",
            table_id="tbl_document_link",
            view_id="vew_document_link",
            wiki_parent_token=None,
        )
        raw_records = [
            {
                "record_id": "rec_jp",
                "fields": {
                    process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_JP_ja_1.0",
                    process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_JP",
                    process_build_queue.VERSION_FIELD: ["1.0"],
                    process_build_queue.LANG_FIELD: ["ja"],
                    process_build_queue.WORKFLOW_ACTION_FIELD: ["Publish"],
                    process_build_queue.DOC_PHASE_FIELD: ["Publish"],
                    process_build_queue.BUILD_STARTED_AT_FIELD: None,
                    process_build_queue.TRIGGER_FIELD: ["Y"],
                    process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    process_build_queue.FORCE_PHASE2_REFRESH_FIELD: False,
                    process_build_queue.DATA_SYNC_FIELD: "",
                },
            }
        ]
        captured_upserts: list[dict[str, object]] = []
        with tempfile.TemporaryDirectory() as td:
            generated_path = Path(td) / "docs" / "_build" / "JE-1000F" / "JP" / "word" / "manual_je1000f_jp.docx"
            build_document_mock = mock.Mock(return_value=generated_path)
            sync_mock = mock.Mock()

            class FakeSource:
                def fetch_records_with_ids(self, **_: object) -> list[dict[str, object]]:
                    return raw_records

                def upsert_record(self, **kwargs: object) -> dict[str, object]:
                    captured_upserts.append(kwargs)
                    return {"ok": True}

            with mock.patch.object(process_build_queue, "collect_queue_preflight_errors", return_value=[]), mock.patch.object(
                process_build_queue,
                "resolve_document_link_binding",
                return_value=binding,
            ), mock.patch.object(process_build_queue, "LarkCliSource", return_value=FakeSource()), mock.patch.object(
                process_build_queue,
                "sync_phase2_snapshot_before_queue",
                sync_mock,
            ), mock.patch.object(
                process_build_queue,
                "resolve_config_path_for_task",
                return_value=Path("configs/config.ja.yaml"),
            ), mock.patch.object(
                process_build_queue,
                "build_document_for_task",
                build_document_mock,
            ), mock.patch.object(
                process_build_queue,
                "upload_word_to_drive",
                return_value=("file_token_123", "https://test-degwga5x6ex8.feishu.cn/file/file_token_123"),
            ), mock.patch.object(
                process_build_queue,
                "resolve_wiki_destination",
                return_value=process_build_queue.WikiDestination(
                    space_id="space_123",
                    parent_wiki_token="wiki_parent",
                ),
            ), mock.patch.object(
                process_build_queue,
                "move_drive_file_to_wiki",
                side_effect=RuntimeError("permission | Permission denied [99991679]"),
            ), mock.patch.object(
                process_build_queue,
                "_phase2_identity",
                return_value="user",
            ):
                exit_code = process_build_queue.process_build_queue(
                    cfg=cfg,
                    config_path=Path("configs/config.ja.yaml"),
                    data_root="data/phase2",
                    dry_run=False,
                )

        self.assertEqual(0, exit_code)
        self.assertEqual(2, len(captured_upserts))
        success_payload = captured_upserts[1]["record"]
        self.assertIsInstance(success_payload, dict)
        self.assertEqual(
            generated_path.resolve(strict=False).as_posix(),
            success_payload[process_build_queue.DOCUMENT_DIRECTORY_FIELD],
        )
        self.assertEqual(
            "https://test-degwga5x6ex8.feishu.cn/file/file_token_123",
            success_payload[process_build_queue.DOCUMENT_LINK_FIELD],
        )
        self.assertEqual([process_build_queue.DONE_TRIGGER_VALUE], success_payload[process_build_queue.TRIGGER_FIELD])
        self.assertFalse(success_payload[process_build_queue.IMMEDIATE_TRIGGER_FIELD])
        self.assertFalse(success_payload[process_build_queue.FORCE_PHASE2_REFRESH_FIELD])
        self.assertEqual("skipped", success_payload[process_build_queue.DATA_SYNC_FIELD])
        self.assertIn("SUCCESS", success_payload[process_build_queue.RESULT_FIELD])
        self.assertIn("data_sync=skipped", success_payload[process_build_queue.RESULT_FIELD])
        self.assertIn("drive_only", success_payload[process_build_queue.RESULT_FIELD])
        self.assertIn("Permission denied [99991679]", success_payload[process_build_queue.RESULT_FIELD])
        sync_mock.assert_not_called()

    def test_process_build_queue_should_fail_and_write_back_when_draft_row_is_missing_git_ref(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "cli_bin": "lark-cli",
                    "base_token_env": "BASE_TOKEN",
                    "document_link": {
                        "table_id_env": "DOCUMENT_LINK_TABLE",
                        "view_id_env": "DOCUMENT_LINK_VIEW",
                    },
                }
            }
        }
        binding = process_build_queue.DocumentLinkBinding(
            base_token_env="BASE_TOKEN",
            table_id_env="DOCUMENT_LINK_TABLE",
            view_id_env="DOCUMENT_LINK_VIEW",
            wiki_parent_token_env=None,
            base_token="app_token",
            table_id="tbl_document_link",
            view_id="vew_document_link",
            wiki_parent_token=None,
        )
        raw_records = [
            {
                "record_id": "rec_missing_git_ref",
                "fields": {
                    process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_JP_ja_0.2",
                    process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_JP",
                    process_build_queue.VERSION_FIELD: ["0.2"],
                    process_build_queue.LANG_FIELD: ["ja"],
                    process_build_queue.BUILD_FAMILY_FIELD: ["jp-ja"],
                    process_build_queue.WORKFLOW_ACTION_FIELD: ["Build Draft Package"],
                    process_build_queue.BUILD_STARTED_AT_FIELD: None,
                    process_build_queue.TRIGGER_FIELD: ["Y"],
                    process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    process_build_queue.FORCE_PHASE2_REFRESH_FIELD: False,
                    process_build_queue.DATA_SYNC_FIELD: "",
                },
            }
        ]
        captured_upserts: list[dict[str, object]] = []
        sync_mock = mock.Mock()
        build_document_mock = mock.Mock()

        class FakeSource:
            def fetch_records_with_ids(self, **_: object) -> list[dict[str, object]]:
                return raw_records

            def upsert_record(self, **kwargs: object) -> dict[str, object]:
                captured_upserts.append(kwargs)
                return {"ok": True}

        with mock.patch.object(process_build_queue, "collect_queue_preflight_errors", return_value=[]), mock.patch.object(
            process_build_queue,
            "resolve_document_link_binding",
            return_value=binding,
        ), mock.patch.object(process_build_queue, "LarkCliSource", return_value=FakeSource()), mock.patch.object(
            process_build_queue,
            "sync_phase2_snapshot_before_queue",
            sync_mock,
        ), mock.patch.object(
            process_build_queue,
            "resolve_config_path_for_task",
            return_value=Path("configs/config.ja.yaml"),
        ), mock.patch.object(
            process_build_queue,
            "build_document_for_task",
            build_document_mock,
        ), mock.patch.object(
            process_build_queue,
            "resolve_wiki_destination",
            return_value=process_build_queue.WikiDestination(
                space_id="space_123",
                parent_wiki_token="wiki_parent",
            ),
        ), mock.patch.object(
            process_build_queue,
            "_phase2_identity",
            return_value="bot",
        ):
            exit_code = process_build_queue.process_build_queue(
                cfg=cfg,
                config_path=Path("config.yaml"),
                data_root="data/phase2",
                dry_run=False,
            )

        self.assertEqual(1, exit_code)
        sync_mock.assert_not_called()
        build_document_mock.assert_not_called()
        self.assertEqual(1, len(captured_upserts))
        failure_payload = captured_upserts[-1]["record"]
        self.assertIsInstance(failure_payload, dict)
        self.assertIn("Build Draft Package queue rows require Git_ref", failure_payload[process_build_queue.RESULT_FIELD])
        self.assertFalse(failure_payload[process_build_queue.IMMEDIATE_TRIGGER_FIELD])
        self.assertFalse(failure_payload[process_build_queue.FORCE_PHASE2_REFRESH_FIELD])
        self.assertEqual("skipped", failure_payload[process_build_queue.DATA_SYNC_FIELD])
        self.assertIn("data_sync=skipped", failure_payload[process_build_queue.RESULT_FIELD])
        sync_mock.assert_not_called()

    def test_process_build_queue_should_sync_phase2_snapshot_before_building_when_forced(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "cli_bin": "lark-cli",
                    "base_token_env": "BASE_TOKEN",
                    "document_link": {
                        "table_id_env": "DOCUMENT_LINK_TABLE",
                        "view_id_env": "DOCUMENT_LINK_VIEW",
                    },
                }
            }
        }
        binding = process_build_queue.DocumentLinkBinding(
            base_token_env="BASE_TOKEN",
            table_id_env="DOCUMENT_LINK_TABLE",
            view_id_env="DOCUMENT_LINK_VIEW",
            wiki_parent_token_env=None,
            base_token="app_token",
            table_id="tbl_document_link",
            view_id="vew_document_link",
            wiki_parent_token=None,
        )
        raw_records = [
            {
                "record_id": "rec_1",
                "fields": {
                    process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_en_1.0",
                    process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                    process_build_queue.VERSION_FIELD: ["1.0"],
                    process_build_queue.LANG_FIELD: ["en"],
                    process_build_queue.WORKFLOW_ACTION_FIELD: ["Build Draft Package"],
                    process_build_queue.DOC_PHASE_FIELD: ["Draft"],
                    process_build_queue.GIT_REF_FIELD: ["codex/review-je-1000f-us-en"],
                    process_build_queue.BUILD_STARTED_AT_FIELD: None,
                    process_build_queue.TRIGGER_FIELD: ["Y"],
                    process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    process_build_queue.FORCE_PHASE2_REFRESH_FIELD: True,
                    process_build_queue.DATA_SYNC_FIELD: "",
                },
            }
        ]
        fetch_calls: list[dict[str, object]] = []
        sync_mock = mock.Mock()
        build_document_mock = mock.Mock(return_value=Path(tempfile.gettempdir()) / "manual.docx")

        class FakeSource:
            def fetch_records_with_ids(self, **kwargs: object) -> list[dict[str, object]]:
                fetch_calls.append(kwargs)
                return raw_records

            def upsert_record(self, **_: object) -> dict[str, object]:
                return {"ok": True}

        with mock.patch.object(process_build_queue, "collect_queue_preflight_errors", return_value=[]), mock.patch.object(
            process_build_queue,
            "resolve_document_link_binding",
            return_value=binding,
        ), mock.patch.object(process_build_queue, "LarkCliSource", return_value=FakeSource()), mock.patch.object(
            process_build_queue,
            "sync_phase2_snapshot_before_queue",
            sync_mock,
        ), mock.patch.object(
            process_build_queue,
            "resolve_config_path_for_task",
            return_value=Path("configs/config.us-en.yaml"),
        ), mock.patch.object(
            process_build_queue,
            "build_document_for_task",
            build_document_mock,
        ), mock.patch.object(
            process_build_queue,
            "upload_word_to_drive",
            return_value=("file_token_123", "https://test-degwga5x6ex8.feishu.cn/file/file_token_123"),
        ), mock.patch.object(
            process_build_queue,
            "resolve_wiki_destination",
            return_value=process_build_queue.WikiDestination(
                space_id="space_123",
                parent_wiki_token="wiki_parent",
            ),
        ), mock.patch.object(
            process_build_queue,
            "move_drive_file_to_wiki",
            return_value="https://test-degwga5x6ex8.feishu.cn/wiki/wiki_token_123",
        ), mock.patch.object(
            process_build_queue,
            "_phase2_identity",
            return_value="user",
        ):
            exit_code = process_build_queue.process_build_queue(
                cfg=cfg,
                config_path=Path("config.yaml"),
                data_root="data/phase2",
                dry_run=False,
            )

        self.assertEqual(0, exit_code)
        sync_mock.assert_called_once_with(
            config_path=Path("config.yaml"),
            data_root="data/phase2",
        )
        self.assertEqual(1, len(fetch_calls))
        build_document_mock.assert_called_once()
        self.assertEqual("1.0", build_document_mock.call_args.kwargs["version"])
        self.assertEqual("codex/review-je-1000f-us-en", build_document_mock.call_args.kwargs["git_ref"])

    def test_process_build_queue_should_write_failed_data_sync_when_forced_refresh_fails(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "cli_bin": "lark-cli",
                    "base_token_env": "BASE_TOKEN",
                    "document_link": {
                        "table_id_env": "DOCUMENT_LINK_TABLE",
                        "view_id_env": "DOCUMENT_LINK_VIEW",
                    },
                }
            }
        }
        binding = process_build_queue.DocumentLinkBinding(
            base_token_env="BASE_TOKEN",
            table_id_env="DOCUMENT_LINK_TABLE",
            view_id_env="DOCUMENT_LINK_VIEW",
            wiki_parent_token_env=None,
            base_token="app_token",
            table_id="tbl_document_link",
            view_id="vew_document_link",
            wiki_parent_token=None,
        )
        raw_records = [
            {
                "record_id": "rec_force_sync_fail",
                "fields": {
                    process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_en_1.0",
                    process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                    process_build_queue.VERSION_FIELD: ["1.0"],
                    process_build_queue.LANG_FIELD: ["en"],
                    process_build_queue.WORKFLOW_ACTION_FIELD: ["Build Draft Package"],
                    process_build_queue.DOC_PHASE_FIELD: ["Draft"],
                    process_build_queue.GIT_REF_FIELD: ["codex/review-je-1000f-us-en"],
                    process_build_queue.BUILD_STARTED_AT_FIELD: None,
                    process_build_queue.TRIGGER_FIELD: ["Y"],
                    process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    process_build_queue.FORCE_PHASE2_REFRESH_FIELD: True,
                    process_build_queue.DATA_SYNC_FIELD: "",
                },
            }
        ]
        captured_upserts: list[dict[str, object]] = []
        sync_mock = mock.Mock(side_effect=RuntimeError("sync boom"))

        class FakeSource:
            def fetch_records_with_ids(self, **_: object) -> list[dict[str, object]]:
                return raw_records

            def upsert_record(self, **kwargs: object) -> dict[str, object]:
                captured_upserts.append(kwargs)
                return {"ok": True}

        with mock.patch.object(process_build_queue, "collect_queue_preflight_errors", return_value=[]), mock.patch.object(
            process_build_queue,
            "resolve_document_link_binding",
            return_value=binding,
        ), mock.patch.object(process_build_queue, "LarkCliSource", return_value=FakeSource()), mock.patch.object(
            process_build_queue,
            "sync_phase2_snapshot_before_queue",
            sync_mock,
        ), mock.patch.object(
            process_build_queue,
            "resolve_wiki_destination",
            return_value=process_build_queue.WikiDestination(
                space_id="space_123",
                parent_wiki_token="wiki_parent",
            ),
        ), mock.patch.object(
            process_build_queue,
            "_phase2_identity",
            return_value="user",
        ):
            exit_code = process_build_queue.process_build_queue(
                cfg=cfg,
                config_path=Path("config.yaml"),
                data_root="data/phase2",
                dry_run=False,
            )

        self.assertEqual(1, exit_code)
        sync_mock.assert_called_once_with(
            config_path=Path("config.yaml"),
            data_root="data/phase2",
        )
        self.assertEqual(1, len(captured_upserts))
        failure_payload = captured_upserts[0]["record"]
        self.assertEqual("failed", failure_payload[process_build_queue.DATA_SYNC_FIELD])
        self.assertFalse(failure_payload[process_build_queue.FORCE_PHASE2_REFRESH_FIELD])
        self.assertIn("data_sync=failed", failure_payload[process_build_queue.RESULT_FIELD])
        self.assertIn("sync boom", failure_payload[process_build_queue.RESULT_FIELD])

    def test_process_build_queue_should_build_once_per_document_key_group_and_write_back_all_rows(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "cli_bin": "lark-cli",
                    "base_token_env": "BASE_TOKEN",
                    "document_link": {
                        "table_id_env": "DOCUMENT_LINK_TABLE",
                        "view_id_env": "DOCUMENT_LINK_VIEW",
                    },
                }
            }
        }
        binding = process_build_queue.DocumentLinkBinding(
            base_token_env="BASE_TOKEN",
            table_id_env="DOCUMENT_LINK_TABLE",
            view_id_env="DOCUMENT_LINK_VIEW",
            wiki_parent_token_env=None,
            base_token="app_token",
            table_id="tbl_document_link",
            view_id="vew_document_link",
            wiki_parent_token=None,
        )
        raw_records = [
            {
                "record_id": "rec_group_1",
                "fields": {
                    process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_1.0",
                    process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                    process_build_queue.VERSION_FIELD: ["1.0"],
                    process_build_queue.LANG_FIELD: [""],
                    process_build_queue.BUILD_FAMILY_FIELD: ["us-merged"],
                    process_build_queue.WORKFLOW_ACTION_FIELD: ["Build Draft Package"],
                    process_build_queue.DOC_PHASE_FIELD: ["Draft"],
                    process_build_queue.GIT_REF_FIELD: ["codex/review-je-1000f-us"],
                    process_build_queue.BUILD_STARTED_AT_FIELD: None,
                    process_build_queue.TRIGGER_FIELD: ["Y"],
                    process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                },
            },
            {
                "record_id": "rec_group_2",
                "fields": {
                    process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_1.0",
                    process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                    process_build_queue.VERSION_FIELD: ["1.0"],
                    process_build_queue.LANG_FIELD: [""],
                    process_build_queue.BUILD_FAMILY_FIELD: ["us-merged"],
                    process_build_queue.WORKFLOW_ACTION_FIELD: ["Build Draft Package"],
                    process_build_queue.DOC_PHASE_FIELD: ["Draft"],
                    process_build_queue.GIT_REF_FIELD: ["codex/review-je-1000f-us"],
                    process_build_queue.BUILD_STARTED_AT_FIELD: None,
                    process_build_queue.TRIGGER_FIELD: ["Y"],
                    process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                },
            },
        ]
        captured_upserts: list[dict[str, object]] = []
        with tempfile.TemporaryDirectory() as td:
            generated_path = Path(td) / "docs" / "_build" / "JE-1000F" / "US" / "word" / "manual_je1000f_us.docx"
            build_document_mock = mock.Mock(return_value=generated_path)

            class FakeSource:
                def fetch_records_with_ids(self, **_: object) -> list[dict[str, object]]:
                    return raw_records

                def upsert_record(self, **kwargs: object) -> dict[str, object]:
                    captured_upserts.append(kwargs)
                    return {"ok": True}

            with mock.patch.object(process_build_queue, "collect_queue_preflight_errors", return_value=[]), mock.patch.object(
                process_build_queue,
                "resolve_document_link_binding",
                return_value=binding,
            ), mock.patch.object(process_build_queue, "LarkCliSource", return_value=FakeSource()), mock.patch.object(
                process_build_queue,
                "sync_phase2_snapshot_before_queue",
            ), mock.patch.object(
                process_build_queue,
                "build_document_for_task",
                build_document_mock,
            ), mock.patch.object(
                process_build_queue,
                "upload_word_to_drive",
                return_value=("file_token_123", "https://test-degwga5x6ex8.feishu.cn/file/file_token_123"),
            ), mock.patch.object(
                process_build_queue,
                "resolve_wiki_destination",
                return_value=process_build_queue.WikiDestination(
                    space_id="space_123",
                    parent_wiki_token="wiki_parent",
                ),
            ), mock.patch.object(
                process_build_queue,
                "move_drive_file_to_wiki",
                return_value="https://test-degwga5x6ex8.feishu.cn/wiki/wiki_token_123",
            ), mock.patch.object(
                process_build_queue,
                "_phase2_identity",
                return_value="bot",
            ):
                exit_code = process_build_queue.process_build_queue(
                    cfg=cfg,
                    config_path=Path("configs/config.us.yaml"),
                    data_root="data/phase2",
                    dry_run=False,
                )

        self.assertEqual(0, exit_code)
        self.assertEqual(4, len(captured_upserts))
        self.assertEqual(
            ["rec_group_1", "rec_group_2", "rec_group_1", "rec_group_2"],
            [entry["record_id"] for entry in captured_upserts],
        )
        build_document_mock.assert_called_once_with(
            config_path=(process_build_queue.ROOT / "configs/config.us.yaml"),
            model="JE-1000F",
            region="US",
            data_root="data/phase2",
            doc_phase="draft",
            lang="",
            version="1.0",
            git_ref="codex/review-je-1000f-us",
        )
        success_payload_1 = captured_upserts[2]["record"]
        success_payload_2 = captured_upserts[3]["record"]
        self.assertIsInstance(success_payload_1, dict)
        self.assertIsInstance(success_payload_2, dict)
        self.assertEqual(
            generated_path.resolve(strict=False).as_posix(),
            success_payload_1[process_build_queue.DOCUMENT_DIRECTORY_FIELD],
        )
        self.assertEqual(
            "https://test-degwga5x6ex8.feishu.cn/wiki/wiki_token_123",
            success_payload_1[process_build_queue.DOCUMENT_LINK_FIELD],
        )
        self.assertEqual(success_payload_1, success_payload_2)

    def test_publish_word_artifact_should_sync_dingtalk_mirror_without_replacing_feishu_link(self) -> None:
        cfg = {
            "queue": {
                "artifact_sink": {
                    "provider": "lark_drive",
                }
            }
        }
        wiki_destination = process_build_queue.WikiDestination(
            space_id="space_123",
            parent_wiki_token="wiki_parent",
        )
        dingtalk_mirror_destination = process_build_queue.ArtifactDestination(
            provider="dingtalk_alidocs_session",
            label="DingTalk docs target",
            details={"target_node_id": "MirrorNode123"},
            runtime_target="https://alidocs.dingtalk.com/i/nodes/MirrorNode123",
        )

        with tempfile.TemporaryDirectory() as td:
            word_output_path = Path(td) / "manual.docx"
            word_output_path.write_bytes(b"docx")

            with mock.patch.dict(
                process_build_queue.os.environ,
                {
                    "DINGTALK_DOCS_A_TOKEN": "token",
                    "DINGTALK_DOCS_XSRF_TOKEN": "xsrf",
                    "DINGTALK_DOCS_COOKIE": "cookie=value",
                },
                clear=False,
            ), mock.patch.object(
                process_build_queue,
                "upload_word_to_drive",
                return_value=("file_token_123", "https://test-degwga5x6ex8.feishu.cn/file/file_token_123"),
            ), mock.patch.object(
                process_build_queue,
                "move_drive_file_to_wiki",
                return_value="https://test-degwga5x6ex8.feishu.cn/wiki/wiki_token_123",
            ), mock.patch.object(
                process_build_queue,
                "load_session_config_for_operator_union_id",
                return_value=object(),
            ), mock.patch.object(
                process_build_queue,
                "upload_file_to_node",
                return_value=mock.Mock(
                    dentry_uuid="mirror_upload_123",
                    node_url="https://alidocs.dingtalk.com/i/nodes/MirrorUpload123",
                ),
            ):
                result = process_build_queue.publish_word_artifact(
                    cfg=cfg,
                    cli_bin="lark-cli",
                    word_output_path=word_output_path,
                    identity="user",
                    artifact_destination=wiki_destination,
                    dingtalk_mirror_destination=dingtalk_mirror_destination,
                )

        self.assertEqual("lark_drive", result.provider)
        self.assertEqual("file_token_123", result.reference_id)
        self.assertEqual(
            "https://test-degwga5x6ex8.feishu.cn/wiki/wiki_token_123",
            result.document_link_url,
        )
        self.assertEqual(
            "https://alidocs.dingtalk.com/i/nodes/MirrorUpload123",
            result.document_link_dd_url,
        )
        self.assertIn("dingtalk_sync=ok", result.status_notes)

    def test_publish_word_artifact_should_preserve_feishu_success_when_dingtalk_mirror_fails(self) -> None:
        cfg = {
            "queue": {
                "artifact_sink": {
                    "provider": "lark_drive",
                }
            }
        }
        wiki_destination = process_build_queue.WikiDestination(
            space_id="space_123",
            parent_wiki_token="wiki_parent",
        )
        dingtalk_mirror_destination = process_build_queue.ArtifactDestination(
            provider="dingtalk_alidocs_session",
            label="DingTalk docs target",
            details={"target_node_id": "MirrorNode123"},
            runtime_target="https://alidocs.dingtalk.com/i/nodes/MirrorNode123",
        )

        with tempfile.TemporaryDirectory() as td:
            word_output_path = Path(td) / "manual.docx"
            word_output_path.write_bytes(b"docx")

            with mock.patch.dict(
                process_build_queue.os.environ,
                {
                    "DINGTALK_DOCS_A_TOKEN": "token",
                    "DINGTALK_DOCS_XSRF_TOKEN": "xsrf",
                    "DINGTALK_DOCS_COOKIE": "cookie=value",
                },
                clear=False,
            ), mock.patch.object(
                process_build_queue,
                "upload_word_to_drive",
                return_value=("file_token_123", "https://test-degwga5x6ex8.feishu.cn/file/file_token_123"),
            ), mock.patch.object(
                process_build_queue,
                "move_drive_file_to_wiki",
                return_value="https://test-degwga5x6ex8.feishu.cn/wiki/wiki_token_123",
            ), mock.patch.object(
                process_build_queue,
                "load_session_config_for_operator_union_id",
                return_value=object(),
            ), mock.patch.object(
                process_build_queue,
                "upload_file_to_node",
                side_effect=RuntimeError("mirror upload failed"),
            ):
                result = process_build_queue.publish_word_artifact(
                    cfg=cfg,
                    cli_bin="lark-cli",
                    word_output_path=word_output_path,
                    identity="user",
                    artifact_destination=wiki_destination,
                    dingtalk_mirror_destination=dingtalk_mirror_destination,
                )

        self.assertEqual("lark_drive", result.provider)
        self.assertEqual(
            "https://test-degwga5x6ex8.feishu.cn/wiki/wiki_token_123",
            result.document_link_url,
        )
        self.assertEqual("", result.document_link_dd_url)
        self.assertIn("dingtalk_sync=failed", result.status_notes)
        self.assertIn("dingtalk_sync_error=mirror upload failed", result.status_notes)

    def test_process_build_queue_should_sync_dingtalk_mirror_and_keep_feishu_document_link(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "cli_bin": "lark-cli",
                    "base_token_env": "BASE_TOKEN",
                    "document_link": {
                        "table_id_env": "DOCUMENT_LINK_TABLE",
                        "view_id_env": "DOCUMENT_LINK_VIEW",
                    },
                }
            },
            "queue": {
                "artifact_sink": {
                    "provider": "lark_drive",
                    "mirror_provider": "dingtalk_alidocs_session",
                }
            },
        }
        binding = process_build_queue.DocumentLinkBinding(
            base_token_env="BASE_TOKEN",
            table_id_env="DOCUMENT_LINK_TABLE",
            view_id_env="DOCUMENT_LINK_VIEW",
            wiki_parent_token_env=None,
            base_token="app_token",
            table_id="tbl_document_link",
            view_id="vew_document_link",
            wiki_parent_token=None,
        )
        raw_records = [
            {
                "record_id": "rec_mirror_1",
                "fields": {
                    process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_en_1.0",
                    process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                    process_build_queue.VERSION_FIELD: ["1.0"],
                    process_build_queue.LANG_FIELD: ["en"],
                    process_build_queue.BUILD_FAMILY_FIELD: ["us-en"],
                    process_build_queue.WORKFLOW_ACTION_FIELD: ["Build Draft Package"],
                    process_build_queue.DOC_PHASE_FIELD: ["Draft"],
                    process_build_queue.GIT_REF_FIELD: ["codex/review-je-1000f-us-en"],
                    process_build_queue.BUILD_STARTED_AT_FIELD: None,
                    process_build_queue.TRIGGER_FIELD: ["Y"],
                    process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    process_build_queue.UPLOAD_DINGTALK_FIELD: True,
                    process_build_queue.DOCUMENT_LINK_DD_FIELD: "",
                },
            }
        ]
        captured_upserts: list[dict[str, object]] = []
        publish_calls: list[dict[str, object]] = []
        wiki_destination = process_build_queue.WikiDestination(
            space_id="space_123",
            parent_wiki_token="wiki_parent",
        )
        dingtalk_destination = process_build_queue.ArtifactDestination(
            provider="dingtalk_alidocs_session",
            label="DingTalk docs target",
            details={"target_node_id": "MirrorNode123"},
            runtime_target="https://alidocs.dingtalk.com/i/nodes/MirrorNode123",
        )

        with tempfile.TemporaryDirectory() as td:
            generated_path = Path(td) / "docs" / "_build" / "JE-1000F" / "US" / "word" / "manual_je1000f_us.docx"
            build_document_mock = mock.Mock(return_value=generated_path)

            class FakeSource:
                def fetch_records_with_ids(self, **_: object) -> list[dict[str, object]]:
                    return raw_records

                def upsert_record(self, **kwargs: object) -> dict[str, object]:
                    captured_upserts.append(kwargs)
                    return {"ok": True}

            def fake_publish_word_artifact(**kwargs: object) -> process_build_queue.ArtifactPublishResult:
                publish_calls.append(kwargs)
                self.assertEqual(wiki_destination, kwargs["artifact_destination"])
                self.assertEqual(dingtalk_destination, kwargs["dingtalk_mirror_destination"])
                return process_build_queue.ArtifactPublishResult(
                    provider="lark_drive",
                    reference_id="file_token_123",
                    latest_link_url="https://test-degwga5x6ex8.feishu.cn/file/file_token_123",
                    document_link_url="https://test-degwga5x6ex8.feishu.cn/wiki/wiki_token_123",
                    document_link_dd_url="https://alidocs.dingtalk.com/i/nodes/MirrorUpload123",
                    status_notes=("dingtalk_sync=ok",),
                )

            with mock.patch.object(process_build_queue, "collect_queue_preflight_errors", return_value=[]), mock.patch.object(
                process_build_queue,
                "resolve_document_link_binding",
                return_value=binding,
            ), mock.patch.object(process_build_queue, "LarkCliSource", return_value=FakeSource()), mock.patch.object(
                process_build_queue,
                "sync_phase2_snapshot_before_queue",
            ), mock.patch.object(
                process_build_queue,
                "build_document_for_task",
                build_document_mock,
            ), mock.patch.object(
                process_build_queue,
                "resolve_artifact_destination",
                return_value=wiki_destination,
            ), mock.patch.object(
                process_build_queue,
                "resolve_dingtalk_mirror_destination",
                return_value=dingtalk_destination,
            ), mock.patch.object(
                process_build_queue,
                "publish_word_artifact",
                side_effect=fake_publish_word_artifact,
            ), mock.patch.object(
                process_build_queue,
                "ensure_dingtalk_session_ready",
            ), mock.patch.object(
                process_build_queue,
                "_phase2_identity",
                return_value="user",
            ):
                exit_code = process_build_queue.process_build_queue(
                    cfg=cfg,
                    config_path=Path("configs/config.us.yaml"),
                    data_root="data/phase2",
                    dry_run=False,
                )

        self.assertEqual(0, exit_code)
        self.assertEqual(1, len(publish_calls))
        success_payload = captured_upserts[1]["record"]
        self.assertEqual(
            "https://test-degwga5x6ex8.feishu.cn/wiki/wiki_token_123",
            success_payload[process_build_queue.DOCUMENT_LINK_FIELD],
        )
        self.assertEqual(
            "https://alidocs.dingtalk.com/i/nodes/MirrorUpload123",
            success_payload[process_build_queue.DOCUMENT_LINK_DD_FIELD],
        )
        self.assertIn("dingtalk_sync=ok", success_payload[process_build_queue.RESULT_FIELD])

    def test_process_build_queue_should_continue_when_operator_session_is_missing_for_mirror(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "cli_bin": "lark-cli",
                    "base_token_env": "BASE_TOKEN",
                    "document_link": {
                        "table_id_env": "DOCUMENT_LINK_TABLE",
                        "view_id_env": "DOCUMENT_LINK_VIEW",
                    },
                }
            },
            "queue": {
                "artifact_sink": {
                    "provider": "lark_drive",
                    "mirror_provider": "dingtalk_alidocs_session",
                }
            },
        }
        binding = process_build_queue.DocumentLinkBinding(
            base_token_env="BASE_TOKEN",
            table_id_env="DOCUMENT_LINK_TABLE",
            view_id_env="DOCUMENT_LINK_VIEW",
            wiki_parent_token_env=None,
            base_token="app_token",
            table_id="tbl_document_link",
            view_id="vew_document_link",
            wiki_parent_token=None,
        )
        raw_records = [
            {
                "record_id": "rec_missing_session_1",
                "fields": {
                    process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_en_1.0",
                    process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                    process_build_queue.VERSION_FIELD: ["1.0"],
                    process_build_queue.LANG_FIELD: ["en"],
                    process_build_queue.BUILD_FAMILY_FIELD: ["us-en"],
                    process_build_queue.WORKFLOW_ACTION_FIELD: ["Build Draft Package"],
                    process_build_queue.DOC_PHASE_FIELD: ["Draft"],
                    process_build_queue.GIT_REF_FIELD: ["codex/review-je-1000f-us-en"],
                    process_build_queue.BUILD_STARTED_AT_FIELD: None,
                    process_build_queue.TRIGGER_FIELD: ["Y"],
                    process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    process_build_queue.UPLOAD_DINGTALK_FIELD: True,
                    process_build_queue.OPERATOR_UNION_ID_FIELD: "alice",
                    process_build_queue.DOCUMENT_LINK_DD_FIELD: "",
                },
            }
        ]
        captured_upserts: list[dict[str, object]] = []
        publish_calls: list[dict[str, object]] = []
        wiki_destination = process_build_queue.WikiDestination(
            space_id="space_123",
            parent_wiki_token="wiki_parent",
        )
        dingtalk_destination = process_build_queue.ArtifactDestination(
            provider="dingtalk_alidocs_session",
            label="DingTalk docs target",
            details={"target_node_id": "MirrorNode123"},
            runtime_target="https://alidocs.dingtalk.com/i/nodes/MirrorNode123",
        )

        with tempfile.TemporaryDirectory() as td:
            generated_path = Path(td) / "docs" / "_build" / "JE-1000F" / "US" / "word" / "manual_je1000f_us.docx"
            build_document_mock = mock.Mock(return_value=generated_path)

            class FakeSource:
                def fetch_records_with_ids(self, **_: object) -> list[dict[str, object]]:
                    return raw_records

                def upsert_record(self, **kwargs: object) -> dict[str, object]:
                    captured_upserts.append(kwargs)
                    return {"ok": True}

            def fake_publish_word_artifact(**kwargs: object) -> process_build_queue.ArtifactPublishResult:
                publish_calls.append(kwargs)
                self.assertEqual(wiki_destination, kwargs["artifact_destination"])
                self.assertIsNone(kwargs["dingtalk_mirror_destination"])
                return process_build_queue.ArtifactPublishResult(
                    provider="lark_drive",
                    reference_id="file_token_123",
                    latest_link_url="https://test-degwga5x6ex8.feishu.cn/file/file_token_123",
                    document_link_url="https://test-degwga5x6ex8.feishu.cn/wiki/wiki_token_123",
                )

            with mock.patch.object(process_build_queue, "collect_queue_preflight_errors", return_value=[]), mock.patch.object(
                process_build_queue,
                "resolve_document_link_binding",
                return_value=binding,
            ), mock.patch.object(process_build_queue, "LarkCliSource", return_value=FakeSource()), mock.patch.object(
                process_build_queue,
                "sync_phase2_snapshot_before_queue",
            ), mock.patch.object(
                process_build_queue,
                "build_document_for_task",
                build_document_mock,
            ), mock.patch.object(
                process_build_queue,
                "resolve_artifact_destination",
                return_value=wiki_destination,
            ), mock.patch.object(
                process_build_queue,
                "resolve_dingtalk_mirror_destination",
                return_value=dingtalk_destination,
            ), mock.patch.object(
                process_build_queue,
                "publish_word_artifact",
                side_effect=fake_publish_word_artifact,
            ), mock.patch.object(
                process_build_queue,
                "ensure_dingtalk_session_ready",
                side_effect=RuntimeError(
                    "No AliDocs session found for operator_union_id=alice. "
                    "Expected session file C:/Users/Administrator/.auto-manual/dingtalk-sessions/alice.json "
                    "or environment variables DINGTALK_DOCS_A_TOKEN, DINGTALK_DOCS_XSRF_TOKEN, DINGTALK_DOCS_COOKIE."
                ),
            ), mock.patch.object(
                process_build_queue,
                "_phase2_identity",
                return_value="user",
            ):
                exit_code = process_build_queue.process_build_queue(
                    cfg=cfg,
                    config_path=Path("configs/config.us.yaml"),
                    data_root="data/phase2",
                    dry_run=False,
                )

        self.assertEqual(0, exit_code)
        build_document_mock.assert_called_once()
        self.assertEqual(1, len(publish_calls))
        self.assertEqual(2, len(captured_upserts))
        success_payload = captured_upserts[1]["record"]
        self.assertEqual(
            "https://test-degwga5x6ex8.feishu.cn/wiki/wiki_token_123",
            success_payload[process_build_queue.DOCUMENT_LINK_FIELD],
        )
        self.assertIn("SUCCESS", success_payload[process_build_queue.RESULT_FIELD])
        self.assertIn("dingtalk_sync=failed", success_payload[process_build_queue.RESULT_FIELD])
        self.assertIn("operator_union_id=alice", success_payload[process_build_queue.RESULT_FIELD])
        self.assertFalse(success_payload[process_build_queue.IMMEDIATE_TRIGGER_FIELD])

    def test_process_build_queue_should_continue_when_mirror_target_is_invalid(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "cli_bin": "lark-cli",
                    "base_token_env": "BASE_TOKEN",
                    "document_link": {
                        "table_id_env": "DOCUMENT_LINK_TABLE",
                        "view_id_env": "DOCUMENT_LINK_VIEW",
                    },
                }
            },
            "queue": {
                "artifact_sink": {
                    "provider": "lark_drive",
                    "mirror_provider": "dingtalk_alidocs_session",
                }
            },
        }
        binding = process_build_queue.DocumentLinkBinding(
            base_token_env="BASE_TOKEN",
            table_id_env="DOCUMENT_LINK_TABLE",
            view_id_env="DOCUMENT_LINK_VIEW",
            wiki_parent_token_env=None,
            base_token="app_token",
            table_id="tbl_document_link",
            view_id="vew_document_link",
            wiki_parent_token=None,
        )
        raw_records = [
            {
                "record_id": "rec_invalid_target_1",
                "fields": {
                    process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_en_1.0",
                    process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                    process_build_queue.VERSION_FIELD: ["1.0"],
                    process_build_queue.LANG_FIELD: ["en"],
                    process_build_queue.BUILD_FAMILY_FIELD: ["us-en"],
                    process_build_queue.WORKFLOW_ACTION_FIELD: ["Build Draft Package"],
                    process_build_queue.DOC_PHASE_FIELD: ["Draft"],
                    process_build_queue.GIT_REF_FIELD: ["codex/review-je-1000f-us-en"],
                    process_build_queue.BUILD_STARTED_AT_FIELD: None,
                    process_build_queue.TRIGGER_FIELD: ["Y"],
                    process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    process_build_queue.UPLOAD_DINGTALK_FIELD: True,
                    process_build_queue.DOCUMENT_LINK_DD_FIELD: "",
                    process_build_queue.DINGTALK_TARGET_NODE_URL_FIELD: "-",
                },
            }
        ]
        captured_upserts: list[dict[str, object]] = []
        publish_calls: list[dict[str, object]] = []
        wiki_destination = process_build_queue.WikiDestination(
            space_id="space_123",
            parent_wiki_token="wiki_parent",
        )

        with tempfile.TemporaryDirectory() as td:
            generated_path = Path(td) / "docs" / "_build" / "JE-1000F" / "US" / "word" / "manual_je1000f_us.docx"
            build_document_mock = mock.Mock(return_value=generated_path)

            class FakeSource:
                def fetch_records_with_ids(self, **_: object) -> list[dict[str, object]]:
                    return raw_records

                def upsert_record(self, **kwargs: object) -> dict[str, object]:
                    captured_upserts.append(kwargs)
                    return {"ok": True}

            def fake_publish_word_artifact(**kwargs: object) -> process_build_queue.ArtifactPublishResult:
                publish_calls.append(kwargs)
                self.assertEqual(wiki_destination, kwargs["artifact_destination"])
                self.assertIsNone(kwargs["dingtalk_mirror_destination"])
                return process_build_queue.ArtifactPublishResult(
                    provider="lark_drive",
                    reference_id="file_token_123",
                    latest_link_url="https://test-degwga5x6ex8.feishu.cn/file/file_token_123",
                    document_link_url="https://test-degwga5x6ex8.feishu.cn/wiki/wiki_token_123",
                )

            with mock.patch.object(process_build_queue, "collect_queue_preflight_errors", return_value=[]), mock.patch.object(
                process_build_queue,
                "resolve_document_link_binding",
                return_value=binding,
            ), mock.patch.object(process_build_queue, "LarkCliSource", return_value=FakeSource()), mock.patch.object(
                process_build_queue,
                "sync_phase2_snapshot_before_queue",
            ), mock.patch.object(
                process_build_queue,
                "build_document_for_task",
                build_document_mock,
            ), mock.patch.object(
                process_build_queue,
                "resolve_artifact_destination",
                return_value=wiki_destination,
            ), mock.patch.object(
                process_build_queue,
                "resolve_dingtalk_mirror_destination",
                side_effect=RuntimeError("Invalid DingTalk workspace URL: -"),
            ), mock.patch.object(
                process_build_queue,
                "publish_word_artifact",
                side_effect=fake_publish_word_artifact,
            ), mock.patch.object(
                process_build_queue,
                "_phase2_identity",
                return_value="user",
            ):
                exit_code = process_build_queue.process_build_queue(
                    cfg=cfg,
                    config_path=Path("configs/config.us.yaml"),
                    data_root="data/phase2",
                    dry_run=False,
                )

        self.assertEqual(0, exit_code)
        build_document_mock.assert_called_once()
        self.assertEqual(1, len(publish_calls))
        success_payload = captured_upserts[1]["record"]
        self.assertIn("SUCCESS", success_payload[process_build_queue.RESULT_FIELD])
        self.assertIn("dingtalk_sync=failed", success_payload[process_build_queue.RESULT_FIELD])
        self.assertIn("Invalid DingTalk workspace URL: -", success_payload[process_build_queue.RESULT_FIELD])

    def test_process_build_queue_should_mark_dingtalk_sync_skipped_when_row_disables_mirror(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "cli_bin": "lark-cli",
                    "base_token_env": "BASE_TOKEN",
                    "document_link": {
                        "table_id_env": "DOCUMENT_LINK_TABLE",
                        "view_id_env": "DOCUMENT_LINK_VIEW",
                    },
                }
            },
            "queue": {
                "artifact_sink": {
                    "provider": "lark_drive",
                    "mirror_provider": "dingtalk_alidocs_session",
                }
            },
        }
        binding = process_build_queue.DocumentLinkBinding(
            base_token_env="BASE_TOKEN",
            table_id_env="DOCUMENT_LINK_TABLE",
            view_id_env="DOCUMENT_LINK_VIEW",
            wiki_parent_token_env=None,
            base_token="app_token",
            table_id="tbl_document_link",
            view_id="vew_document_link",
            wiki_parent_token=None,
        )
        raw_records = [
            {
                "record_id": "rec_mirror_off_1",
                "fields": {
                    process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_en_1.0",
                    process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                    process_build_queue.VERSION_FIELD: ["1.0"],
                    process_build_queue.LANG_FIELD: ["en"],
                    process_build_queue.BUILD_FAMILY_FIELD: ["us-en"],
                    process_build_queue.WORKFLOW_ACTION_FIELD: ["Build Draft Package"],
                    process_build_queue.DOC_PHASE_FIELD: ["Draft"],
                    process_build_queue.GIT_REF_FIELD: ["codex/review-je-1000f-us-en"],
                    process_build_queue.BUILD_STARTED_AT_FIELD: None,
                    process_build_queue.TRIGGER_FIELD: ["Y"],
                    process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    process_build_queue.UPLOAD_DINGTALK_FIELD: False,
                    process_build_queue.DOCUMENT_LINK_DD_FIELD: "https://alidocs.dingtalk.com/i/nodes/old-link",
                },
            }
        ]
        captured_upserts: list[dict[str, object]] = []
        publish_calls: list[dict[str, object]] = []
        wiki_destination = process_build_queue.WikiDestination(
            space_id="space_123",
            parent_wiki_token="wiki_parent",
        )

        with tempfile.TemporaryDirectory() as td:
            generated_path = Path(td) / "docs" / "_build" / "JE-1000F" / "US" / "word" / "manual_je1000f_us.docx"
            build_document_mock = mock.Mock(return_value=generated_path)

            class FakeSource:
                def fetch_records_with_ids(self, **_: object) -> list[dict[str, object]]:
                    return raw_records

                def upsert_record(self, **kwargs: object) -> dict[str, object]:
                    captured_upserts.append(kwargs)
                    return {"ok": True}

            def fake_publish_word_artifact(**kwargs: object) -> process_build_queue.ArtifactPublishResult:
                publish_calls.append(kwargs)
                self.assertEqual(wiki_destination, kwargs["artifact_destination"])
                self.assertIsNone(kwargs["dingtalk_mirror_destination"])
                return process_build_queue.ArtifactPublishResult(
                    provider="lark_drive",
                    reference_id="file_token_123",
                    latest_link_url="https://test-degwga5x6ex8.feishu.cn/file/file_token_123",
                    document_link_url="https://test-degwga5x6ex8.feishu.cn/wiki/wiki_token_123",
                )

            with mock.patch.object(process_build_queue, "collect_queue_preflight_errors", return_value=[]), mock.patch.object(
                process_build_queue,
                "resolve_document_link_binding",
                return_value=binding,
            ), mock.patch.object(process_build_queue, "LarkCliSource", return_value=FakeSource()), mock.patch.object(
                process_build_queue,
                "sync_phase2_snapshot_before_queue",
            ), mock.patch.object(
                process_build_queue,
                "build_document_for_task",
                build_document_mock,
            ), mock.patch.object(
                process_build_queue,
                "resolve_artifact_destination",
                return_value=wiki_destination,
            ), mock.patch.object(
                process_build_queue,
                "publish_word_artifact",
                side_effect=fake_publish_word_artifact,
            ), mock.patch.object(
                process_build_queue,
                "_phase2_identity",
                return_value="user",
            ):
                exit_code = process_build_queue.process_build_queue(
                    cfg=cfg,
                    config_path=Path("configs/config.us.yaml"),
                    data_root="data/phase2",
                    dry_run=False,
                )

        self.assertEqual(0, exit_code)
        self.assertEqual(1, len(publish_calls))
        success_payload = captured_upserts[1]["record"]
        self.assertEqual(
            "https://test-degwga5x6ex8.feishu.cn/wiki/wiki_token_123",
            success_payload[process_build_queue.DOCUMENT_LINK_FIELD],
        )
        self.assertEqual("", success_payload[process_build_queue.DOCUMENT_LINK_DD_FIELD])
        self.assertIn("dingtalk_sync=skipped", success_payload[process_build_queue.RESULT_FIELD])

    def test_process_build_queue_should_write_dingtalk_node_url_back_to_document_link_and_document_link_dd(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "cli_bin": "lark-cli",
                    "base_token_env": "BASE_TOKEN",
                    "document_link": {
                        "table_id_env": "DOCUMENT_LINK_TABLE",
                        "view_id_env": "DOCUMENT_LINK_VIEW",
                    },
                }
            },
            "queue": {
                "artifact_sink": {
                    "provider": "dingtalk_alidocs_session",
                }
            },
        }
        binding = process_build_queue.DocumentLinkBinding(
            base_token_env="BASE_TOKEN",
            table_id_env="DOCUMENT_LINK_TABLE",
            view_id_env="DOCUMENT_LINK_VIEW",
            wiki_parent_token_env=None,
            base_token="app_token",
            table_id="tbl_document_link",
            view_id="vew_document_link",
            wiki_parent_token=None,
        )
        raw_records = [
            {
                "record_id": "rec_dingtalk_1",
                "fields": {
                    process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_en_1.0",
                    process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                    process_build_queue.VERSION_FIELD: ["1.0"],
                    process_build_queue.LANG_FIELD: ["en"],
                    process_build_queue.BUILD_FAMILY_FIELD: ["us-en"],
                    process_build_queue.WORKFLOW_ACTION_FIELD: ["Build Draft Package"],
                    process_build_queue.DOC_PHASE_FIELD: ["Draft"],
                    process_build_queue.GIT_REF_FIELD: ["codex/review-je-1000f-us-en"],
                    process_build_queue.BUILD_STARTED_AT_FIELD: None,
                    process_build_queue.TRIGGER_FIELD: ["Y"],
                    process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    process_build_queue.UPLOAD_DINGTALK_FIELD: True,
                    process_build_queue.DOCUMENT_LINK_DD_FIELD: "",
                },
            }
        ]
        captured_upserts: list[dict[str, object]] = []
        with tempfile.TemporaryDirectory() as td:
            generated_path = Path(td) / "docs" / "_build" / "JE-1000F" / "US" / "word" / "manual_je1000f_us.docx"
            build_document_mock = mock.Mock(return_value=generated_path)

            class FakeSource:
                def fetch_records_with_ids(self, **_: object) -> list[dict[str, object]]:
                    return raw_records

                def upsert_record(self, **kwargs: object) -> dict[str, object]:
                    captured_upserts.append(kwargs)
                    return {"ok": True}

            with mock.patch.object(process_build_queue, "collect_queue_preflight_errors", return_value=[]), mock.patch.object(
                process_build_queue,
                "resolve_document_link_binding",
                return_value=binding,
            ), mock.patch.object(process_build_queue, "LarkCliSource", return_value=FakeSource()), mock.patch.object(
                process_build_queue,
                "sync_phase2_snapshot_before_queue",
            ), mock.patch.object(
                process_build_queue,
                "build_document_for_task",
                build_document_mock,
            ), mock.patch.object(
                process_build_queue,
                "resolve_artifact_destination",
                return_value=process_build_queue.ArtifactDestination(
                    provider="dingtalk_alidocs_session",
                    label="DingTalk docs target",
                    details={"target_node_id": "NkDwLng8ZLyr1dQ5Ha9gj6gBVKMEvZBY"},
                    runtime_target="https://alidocs.dingtalk.com/i/nodes/NkDwLng8ZLyr1dQ5Ha9gj6gBVKMEvZBY",
                ),
            ), mock.patch.object(
                process_build_queue,
                "publish_word_artifact",
                return_value=process_build_queue.ArtifactPublishResult(
                    provider="dingtalk_alidocs_session",
                    reference_id="Amq4vjg890BMY9ZRFQN6MoXmJ3kdP0wQ",
                    latest_link_url="https://alidocs.dingtalk.com/i/nodes/Amq4vjg890BMY9ZRFQN6MoXmJ3kdP0wQ",
                    document_link_url="https://alidocs.dingtalk.com/i/nodes/Amq4vjg890BMY9ZRFQN6MoXmJ3kdP0wQ",
                    document_link_dd_url="https://alidocs.dingtalk.com/i/nodes/Amq4vjg890BMY9ZRFQN6MoXmJ3kdP0wQ",
                ),
            ), mock.patch.object(
                process_build_queue,
                "ensure_dingtalk_session_ready",
            ), mock.patch.object(
                process_build_queue,
                "_phase2_identity",
                return_value="user",
            ):
                exit_code = process_build_queue.process_build_queue(
                    cfg=cfg,
                    config_path=Path("configs/config.us.yaml"),
                    data_root="data/phase2",
                    dry_run=False,
                )

        self.assertEqual(0, exit_code)
        self.assertEqual(2, len(captured_upserts))
        success_payload = captured_upserts[1]["record"]
        self.assertIsInstance(success_payload, dict)
        self.assertEqual(
            "https://alidocs.dingtalk.com/i/nodes/Amq4vjg890BMY9ZRFQN6MoXmJ3kdP0wQ",
            success_payload[process_build_queue.DOCUMENT_LINK_FIELD],
        )
        self.assertEqual(
            "https://alidocs.dingtalk.com/i/nodes/Amq4vjg890BMY9ZRFQN6MoXmJ3kdP0wQ",
            success_payload[process_build_queue.DOCUMENT_LINK_DD_FIELD],
        )
        self.assertEqual(
            generated_path.resolve(strict=False).as_posix(),
            success_payload[process_build_queue.DOCUMENT_DIRECTORY_FIELD],
        )
        self.assertIn("SUCCESS", success_payload[process_build_queue.RESULT_FIELD])
        self.assertFalse(success_payload[process_build_queue.IMMEDIATE_TRIGGER_FIELD])

    def test_process_build_queue_should_prefer_row_level_dingtalk_target_node_url_over_default(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "cli_bin": "lark-cli",
                    "base_token_env": "BASE_TOKEN",
                    "document_link": {
                        "table_id_env": "DOCUMENT_LINK_TABLE",
                        "view_id_env": "DOCUMENT_LINK_VIEW",
                    },
                }
            },
            "queue": {
                "artifact_sink": {
                    "provider": "dingtalk_alidocs_session",
                }
            },
        }
        binding = process_build_queue.DocumentLinkBinding(
            base_token_env="BASE_TOKEN",
            table_id_env="DOCUMENT_LINK_TABLE",
            view_id_env="DOCUMENT_LINK_VIEW",
            wiki_parent_token_env=None,
            base_token="app_token",
            table_id="tbl_document_link",
            view_id="vew_document_link",
            wiki_parent_token=None,
        )
        row_target = "https://alidocs.dingtalk.com/i/nodes/RowTargetNode123?utm_scene=team_space"
        raw_records = [
            {
                "record_id": "rec_dingtalk_row_target_1",
                "fields": {
                    process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_en_1.0",
                    process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                    process_build_queue.VERSION_FIELD: ["1.0"],
                    process_build_queue.LANG_FIELD: ["en"],
                    process_build_queue.BUILD_FAMILY_FIELD: ["us-en"],
                    process_build_queue.WORKFLOW_ACTION_FIELD: ["Build Draft Package"],
                    process_build_queue.DOC_PHASE_FIELD: ["Draft"],
                    process_build_queue.GIT_REF_FIELD: ["codex/review-je-1000f-us-en"],
                    process_build_queue.BUILD_STARTED_AT_FIELD: None,
                    process_build_queue.TRIGGER_FIELD: ["Y"],
                    process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    process_build_queue.UPLOAD_DINGTALK_FIELD: True,
                    process_build_queue.DOCUMENT_LINK_DD_FIELD: "",
                    process_build_queue.DINGTALK_TARGET_NODE_URL_FIELD: row_target,
                },
            }
        ]
        captured_upserts: list[dict[str, object]] = []
        publish_destinations: list[object] = []
        default_destination = process_build_queue.ArtifactDestination(
            provider="dingtalk_alidocs_session",
            label="DingTalk docs target",
            details={"target_node_id": "DefaultNode", "target_node_url": "https://alidocs.dingtalk.com/i/nodes/DefaultNode"},
            runtime_target="https://alidocs.dingtalk.com/i/nodes/DefaultNode",
        )

        with tempfile.TemporaryDirectory() as td:
            generated_path = Path(td) / "docs" / "_build" / "JE-1000F" / "US" / "word" / "manual_je1000f_us.docx"
            build_document_mock = mock.Mock(return_value=generated_path)

            class FakeSource:
                def fetch_records_with_ids(self, **_: object) -> list[dict[str, object]]:
                    return raw_records

                def upsert_record(self, **kwargs: object) -> dict[str, object]:
                    captured_upserts.append(kwargs)
                    return {"ok": True}

            def fake_resolve_artifact_destination(**kwargs: object) -> object:
                target_node_url = kwargs.get("target_node_url")
                if target_node_url:
                    return process_build_queue.ArtifactDestination(
                        provider="dingtalk_alidocs_session",
                        label="DingTalk docs target",
                        details={"target_node_id": "RowTargetNode123", "target_node_url": target_node_url},
                        runtime_target=target_node_url,
                    )
                return default_destination

            def fake_publish_word_artifact(**kwargs: object) -> process_build_queue.ArtifactPublishResult:
                publish_destinations.append(kwargs["artifact_destination"])
                self.assertEqual(row_target, kwargs["artifact_destination"].runtime_target)
                return process_build_queue.ArtifactPublishResult(
                    provider="dingtalk_alidocs_session",
                    reference_id="row_target_upload",
                    latest_link_url="https://alidocs.dingtalk.com/i/nodes/UploadedRowTargetNode",
                    document_link_url="https://alidocs.dingtalk.com/i/nodes/UploadedRowTargetNode",
                    document_link_dd_url="https://alidocs.dingtalk.com/i/nodes/UploadedRowTargetNode",
                )

            with mock.patch.object(process_build_queue, "collect_queue_preflight_errors", return_value=[]), mock.patch.object(
                process_build_queue,
                "resolve_document_link_binding",
                return_value=binding,
            ), mock.patch.object(process_build_queue, "LarkCliSource", return_value=FakeSource()), mock.patch.object(
                process_build_queue,
                "sync_phase2_snapshot_before_queue",
            ), mock.patch.object(
                process_build_queue,
                "build_document_for_task",
                build_document_mock,
            ), mock.patch.object(
                process_build_queue,
                "resolve_artifact_destination",
                side_effect=fake_resolve_artifact_destination,
            ), mock.patch.object(
                process_build_queue,
                "publish_word_artifact",
                side_effect=fake_publish_word_artifact,
            ), mock.patch.object(
                process_build_queue,
                "ensure_dingtalk_session_ready",
            ), mock.patch.object(
                process_build_queue,
                "_phase2_identity",
                return_value="user",
            ):
                exit_code = process_build_queue.process_build_queue(
                    cfg=cfg,
                    config_path=Path("configs/config.us.yaml"),
                    data_root="data/phase2",
                    dry_run=False,
                )

        self.assertEqual(0, exit_code)
        self.assertEqual(1, len(publish_destinations))
        success_payload = captured_upserts[1]["record"]
        self.assertEqual(
            "https://alidocs.dingtalk.com/i/nodes/UploadedRowTargetNode",
            success_payload[process_build_queue.DOCUMENT_LINK_DD_FIELD],
        )

    def test_process_build_queue_should_allow_row_level_dingtalk_target_without_default_target(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "cli_bin": "lark-cli",
                    "base_token_env": "BASE_TOKEN",
                    "document_link": {
                        "table_id_env": "DOCUMENT_LINK_TABLE",
                        "view_id_env": "DOCUMENT_LINK_VIEW",
                    },
                }
            },
            "queue": {
                "artifact_sink": {
                    "provider": "dingtalk_alidocs_session",
                }
            },
        }
        binding = process_build_queue.DocumentLinkBinding(
            base_token_env="BASE_TOKEN",
            table_id_env="DOCUMENT_LINK_TABLE",
            view_id_env="DOCUMENT_LINK_VIEW",
            wiki_parent_token_env=None,
            base_token="app_token",
            table_id="tbl_document_link",
            view_id="vew_document_link",
            wiki_parent_token=None,
        )
        row_target = "https://alidocs.dingtalk.com/i/nodes/RowOnlyTargetNode456?utm_scene=team_space"
        raw_records = [
            {
                "record_id": "rec_dingtalk_row_only_target_1",
                "fields": {
                    process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_en_1.0",
                    process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                    process_build_queue.VERSION_FIELD: ["1.0"],
                    process_build_queue.LANG_FIELD: ["en"],
                    process_build_queue.BUILD_FAMILY_FIELD: ["us-en"],
                    process_build_queue.WORKFLOW_ACTION_FIELD: ["Build Draft Package"],
                    process_build_queue.DOC_PHASE_FIELD: ["Draft"],
                    process_build_queue.GIT_REF_FIELD: ["codex/review-je-1000f-us-en"],
                    process_build_queue.BUILD_STARTED_AT_FIELD: None,
                    process_build_queue.TRIGGER_FIELD: ["Y"],
                    process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    process_build_queue.UPLOAD_DINGTALK_FIELD: True,
                    process_build_queue.DOCUMENT_LINK_DD_FIELD: "",
                    process_build_queue.DINGTALK_TARGET_NODE_URL_FIELD: row_target,
                },
            }
        ]
        captured_upserts: list[dict[str, object]] = []
        publish_destinations: list[object] = []
        placeholder_destination = process_build_queue.ArtifactDestination(
            provider="dingtalk_alidocs_session",
            label="DingTalk docs target",
            details={"target_node_id": "", "target_node_url": ""},
            runtime_target="",
        )

        with tempfile.TemporaryDirectory() as td:
            generated_path = Path(td) / "docs" / "_build" / "JE-1000F" / "US" / "word" / "manual_je1000f_us.docx"
            build_document_mock = mock.Mock(return_value=generated_path)

            class FakeSource:
                def fetch_records_with_ids(self, **_: object) -> list[dict[str, object]]:
                    return raw_records

                def upsert_record(self, **kwargs: object) -> dict[str, object]:
                    captured_upserts.append(kwargs)
                    return {"ok": True}

            def fake_resolve_artifact_destination(**kwargs: object) -> object:
                target_node_url = kwargs.get("target_node_url")
                if target_node_url:
                    return process_build_queue.ArtifactDestination(
                        provider="dingtalk_alidocs_session",
                        label="DingTalk docs target",
                        details={"target_node_id": "RowOnlyTargetNode456", "target_node_url": target_node_url},
                        runtime_target=target_node_url,
                    )
                return placeholder_destination

            def fake_publish_word_artifact(**kwargs: object) -> process_build_queue.ArtifactPublishResult:
                publish_destinations.append(kwargs["artifact_destination"])
                self.assertEqual(row_target, kwargs["artifact_destination"].runtime_target)
                return process_build_queue.ArtifactPublishResult(
                    provider="dingtalk_alidocs_session",
                    reference_id="row_only_target_upload",
                    latest_link_url="https://alidocs.dingtalk.com/i/nodes/UploadedRowOnlyTargetNode",
                    document_link_url="https://alidocs.dingtalk.com/i/nodes/UploadedRowOnlyTargetNode",
                    document_link_dd_url="https://alidocs.dingtalk.com/i/nodes/UploadedRowOnlyTargetNode",
                )

            with mock.patch.object(process_build_queue, "collect_queue_preflight_errors", return_value=[]), mock.patch.object(
                process_build_queue,
                "resolve_document_link_binding",
                return_value=binding,
            ), mock.patch.object(process_build_queue, "LarkCliSource", return_value=FakeSource()), mock.patch.object(
                process_build_queue,
                "sync_phase2_snapshot_before_queue",
            ), mock.patch.object(
                process_build_queue,
                "build_document_for_task",
                build_document_mock,
            ), mock.patch.object(
                process_build_queue,
                "resolve_artifact_destination",
                side_effect=fake_resolve_artifact_destination,
            ), mock.patch.object(
                process_build_queue,
                "publish_word_artifact",
                side_effect=fake_publish_word_artifact,
            ), mock.patch.object(
                process_build_queue,
                "ensure_dingtalk_session_ready",
            ), mock.patch.object(
                process_build_queue,
                "_phase2_identity",
                return_value="user",
            ):
                exit_code = process_build_queue.process_build_queue(
                    cfg=cfg,
                    config_path=Path("configs/config.us.yaml"),
                    data_root="data/phase2",
                    dry_run=False,
                )

        self.assertEqual(0, exit_code)
        self.assertEqual(1, len(publish_destinations))
        success_payload = captured_upserts[1]["record"]
        self.assertEqual(
            "https://alidocs.dingtalk.com/i/nodes/UploadedRowOnlyTargetNode",
            success_payload[process_build_queue.DOCUMENT_LINK_DD_FIELD],
        )

    def test_process_build_queue_should_accept_default_target_node_url_field_as_dingtalk_alias(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "cli_bin": "lark-cli",
                    "base_token_env": "BASE_TOKEN",
                    "document_link": {
                        "table_id_env": "DOCUMENT_LINK_TABLE",
                        "view_id_env": "DOCUMENT_LINK_VIEW",
                    },
                }
            },
            "queue": {
                "artifact_sink": {
                    "provider": "dingtalk_alidocs_session",
                }
            },
        }
        binding = process_build_queue.DocumentLinkBinding(
            base_token_env="BASE_TOKEN",
            table_id_env="DOCUMENT_LINK_TABLE",
            view_id_env="DOCUMENT_LINK_VIEW",
            wiki_parent_token_env=None,
            base_token="app_token",
            table_id="tbl_document_link",
            view_id="vew_document_link",
            wiki_parent_token=None,
        )
        row_target = "https://alidocs.dingtalk.com/i/nodes/DefaultTargetAlias123?utm_scene=team_space"
        raw_records = [
            {
                "record_id": "rec_dingtalk_default_alias_1",
                "fields": {
                    process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_en_1.0",
                    process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                    process_build_queue.VERSION_FIELD: ["1.0"],
                    process_build_queue.LANG_FIELD: ["en"],
                    process_build_queue.BUILD_FAMILY_FIELD: ["us-en"],
                    process_build_queue.WORKFLOW_ACTION_FIELD: ["Build Draft Package"],
                    process_build_queue.DOC_PHASE_FIELD: ["Draft"],
                    process_build_queue.GIT_REF_FIELD: ["codex/review-je-1000f-us-en"],
                    process_build_queue.BUILD_STARTED_AT_FIELD: None,
                    process_build_queue.TRIGGER_FIELD: ["Y"],
                    process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    process_build_queue.UPLOAD_DINGTALK_FIELD: True,
                    process_build_queue.DOCUMENT_LINK_DD_FIELD: "",
                    "default_target_node_url": row_target,
                },
            }
        ]
        captured_upserts: list[dict[str, object]] = []
        publish_destinations: list[object] = []
        placeholder_destination = process_build_queue.ArtifactDestination(
            provider="dingtalk_alidocs_session",
            label="DingTalk docs target",
            details={"target_node_id": "", "target_node_url": ""},
            runtime_target="",
        )

        with tempfile.TemporaryDirectory() as td:
            generated_path = Path(td) / "docs" / "_build" / "JE-1000F" / "US" / "word" / "manual_je1000f_us.docx"
            build_document_mock = mock.Mock(return_value=generated_path)

            class FakeSource:
                def fetch_records_with_ids(self, **_: object) -> list[dict[str, object]]:
                    return raw_records

                def upsert_record(self, **kwargs: object) -> dict[str, object]:
                    captured_upserts.append(kwargs)
                    return {"ok": True}

            def fake_resolve_artifact_destination(**kwargs: object) -> object:
                target_node_url = kwargs.get("target_node_url")
                if target_node_url:
                    return process_build_queue.ArtifactDestination(
                        provider="dingtalk_alidocs_session",
                        label="DingTalk docs target",
                        details={"target_node_id": "DefaultTargetAlias123", "target_node_url": target_node_url},
                        runtime_target=target_node_url,
                    )
                return placeholder_destination

            def fake_publish_word_artifact(**kwargs: object) -> process_build_queue.ArtifactPublishResult:
                publish_destinations.append(kwargs["artifact_destination"])
                self.assertEqual(row_target, kwargs["artifact_destination"].runtime_target)
                return process_build_queue.ArtifactPublishResult(
                    provider="dingtalk_alidocs_session",
                    reference_id="default_alias_upload",
                    latest_link_url="https://alidocs.dingtalk.com/i/nodes/UploadedDefaultAliasNode",
                    document_link_url="https://alidocs.dingtalk.com/i/nodes/UploadedDefaultAliasNode",
                    document_link_dd_url="https://alidocs.dingtalk.com/i/nodes/UploadedDefaultAliasNode",
                )

            with mock.patch.object(process_build_queue, "collect_queue_preflight_errors", return_value=[]), mock.patch.object(
                process_build_queue,
                "resolve_document_link_binding",
                return_value=binding,
            ), mock.patch.object(process_build_queue, "LarkCliSource", return_value=FakeSource()), mock.patch.object(
                process_build_queue,
                "sync_phase2_snapshot_before_queue",
            ), mock.patch.object(
                process_build_queue,
                "build_document_for_task",
                build_document_mock,
            ), mock.patch.object(
                process_build_queue,
                "resolve_artifact_destination",
                side_effect=fake_resolve_artifact_destination,
            ), mock.patch.object(
                process_build_queue,
                "publish_word_artifact",
                side_effect=fake_publish_word_artifact,
            ), mock.patch.object(
                process_build_queue,
                "ensure_dingtalk_session_ready",
            ), mock.patch.object(
                process_build_queue,
                "_phase2_identity",
                return_value="user",
            ):
                exit_code = process_build_queue.process_build_queue(
                    cfg=cfg,
                    config_path=Path("configs/config.us.yaml"),
                    data_root="data/phase2",
                    dry_run=False,
                )

        self.assertEqual(0, exit_code)
        self.assertEqual(1, len(publish_destinations))
        success_payload = captured_upserts[1]["record"]
        self.assertEqual(
            "https://alidocs.dingtalk.com/i/nodes/UploadedDefaultAliasNode",
            success_payload[process_build_queue.DOCUMENT_LINK_DD_FIELD],
        )

    def test_process_build_queue_should_fallback_to_feishu_when_dingtalk_upload_is_not_checked(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "cli_bin": "lark-cli",
                    "base_token_env": "BASE_TOKEN",
                    "document_link": {
                        "table_id_env": "DOCUMENT_LINK_TABLE",
                        "view_id_env": "DOCUMENT_LINK_VIEW",
                    },
                }
            },
            "queue": {
                "artifact_sink": {
                    "provider": "dingtalk_alidocs_session",
                }
            },
        }
        binding = process_build_queue.DocumentLinkBinding(
            base_token_env="BASE_TOKEN",
            table_id_env="DOCUMENT_LINK_TABLE",
            view_id_env="DOCUMENT_LINK_VIEW",
            wiki_parent_token_env=None,
            base_token="app_token",
            table_id="tbl_document_link",
            view_id="vew_document_link",
            wiki_parent_token=None,
        )
        raw_records = [
            {
                "record_id": "rec_dingtalk_off_1",
                "fields": {
                    process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_en_1.0",
                    process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                    process_build_queue.VERSION_FIELD: ["1.0"],
                    process_build_queue.LANG_FIELD: ["en"],
                    process_build_queue.BUILD_FAMILY_FIELD: ["us-en"],
                    process_build_queue.WORKFLOW_ACTION_FIELD: ["Build Draft Package"],
                    process_build_queue.DOC_PHASE_FIELD: ["Draft"],
                    process_build_queue.GIT_REF_FIELD: ["codex/review-je-1000f-us-en"],
                    process_build_queue.BUILD_STARTED_AT_FIELD: None,
                    process_build_queue.TRIGGER_FIELD: ["Y"],
                    process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    process_build_queue.DOCUMENT_LINK_DD_FIELD: "https://alidocs.dingtalk.com/i/nodes/old-link",
                    process_build_queue.UPLOAD_DINGTALK_FIELD: False,
                    process_build_queue.DINGTALK_TARGET_NODE_URL_FIELD: "https://alidocs.dingtalk.com/i/nodes/ignored-row-target",
                },
            }
        ]
        captured_upserts: list[dict[str, object]] = []
        publish_destinations: list[object] = []
        dingtalk_destination = process_build_queue.ArtifactDestination(
            provider="dingtalk_alidocs_session",
            label="DingTalk docs target",
            details={"target_node_id": "NkDwLng8ZLyr1dQ5Ha9gj6gBVKMEvZBY"},
            runtime_target="https://alidocs.dingtalk.com/i/nodes/NkDwLng8ZLyr1dQ5Ha9gj6gBVKMEvZBY",
        )
        wiki_destination = process_build_queue.WikiDestination(
            space_id="space_123",
            parent_wiki_token="wiki_parent",
        )

        with tempfile.TemporaryDirectory() as td:
            generated_path = Path(td) / "docs" / "_build" / "JE-1000F" / "US" / "word" / "manual_je1000f_us.docx"
            build_document_mock = mock.Mock(return_value=generated_path)

            class FakeSource:
                def fetch_records_with_ids(self, **_: object) -> list[dict[str, object]]:
                    return raw_records

                def upsert_record(self, **kwargs: object) -> dict[str, object]:
                    captured_upserts.append(kwargs)
                    return {"ok": True}

            def fake_publish_word_artifact(**kwargs: object) -> process_build_queue.ArtifactPublishResult:
                publish_destinations.append(kwargs["artifact_destination"])
                self.assertEqual(wiki_destination, kwargs["artifact_destination"])
                return process_build_queue.ArtifactPublishResult(
                    provider="lark_drive",
                    reference_id="file_token_123",
                    latest_link_url="https://test-degwga5x6ex8.feishu.cn/file/file_token_123",
                    document_link_url="https://test-degwga5x6ex8.feishu.cn/wiki/wiki_token_123",
                )

            with mock.patch.object(process_build_queue, "collect_queue_preflight_errors", return_value=[]), mock.patch.object(
                process_build_queue,
                "resolve_document_link_binding",
                return_value=binding,
            ), mock.patch.object(process_build_queue, "LarkCliSource", return_value=FakeSource()), mock.patch.object(
                process_build_queue,
                "sync_phase2_snapshot_before_queue",
            ), mock.patch.object(
                process_build_queue,
                "build_document_for_task",
                build_document_mock,
            ), mock.patch.object(
                process_build_queue,
                "resolve_artifact_destination",
                return_value=dingtalk_destination,
            ), mock.patch.object(
                process_build_queue,
                "resolve_wiki_destination",
                return_value=wiki_destination,
            ), mock.patch.object(
                process_build_queue,
                "publish_word_artifact",
                side_effect=fake_publish_word_artifact,
            ), mock.patch.object(
                process_build_queue,
                "_phase2_identity",
                return_value="user",
            ):
                exit_code = process_build_queue.process_build_queue(
                    cfg=cfg,
                    config_path=Path("configs/config.us.yaml"),
                    data_root="data/phase2",
                    dry_run=False,
                )

        self.assertEqual(0, exit_code)
        self.assertEqual(1, len(publish_destinations))
        self.assertEqual(2, len(captured_upserts))
        success_payload = captured_upserts[1]["record"]
        self.assertIsInstance(success_payload, dict)
        self.assertEqual(
            "https://test-degwga5x6ex8.feishu.cn/wiki/wiki_token_123",
            success_payload[process_build_queue.DOCUMENT_LINK_FIELD],
        )
        self.assertEqual("", success_payload[process_build_queue.DOCUMENT_LINK_DD_FIELD])

    def test_build_success_fields_should_optionally_write_dingtalk_link(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            word_path = Path(td) / "docs" / "_build" / "JE-1000F" / "US" / "word" / "manual_je1000f_us.docx"
            built_at = datetime(2026, 4, 1, 12, 34, 56)
            dingtalk_url = "https://alidocs.dingtalk.com/i/nodes/Amq4vjg890BMY9ZRFQN6MoXmJ3kdP0wQ"

            fields = process_build_queue.build_success_fields(
                version="1.0",
                word_output_path=word_path,
                document_link_url=dingtalk_url,
                document_link_dd_url=dingtalk_url,
                built_at=built_at,
                workflow_action="Build Draft Package",
                doc_phase="Draft",
                data_sync_status="skipped",
                write_document_link_dd=True,
            )

        self.assertEqual(dingtalk_url, fields[process_build_queue.DOCUMENT_LINK_FIELD])
        self.assertEqual(dingtalk_url, fields[process_build_queue.DOCUMENT_LINK_DD_FIELD])


if __name__ == "__main__":
    unittest.main()
