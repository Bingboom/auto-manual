#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Localized data-column loading for the IDML exporter (componentization
leftover: --lang used to affect only the bundle path/tags while every data
page shipped the *_en columns).

Contract: localized column with per-table suffix aliases (jp/ja, uk/ukr,
pt-BR/br), falling back to the source/en column when the translation is
empty — the same philosophy as load_symbols_rows.
"""
from __future__ import annotations

import unittest
from pathlib import Path

from tools.idml.loaders import (
    load_lcd_rows,
    load_spec_annotations,
    load_spec_sections,
    load_trouble_rows,
)

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "phase2"


class LocalizedLoaderTests(unittest.TestCase):
    def test_default_lang_is_en_and_matches_previous_behavior(self) -> None:
        self.assertEqual(load_lcd_rows(FIXTURES, "JE-1000F"),
                         load_lcd_rows(FIXTURES, "JE-1000F", lang="en"))
        self.assertEqual(load_spec_sections(FIXTURES, "JE-1000F", "US"),
                         load_spec_sections(FIXTURES, "JE-1000F", "US", lang="en"))

    def test_lcd_rows_localize_to_french(self) -> None:
        en = load_lcd_rows(FIXTURES, "JE-1000F", lang="en")
        fr = load_lcd_rows(FIXTURES, "JE-1000F", lang="fr")
        self.assertEqual(len(en), len(fr))
        wifi_fr = next(r for r in fr if r["name"] == "Wi-Fi")
        self.assertIn("Allumé", wifi_fr["desc"])
        self.assertTrue(any(e["desc"] != f["desc"] for e, f in zip(en, fr)))

    def test_lcd_rows_uk_uses_ukr_suffix_alias(self) -> None:
        uk = load_lcd_rows(FIXTURES, "JE-1000F", lang="uk")
        wifi = next(r for r in uk if r["name"] == "Wi-Fi")
        self.assertIn("Увімкнено", wifi["desc"])

    def test_spec_annotations_ja_uses_ja_suffix_alias(self) -> None:
        # Spec_Footnotes use Text_ja (not Text_jp) and the JP rows carry it;
        # the jp candidate list must find it.
        ja = load_spec_annotations(FIXTURES, "JE-1000F", "JP", lang="ja")
        self.assertTrue(ja)
        self.assertTrue(any("参考値" in text for text in ja), ja)

    def test_spec_annotations_localize_to_french(self) -> None:
        fr = load_spec_annotations(FIXTURES, "JE-1000F", "US", lang="fr")
        self.assertTrue(any("Le produit" in text for text in fr), fr)

    def test_empty_translation_falls_back_to_english(self) -> None:
        # the US footnote rows have no Text_ja -> a ja request ships the en
        # text instead of a hole.
        en = load_spec_annotations(FIXTURES, "JE-1000F", "US", lang="en")
        ja = load_spec_annotations(FIXTURES, "JE-1000F", "US", lang="ja")
        self.assertEqual(en, ja)

    def test_trouble_rows_localize_to_french(self) -> None:
        fr = load_trouble_rows(FIXTURES, "JE-1000F", "US", lang="fr")
        self.assertIn(("F0", "Redémarrez le produit."), fr)

    def test_spec_sections_localize_values_with_source_fallback(self) -> None:
        en = load_spec_sections(FIXTURES, "JE-1000F", "US", lang="en")
        fr = load_spec_sections(FIXTURES, "JE-1000F", "US", lang="fr")
        self.assertEqual([s["title"] for s in en], [s["title"] for s in fr])
        en_cells = [line for s in en for _, line in s["rows"]]
        fr_cells = [line for s in fr for _, line in s["rows"]]
        self.assertEqual(len(en_cells), len(fr_cells))
        self.assertTrue(all(cell for cell in fr_cells), "no holes: fallback must fill")


if __name__ == "__main__":
    unittest.main()
