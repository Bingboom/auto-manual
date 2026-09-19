"""Wrapper so the Illustrator importer's regression checks run under unittest.

The importer is ExtendScript, exercised through a Node-hosted mock of
Illustrator's text DOM. Node is not part of this repo's required toolchain, so
the test skips when it is unavailable rather than failing the suite.
"""
from __future__ import annotations

import shutil
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / ".agents" / "skills" / "illustrator-text-roundtrip" / "scripts"


def _load_verifier():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "illustrator_verify_importer", SCRIPTS / "verify_importer.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class IllustratorTextRoundTripTest(unittest.TestCase):
    def test_scripts_are_present(self) -> None:
        for name in (
            "Illustrator_Text_Extractor.jsx",
            "Illustrator_Text_Importer.jsx",
            "mock_illustrator.js",
            "verify_importer.py",
        ):
            self.assertTrue((SCRIPTS / name).is_file(), f"missing {name}")

    def test_importer_regression_checks(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not on PATH; cannot run the ExtendScript harness")

        results = _load_verifier().run_all(node)
        self.assertTrue(results, "the verifier reported no checks")
        failures = [
            f"{name}: {detail}" for name, ok, detail in results if not ok
        ]
        self.assertEqual(failures, [], "\n".join(failures))


if __name__ == "__main__":
    unittest.main()
