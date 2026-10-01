from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from tools import check_zip_strict_ratchet as ratchet


def _write(root: Path, relative: str, source: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(source), encoding="utf-8")
    return path


class CountFileTest(unittest.TestCase):
    def test_counts_multi_argument_zip_without_strict_only(self) -> None:
        source = """
            pairs = zip(a)
            pairs = zip(a, b, strict=True)
            pairs = zip(a, b, strict=False)
            pairs = zip(a, b)
            pairs = zip(*rows)
            pairs = builtins.zip(a, b)
            pairs = zip(a, b, c)
        """
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(Path(tmp), "tools/x.py", source)
            self.assertEqual((3, 5), ratchet.count_file(path))


class CheckRepositoryTest(unittest.TestCase):
    def test_new_file_fails_and_update_then_check_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "tools/a.py", "x = zip(a, b)\n")
            _write(root, "tests/test_b.py", "x = zip(a, b, strict=True)\n")
            baseline = root / "data" / "baseline.tsv"
            ratchet.write_baseline(baseline, ())
            lines: list[str] = []
            result = ratchet.check_repository(root, baseline_path=baseline, printer=lines.append)
            self.assertEqual(1, result.exit_code)
            self.assertIn("NEW tools/a.py:1", lines[0])

            ratchet.write_baseline(baseline, ratchet.collect_counts(root))
            self.assertEqual(0, ratchet.check_repository(root, baseline_path=baseline, printer=lambda _: None).exit_code)

            _write(root, "tools/a.py", "x = zip(a, b, strict=True)\n")
            lines.clear()
            result = ratchet.check_repository(root, baseline_path=baseline, printer=lines.append)
            self.assertEqual(1, result.exit_code)
            self.assertIn("IMPROVED tools/a.py zip() without strict= 1 -> 0", lines[0])

    def test_missing_baseline_is_a_setup_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = ratchet.check_repository(Path(tmp), baseline_path=Path(tmp) / "none.tsv", printer=lambda _: None)
            self.assertEqual(2, result.exit_code)

    def test_repository_matches_its_baseline(self) -> None:
        self.assertEqual(0, ratchet.check_repository(printer=lambda _: None).exit_code)


if __name__ == "__main__":
    unittest.main()
