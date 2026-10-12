from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "setup_dev_env.sh"


@unittest.skipUnless(shutil.which("bash") and os.name != "nt", "bash script")
class SetupDevEnvScriptTest(unittest.TestCase):
    """Guard rails that fire before any venv is created or package installed."""

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(SCRIPT), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )

    def test_rejects_an_interpreter_that_is_not_the_pinned_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "python"
            fake.write_text("#!/bin/sh\necho 2.7\n", encoding="utf-8")
            fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
            venv = Path(tmp) / "venv"
            proc = self._run("--python", str(fake), "--venv", str(venv))
            self.assertEqual(proc.returncode, 2, proc.stderr)
            self.assertIn("is Python 2.7, but the repo pins", proc.stderr)
            self.assertFalse(venv.exists())

    def test_unknown_argument_is_a_usage_error(self) -> None:
        proc = self._run("--bogus")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("unknown argument: --bogus", proc.stderr)

    def test_help_prints_usage_without_side_effects(self) -> None:
        proc = self._run("--help")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Usage: scripts/setup_dev_env.sh", proc.stdout)


if __name__ == "__main__":
    unittest.main()
