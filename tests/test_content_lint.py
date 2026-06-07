#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for tools/content_lint.py — each check flags a planted issue and
passes on clean input."""
from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.content_lint import (
    check_english_residue,
    check_slot_key_collision,
    check_spec_overview_drift,
    check_status_word_consistency,
    check_tm_duplicate,
    main,
)

LANGS = ("fr", "es", "de", "it", "uk")


def _write(root: Path, name: str, header: list[str], rows: list[dict]) -> None:
    with (root / name).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _status_words(root: Path, *, fr_on: str = "Allumé") -> None:
    _write(
        root,
        "Status_Words.csv",
        ["en", "fr", "es", "de", "it", "uk", "是否为 status word"],
        [
            {"en": "On", "fr": fr_on, "es": "Encendido", "de": "Ein", "it": "Acceso", "uk": "Увімкнено", "是否为 status word": "Y"},
            {"en": "Off", "fr": "Éteint", "es": "Apagado", "de": "Aus", "it": "Spento", "uk": "Вимкнено", "是否为 status word": "Y"},
        ],
    )


class ContentLintTest(unittest.TestCase):
    def test_status_word_consistency_flags_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _status_words(root, fr_on="Activé")  # table says Activé...
            _write(root, "lcd_icons_blocks.csv", ["icon_en", "icon_desc_fr"],
                   [{"icon_en": "Wi-Fi", "icon_desc_fr": "Allumé : connecté."}])  # ...content says Allumé
            findings = check_status_word_consistency(root, LANGS)
            self.assertTrue(any(f["prefix"] == "Allumé" for f in findings))

    def test_status_word_consistency_passes_when_canonical(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _status_words(root, fr_on="Allumé")
            _write(root, "lcd_icons_blocks.csv", ["icon_en", "icon_desc_fr"],
                   [{"icon_en": "Wi-Fi", "icon_desc_fr": "Allumé : connecté."}])
            self.assertEqual(check_status_word_consistency(root, LANGS), [])

    def test_status_word_consistency_ignores_non_prefix_sentences(self) -> None:
        # A descriptive sentence with no leading "word:" must not be flagged.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _status_words(root)
            _write(root, "lcd_icons_blocks.csv", ["icon_en", "icon_desc_it"],
                   [{"icon_en": "High Temp", "icon_desc_it": "È stata attivata la protezione."}])
            self.assertEqual(check_status_word_consistency(root, LANGS), [])

    def test_english_residue_flags_italian(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write(root, "lcd_icons_blocks.csv", ["icon_en", "icon_desc_it"],
                   [{"icon_en": "TOU", "icon_desc_it": "On: la modalità è abilitata."}])
            findings = check_english_residue(root, LANGS)
            self.assertTrue(any(f["lang"] == "it" and f["token"] == "On:" for f in findings))

    def test_slot_key_collision_flags_duplicate_key(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write(root, "Spec_Master.csv", ["spec_row_key", "document_key", "Row_key"],
                   [{"spec_row_key": "k__usb_c__main", "document_key": "JE-2000F_EU", "Row_key": "usb_c"},
                    {"spec_row_key": "k__usb_c__main", "document_key": "JE-2000F_EU", "Row_key": "usb_c"}])
            findings = check_slot_key_collision(root)
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0]["count"], 2)

    def test_spec_overview_drift_flags_divergent_value(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write(root, "Spec_Master.csv",
                   ["document_key", "Row_key", "Page", "Value_source"],
                   [{"document_key": "D", "Row_key": "ac_output", "Page": "specifications", "Value_source": "2200 W total"},
                    {"document_key": "D", "Row_key": "ac_output", "Page": "Product overview", "Value_source": "2200 W"}])
            findings = check_spec_overview_drift(root, LANGS)
            self.assertTrue(any(f["row_key"] == "ac_output" and f["lang"] == "en" for f in findings))

    def test_spec_overview_drift_passes_when_value_shared(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write(root, "Spec_Master.csv",
                   ["document_key", "Row_key", "Page", "Value_source"],
                   [{"document_key": "D", "Row_key": "ac_input", "Page": "specifications", "Value_source": "220 V"},
                    # overview carries the same value plus a label callout — not drift
                    {"document_key": "D", "Row_key": "ac_input", "Page": "Product overview", "Value_source": "220 V"},
                    {"document_key": "D", "Row_key": "ac_input", "Page": "Product overview", "Value_source": "AC Input"}])
            self.assertEqual(check_spec_overview_drift(root, LANGS), [])

    def test_tm_duplicate_flags_repeated_en(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write(root, "Status_Words.csv", ["en", "是否为 status word"],
                   [{"en": "On", "是否为 status word": "Y"}, {"en": "On", "是否为 status word": "Y"}])
            findings = check_tm_duplicate(root)
            self.assertEqual(findings, [{"en": "On", "count": 2}])

    def test_main_exit_zero_on_clean_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _status_words(root)
            _write(root, "lcd_icons_blocks.csv", ["icon_en", "icon_desc_fr"],
                   [{"icon_en": "Wi-Fi", "icon_desc_fr": "Allumé : connecté."}])
            _write(root, "Spec_Master.csv", ["spec_row_key", "document_key", "Row_key", "Page", "Value_source"],
                   [{"spec_row_key": "k1", "document_key": "D", "Row_key": "x", "Page": "specifications", "Value_source": "v"}])
            self.assertEqual(main(["--data-root", str(root)]), 0)

    def test_main_exit_one_on_residue(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _status_words(root)
            _write(root, "lcd_icons_blocks.csv", ["icon_en", "icon_desc_it"],
                   [{"icon_en": "TOU", "icon_desc_it": "On: abilitata."}])
            self.assertEqual(main(["--data-root", str(root)]), 1)


if __name__ == "__main__":
    unittest.main()
