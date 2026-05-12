from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import content_assembly, content_assembly_contract, topic_map_adapter


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "topic_map"
CONTRACT_PATH = REPO_ROOT / "docs" / "templates" / "assembly_contracts" / "03_product_overview.yaml"
BLOCK_TEMPLATE_DIR = REPO_ROOT / "docs" / "templates" / "assembly_blocks" / "03_product_overview"


class TopicMapAdapterTests(unittest.TestCase):
    def _substitutions(self) -> dict[str, str]:
        return {
            "PRODUCT_NAME": "Jackery Explorer 1000 Plus",
            "MODEL_NO": "JE-1000F",
            "MAIN_POWER_BUTTON_LABEL": "Main Power Button",
            "FRONT_DC12_PORT_LABEL": "DC 12V Port",
            "FRONT_DC12_PORT_SPEC": "12V/10A Max",
            "DC_USB_POWER_BUTTON_LABEL": "DC/USB Power Button",
            "FRONT_USB_C_LOW_LABEL": "USB-C 30W Output",
            "FRONT_USB_C_LOW_SPEC": "30W Max",
            "FRONT_USB_C_HIGH_LABEL": "USB-C 100W Output",
            "FRONT_USB_C_HIGH_SPEC": "100W Max",
            "AC_POWER_BUTTON_LABEL": "AC Power Button",
            "FRONT_USB_A_LABEL": "USB-A 18W Output",
            "FRONT_USB_A_SPEC": "18W Max",
            "FRONT_AC_OUTPUT_LABEL": "AC Output",
            "FRONT_AC_OUTPUT_SPEC": "120V~60Hz",
            "FRONT_TOTAL_OUTPUT_LABEL": "Total Output",
            "FRONT_TOTAL_OUTPUT_SPEC": "1500W Rated",
            "SIDE_AC_INPUT_LABEL": "AC Input",
            "SIDE_AC_INPUT_SPEC": "100V-120V~60Hz",
            "SIDE_DC_INPUT_LABEL": "DC Input",
            "SIDE_DC_INPUT_PV_SPEC": "PV Input",
            "SIDE_DC_INPUT_CAR_SPEC": "Car Input",
        }

    def test_adapter_should_emit_content_assembly_tables_for_product_overview(self) -> None:
        tables = topic_map_adapter.adapt_topic_map_to_content_assembly(
            fixtures_dir=FIXTURE_DIR,
            page_id="03_product_overview",
            product_family="JE-1000F",
            repo_root=REPO_ROOT,
        )

        self.assertEqual(
            {"page_assembly", "content_blocks", "block_fields", "asset_registry", "block_rules"},
            set(tables),
        )
        self.assertEqual(11, len(tables["page_assembly"]))
        self.assertIn(
            {
                "page_id": "03_product_overview",
                "product_family": "JE-1000F",
                "region": "US",
                "lang": "en",
                "block_id": "product_overview.total_output",
                "block_type": "spec_summary",
                "order": "40",
                "enabled": "true",
                "fallback_lang": "en",
            },
            tables["page_assembly"],
        )
        self.assertNotIn(
            ("JP", "ja", "product_overview.total_output"),
            {(row["region"], row["lang"], row["block_id"]) for row in tables["page_assembly"]},
        )
        self.assertIn(
            ("product_overview.front_features", "FRONT_VIEW_JA", "JP", "ja"),
            {
                (row["block_id"], row["title_key"], row["region"], row["lang"])
                for row in tables["content_blocks"]
            },
        )

    def test_adapter_output_should_validate_as_content_assembly_contract(self) -> None:
        tables = topic_map_adapter.adapt_topic_map_to_content_assembly(
            fixtures_dir=FIXTURE_DIR,
            page_id="03_product_overview",
            product_family="JE-1000F",
            repo_root=REPO_ROOT,
        )
        with tempfile.TemporaryDirectory() as td:
            output_dir = Path(td) / "content_assembly"
            topic_map_adapter.write_content_assembly_fixtures(tables, output_dir=output_dir, repo_root=REPO_ROOT)

            result = content_assembly_contract.validate_content_assembly_contract(
                contract_path=CONTRACT_PATH,
                fixtures_dir=output_dir,
                repo_root=REPO_ROOT,
            )

        self.assertTrue(result.valid, content_assembly_contract.render_content_assembly_report(result))

    def test_adapter_output_should_render_product_overview_page(self) -> None:
        tables = topic_map_adapter.adapt_topic_map_to_content_assembly(
            fixtures_dir=FIXTURE_DIR,
            page_id="03_product_overview",
            product_family="JE-1000F",
            repo_root=REPO_ROOT,
        )
        with tempfile.TemporaryDirectory() as td:
            output_dir = Path(td) / "content_assembly"
            topic_map_adapter.write_content_assembly_fixtures(tables, output_dir=output_dir, repo_root=REPO_ROOT)

            rendered = content_assembly.render_content_assembly_page(
                contract_path=CONTRACT_PATH,
                fixtures_dir=output_dir,
                block_template_dir=BLOCK_TEMPLATE_DIR,
                region="JP",
                lang="ja",
                substitutions=self._substitutions(),
                repo_root=REPO_ROOT,
            )

        self.assertIn("各部の名称", rendered)
        self.assertIn("正面", rendered)
        self.assertNotIn("FRONT_TOTAL_OUTPUT_LABEL", rendered)

    def test_cli_export_should_write_content_assembly_csvs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            output_dir = Path(td) / "content_assembly"
            rc = topic_map_adapter.run(
                [
                    "export-content-assembly",
                    "--fixtures",
                    str(FIXTURE_DIR),
                    "--page-id",
                    "03_product_overview",
                    "--product-family",
                    "JE-1000F",
                    "--output",
                    str(output_dir),
                ]
            )

            self.assertEqual(0, rc)
            self.assertTrue((output_dir / "page_assembly.csv").exists())
            self.assertTrue((output_dir / "content_blocks.csv").exists())

    def test_cli_export_should_reject_managed_build_outputs(self) -> None:
        output_dir = REPO_ROOT / "docs" / "_build" / "topic_map_adapter_should_not_write"
        self.assertFalse(output_dir.exists())

        rc = topic_map_adapter.run(
            [
                "export-content-assembly",
                "--fixtures",
                str(FIXTURE_DIR),
                "--output",
                str(output_dir),
            ]
        )

        self.assertEqual(1, rc)
        self.assertFalse(output_dir.exists())


if __name__ == "__main__":
    unittest.main()
