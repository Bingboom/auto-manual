from __future__ import annotations

import unittest

from tools import build_docs, build_docs_shared, content_lint, localized_copy
from tools import lang_registry, signal_words
from tools.check_docs import _pick_spec_value
from tools.idml import loaders
from tools.idml.page_toc import _LANG_HEADERS
from tools.manual_copy_source import TM_LANGUAGE_FIELDS
from tools.process_docs import build_review_preview_render
from tools.utils import variable_resolver


RESOLVED_LONGTAIL_DRIFTS = (
    {
        "surface": "display.language_labels",
        "missing_languages": ("de", "it", "uk", "ko"),
        "reason": "display maps currently cover only the original preview languages.",
        "status": "resolved",
    },
)


def _suffix(columns: tuple[str, ...], prefix: str) -> str:
    matches = [column.removeprefix(f"{prefix}_") for column in columns if column.startswith(f"{prefix}_")]
    if not matches:
        raise AssertionError(f"expected at least one {prefix} column, got {matches!r}")
    return matches[0]


def _suffix_or(columns: tuple[str, ...], prefix: str, fallback: str) -> str:
    matches = [column.removeprefix(f"{prefix}_") for column in columns if column.startswith(f"{prefix}_")]
    return matches[0] if matches else fallback


class LanguageLongTailParityTest(unittest.TestCase):
    def test_content_lint_four_maps_match_registered_table_columns(self) -> None:
        expected_languages = tuple(spec.code for spec in lang_registry.LANGUAGE_REGISTRY)
        expected_lcd = {}
        expected_trouble = {}
        expected_text = {}
        expected_value = {}
        for code in expected_languages:
            spec = lang_registry.language_spec(code)
            self.assertIsNotNone(spec, code)
            assert spec is not None
            expected_lcd[code] = _suffix(spec.columns_for_table("lcd_icons"), "icon_desc")
            expected_trouble[code] = _suffix(
                spec.columns_for_table("troubleshooting"), "corrective_measures"
            )
            expected_text[code] = _suffix_or(
                spec.columns_for_table("spec_notes"),
                "Text",
                _suffix_or(spec.columns_for_table("spec_footnotes"), "Text", code),
            )
            expected_value[code] = _suffix_or(
                spec.columns_for_table("spec_master"), "Value", "source"
            )

        self.assertEqual(content_lint._LCD_DESC, expected_lcd)
        self.assertEqual(content_lint._TROUBLE, expected_trouble)
        self.assertEqual(content_lint._TEXT, expected_text)
        self.assertEqual(content_lint._VALUE, expected_value)
        self.assertEqual(content_lint.SUPPORTED_LANGS, expected_languages)

    def test_idml_loader_suffix_candidates_match_registry(self) -> None:
        for spec in lang_registry.LANGUAGE_REGISTRY:
            with self.subTest(language=spec.code):
                self.assertEqual(loaders._lang_suffixes(spec.code), spec.column_suffixes)

    def test_variable_resolver_alias_candidates_match_registry(self) -> None:
        expected_aliases: dict[str, tuple[str, ...]] = {}
        for spec in lang_registry.LANGUAGE_REGISTRY:
            aliases = tuple(alias.casefold() for alias in spec.aliases)
            if len(aliases) <= 1:
                continue
            for index, alias in enumerate(aliases):
                expected_aliases[alias] = aliases[index:] + aliases[:index]

        self.assertEqual(set(variable_resolver._LANG_ALIASES), set(expected_aliases))
        for alias, candidates in variable_resolver._LANG_ALIASES.items():
            with self.subTest(alias=alias):
                # Candidate order is a historical precedence detail; the
                # registry lock requires the same alias closure and the same
                # first-choice lookup without duplicating that order here.
                self.assertEqual(candidates[0], alias)
                self.assertEqual(set(candidates), set(expected_aliases[alias]))
        for spec in lang_registry.LANGUAGE_REGISTRY:
            for alias in spec.aliases:
                with self.subTest(language=spec.code, alias=alias):
                    self.assertTrue(variable_resolver._lang_candidates(alias))

    def test_check_docs_canonical_spec_value_lookup_matches_registry(self) -> None:
        for spec in lang_registry.LANGUAGE_REGISTRY:
            value_columns = tuple(
                column for column in spec.columns_for_table("spec_master") if column.startswith("Value_")
            )
            if not value_columns:
                continue
            row = {"Value_source": "SOURCE"}
            for column in value_columns:
                row[column] = f"{spec.code}-VALUE"
            with self.subTest(language=spec.code):
                self.assertEqual(_pick_spec_value(row, spec.code), f"{spec.code}-VALUE")

    def test_longtail_drift_ledger_is_explicit(self) -> None:
        registered = {spec.code for spec in lang_registry.LANGUAGE_REGISTRY}
        self.assertTrue(RESOLVED_LONGTAIL_DRIFTS)
        for entry in RESOLVED_LONGTAIL_DRIFTS:
            with self.subTest(surface=entry["surface"]):
                self.assertTrue(entry["surface"])
                self.assertTrue(entry["reason"])
                self.assertEqual(entry["status"], "resolved")
                self.assertTrue(set(entry["missing_languages"]) <= registered)

    def test_ukr_alias_in_check_docs_is_closed(self) -> None:
        row = {"Value_source": "SOURCE", "Value_uk": "UK-VALUE"}
        self.assertEqual(_pick_spec_value(row, "ukr"), "UK-VALUE")

    def test_idml_loader_has_no_visible_symbol_copy_registry(self) -> None:
        self.assertFalse(hasattr(loaders, "SYMBOL_COPY"))
        self.assertFalse(hasattr(loaders, "symbol_copy"))

    def test_idml_governed_languages_have_one_registry_source(self) -> None:
        self.assertEqual(lang_registry.governed_languages(), ("en", "fr", "es"))

    def test_longtail_display_registration_is_closed(self) -> None:
        maps = (
            build_docs.LANGUAGE_LABELS,
            build_docs_shared.LANGUAGE_LABELS,
            build_review_preview_render.LANGUAGE_LABELS,
        )
        expected_labels = lang_registry.language_display_labels()
        for language_map in maps:
            self.assertEqual(language_map, expected_labels)
        for spec in lang_registry.LANGUAGE_REGISTRY:
            with self.subTest(language=spec.code):
                self.assertIn(spec.code, _LANG_HEADERS)
                self.assertIn(spec.code, lang_registry.IDML_LANGUAGE_PACKS)

    def test_core_longtail_alias_sets_remain_closed(self) -> None:
        aliases = {
            alias.casefold()
            for spec in lang_registry.LANGUAGE_REGISTRY
            for alias in spec.aliases
        }
        self.assertEqual(set(TM_LANGUAGE_FIELDS), aliases)
        self.assertEqual(signal_words._SUPPORTED_LANGS, aliases)
        self.assertEqual(
            set(localized_copy._LANG_TEXT_COLUMNS),
            aliases,
        )


if __name__ == "__main__":
    unittest.main()
