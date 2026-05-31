from __future__ import annotations

import unittest

from tools.localized_copy import LocalizedCopyResolver


class TestLocalizedCopyResolver(unittest.TestCase):
    def test_resolve_should_prefer_model_and_region_specific_copy(self) -> None:
        resolver = LocalizedCopyResolver(
            [
                {
                    "copy_key": "product.page_title",
                    "Region": "",
                    "Model": "",
                    "Is_Latest": "TRUE",
                    "text_en": "Generic",
                },
                {
                    "copy_key": "product.page_title",
                    "Region": "US",
                    "Model": "JE-1000F",
                    "Is_Latest": "TRUE",
                    "text_en": "Specific",
                },
            ]
        )

        self.assertEqual(
            "Specific",
            resolver.resolve(
                "product.page_title",
                lang="en",
                model="JE-1000F_US",
                region="US",
            ),
        )

    def test_resolve_should_reject_missing_target_language_text(self) -> None:
        resolver = LocalizedCopyResolver(
            [
                {
                    "copy_key": "product.page_title",
                    "Region": "",
                    "Model": "",
                    "Is_Latest": "TRUE",
                    "text_en": "English",
                    "text_fr": "",
                }
            ]
        )

        with self.assertRaisesRegex(KeyError, "has no value for lang 'fr'"):
            resolver.resolve("product.page_title", lang="fr")

    def test_apply_should_replace_copy_tokens(self) -> None:
        resolver = LocalizedCopyResolver(
            [
                {
                    "copy_key": "product.page_title",
                    "Region": "",
                    "Model": "",
                    "Is_Latest": "TRUE",
                    "text_en": "PRODUCT OVERVIEW",
                }
            ]
        )

        self.assertEqual(
            "PRODUCT OVERVIEW\n================",
            resolver.apply("{{ copy:product.page_title }}\n================", lang="en"),
        )


if __name__ == "__main__":
    unittest.main()
