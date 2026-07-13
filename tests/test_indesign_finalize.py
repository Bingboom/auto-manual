from __future__ import annotations

import argparse
import unittest
from pathlib import Path

from tools.indesign_finalize import JSX, _job


class InDesignFinalizeTests(unittest.TestCase):
    def test_job_paths_are_absolute_and_script_checks_required_gates(self) -> None:
        job = _job(argparse.Namespace(
            idml="input.idml", indd="output.indd", pdf="output.pdf",
            report="report.json", pdf_preset="[High Quality Print]"))
        self.assertTrue(all(Path(job[key]).is_absolute() for key in (
            "input_idml", "output_indd", "output_pdf", "report_json")))
        jsx = JSX.read_text(encoding="utf-8")
        self.assertIn("story.overflows", jsx)
        self.assertIn("FontStatus.INSTALLED", jsx)
        self.assertIn("LinkStatus.NORMAL", jsx)
        self.assertIn("hb:page=", jsx)
        self.assertIn("doc.exportFile", jsx)
        self.assertIn("backgroundTaskPreferences.enableBackgroundTask = false", jsx)

    def test_runner_allows_synchronous_pdf_export_to_finish(self) -> None:
        runner = (JSX.parent.parent / "indesign_finalize.py").read_text(encoding="utf-8")

        self.assertIn("with timeout of 600 seconds", runner)
        self.assertIn("timeout=660", runner)


if __name__ == "__main__":
    unittest.main()
