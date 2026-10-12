from __future__ import annotations

import contextlib
import io
import tempfile
import textwrap
import unittest
from pathlib import Path

from tools import check_top_level_module_ratchet as ratchet


def _write(root: Path, relative: str, source: str = "") -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(source), encoding="utf-8")
    return path


class BootstrapDetectionTest(unittest.TestCase):
    def test_detects_bootstrap_imports_and_sys_path_insert(self) -> None:
        cases = {
            "from tools.utils.script_bootstrap import bootstrap_repo_root\n": True,
            "from utils import script_bootstrap\n": True,
            "import tools.utils.script_bootstrap as sb\n": True,
            "import sys\nsys.path.insert(0, 'x')\n": True,
            "# sys.path.insert(0, 'x') is not code\nimport os\n": False,
            '"""script_bootstrap mentioned in a docstring."""\n': False,
            "paths = []\npaths.insert(0, 'x')\n": False,
        }
        with tempfile.TemporaryDirectory() as tmp:
            for index, (source, expected) in enumerate(cases.items()):
                path = _write(Path(tmp), f"case_{index}.py", source)
                with self.subTest(source=source):
                    self.assertEqual(expected, ratchet.uses_bootstrap(path))

    def test_scans_subpackages_but_skips_the_bootstrap_helper_itself(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "tools/top.py", "import sys\nsys.path.insert(0, '.')\n")
            _write(root, "tools/pkg/inner.py", "from tools.utils.script_bootstrap import x\n")
            _write(root, "tools/utils/script_bootstrap.py", "import sys\nsys.path.insert(0, '.')\n")
            _write(root, "tools/clean.py", "VALUE = 1\n")
            self.assertEqual(
                ("tools/pkg/inner.py", "tools/top.py"),
                ratchet.bootstrap_files(root),
            )
            self.assertEqual(("clean.py", "top.py"), ratchet.top_level_modules(root))


class CompareTest(unittest.TestCase):
    def test_new_and_removed_entries_fail(self) -> None:
        baseline = ratchet.Baseline({"a.py": "", "gone.py": ""}, frozenset({"tools/a.py", "tools/old.py"}))
        result = ratchet.compare(("a.py", "new.py"), ("tools/a.py", "tools/new.py"), baseline)
        self.assertEqual(("new.py",), result.new_modules)
        self.assertEqual(("tools/new.py",), result.new_bootstraps)
        self.assertEqual(("gone.py",), result.removed_modules)
        self.assertEqual(("tools/old.py",), result.removed_bootstraps)
        self.assertEqual(1, result.exit_code)

    def test_matching_tree_passes(self) -> None:
        baseline = ratchet.Baseline({"a.py": ""}, frozenset({"tools/a.py"}))
        self.assertEqual(0, ratchet.compare(("a.py",), ("tools/a.py",), baseline).exit_code)


class RepositoryTest(unittest.TestCase):
    def _run(self, *argv: str) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ratchet.main(list(argv))
        return code, out.getvalue()

    def test_update_refuses_new_module_without_reason_and_records_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline.tsv"
            _write(root, "tools/a.py", "VALUE = 1\n")
            common = ("--repo-root", str(root), "--baseline", str(baseline))
            self.assertEqual(0, self._run("update", *common)[0])
            self.assertEqual(0, self._run("check", *common)[0])

            _write(root, "tools/b.py", "VALUE = 2\n")
            code, output = self._run("check", *common)
            self.assertEqual(1, code)
            self.assertIn("NEW tools/b.py", output)

            code, output = self._run("update", *common)
            self.assertEqual(1, code)
            self.assertIn("REFUSED tools/b.py", output)

            code, _ = self._run("update", *common, "--allow", "b.py=CLI entry point named in AGENTS.md")
            self.assertEqual(0, code)
            loaded = ratchet.load_baseline(baseline)
            assert loaded is not None
            self.assertEqual("CLI entry point named in AGENTS.md", loaded.modules["b.py"])
            self.assertEqual(0, self._run("check", *common)[0])

    def test_removed_module_must_be_written_back(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline.tsv"
            _write(root, "tools/a.py", "VALUE = 1\n")
            gone = _write(root, "tools/gone.py", "import sys\nsys.path.insert(0, '.')\n")
            common = ("--repo-root", str(root), "--baseline", str(baseline))
            self._run("update", *common)
            gone.unlink()
            code, output = self._run("check", *common)
            self.assertEqual(1, code)
            self.assertIn("REMOVED tools/gone.py", output)
            self.assertIn("REMOVED-BOOTSTRAP tools/gone.py", output)
            self.assertEqual(0, self._run("update", *common)[0])
            self.assertEqual(0, self._run("check", *common)[0])

    def test_missing_baseline_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "tools/a.py")
            result = ratchet.check_repository(root, baseline_path=root / "missing.tsv", printer=lambda _: None)
            self.assertEqual(2, result.exit_code)


if __name__ == "__main__":
    unittest.main()
