from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

from tools import process_build_queue


class TestProcessBuildQueue(unittest.TestCase):
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
                        process_build_queue.DOC_PHASE_FIELD: ["Draft"],
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
        self.assertEqual("Draft", records[0].doc_phase)

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
            trigger_value="Y",
            immediate_trigger_value=False,
        )

        model, region = process_build_queue.resolve_target_for_record(record)

        self.assertEqual("JE-1000F", model)
        self.assertEqual("US", region)

    def test_resolve_config_path_for_task_should_prefer_lang_specific_config(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name in ("config.yaml", "config.us-en.yaml", "config.us-fr.yaml"):
                (root / name).write_text("build: {}\n", encoding="utf-8")

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
                doc_phase="Draft",
            )

        self.assertEqual(
            word_path.resolve(strict=False).as_posix(),
            fields[process_build_queue.DOCUMENT_DIRECTORY_FIELD],
        )
        self.assertEqual(drive_url, fields[process_build_queue.DOCUMENT_LINK_FIELD])
        self.assertEqual(["已构建"], fields[process_build_queue.TRIGGER_FIELD])
        self.assertFalse(fields[process_build_queue.IMMEDIATE_TRIGGER_FIELD])
        self.assertIn("SUCCESS", fields[process_build_queue.RESULT_FIELD])
        self.assertIn("doc_phase=draft", fields[process_build_queue.RESULT_FIELD])
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
                doc_phase="Publish",
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
        self.assertFalse(fields[process_build_queue.IMMEDIATE_TRIGGER_FIELD])
        self.assertIn("FAILED", fields[process_build_queue.RESULT_FIELD])
        self.assertIn("doc_phase=publish", fields[process_build_queue.RESULT_FIELD])
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
                        process_build_queue.DOC_PHASE_FIELD: ["Draft"],
                        process_build_queue.TRIGGER_FIELD: ["Y"],
                        process_build_queue.IMMEDIATE_TRIGGER_FIELD: False,
                    },
                },
            ]
        )

        self.assertEqual(["rec_immediate"], [record.record_id for record in records])

    def test_select_pending_queue_records_should_filter_by_doc_phase(self) -> None:
        records = process_build_queue.select_pending_queue_records(
            [
                {
                    "record_id": "rec_draft",
                    "fields": {
                        process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_en_1.0",
                        process_build_queue.DOCUMENT_KEY_FIELD: "JE-1000F_US",
                        process_build_queue.VERSION_FIELD: ["1.0"],
                        process_build_queue.LANG_FIELD: ["en"],
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
                        process_build_queue.DOC_PHASE_FIELD: ["Publish"],
                        process_build_queue.TRIGGER_FIELD: ["Y"],
                        process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    },
                },
            ],
            doc_phase="draft",
        )

        self.assertEqual(["rec_draft"], [record.record_id for record in records])

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
        self.assertEqual("publish", process_build_queue.normalize_doc_phase("Publish"))
        self.assertIsNone(process_build_queue.normalize_doc_phase(""))

    def test_normalize_doc_phase_should_reject_unknown_value(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "Doc_phase must be Draft or Publish"):
            process_build_queue.normalize_doc_phase("staging")

    def test_build_document_for_task_should_use_review_source_for_draft_phase(self) -> None:
        commands: list[list[str]] = []
        with tempfile.TemporaryDirectory() as td:
            word_path = Path(td) / "docs" / "_build" / "JE-1000F" / "US" / "en" / "word" / "manual_je1000f_us_en.docx"
            word_path.parent.mkdir(parents=True, exist_ok=True)
            word_path.write_bytes(b"docx")

            with mock.patch.object(process_build_queue, "_run_command", side_effect=lambda cmd: commands.append(cmd)), mock.patch.object(
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
                )

        self.assertEqual(word_path, resolved_path)
        self.assertEqual(2, len(commands))
        self.assertEqual("check", commands[0][2])
        self.assertIn("--source", commands[0])
        self.assertIn("review", commands[0])
        self.assertEqual("word", commands[1][2])
        self.assertIn("--source", commands[1])
        self.assertIn("review", commands[1])
        self.assertIn("--no-clean", commands[1])

    def test_build_document_for_task_should_use_publish_action_for_publish_phase(self) -> None:
        commands: list[list[str]] = []
        with tempfile.TemporaryDirectory() as td:
            word_path = Path(td) / "docs" / "_build" / "JE-1000F" / "JP" / "word" / "manual_je1000f_jp.docx"
            word_path.parent.mkdir(parents=True, exist_ok=True)
            word_path.write_bytes(b"docx")

            with mock.patch.object(process_build_queue, "_run_command", side_effect=lambda cmd: commands.append(cmd)), mock.patch.object(
                process_build_queue,
                "resolve_word_output_path_for_target",
                return_value=word_path,
            ):
                resolved_path = process_build_queue.build_document_for_task(
                    config_path=Path("config.ja.yaml"),
                    model="JE-1000F",
                    region="JP",
                    data_root="data/phase2",
                    doc_phase="Publish",
                )

        self.assertEqual(word_path, resolved_path)
        self.assertEqual(1, len(commands))
        self.assertEqual("publish", commands[0][2])
        self.assertIn("--data-root", commands[0])

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
                    process_build_queue.DOC_PHASE_FIELD: ["Draft"],
                    process_build_queue.BUILD_STARTED_AT_FIELD: None,
                    process_build_queue.TRIGGER_FIELD: ["Y"],
                    process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                },
            }
        ]
        captured_upserts: list[dict[str, object]] = []
        with tempfile.TemporaryDirectory() as td:
            generated_path = (
                Path(td) / "docs" / "_build" / "JE-1000F" / "US" / "en" / "word" / "manual_je1000f_us_en.docx"
            )
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
        self.assertIn("doc_phase=draft", record_payload[process_build_queue.RESULT_FIELD])
        build_document_mock.assert_called_once_with(
            config_path=Path("config.us-en.yaml"),
            model="JE-1000F",
            region="US",
            data_root="data/phase2",
            doc_phase="draft",
        )

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
                    process_build_queue.DOC_PHASE_FIELD: ["Publish"],
                    process_build_queue.BUILD_STARTED_AT_FIELD: None,
                    process_build_queue.TRIGGER_FIELD: ["Y"],
                    process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                },
            }
        ]
        captured_upserts: list[dict[str, object]] = []
        with tempfile.TemporaryDirectory() as td:
            generated_path = Path(td) / "docs" / "_build" / "JE-1000F" / "JP" / "word" / "manual_je1000f_jp.docx"
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

        self.assertEqual(1, exit_code)
        self.assertEqual(2, len(captured_upserts))
        failure_payload = captured_upserts[1]["record"]
        self.assertIsInstance(failure_payload, dict)
        self.assertEqual(
            generated_path.resolve(strict=False).as_posix(),
            failure_payload[process_build_queue.DOCUMENT_DIRECTORY_FIELD],
        )
        self.assertEqual(
            "https://test-degwga5x6ex8.feishu.cn/file/file_token_123",
            failure_payload[process_build_queue.DOCUMENT_LINK_FIELD],
        )
        self.assertFalse(failure_payload[process_build_queue.IMMEDIATE_TRIGGER_FIELD])
        self.assertIn("FAILED", failure_payload[process_build_queue.RESULT_FIELD])
        self.assertIn("latest_drive_link_preserved", failure_payload[process_build_queue.RESULT_FIELD])
        self.assertIn("Permission denied [99991679]", failure_payload[process_build_queue.RESULT_FIELD])

    def test_process_build_queue_should_sync_phase2_snapshot_before_building(self) -> None:
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
                    process_build_queue.DOC_PHASE_FIELD: ["Draft"],
                    process_build_queue.BUILD_STARTED_AT_FIELD: None,
                    process_build_queue.TRIGGER_FIELD: ["Y"],
                    process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
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
        self.assertEqual(2, len(fetch_calls))
        build_document_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
