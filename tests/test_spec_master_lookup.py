from __future__ import annotations

import unittest
from pathlib import Path

from tools.utils.spec_master import (
    resolve_product_name_from_rows,
    resolve_product_name_from_spec_master,
    resolve_spec_value_from_rows,
    resolve_template_substitutions_from_rows,
    resolve_template_substitutions_from_spec_master,
)


class TestSpecMasterLookup(unittest.TestCase):
    def _rows(self) -> list[dict[str, str]]:
        return [
            {
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Row_key": "product_name",
                "Value_en": "Jackery HomePower 2000 Plus v2",
                "Value_fr": "Jackery HomePower 2000 Plus v2 FR",
                "Model": "JHP-2000A",
            },
            {
                "Region": "EU",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Row_key": "product_name",
                "Value_en": "Jackery HomePower 2000 Plus EU",
                "Model": "JHP-2000A",
            },
            {
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Row_key": "model_no",
                "Value_en": "JHP-2000A",
                "Model": "JHP-2000A",
            },
            {
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Row_key": "tpl_main_power_button_label",
                "Value_en": "Main POWER Button",
                "Model": "JHP-2000A",
            },
            {
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Row_key": "tpl_battery_pack_name",
                "Value_en": "Jackery Battery Pack 3600",
                "Model": "JHP-2000A",
            },
        ]

    def test_lookup_product_name_by_model_region_and_lang(self) -> None:
        match = resolve_product_name_from_rows(
            self._rows(),
            model="JHP-2000A",
            region="US",
            lang="en",
        )
        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual("Jackery HomePower 2000 Plus v2", match.product_name)
        self.assertEqual("US", match.region)

    def test_lookup_product_name_uses_language_value_when_available(self) -> None:
        match = resolve_product_name_from_rows(
            self._rows(),
            model="JHP-2000A",
            region="US",
            lang="fr",
        )
        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual("Jackery HomePower 2000 Plus v2 FR", match.product_name)

    def test_lookup_product_name_returns_none_when_model_not_found(self) -> None:
        match = resolve_product_name_from_rows(
            self._rows(),
            model="JHP-9999X",
            region="US",
            lang="en",
        )
        self.assertIsNone(match)

    def test_template_substitutions_should_include_derived_and_custom_values(self) -> None:
        substitutions = resolve_template_substitutions_from_rows(
            self._rows(),
            model="JHP-2000A",
            region="US",
            lang="en",
        )

        self.assertEqual("Jackery HomePower 2000 Plus v2", substitutions["PRODUCT_NAME"])
        self.assertEqual("HomePower 2000 Plus v2", substitutions["PRODUCT_SHORT_NAME"])
        self.assertEqual("JHP-2000A", substitutions["MODEL_NO"])
        self.assertEqual("Main POWER Button", substitutions["MAIN_POWER_BUTTON_LABEL"])
        self.assertEqual("main POWER button", substitutions["MAIN_POWER_BUTTON_LABEL_LOWER"])
        self.assertEqual("**Jackery Battery Pack 3600**", substitutions["BATTERY_PACK_NAME_BOLD"])

    def test_lookup_should_match_comma_separated_page_values(self) -> None:
        rows = [
            {
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "Product overview, specifications,",
                "Row_key": "product_name",
                "Value_en": "Jackery HomePower 2000 Plus v2",
                "Model": "JHP-2000A",
            }
        ]

        match = resolve_spec_value_from_rows(
            rows,
            model="JHP-2000A",
            region="US",
            lang="en",
            row_key="product_name",
            pages=("specifications",),
        )

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual("Jackery HomePower 2000 Plus v2", match.value)

    def test_template_substitutions_should_include_tpl_rows_from_product_overview_pages(self) -> None:
        rows = [
            {
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "Product overview, specifications,",
                "Row_key": "product_name",
                "Value_en": "Jackery HomePower 2000 Plus v2",
                "Model": "JHP-2000A",
            },
            {
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "Product overview, specifications,",
                "Row_key": "model_no",
                "Value_en": "JHP-2000A",
                "Model": "JHP-2000A",
            },
            {
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "Product overview",
                "Row_key": "tpl_main_power_button_label",
                "Value_en": "Main POWER Button",
                "Model": "JHP-2000A",
            },
        ]

        substitutions = resolve_template_substitutions_from_rows(
            rows,
            model="JHP-2000A",
            region="US",
            lang="en",
        )

        self.assertEqual("Jackery HomePower 2000 Plus v2", substitutions["PRODUCT_NAME"])
        self.assertEqual("JHP-2000A", substitutions["MODEL_NO"])
        self.assertEqual("Main POWER Button", substitutions["MAIN_POWER_BUTTON_LABEL"])

    def test_real_spec_master_should_resolve_je1000f_us_product_name_for_western_langs(self) -> None:
        spec_master_csv = Path(__file__).resolve().parents[1] / "data" / "phase1" / "Spec_Master.csv"

        for lang in ("en", "es", "fr"):
            match = resolve_product_name_from_spec_master(
                spec_master_csv,
                model="JE-1000F",
                region="US",
                lang=lang,
            )
            self.assertIsNotNone(match)
            assert match is not None
            self.assertEqual("Jackery Explorer 1000", match.product_name)
            self.assertEqual("US", match.region)

        substitutions = resolve_template_substitutions_from_spec_master(
            spec_master_csv,
            model="JE-1000F",
            region="US",
            lang="en",
        )
        self.assertEqual("Jackery Explorer 1000", substitutions["PRODUCT_NAME"])
        self.assertEqual("Explorer 1000", substitutions["PRODUCT_SHORT_NAME"])


if __name__ == "__main__":
    unittest.main()
