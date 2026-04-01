from __future__ import annotations

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


class TestSyncData(unittest.TestCase):
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

            manifest = json.loads((root / "data" / "phase2" / "snapshot_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(["spec_titles", "spec_master"], manifest["requested_tables"])
            self.assertIn("spec_footnotes", manifest["skipped_tables"])
            self.assertEqual(2, len(manifest["tables"]))

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
            self.assertFalse((root / "data" / "phase2" / "snapshot_manifest.json").exists())

    def test_lark_cli_source_should_paginate_records(self) -> None:
        source = sync_data.LarkCliSource(cli_bin="lark-cli")
        payloads = [
            json.dumps(
                {
                    "code": 0,
                    "data": {
                        "items": [{"fields": {"title_en": "A"}}],
                        "has_more": True,
                        "page_token": "next-token",
                    },
                }
            ),
            json.dumps(
                {
                    "code": 0,
                    "data": {
                        "items": [{"fields": {"title_en": "B"}}],
                        "has_more": False,
                    },
                }
            ),
        ]
        seen_commands: list[list[str]] = []

        def fake_run(cmd: list[str], **_: object) -> mock.Mock:
            seen_commands.append(cmd)
            return mock.Mock(stdout=payloads.pop(0))

        with mock.patch("tools.sync_data.subprocess.run", side_effect=fake_run):
            rows = source.fetch_records(
                base_token="app_token",
                table_id="tbl_titles",
                view_id="view_titles",
            )

        self.assertEqual(2, len(rows))
        self.assertEqual(2, len(seen_commands))
        self.assertEqual("api", seen_commands[0][1])
        self.assertEqual("GET", seen_commands[0][2])
        self.assertIn("/open-apis/bitable/v1/apps/app_token/tables/tbl_titles/records", seen_commands[0])
        self.assertIn("--params", seen_commands[0])
        self.assertIn("next-token", seen_commands[1][-1])


if __name__ == "__main__":
    unittest.main()
