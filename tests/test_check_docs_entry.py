from __future__ import annotations

import argparse
import unittest
from pathlib import Path
from types import SimpleNamespace

from tools.check_docs_entry import run_check_entry


class CheckDocsEntryTests(unittest.TestCase):
    def test_capability_row_missing_is_printed_as_warning_without_failing(self) -> None:
        output: list[str] = []
        errors: list[str] = []
        issue = SimpleNamespace(
            code="CAPABILITY_ROW_MISSING",
            model="JE-1000F",
            region="US",
            lang=None,
            path=Path("data/capability_known_missing.csv"),
            message="missing capability row",
        )
        args = argparse.Namespace(
            config="configs/config.us.yaml",
            docs_build_dir=None,
            model="JE-1000F",
            region="US",
            lang=None,
            all_targets=False,
            data_root=None,
        )

        result = run_check_entry(
            args,
            repo_root=Path("/repo"),
            collect_check_issues=lambda **_: [issue],
            repo_relative=lambda path: str(path),
            printer=output.append,
            error_printer=errors.append,
        )

        self.assertEqual(0, result)
        self.assertTrue(any("WARNING CAPABILITY_ROW_MISSING" in line for line in output))
        self.assertIn("[check] OK", output)
        self.assertEqual([], errors)


if __name__ == "__main__":
    unittest.main()
