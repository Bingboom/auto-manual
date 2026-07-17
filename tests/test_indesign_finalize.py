from __future__ import annotations

import argparse
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.test_helpers import temp_test_root

from tools.indesign_finalize import (
    DEFAULT_OUTPUT_CONDITION,
    DEFAULT_OUTPUT_INTENT,
    DEFAULT_PDF_PRESET,
    DEFAULT_PDFX,
    JSX,
    VERSION_PIN,
    _job,
    _parse_pdf_export_compliance,
    check_version_pin,
    main,
    write_version_pin,
)


class InDesignFinalizeTests(unittest.TestCase):
    def test_job_paths_are_absolute_and_script_checks_required_gates(self) -> None:
        job = _job(argparse.Namespace(
            idml="input.idml", indd="output.indd", pdf="output.pdf",
            report="report.json", pdf_preset="[High Quality Print]",
            output_intent=DEFAULT_OUTPUT_INTENT,
            output_condition=DEFAULT_OUTPUT_CONDITION,
            pdfx=DEFAULT_PDFX))
        self.assertTrue(all(Path(job[key]).is_absolute() for key in (
            "input_idml", "output_indd", "output_pdf", "report_json")))
        jsx = JSX.read_text(encoding="utf-8")
        self.assertIn("story.overflows", jsx)
        self.assertIn("FontStatus.INSTALLED", jsx)
        self.assertIn("LinkStatus.NORMAL", jsx)
        self.assertIn("hb:page=", jsx)
        self.assertIn("doc.exportFile", jsx)
        self.assertIn("backgroundTaskPreferences.enableBackgroundTask = false", jsx)
        self.assertIn("fitLcdTableShells(doc)", jsx)
        self.assertIn('indexOf(" table segment ")', jsx)
        self.assertIn("table.rows[ri].height", jsx)
        self.assertIn("fitted_lcd_table_groups", jsx)
        self.assertIn("fitComposedSymbolTableShells(doc)", jsx)
        self.assertIn('title.indexOf("Symbol icons ")', jsx)
        self.assertIn("fitted_symbol_table_shells", jsx)
        self.assertIn("app.pdfExportPresets.itemByName(job.pdf_preset)", jsx)
        self.assertIn("if (!pdfPreset.isValid)", jsx)
        self.assertIn("app.pdfExportPreferences.pageRange = PageRange.ALL_PAGES", jsx)
        self.assertIn("doc.cmykProfile = job.output_intent", jsx)
        self.assertIn(
            "doc.exportFile(ExportFormat.pdfType, File(job.output_pdf), false, pdfPreset)",
            jsx,
        )

    def test_default_pdf_preset_is_pdfx4(self) -> None:
        self.assertEqual("[PDF/X-4:2008 (Japan)]", DEFAULT_PDF_PRESET)

    def test_pdf_export_compliance_requires_pdfx_and_output_intent(self) -> None:
        result = _parse_pdf_export_compliance(
            pdfinfo_text="PDF subtype:    PDF/X-4\n",
            pdf_bytes=(
                b"/Info(Japan Color 2001 Coated) "
                b"/OutputConditionIdentifier(JC200103)"
            ),
            expected_pdfx=DEFAULT_PDFX,
            expected_output_intent=DEFAULT_OUTPUT_INTENT,
            expected_output_condition=DEFAULT_OUTPUT_CONDITION,
        )

        self.assertTrue(result["pass"])

    def test_pdf_export_compliance_rejects_wrong_output_intent(self) -> None:
        result = _parse_pdf_export_compliance(
            pdfinfo_text="PDF subtype:    PDF/X-4\n",
            pdf_bytes=b"/Info(U.S. Web Coated (SWOP) v2)",
            expected_pdfx=DEFAULT_PDFX,
            expected_output_intent=DEFAULT_OUTPUT_INTENT,
            expected_output_condition=DEFAULT_OUTPUT_CONDITION,
        )

        self.assertFalse(result["pass"])

    def test_runner_allows_synchronous_pdf_export_to_finish(self) -> None:
        runner = (JSX.parent.parent / "indesign_finalize.py").read_text(encoding="utf-8")

        self.assertIn("with timeout of 600 seconds", runner)
        self.assertIn("timeout=660", runner)


class VersionPinTests(unittest.TestCase):
    """Milestone K7: the finalize leg refuses to run on a version-drifted host."""

    PINNED = "Adobe InDesign 2026 21.0.1.6"

    def _pin(self, root, expected=PINNED) -> Path:
        pin = Path(root) / "pin.json"
        pin.write_text(json.dumps({"expected": expected}), encoding="utf-8")
        return pin

    def test_committed_pin_exists_and_matches_the_check_shape(self) -> None:
        self.assertTrue(VERSION_PIN.is_file(), "committed pin file missing")
        pin = json.loads(VERSION_PIN.read_text(encoding="utf-8"))
        self.assertRegex(pin["expected"], r"^Adobe InDesign .+ \d")
        self.assertIn("pinned_at", pin)

    def test_check_statuses(self) -> None:
        with temp_test_root() as root:
            pin = self._pin(root)
            self.assertEqual(check_version_pin(pin, self.PINNED)[0], "match")
            self.assertEqual(check_version_pin(pin, "Adobe InDesign 2026 21.0.2.1")[0], "mismatch")
            self.assertEqual(check_version_pin(pin, None)[0], "no_indesign")
            self.assertEqual(check_version_pin(Path(root) / "absent.json", self.PINNED)[0], "no_pin")

    def test_mismatch_message_names_both_versions_and_the_runbook(self) -> None:
        with temp_test_root() as root:
            _, message = check_version_pin(self._pin(root), "Adobe InDesign 2027 22.0")
            self.assertIn(self.PINNED, message)
            self.assertIn("Adobe InDesign 2027 22.0", message)
            self.assertIn("indesign_second_host_runbook", message)

    def test_write_pin_seeds_from_host_and_refuses_without_indesign(self) -> None:
        with temp_test_root() as root:
            pin = Path(root) / "pin.json"
            written = write_version_pin(pin, actual="Adobe InDesign 2026 21.0.1.6")
            self.assertEqual(written, self.PINNED)
            data = json.loads(pin.read_text(encoding="utf-8"))
            self.assertEqual(data["expected"], self.PINNED)
            with self.assertRaises(RuntimeError):
                write_version_pin(pin, actual=None)

    def test_check_host_cli_exits_zero_on_match_two_otherwise(self) -> None:
        with patch("tools.indesign_finalize.check_version_pin",
                   return_value=("match", "ok")):
            with patch("sys.argv", ["indesign_finalize.py", "--check-host"]):
                self.assertEqual(main(), 0)
        with patch("tools.indesign_finalize.check_version_pin",
                   return_value=("mismatch", "drift")):
            with patch("sys.argv", ["indesign_finalize.py", "--check-host"]):
                self.assertEqual(main(), 2)

    def test_run_refuses_on_mismatch_without_override_and_never_launches(self) -> None:
        with patch("tools.indesign_finalize.check_version_pin",
                   return_value=("mismatch", "drift")), \
             patch("tools.indesign_finalize._run_jsx") as run_jsx, \
             patch("sys.argv", ["indesign_finalize.py", "--idml", "a.idml",
                                "--indd", "a.indd", "--pdf", "a.pdf", "--report", "r.json"]):
            self.assertEqual(main(), 2)
            run_jsx.assert_not_called()


if __name__ == "__main__":
    unittest.main()
