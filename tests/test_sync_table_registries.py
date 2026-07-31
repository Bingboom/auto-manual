from __future__ import annotations

import unittest
from pathlib import Path

from tools.data_snapshot import PHASE2_REQUIRED_DERIVED_FILES, PHASE2_REQUIRED_TABLE_FILES
from tools.schema_drift import REQUIRED_CSV_HEADERS
from tools.source_table_contract import load_source_table_contract, source_tables
from tools.sync_data_models import TABLE_SCHEMAS


# These are intentional topology differences between the registries.  Keep
# them explicit so a new difference cannot be introduced accidentally under
# the guise of an existing exception.
REGISTRY_EXEMPTIONS = {
    "table_schemas": {
        "translation_memory": (
            "Translation_Memory is a separate online base; its derived outputs "
            "are declared under phase2_source_tables.json.derived_contracts, not "
            "as a required phase2 source-table snapshot."
        ),
    },
    "source_table_contract": {
        "Page_Placeholders_Source": (
            "Page placeholders and specification rows are materialized together "
            "in Spec_Master.csv and separated by row_filter."
        ),
    },
    "csv_headers": {
        "page_registry": (
            "page_registry.csv is a repo-maintained input with its own reader "
            "contract; it is not part of the fixed-header registry."
        ),
    },
}


class SyncTableRegistriesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_source_table_contract()
        cls.contract_tables = source_tables(cls.contract)

    def test_registry_exemptions_are_explicitly_justified(self) -> None:
        self.assertEqual(
            set(REGISTRY_EXEMPTIONS),
            {"table_schemas", "source_table_contract", "csv_headers"},
        )
        for registry_name, exemptions in REGISTRY_EXEMPTIONS.items():
            with self.subTest(registry=registry_name):
                self.assertTrue(exemptions)
                for item, reason in exemptions.items():
                    with self.subTest(item=item):
                        self.assertTrue(reason.strip())

    def test_required_source_tables_close_over_table_schemas(self) -> None:
        required_tables = set(PHASE2_REQUIRED_TABLE_FILES)
        schema_tables = set(TABLE_SCHEMAS)
        schema_extras = schema_tables - required_tables

        self.assertEqual(
            schema_extras,
            set(REGISTRY_EXEMPTIONS["table_schemas"]),
            "Every TABLE_SCHEMAS extra must have an explicit topology exemption",
        )
        self.assertEqual(
            required_tables,
            schema_tables - set(REGISTRY_EXEMPTIONS["table_schemas"]),
        )

        for logical_name, file_name in PHASE2_REQUIRED_TABLE_FILES.items():
            with self.subTest(table=logical_name):
                self.assertEqual(TABLE_SCHEMAS[logical_name].file_name, file_name)

    def test_required_file_and_header_registries_are_schema_derived(self) -> None:
        self.assertEqual(
            PHASE2_REQUIRED_TABLE_FILES,
            {
                logical_name: schema.file_name
                for logical_name, schema in TABLE_SCHEMAS.items()
                if logical_name in PHASE2_REQUIRED_TABLE_FILES
            },
        )
        self.assertEqual(
            {
                logical_name: REQUIRED_CSV_HEADERS[logical_name]
                for logical_name in PHASE2_REQUIRED_TABLE_FILES
            },
            {
                logical_name: schema.required_headers
                for logical_name, schema in TABLE_SCHEMAS.items()
                if logical_name in PHASE2_REQUIRED_TABLE_FILES
            },
        )

    def test_source_contract_maps_required_source_files_exactly(self) -> None:
        snapshot_rows = [
            (
                str(table.get("contract_name") or "").strip(),
                str((table.get("snapshot") or {}).get("logical_name") or "").strip(),
                str((table.get("snapshot") or {}).get("file") or "").strip(),
            )
            for table in self.contract_tables
        ]
        snapshot_rows = [row for row in snapshot_rows if row[1] and row[2]]

        self.assertEqual(
            {(logical_name, file_name) for _, logical_name, file_name in snapshot_rows},
            set(PHASE2_REQUIRED_TABLE_FILES.items()),
        )

        aliases = {
            contract_name: (logical_name, file_name)
            for contract_name, logical_name, file_name in snapshot_rows
            if contract_name in REGISTRY_EXEMPTIONS["source_table_contract"]
        }
        self.assertEqual(
            aliases,
            {
                "Page_Placeholders_Source": ("spec_master", "Spec_Master.csv"),
            },
        )

        logical_to_contract_names: dict[str, set[str]] = {}
        for contract_name, logical_name, _ in snapshot_rows:
            logical_to_contract_names.setdefault(logical_name, set()).add(contract_name)
        self.assertEqual(
            logical_to_contract_names["spec_master"],
            {"Spec_Master", "Page_Placeholders_Source"},
        )
        for logical_name, contract_names in logical_to_contract_names.items():
            if logical_name != "spec_master":
                with self.subTest(table=logical_name):
                    self.assertEqual(len(contract_names), 1)

    def test_derived_file_registry_closes_over_contract(self) -> None:
        derived_contracts = self.contract.get("derived_contracts")
        if not isinstance(derived_contracts, list):
            self.fail("phase2_source_tables.json.derived_contracts must be a list")

        contract_files: set[str] = set()
        for contract in derived_contracts:
            if not isinstance(contract, dict):
                continue
            file_name = contract.get("file")
            if isinstance(file_name, str) and file_name.strip():
                contract_files.add(Path(file_name).name)
            for derived_file in contract.get("derived_files", ()):
                if isinstance(derived_file, str) and derived_file.strip():
                    contract_files.add(Path(derived_file).name)

        self.assertEqual(
            contract_files,
            set(PHASE2_REQUIRED_DERIVED_FILES.values()),
        )

    def test_required_csv_headers_close_over_snapshot_registries(self) -> None:
        snapshot_logical_names = set(PHASE2_REQUIRED_TABLE_FILES) | set(PHASE2_REQUIRED_DERIVED_FILES)
        header_logical_names = set(REQUIRED_CSV_HEADERS)

        missing_headers = snapshot_logical_names - header_logical_names
        extra_headers = header_logical_names - snapshot_logical_names
        self.assertEqual(
            missing_headers,
            set(REGISTRY_EXEMPTIONS["csv_headers"]),
            "Every snapshot without fixed headers must have an explicit topology exemption",
        )
        self.assertEqual(extra_headers, set())

        for logical_name, required_headers in REQUIRED_CSV_HEADERS.items():
            with self.subTest(table=logical_name):
                self.assertTrue(required_headers)
                self.assertEqual(len(required_headers), len(set(required_headers)))


if __name__ == "__main__":
    unittest.main()
