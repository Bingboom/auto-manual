from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import validate_spec_master


class TestValidateSpecMaster(unittest.TestCase):
    def _write_generated_page_fixture(self, root: Path) -> Path:
        docs_dir = root / "docs"
        (docs_dir / "templates" / "page_us-en").mkdir(parents=True)
        (docs_dir / "templates" / "recipes").mkdir(parents=True)

        (docs_dir / "templates" / "page_us-en" / "demo.rst").write_text(
            "|MAIN_POWER_BUTTON_LABEL|\n",
            encoding="utf-8",
        )
        (docs_dir / "templates" / "recipes" / "demo.yaml").write_text(
            "\n".join(
                [
                    "page_id: demo_page",
                    "template: templates/page_us-en/demo.rst",
                    "field_map:",
                    "  MAIN_POWER_BUTTON_LABEL:",
                    "    row_key: main_power_button",
                    "    pages: [Product overview]",
                    "    usage_type: page_value",
                    "    value_role: label",
                    "required_row_keys:",
                    "  - product_name",
                    "  - model_no",
                    "snippet_slots: {}",
                    "contracts: []",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        manifest_path = root / "manual.yaml"
        manifest_path.write_text(
            "\n".join(
                [
                    "pages:",
                    "  - type: generated_page",
                    "    page: demo_page",
                    "    engine: draft_v1",
                    "    recipe: templates/recipes/demo.yaml",
                    "    template: templates/page_us-en/demo.rst",
                    "    langs: [en]",
                    "    include_dir: generated/{model}/draft",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        return manifest_path

    def _write_config(self, root: Path, *, manifest_path: Path, spec_master_csv: Path) -> Path:
        docs_dir = root / "docs"
        config_path = root / "config.yaml"
        config_path.write_text(
            "\n".join(
                [
                    "build:",
                    "  languages: [en]",
                    "  default_model: JE-1000F",
                    "  default_region: US",
                    "paths:",
                    f"  docs_dir: {docs_dir.as_posix()}",
                    f"  spec_master_csv: {spec_master_csv.as_posix()}",
                    f"  page_manifest: {manifest_path.as_posix()}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        return config_path

    def test_collect_spec_master_validation_issues_should_report_duplicate_latest_rows(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest_path = self._write_generated_page_fixture(root)
            spec_master_csv = root / "Spec_Master.csv"
            spec_master_csv.write_text(
                "\n".join(
                    [
                        "Model,Region,Is_Latest,Page,Row_key,Slot_key,Line_order,Value_source",
                        "JE-1000F,US,TRUE,specifications,product_name,,,Jackery 1000",
                        "JE-1000F,US,TRUE,specifications,model_no,,,JE-1000F",
                        "JE-1000F,US,TRUE,Product overview,main_power_button,label,1,Main POWER Button",
                        "JE-1000F,US,TRUE,Product overview,main_power_button,label,1,Main POWER Button",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            config_path = self._write_config(root, manifest_path=manifest_path, spec_master_csv=spec_master_csv)

            issues = validate_spec_master.collect_spec_master_validation_issues(
                cfg_path=config_path,
                model="JE-1000F",
                region="US",
                all_targets=False,
            )

            codes = {issue.code for issue in issues}
            self.assertIn("DUPLICATE_LATEST_SPEC_ROW", codes)

    def test_collect_spec_master_validation_issues_should_report_ambiguous_selector_values(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest_path = self._write_generated_page_fixture(root)
            spec_master_csv = root / "Spec_Master.csv"
            spec_master_csv.write_text(
                "\n".join(
                    [
                        "Model,Region,Is_Latest,Page,Row_key,Slot_key,Line_order,Value_source",
                        "JE-1000F,US,TRUE,specifications,product_name,,,Jackery 1000",
                        "JE-1000F,US,TRUE,specifications,model_no,,,JE-1000F",
                        "JE-1000F,US,TRUE,Product overview,main_power_button,label,1,Main POWER Button",
                        "JE-1000F,US,TRUE,Product overview,main_power_button,label,2,Primary POWER Button",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            config_path = self._write_config(root, manifest_path=manifest_path, spec_master_csv=spec_master_csv)

            issues = validate_spec_master.collect_spec_master_validation_issues(
                cfg_path=config_path,
                model="JE-1000F",
                region="US",
                all_targets=False,
            )

            codes = {issue.code for issue in issues}
            self.assertIn("AMBIGUOUS_SPEC_SELECTOR", codes)

    def test_collect_spec_master_validation_issues_should_report_empty_required_values(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest_path = self._write_generated_page_fixture(root)
            spec_master_csv = root / "Spec_Master.csv"
            spec_master_csv.write_text(
                "\n".join(
                    [
                        "Model,Region,Is_Latest,Page,Row_key,Slot_key,Line_order,Value_source",
                        "JE-1000F,US,TRUE,specifications,product_name,,,",
                        "JE-1000F,US,TRUE,specifications,model_no,,,JE-1000F",
                        "JE-1000F,US,TRUE,Product overview,main_power_button,label,1,Main POWER Button",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            config_path = self._write_config(root, manifest_path=manifest_path, spec_master_csv=spec_master_csv)

            issues = validate_spec_master.collect_spec_master_validation_issues(
                cfg_path=config_path,
                model="JE-1000F",
                region="US",
                all_targets=False,
            )

            codes = {issue.code for issue in issues}
            self.assertIn("EMPTY_REQUIRED_SPEC_VALUE", codes)

    def test_collect_spec_master_validation_issues_should_reject_legacy_value_en_source_header(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest_path = self._write_generated_page_fixture(root)
            spec_master_csv = root / "Spec_Master.csv"
            spec_master_csv.write_text(
                "\n".join(
                    [
                        "Model,Region,Is_Latest,Page,Row_key,Slot_key,Line_order,Value_en",
                        "JE-1000F,US,TRUE,specifications,product_name,,,Jackery 1000",
                        "JE-1000F,US,TRUE,specifications,model_no,,,JE-1000F",
                        "JE-1000F,US,TRUE,Product overview,main_power_button,label,1,Main POWER Button",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            config_path = self._write_config(root, manifest_path=manifest_path, spec_master_csv=spec_master_csv)

            issues = validate_spec_master.collect_spec_master_validation_issues(
                cfg_path=config_path,
                model="JE-1000F",
                region="US",
                all_targets=False,
            )

            codes = {issue.code for issue in issues}
            self.assertIn("LEGACY_SOURCE_HEADERS_PRESENT", codes)
            self.assertIn("MISSING_SOURCE_VALUE", codes)
            self.assertIn("EMPTY_REQUIRED_SPEC_VALUE", codes)

    def test_collect_spec_master_validation_issues_should_report_missing_source_value_for_jp_rows(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest_path = self._write_generated_page_fixture(root)
            spec_master_csv = root / "Spec_Master.csv"
            spec_master_csv.write_text(
                "\n".join(
                    [
                        "Model,Region,Is_Latest,Page,Row_key,Slot_key,Line_order,Value_source",
                        "JE-1000F,JP,TRUE,specifications,product_name,,,,Jackery ポータブル電源 1000 New",
                        "JE-1000F,JP,TRUE,specifications,model_no,,,,JE-1000F",
                        "JE-1000F,JP,TRUE,Product overview,main_power_button,label,1,",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            config_path = self._write_config(root, manifest_path=manifest_path, spec_master_csv=spec_master_csv)

            issues = validate_spec_master.collect_spec_master_validation_issues(
                cfg_path=config_path,
                model="JE-1000F",
                region="JP",
                all_targets=False,
            )

            codes = {issue.code for issue in issues}
            self.assertIn("MISSING_SOURCE_VALUE", codes)
            self.assertIn("EMPTY_REQUIRED_SPEC_VALUE", codes)


if __name__ == "__main__":
    unittest.main()

