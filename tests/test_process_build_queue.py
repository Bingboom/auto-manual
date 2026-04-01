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
                drive_url=drive_url,
                built_at=built_at,
            )

        self.assertEqual(
            word_path.resolve(strict=False).as_posix(),
            fields[process_build_queue.DOCUMENT_DIRECTORY_FIELD],
        )
        self.assertEqual(drive_url, fields[process_build_queue.DOCUMENT_LINK_FIELD])
        self.assertEqual(["已构建"], fields[process_build_queue.TRIGGER_FIELD])
        self.assertFalse(fields[process_build_queue.IMMEDIATE_TRIGGER_FIELD])
        self.assertIn("SUCCESS", fields[process_build_queue.RESULT_FIELD])
        self.assertIn("version=1.0", fields[process_build_queue.RESULT_FIELD])

    def test_build_started_fields_should_write_datetime_millis(self) -> None:
        started_at = datetime(2026, 4, 1, 14, 55, 6)

        fields = process_build_queue.build_started_fields(started_at=started_at)

        self.assertEqual(
            int(started_at.timestamp() * 1000),
            fields[process_build_queue.BUILD_STARTED_AT_FIELD],
        )

    def test_pending_queue_records_should_accept_immediate_checkbox(self) -> None:
        records = process_build_queue.pending_queue_records(
            [
                {
                    "record_id": "rec_immediate",
                    "fields": {
                        process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_en_1.0",
                        process_build_queue.DOCUMENT_KEY_FIELD: [{"id": "recvfw0zG4PzxS"}],
                        process_build_queue.VERSION_FIELD: ["1.0"],
                        process_build_queue.LANG_FIELD: ["en"],
                        process_build_queue.TRIGGER_FIELD: ["已构建"],
                        process_build_queue.IMMEDIATE_TRIGGER_FIELD: True,
                    },
                }
            ]
        )

        self.assertEqual(1, len(records))
        self.assertTrue(records[0].immediate_trigger_value)

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
                )

        self.assertEqual("file_token_123", file_token)
        self.assertEqual("https://test-degwga5x6ex8.feishu.cn/file/file_token_123", drive_url)
        self.assertEqual(2, len(observed_args))
        self.assertEqual(["drive", "+upload"], observed_args[0][:2])
        self.assertEqual(["drive", "metas", "batch_query"], observed_args[1][:3])
        self.assertFalse(Path(observed_args[0][5]).is_absolute())
        self.assertEqual("manual_je1000f_us_en.docx", observed_args[0][7])

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
            base_token="app_token",
            table_id="tbl_document_link",
            view_id="vew_document_link",
        )
        raw_records = [
            {
                "record_id": "rec_1",
                "fields": {
                    process_build_queue.DOCUMENT_ID_FIELD: "JE-1000F_US_en_1.0",
                    process_build_queue.DOCUMENT_KEY_FIELD: [{"id": "recvfw0zG4PzxS"}],
                    process_build_queue.VERSION_FIELD: ["1.0"],
                    process_build_queue.LANG_FIELD: ["en"],
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
                return_value=generated_path,
            ), mock.patch.object(
                process_build_queue,
                "upload_word_to_drive",
                return_value=("file_token_123", "https://test-degwga5x6ex8.feishu.cn/file/file_token_123"),
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
            "https://test-degwga5x6ex8.feishu.cn/file/file_token_123",
            record_payload[process_build_queue.DOCUMENT_LINK_FIELD],
        )
        self.assertFalse(record_payload[process_build_queue.IMMEDIATE_TRIGGER_FIELD])


if __name__ == "__main__":
    unittest.main()
