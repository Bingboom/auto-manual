from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

from tools import process_build_queue
from tools import process_build_queue_main
from tests.test_helpers import temp_test_root, write_text


class TestProcessBuildQueue(unittest.TestCase):
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

    def test_parse_document_key_should_split_model_and_region(self) -> None:
        model, region = process_build_queue.parse_document_key("JE-1000F_US")

        self.assertEqual("JE-1000F", model)
        self.assertEqual("US", region)

    def test_resolve_target_for_record_should_fallback_to_document_id(self) -> None:
        record = process_build_queue.QueueRecord(
            record_id="rec_1",
            document_id="JE-1000F_US_en_1.0",
            document_key='{"id":"recvfw0zG4PzxS"}',
            version="1.0",
            lang="en",
            doc_phase="",
            git_ref="",
            trigger_value="Y",
            immediate_trigger_value=False,
        )

        model, region = process_build_queue.resolve_target_for_record(record)

        self.assertEqual("JE-1000F", model)
        self.assertEqual("US", region)

    def test_queue_record_key_should_ignore_link_style_document_key_for_display(self) -> None:
        record = process_build_queue.QueueRecord(
            record_id="rec_1",
            document_id="JE-1000F_US_en_1.0",
            document_key='{"id":"recvfw0zG4PzxS"}',
            version="1.0",
            lang="en",
            doc_phase="",
            git_ref="",
            trigger_value="Y",
            immediate_trigger_value=False,
        )

        self.assertEqual("JE-1000F_US", process_build_queue.queue_record_key(record))

    def test_resolve_config_path_for_task_should_prefer_lang_specific_config(self) -> None:
        with temp_test_root() as root:
            for name in ("config.yaml", "config.us-en.yaml", "config.us-fr.yaml"):
                write_text(root / name, "build: {}\n")

            configs = {
                "config.yaml": {
                    "build": {
                        "default_region": "US",
                        "languages": ["en"],
                        "include_lang_in_output_path": False,
                    }
                },
                "config.us-en.yaml": {
                    "build": {
                        "default_region": "US",
                        "languages": ["en"],
                        "include_lang_in_output_path": True,
                    }
                },
                "config.us-fr.yaml": {
                    "build": {
                        "default_region": "US",
                        "languages": ["fr"],
                        "include_lang_in_output_path": True,
                    }
                },
            }

            with mock.patch.object(process_build_queue, "ROOT", root), mock.patch.object(
                process_build_queue,
                "load_config",
                side_effect=lambda path: configs[path.name],
            ):
                config_path = process_build_queue.resolve_config_path_for_task(region="US", lang="en")

        self.assertEqual(root / "config.us-en.yaml", config_path)

    def test_resolve_config_path_for_task_should_use_document_key_config_as_lang_fallback(self) -> None:
        with temp_test_root() as root:
            for name in ("config.yaml", "config.us-en.yaml"):
                write_text(root / name, "build: {}\n")

            configs = {
                "config.yaml": {
                    "build": {
                        "default_region": "US",
                        "languages": ["en", "fr", "es"],
                        "include_lang_in_output_path": True,
                        "queue_by_document_key": True,
                    }
                },
                "config.us-en.yaml": {
                    "build": {
                        "default_region": "US",
                        "languages": ["en"],
                        "include_lang_in_output_path": True,
                    }
                },
            }

            with mock.patch.object(process_build_queue, "ROOT", root), mock.patch.object(
                process_build_queue,
                "load_config",
                side_effect=lambda path: configs[path.name],
            ):
                config_path = process_build_queue.resolve_config_path_for_task(region="US", lang="fr")

        self.assertEqual(root / "config.yaml", config_path)

    def test_resolve_config_path_for_task_should_allow_blank_lang_for_document_key_config(self) -> None:
        with temp_test_root() as root:
            for name in ("config.us.yaml", "config.us-en.yaml", "config.us-fr.yaml"):
                write_text(root / name, "build: {}\n")

            configs = {
                "config.us.yaml": {
                    "build": {
                        "default_region": "US",
                        "languages": ["en", "fr", "es"],
                        "include_lang_in_output_path": False,
                        "queue_by_document_key": True,
                    }
                },
                "config.us-en.yaml": {
                    "build": {
                        "default_region": "US",
                        "languages": ["en"],
                        "include_lang_in_output_path": True,
                    }
                },
                "config.us-fr.yaml": {
                    "build": {
                        "default_region": "US",
                        "languages": ["fr"],
                        "include_lang_in_output_path": True,
                    }
                },
            }

            with mock.patch.object(process_build_queue, "ROOT", root), mock.patch.object(
                process_build_queue,
                "load_config",
                side_effect=lambda path: configs[path.name],
            ):
                config_path = process_build_queue.resolve_config_path_for_task(region="US", lang="")

        self.assertEqual(root / "config.us.yaml", config_path)

    def test_resolve_config_path_for_task_should_prefer_build_family_when_present(self) -> None:
        with temp_test_root() as root:
            for name in ("config.us.yaml", "config.us-en.yaml", "config.us-fr.yaml"):
                write_text(root / name, "build: {}\n")

            configs = {
                "config.us.yaml": {
                    "build": {
                        "family_id": "us-merged",
                        "default_region": "US",
                        "languages": ["en", "fr", "es"],
                        "include_lang_in_output_path": False,
                        "queue_by_document_key": True,
                    }
                },
                "config.us-en.yaml": {
                    "build": {
                        "family_id": "us-en",
                        "default_region": "US",
                        "languages": ["en"],
                        "include_lang_in_output_path": True,
                    }
                },
                "config.us-fr.yaml": {
                    "build": {
                        "family_id": "us-fr",
                        "default_region": "US",
                        "languages": ["fr"],
                        "include_lang_in_output_path": True,
                    }
                },
            }

            with mock.patch.object(process_build_queue, "ROOT", root), mock.patch.object(
                process_build_queue,
                "load_config",
                side_effect=lambda path: configs[path.name],
            ):
                config_path = process_build_queue.resolve_config_path_for_task(
                    region="US",
                    lang="fr",
                    build_family="us-merged",
                )

        self.assertEqual(root / "config.us.yaml", config_path)

    def test_resolve_config_path_for_task_should_fallback_to_lang_when_build_family_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name in ("config.us.yaml", "config.us-en.yaml"):
                (root / name).write_text("build: {}\n", encoding="utf-8")

            configs = {
                "config.us.yaml": {
                    "build": {
                        "family_id": "us-merged",
                        "default_region": "US",
                        "languages": ["en", "fr", "es"],
                        "include_lang_in_output_path": False,
                        "queue_by_document_key": True,
                    }
                },
                "config.us-en.yaml": {
                    "build": {
                        "family_id": "us-en",
                        "default_region": "US",
                        "languages": ["en"],
                        "include_lang_in_output_path": True,
                    }
                },
            }

            with mock.patch.object(process_build_queue, "ROOT", root), mock.patch.object(
                process_build_queue,
                "load_config",
                side_effect=lambda path: configs[path.name],
            ):
                config_path = process_build_queue.resolve_config_path_for_task(region="US", lang="en")

        self.assertEqual(root / "config.us-en.yaml", config_path)

    def test_resolve_config_path_for_task_should_reject_conflicting_build_family_and_lang(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_path = root / "config.us-en.yaml"
            config_path.write_text("build: {}\n", encoding="utf-8")
            configs = {
                "config.us-en.yaml": {
                    "build": {
                        "family_id": "us-en",
                        "default_region": "US",
                        "languages": ["en"],
                        "include_lang_in_output_path": True,
                    }
                }
            }

            with mock.patch.object(process_build_queue, "ROOT", root), mock.patch.object(
                process_build_queue,
                "load_config",
                side_effect=lambda path: configs[path.name],
            ):
                with self.assertRaisesRegex(RuntimeError, "conflicts with Lang"):
                    process_build_queue.resolve_config_path_for_task(
                        region="US",
                        lang="fr",
                        build_family="us-en",
                    )

    def test_resolve_config_path_for_task_should_reject_conflicting_build_family_and_region(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_path = root / "config.us-en.yaml"
            config_path.write_text("build: {}\n", encoding="utf-8")
            configs = {
                "config.us-en.yaml": {
                    "build": {
                        "family_id": "us-en",
                        "default_region": "US",
                        "languages": ["en"],
                        "include_lang_in_output_path": True,
                    }
                }
            }

            with mock.patch.object(process_build_queue, "ROOT", root), mock.patch.object(
                process_build_queue,
                "load_config",
                side_effect=lambda path: configs[path.name],
            ):
                with self.assertRaisesRegex(RuntimeError, "routes to region"):
                    process_build_queue.resolve_config_path_for_task(
                        region="JP",
                        lang="en",
                        build_family="us-en",
                    )

    def test_resolve_config_path_for_task_should_reject_publish_single_language_family(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_path = root / "config.us-en.yaml"
            config_path.write_text("build: {}\n", encoding="utf-8")
            configs = {
                "config.us-en.yaml": {
                    "build": {
                        "family_id": "us-en",
                        "default_region": "US",
                        "languages": ["en"],
                        "include_lang_in_output_path": True,
                    }
                }
            }

            with mock.patch.object(process_build_queue, "ROOT", root), mock.patch.object(
                process_build_queue,
                "load_config",
                side_effect=lambda path: configs[path.name],
            ):
                with self.assertRaisesRegex(RuntimeError, "whole-book Build_family"):
                    process_build_queue.resolve_config_path_for_task(
                        region="US",
                        lang="",
                        build_family="us-en",
                        workflow_action="publish",
                    )

    def test_resolve_config_path_for_task_should_reject_draft_lang_against_merged_family(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_path = root / "config.us.yaml"
            config_path.write_text("build: {}\n", encoding="utf-8")
            configs = {
                "config.us.yaml": {
                    "build": {
                        "family_id": "us-merged",
                        "default_region": "US",
                        "languages": ["en", "fr", "es"],
                        "include_lang_in_output_path": False,
                        "queue_by_document_key": True,
                    }
                }
            }

            with mock.patch.object(process_build_queue, "ROOT", root), mock.patch.object(
                process_build_queue,
                "load_config",
                side_effect=lambda path: configs[path.name],
            ):
                with self.assertRaisesRegex(RuntimeError, "single-language Build_family"):
                    process_build_queue.resolve_config_path_for_task(
                        region="US",
                        lang="en",
                        build_family="us-merged",
                        workflow_action="draft",
                    )

    def test_group_pending_queue_records_should_merge_document_key_rows_when_config_requests_it(self) -> None:
        records = [
            process_build_queue.QueueRecord(
                record_id="rec_us_blank",
                document_id="JE-1000F_US_1.0",
                document_key="JE-1000F_US",
                version="1.0",
                lang="",
                workflow_action="Build Draft Package",
                doc_phase="Draft",
                git_ref="codex/review-je-1000f-us",
                trigger_value="Y",
                immediate_trigger_value=True,
                build_family="us-merged",
            ),
            process_build_queue.QueueRecord(
                record_id="rec_us_fr",
                document_id="JE-1000F_US_1.0",
                document_key="JE-1000F_US",
                version="1.0",
                lang="",
                workflow_action="Build Draft Package",
                doc_phase="Draft",
                git_ref="codex/review-je-1000f-us",
                trigger_value="Y",
                immediate_trigger_value=True,
                build_family="us-merged",
            ),
            process_build_queue.QueueRecord(
                record_id="rec_jp",
                document_id="JE-1000F_JP_ja_1.0",
                document_key="JE-1000F_JP",
                version="1.0",
                lang="ja",
                workflow_action="Build Draft Package",
                doc_phase="Draft",
                git_ref="codex/review-je-1000f-jp",
                trigger_value="Y",
                immediate_trigger_value=True,
                build_family="jp-ja",
            ),
        ]

        grouped = process_build_queue.group_pending_queue_records(records)

        self.assertEqual(
            [["rec_us_blank", "rec_us_fr"], ["rec_jp"]],
            [[record.record_id for record in group] for group in grouped],
        )

    def test_group_pending_queue_records_should_keep_single_language_families_separate(self) -> None:
        records = [
            process_build_queue.QueueRecord(
                record_id="rec_us_en",
                document_id="JE-1000F_US_en_1.0",
                document_key="JE-1000F_US",
                version="1.0",
                lang="en",
                workflow_action="Build Draft Package",
                doc_phase="Draft",
                git_ref="codex/review-je-1000f-us-en",
                trigger_value="Y",
                immediate_trigger_value=True,
                build_family="us-en",
            ),
            process_build_queue.QueueRecord(
                record_id="rec_us_fr",
                document_id="JE-1000F_US_fr_1.0",
                document_key="JE-1000F_US",
                version="1.0",
                lang="fr",
                workflow_action="Build Draft Package",
                doc_phase="Draft",
                git_ref="codex/review-je-1000f-us-fr",
                trigger_value="Y",
                immediate_trigger_value=True,
                build_family="us-fr",
            ),
        ]

        grouped = process_build_queue.group_pending_queue_records(records)

        self.assertEqual(
            [["rec_us_en"], ["rec_us_fr"]],
            [[record.record_id for record in group] for group in grouped],
        )

    def test_group_pending_queue_records_should_not_merge_link_style_document_key_rows(self) -> None:
        records = [
            process_build_queue.QueueRecord(
                record_id="rec_us_1",
                document_id="JE-1000F_US_en_1.0",
                document_key='{"id":"recvfw0zG4PzxS"}',
                version="1.0",
                lang="en",
                workflow_action="Build Draft Package",
                doc_phase="Draft",
                git_ref="codex/review-je-1000f-us-en",
                trigger_value="Y",
                immediate_trigger_value=True,
                build_family="us-en",
            ),
            process_build_queue.QueueRecord(
                record_id="rec_us_2",
                document_id="JE-1000F_US_en_1.0",
                document_key='{"id":"recvfw0zG4PzxS"}',
                version="1.0",
                lang="en",
                workflow_action="Build Draft Package",
                doc_phase="Draft",
                git_ref="codex/review-je-1000f-us-en",
                trigger_value="Y",
                immediate_trigger_value=True,
                build_family="us-en",
            ),
        ]

        grouped = process_build_queue.group_pending_queue_records(records)

        self.assertEqual(
            [["rec_us_1"], ["rec_us_2"]],
            [[record.record_id for record in group] for group in grouped],
        )

    def test_process_build_queue_dry_run_should_use_build_family_for_document_key_groups(self) -> None:
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

        class FakeSource:
            def fetch_records_with_ids(self, **_: object) -> list[dict[str, object]]:
                return raw_records

            def upsert_record(self, **_: object) -> dict[str, object]:
                raise AssertionError("dry-run should not write records")

        with mock.patch.object(process_build_queue, "collect_queue_preflight_errors", return_value=[]), mock.patch.object(
            process_build_queue,
            "resolve_document_link_binding",
            return_value=binding,
        ), mock.patch.object(process_build_queue, "LarkCliSource", return_value=FakeSource()), mock.patch.object(
            process_build_queue,
            "sync_phase2_snapshot_before_queue",
        ) as sync_mock, mock.patch.object(
            process_build_queue,
            "resolve_config_path_for_task",
            return_value=Path("config.us.yaml"),
        ) as resolve_mock:
            exit_code = process_build_queue.process_build_queue(
                cfg=cfg,
                config_path=Path("config.us.yaml"),
                data_root="data/phase2",
                dry_run=True,
            )

        self.assertEqual(0, exit_code)
        sync_mock.assert_not_called()
        self.assertEqual(3, resolve_mock.call_count)
        self.assertTrue(all(call.kwargs.get("build_family") == "us-merged" for call in resolve_mock.call_args_list))
        self.assertTrue(all(call.kwargs.get("workflow_action") == "draft" for call in resolve_mock.call_args_list))

    def test_build_success_fields_should_write_local_path_and_drive_url_and_clear_trigger(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            word_path = Path(td) / "docs" / "_build" / "JE-1000F" / "US" / "en" / "word" / "manual_je1000f_us_en.docx"
            drive_url = "https://test-degwga5x6ex8.feishu.cn/file/file_token_123"
            built_at = datetime(2026, 4, 1, 12, 34, 56)

            fields = process_build_queue.build_success_fields(
                version="1.0",
                word_output_path=word_path,
                document_link_url=drive_url,
                built_at=built_at,
                workflow_action="Build Draft Package",
                doc_phase="Draft",
                data_sync_status="skipped",
            )

        self.assertEqual(
            word_path.resolve(strict=False).as_posix(),
            fields[process_build_queue.DOCUMENT_DIRECTORY_FIELD],
        )
        self.assertEqual(drive_url, fields[process_build_queue.DOCUMENT_LINK_FIELD])
        self.assertNotIn(process_build_queue.DOCUMENT_LINK_DD_FIELD, fields)
        self.assertEqual(["已构建"], fields[process_build_queue.TRIGGER_FIELD])
        self.assertFalse(fields[process_build_queue.IMMEDIATE_TRIGGER_FIELD])
        self.assertFalse(fields[process_build_queue.FORCE_PHASE2_REFRESH_FIELD])
        self.assertEqual("skipped", fields[process_build_queue.DATA_SYNC_FIELD])
        self.assertIn("SUCCESS", fields[process_build_queue.RESULT_FIELD])
        self.assertIn("data_sync=skipped", fields[process_build_queue.RESULT_FIELD])
        self.assertIn("workflow_action=Build Draft Package", fields[process_build_queue.RESULT_FIELD])
        self.assertIn("version=1.0", fields[process_build_queue.RESULT_FIELD])

    def test_build_started_fields_should_write_datetime_millis(self) -> None:
        started_at = datetime(2026, 4, 1, 14, 55, 6)

        fields = process_build_queue.build_started_fields(started_at=started_at)

        self.assertEqual(
            int(started_at.timestamp() * 1000),
            fields[process_build_queue.BUILD_STARTED_AT_FIELD],
        )

    def test_build_failure_writeback_fields_should_preserve_latest_local_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            word_path = Path(td) / "docs" / "_build" / "JE-1000F" / "JP" / "word" / "manual_je1000f_jp.docx"
            fields = process_build_queue.build_failure_writeback_fields(
                version="1.0",
                message="permission | Permission denied [99991679]",
                workflow_action="Publish",
                doc_phase="Publish",
                data_sync_status="failed",
                word_output_path=word_path,
                document_link_url="https://test-degwga5x6ex8.feishu.cn/file/file_token_123",
            )

        self.assertEqual(
            word_path.resolve(strict=False).as_posix(),
            fields[process_build_queue.DOCUMENT_DIRECTORY_FIELD],
        )
        self.assertEqual(
            "https://test-degwga5x6ex8.feishu.cn/file/file_token_123",
            fields[process_build_queue.DOCUMENT_LINK_FIELD],
        )
        self.assertNotIn(process_build_queue.DOCUMENT_LINK_DD_FIELD, fields)
        self.assertFalse(fields[process_build_queue.IMMEDIATE_TRIGGER_FIELD])
        self.assertFalse(fields[process_build_queue.FORCE_PHASE2_REFRESH_FIELD])
        self.assertEqual("failed", fields[process_build_queue.DATA_SYNC_FIELD])
        self.assertIn("FAILED", fields[process_build_queue.RESULT_FIELD])
        self.assertIn("data_sync=failed", fields[process_build_queue.RESULT_FIELD])
        self.assertIn("workflow_action=Publish", fields[process_build_queue.RESULT_FIELD])
        self.assertIn("latest_drive_link_preserved", fields[process_build_queue.RESULT_FIELD])

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

    def test_build_document_for_task_should_use_review_source_for_draft_phase(self) -> None:
        commands: list[list[str]] = []
        with tempfile.TemporaryDirectory() as td:
            word_path = Path(td) / "docs" / "_build" / "JE-1000F" / "US" / "en" / "word" / "manual_je1000f_us_en.docx"
            word_path.parent.mkdir(parents=True, exist_ok=True)
            word_path.write_bytes(b"docx")

            with mock.patch.object(
                process_build_queue,
                "_run_command",
                side_effect=lambda cmd, **kwargs: commands.append(cmd),
            ), mock.patch.object(
                process_build_queue,
                "resolve_word_output_path_for_target",
                return_value=word_path,
            ):
                resolved_path = process_build_queue.build_document_for_task(
                    config_path=Path("config.us-en.yaml"),
                    model="JE-1000F",
                    region="US",
                    data_root="data/phase2",
                    doc_phase="Draft",
                    version="0.2",
                )
                self.assertTrue(resolved_path.exists())

        self.assertEqual(word_path.with_name("manual_je1000f_us_en_0.2.docx"), resolved_path)
        self.assertEqual(2, len(commands))
        self.assertEqual("check", commands[0][2])
        self.assertIn("--source", commands[0])
        self.assertIn("review", commands[0])
        self.assertEqual("word", commands[1][2])
        self.assertIn("--source", commands[1])
        self.assertIn("review", commands[1])
        self.assertIn("--no-clean", commands[1])

    def test_build_document_for_task_should_build_from_git_ref_and_stage_output_under_host_repo(self) -> None:
        commands: list[tuple[list[str], Path]] = []
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            worktree = root / ".tmp" / "process-build-queue-worktrees" / "codex-review-us-en"
            host_config_path = root / "config.us-en.yaml"
            worktree_config_path = worktree / "config.us-en.yaml"
            worktree_word_path = worktree / "docs" / "_build" / "JE-1000F" / "US" / "en" / "word" / "manual_je1000f_us_en.docx"
            worktree_html_dir = worktree / "docs" / "_build" / "JE-1000F" / "US" / "en" / "html"
            host_config_path.write_text("build: {}\n", encoding="utf-8")
            worktree_config_path.parent.mkdir(parents=True, exist_ok=True)
            worktree_config_path.write_text("build: {}\n", encoding="utf-8")
            worktree_word_path.parent.mkdir(parents=True, exist_ok=True)
            worktree_word_path.write_bytes(b"docx")
            worktree_html_dir.mkdir(parents=True, exist_ok=True)
            (worktree_html_dir / "index.html").write_text("<html>published</html>\n", encoding="utf-8")

            with mock.patch.object(process_build_queue, "ROOT", root), mock.patch.object(
                process_build_queue,
                "_prepare_git_ref_worktree",
                return_value=worktree,
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
                return_value=worktree_word_path,
            ), mock.patch.object(
                process_build_queue,
                "resolve_html_output_dir_for_target",
                return_value=worktree_html_dir,
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
                self.assertTrue(resolved_path.exists())

        self.assertEqual(
            root / "reports" / "releases" / "JE-1000F" / "US" / "en" / "versions" / "0.2" / "manual_je1000f_us_en_publish_0.2.docx",
            resolved_path,
        )
        self.assertEqual(2, len(commands))
        self.assertEqual("publish", commands[0][0][2])
        self.assertEqual(worktree, commands[0][1])
        self.assertEqual("html", commands[1][0][2])
        self.assertEqual(worktree, commands[1][1])
        prepare_mock.assert_called_once_with("codex/review-us-en")
        remove_mock.assert_called_once_with(worktree)

    def test_build_document_for_task_should_use_publish_action_for_publish_phase(self) -> None:
        commands: list[list[str]] = []
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_path = root / "config.ja.yaml"
            word_path = root / "docs" / "_build" / "JE-1000F" / "JP" / "word" / "manual_je1000f_jp.docx"
            html_dir = root / "docs" / "_build" / "JE-1000F" / "JP" / "html"
            config_path.write_text("build:\n  languages: [ja]\n", encoding="utf-8")
            word_path.parent.mkdir(parents=True, exist_ok=True)
            word_path.write_bytes(b"docx")
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
                self.assertTrue(resolved_path.exists())

        self.assertEqual(
            root / "reports" / "releases" / "JE-1000F" / "JP" / "ja" / "versions" / "1.0" / "manual_je1000f_jp_publish_1.0.docx",
            resolved_path,
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
            html_dir = root / "reports" / "releases" / "JE-1000F" / "US" / "en" / "latest" / "html"
            word_output_path.parent.mkdir(parents=True, exist_ok=True)
            html_dir.mkdir(parents=True, exist_ok=True)
            word_output_path.write_bytes(b"docx")
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
                    html_dir=html_dir,
                    document_link_url="https://example.feishu.cn/wiki/token_123",
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
                "reports/releases/JE-1000F/US/en/latest/html/index.html",
                payload["html_index"],
            )

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
                return_value=Path("config.us-en.yaml"),
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
            config_path=Path("config.us-en.yaml"),
            model="JE-1000F",
            region="US",
            data_root="data/phase2",
            doc_phase="draft",
            version="1.0",
            git_ref="codex/review-je-1000f-us-en",
        )
        sync_mock.assert_not_called()

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
                return_value=Path("config.ja.yaml"),
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
                    config_path=Path("config.ja.yaml"),
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
            return_value=Path("config.ja.yaml"),
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
            return_value=Path("config.us-en.yaml"),
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
                    config_path=Path("config.us.yaml"),
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
            config_path=(process_build_queue.ROOT / "config.us.yaml"),
            model="JE-1000F",
            region="US",
            data_root="data/phase2",
            doc_phase="draft",
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
                "_phase2_identity",
                return_value="user",
            ):
                exit_code = process_build_queue.process_build_queue(
                    cfg=cfg,
                    config_path=Path("config.us.yaml"),
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
                "_phase2_identity",
                return_value="user",
            ):
                exit_code = process_build_queue.process_build_queue(
                    cfg=cfg,
                    config_path=Path("config.us.yaml"),
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
                    config_path=Path("config.us.yaml"),
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
