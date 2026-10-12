from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import check_mypy_ratchet as ratchet

OUTPUT = """\
tools/manual_ir/a.py:3: error: Function is missing a type annotation  [no-untyped-def]
tools/manual_ir/a.py:9:5: error: Function is missing a return type annotation  [no-untyped-def]
tools/manual_ir/a.py:9: note: Use "-> None" if function does not return a value
tools\\csv_pages\\b.py:12: error: Missing type parameters  [type-arg]
tools/utils/elsewhere.py:1: error: Function is missing a type annotation  [no-untyped-def]
"""


class ParseTest(unittest.TestCase):
    def test_counts_errors_inside_scoped_packages_only(self) -> None:
        counts = ratchet.parse_mypy_output(OUTPUT)
        self.assertEqual(
            (
                ratchet.FileCount("tools/csv_pages/b.py", 1, 12),
                ratchet.FileCount("tools/manual_ir/a.py", 2, 3),
            ),
            counts,
        )


class CheckRepositoryTest(unittest.TestCase):
    def _root(self, tmp: str) -> Path:
        root = Path(tmp)
        for relative in ("tools/manual_ir/a.py", "tools/csv_pages/b.py", "tools/csv_pages/c.py"):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")
        return root

    def test_grown_new_improved_and_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(tmp)
            baseline = root / "baseline.tsv"
            baseline.write_text(
                "# header\ntools/manual_ir/a.py\t1\ntools/csv_pages/c.py\t2\n", encoding="utf-8"
            )
            lines: list[str] = []
            result = ratchet.check_repository(
                root, baseline_path=baseline, printer=lines.append, mypy_output=OUTPUT
            )
            self.assertEqual(1, result.exit_code)
            self.assertIn("NEW tools/csv_pages/b.py:12", lines[0])
            self.assertIn("GREW tools/manual_ir/a.py:3 mypy errors 1 -> 2", lines[1])
            self.assertIn("IMPROVED tools/csv_pages/c.py mypy errors 2 -> 0", lines[2])

            ratchet.write_baseline(baseline, ratchet.parse_mypy_output(OUTPUT))
            clean = ratchet.check_repository(
                root, baseline_path=baseline, printer=lambda _: None, mypy_output=OUTPUT
            )
            self.assertEqual(0, clean.exit_code)

    def test_missing_mypy_is_a_setup_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(tmp)
            baseline = root / "baseline.tsv"
            ratchet.write_baseline(baseline, ())
            original = ratchet.run_mypy

            def _missing(_root: Path) -> str:
                raise RuntimeError("mypy is not installed")

            ratchet.run_mypy = _missing
            try:
                self.assertEqual(2, ratchet.main(["check", "--repo-root", str(root), "--baseline", str(baseline)]))
            finally:
                ratchet.run_mypy = original


if __name__ == "__main__":
    unittest.main()
