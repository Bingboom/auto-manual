from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import page_contracts


class TestPageContracts(unittest.TestCase):
    def test_load_page_contracts_should_parse_default_and_lang_specific_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            contracts_dir = Path(td)
            (contracts_dir / "03_product_overview.yaml").write_text(
                "\n".join(
                    [
                        "page_id: 03_product_overview",
                        "source_files:",
                        "  - templates/page_us-en/03_product_overview_placeholder.rst",
                        "required_placeholders:",
                        "  default:",
                        "    - MAIN_POWER_BUTTON_LABEL",
                        "  en:",
                        "    - FRONT_TOTAL_OUTPUT_LABEL",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            contracts = page_contracts.load_page_contracts(contracts_dir)

            self.assertEqual(1, len(contracts))
            contract = contracts[0]
            self.assertEqual("03_product_overview", contract.page_id)
            self.assertEqual(
                ("MAIN_POWER_BUTTON_LABEL", "FRONT_TOTAL_OUTPUT_LABEL"),
                page_contracts.required_placeholders_for_lang(contract, "en"),
            )
            self.assertEqual(
                ("MAIN_POWER_BUTTON_LABEL",),
                page_contracts.required_placeholders_for_lang(contract, "ja"),
            )

    def test_find_contract_for_source_should_match_normalized_relative_paths(self) -> None:
        contract = page_contracts.PageContract(
            page_id="03_product_overview",
            source_files=("templates/page_us-en/03_product_overview_placeholder.rst",),
            required_placeholders={"default": ("MAIN_POWER_BUTTON_LABEL",)},
            required_spec_keys={},
            required_page_values={},
            required_assets={},
            allowed_languages=(),
            allowed_regions=(),
            allowed_models=(),
        )

        matched = page_contracts.find_contract_for_source(
            r"templates\page_us-en\03_product_overview_placeholder.rst",
            [contract],
        )

        self.assertIsNotNone(matched)
        assert matched is not None
        self.assertEqual("03_product_overview", matched.page_id)

    def test_load_page_contracts_should_parse_page_value_selectors_and_scope(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            contracts_dir = Path(td)
            (contracts_dir / "05_operation_guide.yaml").write_text(
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
                        "    - product_name",
                        "required_page_values:",
                        "  default:",
                        "    - row_key: main_power_button",
                        "      pages: [Product overview]",
                        "      usage_type: page_value",
                        "      value_role: label",
                        "required_assets:",
                        "  en:",
                        "    - templates/word_template/common_assets/overview/front_product.jpg",
                        "allowed_languages: [en]",
                        "allowed_regions: [US]",
                        "allowed_models: [JE-1000F]",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            contracts = page_contracts.load_page_contracts(contracts_dir)

            self.assertEqual(1, len(contracts))
            contract = contracts[0]
            self.assertEqual(("product_name",), page_contracts.required_spec_keys_for_lang(contract, "en"))
            page_values = page_contracts.required_page_values_for_lang(contract, "en")
            self.assertEqual(1, len(page_values))
            self.assertEqual("main_power_button", page_values[0].row_key)
            self.assertEqual(("Product overview",), page_values[0].pages)
            self.assertEqual("page_value", page_values[0].usage_type)
            self.assertEqual("label", page_values[0].value_role)
            self.assertEqual(
                ("templates/word_template/common_assets/overview/front_product.jpg",),
                page_contracts.required_assets_for_lang(contract, "en"),
            )
            self.assertTrue(
                page_contracts.contract_applies_to(
                    contract,
                    lang="en",
                    model="JE-1000F",
                    region="US",
                )
            )
            self.assertFalse(
                page_contracts.contract_applies_to(
                    contract,
                    lang="ja",
                    model="JE-1000F",
                    region="US",
                )
            )

    def test_load_page_contracts_should_reject_page_value_selector_without_row_key(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            contracts_dir = Path(td)
            (contracts_dir / "bad.yaml").write_text(
                "\n".join(
                    [
                        "page_id: bad",
                        "source_files:",
                        "  - templates/page_en/bad.rst",
                        "required_page_values:",
                        "  default:",
                        "    - usage_type: page_value",
                        "      value_role: label",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, "row_key is required"):
                page_contracts.load_page_contracts(contracts_dir)


if __name__ == "__main__":
    unittest.main()
