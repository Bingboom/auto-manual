from __future__ import annotations

import unittest

from tools.utils.spec_master import resolve_product_name_from_rows


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


if __name__ == "__main__":
    unittest.main()
