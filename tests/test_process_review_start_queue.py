from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import process_review_start_queue


class TestProcessReviewStartQueue(unittest.TestCase):
    def test_resolve_docs_dir_for_config_should_follow_worktree_relative_path(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            worktree = Path(td) / "review-start-worktree"
            config_path = worktree / "config.us-en.yaml"
            cfg = {"paths": {"docs_dir": "docs"}}

            docs_dir = process_review_start_queue._resolve_docs_dir_for_config(config_path, cfg)

        self.assertEqual(worktree / "docs", docs_dir)

    def test_parse_review_start_records_should_parse_build_family(self) -> None:
        records = process_review_start_queue.parse_review_start_records(
            [
                {
                    "record_id": "rec_merged",
                    "fields": {
                        process_review_start_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_0.1",
                        process_review_start_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                        process_review_start_queue.BUILD_FAMILY_FIELD: ["US-MERGED"],
                        process_review_start_queue.LANG_FIELD: ["en"],
                        process_review_start_queue.VERSION_FIELD: ["0.1"],
                        process_review_start_queue.REVIEW_STATUS_FIELD: [process_review_start_queue.REVIEW_STATUS_NOT_STARTED],
                        process_review_start_queue.REVIEW_TRIGGER_FIELD: True,
                    },
                }
            ]
        )

        self.assertEqual("us-merged", records[0].build_family)

    def test_select_pending_review_start_records_should_require_checkbox_and_notstarted_status(self) -> None:
        records = process_review_start_queue.select_pending_review_start_records(
            [
                {
                    "record_id": "rec_pending",
                    "fields": {
                        process_review_start_queue.DOCUMENT_ID_FIELD: "JE-1000F_JP_ja_0.1",
                        process_review_start_queue.DOCUMENT_KEY_FIELD: "JE-1000F_JP",
                        process_review_start_queue.BUILD_FAMILY_FIELD: ["jp-ja"],
                        process_review_start_queue.LANG_FIELD: ["ja"],
                        process_review_start_queue.VERSION_FIELD: ["0.1"],
                        process_review_start_queue.REVIEW_STATUS_FIELD: [process_review_start_queue.REVIEW_STATUS_NOT_STARTED],
                        process_review_start_queue.REVIEW_TRIGGER_FIELD: True,
                    },
                },
                {
                    "record_id": "rec_started",
                    "fields": {
                        process_review_start_queue.DOCUMENT_ID_FIELD: "JE-1000F_JP_ja_0.1",
                        process_review_start_queue.DOCUMENT_KEY_FIELD: "JE-1000F_JP",
                        process_review_start_queue.BUILD_FAMILY_FIELD: ["jp-ja"],
                        process_review_start_queue.LANG_FIELD: ["ja"],
                        process_review_start_queue.VERSION_FIELD: ["0.1"],
                        process_review_start_queue.REVIEW_STATUS_FIELD: [process_review_start_queue.REVIEW_STATUS_IN_REVIEW],
                        process_review_start_queue.REVIEW_TRIGGER_FIELD: True,
                    },
                },
            ]
        )

        self.assertEqual(["rec_pending"], [record.record_id for record in records])

    def test_generate_review_branch_name_should_default_to_codex_prefix(self) -> None:
        record = process_review_start_queue.ReviewStartRecord(
            record_id="rec_1",
            document_id="JE-1000F_JP_ja_0.1",
            document_key="JE-1000F_JP",
            build_family="jp-ja",
            version="0.1",
            lang="ja",
            review_status="NotStarted",
            review_trigger_value=True,
            git_ref="",
            pr_url="",
        )

        branch_name = process_review_start_queue.generate_review_branch_name(record)

        self.assertTrue(branch_name.startswith("codex/review-"))
        self.assertIn("je-1000f-jp", branch_name)

    def test_group_review_start_records_should_collapse_same_document_key_for_merged_family(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "config.us.yaml").write_text("build: {}\n", encoding="utf-8")
            cfgs = {
                "config.us.yaml": {"build": {"queue_by_document_key": True}},
            }
            records = [
                process_review_start_queue.ReviewStartRecord(
                    record_id="rec_en",
                    document_id="JE-1000F_US_en_0.1",
                    document_key="JE-1000F_US",
                    build_family="us-merged",
                    version="0.1",
                    lang="",
                    review_status="NotStarted",
                    review_trigger_value=True,
                    git_ref="",
                    pr_url="",
                ),
                process_review_start_queue.ReviewStartRecord(
                    record_id="rec_fr",
                    document_id="JE-1000F_US_fr_0.1",
                    document_key="JE-1000F_US",
                    build_family="us-merged",
                    version="0.1",
                    lang="",
                    review_status="NotStarted",
                    review_trigger_value=True,
                    git_ref="",
                    pr_url="",
                ),
            ]

            with mock.patch.object(
                process_review_start_queue,
                "resolve_config_path_for_task",
                side_effect=lambda *, region, lang, build_family=None: root / "config.us.yaml",
            ), mock.patch.object(
                process_review_start_queue,
                "load_config",
                side_effect=lambda path: cfgs[path.name],
            ):
                grouped = process_review_start_queue.group_review_start_records(records)

        self.assertEqual(1, len(grouped))
        self.assertEqual(["rec_en", "rec_fr"], [record.record_id for record in grouped[0]])

    def test_group_review_start_records_should_not_collapse_same_document_key_for_single_language_family(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "config.us-en.yaml").write_text("build: {}\n", encoding="utf-8")
            cfgs = {
                "config.us-en.yaml": {"build": {"queue_by_document_key": False}},
            }
            records = [
                process_review_start_queue.ReviewStartRecord(
                    record_id="rec_en_1",
                    document_id="JE-1000F_US_en_0.1",
                    document_key="JE-1000F_US",
                    build_family="",
                    version="0.1",
                    lang="en",
                    review_status="NotStarted",
                    review_trigger_value=True,
                    git_ref="",
                    pr_url="",
                ),
                process_review_start_queue.ReviewStartRecord(
                    record_id="rec_en_2",
                    document_id="JE-1000F_US_en_0.1",
                    document_key="JE-1000F_US",
                    build_family="",
                    version="0.1",
                    lang="en",
                    review_status="NotStarted",
                    review_trigger_value=True,
                    git_ref="",
                    pr_url="",
                ),
            ]

            with mock.patch.object(
                process_review_start_queue,
                "resolve_config_path_for_task",
                side_effect=lambda *, region, lang, build_family=None: root / "config.us-en.yaml",
            ) as mock_resolve_config_path, mock.patch.object(
                process_review_start_queue,
                "load_config",
                side_effect=lambda path: cfgs[path.name],
            ):
                grouped = process_review_start_queue.group_review_start_records(records)

        self.assertEqual(2, len(grouped))
        self.assertEqual(["rec_en_1"], [record.record_id for record in grouped[0]])
        self.assertEqual(["rec_en_2"], [record.record_id for record in grouped[1]])
        self.assertEqual("", mock_resolve_config_path.call_args.kwargs["build_family"])

    def test_resolve_target_for_review_start_should_fallback_to_document_id(self) -> None:
        record = process_review_start_queue.ReviewStartRecord(
            record_id="rec_1",
            document_id="JE-1000F_JP_ja_0.1",
            document_key="{'id': 'recv_bad_link'}",
            build_family="jp-ja",
            version="0.1",
            lang="ja",
            review_status="NotStarted",
            review_trigger_value=True,
            git_ref="",
            pr_url="",
        )

        model, region = process_review_start_queue.resolve_target_for_review_start(record)

        self.assertEqual("JE-1000F", model)
        self.assertEqual("JP", region)

    def test_resolve_docs_dir_for_config_should_follow_worktree_relative_path(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            worktree = Path(td)
            config_path = worktree / "config.yaml"
            docs_dir = process_review_start_queue._resolve_docs_dir_for_config(
                config_path,
                {"paths": {"docs_dir": "docs"}},
            )

        self.assertEqual((worktree / "docs").resolve(), docs_dir)

    @mock.patch.dict(
        "os.environ",
        {
            "FEISHU_PHASE2_BASE_TOKEN": "app_xxx",
            "FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID": "tbl_document_link",
            "FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID": "vew_document_link",
        },
        clear=False,
    )
    def test_review_init_env_names_should_default_to_document_link_binding(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "base_token_env": "FEISHU_PHASE2_BASE_TOKEN",
                    "document_link": {
                        "table_id_env": "FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID",
                        "view_id_env": "FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID",
                    },
                }
            }
        }

        base_token_env, table_id_env, view_id_env = process_review_start_queue._review_init_env_names(cfg)

        self.assertEqual("FEISHU_PHASE2_BASE_TOKEN", base_token_env)
        self.assertEqual("FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID", table_id_env)
        self.assertEqual("FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID", view_id_env)

    def test_process_review_start_queue_should_write_back_git_ref_and_pr_url(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "cli_bin": "lark-cli",
                    "base_token_env": "FEISHU_PHASE2_BASE_TOKEN",
                    "document_link": {
                        "table_id_env": "FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID",
                        "view_id_env": "FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID",
                    },
                }
            }
        }
        raw_records = [
            {
                "record_id": "rec_init_1",
                "fields": {
                    process_review_start_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_en_0.1",
                    process_review_start_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                    process_review_start_queue.BUILD_FAMILY_FIELD: ["us-merged"],
                    process_review_start_queue.LANG_FIELD: [""],
                    process_review_start_queue.VERSION_FIELD: ["0.1"],
                    process_review_start_queue.REVIEW_STATUS_FIELD: [process_review_start_queue.REVIEW_STATUS_NOT_STARTED],
                    process_review_start_queue.REVIEW_TRIGGER_FIELD: True,
                    process_review_start_queue.GIT_REF_FIELD: "",
                    process_review_start_queue.PR_URL_FIELD: "",
                },
            },
            {
                "record_id": "rec_init_2",
                "fields": {
                    process_review_start_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_fr_0.1",
                    process_review_start_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                    process_review_start_queue.BUILD_FAMILY_FIELD: ["us-merged"],
                    process_review_start_queue.LANG_FIELD: [""],
                    process_review_start_queue.VERSION_FIELD: ["0.1"],
                    process_review_start_queue.REVIEW_STATUS_FIELD: [process_review_start_queue.REVIEW_STATUS_NOT_STARTED],
                    process_review_start_queue.REVIEW_TRIGGER_FIELD: True,
                    process_review_start_queue.GIT_REF_FIELD: "",
                    process_review_start_queue.PR_URL_FIELD: "",
                },
            },
        ]

        source = mock.Mock()
        source.fetch_records_with_ids.return_value = raw_records

        with tempfile.TemporaryDirectory() as td, \
            mock.patch.object(process_review_start_queue, "collect_review_start_preflight_errors", return_value=[]), \
            mock.patch.object(process_review_start_queue, "resolve_review_init_binding") as mock_binding, \
            mock.patch.object(process_review_start_queue, "_cli_bin", return_value="lark-cli"), \
            mock.patch.object(process_review_start_queue, "_phase2_identity", return_value="bot"), \
            mock.patch.object(process_review_start_queue, "LarkCliSource", return_value=source), \
            mock.patch.object(process_review_start_queue, "sync_phase2_snapshot_before_review_start"), \
            mock.patch.object(process_review_start_queue, "_run_git"), \
            mock.patch.object(process_review_start_queue, "load_config", return_value={"build": {"queue_by_document_key": True}}), \
            mock.patch.object(
                process_review_start_queue,
                "resolve_config_path_for_task",
                side_effect=lambda *, region, lang, build_family=None: Path(td) / ("config.us.yaml" if build_family == "us-merged" else "config.us-en.yaml"),
            ) as mock_resolve_config_path, \
            mock.patch.object(process_review_start_queue, "base_ref_contains_target_review_root", return_value=False), \
            mock.patch.object(
                process_review_start_queue,
                "start_review_for_record",
                return_value=("codex/review-je-1000f-us", "https://github.com/Bingboom/auto-manual/pull/999"),
            ) as mock_start_review:
            mock_binding.return_value = process_review_start_queue.ReviewInitBinding(
                base_token_env="FEISHU_PHASE2_BASE_TOKEN",
                table_id_env="FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID",
                view_id_env="FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID",
                base_token="app_xxx",
                table_id="tbl_init",
                view_id="vew_init",
            )
            exit_code = process_review_start_queue.process_review_start_queue(
                cfg=cfg,
                config_path=Path(td) / "config.yaml",
                data_root=str(Path(td) / ".tmp" / "review-start" / "phase2"),
                dry_run=False,
                record_id=None,
            )

        self.assertEqual(0, exit_code)
        self.assertEqual(2, source.upsert_record.call_count)
        observed_record_ids = [call.kwargs["record_id"] for call in source.upsert_record.call_args_list]
        self.assertEqual(["rec_init_1", "rec_init_2"], observed_record_ids)
        self.assertEqual("us-merged", mock_resolve_config_path.call_args.kwargs["build_family"])
        self.assertEqual(
            Path(td) / "config.us.yaml",
            mock_start_review.call_args.kwargs["build_config_path"],
        )
        for call in source.upsert_record.call_args_list:
            record_payload = call.kwargs["record"]
            self.assertEqual(["InReview"], record_payload[process_review_start_queue.REVIEW_STATUS_FIELD])
            self.assertEqual(
                "codex/review-je-1000f-us",
                record_payload[process_review_start_queue.GIT_REF_FIELD],
            )
            self.assertEqual(
                "https://github.com/Bingboom/auto-manual/pull/999",
                record_payload[process_review_start_queue.PR_URL_FIELD],
            )
            self.assertFalse(record_payload[process_review_start_queue.REVIEW_TRIGGER_FIELD])

    def test_process_review_start_queue_should_block_duplicate_review_root_and_write_initial_result(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "cli_bin": "lark-cli",
                    "base_token_env": "FEISHU_PHASE2_BASE_TOKEN",
                    "review_init": {
                        "table_id_env": "FEISHU_PHASE2_REVIEW_INIT_TABLE_ID",
                        "view_id_env": "FEISHU_PHASE2_REVIEW_INIT_VIEW_ID",
                    },
                }
            }
        }
        raw_records = [
            {
                "record_id": "rec_init_dup",
                "fields": {
                    process_review_start_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_en_0.1",
                    process_review_start_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                    process_review_start_queue.BUILD_FAMILY_FIELD: ["us-merged"],
                    process_review_start_queue.LANG_FIELD: ["en"],
                    process_review_start_queue.VERSION_FIELD: ["0.1"],
                    process_review_start_queue.REVIEW_STATUS_FIELD: [process_review_start_queue.REVIEW_STATUS_NOT_STARTED],
                    process_review_start_queue.REVIEW_TRIGGER_FIELD: True,
                },
            }
        ]

        source = mock.Mock()
        source.fetch_records_with_ids.return_value = raw_records

        with tempfile.TemporaryDirectory() as td, \
            mock.patch.object(process_review_start_queue, "collect_review_start_preflight_errors", return_value=[]), \
            mock.patch.object(process_review_start_queue, "resolve_review_init_binding") as mock_binding, \
            mock.patch.object(process_review_start_queue, "_cli_bin", return_value="lark-cli"), \
            mock.patch.object(process_review_start_queue, "_phase2_identity", return_value="bot"), \
            mock.patch.object(process_review_start_queue, "LarkCliSource", return_value=source), \
            mock.patch.object(process_review_start_queue, "sync_phase2_snapshot_before_review_start"), \
            mock.patch.object(process_review_start_queue, "_run_git"), \
            mock.patch.object(process_review_start_queue, "load_config", return_value={"build": {"queue_by_document_key": True}}), \
            mock.patch.object(
                process_review_start_queue,
                "resolve_config_path_for_task",
                return_value=Path(td) / "config.us.yaml",
            ), \
            mock.patch.object(process_review_start_queue, "base_ref_contains_target_review_root", return_value=True), \
            mock.patch.object(process_review_start_queue, "start_review_for_record") as mock_start_review:
            mock_binding.return_value = process_review_start_queue.ReviewInitBinding(
                base_token_env="FEISHU_PHASE2_BASE_TOKEN",
                table_id_env="FEISHU_PHASE2_REVIEW_INIT_TABLE_ID",
                view_id_env="FEISHU_PHASE2_REVIEW_INIT_VIEW_ID",
                base_token="app_xxx",
                table_id="tbl_init",
                view_id="vew_init",
            )
            exit_code = process_review_start_queue.process_review_start_queue(
                cfg=cfg,
                config_path=Path(td) / "config.yaml",
                data_root=str(Path(td) / ".tmp" / "review-start" / "phase2"),
                dry_run=False,
                record_id="rec_init_dup",
            )

        self.assertEqual(0, exit_code)
        mock_start_review.assert_not_called()
        source.upsert_record.assert_called_once()
        kwargs = source.upsert_record.call_args.kwargs
        self.assertEqual("rec_init_dup", kwargs["record_id"])
        self.assertEqual(
            process_review_start_queue.INITIAL_RESULT_DUPLICATE,
            kwargs["record"][process_review_start_queue.INITIAL_RESULT_FIELD],
        )
        self.assertEqual(
            process_review_start_queue.DUPLICATE_REMARKS,
            kwargs["record"][process_review_start_queue.REMARKS_FIELD],
        )
        self.assertFalse(kwargs["record"][process_review_start_queue.REVIEW_TRIGGER_FIELD])

    def test_process_review_start_queue_should_fail_on_conflicting_build_family_in_same_merged_group(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "cli_bin": "lark-cli",
                    "base_token_env": "FEISHU_PHASE2_BASE_TOKEN",
                    "review_init": {
                        "table_id_env": "FEISHU_PHASE2_REVIEW_INIT_TABLE_ID",
                        "view_id_env": "FEISHU_PHASE2_REVIEW_INIT_VIEW_ID",
                    },
                }
            }
        }
        raw_records = [
            {
                "record_id": "rec_init_1",
                "fields": {
                    process_review_start_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_en_0.1",
                    process_review_start_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                    process_review_start_queue.BUILD_FAMILY_FIELD: ["us-merged"],
                    process_review_start_queue.LANG_FIELD: [""],
                    process_review_start_queue.VERSION_FIELD: ["0.1"],
                    process_review_start_queue.REVIEW_STATUS_FIELD: [process_review_start_queue.REVIEW_STATUS_NOT_STARTED],
                    process_review_start_queue.REVIEW_TRIGGER_FIELD: True,
                    process_review_start_queue.GIT_REF_FIELD: "",
                    process_review_start_queue.PR_URL_FIELD: "",
                },
            },
            {
                "record_id": "rec_init_2",
                "fields": {
                    process_review_start_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_fr_0.1",
                    process_review_start_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                    process_review_start_queue.BUILD_FAMILY_FIELD: ["us-en"],
                    process_review_start_queue.LANG_FIELD: [""],
                    process_review_start_queue.VERSION_FIELD: ["0.1"],
                    process_review_start_queue.REVIEW_STATUS_FIELD: [process_review_start_queue.REVIEW_STATUS_NOT_STARTED],
                    process_review_start_queue.REVIEW_TRIGGER_FIELD: True,
                    process_review_start_queue.GIT_REF_FIELD: "",
                    process_review_start_queue.PR_URL_FIELD: "",
                },
            },
        ]

        source = mock.Mock()
        source.fetch_records_with_ids.return_value = raw_records

        with tempfile.TemporaryDirectory() as td, \
            mock.patch.object(process_review_start_queue, "collect_review_start_preflight_errors", return_value=[]), \
            mock.patch.object(process_review_start_queue, "resolve_review_init_binding") as mock_binding, \
            mock.patch.object(process_review_start_queue, "_cli_bin", return_value="lark-cli"), \
            mock.patch.object(process_review_start_queue, "_phase2_identity", return_value="bot"), \
            mock.patch.object(process_review_start_queue, "LarkCliSource", return_value=source), \
            mock.patch.object(process_review_start_queue, "sync_phase2_snapshot_before_review_start"), \
            mock.patch.object(process_review_start_queue, "_run_git"), \
            mock.patch.object(
                process_review_start_queue,
                "resolve_config_path_for_task",
                side_effect=lambda *, region, lang, build_family=None: Path(td) / "config.us.yaml",
            ), \
            mock.patch.object(process_review_start_queue, "load_config", return_value={"build": {"queue_by_document_key": True}}), \
            mock.patch.object(process_review_start_queue, "start_review_for_record") as mock_start_review:
            mock_binding.return_value = process_review_start_queue.ReviewInitBinding(
                base_token_env="FEISHU_PHASE2_BASE_TOKEN",
                table_id_env="FEISHU_PHASE2_REVIEW_INIT_TABLE_ID",
                view_id_env="FEISHU_PHASE2_REVIEW_INIT_VIEW_ID",
                base_token="app_xxx",
                table_id="tbl_init",
                view_id="vew_init",
            )
            exit_code = process_review_start_queue.process_review_start_queue(
                cfg=cfg,
                config_path=Path(td) / "config.yaml",
                data_root=str(Path(td) / ".tmp" / "review-start" / "phase2"),
                dry_run=False,
                record_id=None,
            )

        self.assertEqual(1, exit_code)
        mock_start_review.assert_not_called()
        source.upsert_record.assert_not_called()
