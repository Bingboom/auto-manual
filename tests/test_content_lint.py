#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for tools/content_lint.py — each check flags a planted issue and
passes on clean input."""
from __future__ import annotations

import csv
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
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

    def test_main_json_output_is_machine_readable(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _status_words(root)
            _write(root, "Spec_Notes.csv", ["Text_it"],
                   [{"Text_it": "Blinking while charging."}])
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["--data-root", str(root), "--json", "--run-id", "run-1"])

            self.assertEqual(exit_code, 1)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["schema_version"], "content-qc-report/v1")
            self.assertEqual(payload["run_id"], "run-1")
            self.assertEqual(payload["result"], "FAIL")
            self.assertEqual(payload["summary"]["fail"], 1)
            self.assertEqual(payload["summary"]["rules"]["english_residue"], 1)
            finding = payload["findings"][0]
            self.assertEqual(finding["schema_version"], "content-qc-finding/v1")
            self.assertEqual(finding["run_id"], "run-1")
            self.assertEqual(finding["rule"], "english_residue")
            self.assertEqual(finding["severity"], "FAIL")
            self.assertEqual(finding["table"], "Spec_Notes")
            self.assertEqual(finding["file"], "Spec_Notes.csv")
            self.assertIsNone(finding["source_ref"])
            self.assertIsNone(finding["record_id"])
            self.assertEqual(finding["resolution_status"], "snapshot_only")
            self.assertEqual(finding["lang"], "it")
            self.assertEqual(finding["field"], "Text_it")
            self.assertEqual(len(finding["finding_hash"]), 64)

    def test_main_writes_local_report_files(self) -> None:
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as rd:
            root = Path(td)
            report_dir = Path(rd)
            _status_words(root)
            _write(root, "Spec_Notes.csv", ["Text_it"],
                   [{"Text_it": "Blinking while charging."}])
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main([
                    "--data-root",
                    str(root),
                    "--json",
                    "--run-id",
                    "run-1",
                    "--report-dir",
                    str(report_dir),
                ])

            self.assertEqual(exit_code, 1)
            payload = json.loads(stdout.getvalue())
            findings_path = report_dir / "findings.json"
            markdown_path = report_dir / "report.md"
            self.assertTrue(findings_path.exists())
            self.assertTrue(markdown_path.exists())
            self.assertEqual(json.loads(findings_path.read_text(encoding="utf-8")), payload)
            self.assertEqual(payload["metadata"]["target"], "snapshot")
            self.assertIn("started_at", payload["metadata"])
            self.assertEqual(payload["summary"]["unresolved_record_count"], 1)
            markdown = markdown_path.read_text(encoding="utf-8")
            self.assertIn("# Content QC Report", markdown)
            self.assertIn("`english_residue`", markdown)
            self.assertIn("Unresolved records: `1`", markdown)

    def test_main_text_output_remains_default(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _status_words(root)
            _write(root, "lcd_icons_blocks.csv", ["icon_en", "icon_desc_fr"],
                   [{"icon_en": "Wi-Fi", "icon_desc_fr": "Allumé : connecté."}])
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["--data-root", str(root)])

            self.assertEqual(exit_code, 0)
            text = stdout.getvalue()
            self.assertIn("content-lint  (data-root:", text)
            self.assertIn("[status-word consistency]", text)
            self.assertIn("RESULT: OK", text)
            with self.assertRaises(json.JSONDecodeError):
                json.loads(text)


if __name__ == "__main__":
    unittest.main()
