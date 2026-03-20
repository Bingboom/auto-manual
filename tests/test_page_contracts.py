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
        )

        matched = page_contracts.find_contract_for_source(
            r"templates\page_us-en\03_product_overview_placeholder.rst",
            [contract],
        )

        self.assertIsNotNone(matched)
        assert matched is not None
        self.assertEqual("03_product_overview", matched.page_id)


if __name__ == "__main__":
    unittest.main()
