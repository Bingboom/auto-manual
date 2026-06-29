from __future__ import annotations

import copy
import unittest
from pathlib import Path

from tools import schema_drift
from tools.queue_contract import DATA_SYNC_FIELD


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "schema_drift"


class SchemaDriftTests(unittest.TestCase):
    def _result(self, fixture_name: str) -> schema_drift.SchemaDriftResult:
        payload = schema_drift.load_schema_drift_payload(FIXTURE_DIR / fixture_name)
        return schema_drift.check_schema_drift_payload(payload)

    def test_passing_payload_should_pass(self) -> None:
        result = self._result("passing_payload.json")

        self.assertTrue(result.valid, schema_drift.render_schema_drift_report(result))
        self.assertEqual((), result.issues)

    def test_missing_required_logical_table_should_fail(self) -> None:
        result = self._result("missing_required_logical_table.json")

        self.assertFalse(result.valid)
        matching = [
            issue
            for issue in result.issues
            if issue.code == "missing_required_logical_table"
            and issue.surface == "snapshot_manifest.tables"
        ]
        self.assertEqual(1, len(matching))
        self.assertEqual(("symbols_blocks",), matching[0].missing)

    def test_missing_csv_header_should_fail(self) -> None:
        result = self._result("missing_csv_header.json")

        self.assertFalse(result.valid)
        matching = [
            issue
            for issue in result.issues
            if issue.code == "missing_csv_header" and issue.surface == "spec_master"
        ]
        self.assertEqual(1, len(matching))
        self.assertIn("Model", matching[0].missing)

    def test_missing_queue_writable_field_should_fail(self) -> None:
        result = self._result("missing_queue_writable_field.json")

        self.assertFalse(result.valid)
        matching = [
            issue
            for issue in result.issues
            if issue.code == "missing_queue_writable_field"
            and issue.surface == "document_link"
        ]
        self.assertEqual(1, len(matching))
        self.assertEqual((DATA_SYNC_FIELD,), matching[0].missing)

    def test_source_table_contract_missing_writable_header_should_fail(self) -> None:
        payload = copy.deepcopy(schema_drift.load_schema_drift_payload(FIXTURE_DIR / "passing_payload.json"))
        payload["csv_headers"]["manual_copy_source"].remove("notes")

        result = schema_drift.check_schema_drift_payload(payload)

        self.assertFalse(result.valid)
        matching = [
            issue
            for issue in result.issues
            if issue.code == "source_contract.required_header_missing"
            and issue.surface == "Manual_Copy_Source"
        ]
        self.assertEqual(1, len(matching))
        self.assertEqual(("notes",), matching[0].missing)


if __name__ == "__main__":
    unittest.main()
