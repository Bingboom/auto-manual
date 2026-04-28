from __future__ import annotations

import unittest

from tools.utils.variable_resolver import (
    parse_model_tokens,
    resolve_variable_value,
    resolve_variables,
)


class TestVariableResolver(unittest.TestCase):
    def _defaults(self) -> list[dict[str, object]]:
        return [
            {
                "Variable_key": "CURRENT_MODE",
                "Model_key": "",
                "Model": "JE-1000F, JE-2000",
                "Value": "AC",
                "is_default": "",
            },
            {
                "Variable_key": "CURRENT_MODE",
                "Model_key": "",
                "Model": "",
                "Value": "AC default",
                "is_default": "TRUE",
            },
            {
                "Variable_key": "CURRENT_MODE_NUMBERED",
                "Model": "['JE-1000F', 'JE-3000']",
                "Value": "AC1/2",
                "is_default": "",
            },
            {
                "Variable_key": "PORT_GROUP",
                "Model": "JE-1000F|JE-2000",
                "Value": "DC/USB",
                "is_default": "",
            },
            {
                "Variable_key": "UKR_PHRASE",
                "Model": "JE-1000F; JE-3000",
                "Value": "AC output is on.",
                "is_default": "",
            },
        ]

    def _overrides(self) -> list[dict[str, str]]:
        return [
            {
                "Variable_key": "CURRENT_MODE",
                "lang": "fr",
                "source_value": "AC",
                "Value": "CA",
            },
            {
                "Variable_key": "CURRENT_MODE_NUMBERED",
                "lang": "fr",
                "source_value": "AC1/2",
                "Value": "CA1/2",
            },
            {
                "Variable_key": "PORT_GROUP",
                "lang": "fr",
                "source_value": "DC/USB",
                "Value": "CC/USB",
            },
            {
                "Variable_key": "PORT_GROUP",
                "lang": "es",
                "from_prefix": "DC/USB",
                "to_prefix": "CC/USB",
            },
            {
                "Variable_key": "UKR_PHRASE",
                "lang": "ukr",
                "source_value": "AC output",
                "Value": "partial match should not apply",
            },
            {
                "Variable_key": "UKR_PHRASE",
                "lang": "ukr",
                "source_value": "AC output is on.",
                "Value": "Вихід змінного струму увімкнено.",
            },
        ]

    def test_model_membership_is_exact_and_preferred_over_default(self) -> None:
        value = resolve_variable_value(
            self._defaults(),
            self._overrides(),
            "CURRENT_MODE",
            model="JE-1000F",
            lang="en",
        )

        self.assertEqual("AC", value)

    def test_model_key_is_preferred_when_model_cell_is_link_id_json(self) -> None:
        rows = [
            {
                "Variable_key": "CURRENT_MODE",
                "Model_key": "JE-1000F",
                "Model": '{"id":"rec_link_id"}',
                "Value": "AC",
                "is_default": "FALSE",
            },
            {
                "Variable_key": "CURRENT_MODE",
                "Model_key": "",
                "Model": "",
                "Value": "AC1/2",
                "is_default": "TRUE",
            },
        ]

        value = resolve_variable_value(rows, [], "CURRENT_MODE", model="JE-1000F", lang="en")

        self.assertEqual("AC", value)

    def test_ac_resolves_to_ca_for_french(self) -> None:
        value = resolve_variable_value(
            self._defaults(),
            self._overrides(),
            "CURRENT_MODE",
            model="JE-1000F",
            lang="fr",
        )

        self.assertEqual("CA", value)

    def test_ac_numbered_resolves_to_ca_numbered_for_french(self) -> None:
        value = resolve_variable_value(
            self._defaults(),
            self._overrides(),
            "CURRENT_MODE_NUMBERED",
            model="JE-3000",
            lang="fr",
        )

        self.assertEqual("CA1/2", value)

    def test_dc_usb_resolves_to_cc_usb_for_french(self) -> None:
        value = resolve_variable_value(
            self._defaults(),
            self._overrides(),
            "PORT_GROUP",
            model="JE-2000",
            lang="fr",
        )

        self.assertEqual("CC/USB", value)

    def test_override_accepts_prefix_field_aliases(self) -> None:
        value = resolve_variable_value(
            self._defaults(),
            self._overrides(),
            "PORT_GROUP",
            model="JE-2000",
            lang="es",
        )

        self.assertEqual("CC/USB", value)

    def test_uk_lang_alias_matches_ukr_override_rows(self) -> None:
        value = resolve_variable_value(
            self._defaults(),
            self._overrides(),
            "UKR_PHRASE",
            model="JE-1000F",
            lang="uk",
        )
        expected = resolve_variable_value(
            self._defaults(),
            self._overrides(),
            "UKR_PHRASE",
            model="JE-1000F",
            lang="ukr",
        )

        self.assertEqual(expected, value)

    def test_ukr_override_uses_exact_source_phrase(self) -> None:
        value = resolve_variable_value(
            self._defaults(),
            self._overrides(),
            "UKR_PHRASE",
            model="JE-1000F",
            lang="ukr",
        )

        self.assertEqual("Вихід змінного струму увімкнено.", value)

    def test_falls_back_to_single_default_when_model_does_not_match(self) -> None:
        value = resolve_variable_value(
            self._defaults(),
            self._overrides(),
            "CURRENT_MODE",
            model="JE-1000F-PRO",
            lang="fr",
        )

        self.assertEqual("AC default", value)

    def test_parse_model_tokens_accepts_separators_and_list_like_text(self) -> None:
        self.assertEqual(("JE-1000F", "JE-2000", "JE-3000"), parse_model_tokens("JE-1000F, JE-2000|JE-3000"))
        self.assertEqual(("JE-1000F", "JE-2000"), parse_model_tokens("['JE-1000F', 'JE-2000']"))
        self.assertEqual(("JE-1000F", "JE-2000"), parse_model_tokens(["JE-1000F", "JE-2000"]))

    def test_resolve_variables_returns_each_known_key(self) -> None:
        values = resolve_variables(self._defaults(), self._overrides(), model="JE-1000F", lang="fr")

        self.assertEqual("CA", values["CURRENT_MODE"])
        self.assertEqual("CA1/2", values["CURRENT_MODE_NUMBERED"])
        self.assertEqual("CC/USB", values["PORT_GROUP"])

    def test_duplicate_exact_model_matches_raise(self) -> None:
        rows = [
            {"Variable_key": "CURRENT_MODE", "Model": "JE-1000F", "Value": "AC", "is_default": ""},
            {"Variable_key": "CURRENT_MODE", "Model": "JE-1000F|JE-2000", "Value": "AC duplicate", "is_default": ""},
        ]

        with self.assertRaises(ValueError):
            resolve_variable_value(rows, [], "CURRENT_MODE", model="JE-1000F", lang="fr")

    def test_duplicate_defaults_raise(self) -> None:
        rows = [
            {"Variable_key": "CURRENT_MODE", "Model": "", "Value": "AC", "is_default": "TRUE"},
            {"Variable_key": "CURRENT_MODE", "Model": "", "Value": "AC duplicate", "is_default": "true"},
        ]

        with self.assertRaises(ValueError):
            resolve_variable_value(rows, [], "CURRENT_MODE", model="JE-1000F", lang="fr")

    def test_duplicate_exact_overrides_raise(self) -> None:
        overrides = [
            {"Variable_key": "CURRENT_MODE", "lang": "fr", "source_value": "AC", "Value": "CA"},
            {"Variable_key": "CURRENT_MODE", "lang": "FR", "source_value": "AC", "Value": "CA duplicate"},
        ]

        with self.assertRaises(ValueError):
            resolve_variable_value(self._defaults(), overrides, "CURRENT_MODE", model="JE-1000F", lang="fr")


if __name__ == "__main__":
    unittest.main()
