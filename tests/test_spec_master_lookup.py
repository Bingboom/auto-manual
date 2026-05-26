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
                "Value_source": "Jackery HomePower 2000 Plus v2",
                "Value_fr": "Jackery HomePower 2000 Plus v2 FR",
                "Model": "JHP-2000A",
            },
            {
                "Region": "JP",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Row_key": "product_name",
                "Value_source": "Jackery HomePower 2000 Plus JP",
                "Model": "JHP-2000A",
            },
            {
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Row_key": "model_no",
                "Value_source": "JHP-2000A",
                "Model": "JHP-2000A",
            },
            {
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Row_key": "main_power_button",
                "Slot_key": "label",
                "Value_source": "Main POWER Button",
                "Model": "JHP-2000A",
            },
            {
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Row_key": "battery_pack_name",
                "Slot_key": "value",
                "Value_source": "Jackery Battery Pack 3600",
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

    def test_lookup_product_name_should_normalize_document_key_style_model_suffix(self) -> None:
        match = resolve_product_name_from_rows(
            self._rows(),
            model="JHP-2000A_JP",
            region="JP",
            lang="ja",
        )
        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual("Jackery HomePower 2000 Plus JP", match.product_name)
        self.assertEqual("JP", match.region)

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

    def test_lookup_should_prefer_localized_row_label_for_translated_label_page_values(self) -> None:
        rows = [
            {
                "Region": "EU",
                "Is_Latest": "TRUE",
                "Page": "Product overview",
                "Row_key": "main_power_button",
                "Slot_key": "label",
                "Source_lang": "en",
                "Row_label_source": "Power Button",
                "Row_label_de": "Einschalttaste",
                "Value_source": "POWER Button",
                "Value_de": "POWER-Taste",
                "Model": "JE-1000F",
            }
        ]

        match = resolve_spec_value_from_rows(
            rows,
            model="JE-1000F",
            region="EU",
            lang="de",
            row_key="main_power_button",
            pages=("Product overview",),
            usage_type="page_value",
            value_role="label",
        )

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual("Einschalttaste", match.value)

        substitutions = resolve_template_substitutions_from_rows(
            rows,
            model="JE-1000F",
            region="EU",
            lang="de",
        )
        self.assertEqual("Einschalttaste", substitutions["MAIN_POWER_BUTTON_LABEL"])
        self.assertEqual("einschalttaste", substitutions["MAIN_POWER_BUTTON_LABEL_LOWER"])

    def test_lookup_should_fallback_to_value_when_localized_row_label_contains_translation_note(self) -> None:
        rows = [
            {
                "Region": "EU",
                "Is_Latest": "TRUE",
                "Page": "Product overview",
                "Row_key": "ac_power_button",
                "Slot_key": "label",
                "Source_lang": "en",
                "Row_label_source": "AC Power Button",
                "Row_label_uk": "Вхід струму змінного струму\n（说明：这是翻译备注）",
                "Value_source": "AC Power Button",
                "Value_uk": "Кнопка живлення змінного струму",
                "Model": "JE-1000F",
            }
        ]

        match = resolve_spec_value_from_rows(
            rows,
            model="JE-1000F",
            region="EU",
            lang="uk",
            row_key="ac_power_button",
            pages=("Product overview",),
            usage_type="page_value",
            value_role="label",
        )

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual("Кнопка живлення змінного струму", match.value)

    def test_lookup_should_fallback_to_value_when_localized_row_label_matches_source_text(self) -> None:
        rows = [
            {
                "Region": "EU",
                "Is_Latest": "TRUE",
                "Page": "Product overview",
                "Row_key": "dc_usb_power_button",
                "Slot_key": "label",
                "Source_lang": "en",
                "Row_label_source": "DC/USB Power Button",
                "Row_label_de": "DC/USB Power Button",
                "Value_source": "DC/USB Power Button",
                "Value_de": "DC/USB-Ein/Ausschaltknopf",
                "Model": "JE-1000F",
            }
        ]

        match = resolve_spec_value_from_rows(
            rows,
            model="JE-1000F",
            region="EU",
            lang="de",
            row_key="dc_usb_power_button",
            pages=("Product overview",),
            usage_type="page_value",
            value_role="label",
        )

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual("DC/USB-Ein/Ausschaltknopf", match.value)

    def test_lookup_should_use_br_columns_for_pt_br_language(self) -> None:
        rows = [
            {
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "Product overview",
                "Row_key": "main_power_button",
                "Slot_key": "label",
                "Source_lang": "en",
                "Row_label_source": "Main Power Button",
                "Row_label_br": "Botão Power Principal",
                "Value_source": "Main Power Button",
                "Value_br": "Botão Power Principal",
                "Model": "JE-1000F",
            },
            {
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "Product overview",
                "Row_key": "ac_power_button",
                "Slot_key": "label",
                "Source_lang": "en",
                "Row_label_source": "AC Power Button",
                "Row_label_br": "Botão CA",
                "Value_source": "AC Power Button",
                "Value_br": "Botão CA",
                "Model": "JE-1000F",
            },
            {
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "operation_guide",
                "Row_key": "energy_saving_auto_off_duration",
                "Slot_key": "value",
                "Source_lang": "en",
                "Value_source": "12 hours",
                "Value_br": "12 horas",
                "Model": "JE-1000F",
            },
        ]

        label = resolve_spec_value_from_rows(
            rows,
            model="JE-1000F",
            region="US",
            lang="pt-BR",
            row_key="ac_power_button",
            pages=("Product overview",),
            usage_type="page_value",
            value_role="label",
        )
        duration = resolve_spec_value_from_rows(
            rows,
            model="JE-1000F",
            region="US",
            lang="pt-BR",
            row_key="energy_saving_auto_off_duration",
            pages=("operation_guide",),
            usage_type="page_value",
        )

        self.assertIsNotNone(label)
        self.assertIsNotNone(duration)
        assert label is not None
        assert duration is not None
        self.assertEqual("Botão CA", label.value)
        self.assertEqual("12 horas", duration.value)

        substitutions = resolve_template_substitutions_from_rows(
            rows,
            model="JE-1000F",
            region="US",
            lang="pt-BR",
        )
        self.assertEqual("Botão Power Principal", substitutions["MAIN_POWER_BUTTON_LABEL"])
        self.assertEqual("botão Power principal", substitutions["MAIN_POWER_BUTTON_LABEL_LOWER"])

    def test_lookup_should_match_comma_separated_page_values(self) -> None:
        rows = [
            {
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "Product overview, specifications,",
                "Row_key": "product_name",
                "Value_source": "Jackery HomePower 2000 Plus v2",
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
                "Value_source": "Jackery HomePower 2000 Plus v2",
                "Model": "JHP-2000A",
            },
            {
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "Product overview, specifications,",
                "Row_key": "model_no",
                "Value_source": "JHP-2000A",
                "Model": "JHP-2000A",
            },
            {
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "Product overview",
                "Row_key": "tpl_main_power_button_label",
                "Value_source": "Main POWER Button",
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

    def test_template_substitutions_should_include_storage_temperature_multiline_placeholders(self) -> None:
        rows = [
            {
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Row_key": "charging_temperature",
                "Line_order": "1",
                "Value_source": "-4°F to 113°F / -20°C to 45°C",
                "Value_fr": "-4°F à 113°F / -20°C à 45°C",
                "Value_es": "-4°F a 113°F / -20°C a 45°C",
                "Model": "JHP-2000A",
            },
            {
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "specifications",
                "Row_key": "discharging_temperature",
                "Line_order": "1",
                "Value_source": "-4°F to 113°F / -20°C to 45°C",
                "Value_fr": "-4°F à 113°F / -20°C à 45°C",
                "Value_es": "-4°F a 113°F / -20°C a 45°C",
                "Model": "JHP-2000A",
            },
            {
                "Region": "US",
                "Is_Latest": "TRUE",
                "Page": "storage",
                "Row_key": "storage_temperature",
                "Line_order": "1",
                "Param_source": "1 month",
                "Value_source": "-4°F to 113°F / -20°C to 45°C (0-60%RH)",
                "Param_fr": "1 mois",
                "Value_fr": "-4°F à 113°F / -20°C à 45°C (0-60% HR)",
                "Param_es": "1 mes",
                "Value_es": "-4°F a 113°F / -20°C a 45°C (0-60% HR)",
                "Model": "JHP-2000A",
            },
            {
                "Region": "JP",
                "Is_Latest": "TRUE",
                "Page": "storage",
                "Row_key": "storage_temperature",
                "Line_order": "1",
                "Param_source": "1か月",
                "Value_source": "-20℃ ～ 45℃（0-60% RH）",
                "Model": "JHP-2000A",
            },
        ]

        en_substitutions = resolve_template_substitutions_from_rows(
            rows,
            model="JHP-2000A",
            region="US",
            lang="en",
        )
        fr_substitutions = resolve_template_substitutions_from_rows(
            rows,
            model="JHP-2000A",
            region="US",
            lang="fr",
        )
        es_substitutions = resolve_template_substitutions_from_rows(
            rows,
            model="JHP-2000A",
            region="US",
            lang="es",
        )
        ja_substitutions = resolve_template_substitutions_from_rows(
            rows,
            model="JHP-2000A",
            region="JP",
            lang="ja",
        )

        self.assertEqual(
            "1 month: -4°F to 113°F / -20°C to 45°C (0-60%RH)",
            en_substitutions["STORAGE_TEMPERATURE_LINE_1"],
        )
        self.assertEqual(
            "-4°F to 113°F / -20°C to 45°C",
            en_substitutions["CHARGING_TEMPERATURE_VALUE_1"],
        )
        self.assertEqual(
            "-4°F to 113°F / -20°C to 45°C",
            en_substitutions["DISCHARGING_TEMPERATURE_VALUE_1"],
        )
        self.assertEqual(
            "1 mois : -4°F à 113°F / -20°C à 45°C (0-60% HR)",
            fr_substitutions["STORAGE_TEMPERATURE_LINE_1"],
        )
        self.assertEqual(
            "-4°F à 113°F / -20°C à 45°C",
            fr_substitutions["CHARGING_TEMPERATURE_VALUE_1"],
        )
        self.assertEqual(
            "1 mes: -4°F a 113°F / -20°C a 45°C (0-60% HR)",
            es_substitutions["STORAGE_TEMPERATURE_LINE_1"],
        )
        self.assertEqual(
            "-4°F a 113°F / -20°C a 45°C",
            es_substitutions["CHARGING_TEMPERATURE_VALUE_1"],
        )
        self.assertEqual(
            "1か月：-20℃ ～ 45℃（0-60% RH）",
            ja_substitutions["STORAGE_TEMPERATURE_LINE_1"],
        )

    def test_real_spec_master_should_resolve_je1000f_us_product_name_for_western_langs(self) -> None:
        spec_master_csv = Path(__file__).resolve().parents[1] / "data" / "phase2" / "Spec_Master.csv"

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

    def test_real_spec_master_should_resolve_phase2_temperature_placeholders_for_us_and_jp(self) -> None:
        spec_master_csv = Path(__file__).resolve().parents[1] / "data" / "phase2" / "Spec_Master.csv"

        expected_us_prefixes = {
            "en": "1 month:",
            "fr": "1 mois :",
            "es": "1 mes:",
        }
        for lang, expected_prefix in expected_us_prefixes.items():
            substitutions = resolve_template_substitutions_from_spec_master(
                spec_master_csv,
                model="JE-1000F",
                region="US",
                lang=lang,
            )
            storage_line = substitutions["STORAGE_TEMPERATURE_LINE_1"]
            self.assertTrue(storage_line.startswith(expected_prefix), storage_line)
            self.assertIn("0-60", storage_line)

        us_en_substitutions = resolve_template_substitutions_from_spec_master(
            spec_master_csv,
            model="JE-1000F",
            region="US",
            lang="en",
        )
        self.assertTrue(us_en_substitutions["CHARGING_TEMPERATURE_VALUE_1"].startswith("14"))
        self.assertIn("45", us_en_substitutions["DISCHARGING_TEMPERATURE_VALUE_1"])

        jp_substitutions = resolve_template_substitutions_from_spec_master(
            spec_master_csv,
            model="JE-1000F",
            region="JP",
            lang="ja",
        )
        self.assertTrue(jp_substitutions["CHARGING_TEMPERATURE_VALUE_1"].startswith("-10"))
        self.assertIn("45", jp_substitutions["DISCHARGING_TEMPERATURE_VALUE_1"])


if __name__ == "__main__":
    unittest.main()
