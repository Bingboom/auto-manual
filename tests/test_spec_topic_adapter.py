from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import spec_topic_adapter
from tools.utils.spec_master import read_spec_master_rows, resolve_spec_value_from_rows


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "spec_topics"


class SpecTopicAdapterTests(unittest.TestCase):
    def test_adapter_should_emit_compatible_spec_master_rows(self) -> None:
        rows = spec_topic_adapter.adapt_spec_topics_to_spec_master(
            fixtures_dir=FIXTURE_DIR,
            model="JE-1000F",
            region="US",
        )

        self.assertEqual(13, len(rows))
        self.assertEqual("product_name", rows[0]["Row_key"])
        self.assertEqual("GENERAL INFO", rows[0]["Section"])
        self.assertEqual("ac_input", rows[3]["Row_key"])
        self.assertEqual("Charge Mode", rows[3]["Param_source"])
        self.assertEqual("OUTPUT PORTS", rows[-1]["Section"])

    def test_exported_rows_should_work_with_existing_spec_master_lookup(self) -> None:
        rows = spec_topic_adapter.adapt_spec_topics_to_spec_master(
            fixtures_dir=FIXTURE_DIR,
            model="JE-1000F",
            region="US",
        )

        match = resolve_spec_value_from_rows(
            list(rows),
            model="JE-1000F",
            region="US",
            lang="en",
            row_key="usb_c",
            pages="specifications",
            line_order="2",
        )

        self.assertIsNotNone(match)
        self.assertIn("100W Max", match.value)

    def test_cli_export_should_write_temp_spec_master_csv(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            output_path = Path(td) / "Spec_Master.csv"
            rc = spec_topic_adapter.run(
                [
                    "export-spec-master",
                    "--fixtures",
                    str(FIXTURE_DIR),
                    "--model",
                    "JE-1000F",
                    "--region",
                    "US",
                    "--output",
                    str(output_path),
                ]
            )

            self.assertEqual(0, rc)
            rows = read_spec_master_rows(output_path)
            self.assertEqual(13, len(rows))
            self.assertEqual("capacity", rows[2]["Row_key"])

    def test_cli_export_should_reject_live_data_roots(self) -> None:
        output_path = REPO_ROOT / "data" / "phase1" / "Spec_Master.topic_export.csv"
        self.assertFalse(output_path.exists())

        rc = spec_topic_adapter.run(
            [
                "export-spec-master",
                "--fixtures",
                str(FIXTURE_DIR),
                "--output",
                str(output_path),
            ]
        )

        self.assertEqual(1, rc)
        self.assertFalse(output_path.exists())


if __name__ == "__main__":
    unittest.main()
