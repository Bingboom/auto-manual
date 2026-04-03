from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import process_review_start_queue


class TestProcessReviewStartQueue(unittest.TestCase):
    def test_select_pending_review_start_records_should_require_checkbox_and_notstarted_status(self) -> None:
        records = process_review_start_queue.select_pending_review_start_records(
            [
                {
                    "record_id": "rec_pending",
                    "fields": {
                        process_review_start_queue.DOCUMENT_ID_FIELD: "JE-1000F_JP_ja_0.1",
                        process_review_start_queue.DOCUMENT_KEY_FIELD: "JE-1000F_JP",
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
            version="0.1",
            lang="ja",
            review_status="NotStarted",
            review_trigger_value=True,
            git_ref="",
            pr_url="",
        )

        branch_name = process_review_start_queue.generate_review_branch_name(record)

        self.assertTrue(branch_name.startswith("codex/review-"))
        self.assertIn("je-1000f-jp-ja-0-1", branch_name)

    def test_resolve_target_for_review_start_should_fallback_to_document_id(self) -> None:
        record = process_review_start_queue.ReviewStartRecord(
            record_id="rec_1",
            document_id="JE-1000F_JP_ja_0.1",
            document_key="{'id': 'recv_bad_link'}",
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
                    process_review_start_queue.DOCUMENT_ID_FIELD: "JE-1000F_JP_ja_0.1",
                    process_review_start_queue.DOCUMENT_KEY_FIELD: "JE-1000F_JP",
                    process_review_start_queue.LANG_FIELD: ["ja"],
                    process_review_start_queue.VERSION_FIELD: ["0.1"],
                    process_review_start_queue.REVIEW_STATUS_FIELD: [process_review_start_queue.REVIEW_STATUS_NOT_STARTED],
                    process_review_start_queue.REVIEW_TRIGGER_FIELD: True,
                    process_review_start_queue.GIT_REF_FIELD: "",
                    process_review_start_queue.PR_URL_FIELD: "",
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
            mock.patch.object(
                process_review_start_queue,
                "start_review_for_record",
                return_value=("codex/review-je-1000f-jp-ja-0-1", "https://github.com/Bingboom/auto-manual/pull/999"),
            ):
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
                record_id="rec_init_1",
            )

        self.assertEqual(0, exit_code)
        source.upsert_record.assert_called_once()
        kwargs = source.upsert_record.call_args.kwargs
        self.assertEqual("rec_init_1", kwargs["record_id"])
        self.assertEqual(["InReview"], kwargs["record"][process_review_start_queue.REVIEW_STATUS_FIELD])
        self.assertEqual("codex/review-je-1000f-jp-ja-0-1", kwargs["record"][process_review_start_queue.GIT_REF_FIELD])
        self.assertEqual(
            "https://github.com/Bingboom/auto-manual/pull/999",
            kwargs["record"][process_review_start_queue.PR_URL_FIELD],
        )
        self.assertFalse(kwargs["record"][process_review_start_queue.REVIEW_TRIGGER_FIELD])

    def test_ensure_pull_request_for_branch_should_retry_with_empty_commit_when_no_commits(self) -> None:
        record = process_review_start_queue.ReviewStartRecord(
            record_id="rec_1",
            document_id="JE-1000F_JP_ja_0.1",
            document_key="JE-1000F_JP",
            version="0.1",
            lang="ja",
            review_status="NotStarted",
            review_trigger_value=True,
            git_ref="",
            pr_url="",
        )
        worktree = Path(tempfile.mkdtemp())
        try:
            with mock.patch.object(
                process_review_start_queue,
                "_github_api_request",
                side_effect=[
                    [],
                    RuntimeError(
                        'GitHub API POST /repos/Bingboom/auto-manual/pulls failed: '
                        '{"message":"Validation Failed","errors":[{"resource":"PullRequest","code":"custom","message":"No commits between main and codex/review-je-1000f-jp-ja-0-1"}]}'
                    ),
                    {"html_url": "https://github.com/Bingboom/auto-manual/pull/1234"},
                ],
            ) as mock_api, mock.patch.object(
                process_review_start_queue, "_create_empty_review_start_commit"
            ) as mock_empty, mock.patch.object(process_review_start_queue, "_push_branch") as mock_push:
                pr_url = process_review_start_queue.ensure_pull_request_for_branch(
                    repository="Bingboom/auto-manual",
                    branch_name="codex/review-je-1000f-jp-ja-0-1",
                    base_ref="main",
                    token="ghs_test",
                    record=record,
                    worktree=worktree,
                )
        finally:
            worktree.rmdir()

        self.assertEqual("https://github.com/Bingboom/auto-manual/pull/1234", pr_url)
        mock_empty.assert_called_once_with(worktree=worktree, record=record)
        mock_push.assert_called_once_with(worktree=worktree, branch_name="codex/review-je-1000f-jp-ja-0-1")
        self.assertEqual(3, mock_api.call_count)
