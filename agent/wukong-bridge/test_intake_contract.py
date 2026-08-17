from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

import intake_commit_driver as driver
import server
from intake_contract import (
    KR_CONTRACT_VERSION,
    is_kr_document_key,
    validate_kr_candidate,
    validate_kr_source,
    validate_sibling_structure,
)


STAGING_COLUMNS = [
    *server.INTAKE_STAGE_FIELDS,
    "确认",
    "入库结果",
]


def row_for(columns: list[str], **values) -> list:
    return [values.get(column) for column in columns]


def valid_kr_values(**overrides) -> dict:
    values = {
        "document_key": "JE-TEST_KR",
        "Row_key": "capacity",
        "Slot_key": None,
        "Line_order": 1,
        "Page": "specifications",
        "章节": "GENERAL INFO",
        "行标签": "Capacity",
        "行标签_ko": "",
        "规格书字段": "Capacity",
        "规格书原值": "2048Wh",
        "手册值": "2048 Wh",
        "手册值_ko": "",
        "Source_lang": "en",
        "备注": "test",
        "状态": "⚠️需确认",
        "确认": None,
        "入库结果": None,
    }
    values.update(overrides)
    return values


SOURCE_STRUCTURE_COLUMNS = ["Page", "Section", "Row_key", "Slot_key", "Line_order"]


def source_dataset(*rows: dict) -> dict:
    return {
        "ok": True,
        "columns": SOURCE_STRUCTURE_COLUMNS,
        "rows": [row_for(SOURCE_STRUCTURE_COLUMNS, **row) for row in rows],
        "record_ids": [f"rec-ref-{index}" for index, _row in enumerate(rows)],
    }


CAPACITY_REFERENCE = source_dataset({
    "Page": "specifications", "Section": "GENERAL INFO", "Row_key": "capacity",
    "Slot_key": None, "Line_order": 1,
})
EMPTY_REFERENCE = source_dataset()


class KrContractUnitTests(unittest.TestCase):
    def test_target_detection_is_region_based(self):
        self.assertTrue(is_kr_document_key("JE-2000E_KR"))
        self.assertTrue(is_kr_document_key("JE-2000E_kr"))
        self.assertFalse(is_kr_document_key("JE-2000E_US"))
        self.assertFalse(is_kr_document_key("KR"))

    def test_source_first_requires_english_value_label_and_en_source(self):
        violations = validate_kr_source(
            "JE-2000E_KR",
            value_source="",
            row_label_source="",
            source_lang="ko",
        )
        self.assertEqual(
            {item["code"] for item in violations},
            {
                "MISSING_VALUE_SOURCE",
                "MISSING_ROW_LABEL_SOURCE",
                "SOURCE_LANG_NOT_EN",
            },
        )

    def test_korean_localization_is_not_required_for_initial_intake(self):
        self.assertEqual(
            validate_kr_source(
                "JE-2000E_KR",
                value_source="2048 Wh",
                row_label_source="Capacity",
                source_lang="en",
            ),
            [],
        )

    def test_non_kr_target_is_not_subject_to_kr_contract(self):
        self.assertEqual(
            validate_kr_source(
                "JE-2000E_US",
                value_source="",
                row_label_source="",
                source_lang="en",
            ),
            [],
        )

    def test_korean_text_cannot_masquerade_as_english_source(self):
        violations = validate_kr_source(
            "JE-2000E_KR",
            value_source="리튬이차전지시스템",
            row_label_source="제품명",
            source_lang="en",
        )
        self.assertEqual(
            [item["code"] for item in violations].count("NON_ENGLISH_SOURCE_TEXT"), 2
        )

    def test_storage_duration_has_canonical_line_order(self):
        violations = validate_kr_candidate("JE-2000E_KR", {
            "Row_key": "storage_temperature",
            "Line_order": 1,
            "行标签": "Storage Temperature",
            "手册值": "0 °C to 25 °C",
            "规格书原值": "1 year: 0~25℃",
            "Source_lang": "en",
        })
        self.assertIn("STORAGE_LINE_ORDER_MISMATCH", {
            item["code"] for item in violations
        })

    def test_english_values_require_manual_unit_style(self):
        violations = validate_kr_candidate("JE-2000E_KR", {
            "Row_key": "capacity", "Line_order": 1,
            "行标签": "Capacity", "手册值": "2048Wh (40Ah/51.2V)",
            "Source_lang": "en",
        })
        self.assertIn("NON_CANONICAL_UNIT_SPACING", {
            item["code"] for item in violations
        })

    def test_dc_values_reject_equals_even_when_units_are_spaced(self):
        violations = validate_kr_candidate("JE-2000E_KR", {
            "Row_key": "usb_c_output", "Line_order": 1,
            "行标签": "USB-C Output", "手册值": "5 V = 3 A",
            "Source_lang": "en",
        })
        self.assertIn("NON_CANONICAL_DC_SYMBOL", {
            item["code"] for item in violations
        })

    def test_sibling_structure_catches_page_route_and_reports_coverage(self):
        references = [
            {"Page": "storage", "Section": "ENV", "Row_key": "storage_temperature",
             "Slot_key": "", "Line_order": 1},
            {"Page": "specifications", "Section": "GENERAL INFO",
             "Row_key": "capacity", "Slot_key": "", "Line_order": 1},
        ]
        candidates = [
            {"Page": "specifications", "Section": "ENV",
             "Row_key": "storage_temperature", "Slot_key": "", "Line_order": 1},
        ]
        report = validate_sibling_structure(candidates, references)
        self.assertIn("PAGE_ROUTE_MISMATCH", {
            item["code"] for item in report["violations"]
        })
        self.assertEqual(len(report["missing_rows"]), 2)


class ServerKrContractTests(unittest.TestCase):
    def test_bridge_info_reports_server_and_contract_versions(self):
        outcome = server.bridge_info({})
        self.assertEqual(outcome["server_name"], "hello-docs-bridge")
        self.assertEqual(outcome["server_version"], "0.8.0")
        self.assertEqual(outcome["intake_contract_version"], KR_CONTRACT_VERSION)

    def test_stage_requires_explicit_sibling_for_kr(self):
        existing = {"ok": True, "columns": STAGING_COLUMNS,
                    "rows": [], "record_ids": []}
        with mock.patch.object(server, "lark_records_all", return_value=existing), \
                mock.patch.object(server, "run_lark_cli") as write:
            outcome = server.intake_stage({
                "document_key": "JE-TEST_KR", "rows": [valid_kr_values()],
            })
        self.assertFalse(outcome["ok"])
        self.assertEqual(outcome["staged"], 0)
        write.assert_not_called()

    def test_stage_rejects_wrong_sibling_page_before_write(self):
        existing = {"ok": True, "columns": STAGING_COLUMNS,
                    "rows": [], "record_ids": []}
        wrong_page = valid_kr_values(Page="storage")
        with mock.patch.object(server, "lark_records_all",
                               side_effect=[existing, CAPACITY_REFERENCE,
                                            EMPTY_REFERENCE]), \
                mock.patch.object(server, "run_lark_cli") as write:
            outcome = server.intake_stage({
                "document_key": "JE-TEST_KR",
                "sibling_document_key": "JE-TEST_US",
                "rows": [wrong_page],
            })
        self.assertFalse(outcome["ok"])
        self.assertIn("PAGE_ROUTE_MISMATCH", {
            item["code"]
            for item in outcome["structure_preflight"]["violations"]
        })
        write.assert_not_called()

    def test_stage_atomically_rejects_any_invalid_kr_row(self):
        existing = {"ok": True, "columns": STAGING_COLUMNS,
                    "rows": [], "record_ids": []}
        good = valid_kr_values()
        bad = valid_kr_values(Row_key="weight", 手册值="")
        with mock.patch.object(server, "lark_records_all",
                               side_effect=[existing, CAPACITY_REFERENCE,
                                            EMPTY_REFERENCE]), \
                mock.patch.object(server, "run_lark_cli") as write:
            outcome = server.intake_stage({
                "document_key": "JE-TEST_KR",
                "sibling_document_key": "JE-TEST_US",
                "rows": [good, bad],
                "source_lang": "en",
            })
        self.assertFalse(outcome["ok"])
        self.assertEqual(outcome["staged"], 0)
        self.assertEqual(outcome["contract_version"], KR_CONTRACT_VERSION)
        write.assert_not_called()

    def test_stage_verifies_full_kr_row_after_write(self):
        existing = {"ok": True, "columns": STAGING_COLUMNS,
                    "rows": [], "record_ids": []}
        values = valid_kr_values()
        after = {
            "ok": True,
            "columns": STAGING_COLUMNS,
            "rows": [row_for(STAGING_COLUMNS, **values)],
            "record_ids": ["rec-stage-1"],
        }
        with mock.patch.object(server, "lark_records_all",
                               side_effect=[existing, CAPACITY_REFERENCE,
                                            EMPTY_REFERENCE, after]), \
                mock.patch.object(server, "run_lark_cli",
                                  return_value={"ok": True, "data": {}}) as write:
            outcome = server.intake_stage({
                "document_key": "JE-TEST_KR",
                "sibling_document_key": "JE-TEST_US",
                "rows": [values],
                "source_lang": "en",
            })
        self.assertTrue(outcome["ok"])
        self.assertTrue(outcome["readback_matches_staged"])
        self.assertEqual(outcome["staged_record_ids"], ["rec-stage-1"])
        write.assert_called_once()

    def test_stage_coverage_includes_prior_valid_pending_rows(self):
        capacity = valid_kr_values()
        weight = valid_kr_values(
            Row_key="weight", 行标签="Weight", 规格书原值="About 19.1Kg",
            手册值="About 19.1 kg",
        )
        existing = {"ok": True, "columns": STAGING_COLUMNS,
                    "rows": [row_for(STAGING_COLUMNS, **capacity)],
                    "record_ids": ["rec-capacity"]}
        reference = source_dataset(
            {"Page": "specifications", "Section": "GENERAL INFO",
             "Row_key": "capacity", "Slot_key": None, "Line_order": 1},
            {"Page": "specifications", "Section": "GENERAL INFO",
             "Row_key": "weight", "Slot_key": None, "Line_order": 1},
        )
        after = {"ok": True, "columns": STAGING_COLUMNS,
                 "rows": [row_for(STAGING_COLUMNS, **capacity),
                          row_for(STAGING_COLUMNS, **weight)],
                 "record_ids": ["rec-capacity", "rec-weight"]}
        with mock.patch.object(server, "lark_records_all",
                               side_effect=[existing, reference,
                                            EMPTY_REFERENCE, after]), \
                mock.patch.object(server, "run_lark_cli",
                                  return_value={"ok": True, "data": {}}):
            outcome = server.intake_stage({
                "document_key": "JE-TEST_KR",
                "sibling_document_key": "JE-TEST_US",
                "rows": [weight],
            })
        self.assertTrue(outcome["ok"])
        self.assertTrue(outcome["coverage_complete"])
        self.assertEqual(outcome["coverage_missing_rows"], [])

    def test_stage_does_not_require_korean_columns_for_english_source(self):
        columns = [column for column in STAGING_COLUMNS
                   if column not in {"手册值_ko", "行标签_ko"}]
        existing = {"ok": True, "columns": columns,
                    "rows": [], "record_ids": []}
        values = valid_kr_values()
        after = {
            "ok": True,
            "columns": columns,
            "rows": [row_for(columns, **values)],
            "record_ids": ["rec-source-only"],
        }
        with mock.patch.object(server, "lark_records_all",
                               side_effect=[existing, CAPACITY_REFERENCE,
                                            EMPTY_REFERENCE, after]), \
                mock.patch.object(server, "run_lark_cli",
                                  return_value={"ok": True, "data": {}}) as write:
            outcome = server.intake_stage({
                "document_key": "JE-TEST_KR",
                "sibling_document_key": "JE-TEST_US",
                "rows": [values],
                "source_lang": "en",
            })
        self.assertTrue(outcome["ok"])
        argv = write.call_args.args[0]
        payload = json.loads(argv[argv.index("--json") + 1])
        self.assertNotIn("手册值_ko", payload["fields"])
        self.assertNotIn("行标签_ko", payload["fields"])

    def test_status_separates_contract_blocked_rows(self):
        invalid = valid_kr_values(手册值="")
        staging = {
            "ok": True,
            "columns": STAGING_COLUMNS,
            "rows": [row_for(STAGING_COLUMNS, **invalid)],
            "record_ids": ["rec-invalid"],
        }
        with mock.patch.object(server, "lark_records_all", return_value=staging):
            outcome = server.intake_status({})
        self.assertEqual(len(outcome["contract_blocked"]), 1)
        self.assertEqual(outcome["pending_confirm"], [])
        self.assertEqual(outcome["kr_contract"]["blocked_rows"], 1)

    def test_commit_does_not_spawn_when_kr_contract_is_blocked(self):
        blocked = {"record_id": "rec-invalid", "contract_violations": [
            {"code": "MISSING_VALUE_SOURCE"}
        ]}
        with mock.patch.object(server, "intake_status", return_value={
            "ok": True,
            "contract_blocked": [blocked],
            "confirmed_ready": [],
        }), mock.patch.object(server, "_spawn_job") as spawn:
            outcome = server.intake_commit({
                "document_key": "JE-TEST_KR",
                "sibling_document_key": "JE-TEST_US",
                "confirm_ingest": True,
                "approved_by": "tester",
            })
        self.assertFalse(outcome["ok"])
        spawn.assert_not_called()

    def test_discard_requires_explicit_current_turn_approval(self):
        with mock.patch.object(server, "lark_records_all") as read, \
                mock.patch.object(server, "run_lark_cli") as write:
            outcome = server.intake_discard({
                "document_key": "JE-TEST_KR", "record_ids": ["rec-old"],
                "reason": "wrong structure", "discarded_by": "tester",
            })
        self.assertFalse(outcome["ok"])
        read.assert_not_called()
        write.assert_not_called()

    def test_discard_marks_unconfirmed_rows_and_reads_back(self):
        values = valid_kr_values()
        existing = {"ok": True, "columns": STAGING_COLUMNS,
                    "rows": [row_for(STAGING_COLUMNS, **values)],
                    "record_ids": ["rec-old"]}
        marker = f"已作废 {date.today().isoformat()} by tester: wrong structure"
        after_values = {**values, "入库结果": marker}
        after = {"ok": True, "columns": STAGING_COLUMNS,
                 "rows": [row_for(STAGING_COLUMNS, **after_values)],
                 "record_ids": ["rec-old"]}
        with mock.patch.object(server, "lark_records_all",
                               side_effect=[existing, after]), \
                mock.patch.object(server, "run_lark_cli",
                                  return_value={"ok": True, "data": {}}) as write:
            outcome = server.intake_discard({
                "document_key": "JE-TEST_KR", "record_ids": ["rec-old"],
                "reason": "wrong structure", "discarded_by": "tester",
                "confirm_discard": True,
            })
        self.assertTrue(outcome["ok"])
        self.assertTrue(outcome["readback_ok"])
        self.assertEqual(outcome["discarded"], 1)
        write.assert_called_once()


class DriverKrContractTests(unittest.TestCase):
    def test_table_key_distinguishes_input_and_output_sections(self):
        columns = ["Page", "Section", "Row_key", "Slot_key", "Line_order"]
        rows = [
            row_for(columns, Page="specifications", Section="INPUT PORTS",
                    Row_key="dc_expansion_port", Slot_key=None, Line_order=1),
            row_for(columns, Page="specifications", Section="OUTPUT PORTS",
                    Row_key="dc_expansion_port", Slot_key=None, Line_order=1),
        ]
        dataset = {"columns": columns, "rows": rows,
                   "record_ids": ["rec-input", "rec-output"]}
        with mock.patch.object(driver, "read_rows", return_value=dataset):
            table = driver.Table(driver.SPEC_TABLE, "JE-TEST_US")
        self.assertEqual(
            [record_id for record_id, _row in table.matches(
                ("specifications", "dc_expansion_port", "", "input ports", "1")
            )],
            ["rec-input"],
        )
        self.assertEqual(
            [record_id for record_id, _row in table.matches(
                ("specifications", "dc_expansion_port", "", "output ports", "1")
            )],
            ["rec-output"],
        )

    def run_driver(self, read_rows_side_effect) -> tuple[dict, mock.Mock, mock.Mock]:
        with tempfile.TemporaryDirectory() as temp_dir, \
                mock.patch.object(driver, "read_rows", side_effect=read_rows_side_effect), \
                mock.patch.object(driver, "upsert") as upsert, \
                mock.patch.object(driver, "batch_create") as batch_create, \
                mock.patch.object(driver, "run_close_checks",
                                  return_value={"check": {"ok": True}}), \
                mock.patch.object(sys, "argv", [
                    "intake_commit_driver.py",
                    "--document-key", "JE-TEST_KR",
                    "--sibling-document-key", "JE-TEST_US",
                    "--approved-by", "tester",
                    "--job-dir", temp_dir,
                ]):
            driver.main()
            result = json.loads((Path(temp_dir) / "result.json").read_text())
            return result, upsert, batch_create

    def test_driver_rejects_bad_pending_kr_row_before_any_write(self):
        invalid = valid_kr_values(手册值="")
        staging = {"columns": STAGING_COLUMNS,
                   "rows": [row_for(STAGING_COLUMNS, **invalid)],
                   "record_ids": ["rec-invalid"]}
        result, upsert, batch_create = self.run_driver(lambda *_args: staging)
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["formal_source_writes"], 0)
        upsert.assert_not_called()
        batch_create.assert_not_called()

    def test_driver_updates_english_source_without_overwriting_korean(self):
        confirmed = valid_kr_values(确认=True)
        staging = {"columns": STAGING_COLUMNS,
                   "rows": [row_for(STAGING_COLUMNS, **confirmed)],
                   "record_ids": ["rec-confirmed"]}
        source_columns = sorted({
            *driver.KR_SOURCE_REQUIRED_FIELDS,
            "Slot_key",
            "Line_order",
            "Page",
            "Section",
            *driver.LANG_VALUE_COLUMNS,
        })
        before_values = {
            "document_key": "JE-TEST_KR",
            "Row_key": "capacity",
            "Slot_key": None,
            "Line_order": 1,
            "Page": "specifications",
            "Section": "GENERAL INFO",
            "Value_source": "old",
            "Value_ko": "이전",
            "Row_label_source": "Old label",
            "Row_label_ko": "이전 라벨",
            "Source_lang": "en",
        }
        after_values = {
            **before_values,
            "Value_source": "2048 Wh",
            "Row_label_source": "Capacity",
        }
        sibling_values = {
            **before_values,
            "document_key": "JE-TEST_US",
            "Value_source": "2048 Wh",
            "Row_label_source": "Capacity",
            "Value_ko": "",
            "Row_label_ko": "",
        }
        target_spec_reads = 0

        def fake_read_rows(table_id, document_key=None):
            nonlocal target_spec_reads
            if table_id == driver.STAGING_TABLE:
                return staging
            if table_id == driver.SPEC_TABLE and document_key == "JE-TEST_KR":
                target_spec_reads += 1
                values = before_values if target_spec_reads == 1 else after_values
                return {"columns": source_columns,
                        "rows": [row_for(source_columns, **values)],
                        "record_ids": ["rec-source"]}
            if table_id == driver.SPEC_TABLE and document_key == "JE-TEST_US":
                return {"columns": source_columns,
                        "rows": [row_for(source_columns, **sibling_values)],
                        "record_ids": ["rec-sibling"]}
            return {"columns": source_columns, "rows": [], "record_ids": []}

        result, upsert, batch_create = self.run_driver(fake_read_rows)
        self.assertEqual(result["status"], "done")
        self.assertTrue(result["updated"][0]["readback_ok"])
        self.assertEqual(result["updated"][0]["readback_record_id"], "rec-source")
        source_write = upsert.call_args_list[0].args
        self.assertEqual(source_write[0:2], (driver.SPEC_TABLE, "rec-source"))
        self.assertEqual(source_write[2], {
            "Value_source": "2048 Wh",
            "Row_label_source": "Capacity",
            "Source_lang": "en",
        })
        staging_result = upsert.call_args_list[-1].args[2]["入库结果"]
        self.assertTrue(staging_result.startswith("已入库 update rec-source"))
        batch_create.assert_not_called()

    def test_driver_structure_preflight_is_zero_write_for_kr(self):
        confirmed = valid_kr_values(确认=True)
        staging = {"columns": STAGING_COLUMNS,
                   "rows": [row_for(STAGING_COLUMNS, **confirmed)],
                   "record_ids": ["rec-confirmed"]}
        source_columns = sorted({
            *driver.KR_SOURCE_REQUIRED_FIELDS,
            "Slot_key",
            "Line_order",
        })

        def fake_read_rows(table_id, _document_key=None):
            if table_id == driver.STAGING_TABLE:
                return staging
            return {"columns": source_columns, "rows": [], "record_ids": []}

        result, upsert, batch_create = self.run_driver(fake_read_rows)
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["formal_source_writes"], 0)
        self.assertIn("结构/完整性预检失败", result["error"])
        upsert.assert_not_called()
        batch_create.assert_not_called()


if __name__ == "__main__":
    unittest.main()
