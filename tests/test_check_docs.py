from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import check_docs
from tools.check_docs_duplicate_text import collect_duplicate_render_text_issues
from tests.test_helpers import temp_test_root, write_lines, write_text


class TestCheckDocs(unittest.TestCase):
    def test_resolve_spec_master_csv_path_should_honor_data_root_override(self) -> None:
        with temp_test_root() as root:
            cfg = {"paths": {"spec_master_csv": "data/phase2/Spec_Master.csv"}}

            path = check_docs.resolve_spec_master_csv_path(cfg, data_root=(root / "data" / "phase2").as_posix())

        self.assertEqual(root / "data" / "phase2" / "Spec_Master.csv", path)

    def test_collect_check_issues_should_report_stale_identity_literal(self) -> None:
        with temp_test_root() as root:
            docs_dir = root / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "US" / "rst"
            (bundle_dir / "page").mkdir(parents=True)

            write_text(bundle_dir / "index.rst", ".. include:: page/overview_en.rst\n")
            write_text(bundle_dir / "page" / "overview_en.rst", "Compare this unit with Jackery Explorer 2000 Pro.\n")

            spec_master = root / "Spec_Master.csv"
            write_lines(
                spec_master,
                [
                    "Model,Region,Is_Latest,Page,Row_key,Value_source",
                    "JE-1000F,US,TRUE,specifications,product_name,Jackery Explorer 1000 Pro",
                    "JE-1000F,US,TRUE,specifications,model_no,JE-1000F",
                    "JE-2000F,US,TRUE,specifications,product_name,Jackery Explorer 2000 Pro",
                    "JE-2000F,US,TRUE,specifications,model_no,JE-2000F",
                ],
            )

            config_path = root / "config.yaml"
            write_lines(
                config_path,
                [
                    "build:",
                    "  languages: [en]",
                    "paths:",
                    f"  docs_dir: {docs_dir.as_posix()}",
                    f"  spec_master_csv: {spec_master.as_posix()}",
                ],
            )

            issues = check_docs.collect_check_issues(
                cfg_path=config_path,
                model="JE-1000F",
                region="US",
                all_targets=False,
            )

            stale_issues = [issue for issue in issues if issue.code == "STALE_IDENTITY_LITERAL"]
            self.assertEqual(1, len(stale_issues))
            self.assertIn("Jackery Explorer 2000 Pro", stale_issues[0].message)

    def test_collect_check_issues_should_not_report_current_target_identity_as_stale(self) -> None:
        with temp_test_root() as root:
            docs_dir = root / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "US" / "rst"
            (bundle_dir / "page").mkdir(parents=True)

            write_text(bundle_dir / "index.rst", ".. include:: page/overview_en.rst\n")
            write_lines(
                bundle_dir / "page" / "overview_en.rst",
                [
                    "Jackery Explorer 1000 Pro keeps the current naming.",
                    ".. include:: page/JE-2000F_reference.rst",
                ],
            )

            spec_master = root / "Spec_Master.csv"
            write_lines(
                spec_master,
                [
                    "Model,Region,Is_Latest,Page,Row_key,Value_source",
                    "JE-1000F,US,TRUE,specifications,product_name,Jackery Explorer 1000 Pro",
                    "JE-1000F,US,TRUE,specifications,model_no,JE-1000F",
                    "JE-2000F,US,TRUE,specifications,product_name,Jackery Explorer 2000 Pro",
                    "JE-2000F,US,TRUE,specifications,model_no,JE-2000F",
                ],
            )

            config_path = root / "config.yaml"
            write_lines(
                config_path,
                [
                    "build:",
                    "  languages: [en]",
                    "paths:",
                    f"  docs_dir: {docs_dir.as_posix()}",
                    f"  spec_master_csv: {spec_master.as_posix()}",
                ],
            )

            issues = check_docs.collect_check_issues(
                cfg_path=config_path,
                model="JE-1000F",
                region="US",
                all_targets=False,
            )

            stale_issues = [issue for issue in issues if issue.code == "STALE_IDENTITY_LITERAL"]
            self.assertEqual([], stale_issues)

    def test_collect_check_issues_should_treat_document_key_style_target_model_as_current_identity(self) -> None:
        with temp_test_root() as root:
            docs_dir = root / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F_JP" / "JP" / "rst"
            (bundle_dir / "page").mkdir(parents=True)

            write_text(bundle_dir / "index.rst", ".. include:: page/overview_ja.rst\n")
            write_lines(
                bundle_dir / "page" / "overview_ja.rst",
                [
                    "Jackery ポータブル電源 1000 New を正しく表示します。",
                    "型番は JE-1000F / JE-1000F-SG です。",
                ],
            )

            spec_master = root / "Spec_Master.csv"
            write_lines(
                spec_master,
                [
                    "Model,Region,Is_Latest,Page,Row_key,Value_source",
                    "JE-1000F,JP,TRUE,specifications,product_name,Jackery ポータブル電源 1000 New",
                    "JE-1000F,JP,TRUE,specifications,model_no,JE-1000F / JE-1000F-SG",
                    "JE-2000F,JP,TRUE,specifications,product_name,Jackery ポータブル電源 2000 Pro",
                    "JE-2000F,JP,TRUE,specifications,model_no,JE-2000F",
                ],
            )

            config_path = root / "config.yaml"
            write_lines(
                config_path,
                [
                    "build:",
                    "  languages: [ja]",
                    "paths:",
                    f"  docs_dir: {docs_dir.as_posix()}",
                    f"  spec_master_csv: {spec_master.as_posix()}",
                ],
            )

            issues = check_docs.collect_check_issues(
                cfg_path=config_path,
                model="JE-1000F_JP",
                region="JP",
                all_targets=False,
            )

            stale_issues = [issue for issue in issues if issue.code == "STALE_IDENTITY_LITERAL"]
            self.assertEqual([], stale_issues)

    def test_collect_check_issues_should_allow_whitelisted_foreign_identity_literals(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "US" / "rst"
            (bundle_dir / "page").mkdir(parents=True)

            (bundle_dir / "index.rst").write_text(".. include:: page/overview_en.rst\n", encoding="utf-8")
            (bundle_dir / "page" / "overview_en.rst").write_text(
                "Accessory matches Jackery Explorer 2000 Pro battery pack.\n",
                encoding="utf-8",
            )

            spec_master = root / "Spec_Master.csv"
            spec_master.write_text(
                "\n".join(
                    [
                        "Model,Region,Is_Latest,Page,Row_key,Value_source",
                        "JE-1000F,US,TRUE,specifications,product_name,Jackery Explorer 1000 Pro",
                        "JE-1000F,US,TRUE,specifications,model_no,JE-1000F",
                        "JE-2000F,US,TRUE,specifications,product_name,Jackery Explorer 2000 Pro",
                        "JE-2000F,US,TRUE,specifications,model_no,JE-2000F",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            config_path = root / "config.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "build:",
                        "  languages: [en]",
                        "checks:",
                        "  allowed_foreign_identity_literals:",
                        "    - Jackery Explorer 2000 Pro",
                        "paths:",
                        f"  docs_dir: {docs_dir.as_posix()}",
                        f"  spec_master_csv: {spec_master.as_posix()}",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            issues = check_docs.collect_check_issues(
                cfg_path=config_path,
                model="JE-1000F",
                region="US",
                all_targets=False,
            )

            stale_issues = [issue for issue in issues if issue.code == "STALE_IDENTITY_LITERAL"]
            self.assertEqual([], stale_issues)

    def test_collect_check_issues_should_report_12_app_setup_contract_missing_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "US" / "rst"
            (bundle_dir / "page").mkdir(parents=True)
            (docs_dir / "templates" / "page_us-en").mkdir(parents=True)
            (docs_dir / "templates" / "contracts").mkdir(parents=True)

            (bundle_dir / "index.rst").write_text(".. include:: page/12_app_setup_placeholder.rst\n", encoding="utf-8")
            (bundle_dir / "page" / "12_app_setup_placeholder.rst").write_text("Ready\n", encoding="utf-8")
            (docs_dir / "templates" / "page_us-en" / "12_app_setup_placeholder.rst").write_text(
                "\n".join(
                    [
                        "|MAIN_POWER_BUTTON_LABEL|",
                        "|AC_POWER_BUTTON_LABEL|",
                        "|DC_USB_POWER_BUTTON_LABEL|",
                        "|MAIN_POWER_BUTTON_LABEL_LOWER|",
                        "|AC_POWER_BUTTON_LABEL_LOWER|",
                        "|DC_USB_POWER_BUTTON_LABEL_LOWER|",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (docs_dir / "templates" / "contracts" / "12_app_setup.yaml").write_text(
                "\n".join(
                    [
                        "page_id: 12_app_setup",
                        "source_files:",
                        "  - templates/page_us-en/12_app_setup_placeholder.rst",
                        "required_placeholders:",
                        "  default:",
                        "    - MAIN_POWER_BUTTON_LABEL",
                        "    - AC_POWER_BUTTON_LABEL",
                        "    - DC_USB_POWER_BUTTON_LABEL",
                        "  en:",
                        "    - MAIN_POWER_BUTTON_LABEL_LOWER",
                        "    - AC_POWER_BUTTON_LABEL_LOWER",
                        "    - DC_USB_POWER_BUTTON_LABEL_LOWER",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            spec_master = root / "Spec_Master.csv"
            spec_master.write_text(
                "\n".join(
                    [
                        "Model,Region,Is_Latest,Page,Row_key,Usage_type,Value_role,Value_source",
                        "JE-1000F,US,TRUE,specifications,product_name,,,Jackery 1000",
                        "JE-1000F,US,TRUE,specifications,model_no,,,JE-1000F",
                        "JE-1000F,US,TRUE,Product overview,main_power_button,page_value,label,Main POWER Button",
                        "JE-1000F,US,TRUE,Product overview,ac_power_button,page_value,label,AC Button",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            config_path = root / "config.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "build:",
                        "  languages: [en]",
                        "paths:",
                        f"  docs_dir: {docs_dir.as_posix()}",
                        f"  spec_master_csv: {spec_master.as_posix()}",
                        "pages:",
                        "  - type: rst_include",
                        "    lang: en",
                        "    file: templates/page_us-en/12_app_setup_placeholder.rst",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            issues = check_docs.collect_check_issues(
                cfg_path=config_path,
                model="JE-1000F",
                region="US",
                all_targets=False,
            )

            messages = [issue.message for issue in issues if issue.code == "CONTRACT_MISSING_PLACEHOLDERS"]
            self.assertTrue(messages)
            self.assertTrue(any("DC_USB_POWER_BUTTON_LABEL" in message for message in messages))

    def test_collect_check_issues_should_report_contract_missing_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "US" / "rst"
            (bundle_dir / "page").mkdir(parents=True)
            (docs_dir / "templates" / "page_us-en").mkdir(parents=True)
            (docs_dir / "templates" / "contracts").mkdir(parents=True)

            (bundle_dir / "index.rst").write_text(".. include:: page/03_product_overview_placeholder.rst\n", encoding="utf-8")
            (bundle_dir / "page" / "03_product_overview_placeholder.rst").write_text("Ready\n", encoding="utf-8")
            (docs_dir / "templates" / "page_us-en" / "03_product_overview_placeholder.rst").write_text(
                "|MAIN_POWER_BUTTON_LABEL|\n",
                encoding="utf-8",
            )
            (docs_dir / "templates" / "contracts" / "03_product_overview.yaml").write_text(
                "\n".join(
                    [
                        "page_id: 03_product_overview",
                        "source_files:",
                        "  - templates/page_us-en/03_product_overview_placeholder.rst",
                        "required_placeholders:",
                        "  default:",
                        "    - MAIN_POWER_BUTTON_LABEL",
                        "    - FRONT_DC12_PORT_LABEL",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            spec_master = root / "Spec_Master.csv"
            spec_master.write_text(
                "\n".join(
                    [
                        "Model,Region,Is_Latest,Page,Row_key,Usage_type,Value_role,Value_source",
                        "JE-1000F,US,TRUE,specifications,product_name,,,Jackery 1000",
                        "JE-1000F,US,TRUE,specifications,model_no,,,JE-1000F",
                        "JE-1000F,US,TRUE,Product overview,main_power_button,page_value,label,Main POWER Button",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            config_path = root / "config.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "build:",
                        "  languages: [en]",
                        "paths:",
                        f"  docs_dir: {docs_dir.as_posix()}",
                        f"  spec_master_csv: {spec_master.as_posix()}",
                        "pages:",
                        "  - type: rst_include",
                        "    lang: en",
                        "    file: templates/page_us-en/03_product_overview_placeholder.rst",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            issues = check_docs.collect_check_issues(
                cfg_path=config_path,
                model="JE-1000F",
                region="US",
                all_targets=False,
            )

            codes = {issue.code for issue in issues}
            self.assertIn("CONTRACT_MISSING_PLACEHOLDERS", codes)

    def test_collect_check_issues_should_report_contract_missing_copy(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "US" / "rst"
            (bundle_dir / "page").mkdir(parents=True)
            (docs_dir / "templates" / "page_us-en").mkdir(parents=True)
            (docs_dir / "templates" / "contracts").mkdir(parents=True)

            (bundle_dir / "index.rst").write_text(".. include:: page/03_product_overview_placeholder.rst\n", encoding="utf-8")
            (bundle_dir / "page" / "03_product_overview_placeholder.rst").write_text("Ready\n", encoding="utf-8")
            (docs_dir / "templates" / "page_us-en" / "03_product_overview_placeholder.rst").write_text(
                "{{ copy:product_overview.page_title }}\n",
                encoding="utf-8",
            )
            (docs_dir / "templates" / "contracts" / "03_product_overview.yaml").write_text(
                "\n".join(
                    [
                        "page_id: 03_product_overview",
                        "source_files:",
                        "  - templates/page_us-en/03_product_overview_placeholder.rst",
                        "required_copy_keys:",
                        "  en:",
                        "    - product_overview.page_title",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            spec_master = root / "Spec_Master.csv"
            spec_master.write_text(
                "\n".join(
                    [
                        "Model,Region,Is_Latest,Page,Row_key,Usage_type,Value_role,Value_source",
                        "JE-1000F,US,TRUE,specifications,product_name,,,Jackery 1000",
                        "JE-1000F,US,TRUE,specifications,model_no,,,JE-1000F",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            localized_copy = root / "Localized_Copy.csv"
            localized_copy.write_text(
                "copy_key,page_id,copy_type,Region,Model,Source_lang,Is_Latest,Version,text_en\n",
                encoding="utf-8",
            )

            config_path = root / "config.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "build:",
                        "  languages: [en]",
                        "paths:",
                        f"  docs_dir: {docs_dir.as_posix()}",
                        f"  spec_master_csv: {spec_master.as_posix()}",
                        f"  localized_copy_csv: {localized_copy.as_posix()}",
                        "pages:",
                        "  - type: rst_include",
                        "    lang: en",
                        "    file: templates/page_us-en/03_product_overview_placeholder.rst",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            issues = check_docs.collect_check_issues(
                cfg_path=config_path,
                model="JE-1000F",
                region="US",
                all_targets=False,
            )

            messages = [issue.message for issue in issues if issue.code == "CONTRACT_MISSING_COPY"]
            self.assertTrue(messages)
            self.assertTrue(any("product_overview.page_title" in message for message in messages))

    def test_collect_check_issues_should_report_contract_v2_missing_spec_page_values_and_assets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "US" / "rst"
            (bundle_dir / "page").mkdir(parents=True)
            (docs_dir / "templates" / "page_en").mkdir(parents=True)
            (docs_dir / "templates" / "contracts").mkdir(parents=True)

            (bundle_dir / "index.rst").write_text(".. include:: page/05_operation_guide_placeholder.rst\n", encoding="utf-8")
            (bundle_dir / "page" / "05_operation_guide_placeholder.rst").write_text("Ready\n", encoding="utf-8")
            (docs_dir / "templates" / "page_en" / "05_operation_guide_placeholder.rst").write_text(
                "|PRODUCT_NAME|\n",
                encoding="utf-8",
            )
            (docs_dir / "templates" / "contracts" / "05_operation_guide.yaml").write_text(
                "\n".join(
                    [
                        "page_id: 05_operation_guide",
                        "source_files:",
                        "  - templates/page_en/05_operation_guide_placeholder.rst",
                        "required_placeholders:",
                        "  default:",
                        "    - PRODUCT_NAME",
                        "required_spec_keys:",
                        "  default:",
                        "    - battery_capacity",
                        "required_page_values:",
                        "  default:",
                        "    - row_key: main_power_button",
                        "      pages: [Product overview]",
                        "      usage_type: page_value",
                        "      value_role: label",
                        "required_assets:",
                        "  default:",
                        "    - templates/word_template/common_assets/overview/front_product.jpg",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            spec_master = root / "Spec_Master.csv"
            spec_master.write_text(
                "\n".join(
                    [
                        "Model,Region,Is_Latest,Page,Row_key,Value_source",
                        "JE-1000F,US,TRUE,specifications,product_name,Jackery 1000",
                        "JE-1000F,US,TRUE,specifications,model_no,JE-1000F",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            config_path = root / "config.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "build:",
                        "  languages: [en]",
                        "paths:",
                        f"  docs_dir: {docs_dir.as_posix()}",
                        f"  spec_master_csv: {spec_master.as_posix()}",
                        "pages:",
                        "  - type: rst_include",
                        "    lang: en",
                        "    file: templates/page_en/05_operation_guide_placeholder.rst",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            issues = check_docs.collect_check_issues(
                cfg_path=config_path,
                model="JE-1000F",
                region="US",
                all_targets=False,
            )

            codes = {issue.code for issue in issues}
            self.assertIn("CONTRACT_MISSING_SPEC_KEYS", codes)
            self.assertIn("CONTRACT_MISSING_PAGE_VALUES", codes)
            self.assertIn("CONTRACT_MISSING_ASSETS", codes)

    def test_collect_check_issues_should_skip_contract_when_scope_does_not_apply(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "US" / "rst"
            (bundle_dir / "page").mkdir(parents=True)
            (docs_dir / "templates" / "page_en").mkdir(parents=True)
            (docs_dir / "templates" / "contracts").mkdir(parents=True)

            (bundle_dir / "index.rst").write_text(".. include:: page/03_product_overview_placeholder.rst\n", encoding="utf-8")
            (bundle_dir / "page" / "03_product_overview_placeholder.rst").write_text("Ready\n", encoding="utf-8")
            (docs_dir / "templates" / "page_en" / "03_product_overview_placeholder.rst").write_text(
                "Ready\n",
                encoding="utf-8",
            )
            (docs_dir / "templates" / "contracts" / "03_product_overview.yaml").write_text(
                "\n".join(
                    [
                        "page_id: 03_product_overview",
                        "source_files:",
                        "  - templates/page_en/03_product_overview_placeholder.rst",
                        "required_spec_keys:",
                        "  default:",
                        "    - battery_capacity",
                        "allowed_regions: [JP]",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            spec_master = root / "Spec_Master.csv"
            spec_master.write_text(
                "\n".join(
                    [
                        "Model,Region,Is_Latest,Page,Row_key,Value_source",
                        "JE-1000F,US,TRUE,specifications,product_name,Jackery 1000",
                        "JE-1000F,US,TRUE,specifications,model_no,JE-1000F",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            config_path = root / "config.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "build:",
                        "  languages: [en]",
                        "paths:",
                        f"  docs_dir: {docs_dir.as_posix()}",
                        f"  spec_master_csv: {spec_master.as_posix()}",
                        "pages:",
                        "  - type: rst_include",
                        "    lang: en",
                        "    file: templates/page_en/03_product_overview_placeholder.rst",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            issues = check_docs.collect_check_issues(
                cfg_path=config_path,
                model="JE-1000F",
                region="US",
                all_targets=False,
            )

            contract_issues = [issue for issue in issues if issue.code.startswith("CONTRACT_")]
            self.assertEqual([], contract_issues)

    def test_collect_check_issues_should_report_missing_model_no_placeholder_and_asset(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "US" / "rst"
            (bundle_dir / "page").mkdir(parents=True)

            (bundle_dir / "index.rst").write_text(".. include:: page/spec_en.rst\n", encoding="utf-8")
            (bundle_dir / "page" / "spec_en.rst").write_text(
                "\n".join(
                    [
                        "PRODUCT OVERVIEW",
                        "================",
                        "",
                        ".. image:: missing.png",
                        "",
                        "|MISSING_TOKEN|",
                        "",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            spec_master = root / "Spec_Master.csv"
            spec_master.write_text(
                "\n".join(
                    [
                        "Model,Region,Is_Latest,Page,Row_key,Value_source",
                        "JE-1000F,US,TRUE,specifications,product_name,Jackery 1000",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            config_path = root / "config.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "build:",
                        "  languages: [en]",
                        "paths:",
                        f"  docs_dir: {docs_dir.as_posix()}",
                        f"  spec_master_csv: {spec_master.as_posix()}",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            issues = check_docs.collect_check_issues(
                cfg_path=config_path,
                model="JE-1000F",
                region="US",
                all_targets=False,
            )

            codes = {issue.code for issue in issues}
            self.assertIn("MISSING_MODEL_NO", codes)
            self.assertIn("UNRESOLVED_PLACEHOLDER", codes)
            self.assertIn("MISSING_ASSET", codes)

    def test_collect_check_issues_should_pass_for_clean_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "US" / "rst"
            (bundle_dir / "page").mkdir(parents=True)
            (bundle_dir / "_static").mkdir(parents=True)

            (bundle_dir / "index.rst").write_text(".. include:: page/spec_en.rst\n", encoding="utf-8")
            (bundle_dir / "_static" / "ok.png").write_text("png", encoding="utf-8")
            (bundle_dir / "page" / "spec_en.rst").write_text(
                "\n".join(
                    [
                        "PRODUCT OVERVIEW",
                        "================",
                        "",
                        ".. image:: _static/ok.png",
                        "",
                        "Ready",
                        "",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            spec_master = root / "Spec_Master.csv"
            spec_master.write_text(
                "\n".join(
                    [
                        "Model,Region,Is_Latest,Page,Row_key,Value_source",
                        "JE-1000F,US,TRUE,specifications,product_name,Jackery 1000",
                        "JE-1000F,US,TRUE,specifications,model_no,JE-1000F",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            config_path = root / "config.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "build:",
                        "  languages: [en]",
                        "paths:",
                        f"  docs_dir: {docs_dir.as_posix()}",
                        f"  spec_master_csv: {spec_master.as_posix()}",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            issues = check_docs.collect_check_issues(
                cfg_path=config_path,
                model="JE-1000F",
                region="US",
                all_targets=False,
            )

            self.assertEqual([], issues)

    def test_collect_duplicate_render_text_issues_should_report_raw_html_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "US" / "rst"
            template_path = docs_dir / "templates" / "page_us-en" / "safety_en.rst"

            write_lines(
                template_path,
                [
                    ".. only:: latex",
                    "",
                    "   - The plug must follow all local codes and ordinances.",
                    "",
                    ".. only:: html",
                    "",
                    "   .. raw:: html",
                    "",
                    "      <ul><li>The plug must follow all local codes ordinances.</li></ul>",
                ],
            )

            issues = collect_duplicate_render_text_issues(
                repo_root=root,
                docs_dir=docs_dir,
                bundle_dir=bundle_dir,
                model="JE-1000F",
                region="US",
                issue_cls=check_docs.CheckIssue,
            )

            self.assertEqual(1, len(issues))
            self.assertEqual("DUPLICATE_RENDER_TEXT_MISMATCH", issues[0].code)
            self.assertIn("RST-only=1 HTML-only=1", issues[0].message)

    def test_collect_reference_issues_should_resolve_docs_relative_assets_for_generated_pages(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "US" / "rst"
            generated_dir = bundle_dir / "generated" / "JE-1000F"
            asset_dir = docs_dir / "templates" / "word_template" / "common_assets" / "symbols"
            generated_dir.mkdir(parents=True)
            asset_dir.mkdir(parents=True)

            (asset_dir / "warning_triangle.png").write_text("png", encoding="utf-8")
            rst_path = generated_dir / "symbols_en.rst"
            rst_path.write_text(
                ".. image:: templates/word_template/common_assets/symbols/warning_triangle.png\n",
                encoding="utf-8",
            )

            issues = check_docs.collect_reference_issues(
                rst_path=rst_path,
                bundle_dir=bundle_dir,
                docs_dir=docs_dir,
                model="JE-1000F",
                region="US",
            )

            self.assertEqual([], issues)

    def test_collect_check_issues_should_report_generated_page_snippet_problems(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "US" / "rst"
            (bundle_dir / "page").mkdir(parents=True)
            (docs_dir / "templates" / "page_us-en").mkdir(parents=True)
            (docs_dir / "templates" / "recipes").mkdir(parents=True)
            (docs_dir / "templates" / "snippets").mkdir(parents=True)

            (bundle_dir / "index.rst").write_text(".. include:: page/03_product_overview_placeholder.rst\n", encoding="utf-8")
            (bundle_dir / "page" / "03_product_overview_placeholder.rst").write_text("Ready\n", encoding="utf-8")

            (docs_dir / "templates" / "page_us-en" / "03_product_overview_placeholder.rst").write_text(
                "{{snippet:intro}}\n",
                encoding="utf-8",
            )
            (docs_dir / "templates" / "recipes" / "03_product_overview.yaml").write_text(
                "\n".join(
                    [
                        "page_id: 03_product_overview",
                        "template: templates/page_us-en/03_product_overview_placeholder.rst",
                        "field_map:",
                        "  MAIN_POWER_BUTTON_LABEL:",
                        "    row_key: main_power_button",
                        "    pages: [Product overview]",
                        "    usage_type: page_value",
                        "    value_role: label",
                        "required_row_keys:",
                        "  - product_name",
                        "snippet_slots:",
                        "  intro: missing_intro",
                        "contracts:",
                        "  - 03_product_overview",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (docs_dir / "templates" / "snippets" / "registry.yaml").write_text("snippets: []\n", encoding="utf-8")

            spec_master = root / "Spec_Master.csv"
            spec_master.write_text(
                "\n".join(
                    [
                        "Model,Region,Is_Latest,Page,Row_key,Value_source",
                        "JE-1000F,US,TRUE,specifications,product_name,Jackery 1000",
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
                        "    page: 03_product_overview",
                        "    engine: draft_v1",
                        "    recipe: templates/recipes/03_product_overview.yaml",
                        "    template: templates/page_us-en/03_product_overview_placeholder.rst",
                        "    langs: [en]",
                        "    include_dir: generated/{model}/draft",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            config_path = root / "config.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "build:",
                        "  languages: [en]",
                        "paths:",
                        f"  docs_dir: {docs_dir.as_posix()}",
                        f"  spec_master_csv: {spec_master.as_posix()}",
                        f"  page_manifest: {manifest_path.as_posix()}",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            issues = check_docs.collect_check_issues(
                cfg_path=config_path,
                model="JE-1000F",
                region="US",
                all_targets=False,
            )

            codes = {issue.code for issue in issues}
            self.assertIn("RECIPE_MISSING_FIELD_MAP_ROWS", codes)
            self.assertIn("MISSING_SNIPPET", codes)

    def test_collect_check_issues_should_report_unused_field_map_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "US" / "rst"
            (bundle_dir / "page").mkdir(parents=True)
            (docs_dir / "templates" / "page_us-en").mkdir(parents=True)
            (docs_dir / "templates" / "recipes").mkdir(parents=True)
            (docs_dir / "templates" / "snippets").mkdir(parents=True)

            (bundle_dir / "index.rst").write_text(".. include:: page/demo.rst\n", encoding="utf-8")
            (bundle_dir / "page" / "demo.rst").write_text("Ready\n", encoding="utf-8")
            (docs_dir / "templates" / "page_us-en" / "demo.rst").write_text(
                "|PRODUCT_NAME|\n",
                encoding="utf-8",
            )
            (docs_dir / "templates" / "recipes" / "demo.yaml").write_text(
                "\n".join(
                    [
                        "page_id: demo",
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
            (docs_dir / "templates" / "snippets" / "registry.yaml").write_text("snippets: []\n", encoding="utf-8")

            spec_master = root / "Spec_Master.csv"
            spec_master.write_text(
                "\n".join(
                    [
                        "Model,Region,Is_Latest,Page,Row_key,Usage_type,Value_role,Value_source",
                        "JE-1000F,US,TRUE,specifications,product_name,,,Jackery 1000",
                        "JE-1000F,US,TRUE,specifications,model_no,,,JE-1000F",
                        "JE-1000F,US,TRUE,Product overview,main_power_button,page_value,label,Main POWER Button",
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
                        "    page: demo",
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

            config_path = root / "config.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "build:",
                        "  languages: [en]",
                        "paths:",
                        f"  docs_dir: {docs_dir.as_posix()}",
                        f"  spec_master_csv: {spec_master.as_posix()}",
                        f"  page_manifest: {manifest_path.as_posix()}",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            issues = check_docs.collect_check_issues(
                cfg_path=config_path,
                model="JE-1000F",
                region="US",
                all_targets=False,
            )

            codes = {issue.code for issue in issues}
            self.assertIn("UNUSED_FIELD_MAP_PLACEHOLDER", codes)

    def test_collect_check_issues_should_report_unknown_recipe_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs_dir = root / "docs"
            bundle_dir = docs_dir / "_build" / "JE-1000F" / "US" / "rst"
            (bundle_dir / "page").mkdir(parents=True)
            (docs_dir / "templates" / "page_us-en").mkdir(parents=True)
            (docs_dir / "templates" / "recipes").mkdir(parents=True)
            (docs_dir / "templates" / "snippets").mkdir(parents=True)

            (bundle_dir / "index.rst").write_text(".. include:: page/demo.rst\n", encoding="utf-8")
            (bundle_dir / "page" / "demo.rst").write_text("Ready\n", encoding="utf-8")
            (docs_dir / "templates" / "page_us-en" / "demo.rst").write_text(
                "|MYSTERY_TOKEN|\n",
                encoding="utf-8",
            )
            (docs_dir / "templates" / "recipes" / "demo.yaml").write_text(
                "\n".join(
                    [
                        "page_id: demo",
                        "template: templates/page_us-en/demo.rst",
                        "field_map: {}",
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
            (docs_dir / "templates" / "snippets" / "registry.yaml").write_text("snippets: []\n", encoding="utf-8")

            spec_master = root / "Spec_Master.csv"
            spec_master.write_text(
                "\n".join(
                    [
                        "Model,Region,Is_Latest,Page,Row_key,Value_source",
                        "JE-1000F,US,TRUE,specifications,product_name,Jackery 1000",
                        "JE-1000F,US,TRUE,specifications,model_no,JE-1000F",
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
                        "    page: demo",
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

            config_path = root / "config.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "build:",
                        "  languages: [en]",
                        "paths:",
                        f"  docs_dir: {docs_dir.as_posix()}",
                        f"  spec_master_csv: {spec_master.as_posix()}",
                        f"  page_manifest: {manifest_path.as_posix()}",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            issues = check_docs.collect_check_issues(
                cfg_path=config_path,
                model="JE-1000F",
                region="US",
                all_targets=False,
            )

            codes = {issue.code for issue in issues}
            self.assertIn("UNKNOWN_RECIPE_PLACEHOLDERS", codes)


if __name__ == "__main__":
    unittest.main()
