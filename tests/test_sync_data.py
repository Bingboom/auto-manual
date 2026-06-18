from __future__ import annotations

import csv
import io
import json
import subprocess
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
        if table_id in self.records_with_ids_by_table:
            return list(self.records_with_ids_by_table[table_id])
        return list(self.records_by_table.get(table_id, []))


class _FakeSourceWithDownloads(_FakeSource):
    def __init__(self, records_by_table: dict[str, list[dict[str, object]]]) -> None:
        super().__init__(records_by_table)
        self.downloads: list[tuple[str, Path, bool]] = []

    def download_drive_file(self, *, file_token: str, output_path: Path, overwrite: bool = False) -> None:
        self.downloads.append((file_token, output_path, overwrite))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake image")


class _FakeSourceWithFailingDownloads(_FakeSource):
    def __init__(self, records_by_table: dict[str, list[dict[str, object]]]) -> None:
        super().__init__(records_by_table)
        self.downloads: list[tuple[str, Path, bool]] = []

    def download_drive_file(self, *, file_token: str, output_path: Path, overwrite: bool = False) -> None:
        self.downloads.append((file_token, output_path, overwrite))
        raise RuntimeError("download failed")


def _write_page_registry(root: Path, relative_path: str = "data/phase2/page_registry.csv") -> Path:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "page_id,order,page_type,sku_scope,langs,template,content_query,asset_ref,enabled\n"
        "spec,20,csv_page,ALL,en,spec_template.rst,page_id=spec,,1\n",
        encoding="utf-8",
    )
    return path


class TestSyncData(unittest.TestCase):
    def test_phase2_table_schemas_should_include_eu_and_pt_br_columns(self) -> None:
        self.assertEqual(
            (
                "spec_row_key",
                "document_key",
                "Model",
                "Region",
                "Source_lang",
                "Version",
                "Is_Latest",
                "Page",
                "Section",
                "Section_order",
                "Row_order",
                "Row_key",
                "Slot_key",
                "Row_label_source",
                "Row_label_footnote_refs",
                "Line_order",
                "Param_source",
                "Param_footnote_refs",
                "Value_source",
                "Value_footnote_refs",
                "Row_label_fr",
                "Param_fr",
                "Value_fr",
                "Row_label_es",
                "Param_es",
                "Value_es",
                "Row_label_br",
                "Param_br",
                "Value_br",
                "Row_label_de",
                "Param_de",
                "Value_de",
                "Row_label_it",
                "Param_it",
                "Value_it",
                "Row_label_uk",
                "Param_uk",
                "Value_uk",
            ),
            sync_data.TABLE_SCHEMAS["spec_master"].columns,
        )
        self.assertEqual(
            (
                "Footnote_id",
                "Region",
                "Model",
                "Source_lang",
                "Is_Latest",
                "Page",
                "Footnote_order",
                "Type",
                "Text_en",
                "Text_fr",
                "Text_es",
                "Text_pt-BR",
                "pt-BR",
                "Text_ja",
                "Text_de",
                "Text_it",
                "Text_uk",
                "Enabled",
            ),
            sync_data.TABLE_SCHEMAS["spec_footnotes"].columns,
        )
        self.assertEqual(
            (
                "Note_id",
                "Region",
                "Model",
                "Source_lang",
                "Is_Latest",
                "Page",
                "Note_order",
                "Type",
                "Text_en",
                "Text_fr",
                "Text_es",
                "Text_pt-BR",
                "Text_ja",
                "Text_de",
                "Text_it",
                "Text_uk",
                "Enabled",
            ),
            sync_data.TABLE_SCHEMAS["spec_notes"].columns,
        )
        self.assertEqual(
            (
                "symbol_key",
                "Figure",
                "image_path",
                "label_en",
                "aliases_en",
                "text_en",
                "label_fr",
                "aliases_fr",
                "text_fr",
                "label_es",
                "aliases_es",
                "text_es",
                "label_pt-BR",
                "aliases_pt-BR",
                "text_pt-BR",
                "label_de",
                "aliases_de",
                "text_de",
                "label_it",
                "aliases_it",
                "text_it",
                "label_uk",
                "aliases_uk",
                "text_uk",
                "label_jp",
                "aliases_jp",
                "text_jp",
                "label_zh",
                "aliases_zh",
                "text_zh",
                "Is_Latest",
                "Market",
                "block_type",
                "order",
                "Model",
                "Source_lang",
                "notes",
            ),
            sync_data.TABLE_SCHEMAS["symbols_blocks"].columns,
        )
        self.assertEqual(
            (
                "No.",
                "Model",
                "Is_latest",
                "Version",
                "icon_en",
                "icon_zh",
                "icon_jp",
                "icon_fr",
                "icon_es",
                "icon_pt-BR",
                "icon_br",
                "icon_de",
                "icon_it",
                "icon_ukr",
                "icon_desc_en",
                "icon_desc_zh",
                "icon_desc_jp",
                "icon_desc_fr",
                "icon_desc_es",
                "icon_desc_pt-BR",
                "icon_desc_br",
                "icon_desc_de",
                "icon_desc_it",
                "icon_desc_ukr",
                "has_variables",
                "variable_keys",
                "figure",
                "render_preview_en",
            ),
            sync_data.TABLE_SCHEMAS["lcd_icons"].columns,
        )
        self.assertEqual(
            (
                "No.",
                "Model",
                "Region",
                "Is_latest",
                "Version",
                "error_code",
                "corrective_measures_en",
                "corrective_measures_fr",
                "corrective_measures_es",
                "corrective_measures_pt-BR",
                "corrective_measures_br",
                "corrective_measures_de",
                "corrective_measures_it",
                "corrective_measures_ukr",
                "corrective_measures_jp",
                "corrective_measures_zh",
                "render_preview_en",
            ),
            sync_data.TABLE_SCHEMAS["troubleshooting"].columns,
        )
        self.assertEqual(
            ("Variable_key", "Model_key", "Model", "Value", "is_default"),
            sync_data.TABLE_SCHEMAS["variable_defaults"].columns,
        )
        self.assertEqual(
            ("Variable_key", "lang", "source_value", "Value", "from_prefix", "to_prefix"),
            sync_data.TABLE_SCHEMAS["variable_lang_overrides"].columns,
        )
        self.assertEqual(
            (
                "copy_key",
                "page_id",
                "copy_type",
                "Market",
                "Model",
                "Source_lang",
                "Is_Latest",
                "Version",
                "source_text",
                "section_order",
                "notes",
            ),
            sync_data.TABLE_SCHEMAS["manual_copy_source"].columns,
        )

    def test_symbols_blocks_should_normalize_model_multiselect_cells(self) -> None:
        rows = sync_data.normalize_records(
            sync_data.TABLE_SCHEMAS["symbols_blocks"],
            [
                {
                    "fields": {
                        "page_id": "symbols",
                        "Market": [{"text": "US"}, {"text": "EU"}],
                        "Model": [{"text": "JE-1000F"}, {"text": "JE-2000E"}],
                        "block_type": "table_row",
                        "order": 1,
                    }
                }
            ],
        )

        self.assertEqual("US, EU", rows[0]["Market"])
        self.assertEqual("JE-1000F, JE-2000E", rows[0]["Model"])

    def test_troubleshooting_should_normalize_latest_flag_and_sort_by_region_model_no(self) -> None:
        rows = sync_data.normalize_records(
            sync_data.TABLE_SCHEMAS["troubleshooting"],
            [
                {
                    "fields": {
                        "No.": "10",
                        "Model": "JE-1000F",
                        "Region": "US",
                        "Is_latest": False,
                        "error_code": "FE",
                    }
                },
                {
                    "fields": {
                        "No.": "2",
                        "Model": "JE-1000F",
                        "Region": "EU",
                        "Is_latest": "yes",
                        "error_code": "F2",
                    }
                },
                {
                    "fields": {
                        "No.": "1",
                        "Model": "ALL",
                        "Region": "EU",
                        "Is_latest": True,
                        "error_code": "F1",
                    }
                },
            ],
        )

        self.assertEqual(
            [("EU", "ALL", "1", "TRUE"), ("EU", "JE-1000F", "2", "TRUE"), ("US", "JE-1000F", "10", "FALSE")],
            [(row["Region"], row["Model"], row["No."], row["Is_latest"]) for row in rows],
        )

    def test_spec_footnotes_should_alias_pt_br_field_name(self) -> None:
        rows = sync_data.normalize_records(
            sync_data.TABLE_SCHEMAS["spec_footnotes"],
            [
                {
                    "fields": {
                        "Footnote_id": "fn1",
                        "Text_en": "English footnote.",
                        "pt-BR": "Nota em portugues.",
                    }
                }
            ],
        )

        self.assertEqual("Nota em portugues.", rows[0]["Text_pt-BR"])

    def test_collect_sync_preflight_errors_should_report_missing_cli_and_envs_together(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "cli_bin": "lark-cli",
                    "base_token_env": "BASE_TOKEN",
                    "tables": {
                        "spec_footnotes": {
                            "table_id_env": "SPEC_FOOTNOTES_TABLE",
                            "view_id_env": "SPEC_FOOTNOTES_VIEW",
                        },
                    },
                }
            }
        }

        with mock.patch("tools.sync_data.shutil.which", return_value=None):
            errors = sync_data.collect_sync_preflight_errors(
                cfg,
                table_names=["spec_footnotes"],
                environ={},
                require_cli=True,
            )

        self.assertEqual(
            [
                "sync.phase2.cli_bin executable is not available: lark-cli",
                "Required environment variables are not set: BASE_TOKEN, SPEC_FOOTNOTES_TABLE, SPEC_FOOTNOTES_VIEW",
            ],
            errors,
        )

    def test_collect_sync_preflight_errors_should_allow_literal_table_and_view_ids(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "cli_bin": "lark-cli",
                    "base_token_env": "BASE_TOKEN",
                    "tables": {
                        "spec_master": {
                            "table_id": "tbl_master_total",
                            "view_id": "view_master_total",
                        },
                    },
                }
            }
        }

        with mock.patch("tools.sync_data.shutil.which", return_value=r"C:\tools\lark-cli.cmd"):
            errors = sync_data.collect_sync_preflight_errors(
                cfg,
                table_names=["spec_master"],
                environ={"BASE_TOKEN": "app_token"},
                require_cli=True,
            )

        self.assertEqual([], errors)

    def test_collect_sync_preflight_errors_should_allow_spec_master_source_tables_without_total_binding(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "cli_bin": "lark-cli",
                    "base_token_env": "BASE_TOKEN",
                    "spec_master_sources": {
                        "spec_rows_source_table_id": "tbl_spec_rows",
                        "spec_rows_source_view_id": "view_spec_rows",
                        "page_placeholders_source_table_id": "tbl_placeholders",
                        "page_placeholders_source_view_id": "view_placeholders",
                    },
                    "tables": {
                        "spec_master": {},
                    },
                }
            }
        }

        errors = sync_data.collect_sync_preflight_errors(
            cfg,
            table_names=["spec_master"],
            environ={"BASE_TOKEN": "app_token"},
            require_cli=False,
        )

        self.assertEqual([], errors)

    def test_collect_sync_preflight_errors_should_require_spec_master_source_env_bindings(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "provider": "lark_cli",
                    "cli_bin": "lark-cli",
                    "base_token_env": "BASE_TOKEN",
                    "spec_master_sources": {
                        "spec_rows_source_table_id_env": "SPEC_ROWS_SOURCE_TABLE",
                        "spec_rows_source_view_id_env": "SPEC_ROWS_SOURCE_VIEW",
                        "page_placeholders_source_table_id_env": "PAGE_PLACEHOLDERS_SOURCE_TABLE",
                        "page_placeholders_source_view_id_env": "PAGE_PLACEHOLDERS_SOURCE_VIEW",
                    },
                    "tables": {
                        "spec_master": {},
                    },
                }
            }
        }

        errors = sync_data.collect_sync_preflight_errors(
            cfg,
            table_names=["spec_master"],
            environ={"BASE_TOKEN": "app_token"},
            require_cli=False,
        )

        self.assertEqual(
            [
                "Required environment variables are not set: "
                "SPEC_ROWS_SOURCE_TABLE, PAGE_PLACEHOLDERS_SOURCE_TABLE, "
                "SPEC_ROWS_SOURCE_VIEW, PAGE_PLACEHOLDERS_SOURCE_VIEW",
            ],
            errors,
        )

    def test_sync_phase2_snapshot_should_write_csvs_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = {
                "paths": {
                    "page_registry_csv": "fixtures/page_registry.csv",
                },
                "sync": {
                    "phase2": {
                        "provider": "lark_cli",
                        "base_token_env": "BASE_TOKEN",
                        "tables": {
                            "manual_copy_source": {
                                "table_id_env": "MANUAL_COPY_SOURCE_TABLE",
                            },
                            "translation_memory": {
                                "base_token_env": "TM_BASE_TOKEN",
                                "table_id": "tbl_tm",
                                "view_id": "view_tm",
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
            _write_page_registry(root, "fixtures/page_registry.csv")

            fake_source = _FakeSource(
                {
                    "tbl_manual": [
                        {
                            "fields": {
                                "copy_key": "spec.section.b",
                                "page_id": "specifications",
                                "copy_type": "section_title",
                                "Market": "ALL",
                                "Model": "ALL",
                                "Source_lang": "en",
                                "Is_Latest": True,
                                "Version": "V1.0",
                                "source_text": "B",
                                "section_order": 2,
                            }
                        },
                        {
                            "fields": {
                                "copy_key": "spec.section.a",
                                "page_id": "specifications",
                                "copy_type": "section_title",
                                "Market": "ALL",
                                "Model": "ALL",
                                "Source_lang": "en",
                                "Is_Latest": True,
                                "Version": "V1.0",
                                "source_text": "A",
                                "section_order": 1,
                            }
                        },
                    ],
                    "tbl_tm": [
                        {"fields": {"en": "A", "fr": "A FR", "用途标签": [{"text": "manual_copy"}]}},
                        {"fields": {"en": "B", "fr": "B FR", "用途标签": [{"text": "manual_copy"}]}},
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
                    "MANUAL_COPY_SOURCE_TABLE": "tbl_manual",
                    "TM_BASE_TOKEN": "tm_token",
                    "SPEC_MASTER_TABLE": "tbl_master",
                    "FEISHU_PHASE2_SPEC_ROWS_SOURCE_TABLE_ID": "",
                    "FEISHU_PHASE2_PAGE_PLACEHOLDERS_SOURCE_TABLE_ID": "",
                },
                clear=True,
            ), mock.patch.object(sync_data, "ROOT", root):
                result = sync_data.sync_phase2_snapshot(
                    cfg=cfg,
                    config_path=config_path,
                    data_root="data/phase2",
                    table_names=["manual_copy_source", "spec_master"],
                    dry_run=False,
                    source=fake_source,
                    built_at=datetime(2026, 3, 31, 9, 0, tzinfo=timezone.utc),
                )

            self.assertEqual(root / "data" / "phase2", result.export_root)
            self.assertTrue((root / "data" / "phase2" / "spec_titles.csv").exists())
            self.assertTrue((root / "data" / "phase2" / "Spec_Master.csv").exists())
            self.assertTrue((root / "data" / "phase2" / "page_registry.csv").exists())
            self.assertTrue((root / "data" / "phase2" / "row_key_mapping.csv").exists())
            self.assertTrue((root / "data" / "phase2" / "snapshot_manifest.json").exists())
            self.assertEqual(
                [
                    ("app_token", "tbl_manual", None),
                    ("app_token", "tbl_master", None),
                    ("tm_token", "tbl_tm", "view_tm"),
                ],
                fake_source.calls,
            )

            titles_lines = (root / "data" / "phase2" / "spec_titles.csv").read_text(encoding="utf-8").splitlines()
            self.assertEqual(
                "title_en,section_order,title_zh,title_jp,title_fr,title_es,title_de,title_it,title_uk",
                titles_lines[0],
            )
            self.assertTrue(titles_lines[1].startswith("A,1"))
            self.assertTrue(titles_lines[2].startswith("B,2"))

            master_lines = (root / "data" / "phase2" / "Spec_Master.csv").read_text(encoding="utf-8").splitlines()
            self.assertEqual(
                "spec_row_key,document_key,Model,Region,Source_lang,Version,Is_Latest,Page,Section,Section_order,Row_order,Row_key,Slot_key,Row_label_source,Row_label_footnote_refs,Line_order,Param_source,Param_footnote_refs,Value_source,Value_footnote_refs,Row_label_fr,Param_fr,Value_fr,Row_label_es,Param_es,Value_es,Row_label_br,Param_br,Value_br,Row_label_de,Param_de,Value_de,Row_label_it,Param_it,Value_it,Row_label_uk,Param_uk,Value_uk",
                master_lines[0],
            )
            self.assertIn("TRUE", master_lines[1])
            self.assertIn("product_name", master_lines[1])
            self.assertIn("model_no", master_lines[2])
            self.assertIn("front.label", master_lines[2])

            mapping_lines = (root / "data" / "phase2" / "row_key_mapping.csv").read_text(encoding="utf-8-sig").splitlines()
            self.assertEqual("Row_label_source,Line_order,Row_key,Remark", mapping_lines[0])
            self.assertIn("Product Name,1,product_name,", mapping_lines)
            self.assertIn("Model No.,1,model_no,", mapping_lines)

            manifest = json.loads((root / "data" / "phase2" / "snapshot_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(["manual_copy_source", "spec_master"], manifest["requested_tables"])
            self.assertIn("spec_footnotes", manifest["skipped_tables"])
            self.assertEqual(2, len(manifest["tables"]))
            self.assertEqual(
                ["page_registry", "row_key_mapping", "localized_copy", "status_words", "spec_titles", "source_record_index"],
                [entry["logical_name"] for entry in manifest["derived_files"]],
            )

    def test_sync_phase2_snapshot_should_merge_spec_master_source_tables_without_total_table(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = {
                "paths": {
                    "page_registry_csv": "fixtures/page_registry.csv",
                },
                "sync": {
                    "phase2": {
                        "provider": "lark_cli",
                        "base_token_env": "BASE_TOKEN",
                        "spec_master_sources": {
                            "spec_rows_source_table_id": "tbl_spec_rows",
                            "spec_rows_source_view_id": "view_spec_rows",
                            "page_placeholders_source_table_id": "tbl_placeholders",
                            "page_placeholders_source_view_id": "view_placeholders",
                        },
                        "tables": {
                            "spec_master": {},
                            "spec_footnotes": {
                                "table_id_env": "SPEC_FOOTNOTES_TABLE",
                            },
                        },
                    }
                }
            }
            config_path = root / "config.yaml"
            config_path.write_text("sync: {}\n", encoding="utf-8")
            _write_page_registry(root, "fixtures/page_registry.csv")

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
                    "tbl_spec_rows": [
                        {
                            "fields": {
                                "document_key": "JE-1000F_US",
                                "Source_lang": "en",
                                "Version": "1.0",
                                "Is_Latest": True,
                                "Page": "specifications",
                                "Section": "INPUT PORTS",
                                "Section_order": 2,
                                "Row_order": 1,
                                "Row_key": "ac_input",
                                "Line_order": 2,
                                "Row_label_source": "1 x AC Input",
                                "Param_source": "Bypass Mode",
                                "Param_footnote_refs": {"id": "rec_ac_bypass"},
                                "Value_source": "100V-120V~60Hz, 12A Max",
                            }
                        },
                    ],
                    "tbl_placeholders": [
                        {
                            "fields": {
                                "document_key": "JE-1000F_US",
                                "Source_lang": "en",
                                "Version": "1.0",
                                "Is_Latest": True,
                                "Page": "Product overview",
                                "Section": "INPUT PORTS",
                                "Section_order": 2,
                                "Row_order": 2,
                                "Row_key": "ac_input",
                                "Slot_key": "[side.label](side.label)",
                                "Line_order": 1,
                                "Value_source": "AC Input",
                            }
                        },
                    ],
                    "tbl_footnotes": [{"fields": footnote_fields}],
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
                },
                clear=True,
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

            with (root / "data" / "phase2" / "Spec_Master.csv").open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual(
                [
                    ("app_token", "tbl_spec_rows", "view_spec_rows"),
                    ("app_token", "tbl_placeholders", "view_placeholders"),
                ],
                fake_source.calls,
            )
            self.assertEqual([("app_token", "tbl_footnotes", None)], fake_source.calls_with_ids)
            self.assertEqual(2, len(rows))
            spec_row = next(row for row in rows if row["Page"] == "specifications")
            self.assertEqual("JE-1000F", spec_row["Model"])
            self.assertEqual("US", spec_row["Region"])
            self.assertEqual("ac_bypass", spec_row["Param_footnote_refs"])
            self.assertEqual(
                "JE-1000F_US__v1.0__specifications__s02__r01__ac_input__main__l02",
                spec_row["spec_row_key"],
            )
            placeholder_row = next(row for row in rows if row["Page"] == "Product overview")
            self.assertEqual("side.label", placeholder_row["Slot_key"])
            self.assertEqual("spec_master", result.synced_tables[0].logical_name)
            self.assertEqual(2, result.synced_tables[0].row_count)

    def test_sync_phase2_snapshot_should_download_lcd_icon_figure_attachments(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = {
                "paths": {
                    "page_registry_csv": "fixtures/page_registry.csv",
                },
                "sync": {
                    "phase2": {
                        "provider": "lark_cli",
                        "base_token_env": "BASE_TOKEN",
                        "tables": {
                            "lcd_icons": {
                                "table_id_env": "LCD_TABLE",
                            },
                        },
                    }
                }
            }
            config_path = root / "config.yaml"
            config_path.write_text("sync: {}\n", encoding="utf-8")
            _write_page_registry(root, "fixtures/page_registry.csv")

            fake_source = _FakeSourceWithDownloads(
                {
                    "tbl_lcd": [
                        {
                            "fields": {
                                "No.": "1",
                                "Model": "JE-1000F",
                                "Is_latest": True,
                                "Version": "V1.0",
                                "icon_en": "Wi-Fi",
                                "icon_desc_en": "On: Wi-Fi connected.",
                                "figure": [{"file_token": "file_token_wifi", "name": "wifi.png"}],
                            }
                        }
                    ],
                }
            )

            with mock.patch.dict(
                "os.environ",
                {
                    "BASE_TOKEN": "app_token",
                    "LCD_TABLE": "tbl_lcd",
                },
                clear=True,
            ), mock.patch.object(sync_data, "ROOT", root):
                sync_data.sync_phase2_snapshot(
                    cfg=cfg,
                    config_path=config_path,
                    data_root="data/phase2",
                    table_names=["lcd_icons"],
                    dry_run=False,
                    source=fake_source,
                    built_at=datetime(2026, 3, 31, 9, 0, tzinfo=timezone.utc),
                )

            expected_asset = root / "data" / "phase2" / "_attachments" / "lcd_icons" / "1_Wi-Fi_file_token_wifi.png"
            self.assertEqual([("file_token_wifi", expected_asset, False)], fake_source.downloads)
            self.assertTrue(expected_asset.exists())

            with (root / "data" / "phase2" / "lcd_icons_blocks.csv").open(
                "r",
                encoding="utf-8-sig",
                newline="",
            ) as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(
                "data/phase2/_attachments/lcd_icons/1_Wi-Fi_file_token_wifi.png",
                rows[0]["figure"],
            )

    def test_sync_phase2_snapshot_should_use_cached_lcd_icon_attachment_when_download_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = {
                "sync": {
                    "phase2": {
                        "provider": "lark_cli",
                        "base_token_env": "BASE_TOKEN",
                        "tables": {
                            "lcd_icons": {
                                "table_id_env": "LCD_TABLE",
                            },
                        },
                    }
                }
            }
            config_path = root / "config.yaml"
            config_path.write_text("sync: {}\n", encoding="utf-8")
            _write_page_registry(root)
            fallback_asset = (
                root
                / "data"
                / "phase2"
                / "_attachments"
                / "lcd_icons"
                / "3_Quiet_Charging_Mode_cached_token.png"
            )
            fallback_asset.parent.mkdir(parents=True, exist_ok=True)
            fallback_asset.write_bytes(b"cached image")
            fake_source = _FakeSourceWithFailingDownloads(
                {
                    "tbl_lcd": [
                        {
                            "fields": {
                                "No.": "3",
                                "Model": "JE-2000E",
                                "Is_latest": True,
                                "Version": "V0.2",
                                "icon_en": "Quiet Charging Mode",
                                "icon_desc_en": "On: Quiet charging enabled.",
                                "figure": [{"file_token": "new_token", "name": "quiet.png"}],
                            }
                        }
                    ],
                }
            )
            stderr = io.StringIO()

            with mock.patch.dict(
                "os.environ",
                {
                    "BASE_TOKEN": "app_token",
                    "LCD_TABLE": "tbl_lcd",
                },
                clear=True,
            ), mock.patch.object(sync_data, "ROOT", root), mock.patch("sys.stderr", new=stderr):
                sync_data.sync_phase2_snapshot(
                    cfg=cfg,
                    config_path=config_path,
                    data_root="data/phase2",
                    table_names=["lcd_icons"],
                    dry_run=False,
                    source=fake_source,
                    built_at=datetime(2026, 3, 31, 9, 0, tzinfo=timezone.utc),
                )

            expected_target = root / "data" / "phase2" / "_attachments" / "lcd_icons" / "3_Quiet_Charging_Mode_new_token.png"
            self.assertEqual([("new_token", expected_target, False)], fake_source.downloads)
            self.assertIn("Using cached attachment", stderr.getvalue())

            with (root / "data" / "phase2" / "lcd_icons_blocks.csv").open(
                "r",
                encoding="utf-8-sig",
                newline="",
            ) as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(
                "data/phase2/_attachments/lcd_icons/3_Quiet_Charging_Mode_cached_token.png",
                rows[0]["figure"],
            )

    def test_sync_phase2_snapshot_should_clear_lcd_icon_attachment_when_download_fails_without_cache(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = {
                "sync": {
                    "phase2": {
                        "provider": "lark_cli",
                        "base_token_env": "BASE_TOKEN",
                        "tables": {
                            "lcd_icons": {
                                "table_id_env": "LCD_TABLE",
                            },
                        },
                    }
                }
            }
            config_path = root / "config.yaml"
            config_path.write_text("sync: {}\n", encoding="utf-8")
            _write_page_registry(root)
            fake_source = _FakeSourceWithFailingDownloads(
                {
                    "tbl_lcd": [
                        {
                            "fields": {
                                "No.": "4",
                                "Model": "JE-2000E",
                                "Is_latest": True,
                                "Version": "V0.2",
                                "icon_en": "Charging Plan",
                                "icon_desc_en": "On: Charging plan enabled.",
                                "figure": [{"file_token": "missing_token", "name": "charging.png"}],
                            }
                        }
                    ],
                }
            )
            stderr = io.StringIO()

            with mock.patch.dict(
                "os.environ",
                {
                    "BASE_TOKEN": "app_token",
                    "LCD_TABLE": "tbl_lcd",
                },
                clear=True,
            ), mock.patch.object(sync_data, "ROOT", root), mock.patch("sys.stderr", new=stderr):
                sync_data.sync_phase2_snapshot(
                    cfg=cfg,
                    config_path=config_path,
                    data_root="data/phase2",
                    table_names=["lcd_icons"],
                    dry_run=False,
                    source=fake_source,
                    built_at=datetime(2026, 3, 31, 9, 0, tzinfo=timezone.utc),
                )

            with (root / "data" / "phase2" / "lcd_icons_blocks.csv").open(
                "r",
                encoding="utf-8-sig",
                newline="",
            ) as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual("", rows[0]["figure"])
            self.assertIn("Clearing optional image reference", stderr.getvalue())

    def test_sync_phase2_snapshot_should_download_symbol_figure_attachments(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = {
                "sync": {
                    "phase2": {
                        "provider": "lark_cli",
                        "base_token_env": "BASE_TOKEN",
                        "tables": {
                            "symbols_blocks": {
                                "table_id_env": "SYMBOLS_TABLE",
                            },
                        },
                    }
                }
            }
            config_path = root / "config.yaml"
            config_path.write_text("sync: {}\n", encoding="utf-8")
            _write_page_registry(root)

            fake_source = _FakeSourceWithDownloads(
                {
                    "tbl_symbols": [
                        {
                            "fields": {
                                "page_id": "symbols",
                                "Figure": [{"file_token": "file_token_warning", "name": "warning.png"}],
                                "image_path": "templates/word_template/common_assets/symbols/warning_triangle.png",
                                "symbol_key": "warning_triangle",
                                "text_en": "Warning symbol meaning.",
                                "Is_Latest": "false",
                                "Market": [{"text": "US"}, {"text": "EU"}],
                                "enabled": True,
                                "block_type": "table_row",
                                "order": "10",
                                "Region": "US",
                                "Model": "JE-1000F",
                                "Source_lang": "en",
                            }
                        }
                    ],
                }
            )

            with mock.patch.dict(
                "os.environ",
                {
                    "BASE_TOKEN": "app_token",
                    "SYMBOLS_TABLE": "tbl_symbols",
                },
                clear=True,
            ), mock.patch.object(sync_data, "ROOT", root):
                sync_data.sync_phase2_snapshot(
                    cfg=cfg,
                    config_path=config_path,
                    data_root="data/phase2",
                    table_names=["symbols_blocks"],
                    dry_run=False,
                    source=fake_source,
                    built_at=datetime(2026, 3, 31, 9, 0, tzinfo=timezone.utc),
                )

            expected_asset = root / "data" / "phase2" / "_attachments" / "symbols" / "10_warning_triangle_file_token_warning.png"
            self.assertEqual([("file_token_warning", expected_asset, False)], fake_source.downloads)
            self.assertTrue(expected_asset.exists())

            with (root / "data" / "phase2" / "symbols_blocks.csv").open(
                "r",
                encoding="utf-8-sig",
                newline="",
            ) as handle:
                rows = list(csv.DictReader(handle))
            expected_path = "data/phase2/_attachments/symbols/10_warning_triangle_file_token_warning.png"
            self.assertEqual(expected_path, rows[0]["Figure"])
            self.assertEqual(expected_path, rows[0]["image_path"])
            self.assertEqual("FALSE", rows[0]["Is_Latest"])
            self.assertEqual("US, EU", rows[0]["Market"])

    def test_sync_phase2_snapshot_should_prefer_literal_table_and_view_ids(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = {
                "sync": {
                    "phase2": {
                        "provider": "lark_cli",
                        "base_token_env": "BASE_TOKEN",
                        "tables": {
                            "spec_master": {
                                "table_id": "tbl_master_total",
                                "view_id": "view_master_total",
                                "table_id_env": "SPEC_MASTER_TABLE",
                                "view_id_env": "SPEC_MASTER_VIEW",
                            },
                        },
                    }
                }
            }
            config_path = root / "config.yaml"
            config_path.write_text("sync: {}\n", encoding="utf-8")
            _write_page_registry(root)

            fake_source = _FakeSource(
                {
                    "tbl_master_total": [
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
                                "Row_label_source": "Product Name",
                                "Line_order": 1,
                                "Value_source": "Jackery Explorer 1000",
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
                    "SPEC_MASTER_TABLE": "tbl_master_wrong",
                    "SPEC_MASTER_VIEW": "view_master_wrong",
                    "FEISHU_PHASE2_SPEC_ROWS_SOURCE_TABLE_ID": "",
                    "FEISHU_PHASE2_PAGE_PLACEHOLDERS_SOURCE_TABLE_ID": "",
                },
                clear=True,
            ), mock.patch.object(sync_data, "ROOT", root):
                sync_data.sync_phase2_snapshot(
                    cfg=cfg,
                    config_path=config_path,
                    data_root="data/phase2",
                    table_names=["spec_master"],
                    dry_run=False,
                    source=fake_source,
                    built_at=datetime(2026, 3, 31, 9, 0, tzinfo=timezone.utc),
                )

            self.assertEqual(
                [("app_token", "tbl_master_total", "view_master_total")],
                fake_source.calls,
            )

    def test_sync_phase2_snapshot_should_not_write_files_in_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = {
                "paths": {
                    "page_registry_csv": "fixtures/page_registry.csv",
                },
                "sync": {
                    "phase2": {
                        "provider": "lark_cli",
                        "base_token_env": "BASE_TOKEN",
                        "tables": {
                            "manual_copy_source": {
                                "table_id_env": "MANUAL_COPY_SOURCE_TABLE",
                            },
                            "translation_memory": {
                                "base_token_env": "TM_BASE_TOKEN",
                                "table_id": "tbl_tm",
                            },
                        },
                    }
                }
            }
            _write_page_registry(root, "fixtures/page_registry.csv")
            fake_source = _FakeSource(
                {
                    "tbl_manual": [{"fields": {"copy_key": "spec.page_title", "source_text": "SPECIFICATIONS"}}],
                    "tbl_tm": [{"fields": {"en": "SPECIFICATIONS", "用途标签": [{"text": "manual_copy"}]}}],
                }
            )

            with mock.patch.dict(
                "os.environ",
                {
                    "BASE_TOKEN": "app_token",
                    "MANUAL_COPY_SOURCE_TABLE": "tbl_manual",
                    "TM_BASE_TOKEN": "tm_token",
                },
                clear=True,
            ), mock.patch.object(sync_data, "ROOT", root):
                result = sync_data.sync_phase2_snapshot(
                    cfg=cfg,
                    config_path=root / "config.yaml",
                    data_root="data/phase2",
                    table_names=["manual_copy_source"],
                    dry_run=True,
                    source=fake_source,
                )

            self.assertTrue(result.dry_run)
            self.assertFalse((root / "data" / "phase2" / "Manual_Copy_Source.csv").exists())
            self.assertFalse((root / "data" / "phase2" / "spec_titles.csv").exists())
            self.assertFalse((root / "data" / "phase2" / "page_registry.csv").exists())
            self.assertFalse((root / "data" / "phase2" / "row_key_mapping.csv").exists())
            self.assertFalse((root / "data" / "phase2" / "snapshot_manifest.json").exists())

    def test_sync_phase2_snapshot_should_derive_localized_copy_from_manual_source_and_tm(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = {
                "paths": {
                    "page_registry_csv": "fixtures/page_registry.csv",
                },
                "sync": {
                    "phase2": {
                        "provider": "lark_cli",
                        "base_token_env": "BASE_TOKEN",
                        "tables": {
                            "manual_copy_source": {
                                "table_id_env": "MANUAL_COPY_SOURCE_TABLE",
                            },
                            "translation_memory": {
                                "base_token_env": "TM_BASE_TOKEN",
                                "table_id": "tbl_tm",
                                "view_id": "view_tm",
                            },
                        },
                    }
                },
            }
            _write_page_registry(root, "fixtures/page_registry.csv")
            fake_source = _FakeSource(
                {
                    "tbl_manual": [
                        {
                            "fields": {
                                "copy_key": "product_overview.page_title",
                                "page_id": "03_product_overview",
                                "copy_type": "page_title",
                                "Market": "ALL",
                                "Model": "ALL",
                                "Source_lang": "en",
                                "Is_Latest": True,
                                "Version": "V1.0",
                                "source_text": "PRODUCT OVERVIEW",
                            }
                        }
                    ],
                    "tbl_tm": [
                        {
                            "fields": {
                                "en": "PRODUCT OVERVIEW",
                                "zh": "产品外观",
                                "jp": "各部の名称",
                                "用途标签": [{"text": "manual_copy"}],
                            }
                        },
                        {
                            "fields": {
                                "en": "On",
                                "zh": "点亮",
                                "jp": "点灯",
                                "是否为 status word": "Y",
                            }
                        },
                    ],
                }
            )

            with mock.patch.dict(
                "os.environ",
                {
                    "BASE_TOKEN": "app_token",
                    "MANUAL_COPY_SOURCE_TABLE": "tbl_manual",
                    "TM_BASE_TOKEN": "tm_token",
                },
                clear=True,
            ), mock.patch.object(sync_data, "ROOT", root):
                result = sync_data.sync_phase2_snapshot(
                    cfg=cfg,
                    config_path=root / "config.yaml",
                    data_root="data/phase2",
                    table_names=["manual_copy_source"],
                    dry_run=False,
                    source=fake_source,
                    built_at=datetime(2026, 5, 31, 9, 0, tzinfo=timezone.utc),
                )

            self.assertEqual(
                [("app_token", "tbl_manual", None), ("tm_token", "tbl_tm", "view_tm")],
                fake_source.calls,
            )
            with (root / "data" / "phase2" / "Localized_Copy.csv").open(encoding="utf-8", newline="") as handle:
                localized_rows = list(csv.DictReader(handle))
            self.assertEqual("03_product_overview", localized_rows[0]["page_id"])
            self.assertEqual("ALL", localized_rows[0]["Region"])
            self.assertEqual("PRODUCT OVERVIEW", localized_rows[0]["text_en"])
            self.assertEqual("产品外观", localized_rows[0]["text_zh"])
            self.assertEqual("PRODUCT OVERVIEW", localized_rows[0]["text_fr"])

            with (root / "data" / "phase2" / "Status_Words.csv").open(encoding="utf-8", newline="") as handle:
                status_rows = list(csv.DictReader(handle))
            self.assertEqual("On", status_rows[0]["en"])
            self.assertEqual("Y", status_rows[0]["是否为 status word"])

            missing_report = root / "reports" / "content_audit" / "manual_copy_missing_translations.csv"
            self.assertIn("product_overview.page_title,en,fr,PRODUCT OVERVIEW", missing_report.read_text(encoding="utf-8"))
            self.assertEqual(
                ["page_registry", "localized_copy", "status_words", "spec_titles", "source_record_index"],
                [entry.logical_name for entry in result.derived_files],
            )

    def test_sync_phase2_snapshot_should_preserve_existing_phase2_row_key_mapping(self) -> None:
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
            phase2_dir = root / "data" / "phase2"
            phase2_dir.mkdir(parents=True, exist_ok=True)
            _write_page_registry(root)
            (phase2_dir / "row_key_mapping.csv").write_text(
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
                    "FEISHU_PHASE2_SPEC_ROWS_SOURCE_TABLE_ID": "",
                    "FEISHU_PHASE2_PAGE_PLACEHOLDERS_SOURCE_TABLE_ID": "",
                },
                clear=True,
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
            self.assertEqual(
                ["page_registry", "row_key_mapping", "source_record_index"],
                [entry.logical_name for entry in result.derived_files],
            )

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
            _write_page_registry(root)

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
                    "FEISHU_PHASE2_SPEC_ROWS_SOURCE_TABLE_ID": "",
                    "FEISHU_PHASE2_PAGE_PLACEHOLDERS_SOURCE_TABLE_ID": "",
                },
                clear=True,
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
                        "spec_footnotes": {
                            "table_id_env": "SPEC_FOOTNOTES_TABLE",
                            "view_id_env": "SPEC_FOOTNOTES_VIEW",
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
                    table_names=["spec_footnotes"],
                    dry_run=True,
                    source=None,
                )

        message = str(exc_info.exception)
        self.assertIn("sync.phase2.cli_bin executable is not available: lark-cli", message)
        self.assertIn(
            "Required environment variables are not set: BASE_TOKEN, SPEC_FOOTNOTES_TABLE, SPEC_FOOTNOTES_VIEW",
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
        self.assertIn("--jq", seen_commands[1])
        self.assertIn(".", seen_commands[1])
        format_index = seen_commands[1].index("--format")
        self.assertEqual("json", seen_commands[1][format_index + 1])
        limit_index = seen_commands[1].index("--limit")
        self.assertEqual("200", seen_commands[1][limit_index + 1])
        self.assertIn("--offset", seen_commands[2])
        self.assertIn("1", seen_commands[2])

    def test_lark_cli_source_should_retry_record_list_without_format_for_old_cli(self) -> None:
        source = sync_data.LarkCliSource(cli_bin="lark-cli", identity="bot")
        seen_commands: list[list[str]] = []

        def fake_run(cmd: list[str], **_: object) -> mock.Mock:
            seen_commands.append(cmd)
            if cmd[2] == "+field-list":
                return mock.Mock(
                    stdout=json.dumps(
                        {
                            "data": {
                                "items": [{"field_id": "fld_title_en", "field_name": "title_en"}],
                                "total": 1,
                            },
                            "ok": True,
                        }
                    )
                )
            if "--format" in cmd:
                raise subprocess.CalledProcessError(
                    1,
                    cmd,
                    stderr="Error: unknown flag: --format",
                )
            return mock.Mock(
                stdout=json.dumps(
                    {
                        "data": {
                            "field_id_list": ["fld_title_en"],
                            "fields": ["title_en"],
                            "data": [["A"]],
                            "has_more": False,
                        },
                        "ok": True,
                    }
                )
            )

        with mock.patch("tools.sync_data.shutil.which", return_value="/usr/local/bin/lark-cli"), mock.patch(
            "tools.sync_data.subprocess.run",
            side_effect=fake_run,
        ):
            rows = source.fetch_records(
                base_token="app_token",
                table_id="tbl_titles",
                view_id="view_titles",
            )

        self.assertEqual([{"fields": {"title_en": "A"}}], rows)
        record_commands = [cmd for cmd in seen_commands if cmd[2] == "+record-list"]
        self.assertEqual(2, len(record_commands))
        self.assertIn("--format", record_commands[0])
        self.assertNotIn("--format", record_commands[1])
        self.assertIn("--jq", record_commands[1])
        self.assertIn(".", record_commands[1])

    def test_lark_cli_source_should_include_cli_output_when_command_fails(self) -> None:
        source = sync_data.LarkCliSource(cli_bin="lark-cli")

        def fake_run(*_: object, **__: object) -> mock.Mock:
            raise subprocess.CalledProcessError(
                2,
                ["lark-cli", "base", "+record-list"],
                output="api stdout",
                stderr="api stderr",
            )

        with mock.patch("tools.sync_data.subprocess.run", side_effect=fake_run):
            with self.assertRaisesRegex(RuntimeError, "exit code 2") as exc_info:
                source._run_base_command(args=["+record-list"])

        message = str(exc_info.exception)
        self.assertIn("stdout=api stdout", message)
        self.assertIn("stderr=api stderr", message)

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
