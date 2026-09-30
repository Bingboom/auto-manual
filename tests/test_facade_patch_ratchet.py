from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from tools import check_facade_patch_ratchet as ratchet


def _write(root: Path, relative: str, source: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(source), encoding="utf-8")
    return path


class CountFileTest(unittest.TestCase):
    def test_counts_object_multiple_and_string_targets_through_aliases(self) -> None:
        source = """
            from unittest import mock
            from unittest.mock import patch
            from tools import build_docs
            from tools import process_build_queue as pbq
            import tools.process_review_start_queue as review
            import tools.cloud_doc_backport

            @patch.object(build_docs, "run")
            def test_a(run):
                with mock.patch.object(pbq, "main"), patch.multiple(review, a=1):
                    pass
                with patch.object(tools.cloud_doc_backport, "x"):
                    pass
                with patch("tools.process_build_queue.helper"), mock.patch("tools.build_docs.run"):
                    pass
        """
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(Path(tmp), "tests/test_x.py", source)
            count, first_line = ratchet.count_file(path)
        self.assertEqual(count, 6)
        self.assertEqual(first_line, 9)

    def test_ignores_implementation_modules_and_unrelated_patches(self) -> None:
        source = """
            from unittest.mock import patch
            from tools import build_docs_artifacts, process_build_queue_main
            from pathlib import Path

            with patch.object(build_docs_artifacts, "run"), patch.object(Path, "exists"):
                pass
            with patch.object(process_build_queue_main, "run"):
                pass
            with patch("tools.process_build_queue_main.run"), patch("tools.build_docs.sub.run"):
                pass
            with patch.dict("os.environ", {}):
                pass
        """
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(Path(tmp), "tests/test_y.py", source)
            self.assertEqual(ratchet.count_file(path), (0, 0))


class CompareTest(unittest.TestCase):
    def test_new_grown_improved_and_stale(self) -> None:
        counts = (
            ratchet.FilePatchCount("tests/test_new.py", 1, 3),
            ratchet.FilePatchCount("tests/test_grew.py", 5, 1),
            ratchet.FilePatchCount("tests/test_fell.py", 2, 1),
            ratchet.FilePatchCount("tests/test_same.py", 4, 1),
        )
        baseline = {
            "tests/test_grew.py": 4,
            "tests/test_fell.py": 3,
            "tests/test_same.py": 4,
            "tests/test_cleared.py": 2,
            "tests/test_gone.py": 1,
        }
        existing = [item.path for item in counts] + ["tests/test_cleared.py"]
        result = ratchet.compare(counts, baseline, existing)
        self.assertEqual([item.path for item in result.new], ["tests/test_new.py"])
        self.assertEqual([(item.path, old) for item, old in result.grown], [("tests/test_grew.py", 4)])
        self.assertEqual(
            sorted((item.path, item.count, old) for item, old in result.improved),
            [("tests/test_cleared.py", 0, 2), ("tests/test_fell.py", 2, 3)],
        )
        self.assertEqual(result.stale, ("tests/test_gone.py",))
        self.assertEqual(result.exit_code, 1)

    def test_clean_when_matching_baseline(self) -> None:
        counts = (ratchet.FilePatchCount("tests/test_same.py", 4, 1),)
        result = ratchet.compare(counts, {"tests/test_same.py": 4, "tests/test_gone.py": 1})
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stale, ("tests/test_gone.py",))


class RepositoryTest(unittest.TestCase):
    def test_update_then_check_round_trip_and_missing_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(
                root,
                "tests/test_z.py",
                """
                from unittest.mock import patch
                from tools import build_docs
                with patch.object(build_docs, "run"):
                    pass
                """,
            )
            baseline = root / "data" / "facade_patch_baseline.tsv"
            lines: list[str] = []
            missing = ratchet.check_repository(root, baseline_path=baseline, printer=lines.append)
            self.assertEqual(missing.exit_code, 2)

            ratchet.write_baseline(baseline, ratchet.collect_counts(root))
            self.assertIn("tests/test_z.py\t1\n", baseline.read_text(encoding="utf-8"))
            result = ratchet.check_repository(root, baseline_path=baseline, printer=lines.append)
            self.assertEqual(result.exit_code, 0)

            _write(root, "tests/test_z.py", "from tools import build_docs\n")
            result = ratchet.check_repository(root, baseline_path=baseline, printer=lines.append)
            self.assertEqual(result.exit_code, 1)
            self.assertTrue(any("IMPROVED tests/test_z.py" in line for line in lines))

    def test_repository_baseline_is_current(self) -> None:
        lines: list[str] = []
        result = ratchet.check_repository(printer=lines.append)
        self.assertEqual(result.exit_code, 0, "\n".join(lines))


if __name__ == "__main__":
    unittest.main()
