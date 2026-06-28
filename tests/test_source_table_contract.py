from __future__ import annotations

import unittest

from tools import source_table_contract
from tools.data_snapshot import PHASE2_REQUIRED_TABLE_FILES
from tools.source_intake_model import (
    FOOTNOTE_TEXT_FIELDS,
    MANUAL_COPY_TEXT_FIELDS,
    NOTE_TEXT_FIELDS,
    SPEC_TEXT_FIELDS,
    TARGET_MANUAL_COPY,
    TARGET_PAGE_PLACEHOLDERS,
    TARGET_SPEC_FOOTNOTES,
    TARGET_SPEC_MASTER,
    TARGET_SPEC_NOTES,
    UPDATE_CAPABLE_TABLES,
)
from tools.source_record_index import TABLE_FALLBACK_KEY_FIELDS, TABLE_KEY_FIELDS, TABLE_OPTIONAL_KEY_FIELDS


class SourceTableContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = source_table_contract.load_source_table_contract()
        cls.tables = source_table_contract.source_table_by_name(cls.contract)

    def test_contract_shape_is_valid(self) -> None:
        result = source_table_contract.validate_source_table_contract(self.contract)

        self.assertTrue(
            result.valid,
            "\n".join(issue.format() for issue in result.issues),
        )

    def test_intake_target_tables_are_declared(self) -> None:
        self.assertEqual(
            {
                TARGET_SPEC_MASTER,
                TARGET_PAGE_PLACEHOLDERS,
                TARGET_MANUAL_COPY,
                TARGET_SPEC_FOOTNOTES,
                TARGET_SPEC_NOTES,
            },
            source_table_contract.intake_target_tables(self.contract),
        )

    def test_update_capable_tables_match_source_intake_writer(self) -> None:
        self.assertEqual(
            set(UPDATE_CAPABLE_TABLES),
            source_table_contract.change_request_update_tables(self.contract),
        )

    def test_writable_fields_match_source_intake_model(self) -> None:
        self.assertEqual(
            list(SPEC_TEXT_FIELDS),
            self.tables[TARGET_SPEC_MASTER]["writeback"]["writable_fields"],
        )
        self.assertEqual(
            list(SPEC_TEXT_FIELDS),
            self.tables[TARGET_PAGE_PLACEHOLDERS]["writeback"]["writable_fields"],
        )
        self.assertEqual(
            list(MANUAL_COPY_TEXT_FIELDS),
            self.tables[TARGET_MANUAL_COPY]["writeback"]["writable_fields"],
        )
        self.assertFalse(self.tables[TARGET_SPEC_FOOTNOTES]["writeback"]["change_request_update"])
        self.assertFalse(self.tables[TARGET_SPEC_NOTES]["writeback"]["change_request_update"])
        self.assertTrue(set(FOOTNOTE_TEXT_FIELDS) <= set(self.tables[TARGET_SPEC_FOOTNOTES]["intake"]["candidate_fields"]))
        self.assertTrue(set(NOTE_TEXT_FIELDS) <= set(self.tables[TARGET_SPEC_NOTES]["intake"]["candidate_fields"]))

    def test_snapshot_contract_matches_required_phase2_files(self) -> None:
        by_logical_name = {
            table["snapshot"]["logical_name"]: table["snapshot"]["file"]
            for table in self.tables.values()
            if table.get("snapshot", {}).get("logical_name")
        }

        for logical_name, file_name in PHASE2_REQUIRED_TABLE_FILES.items():
            self.assertEqual(file_name, by_logical_name[logical_name])

    def test_source_record_index_keys_match_contract(self) -> None:
        for table_name, key_fields in TABLE_KEY_FIELDS.items():
            table = self.tables[table_name]
            self.assertEqual(list(key_fields), table["identity"]["business_key_fields"])
            self.assertEqual(
                sorted(TABLE_OPTIONAL_KEY_FIELDS.get(table_name, frozenset())),
                sorted(table["identity"]["optional_key_fields"]),
            )
            self.assertEqual(
                [csv_field for csv_field, _ in TABLE_FALLBACK_KEY_FIELDS.get(table_name, ())],
                table["identity"]["fallback_key_fields"],
            )


if __name__ == "__main__":
    unittest.main()
