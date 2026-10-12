from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from tools import check_broad_except_ratchet as ratchet


def _write(root: Path, relative: str, source: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(source), encoding="utf-8")
    return path


class CountFileTest(unittest.TestCase):
    def test_counts_exception_baseexception_and_tuples_only(self) -> None:
        source = """
            import builtins
            try:
                pass
            except ValueError:
                pass
            try:
                pass
            except Exception:
                pass
            try:
                pass
            except (OSError, BaseException) as exc:
                pass
            try:
                pass
            except builtins.Exception:
                pass
            try:
                pass
            except (KeyError, TypeError):
                pass
        """
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(Path(tmp), "tools/x.py", source)
            self.assertEqual((3, 9), ratchet.count_file(path))

    def test_reraising_and_reasoned_handlers_are_audited(self) -> None:
        source = """
            try:
                pass
            except BaseException:
                cleanup()
                raise
            try:
                pass
            except Exception as exc:
                raise RuntimeError("wrapped") from exc
            try:
                pass
            except Exception:  # noqa: BLE001 - CLI boundary
                pass
            try:
                pass
            except Exception:  # noqa: BLE001
                pass
            try:
                pass
            except Exception:
                raise_later = True
        """
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(Path(tmp), "tools/x.py", source)
            # Only the reasonless noqa and the handler that merely mentions raise count.
            self.assertEqual((2, 17), ratchet.count_file(path))


class CompareTest(unittest.TestCase):
    def test_new_grown_improved_cleared_and_stale(self) -> None:
        counts = (
            ratchet.FileCount("tools/new.py", 1, 3),
            ratchet.FileCount("tools/grew.py", 3, 1),
            ratchet.FileCount("tools/fell.py", 1, 1),
            ratchet.FileCount("tools/same.py", 2, 1),
        )
        baseline = {
            "tools/grew.py": 2,
            "tools/fell.py": 2,
            "tools/same.py": 2,
            "tools/cleared.py": 1,
            "tools/gone.py": 1,
        }
        existing = [item.path for item in counts] + ["tools/cleared.py"]
        result = ratchet.compare(counts, baseline, existing)
        self.assertEqual(["tools/new.py"], [item.path for item in result.new])
        self.assertEqual([("tools/grew.py", 2)], [(item.path, old) for item, old in result.grown])
        self.assertEqual(
            [("tools/cleared.py", 0, 1), ("tools/fell.py", 1, 2)],
            sorted((item.path, item.count, old) for item, old in result.improved),
        )
        self.assertEqual(("tools/gone.py",), result.stale)
        self.assertEqual(1, result.exit_code)


class RepositoryTest(unittest.TestCase):
    def test_missing_baseline_update_check_and_improvement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "build.py", "try:\n    pass\nexcept Exception:\n    pass\n")
            _write(root, "scripts/ok.py", "x = 1\n")
            baseline = root / "data" / "broad_except_baseline.tsv"
            lines: list[str] = []
            self.assertEqual(2, ratchet.check_repository(root, baseline_path=baseline, printer=lines.append).exit_code)

            ratchet.write_baseline(baseline, ratchet.collect_counts(root))
            self.assertIn("build.py\t1\n", baseline.read_text(encoding="utf-8"))
            self.assertEqual(0, ratchet.check_repository(root, baseline_path=baseline, printer=lines.append).exit_code)

            _write(root, "scripts/ok.py", "try:\n    pass\nexcept BaseException:\n    x = 0\n")
            self.assertEqual(1, ratchet.check_repository(root, baseline_path=baseline, printer=lines.append).exit_code)
            self.assertTrue(any("NEW scripts/ok.py:3" in line for line in lines))

    def test_repository_baseline_is_current(self) -> None:
        lines: list[str] = []
        result = ratchet.check_repository(printer=lines.append)
        self.assertEqual(0, result.exit_code, "\n".join(lines))


if __name__ == "__main__":
    unittest.main()
