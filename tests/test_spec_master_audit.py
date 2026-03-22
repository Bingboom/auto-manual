from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.audit_spec_master import render_markdown, write_issues_csv, write_section_summary_csv
from tools.normalize_spec_master import write_csv
from tools.utils.spec_master import audit_spec_master_csv, audit_spec_master_rows, normalize_spec_master_rows


class TestSpecMasterAudit(unittest.TestCase):
    def test_audit_should_detect_section_conflicts_and_row_level_quality_issues(self) -> None:
        rows = [
            {
                "project_code": "HTE152-US",
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Section": "GENERAL INFO",
                "Section_order": "1",
                "Row_key": "product_name",
                "Row_label_en": "Product Name",
                "Line_order": "1",
                "Value_en": "Jackery HomePower 2000 Plus v2",
                "Model": "JHP-2000A",
                "__line__": "2",
            },
            {
                "project_code": "HTE152-JP",
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Section": "GENERAL INFO",
                "Section_order": "1",
                "Row_key": "model_no",
                "Row_label_en": "Model No.",
                "Line_order": "1",
                "Value_en": "JHP-2000A",
                "Model": "JHP-2000A",
                "__line__": "3",
            },
            {
                "project_code": "HTE154-US",
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Section": "ENVIRONMENTAL OPERATING TEMPERATURE",
                "Section_order": "4",
                "Row_key": "charging_temperature",
                "Row_label_en": "Charging Temperature",
                "Line_order": "1",
                "Value_en": "-20C to 45C",
                "Model": "JE-2000F",
                "__line__": "4",
            },
            {
                "project_code": "HTE154-JP",
                "Region": "JP",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Section": "ENVIRONMENTAL",
                "Section_order": "4",
                "Row_key": "humidity",
                "Row_label_en": "動作湿度",
                "Line_order": "1",
                "Value_en": "0~60% RH",
                "Model": "JE-2000E",
                "__line__": "5",
            },
            {
                "project_code": "HTE154-US",
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Section": "TEMPLATE VARS",
                "Section_order": "99",
                "Row_key": "tpl_main_power_button_label",
                "Row_label_en": "Main Power Button Label",
                "Line_order": "1",
                "Value_en": "Main POWER Button???",
                "Model": "JE-2000F",
                "__line__": "6",
            },
            {
                "project_code": "HTE152-US",
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Section": "GENERAL INFO",
                "Section_order": "1",
                "Row_key": "product_name",
                "Row_label_en": "Product Name",
                "Line_order": "1",
                "Value_en": "Jackery HomePower 2000 Plus v2",
                "Model": "JHP-2000A",
                "__line__": "7",
            },
        ]

        audit = audit_spec_master_rows(rows)
        issue_codes = {issue.code for issue in audit.issues}

        self.assertEqual(4, audit.unique_sections)
        self.assertIn("SECTION_ORDER_COLLISION", issue_codes)
        self.assertIn("PROJECT_REGION_MISMATCH", issue_codes)
        self.assertIn("ROW_LABEL_EN_CONTAINS_EAST_ASIAN_TEXT", issue_codes)
        self.assertIn("SUSPECT_TEMPLATE_VALUE", issue_codes)
        self.assertIn("EXACT_DUPLICATE_ROW", issue_codes)

        summaries = {summary.section: summary for summary in audit.section_summaries}
        self.assertEqual("ENVIRONMENTAL", summaries["ENVIRONMENTAL OPERATING TEMPERATURE"].suggested_section)
        self.assertEqual("template", summaries["TEMPLATE VARS"].category)

    def test_cli_report_helpers_should_write_csv_and_markdown_outputs(self) -> None:
        csv_text = "\n".join(
            [
                "project_code,Region,Is_Latest,Page,Section,Section_order,Row_key,Row_label_en,Line_order,Value_en,Model",
                "HTE154-US,US,TRUE,specifications,TEMPLATE VARS,99,tpl_main_power_button_label,Main Power Button Label,1,Main POWER Button???,JE-2000F",
                "HTE154-US,US,TRUE,specifications,ENVIRONMENTAL OPERATING TEMPERATURE,4,charging_temperature,Charging Temperature,1,-20C to 45C,JE-2000F",
                "HTE154-JP,JP,TRUE,specifications,ENVIRONMENTAL,4,humidity,動作湿度,1,0~60% RH,JE-2000E",
            ]
        )

        with tempfile.TemporaryDirectory() as td:
            temp_dir = Path(td)
            csv_path = temp_dir / "Spec_Master.csv"
            out_dir = temp_dir / "reports"
            csv_path.write_text(csv_text + "\n", encoding="utf-8")

            audit = audit_spec_master_csv(csv_path)
            section_csv_path = out_dir / "section_summary.csv"
            issues_csv_path = out_dir / "issues.csv"

            write_section_summary_csv(section_csv_path, audit.section_summaries)
            write_issues_csv(issues_csv_path, audit.issues)
            report = render_markdown(
                audit,
                csv_path=csv_path,
                section_csv_path=section_csv_path,
                issues_csv_path=issues_csv_path,
                sample_limit=10,
            )

            self.assertTrue(section_csv_path.exists())
            self.assertTrue(issues_csv_path.exists())
            self.assertIn("Recommended Section Map", report)
            self.assertIn("SECTION_ORDER_COLLISION", report)
            self.assertIn("SUSPECT_TEMPLATE_VALUE", report)

    def test_audit_should_flag_kana_in_english_label_column(self) -> None:
        rows = [
            {
                "project_code": "HTE154-JP",
                "Region": "JP",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Section": "OUTPUT PORTS",
                "Section_order": "3",
                "Row_key": "usb_c",
                "Row_label_en": "USB-Cポート",
                "Line_order": "1",
                "Value_en": "100W Max",
                "Model": "JE-2000E",
                "__line__": "8",
            },
        ]

        audit = audit_spec_master_rows(rows)
        self.assertEqual(1, len(audit.issues))
        self.assertEqual("ROW_LABEL_EN_CONTAINS_EAST_ASIAN_TEXT", audit.issues[0].code)

    def test_normalization_should_replace_section_and_collect_anomaly_rows(self) -> None:
        rows = [
            {
                "project_code": "HTE154-US",
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Section": "ENVIRONMENTAL OPERATING TEMPERATURE",
                "Section_order": "4",
                "Row_key": "charging_temperature",
                "Row_label_en": "Charging Temperature",
                "Line_order": "1",
                "Value_en": "-20C to 45C",
                "Model": "JE-2000F",
                "__line__": "4",
            },
            {
                "project_code": "",
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Section": "TEMPLATE VARS",
                "Section_order": "99",
                "Row_key": "tpl_main_power_button_label",
                "Row_label_en": "Main Power Button Label",
                "Line_order": "1",
                "Value_en": "Main POWER Button???",
                "Model": "JE-2000F",
                "__line__": "5",
            },
        ]

        result = normalize_spec_master_rows(rows)
        self.assertEqual(2, len(result.normalized_rows))
        self.assertEqual(2, len(result.anomaly_rows))

        env_row = result.normalized_rows[0]
        self.assertEqual("ENVIRONMENTAL", env_row["Section"])
        self.assertEqual("ENVIRONMENTAL OPERATING TEMPERATURE", env_row["Section_original"])
        self.assertEqual("YES", env_row["Normalization_applied"])
        self.assertIn("SECTION_NORMALIZED", env_row["Review_flags"])

        template_row = result.normalized_rows[1]
        self.assertEqual("template", template_row["Record_category"])
        self.assertIn("TEMPLATE_RECORD", template_row["Review_flags"])
        self.assertIn("SUSPECT_TEMPLATE_VALUE", template_row["Review_flags"])

    def test_write_csv_should_emit_normalized_outputs_with_metadata_columns(self) -> None:
        rows = (
            {
                "project_code": "HTE154-US",
                "Region": "US",
                "Section": "ENVIRONMENTAL",
                "Section_original": "ENVIRONMENTAL OPERATING TEMPERATURE",
                "Section_normalized": "ENVIRONMENTAL",
                "Record_category": "spec",
                "Normalization_applied": "YES",
                "Normalization_note": "note",
                "Source_line": "4",
                "Review_flags": "SECTION_NORMALIZED",
                "Review_messages": "message",
            },
        )

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "normalized.csv"
            write_csv(path, rows)
            text = path.read_text(encoding="utf-8")

        self.assertIn("Section_original", text)
        self.assertIn("Section_normalized", text)
        self.assertIn("Review_flags", text)


if __name__ == "__main__":
    unittest.main()
