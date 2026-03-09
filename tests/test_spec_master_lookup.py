from __future__ import annotations

import unittest

from tools.utils.spec_master import resolve_product_name_from_rows, resolve_template_substitutions_from_rows


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


if __name__ == "__main__":
    unittest.main()
