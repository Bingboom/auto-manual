from __future__ import annotations

import argparse
import unittest
from pathlib import Path

from tools.indesign_finalize import (
    DEFAULT_OUTPUT_CONDITION,
    DEFAULT_OUTPUT_INTENT,
    DEFAULT_PDF_PRESET,
    DEFAULT_PDFX,
    JSX,
    _job,
    _parse_pdf_export_compliance,
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


if __name__ == "__main__":
    unittest.main()
