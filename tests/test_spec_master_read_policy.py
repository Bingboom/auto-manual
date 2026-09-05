"""Frozen Spec_Master read policy, characterized before the primitive migration."""
from __future__ import annotations

from itertools import permutations
from pathlib import Path
import subprocess
import sys
import unittest

from tools.utils.spec_master import (
    resolve_product_name_from_rows,
    resolve_template_substitutions_from_rows,
    source_language_for_row,
)
from tools.utils.spec_master_row_helpers import _pick_lang_value, _set_source_value

ROOT = Path(__file__).resolve().parents[1]


def product_row(**fields: str) -> dict[str, str]:
    return {"Model": "DEMO", "Region": "US", "Page": "specifications",
            "Row_key": "product_name", "Is_Latest": "TRUE", **fields}


class TestSpecMasterReadPolicy(unittest.TestCase):
    def assert_product(self, row: dict[str, str], lang: str, expected: str) -> None:
        match = resolve_product_name_from_rows([row], model="DEMO", region="US", lang=lang)
        self.assertEqual(expected, match.product_name if match else "")
        substitutions = resolve_template_substitutions_from_rows(
            [row], model="DEMO", region="US", lang=lang)
        self.assertEqual(expected, substitutions.get("PRODUCT_NAME", ""))

    def test_source_language_policy_bypasses_target_columns_even_when_source_empty(self) -> None:
        for source, target in (("en", "EN"), ("ja", "ja"), ("JP", "JA"),
                               ("fr", "FR"), ("br", "PT-BR"), ("pt_br", "br"),
                               ("ja", "en"), ("fr", "en"), ("", "en")):
            for base in ("Value", "Param", "Row_label"):
                with self.subTest(source=source, target=target, base=base):
                    row = product_row(Source_lang=source, Spec_Value="last")
                    row.update({f"{base}_{target}": "target", f"{base}_source": " source ",
                                f"{base.lower()}_source": "lower source", base: "bare"})
                    self.assertEqual("source", _pick_lang_value(row, base, target))
                    row[f"{base}_source"] = " \t "
                    self.assertEqual("lower source", _pick_lang_value(row, base, target))
                    row[f"{base.lower()}_source"] = ""
                    self.assertEqual("bare", _pick_lang_value(row, base, target))
                    row[base] = ""
                    self.assertEqual("last", _pick_lang_value(row, base, target))
                    if base == "Value":
                        self.assert_product(row, target, "last")
                    row["Spec_Value"] = ""
                    self.assertEqual("", _pick_lang_value(row, base, target))

    def test_target_candidate_order_and_each_fallback_through_public_lookups(self) -> None:
        # Removing one competing column at a time proves the entire order.
        for lang, suffixes in (
            (" Fr ", ("Fr", "fr", "FR")),
            ("PT-BR", ("PT-BR", "pt-br", "PT_BR", "pt_br", "br", "pt-BR", "pt_BR")),
            ("pt_br", ("pt_br", "PT_BR", "br", "pt-BR", "pt-br", "pt_BR")),
            ("br", ("br", "BR", "pt-BR", "pt-br", "pt_BR", "pt_br")),
            ("pt-BR", ("pt-BR", "pt-br", "PT-BR", "pt_BR", "pt_br", "br")),
            ("X-Ab", ("X-Ab", "x-ab", "X-AB", "X_Ab", "x_ab")),
        ):
            keys = [*(f"Value_{suffix}" for suffix in suffixes),
                    "Value_source", "value_source", "Value", "Spec_Value"]
            row = product_row(Source_lang="en", **{key: f" {key} " for key in keys})
            for key in keys:
                with self.subTest(lang=lang, key=key):
                    self.assert_product(row, lang, key)
                    del row[key]
            self.assert_product(row, lang, "")

    def test_missing_empty_and_whitespace_targets_advance_to_source_then_bare_then_spec(self) -> None:
        for fields in ({}, {"Value_fr": ""}, {"Value_fr": " \n "}):
            row = product_row(Source_lang="en", Value_source="source", Value="bare",
                              Spec_Value="last", Value_en="English", **fields)
            self.assert_product(row, "fr", "source")
            del row["Value_source"]
            self.assert_product(row, "fr", "bare")
            del row["Value"]
            self.assert_product(row, "fr", "last")
            del row["Spec_Value"]
            self.assert_product(row, "fr", "")

    def test_no_global_alias_expansion_or_silent_english_fallback(self) -> None:
        for lang, excluded in (("ja", "jp"), ("jp", "ja"), ("uk", "ukr"),
                               ("ukr", "uk"), ("zh", "cn"), ("cn", "zh"),
                               ("br", "PT-BR"), ("pt", "br"),
                               ("", "en"), (" ", "en"), ("xx", "en"),
                               ("Straße", "strasse")):
            row = product_row(Source_lang="en", **{f"Value_{excluded}": "must not match"})
            with self.subTest(lang=lang, excluded=excluded):
                self.assert_product(row, lang, "")
                row["Value_source"] = "source"
                self.assert_product(row, lang, "source")

    def test_source_language_normalization_stays_distinct_from_requested_aliases(self) -> None:
        for source, normalized in (("English", "en"), ("日语", "ja"), ("JP", "ja"),
                                   ("中文", "zh"), ("fr", "fr"), ("PT_BR", "pt-br"),
                                   ("de", ""), ("ko", ""), ("unknown", ""), ("", "")):
            with self.subTest(source=source):
                self.assertEqual(normalized, source_language_for_row({"Source_lang": source}))
        # Source JP normalizes to ja; a requested jp still searches only jp.
        self.assert_product(product_row(Source_lang="JP", Value_source="source", Value_jp="target"),
                            "jp", "target")
        self.assert_product(product_row(Source_lang="de", Value_source="source", Value_de="target"),
                            "de", "target")

    def test_nonshared_bases_do_not_gain_source_policy(self) -> None:
        for base in ("line_text", "value", "Custom"):
            row = {"Source_lang": "ja", f"{base}_ja": "target", f"{base}_source": "source",
                   base: "bare", "Spec_Value": "last"}
            self.assertEqual("target", _pick_lang_value(row, base, "ja"))
            del row[f"{base}_ja"]
            self.assertEqual("bare", _pick_lang_value(row, base, "ja"))
            del row[base]
            self.assertEqual("last", _pick_lang_value(row, base, "ja"))

    def test_source_writer_selects_present_header_even_when_cell_is_blank(self) -> None:
        for base in ("Value", "Param", "Row_label", "Custom"):
            for value in ("", " \t ", "old"):
                row = {f"{base}_source": value, f"{base.lower()}_source": "lower"}
                self.assertEqual(f"{base}_source", _set_source_value(row, base, "new"))
                self.assertEqual("lower", row[f"{base.lower()}_source"])
            row = {f"{base.lower()}_source": ""}
            self.assertEqual(f"{base.lower()}_source", _set_source_value(row, base, "new"))
            self.assertEqual(f"{base}_source", _set_source_value({}, base, "new"))

    def test_page_label_translation_notes_and_source_equivalence_keep_value(self) -> None:
        for label, expected in (("Cible", "Cible"), ("line\nbreak", "Value cible"),
                                ("line\rbreak", "Value cible"), ("说明", "Value cible"),
                                ("占位符", "Value cible"), ("PLACEHOLDER", "Value cible"),
                                ("Source label", "Value cible"), ("Source value", "Value cible"),
                                (" \t ", "Value cible")):
            row = product_row(Source_lang="en", Row_key="main_power_button", Slot_key="label",
                              Row_label_source="Source label", Value_source="Source value",
                              Row_label_fr=label, Value_fr="Value cible")
            substitutions = resolve_template_substitutions_from_rows(
                [row], model="DEMO", region="US", lang="fr")
            with self.subTest(label=label):
                self.assertEqual(expected, substitutions["MAIN_POWER_BUTTON_LABEL"])

    def test_page_label_candidates_keep_narrow_aliases_and_normalized_input_order(self) -> None:
        row = product_row(Source_lang="en", Row_key="main_power_button", Slot_key="label",
                          Row_label_source="source label", Value_source="source value",
                          **{"Row_label_pt-br": "lower first", "Row_label_PT-BR": "upper second",
                             "Row_label_pt_br": "underscore third", "Row_label_br": "br fourth",
                             "Row_label_pt-BR": "mixed fifth", "Row_label_pt_BR": "mixed sixth"})
        for key in ("Row_label_pt-br", "Row_label_PT-BR", "Row_label_pt_br", "Row_label_br",
                    "Row_label_pt-BR", "Row_label_pt_BR"):
            substitutions = resolve_template_substitutions_from_rows(
                [row], model="DEMO", region="US", lang="PT-BR")
            self.assertEqual(row.pop(key), substitutions["MAIN_POWER_BUTTON_LABEL"])
        row.update(Row_label_jp="must not match", Row_label_en="must not match")
        for lang in ("ja", "uk", "br"):
            substitutions = resolve_template_substitutions_from_rows(
                [row], model="DEMO", region="US", lang=lang)
            self.assertEqual("source value", substitutions["MAIN_POWER_BUTTON_LABEL"])


class TestCsvReaderDependencies(unittest.TestCase):
    def test_compatibility_exports_share_the_same_implementation(self) -> None:
        from tools import localized_copy
        from tools.utils import csv_fields, spec_master_row_helpers

        for name in ("localized_columns", "first_text", "first_existing_column"):
            self.assertIs(getattr(csv_fields, name), getattr(localized_copy, name))
        self.assertIs(csv_fields.first_text, spec_master_row_helpers._first_non_empty)
        self.assertEqual(("Text_Straße", "Text_strasse"),
                         localized_copy.localized_columns(("Text",), ("Straße",)))
        self.assertEqual(("Text_Straße", "Text_straße"),
                         csv_fields.localized_columns(("Text",), ("Straße",), casefold=False))

    def test_low_level_import_does_not_load_business_readers_or_registry(self) -> None:
        code = """
import sys
from tools.utils.csv_fields import first_text, localized_columns
assert first_text({'Value_fr': ' texte '}, localized_columns(('Value',), ('fr',))) == 'texte'
assert not any(name.startswith(('tools.utils.spec_master', 'tools.localized_copy',
                                'tools.lang_registry', 'tools.idml')) for name in sys.modules)
"""
        result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_public_reader_import_orders_in_fresh_interpreters(self) -> None:
        modules = ("tools.utils.spec_master", "tools.localized_copy", "tools.idml.loaders", "tools.export_idml")
        # Exercise the entrypoints after importing, not just successful module loading.
        code = """
import importlib
import sys
from pathlib import Path
for name in sys.argv[1:]:
    importlib.import_module(name)
from tools import export_idml, localized_copy
from tools.idml import loaders
from tools.utils import spec_master
fixtures = Path('tests/fixtures/phase2')
match = spec_master.resolve_product_name_from_spec_master(
    fixtures / 'Spec_Master.csv', model='JE-1000F', region='US', lang='en')
assert match.product_name == 'Jackery Explorer 1000'
assert localized_copy.LocalizedCopyResolver([{'copy_key': 'probe', 'text_fr': 'Texte'}]).resolve(
    'probe', lang='fr') == 'Texte'
assert export_idml.load_spec_sections is loaders.load_spec_sections
assert loaders.load_spec_sections(fixtures, 'JE-1000F', 'JP', 'ja')[0]['rows'][2][1] == '1024Wh (20Ah/51.2V DC)'
"""
        for order in permutations(modules):
            with self.subTest(order=order):
                result = subprocess.run([sys.executable, "-c", code, *order], cwd=ROOT,
                                        text=True, capture_output=True)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
