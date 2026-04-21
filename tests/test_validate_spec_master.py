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

    def _write_config(
        self,
        root: Path,
        *,
        manifest_path: Path,
        spec_master_csv: Path,
        spec_footnotes_csv: Path | None = None,
    ) -> Path:
        docs_dir = root / "docs"
        config_path = root / "config.yaml"
        lines = [
            "build:",
            "  languages: [en]",
            "  default_model: JE-1000F",
            "  default_region: US",
            "paths:",
            f"  docs_dir: {docs_dir.as_posix()}",
            f"  spec_master_csv: {spec_master_csv.as_posix()}",
            f"  page_manifest: {manifest_path.as_posix()}",
        ]
        if spec_footnotes_csv is not None:
            lines.append(f"  spec_footnotes_csv: {spec_footnotes_csv.as_posix()}")
        config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return config_path

    def test_collect_spec_master_validation_issues_should_report_duplicate_latest_rows(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest_path = self._write_generated_page_fixture(root)
            spec_master_csv = root / "Spec_Master.csv"
            spec_master_csv.write_text(
                "\n".join(
                    [
                        "Model,Region,Source_lang,Is_Latest,Page,Row_key,Slot_key,Line_order,Value_source",
                        "JE-1000F,US,en,TRUE,specifications,product_name,,,Jackery 1000",
                        "JE-1000F,US,en,TRUE,specifications,model_no,,,JE-1000F",
                        "JE-1000F,US,en,TRUE,Product overview,main_power_button,label,1,Main POWER Button",
                        "JE-1000F,US,en,TRUE,Product overview,main_power_button,label,1,Main POWER Button",
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
                        "Model,Region,Source_lang,Is_Latest,Page,Row_key,Slot_key,Line_order,Value_source",
                        "JE-1000F,US,en,TRUE,specifications,product_name,,,Jackery 1000",
                        "JE-1000F,US,en,TRUE,specifications,model_no,,,JE-1000F",
                        "JE-1000F,US,en,TRUE,Product overview,main_power_button,label,1,Main POWER Button",
                        "JE-1000F,US,en,TRUE,Product overview,main_power_button,label,2,Primary POWER Button",
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
                        "Model,Region,Source_lang,Is_Latest,Page,Row_key,Slot_key,Line_order,Value_source",
                        "JE-1000F,US,en,TRUE,specifications,product_name,,,",
                        "JE-1000F,US,en,TRUE,specifications,model_no,,,JE-1000F",
                        "JE-1000F,US,en,TRUE,Product overview,main_power_button,label,1,Main POWER Button",
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
                        "Model,Region,Source_lang,Is_Latest,Page,Row_key,Slot_key,Line_order,Value_en",
                        "JE-1000F,US,en,TRUE,specifications,product_name,,,Jackery 1000",
                        "JE-1000F,US,en,TRUE,specifications,model_no,,,JE-1000F",
                        "JE-1000F,US,en,TRUE,Product overview,main_power_button,label,1,Main POWER Button",
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
                        "Model,Region,Source_lang,Is_Latest,Page,Row_key,Slot_key,Line_order,Value_source",
                        "JE-1000F,JP,ja,TRUE,specifications,product_name,,,,Jackery ポータブル電源 1000 New",
                        "JE-1000F,JP,ja,TRUE,specifications,model_no,,,,JE-1000F",
                        "JE-1000F,JP,ja,TRUE,Product overview,main_power_button,label,1,",
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

    def test_collect_spec_master_validation_issues_should_report_missing_source_lang(self) -> None:
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
            self.assertIn("MISSING_SOURCE_LANG", codes)

    def test_collect_spec_master_validation_issues_should_fallback_to_sibling_region_footnote(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest_path = self._write_generated_page_fixture(root)
            spec_master_csv = root / "Spec_Master.csv"
            spec_master_csv.write_text(
                "\n".join(
                    [
                        "Model,Region,Source_lang,Is_Latest,Page,Row_key,Slot_key,Line_order,Param_source,Param_footnote_refs,Value_source",
                        "JE-1000F,EU,en,TRUE,specifications,product_name,,,,,Jackery Explorer 1000 EU",
                        "JE-1000F,EU,en,TRUE,specifications,model_no,,,,,JE-1000F",
                        "JE-1000F,EU,en,TRUE,Product overview,main_power_button,label,1,,,Main POWER Button",
                        'JE-1000F,EU,en,TRUE,specifications,ac_input,,1,Bypass Mode,ac_bypass,"100V-120V~60Hz, 12A Max"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            spec_footnotes_csv = root / "Spec_Footnotes.csv"
            spec_footnotes_csv.write_text(
                "\n".join(
                    [
                        "Footnote_id,Type,Region,Model,Source_lang,Is_Latest,Page,Footnote_order,Text_en,Enabled",
                        "ac_bypass,Footnote,US,JE-1000F,en,TRUE,specifications,1,Shared AC bypass footnote,TRUE",
                        "ac_bypass,Footnote,JP,JE-1000F,ja,TRUE,specifications,2,JP bypass footnote,TRUE",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            config_path = self._write_config(
                root,
                manifest_path=manifest_path,
                spec_master_csv=spec_master_csv,
                spec_footnotes_csv=spec_footnotes_csv,
            )

            issues = validate_spec_master.collect_spec_master_validation_issues(
                cfg_path=config_path,
                model="JE-1000F",
                region="EU",
                all_targets=False,
            )

            codes = {issue.code for issue in issues}
            self.assertNotIn("UNKNOWN_FOOTNOTE_REF", codes)

    def test_collect_spec_master_validation_issues_should_accept_family_scoped_document_key(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest_path = self._write_generated_page_fixture(root)
            spec_master_csv = root / "Spec_Master.csv"
            spec_master_csv.write_text(
                "\n".join(
                    [
                        "document_key,Model,Region,Source_lang,Is_Latest,Page,Row_key,Slot_key,Line_order,Value_source",
                        "JE-2000E_CN,JE-2000E,CN,zh,TRUE,specifications,product_name,,,Jackery 2000E",
                        "JE-2000E_CN,JE-2000E,CN,zh,TRUE,specifications,model_no,,,JE-2000E",
                        "JE-2000E_CN,JE-2000E,CN,zh,TRUE,Product overview,main_power_button,label,1,Main POWER Button",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            config_path = self._write_config(root, manifest_path=manifest_path, spec_master_csv=spec_master_csv)

            issues = validate_spec_master.collect_spec_master_validation_issues(
                cfg_path=config_path,
                model="JE-2000E",
                region="CN",
                all_targets=False,
            )

            codes = {issue.code for issue in issues}
            self.assertNotIn("INVALID_DOCUMENT_KEY", codes)
            self.assertNotIn("MISSING_DOCUMENT_KEY", codes)

    def test_collect_spec_master_validation_issues_should_accept_language_scoped_document_key(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest_path = self._write_generated_page_fixture(root)
            spec_master_csv = root / "Spec_Master.csv"
            spec_master_csv.write_text(
                "\n".join(
                    [
                        "document_key,Model,Region,Source_lang,Is_Latest,Page,Row_key,Slot_key,Line_order,Value_source",
                        "JE-1000F_US_en,JE-1000F,US,en,TRUE,specifications,product_name,,,Jackery 1000",
                        "JE-1000F_US_en,JE-1000F,US,en,TRUE,specifications,model_no,,,JE-1000F",
                        "JE-1000F_US_en,JE-1000F,US,en,TRUE,Product overview,main_power_button,label,1,Main POWER Button",
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
            self.assertNotIn("INVALID_DOCUMENT_KEY", codes)
            self.assertNotIn("MISSING_DOCUMENT_KEY", codes)

    def test_collect_spec_master_validation_issues_should_accept_document_key_style_target_model(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest_path = self._write_generated_page_fixture(root)
            spec_master_csv = root / "Spec_Master.csv"
            spec_master_csv.write_text(
                "\n".join(
                    [
                        "document_key,Model,Region,Source_lang,Is_Latest,Page,Row_key,Slot_key,Line_order,Row_label_source,Value_source",
                        "JE-1000F_JP,JE-1000F,JP,en,TRUE,specifications,product_name,,,Product Name,Jackery 1000 JP",
                        "JE-1000F_JP,JE-1000F,JP,en,TRUE,specifications,model_no,,,Model No.,JE-1000F",
                        "JE-1000F_JP,JE-1000F,JP,en,TRUE,Product overview,main_power_button,label,1,Main Power Button,Main Power Button",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            config_path = self._write_config(root, manifest_path=manifest_path, spec_master_csv=spec_master_csv)

            issues = validate_spec_master.collect_spec_master_validation_issues(
                cfg_path=config_path,
                model="JE-1000F_JP",
                region="JP",
                all_targets=False,
            )

            codes = {issue.code for issue in issues}
            self.assertNotIn("MISSING_REQUIRED_SPEC_ROW", codes)
            self.assertNotIn("INVALID_DOCUMENT_KEY", codes)
            self.assertNotIn("MISSING_DOCUMENT_KEY", codes)

    def test_collect_spec_master_validation_issues_should_report_latest_row_claiming_another_targets_document_key(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest_path = self._write_generated_page_fixture(root)
            spec_master_csv = root / "Spec_Master.csv"
            spec_master_csv.write_text(
                "\n".join(
                    [
                        "document_key,Model,Region,Source_lang,Is_Latest,Page,Row_key,Slot_key,Line_order,Row_label_source,Value_source",
                        "JE-1000F_US,JE-1000F,US,en,TRUE,specifications,product_name,,,Product Name,Jackery 1000",
                        "JE-1000F_US,JE-1000F,US,en,TRUE,specifications,model_no,,,Model No.,JE-1000F",
                        "JE-1000F_US,JE-1000F,US,en,TRUE,Product overview,main_power_button,label,1,Main POWER Button,Main POWER Button",
                        "JE-1000F_US,JE-2000E,US,en,TRUE,ups_mode,ups_bypass_output,text,1,UPS Bypass Output,12A (1440W)",
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

            invalid_document_key_messages = [
                issue.message for issue in issues if issue.code == "INVALID_DOCUMENT_KEY"
            ]
            self.assertTrue(invalid_document_key_messages)
            self.assertTrue(
                any("JE-1000F_US" in message and "JE-2000E_US" in message for message in invalid_document_key_messages)
            )


if __name__ == "__main__":
    unittest.main()
