from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.repair_spec_master import write_repairs_csv, write_rows_csv
from tools.utils.spec_master import (
    build_template_row_key_mapping_markdown,
    build_template_row_key_mapping_rows,
    repair_known_spec_master_values,
)


class TestSpecMasterRepairs(unittest.TestCase):
    def test_repair_known_spec_master_values_should_fix_targeted_rows(self) -> None:
        rows = [
            {
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Section": "ENVIRONMENTAL OPERATING TEMPERATURE",
                "Section_order": "4",
                "Row_key": "charging_temperature",
                "Row_label_source": "Charging Temperature",
                "Line_order": "1",
                "Value_source": "-20C to 45C",
                "Model": "JE-2000F",
                "__line__": "138",
            },
            {
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Section": "BATTERY",
                "Section_order": "5",
                "Row_key": "field_001",
                "Row_label_source": "棰濆畾瀹归噺",
                "Line_order": "1",
                "Value_source": "2048Wh",
                "Model": "JHP-2000A",
                "__line__": "4",
            },
            {
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Section": "TEMPLATE VARS",
                "Section_order": "99",
                "Row_key": "tpl_front_dc12_port_spec",
                "Row_label_source": "Front DC12 Port Spec",
                "Line_order": "1",
                "Value_source": "12V?10A Max",
                "Model": "JE-2000F",
                "__line__": "302",
            },
            {
                "Region": "JP",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Section": "TEMPLATE VARS",
                "Section_order": "99",
                "Row_key": "tpl_main_power_button_label",
                "Row_label_source": "Main Power Button Label",
                "Line_order": "1",
                "Value_source": "??????",
                "Model": "JE-2000F",
                "__line__": "326",
            },
            {
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Section": "TEMPLATE VARS",
                "Section_order": "99",
                "Row_key": "tpl_main_power_button_label",
                "Row_label_source": "Main Power Button Label",
                "Line_order": "1",
                "Value_source": "Main POWER Button",
                "Model": "JE-2000F",
                "__line__": "298",
            },
        ]

        result = repair_known_spec_master_values(rows)
        self.assertEqual(13, len(result.applied_repairs))
        self.assertEqual((), result.removed_duplicate_lines)

        self.assertEqual("ENVIRONMENTAL", result.repaired_rows[0]["Section"])
        self.assertEqual("Rated Capacity", result.repaired_rows[1]["Row_label_source"])

        self.assertEqual("OUTPUT PORTS", result.repaired_rows[2]["Section"])
        self.assertEqual("3", result.repaired_rows[2]["Section_order"])
        self.assertEqual("DC 12V Port", result.repaired_rows[2]["Row_label_source"])
        self.assertEqual("12V/10A Max", result.repaired_rows[2]["Value_source"])

        self.assertEqual("CONTROLS", result.repaired_rows[3]["Section"])
        self.assertEqual("7", result.repaired_rows[3]["Section_order"])
        self.assertEqual("Main Power Button", result.repaired_rows[3]["Row_label_source"])
        self.assertEqual("メイン電源ボタン", result.repaired_rows[3]["Value_source"])

        self.assertEqual("CONTROLS", result.repaired_rows[4]["Section"])
        self.assertEqual("7", result.repaired_rows[4]["Section_order"])
        self.assertEqual("Main Power Button", result.repaired_rows[4]["Row_label_source"])
        self.assertEqual("Main POWER Button", result.repaired_rows[4]["Value_source"])

    def test_repair_should_drop_duplicate_rows_after_section_normalization(self) -> None:
        rows = [
            {
                "Region": "JP",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Section": "ENVIRONMENTAL OPERATING TEMPERATURE",
                "Section_order": "4",
                "Row_key": "product_name",
                "Row_label_source": "Product Name",
                "Line_order": "1",
                "Value_source": "Jackery Portable Power 2000 Plus",
                "Model": "JE-2000E",
                "__line__": "71",
            },
            {
                "Region": "JP",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Section": "ENVIRONMENTAL",
                "Section_order": "4",
                "Row_key": "product_name",
                "Row_label_source": "Product Name",
                "Line_order": "1",
                "Value_source": "Jackery Portable Power 2000 Plus",
                "Model": "JE-2000E",
                "__line__": "72",
            },
        ]

        result = repair_known_spec_master_values(rows)
        self.assertEqual(1, len(result.applied_repairs))
        self.assertEqual(1, len(result.repaired_rows))
        self.assertEqual((72,), result.removed_duplicate_lines)
        self.assertEqual("ENVIRONMENTAL", result.repaired_rows[0]["Section"])

    def test_write_rows_csv_and_repairs_csv_should_persist_outputs(self) -> None:
        rows = (
            {
                "Region": "US",
                "Row_key": "tpl_front_dc12_port_spec",
                "Value_source": "12V/10A Max",
            },
        )

        repairs = ()

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rows_path = root / "rows.csv"
            repairs_path = root / "repairs.csv"

            write_rows_csv(rows_path, rows)
            write_repairs_csv(repairs_path, repairs)

            with rows_path.open("r", encoding="utf-8-sig", newline="") as handle:
                loaded_rows = list(csv.DictReader(handle))
            with repairs_path.open("r", encoding="utf-8", newline="") as handle:
                loaded_repairs = list(csv.DictReader(handle))

        self.assertEqual("12V/10A Max", loaded_rows[0]["Value_source"])
        self.assertEqual([], loaded_repairs)

    def test_build_template_row_key_mapping_rows_should_capture_usage(self) -> None:
        rows = [
            {
                "Region": "US",
                "Section": "OUTPUT PORTS",
                "Section_order": "3",
                "Row_key": "tpl_front_dc12_port_spec",
                "Row_label_source": "DC 12V Port",
                "Model": "JE-2000F",
            },
            {
                "Region": "JP",
                "Section": "OUTPUT PORTS",
                "Section_order": "3",
                "Row_key": "tpl_front_dc12_port_spec",
                "Row_label_source": "DC 12V Port",
                "Model": "JE-2000F",
            },
            {
                "Region": "US",
                "Section": "INPUT PORTS",
                "Section_order": "2",
                "Row_key": "tpl_side_ac_input_spec",
                "Row_label_source": "AC Input",
                "Model": "JE-2000F",
            },
        ]

        mapping_rows = build_template_row_key_mapping_rows(rows)
        dc12_row = next(row for row in mapping_rows if row["Row_key"] == "tpl_front_dc12_port_spec")
        ac_input_row = next(row for row in mapping_rows if row["Row_key"] == "tpl_side_ac_input_spec")

        self.assertEqual("OUTPUT PORTS", dc12_row["Section"])
        self.assertEqual("3", dc12_row["Section_order"])
        self.assertEqual("DC 12V Port", dc12_row["Row_label_source"])
        self.assertEqual("2", dc12_row["Usage_count"])
        self.assertEqual("JE-2000F", dc12_row["Models"])
        self.assertEqual("JP,US", dc12_row["Regions"])
        self.assertEqual("OUTPUT PORTS", dc12_row["Observed_sections"])

        self.assertEqual("INPUT PORTS", ac_input_row["Section"])
        self.assertEqual("AC Input", ac_input_row["Row_label_source"])
        self.assertEqual("1", ac_input_row["Usage_count"])

    def test_build_template_row_key_mapping_markdown_should_group_by_section(self) -> None:
        mapping_rows = (
            {
                "Row_key": "tpl_side_ac_input_spec",
                "Section": "INPUT PORTS",
                "Section_order": "2",
                "Row_label_source": "AC Input",
                "Usage_count": "5",
                "Models": "JE-1000F,JE-2000E,JE-2000F",
                "Regions": "JP,US",
                "Observed_sections": "INPUT PORTS",
                "Observed_section_orders": "2",
                "Observed_row_labels_source": "AC Input",
            },
            {
                "Row_key": "tpl_main_power_button_label",
                "Section": "CONTROLS",
                "Section_order": "7",
                "Row_label_source": "Main Power Button",
                "Usage_count": "5",
                "Models": "JE-1000F,JE-2000E,JE-2000F",
                "Regions": "JP,US",
                "Observed_sections": "CONTROLS",
                "Observed_section_orders": "7",
                "Observed_row_labels_source": "Main Power Button",
            },
        )

        markdown = build_template_row_key_mapping_markdown(mapping_rows)

        self.assertIn("# Spec Master Row Key Mapping", markdown)
        self.assertIn("## INPUT PORTS (`2`)", markdown)
        self.assertIn("## CONTROLS (`7`)", markdown)
        self.assertIn("| tpl_side_ac_input_spec | AC Input | 5 |", markdown)
        self.assertIn("| tpl_main_power_button_label | Main Power Button | 5 |", markdown)


if __name__ == "__main__":
    unittest.main()

