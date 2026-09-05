from __future__ import annotations

import unittest

from tools import lang_registry
from tools.localized_copy import (
    LocalizedCopyResolver,
    first_existing_column,
    first_text,
    localized_cell,
    localized_columns,
    snapshot_language_suffixes,
    table_localized_columns,
)


class TestSnapshotColumnSelection(unittest.TestCase):
    def test_canonical_identity_does_not_change_historical_suffix_order(self) -> None:
        for code, aliases, suffixes in (
            ("ja", ("ja", "JP"), ("jp", "ja")),
            ("uk", ("uk", "ukr"), ("uk", "ukr")),
            ("pt-BR", ("pt-BR", "br", "pt_br"), ("pt-BR", "br")),
            ("zh", ("zh",), ("zh", "cn")),
        ):
            for alias in aliases:
                with self.subTest(alias=alias):
                    self.assertEqual(code, lang_registry.canonical_language(alias))
                    self.assertEqual(suffixes, snapshot_language_suffixes(alias))
                    row = {f"Text_{suffix}": suffix for suffix in suffixes}
                    self.assertEqual(suffixes[0], localized_cell(row, "Text", alias))
                    row[f"Text_{suffixes[0]}"] = " \t "
                    self.assertEqual(suffixes[1], localized_cell(row, "Text", alias))

    def test_empty_or_unknown_language_never_invents_english(self) -> None:
        for lang in (None, "", " ", "unregistered"):
            self.assertEqual("", localized_cell({"Text_en": "English"}, "Text", lang))
        self.assertEqual(("custom",), snapshot_language_suffixes(" CUSTOM "))
        # cn is a historical column suffix, not a registered language alias.
        self.assertIsNone(lang_registry.canonical_language("cn"))
        self.assertEqual(("cn",), snapshot_language_suffixes("cn"))
        self.assertEqual("", localized_cell({"Text_zh": "中文"}, "Text", "cn"))

    def test_missing_empty_and_whitespace_have_explicit_fallback_semantics(self) -> None:
        for primary in ({}, {"Text_fr": None}, {"Text_fr": ""}, {"Text_fr": " \n "}):
            row = {**primary, "Text_source": " source ", "Text_en": " English "}
            self.assertEqual("", localized_cell(row, "Text", "fr"))
            self.assertEqual("source", localized_cell(
                row, "Text", "fr", fallback_columns=("Text_source", "Text_en")))
            self.assertEqual("English", localized_cell(
                row, "Text", "fr", fallback_columns=("Text_en", "Text_source")))
        row = {"Text_fr": " \n ", "Text_en": "English"}
        self.assertEqual(" \n ", first_text(
            row, ("Text_fr",), fallback_columns=("Text_en",), strip=False))

    def test_column_presence_does_not_advance_for_empty_cells(self) -> None:
        row = {"text_ja": "", "text_jp": "Japanese", "text_en": "English"}
        self.assertEqual("text_ja", first_existing_column(
            row, ("text_ja", "text_jp"), fallback_columns=("text_en",)))
        del row["text_ja"]
        self.assertEqual("text_jp", first_existing_column(
            row, ("text_ja", "text_jp"), fallback_columns=("text_en",)))
        self.assertEqual("text_ja", first_existing_column((), ("text_ja",)))
        self.assertEqual("missing", first_existing_column((), (), default="missing"))
        with self.assertRaisesRegex(ValueError, "requires candidates"):
            first_existing_column((), ())

    def test_table_columns_do_not_expand_global_alias_policy(self) -> None:
        self.assertEqual(("icon_jp",), table_localized_columns("lcd_icons", "icon", "ja"))
        self.assertEqual(("icon_desc_ukr",), table_localized_columns("lcd_icons", "icon_desc", "uk"))
        self.assertEqual(("Text_ja",), table_localized_columns("spec_footnotes", "Text", "jp"))
        self.assertEqual(("icon_desc_pt-BR", "icon_desc_pt-br", "icon_desc_pt_BR",
                          "icon_desc_pt_br", "icon_desc_br"),
                         table_localized_columns("lcd_icons", "icon_desc", "br"))
        self.assertEqual((), table_localized_columns("unknown_table", "Text", "ja"))

    def test_input_alias_order_and_case_variants_are_opt_in(self) -> None:
        self.assertEqual(("Text_ja", "text_ja", "Text_jp", "text_jp"), localized_columns(
            ("Text", "text"), lang_registry.language_alias_candidates("ja")))
        self.assertEqual(("Value_jp", "Value_JP", "Value_ja", "Value_JA"), localized_columns(
            ("Value",), lang_registry.language_alias_candidates("jp"), uppercase=True))


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
