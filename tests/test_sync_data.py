from __future__ import annotations

import csv
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from tools import sync_data


class _FakeSource:
    def __init__(self, records_by_table: dict[str, list[dict[str, object]]]) -> None:
        self.records_by_table = records_by_table
        self.calls: list[tuple[str, str, str | None]] = []

    def fetch_records(
        self,
        *,
        base_token: str,
        table_id: str,
        view_id: str | None,
    ) -> list[dict[str, object]]:
        self.calls.append((base_token, table_id, view_id))
        return list(self.records_by_table[table_id])


class _FakeSourceWithIds(_FakeSource):
    def __init__(
        self,
        records_by_table: dict[str, list[dict[str, object]]],
        records_with_ids_by_table: dict[str, list[dict[str, object]]],
    ) -> None:
        super().__init__(records_by_table)
        self.records_with_ids_by_table = records_with_ids_by_table
        self.calls_with_ids: list[tuple[str, str, str | None]] = []

    def fetch_records_with_ids(
        self,
        *,
        base_token: str,
        table_id: str,
        view_id: str | None,
    ) -> list[dict[str, object]]:
        self.calls_with_ids.append((base_token, table_id, view_id))
        return list(self.records_with_ids_by_table[table_id])


class TestSyncData(unittest.TestCase):
    def test_collect_sync_preflight_errors_should_report_missing_cli_and_envs_together(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "cli_bin": "lark-cli",
                    "base_token_env": "BASE_TOKEN",
                    "tables": {
                        "spec_titles": {
                            "table_id_env": "SPEC_TITLES_TABLE",
                            "view_id_env": "SPEC_TITLES_VIEW",
                        },
                    },
                }
            }
        }

        with mock.patch("tools.sync_data.shutil.which", return_value=None):
            errors = sync_data.collect_sync_preflight_errors(
                cfg,
                table_names=["spec_titles"],
                environ={},
                require_cli=True,
            )

        self.assertEqual(
            [
                "sync.phase2.cli_bin executable is not available: lark-cli",
                "Required environment variables are not set: BASE_TOKEN, SPEC_TITLES_TABLE, SPEC_TITLES_VIEW",
            ],
            errors,
        )

    def test_sync_phase2_snapshot_should_write_csvs_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = {
                "sync": {
                    "phase2": {
                        "provider": "lark_cli",
                        "base_token_env": "BASE_TOKEN",
                        "tables": {
                            "spec_titles": {
                                "table_id_env": "SPEC_TITLES_TABLE",
                                "view_id_env": "SPEC_TITLES_VIEW",
                            },
                            "spec_master": {
                                "table_id_env": "SPEC_MASTER_TABLE",
                            },
                        },
                    }
                }
            }
            config_path = root / "config.yaml"
            config_path.write_text("sync: {}\n", encoding="utf-8")

            fake_source = _FakeSource(
                {
                    "tbl_titles": [
                        {"fields": {"title_en": "B", "section_order": 2, "title_fr": "B FR"}},
                        {"fields": {"title_en": "A", "section_order": 1, "title_fr": "A FR"}},
                    ],
                    "tbl_master": [
                        {
                            "fields": {
                                "document_key": "JE-1000F_US_en",
                                "Region": "US",
                                "Is_Latest": True,
                                "Page": "specifications",
                                "Section": "GENERAL INFO",
                                "Section_order": 1,
                                "Row_order": 2,
                                "Row_key": "model_no",
                                "Slot_key": "[front.label](front.label)",
                                "Row_label_source": "Model No.",
                                "Line_order": 1,
                                "Value_source": "JE-1000F",
                                "Model": "JE-1000F",
                                "Source_lang": "en",
                            }
                        },
                        {
                            "fields": {
                                "document_key": "JE-1000F_US_en",
                                "Region": "US",
                                "Is_Latest": "true",
                                "Page": "specifications",
                                "Section": "GENERAL INFO",
                                "Section_order": 1,
                                "Row_order": 1,
                                "Row_key": "product_name",
                                "Row_label_source": "Product Name",
                                "Line_order": 1,
                                "Value_source": "Jackery Explorer 1000 Pro",
                                "Model": "JE-1000F",
                                "Source_lang": "en",
                            }
                        },
                    ],
                }
            )

            with mock.patch.dict(
                "os.environ",
                {
                    "BASE_TOKEN": "app_token",
                    "SPEC_TITLES_TABLE": "tbl_titles",
                    "SPEC_TITLES_VIEW": "view_titles",
                    "SPEC_MASTER_TABLE": "tbl_master",
                },
                clear=False,
            ), mock.patch.object(sync_data, "ROOT", root):
                result = sync_data.sync_phase2_snapshot(
                    cfg=cfg,
                    config_path=config_path,
                    data_root="data/phase2",
                    table_names=["spec_titles", "spec_master"],
                    dry_run=False,
                    source=fake_source,
                    built_at=datetime(2026, 3, 31, 9, 0, tzinfo=timezone.utc),
                )

            self.assertEqual(root / "data" / "phase2", result.export_root)
            self.assertTrue((root / "data" / "phase2" / "spec_titles.csv").exists())
            self.assertTrue((root / "data" / "phase2" / "Spec_Master.csv").exists())
            self.assertTrue((root / "data" / "phase2" / "row_key_mapping.csv").exists())
            self.assertTrue((root / "data" / "phase2" / "snapshot_manifest.json").exists())
            self.assertEqual(
                [
                    ("app_token", "tbl_titles", "view_titles"),
                    ("app_token", "tbl_master", None),
                ],
                fake_source.calls,
            )

            titles_lines = (root / "data" / "phase2" / "spec_titles.csv").read_text(encoding="utf-8").splitlines()
            self.assertEqual("title_en,section_order,title_zh,title_jp,title_fr,title_es", titles_lines[0])
            self.assertTrue(titles_lines[1].startswith("A,1"))
            self.assertTrue(titles_lines[2].startswith("B,2"))

            master_lines = (root / "data" / "phase2" / "Spec_Master.csv").read_text(encoding="utf-8").splitlines()
            self.assertIn("TRUE", master_lines[1])
            self.assertIn("product_name", master_lines[1])
            self.assertIn("model_no", master_lines[2])
            self.assertIn("front.label", master_lines[2])

            mapping_lines = (root / "data" / "phase2" / "row_key_mapping.csv").read_text(encoding="utf-8-sig").splitlines()
            self.assertEqual("Row_label_source,Line_order,Row_key,Remark", mapping_lines[0])
            self.assertIn("Product Name,1,product_name,", mapping_lines)
            self.assertIn("Model No.,1,model_no,", mapping_lines)

            manifest = json.loads((root / "data" / "phase2" / "snapshot_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(["spec_titles", "spec_master"], manifest["requested_tables"])
            self.assertIn("spec_footnotes", manifest["skipped_tables"])
            self.assertEqual(2, len(manifest["tables"]))
            self.assertEqual(1, len(manifest["derived_files"]))
            self.assertEqual("row_key_mapping", manifest["derived_files"][0]["logical_name"])

    def test_sync_phase2_snapshot_should_not_write_files_in_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = {
                "sync": {
                    "phase2": {
                        "provider": "lark_cli",
                        "base_token_env": "BASE_TOKEN",
                        "tables": {
                            "spec_titles": {
                                "table_id_env": "SPEC_TITLES_TABLE",
                            },
                        },
                    }
                }
            }
            fake_source = _FakeSource({"tbl_titles": [{"fields": {"title_en": "SPECIFICATIONS"}}]})

            with mock.patch.dict(
                "os.environ",
                {
                    "BASE_TOKEN": "app_token",
                    "SPEC_TITLES_TABLE": "tbl_titles",
                },
                clear=False,
            ), mock.patch.object(sync_data, "ROOT", root):
                result = sync_data.sync_phase2_snapshot(
                    cfg=cfg,
                    config_path=root / "config.yaml",
                    data_root="data/phase2",
                    table_names=["spec_titles"],
                    dry_run=True,
                    source=fake_source,
                )

            self.assertTrue(result.dry_run)
            self.assertFalse((root / "data" / "phase2" / "spec_titles.csv").exists())
            self.assertFalse((root / "data" / "phase2" / "row_key_mapping.csv").exists())
            self.assertFalse((root / "data" / "phase2" / "snapshot_manifest.json").exists())

    def test_sync_phase2_snapshot_should_seed_phase2_row_key_mapping_from_phase1_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = {
                "sync": {
                    "phase2": {
                        "provider": "lark_cli",
                        "base_token_env": "BASE_TOKEN",
                        "tables": {
                            "spec_master": {
                                "table_id_env": "SPEC_MASTER_TABLE",
                            },
                        },
                    }
                }
            }
            config_path = root / "config.yaml"
            config_path.write_text("sync: {}\n", encoding="utf-8")
            phase1_dir = root / "data" / "phase1"
            phase1_dir.mkdir(parents=True, exist_ok=True)
            (phase1_dir / "row_key_mapping.csv").write_text(
                "Row_label_source,Line_order,Row_key,Remark\n"
                "Product Name,1,product_name,keep existing remark\n",
                encoding="utf-8-sig",
            )

            fake_source = _FakeSource(
                {
                    "tbl_master": [
                        {
                            "fields": {
                                "document_key": "JE-1000F_US_en",
                                "Region": "US",
                                "Is_Latest": True,
                                "Page": "specifications",
                                "Section": "GENERAL INFO",
                                "Section_order": 1,
                                "Row_order": 1,
                                "Row_key": "product_name",
                                "Line_order": 1,
                                "Row_label_source": "Product Name",
                                "Value_source": "Jackery Explorer 1000 Pro",
                                "Model": "JE-1000F",
                                "Source_lang": "en",
                            }
                        },
                    ],
                }
            )

            with mock.patch.dict(
                "os.environ",
                {
                    "BASE_TOKEN": "app_token",
                    "SPEC_MASTER_TABLE": "tbl_master",
                },
                clear=False,
            ), mock.patch.object(sync_data, "ROOT", root):
                result = sync_data.sync_phase2_snapshot(
                    cfg=cfg,
                    config_path=config_path,
                    data_root="data/phase2",
                    table_names=["spec_master"],
                    dry_run=False,
                    source=fake_source,
                    built_at=datetime(2026, 3, 31, 9, 0, tzinfo=timezone.utc),
                )

            mapping_text = (root / "data" / "phase2" / "row_key_mapping.csv").read_text(encoding="utf-8-sig")
            self.assertIn("Product Name,1,product_name,keep existing remark", mapping_text)
            self.assertEqual(1, len(result.derived_files))
            self.assertEqual("row_key_mapping", result.derived_files[0].logical_name)

    def test_sync_phase2_snapshot_should_normalize_feishu_link_refs_without_changing_latest_rows(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = {
                "sync": {
                    "phase2": {
                        "provider": "lark_cli",
                        "base_token_env": "BASE_TOKEN",
                        "tables": {
                            "spec_footnotes": {
                                "table_id_env": "SPEC_FOOTNOTES_TABLE",
                            },
                            "spec_master": {
                                "table_id_env": "SPEC_MASTER_TABLE",
                            },
                        },
                    }
                }
            }
            config_path = root / "config.yaml"
            config_path.write_text("sync: {}\n", encoding="utf-8")

            footnote_fields = {
                "Footnote_id": "ac_bypass",
                "Region": "US",
                "Model": "JE-1000F",
                "Source_lang": "en",
                "Is_Latest": True,
                "Page": "specifications",
                "Footnote_order": 1,
                "Text_en": "Bypass footnote",
                "Enabled": True,
            }
            fake_source = _FakeSourceWithIds(
                records_by_table={
                    "tbl_footnotes": [{"fields": footnote_fields}],
                    "tbl_master": [
                        {
                            "fields": {
                                "document_key": "JE-1000F_US",
                                "Region": "US",
                                "Is_Latest": False,
                                "Page": "ups_mode",
                                "Section": "OUTPUT PORTS",
                                "Section_order": 3,
                                "Row_order": 1,
                                "Row_key": "ups_bypass_output",
                                "Slot_key": "text",
                                "Row_label_source": "UPS Bypass Output",
                                "Line_order": 1,
                                "Value_source": "1500W",
                                "Model": "JE-1000F",
                                "Source_lang": "en",
                            }
                        },
                        {
                            "fields": {
                                "document_key": "JE-1000F_US",
                                "Region": "US",
                                "Is_Latest": True,
                                "Page": "ups_mode",
                                "Section": "OUTPUT PORTS",
                                "Section_order": 3,
                                "Row_order": 1,
                                "Row_key": "ups_bypass_output",
                                "Slot_key": "text",
                                "Row_label_source": "UPS Bypass Output",
                                "Line_order": 1,
                                "Value_source": "12A (1440W)",
                                "Model": "JE-2000E",
                                "Source_lang": "en",
                            }
                        },
                        {
                            "fields": {
                                "document_key": "JE-1000F_US",
                                "Region": "US",
                                "Is_Latest": True,
                                "Page": "specifications",
                                "Section": "INPUT PORTS",
                                "Section_order": 2,
                                "Row_order": 1,
                                "Row_key": "ac_input",
                                "Slot_key": "",
                                "Row_label_source": "1 x AC Input",
                                "Line_order": 1,
                                "Param_source": "Bypass Mode",
                                "Param_footnote_refs": {"id": "rec_ac_bypass"},
                                "Value_source": "100V-120V~60Hz, 12A Max",
                                "Model": "JE-1000F",
                                "Source_lang": "en",
                            }
                        },
                    ],
                },
                records_with_ids_by_table={
                    "tbl_footnotes": [{"record_id": "rec_ac_bypass", "fields": footnote_fields}],
                },
            )

            with mock.patch.dict(
                "os.environ",
                {
                    "BASE_TOKEN": "app_token",
                    "SPEC_FOOTNOTES_TABLE": "tbl_footnotes",
                    "SPEC_MASTER_TABLE": "tbl_master",
                },
                clear=False,
            ), mock.patch.object(sync_data, "ROOT", root):
                sync_data.sync_phase2_snapshot(
                    cfg=cfg,
                    config_path=config_path,
                    data_root="data/phase2",
                    table_names=["spec_footnotes", "spec_master"],
                    dry_run=False,
                    source=fake_source,
                    built_at=datetime(2026, 3, 31, 9, 0, tzinfo=timezone.utc),
                )

            with (root / "data" / "phase2" / "Spec_Master.csv").open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual([("app_token", "tbl_footnotes", None)], fake_source.calls_with_ids)

            ac_input_row = next(row for row in rows if row["Row_key"] == "ac_input")
            self.assertEqual("ac_bypass", ac_input_row["Param_footnote_refs"])

            latest_rows = [row for row in rows if row["Row_key"] == "ups_bypass_output"]
            self.assertEqual(
                [("JE-1000F", "FALSE", "1500W"), ("JE-2000E", "TRUE", "12A (1440W)")],
                [(row["Model"], row["Is_Latest"], row["Value_source"]) for row in latest_rows],
            )

    def test_sync_phase2_snapshot_should_fail_with_aggregated_preflight_errors(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "cli_bin": "lark-cli",
                    "base_token_env": "BASE_TOKEN",
                    "tables": {
                        "spec_titles": {
                            "table_id_env": "SPEC_TITLES_TABLE",
                            "view_id_env": "SPEC_TITLES_VIEW",
                        },
                    },
                }
            }
        }

        with mock.patch.dict("os.environ", {}, clear=True), mock.patch(
            "tools.sync_data.shutil.which",
            return_value=None,
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "sync-data preflight failed:",
            ) as exc_info:
                sync_data.sync_phase2_snapshot(
                    cfg=cfg,
                    config_path=Path("config.yaml"),
                    data_root="data/phase2",
                    table_names=["spec_titles"],
                    dry_run=True,
                    source=None,
                )

        message = str(exc_info.exception)
        self.assertIn("sync.phase2.cli_bin executable is not available: lark-cli", message)
        self.assertIn(
            "Required environment variables are not set: BASE_TOKEN, SPEC_TITLES_TABLE, SPEC_TITLES_VIEW",
            message,
        )

    def test_resolved_cli_command_parts_should_use_absolute_path_from_which(self) -> None:
        with mock.patch(
            "tools.sync_data.shutil.which",
            return_value=r"C:\Users\tangxb\AppData\Roaming\npm\lark-cli.cmd",
        ):
            parts = sync_data._resolved_cli_command_parts("lark-cli")

        self.assertEqual([r"C:\Users\tangxb\AppData\Roaming\npm\lark-cli.cmd"], parts)

    def test_normalized_cell_should_strip_markdown_wrapper_from_slot_key(self) -> None:
        value = sync_data._normalized_cell(
            sync_data.TABLE_SCHEMAS["spec_master"],
            "Slot_key",
            "[front.label](front.label)",
        )

        self.assertEqual("front.label", value)

    def test_lark_cli_source_should_paginate_records(self) -> None:
        source = sync_data.LarkCliSource(cli_bin="lark-cli")
        payloads = [
            json.dumps(
                {
                    "data": {
                        "items": [
                            {"field_id": "fld_title_en", "field_name": "title_en"},
                        ],
                        "total": 1,
                    },
                    "ok": True,
                }
            ),
            json.dumps(
                {
                    "data": {
                        "field_id_list": ["fld_title_en"],
                        "fields": ["title_en"],
                        "data": [["A"]],
                        "has_more": True,
                    },
                    "ok": True,
                }
            ),
            json.dumps(
                {
                    "data": {
                        "field_id_list": ["fld_title_en"],
                        "fields": ["title_en"],
                        "data": [["B"]],
                        "has_more": False,
                    },
                    "ok": True,
                }
            ),
        ]
        seen_commands: list[list[str]] = []

        def fake_run(cmd: list[str], **_: object) -> mock.Mock:
            seen_commands.append(cmd)
            return mock.Mock(stdout=payloads.pop(0))

        with mock.patch(
            "tools.sync_data.shutil.which",
            return_value=r"C:\Users\tangxb\AppData\Roaming\npm\lark-cli.cmd",
        ), mock.patch("tools.sync_data.subprocess.run", side_effect=fake_run):
            rows = source.fetch_records(
                base_token="app_token",
                table_id="tbl_titles",
                view_id="view_titles",
            )

        self.assertEqual(2, len(rows))
        self.assertEqual(3, len(seen_commands))
        self.assertEqual([{"fields": {"title_en": "A"}}, {"fields": {"title_en": "B"}}], rows)
        self.assertEqual(r"C:\Users\tangxb\AppData\Roaming\npm\lark-cli.cmd", seen_commands[0][0])
        self.assertEqual("base", seen_commands[0][1])
        self.assertEqual("+field-list", seen_commands[0][2])
        self.assertEqual("+record-list", seen_commands[1][2])
        self.assertIn("--base-token", seen_commands[1])
        self.assertIn("app_token", seen_commands[1])
        self.assertIn("--table-id", seen_commands[1])
        self.assertIn("tbl_titles", seen_commands[1])
        self.assertIn("--view-id", seen_commands[1])
        self.assertIn("view_titles", seen_commands[1])
        self.assertIn("--offset", seen_commands[2])
        self.assertIn("1", seen_commands[2])

    def test_lark_cli_source_should_expand_truncated_field_names_via_field_ids(self) -> None:
        source = sync_data.LarkCliSource(cli_bin="lark-cli")
        payloads = [
            json.dumps(
                {
                    "data": {
                        "items": [
                            {
                                "field_id": "fld_row_label_refs",
                                "field_name": "Row_label_footnote_refs",
                            },
                            {"field_id": "fld_row_key", "field_name": "Row_key"},
                        ],
                        "total": 2,
                    },
                    "ok": True,
                }
            ),
            json.dumps(
                {
                    "data": {
                        "field_id_list": ["fld_row_label_refs", "fld_row_key"],
                        "fields": ["Row_label_footnote_r...", "Row_key"],
                        "data": [["ac_bypass", "ac_output_bypass"]],
                        "has_more": False,
                    },
                    "ok": True,
                }
            ),
        ]

        def fake_run(_: list[str], **__: object) -> mock.Mock:
            return mock.Mock(stdout=payloads.pop(0))

        with mock.patch(
            "tools.sync_data.shutil.which",
            return_value=r"C:\Users\tangxb\AppData\Roaming\npm\lark-cli.cmd",
        ), mock.patch("tools.sync_data.subprocess.run", side_effect=fake_run):
            rows = source.fetch_records(
                base_token="app_token",
                table_id="tbl_master",
                view_id="view_master",
            )

        self.assertEqual(
            [{"fields": {"Row_label_footnote_refs": "ac_bypass", "Row_key": "ac_output_bypass"}}],
            rows,
        )

    def test_lark_cli_source_should_return_record_ids_when_requested(self) -> None:
        source = sync_data.LarkCliSource(cli_bin="lark-cli")
        payloads = [
            json.dumps(
                {
                    "data": {
                        "items": [
                            {"field_id": "fld_document_key", "field_name": "Document_Key"},
                        ],
                        "total": 1,
                    },
                    "ok": True,
                }
            ),
            json.dumps(
                {
                    "data": {
                        "field_id_list": ["fld_document_key"],
                        "fields": ["Document_Key"],
                        "data": [["JE-1000F_US"]],
                        "record_id_list": ["rec_document_link"],
                        "has_more": False,
                    },
                    "ok": True,
                }
            ),
        ]

        def fake_run(_: list[str], **__: object) -> mock.Mock:
            return mock.Mock(stdout=payloads.pop(0))

        with mock.patch(
            "tools.sync_data.shutil.which",
            return_value=r"C:\Users\tangxb\AppData\Roaming\npm\lark-cli.cmd",
        ), mock.patch("tools.sync_data.subprocess.run", side_effect=fake_run):
            rows = source.fetch_records_with_ids(
                base_token="app_token",
                table_id="tbl_document_link",
                view_id="view_document_link",
            )

        self.assertEqual(
            [{"record_id": "rec_document_link", "fields": {"Document_Key": "JE-1000F_US"}}],
            rows,
        )

    def test_lark_cli_source_should_send_record_upsert_payload(self) -> None:
        source = sync_data.LarkCliSource(cli_bin="lark-cli")
        seen_commands: list[list[str]] = []
        seen_payload_text: list[str] = []

        def fake_run(cmd: list[str], **_: object) -> mock.Mock:
            seen_commands.append(cmd)
            payload_arg = cmd[cmd.index("--json") + 1]
            self.assertTrue(payload_arg.startswith("@"))
            payload_path = sync_data.ROOT / payload_arg[1:]
            seen_payload_text.append(payload_path.read_text(encoding="utf-8"))
            return mock.Mock(stdout=json.dumps({"ok": True}))

        with mock.patch(
            "tools.sync_data.shutil.which",
            return_value=r"C:\Users\tangxb\AppData\Roaming\npm\lark-cli.cmd",
        ), mock.patch("tools.sync_data.subprocess.run", side_effect=fake_run):
            source.upsert_record(
                base_token="app_token",
                table_id="tbl_document_link",
                record_id="rec_document_link",
                record={"构建结果": "SUCCESS"},
            )

        self.assertEqual(r"C:\Users\tangxb\AppData\Roaming\npm\lark-cli.cmd", seen_commands[0][0])
        self.assertEqual("base", seen_commands[0][1])
        self.assertEqual("+record-upsert", seen_commands[0][2])
        self.assertIn("--record-id", seen_commands[0])
        self.assertIn("rec_document_link", seen_commands[0])
        self.assertIn("--json", seen_commands[0])
        self.assertEqual('{"构建结果":"SUCCESS"}', seen_payload_text[0])

    def test_lark_cli_source_should_use_configured_identity(self) -> None:
        source = sync_data.LarkCliSource(cli_bin="lark-cli", identity="bot")
        seen_commands: list[list[str]] = []

        def fake_run(cmd: list[str], **_: object) -> mock.Mock:
            seen_commands.append(cmd)
            return mock.Mock(
                stdout=json.dumps(
                    {
                        "data": {
                            "items": [{"field_id": "fld_document_key", "field_name": "Document_Key"}],
                            "total": 1,
                        },
                        "ok": True,
                    }
                )
            )

        with mock.patch(
            "tools.sync_data.shutil.which",
            return_value=r"C:\Users\tangxb\AppData\Roaming\npm\lark-cli.cmd",
        ), mock.patch("tools.sync_data.subprocess.run", side_effect=fake_run):
            source._field_name_map(base_token="app_token", table_id="tbl_document_link")

        self.assertIn("--as", seen_commands[0])
        self.assertIn("bot", seen_commands[0])


if __name__ == "__main__":
    unittest.main()
