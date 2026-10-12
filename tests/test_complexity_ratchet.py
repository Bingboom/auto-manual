from __future__ import annotations

import ast
import tempfile
import textwrap
import unittest
from pathlib import Path

from tools import check_complexity_ratchet as ratchet


def _branchy(name: str, branches: int) -> str:
    body = "".join(f"    if x == {i}:\n        return {i}\n" for i in range(branches))
    return f"def {name}(x):\n{body}    return -1\n"


class ComplexityMetricTest(unittest.TestCase):
    def _complexity(self, source: str) -> int:
        function = ast.parse(textwrap.dedent(source)).body[0]
        assert isinstance(function, ast.FunctionDef)
        return ratchet.function_complexity(function)

    def test_counts_decision_points_but_not_nested_scopes(self) -> None:
        source = """
            def outer(items, flag):
                for item in items:
                    if item and flag or not item:
                        continue
                try:
                    pass
                except ValueError:
                    pass
                values = [i for i in items if i]

                def inner(x):
                    if x:
                        return 1
                    return 0

                return inner(1) if flag else values
        """
        # 1 + for + if + boolop(and/or: 2) + except + comprehension(1 + 1 if) + ifexp
        self.assertEqual(9, self._complexity(source))

    def test_straight_line_function_is_one(self) -> None:
        self.assertEqual(1, self._complexity("def f():\n    return 1\n"))


class ComplexityRatchetTest(unittest.TestCase):
    def _repo(self, source: str) -> tuple[Path, Path, Path]:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "tools").mkdir()
        module = root / "tools" / "example.py"
        module.write_text(source, encoding="utf-8")
        return root, module, root / "baseline.tsv"

    def _check(self, root: Path, baseline: Path) -> ratchet.RatchetResult:
        return ratchet.check_repository(root, baseline_path=baseline, printer=lambda _: None)

    def test_baseline_records_only_functions_above_the_limit(self) -> None:
        limit = ratchet.MAX_NEW_COMPLEXITY
        root, _, baseline = self._repo(_branchy("big", limit) + _branchy("small", 2))
        ratchet.write_baseline(baseline, ratchet.collect_complexities(root))
        self.assertEqual(
            {"tools/example.py\tbig": limit + 1}, ratchet.load_baseline(baseline)
        )
        self.assertEqual(0, self._check(root, baseline).exit_code)

    def test_new_complex_function_fails(self) -> None:
        root, module, baseline = self._repo(_branchy("small", 2))
        ratchet.write_baseline(baseline, ratchet.collect_complexities(root))
        module.write_text(
            _branchy("small", 2) + _branchy("fresh", ratchet.MAX_NEW_COMPLEXITY), encoding="utf-8"
        )
        result = self._check(root, baseline)
        self.assertEqual(1, result.exit_code)
        self.assertEqual(["fresh"], [item.qualname for item in result.new])

    def test_growth_fails_and_improvement_must_be_recorded(self) -> None:
        limit = ratchet.MAX_NEW_COMPLEXITY
        root, module, baseline = self._repo(_branchy("big", limit + 5))
        ratchet.write_baseline(baseline, ratchet.collect_complexities(root))

        module.write_text(_branchy("big", limit + 6), encoding="utf-8")
        grown = self._check(root, baseline)
        self.assertEqual(1, grown.exit_code)
        self.assertEqual(1, len(grown.grown))

        module.write_text(_branchy("big", limit + 2), encoding="utf-8")
        improved = self._check(root, baseline)
        self.assertEqual(1, improved.exit_code)
        self.assertEqual(1, len(improved.improved))

        ratchet.write_baseline(baseline, ratchet.collect_complexities(root))
        self.assertEqual(0, self._check(root, baseline).exit_code)

    def test_removed_function_is_stale_only(self) -> None:
        root, module, baseline = self._repo(_branchy("big", ratchet.MAX_NEW_COMPLEXITY))
        ratchet.write_baseline(baseline, ratchet.collect_complexities(root))
        module.write_text("def small():\n    return 1\n", encoding="utf-8")
        result = self._check(root, baseline)
        self.assertEqual(0, result.exit_code)
        self.assertEqual(("tools/example.py\tbig",), result.stale)

    def test_duplicate_qualnames_get_stable_suffixes(self) -> None:
        source = (
            "if True:\n"
            "    def helper():\n        return 1\n"
            "else:\n"
            "    def helper():\n        return 2\n"
        )
        root, _, _ = self._repo(source)
        names = [item.qualname for item in ratchet.collect_complexities(root)]
        self.assertEqual(["helper", "helper#2"], names)

    def test_missing_baseline_is_a_distinct_failure(self) -> None:
        root, _, _ = self._repo("def f():\n    return 1\n")
        result = self._check(root, root / "missing.tsv")
        self.assertEqual(2, result.exit_code)
        self.assertTrue(result.baseline_missing)


if __name__ == "__main__":
    unittest.main()
