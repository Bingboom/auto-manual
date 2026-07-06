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
