from __future__ import annotations

import re
import unittest

from tools import lang_registry
from tools import localized_copy, signal_words
from tools.manual_copy_source import (
    LOCALIZED_COPY_COLUMNS,
    LOCALIZED_COPY_TEXT_COLUMNS,
    MANUAL_COPY_TAG_FIELD,
    SPEC_TITLE_COLUMNS,
    SPEC_TITLE_TEXT_COLUMNS,
    STATUS_WORD_COLUMNS,
    STATUS_WORD_MARKER_FIELD,
    TM_LANGUAGE_FIELDS,
    TRANSLATION_MEMORY_COLUMNS,
)
from tools.sync_data_models import TABLE_SCHEMAS


class LanguageRegistryTest(unittest.TestCase):
    def test_registry_has_unique_codes_aliases_and_complete_metadata(self) -> None:
        specs = lang_registry.LANGUAGE_REGISTRY
        codes = [spec.code for spec in specs]
        aliases = [alias.casefold() for spec in specs for alias in spec.aliases]

        self.assertEqual(len(codes), len(set(codes)))
        self.assertEqual(len(aliases), len(set(aliases)))
        self.assertEqual(set(codes), set(lang_registry.LANGUAGE_BY_CODE))
        self.assertEqual(set(aliases), set(lang_registry.LANGUAGE_BY_ALIAS))
        self.assertEqual(
            set(lang_registry.CORE_TABLE_NAMES),
            {table_name for spec in specs for table_name, _ in spec.table_columns},
        )

        for spec in specs:
            with self.subTest(language=spec.code):
                self.assertTrue(spec.display_name)
                self.assertTrue(spec.template_directory)
                self.assertIn(spec.code, spec.aliases)
                self.assertTrue(spec.column_suffixes)
                self.assertTrue(spec.tm_column)
                self.assertTrue(spec.localized_copy_column)
                self.assertTrue(spec.status_word_column)
                self.assertIn(spec.separator, (": ", " : ", "："))
                self.assertIs(lang_registry.language_spec(spec.code), spec)
                for table_name, columns in spec.table_columns:
                    self.assertIn(table_name, lang_registry.CORE_TABLE_NAMES)
                    self.assertTrue(columns)
                    self.assertEqual(len(columns), len(set(columns)))

    def test_table_schema_language_columns_match_registry(self) -> None:
        language_column_patterns = {
            "spec_master": re.compile(r"^(?:Row_label|Param|Value)_(?!source$|footnote_refs$).+$"),
            "spec_footnotes": re.compile(r"^Text_.+$"),
            "spec_notes": re.compile(r"^Text_.+$"),
            "symbols_blocks": re.compile(r"^(?:label|aliases|text)_.+$"),
            "lcd_icons": re.compile(r"^(?:icon|icon_desc)_.+$"),
            "troubleshooting": re.compile(r"^corrective_measures_.+$"),
        }

        for table_name in lang_registry.CORE_TABLE_NAMES:
            with self.subTest(table=table_name):
                actual = tuple(
                    column
                    for column in TABLE_SCHEMAS[table_name].columns
                    if language_column_patterns[table_name].match(column)
                )
                expected = lang_registry.table_language_columns(table_name)
                self.assertEqual(set(actual), set(expected))
                self.assertEqual(len(actual), len(expected))
                for spec in lang_registry.LANGUAGE_REGISTRY:
                    for column in spec.columns_for_table(table_name):
                        self.assertIn(column, TABLE_SCHEMAS[table_name].columns)

    def test_manual_copy_source_language_surfaces_match_registry(self) -> None:
        specs = lang_registry.LANGUAGE_REGISTRY
        expected_tm = {
            alias.casefold(): spec.tm_column
            for spec in specs
            for alias in spec.aliases
        }
        expected_localized = {
            spec.localized_copy_column: spec.tm_column
            for spec in specs
        }
        expected_status = tuple(spec.status_word_column for spec in specs)
        expected_titles = tuple(
            spec.spec_title_column
            for spec in specs
            if spec.spec_title_column is not None
        )
        expected_title_map = {
            spec.spec_title_column: spec.tm_column
            for spec in specs
            if spec.spec_title_column is not None
        }

        self.assertEqual(TM_LANGUAGE_FIELDS, expected_tm)
        self.assertEqual(LOCALIZED_COPY_TEXT_COLUMNS, expected_localized)
        self.assertEqual(
            LOCALIZED_COPY_COLUMNS,
            (
                "copy_key",
                "page_id",
                "copy_type",
                "Region",
                "Model",
                "Source_lang",
                "Is_Latest",
                "Version",
                "text_en",
                "text_zh",
                "text_ja",
                "text_fr",
                "text_es",
                "text_pt-BR",
                "text_de",
                "text_it",
                "text_uk",
                "text_ko",
                "notes",
            ),
        )
        self.assertEqual(
            {column for column in LOCALIZED_COPY_COLUMNS if column.startswith("text_")},
            set(expected_localized),
        )
        self.assertEqual(STATUS_WORD_COLUMNS, (*expected_status, STATUS_WORD_MARKER_FIELD))
        self.assertEqual(
            TRANSLATION_MEMORY_COLUMNS,
            (*expected_status, MANUAL_COPY_TAG_FIELD, STATUS_WORD_MARKER_FIELD),
        )
        self.assertEqual(
            SPEC_TITLE_COLUMNS,
            ("title_en", "section_order", *expected_titles[1:]),
        )
        self.assertEqual(SPEC_TITLE_TEXT_COLUMNS, expected_title_map)

    def test_localized_copy_and_signal_word_alias_surfaces_match_registry(self) -> None:
        expected_text_columns = {
            alias.casefold(): spec.localized_copy_column
            for spec in lang_registry.LANGUAGE_REGISTRY
            for alias in spec.aliases
        }
        self.assertEqual(localized_copy._LANG_TEXT_COLUMNS, expected_text_columns)
        self.assertEqual(
            signal_words._SUPPORTED_LANGS,
            set(expected_text_columns),
        )

        for spec in lang_registry.LANGUAGE_REGISTRY:
            for alias in spec.aliases:
                with self.subTest(language=spec.code, alias=alias):
                    columns = signal_words._label_columns(alias)
                    suffixes = {
                        column.rsplit("_", 1)[-1]
                        for column in columns
                        if "_" in column
                    }
                    self.assertTrue(
                        set(spec.column_suffixes).intersection(suffixes),
                        msg=f"signal_words has no label columns for {alias!r}",
                    )

    def test_alias_resolution_is_explicit_and_non_mutating(self) -> None:
        for spec in lang_registry.LANGUAGE_REGISTRY:
            for alias in spec.aliases:
                with self.subTest(language=spec.code, alias=alias):
                    self.assertEqual(lang_registry.canonical_language(alias), spec.code)
                    self.assertIs(lang_registry.language_spec(alias), spec)
        self.assertIsNone(lang_registry.canonical_language("xx"))
        self.assertIsNone(lang_registry.language_spec("xx"))


if __name__ == "__main__":
    unittest.main()
