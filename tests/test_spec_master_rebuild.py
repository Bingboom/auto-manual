from __future__ import annotations

import unittest

from tools import spec_master_rebuild


class TestSpecMasterRebuild(unittest.TestCase):
    def test_spec_row_key_should_use_stable_display_order_tokens(self) -> None:
        key = spec_master_rebuild.spec_row_key(
            {
                "document_key": "JE-1000F_US",
                "Version": ["1.0"],
                "Page": ["specifications"],
                "Section_order": 1,
                "Row_order": 3,
                "Row_key": "capacity",
                "Slot_key": None,
                "Line_order": 1,
            }
        )

        self.assertEqual("JE-1000F_US__v1.0__specifications__s01__r03__capacity__main__l01", key)

    def test_spec_row_key_should_slug_page_and_slot_without_value_summary(self) -> None:
        key = spec_master_rebuild.spec_row_key(
            {
                "document_key": "JE-1000F_US",
                "Version": "1.0",
                "Page": ["Product overview"],
                "Section_order": "3",
                "Row_order": "2",
                "Row_key": "usb_c",
                "Slot_key": "front high spec",
                "Line_order": "1",
                "Value_source": "100W Max",
            }
        )

        self.assertEqual("JE-1000F_US__v1.0__Product_overview__s03__r02__usb_c__front_high_spec__l01", key)

    def test_spec_row_key_should_use_display_text_from_feishu_rich_text_links(self) -> None:
        key = spec_master_rebuild.spec_row_key(
            {
                "document_key": "JE-1000F_US",
                "Version": ["1.0"],
                "Page": ["Product overview"],
                "Section_order": 3,
                "Row_order": 1,
                "Row_key": "dc12_port",
                "Slot_key": "[front.label](front.label)",
                "Line_order": 1,
            }
        )

        self.assertEqual("JE-1000F_US__v1.0__Product_overview__s03__r01__dc12_port__front.label__l01", key)

    def test_source_rows_should_not_write_formula_primary_field_values(self) -> None:
        self.assertNotIn("source_row_key", spec_master_rebuild.SOURCE_FIELD_ORDER)
        self.assertNotIn("Row_key", spec_master_rebuild.SOURCE_FIELD_ORDER)
        self.assertNotIn("Model", spec_master_rebuild.SOURCE_FIELD_ORDER)
        self.assertNotIn("Region", spec_master_rebuild.SOURCE_FIELD_ORDER)

    def test_fill_model_region_should_derive_from_document_key(self) -> None:
        row = {"document_key": "JE-1000F_pt-BR", "Model": "", "Region": ""}

        spec_master_rebuild._fill_model_region_from_document_key(row)

        self.assertEqual("JE-1000F", row["Model"])
        self.assertEqual("pt-BR", row["Region"])

    def test_total_patch_should_derive_model_region_when_source_fields_are_absent(self) -> None:
        patch = spec_master_rebuild._total_patch_from_source_record(
            {"fields": {"document_key": "JE-2000E_US"}},
            {"document_key": {"type": "text"}, "Model": {"type": "text"}, "Region": {"type": "text"}},
        )

        self.assertEqual({"document_key": "JE-2000E_US", "Model": "JE-2000E", "Region": "US"}, patch)

    def test_row_key_lookup_definition_should_read_dictionary_row_key(self) -> None:
        field = spec_master_rebuild._row_key_lookup_definition(
            {"Row_key_link": {"id": "fld_link"}},
            {"Row_key": {"id": "fld_row_key"}},
        )

        self.assertEqual(
            {
                "name": "Row_key",
                "type": "lookup",
                "from": "参数名",
                "select": "fld_row_key",
                "aggregate": "unique",
                "where": {
                    "logic": "and",
                    "conditions": [
                        ["Row_label_source", "intersects", {"type": "field_ref", "field": "Row_key_link"}],
                    ],
                },
            },
            field,
        )

    def test_validate_merged_rows_should_require_unique_keys_and_expected_split_counts(self) -> None:
        rows = [
            {
                "spec_row_key": "a",
                "Page": "specifications",
            },
            {
                "spec_row_key": "b",
                "Page": "Product overview",
            },
        ]

        spec_master_rebuild._validate_merged_rows(rows, expect_spec_rows=1, expect_placeholder_rows=1)
        with self.assertRaisesRegex(RuntimeError, "Duplicate spec_row_key"):
            spec_master_rebuild._validate_merged_rows([*rows, dict(rows[0])], expect_spec_rows=None, expect_placeholder_rows=None)

    def test_format_command_for_log_should_redact_base_token(self) -> None:
        text = spec_master_rebuild._format_command_for_log(
            ["lark-cli", "base", "+field-list", "--base-token", "secret-token", "--table-id", "tbl1"]
        )

        self.assertIn("--base-token <redacted>", text)
        self.assertNotIn("secret-token", text)


if __name__ == "__main__":
    unittest.main()
