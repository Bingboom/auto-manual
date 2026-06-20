from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import process_review_start_queue
from tools import process_review_start_queue_git


class TestProcessReviewStartQueue(unittest.TestCase):
    def test_resolve_docs_dir_for_config_should_follow_worktree_relative_path(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            worktree = Path(td) / "review-start-worktree"
            config_path = worktree / "config.us-en.yaml"
            cfg = {"paths": {"docs_dir": "docs"}}

            docs_dir = process_review_start_queue._resolve_docs_dir_for_config(config_path, cfg)

        self.assertEqual((worktree / "docs").resolve(strict=False), docs_dir.resolve(strict=False))

    def test_resolve_docs_dir_for_config_should_keep_configs_dir_repo_relative(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            worktree = Path(td) / "review-start-worktree"
            config_path = worktree / "configs" / "config.eu.yaml"
            cfg = {"paths": {"docs_dir": "docs"}}

            docs_dir = process_review_start_queue._resolve_docs_dir_for_config(config_path, cfg)

        self.assertEqual((worktree / "docs").resolve(strict=False), docs_dir.resolve(strict=False))

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

    def test_select_pending_review_start_records_should_require_checkbox_but_allow_inreview_status(self) -> None:
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

        self.assertEqual(["rec_pending", "rec_started"], [record.record_id for record in records])

    def test_select_pending_review_start_records_should_require_document_key(self) -> None:
        records = process_review_start_queue.select_pending_review_start_records(
            [
                {
                    "record_id": "rec_missing_key",
                    "fields": {
                        process_review_start_queue.DOCUMENT_ID_FIELD: "JE-1000F_EU_0.1",
                        process_review_start_queue.WORKFLOW_ACTION_FIELD: "Start Review",
                        process_review_start_queue.REVIEW_TRIGGER_FIELD: True,
                    },
                },
                {
                    "record_id": "rec_ready",
                    "fields": {
                        process_review_start_queue.DOCUMENT_KEY_FIELD: "JE-1000F_EU",
                        process_review_start_queue.WORKFLOW_ACTION_FIELD: "Start Review",
                        process_review_start_queue.REVIEW_TRIGGER_FIELD: True,
                    },
                },
            ]
        )

        self.assertEqual(["rec_ready"], [record.record_id for record in records])

    def test_select_pending_review_start_records_should_raise_for_targeted_record_without_document_key(self) -> None:
        with self.assertRaisesRegex(
            RuntimeError,
            "Document_Key must be non-empty for review-start record rec_missing_key",
        ):
            process_review_start_queue.select_pending_review_start_records(
                [
                    {
                        "record_id": "rec_missing_key",
                        "fields": {
                            process_review_start_queue.DOCUMENT_ID_FIELD: "JE-1000F_EU_0.1",
                            process_review_start_queue.WORKFLOW_ACTION_FIELD: "Start Review",
                            process_review_start_queue.REVIEW_TRIGGER_FIELD: True,
                        },
                    }
                ],
                record_id="rec_missing_key",
            )

    def test_select_pending_review_start_records_should_raise_for_targeted_record_with_invalid_workflow_action(self) -> None:
        with self.assertRaisesRegex(
            RuntimeError,
            "Workflow_action must map to Start Review for review-start record rec_bad_action",
        ):
            process_review_start_queue.select_pending_review_start_records(
                [
                    {
                        "record_id": "rec_bad_action",
                        "fields": {
                            process_review_start_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_en_0.1",
                            process_review_start_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                            process_review_start_queue.WORKFLOW_ACTION_FIELD: "Publish",
                            process_review_start_queue.REVIEW_TRIGGER_FIELD: True,
                        },
                    }
                ],
                record_id="rec_bad_action",
            )

    def test_select_pending_review_start_records_should_accept_object_style_feishu_values(self) -> None:
        records = process_review_start_queue.select_pending_review_start_records(
            [
                {
                    "record_id": "rec_object_action",
                    "fields": {
                        process_review_start_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_0.2",
                        process_review_start_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                        process_review_start_queue.WORKFLOW_ACTION_FIELD: [{"text": "Start Review"}],
                        process_review_start_queue.REVIEW_STATUS_FIELD: [{"text": "NotStarted"}],
                        process_review_start_queue.REVIEW_TRIGGER_FIELD: True,
                    },
                }
            ]
        )

        self.assertEqual(["rec_object_action"], [record.record_id for record in records])

    def test_select_pending_review_start_records_should_skip_non_review_actions_in_shared_view(self) -> None:
        records = process_review_start_queue.select_pending_review_start_records(
            [
                {
                    "record_id": "rec_start_review",
                    "fields": {
                        process_review_start_queue.DOCUMENT_ID_FIELD: "JE-1000F_JP_ja_0.2",
                        process_review_start_queue.DOCUMENT_KEY_FIELD: "JE-1000F_JP",
                        process_review_start_queue.BUILD_FAMILY_FIELD: ["jp-ja"],
                        process_review_start_queue.LANG_FIELD: ["ja"],
                        process_review_start_queue.VERSION_FIELD: ["0.2"],
                        process_review_start_queue.WORKFLOW_ACTION_FIELD: "Start Review",
                        process_review_start_queue.REVIEW_STATUS_FIELD: [process_review_start_queue.REVIEW_STATUS_NOT_STARTED],
                        process_review_start_queue.REVIEW_TRIGGER_FIELD: True,
                    },
                },
                {
                    "record_id": "rec_publish",
                    "fields": {
                        process_review_start_queue.DOCUMENT_ID_FIELD: "JE-1000F_JP_ja_0.2",
                        process_review_start_queue.DOCUMENT_KEY_FIELD: "JE-1000F_JP",
                        process_review_start_queue.BUILD_FAMILY_FIELD: ["jp-ja"],
                        process_review_start_queue.LANG_FIELD: ["ja"],
                        process_review_start_queue.VERSION_FIELD: ["0.2"],
                        process_review_start_queue.WORKFLOW_ACTION_FIELD: "Publish",
                        process_review_start_queue.REVIEW_STATUS_FIELD: [process_review_start_queue.REVIEW_STATUS_NOT_STARTED],
                        process_review_start_queue.REVIEW_TRIGGER_FIELD: True,
                    },
                },
            ]
        )

        self.assertEqual(["rec_start_review"], [record.record_id for record in records])

    def test_generate_review_branch_name_uses_model_region(self) -> None:
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

        # new reviews get review/<MODEL>-<REGION> (region = the 2nd Document_ID segment)
        self.assertEqual(
            process_review_start_queue.generate_review_branch_name(record),
            "review/JE-1000F-JP",
        )

    def test_generate_review_branch_name_reuses_existing_git_ref(self) -> None:
        record = process_review_start_queue.ReviewStartRecord(
            record_id="rec_1",
            document_id="JE-1000F_US_1.4",
            document_key="JE-1000F_US",
            build_family="us",
            version="1.4",
            lang="en",
            review_status="InReview",
            review_trigger_value=True,
            git_ref="review/JE-1000F-US",
            pr_url="",
        )

        # an existing review keeps its recorded branch (re-review reuses + reseeds it)
        self.assertEqual(
            process_review_start_queue.generate_review_branch_name(record),
            "review/JE-1000F-US",
        )

    def test_prepare_branch_worktree_should_always_seed_from_latest_base_ref(self) -> None:
        with tempfile.TemporaryDirectory() as td, mock.patch.object(
            process_review_start_queue_git,
            "run_git",
        ) as mock_run_git:
            root = Path(td)

            worktree = process_review_start_queue_git.prepare_branch_worktree(
                root=root,
                branch_name="codex/review-je-1000f-jp",
                base_ref="main",
                slug_branch_token_fn=lambda _: "review-je-1000f-jp",
            )

        self.assertEqual(root / ".tmp" / "review-start-worktrees" / "review-je-1000f-jp", worktree)
        observed_commands = [call.args[0] for call in mock_run_git.call_args_list]
        self.assertEqual(
            [
                ["fetch", "origin", "--prune"],
                ["worktree", "add", "--force", str(worktree), "origin/main"],
                ["checkout", "-B", "codex/review-je-1000f-jp", "origin/main"],
            ],
            observed_commands,
        )

    def test_ensure_review_bundle_on_branch_should_refresh_existing_review_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as td, mock.patch.object(
            process_review_start_queue_git,
            "run_command",
        ) as mock_run_command:
            root = Path(td)
            worktree = root / "worktree"
            docs_dir = worktree / "docs"
            review_dir = docs_dir / "_review" / "JE-1000F" / "JP"
            review_dir.mkdir(parents=True, exist_ok=True)
            config_path = worktree / "config.ja.yaml"
            config_path.write_text("paths:\n  docs_dir: docs\n", encoding="utf-8")

            observed = process_review_start_queue_git.ensure_review_bundle_on_branch(
                root=root,
                worktree=worktree,
                build_config_path=config_path,
                model="JE-1000F",
                region="JP",
                data_root=str(root / ".tmp" / "review-start" / "phase2"),
                load_config_fn=lambda _: {"paths": {"docs_dir": "docs"}},
            )

        self.assertEqual(review_dir, observed)
        review_command = mock_run_command.call_args_list[1].args[0]
        self.assertIn("--refresh-review", review_command)

    def test_ensure_review_bundle_on_branch_should_preserve_configs_relative_config_path(self) -> None:
        with tempfile.TemporaryDirectory() as td, mock.patch.object(
            process_review_start_queue_git,
            "run_command",
        ) as mock_run_command:
            root = Path(td)
            worktree = root / "worktree"
            config_path = root / "configs" / "config.eu.yaml"
            review_dir = worktree / "docs" / "_review" / "JE-2000F" / "EU"
            review_dir.mkdir(parents=True, exist_ok=True)

            observed = process_review_start_queue_git.ensure_review_bundle_on_branch(
                root=root,
                worktree=worktree,
                build_config_path=config_path,
                model="JE-2000F",
                region="EU",
                data_root=str(root / ".tmp" / "review-start" / "phase2"),
                load_config_fn=lambda _: {"paths": {"docs_dir": "docs"}},
            )

        self.assertEqual(review_dir, observed)
        rst_command = mock_run_command.call_args_list[0].args[0]
        self.assertIn(str(worktree / "configs" / "config.eu.yaml"), rst_command)
        self.assertNotIn(str(worktree / "config.eu.yaml"), rst_command)

    def test_push_branch_should_force_with_lease(self) -> None:
        with tempfile.TemporaryDirectory() as td, mock.patch.object(
            process_review_start_queue_git,
            "run_git",
        ) as mock_run_git:
            root = Path(td)
            worktree = root / "worktree"

            process_review_start_queue_git.push_branch(
                root=root,
                worktree=worktree,
                branch_name="codex/review-je-1000f-jp",
            )

        mock_run_git.assert_called_once_with(
            ["push", "--force-with-lease", "-u", "origin", "codex/review-je-1000f-jp"],
            root=root,
            cwd=worktree,
        )

    def test_start_review_for_record_should_push_even_when_seed_matches_base_ref(self) -> None:
        with tempfile.TemporaryDirectory() as td, \
            mock.patch.object(
                process_review_start_queue_git,
                "prepare_branch_worktree",
                return_value=Path(td) / "worktree",
            ), \
            mock.patch.object(process_review_start_queue_git, "configure_git_identity"), \
            mock.patch.object(
                process_review_start_queue_git,
                "ensure_review_bundle_on_branch",
                return_value=Path(td) / "worktree" / "docs" / "_review" / "JE-1000F" / "JP",
            ), \
            mock.patch.object(
                process_review_start_queue_git,
                "commit_review_bundle_if_changed",
                return_value=False,
            ), \
            mock.patch.object(process_review_start_queue_git, "push_branch") as mock_push_branch, \
            mock.patch.object(
                process_review_start_queue_git,
                "ensure_pull_request_for_branch",
                return_value="https://github.com/Bingboom/auto-manual/pull/999",
            ), \
            mock.patch.object(process_review_start_queue_git, "remove_worktree"):
            record = process_review_start_queue.ReviewStartRecord(
                record_id="rec_review",
                document_id="JE-1000F_JP_ja_0.1",
                document_key="JE-1000F_JP",
                build_family="jp-ja",
                version="0.1",
                lang="ja",
                review_status="InReview",
                review_trigger_value=True,
                git_ref="codex/review-je-1000f-jp",
                pr_url="https://github.com/Bingboom/auto-manual/pull/998",
            )

            branch_name, pr_url = process_review_start_queue_git.start_review_for_record(
                root=Path(td),
                record=record,
                build_config_path=Path(td) / "config.ja.yaml",
                snapshot_data_root=str(Path(td) / ".tmp" / "review-start" / "phase2"),
                base_ref="main",
                repository="Bingboom/auto-manual",
                token="ghs_token",
                slug_branch_token_fn=lambda value: value,
                resolve_target_for_review_start_fn=lambda _: ("JE-1000F", "JP"),
                generate_review_branch_name_fn=lambda _: "codex/review-je-1000f-jp",
                load_config_fn=lambda _: {"paths": {"docs_dir": "docs"}},
            )

        self.assertEqual("codex/review-je-1000f-jp", branch_name)
        self.assertEqual("https://github.com/Bingboom/auto-manual/pull/999", pr_url)
        mock_push_branch.assert_called_once_with(
            root=Path(td),
            worktree=Path(td) / "worktree",
            branch_name="codex/review-je-1000f-jp",
        )

    def test_group_review_start_records_should_collapse_same_document_key_without_config_lookup(self) -> None:
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
            side_effect=AssertionError("review-start grouping must not resolve config"),
        ) as mock_resolve_config_path, mock.patch.object(
            process_review_start_queue,
            "load_config",
            side_effect=AssertionError("review-start grouping must not load config"),
        ) as mock_load_config:
            grouped = process_review_start_queue.group_review_start_records(records)

        self.assertEqual(1, len(grouped))
        self.assertEqual(["rec_en", "rec_fr"], [record.record_id for record in grouped[0]])
        mock_resolve_config_path.assert_not_called()
        mock_load_config.assert_not_called()

    def test_review_start_record_key_should_ignore_link_style_document_key_for_display(self) -> None:
        record = process_review_start_queue.ReviewStartRecord(
            record_id="rec_1",
            document_id="JE-1000F_US_en_0.1",
            document_key='{"id":"recvfw0zG4PzxS"}',
            build_family="us-en",
            version="0.1",
            lang="en",
            review_status="NotStarted",
            review_trigger_value=True,
            git_ref="",
            pr_url="",
        )

        self.assertEqual("JE-1000F_US", process_review_start_queue.review_start_record_key(record))

    def test_group_review_start_records_should_not_collapse_link_style_document_key_rows(self) -> None:
        records = [
            process_review_start_queue.ReviewStartRecord(
                record_id="rec_en_1",
                document_id="JE-1000F_US_en_0.1",
                document_key='{"id":"recvfw0zG4PzxS"}',
                build_family="us-en",
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
                document_key='{"id":"recvfw0zG4PzxS"}',
                build_family="us-en",
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
            side_effect=AssertionError("review-start grouping must not resolve config"),
        ) as mock_resolve_config_path, mock.patch.object(
            process_review_start_queue,
            "load_config",
            side_effect=AssertionError("review-start grouping must not load config"),
        ) as mock_load_config:
            grouped = process_review_start_queue.group_review_start_records(records)

        self.assertEqual(2, len(grouped))
        self.assertEqual(["rec_en_1"], [record.record_id for record in grouped[0]])
        self.assertEqual(["rec_en_2"], [record.record_id for record in grouped[1]])
        mock_resolve_config_path.assert_not_called()
        mock_load_config.assert_not_called()

    def test_group_review_start_records_should_collapse_same_document_key_without_queue_config(self) -> None:
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
            side_effect=AssertionError("review-start grouping must not resolve config"),
        ) as mock_resolve_config_path, mock.patch.object(
            process_review_start_queue,
            "load_config",
            side_effect=AssertionError("review-start grouping must not load config"),
        ) as mock_load_config:
            grouped = process_review_start_queue.group_review_start_records(records)

        self.assertEqual(1, len(grouped))
        self.assertEqual(["rec_en_1", "rec_en_2"], [record.record_id for record in grouped[0]])
        mock_resolve_config_path.assert_not_called()
        mock_load_config.assert_not_called()

    def test_resolve_review_start_config_path_should_support_new_resolution_signature(self) -> None:
        expected = Path("config.us.yaml")

        def fake_resolver(*, repo_root, region, lang, build_family=None, config_loader):
            self.assertEqual(process_review_start_queue.ROOT, repo_root)
            self.assertIs(process_review_start_queue.load_config, config_loader)
            self.assertEqual("US", region)
            self.assertEqual("", lang)
            self.assertEqual("us-merged", build_family)
            return expected

        with mock.patch.object(process_review_start_queue, "resolve_config_path_for_task", side_effect=fake_resolver):
            resolved = process_review_start_queue._resolve_review_start_config_path(
                region="US",
                lang="",
                build_family="us-merged",
            )

        self.assertEqual(expected, resolved)

    def test_resolve_review_start_config_path_should_fallback_to_region_config_when_lang_blank(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "config.zh.yaml").write_text("build: {}\n", encoding="utf-8")
            (root / "config.us.yaml").write_text("build: {}\n", encoding="utf-8")
            cfgs = {
                "config.zh.yaml": {
                    "build": {
                        "family_id": "cn-zh",
                        "languages": ["zh"],
                        "default_region": "CN",
                    }
                },
                "config.us.yaml": {
                    "build": {
                        "family_id": "us-merged",
                        "languages": ["en", "fr", "es"],
                        "default_region": "US",
                        "queue_by_document_key": True,
                    }
                },
            }

            with mock.patch.object(process_review_start_queue, "ROOT", root), \
                mock.patch.object(
                    process_review_start_queue,
                    "resolve_config_path_for_task",
                    side_effect=RuntimeError("No config family matches region='CN' and lang=''"),
                ), \
                mock.patch.object(
                    process_review_start_queue,
                    "load_config",
                    side_effect=lambda path: cfgs[path.name],
                ):
                resolved = process_review_start_queue._resolve_review_start_config_path(
                    region="CN",
                    lang="",
                    build_family="",
                )

        self.assertEqual(root / "config.zh.yaml", resolved)

    def test_resolve_review_start_config_path_fallback_should_scan_configs_dir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            configs_dir = root / "configs"
            configs_dir.mkdir()
            (configs_dir / "config.eu.yaml").write_text("build: {}\n", encoding="utf-8")
            cfgs = {
                "config.eu.yaml": {
                    "build": {
                        "family_id": "eu-merged",
                        "languages": ["en", "fr", "es", "de", "it", "uk"],
                        "default_region": "EU",
                        "queue_by_document_key": True,
                    }
                },
            }

            with mock.patch.object(process_review_start_queue, "ROOT", root), \
                mock.patch.object(
                    process_review_start_queue,
                    "resolve_config_path_for_task",
                    side_effect=RuntimeError("No config family matches region='EU' and lang=''"),
                ), \
                mock.patch.object(
                    process_review_start_queue,
                    "load_config",
                    side_effect=lambda path: cfgs[path.name],
                ):
                resolved = process_review_start_queue._resolve_review_start_config_path(
                    region="EU",
                    lang="",
                    build_family="",
                )

        self.assertEqual(configs_dir / "config.eu.yaml", resolved)

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

    def test_resolve_target_for_review_start_should_use_document_key_without_document_id(self) -> None:
        record = process_review_start_queue.ReviewStartRecord(
            record_id="rec_eu_review",
            document_id="",
            document_key="JE-1000F_EU",
            build_family="",
            version="",
            lang="",
            review_status="NotStarted",
            review_trigger_value=True,
            git_ref="",
            pr_url="",
        )

        model, region = process_review_start_queue.resolve_target_for_review_start(record)

        self.assertEqual("JE-1000F", model)
        self.assertEqual("EU", region)
        self.assertEqual("JE-1000F_EU", record.label)

    def test_resolve_target_for_review_start_should_fallback_to_task_id(self) -> None:
        record = process_review_start_queue.ReviewStartRecord(
            record_id="rec_eu_review",
            document_id="",
            document_key='{"id":"recvhoZFKGg7l0"}',
            build_family="eu-merged",
            version="",
            lang="",
            review_status="NotStarted",
            review_trigger_value=True,
            git_ref="",
            pr_url="",
            task_id="JE-1000F_EU_Start Review",
        )

        model, region = process_review_start_queue.resolve_target_for_review_start(record)

        self.assertEqual("JE-1000F", model)
        self.assertEqual("EU", region)
        self.assertEqual("JE-1000F_EU", record.label)

    def test_resolve_docs_dir_for_config_should_follow_repo_relative_path(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            worktree = Path(td)
            config_path = worktree / "config.yaml"
            docs_dir = process_review_start_queue._resolve_docs_dir_for_config(
                config_path,
                {"paths": {"docs_dir": "docs"}},
            )

        self.assertEqual((worktree / "docs").resolve(strict=False), docs_dir.resolve(strict=False))

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

    def test_process_review_start_queue_should_force_restart_existing_inreview_row(self) -> None:
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
                    process_review_start_queue.REVIEW_STATUS_FIELD: [process_review_start_queue.REVIEW_STATUS_IN_REVIEW],
                    process_review_start_queue.REVIEW_TRIGGER_FIELD: True,
                    process_review_start_queue.GIT_REF_FIELD: "codex/review-je-1000f-us",
                    process_review_start_queue.PR_URL_FIELD: "https://github.com/Bingboom/auto-manual/pull/998",
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
            mock.patch.object(
                process_review_start_queue,
                "start_review_for_record",
                return_value=("codex/review-je-1000f-us", "https://github.com/Bingboom/auto-manual/pull/999"),
            ) as mock_start_review:
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
        mock_start_review.assert_called_once()
        source.upsert_record.assert_called_once()
        kwargs = source.upsert_record.call_args.kwargs
        self.assertEqual("rec_init_dup", kwargs["record_id"])
        self.assertEqual(
            ["InReview"],
            kwargs["record"][process_review_start_queue.REVIEW_STATUS_FIELD],
        )
        self.assertEqual(
            "codex/review-je-1000f-us",
            kwargs["record"][process_review_start_queue.GIT_REF_FIELD],
        )
        self.assertEqual(
            "https://github.com/Bingboom/auto-manual/pull/999",
            kwargs["record"][process_review_start_queue.PR_URL_FIELD],
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

    def test_process_review_start_queue_should_fail_on_conflicting_version_and_git_ref_in_same_merged_group(self) -> None:
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
                "record_id": "rec_old_pending",
                "fields": {
                    process_review_start_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_0.1",
                    process_review_start_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                    process_review_start_queue.BUILD_FAMILY_FIELD: ["us-merged"],
                    process_review_start_queue.LANG_FIELD: [""],
                    process_review_start_queue.VERSION_FIELD: ["0.1"],
                    process_review_start_queue.REVIEW_STATUS_FIELD: [process_review_start_queue.REVIEW_STATUS_NOT_STARTED],
                    process_review_start_queue.REVIEW_TRIGGER_FIELD: True,
                    process_review_start_queue.GIT_REF_FIELD: "codex/review-id-recvfw0zg4pzxs",
                    process_review_start_queue.PR_URL_FIELD: "https://github.com/Bingboom/auto-manual/pull/43",
                },
            },
            {
                "record_id": "rec_new_pending",
                "fields": {
                    process_review_start_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_0.2",
                    process_review_start_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                    process_review_start_queue.BUILD_FAMILY_FIELD: ["us-merged"],
                    process_review_start_queue.LANG_FIELD: [""],
                    process_review_start_queue.VERSION_FIELD: ["0.2"],
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
                return_value=Path(td) / "config.us.yaml",
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

    def test_process_review_start_queue_should_write_structured_failure_summary_for_missing_spec_data(self) -> None:
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
                "record_id": "rec_cn_missing_spec",
                "fields": {
                    process_review_start_queue.DOCUMENT_ID_FIELD: "JE-1000F_CN_0.1",
                    process_review_start_queue.DOCUMENT_KEY_FIELD: "JE-1000F_CN",
                    process_review_start_queue.BUILD_FAMILY_FIELD: ["cn-zh"],
                    process_review_start_queue.LANG_FIELD: [""],
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
            mock.patch.object(process_review_start_queue, "_run_git"), \
            mock.patch.object(process_review_start_queue, "load_config", return_value={"build": {"queue_by_document_key": True}}), \
            mock.patch.object(
                process_review_start_queue,
                "resolve_config_path_for_task",
                return_value=Path(td) / "config.zh.yaml",
            ), \
            mock.patch.object(
                process_review_start_queue,
                "start_review_for_record",
                side_effect=RuntimeError(
                    "Failed to resolve Product Name from Spec_Master.csv for model='JE-1000F', region='CN', lang='zh'. "
                    "Source: /tmp/Spec_Master.csv"
                ),
            ):
            mock_binding.return_value = process_review_start_queue.ReviewInitBinding(
                base_token_env="FEISHU_PHASE2_BASE_TOKEN",
                table_id_env="FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID",
                view_id_env="FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID",
                base_token="app_xxx",
                table_id="tbl_init",
                view_id="vew_init",
            )
            summary_path = Path(td) / ".tmp" / "openclaw" / "feishu-start-review-failure-summary.json"
            with mock.patch.dict(
                process_review_start_queue.os.environ,
                {"AUTO_MANUAL_FAILURE_SUMMARY_PATH": str(summary_path)},
                clear=False,
            ):
                exit_code = process_review_start_queue.process_review_start_queue(
                    cfg=cfg,
                    config_path=Path(td) / "config.yaml",
                    data_root=str(Path(td) / ".tmp" / "review-start" / "phase2"),
                    dry_run=False,
                    record_id="rec_cn_missing_spec",
                )
                self.assertEqual(1, exit_code)
                self.assertTrue(summary_path.exists())
                payload = json.loads(summary_path.read_text(encoding="utf-8"))
                self.assertEqual("missing_spec_data", payload["summary_code"])
                self.assertEqual("缺少 JE-1000F_CN 的规格数据，无法进入 review。", payload["summary_message"])
                self.assertEqual(1, payload["failure_count"])
                self.assertEqual(
                    "请先补齐 JE-1000F_CN 在 Spec_Master 中的规格数据，再重试。",
                    payload["summary_next_step"],
                )

    def test_process_review_start_queue_should_write_structured_failure_summary_for_targeted_no_pending_record(self) -> None:
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

        source = mock.Mock()
        source.fetch_records_with_ids.return_value = []

        with tempfile.TemporaryDirectory() as td, \
            mock.patch.object(process_review_start_queue, "collect_review_start_preflight_errors", return_value=[]), \
            mock.patch.object(process_review_start_queue, "resolve_review_init_binding") as mock_binding, \
            mock.patch.object(process_review_start_queue, "_cli_bin", return_value="lark-cli"), \
            mock.patch.object(process_review_start_queue, "_phase2_identity", return_value="bot"), \
            mock.patch.object(process_review_start_queue, "LarkCliSource", return_value=source):
            mock_binding.return_value = process_review_start_queue.ReviewInitBinding(
                base_token_env="FEISHU_PHASE2_BASE_TOKEN",
                table_id_env="FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID",
                view_id_env="FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID",
                base_token="app_xxx",
                table_id="tbl_init",
                view_id="vew_init",
            )
            summary_path = Path(td) / ".tmp" / "openclaw" / "feishu-start-review-failure-summary.json"
            with mock.patch.dict(
                process_review_start_queue.os.environ,
                {"AUTO_MANUAL_FAILURE_SUMMARY_PATH": str(summary_path)},
                clear=False,
            ):
                exit_code = process_review_start_queue.process_review_start_queue(
                    cfg=cfg,
                    config_path=Path(td) / "config.yaml",
                    data_root=str(Path(td) / ".tmp" / "review-start" / "phase2"),
                    dry_run=False,
                    record_id="rec_target_missing",
                )
                self.assertEqual(1, exit_code)
                self.assertTrue(summary_path.exists())
                payload = json.loads(summary_path.read_text(encoding="utf-8"))
                self.assertEqual("review_start_target_not_pending", payload["summary_code"])
                self.assertEqual(
                    "当前 Feishu 视图里没有找到 record_id=rec_target_missing 对应的待进入 review 记录。",
                    payload["summary_message"],
                )
                self.assertEqual(
                    "请检查 GitHub secrets 里的 table/view 绑定、bot 权限，以及该记录当前是否仍勾选 是否进入Review 且 Workflow_action=Start Review。",
                    payload["summary_next_step"],
                )

    def test_process_review_start_queue_should_treat_targeted_completed_record_as_success(self) -> None:
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
                "record_id": "rec_started",
                "fields": {
                    process_review_start_queue.DOCUMENT_ID_FIELD: "JE-1000F_JP_0.6",
                    process_review_start_queue.DOCUMENT_KEY_FIELD: "JE-1000F_JP",
                    process_review_start_queue.BUILD_FAMILY_FIELD: ["jp-ja"],
                    process_review_start_queue.LANG_FIELD: ["ja"],
                    process_review_start_queue.VERSION_FIELD: ["0.6"],
                    process_review_start_queue.WORKFLOW_ACTION_FIELD: "Start Review",
                    process_review_start_queue.REVIEW_STATUS_FIELD: [process_review_start_queue.REVIEW_STATUS_IN_REVIEW],
                    process_review_start_queue.REVIEW_TRIGGER_FIELD: False,
                    process_review_start_queue.GIT_REF_FIELD: "codex/review-je-1000f-jp",
                    process_review_start_queue.PR_URL_FIELD: "https://github.com/Bingboom/auto-manual/pull/120",
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
            mock.patch.object(process_review_start_queue, "sync_phase2_snapshot_before_review_start") as mock_sync, \
            mock.patch.object(process_review_start_queue, "start_review_for_record") as mock_start_review:
            mock_binding.return_value = process_review_start_queue.ReviewInitBinding(
                base_token_env="FEISHU_PHASE2_BASE_TOKEN",
                table_id_env="FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID",
                view_id_env="FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID",
                base_token="app_xxx",
                table_id="tbl_init",
                view_id="vew_init",
            )
            summary_path = Path(td) / ".tmp" / "openclaw" / "feishu-start-review-failure-summary.json"
            with mock.patch.dict(
                process_review_start_queue.os.environ,
                {"AUTO_MANUAL_FAILURE_SUMMARY_PATH": str(summary_path)},
                clear=False,
            ):
                exit_code = process_review_start_queue.process_review_start_queue(
                    cfg=cfg,
                    config_path=Path(td) / "config.yaml",
                    data_root=str(Path(td) / ".tmp" / "review-start" / "phase2"),
                    dry_run=False,
                    record_id="rec_started",
                )

        self.assertEqual(0, exit_code)
        self.assertFalse(summary_path.exists())
        mock_sync.assert_not_called()
        mock_start_review.assert_not_called()
        source.upsert_record.assert_not_called()
