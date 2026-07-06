#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""End-to-end CLI smoke for tools/export_idml.py (componentization P0).

Pins the CLI contract the componentization must not change: exit codes, the
stdout summary line, and the --check validator on a freshly built package.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_FIXTURE = ROOT / "tests" / "fixtures" / "phase2"
BUNDLE_FIXTURE = ROOT / "tests" / "fixtures" / "idml_bundle"


def _run(*argv: str) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(ROOT / "tools" / "export_idml.py"), *argv]
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)


class ExportIdmlCliSmokeTests(unittest.TestCase):
    def test_export_then_check_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "smoke.idml"
            build = _run(
                "--model", "JE-1000F", "--region", "US", "--lang", "en",
                "--data-root", str(DATA_FIXTURE),
                "--bundle-root", str(BUNDLE_FIXTURE),
                "--out", str(out),
            )
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            self.assertIn("[export-idml] OK:", build.stdout)
            self.assertIn("stories=", build.stdout)
            self.assertIn("skipped raw blocks=0", build.stdout)
            self.assertTrue(out.is_file())

            check = _run("--check", str(out))
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
            self.assertIn("[idml-check] OK", check.stdout)

    def test_adjacent_prose_pages_share_one_flow_story(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td) / "bundle"
            page_dir = bundle / "page"
            page_dir.mkdir(parents=True)
            (bundle / "index.rst").write_text(
                "\n".join([
                    ".. include:: page/00_alpha.rst",
                    ".. include:: page/01_beta.rst",
                ]),
                encoding="utf-8",
            )
            for stem, title in (("00_alpha", "ALPHA"), ("01_beta", "BETA")):
                (page_dir / f"{stem}.rst").write_text(
                    "\n".join([
                        ".. raw:: latex",
                        "",
                        "   \\HBApplyLang{en}",
                        "",
                        ".. only:: latex",
                        "",
                        "   .. raw:: latex",
                        "",
                        f"      \\section{{{title}}}",
                        "",
                        f"   Short {title.lower()} copy.",
                        "",
                    ]),
                    encoding="utf-8",
                )

            out = Path(td) / "flow.idml"
            build = _run(
                "--model", "JE-1000F", "--region", "US", "--lang", "en",
                "--data-root", str(DATA_FIXTURE),
                "--bundle-root", str(bundle),
                "--out", str(out),
            )
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)

            with zipfile.ZipFile(out) as zf:
                names = zf.namelist()
                flow = "Stories/Story_st_flow_00_alpha_01_beta.xml"
                self.assertIn(flow, names)
                self.assertNotIn("Stories/Story_st_00_alpha.xml", names)
                self.assertNotIn("Stories/Story_st_01_beta.xml", names)
                story = zf.read(flow).decode("utf-8")
                self.assertIn("ALPHA", story)
                self.assertIn("BETA", story)
                spread = zf.read("Spreads/Spread_sp_0.xml").decode("utf-8")
                self.assertIn('ParentStory="st_flow_00_alpha_01_beta"', spread)

    def test_real_troubleshooting_page_continues_prose_flow(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td) / "bundle"
            page_dir = bundle / "page"
            page_dir.mkdir(parents=True)
            (bundle / "index.rst").write_text(
                "\n".join([
                    ".. include:: page/09_storage.rst",
                    ".. include:: page/troubleshooting_en.rst",
                ]),
                encoding="utf-8",
            )
            (page_dir / "09_storage.rst").write_text(
                "\n".join([
                    "STORAGE",
                    "=======",
                    "",
                    "Store the product in a dry, clean place.",
                    "",
                ]),
                encoding="utf-8",
            )
            (page_dir / "troubleshooting_en.rst").write_text(
                "\n".join([
                    "TROUBLESHOOTING",
                    "===============",
                    "",
                    ".. list-table::",
                    "   :header-rows: 1",
                    "",
                    "   * - Error Code",
                    "     - Corrective Measures",
                    "   * - F0",
                    "     - Restart the product.",
                    "",
                ]),
                encoding="utf-8",
            )

            out = Path(td) / "flow.idml"
            build = _run(
                "--model", "JE-1000F", "--region", "US", "--lang", "en",
                "--data-root", str(DATA_FIXTURE),
                "--bundle-root", str(bundle),
                "--out", str(out),
            )
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)

            with zipfile.ZipFile(out) as zf:
                names = zf.namelist()
                flow = "Stories/Story_st_flow_09_storage_troubleshooting_en.xml"
                self.assertIn(flow, names)
                self.assertNotIn("Stories/Story_st_trouble.xml", names)
                story = zf.read(flow).decode("utf-8")
                self.assertIn("STORAGE", story)
                self.assertIn("TROUBLESHOOTING", story)
                self.assertIn("Restart the product.", story)

    def test_missing_spec_rows_fail_loudly(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "never.idml"
            proc = _run(
                "--model", "NO-SUCH-MODEL", "--region", "ZZ",
                "--data-root", str(DATA_FIXTURE), "--out", str(out),
            )
            self.assertEqual(proc.returncode, 1)
            self.assertIn("no specifications rows", proc.stdout)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
