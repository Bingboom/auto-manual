from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests import run_fast


class SlowListTest(unittest.TestCase):
    def test_comments_blank_lines_and_prefix_are_normalised(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "slow.txt"
            path.write_text(
                "# header\n\ntest_a   # 12.0s\ntests.test_b\n  test_c # note\n", encoding="utf-8"
            )
            self.assertEqual(
                {"tests.test_a", "tests.test_b", "tests.test_c"}, run_fast.load_slow_modules(path)
            )

    def test_every_listed_slow_module_exists(self) -> None:
        stale = run_fast.load_slow_modules() - set(run_fast.discover_modules())
        self.assertEqual(set(), stale, "remove renamed or deleted modules from tests/slow_modules.txt")


class PlanTest(unittest.TestCase):
    def test_batches_cover_every_module_once(self) -> None:
        modules = [f"tests.test_{index}" for index in range(23)]
        batches = run_fast.plan_batches(modules, workers=3)
        self.assertLessEqual(len(batches), 12)
        self.assertEqual(sorted(modules), sorted(name for batch in batches for name in batch))

    def test_few_modules_never_produce_empty_batches(self) -> None:
        self.assertEqual([["tests.test_a"]], run_fast.plan_batches(["tests.test_a"], workers=8))

    def test_selection_skips_slow_unless_all_or_named(self) -> None:
        with (
            mock.patch.object(run_fast, "discover_modules", return_value=["tests.test_a", "tests.test_slow"]),
            mock.patch.object(run_fast, "load_slow_modules", return_value={"tests.test_slow"}),
        ):
            self.assertEqual((["tests.test_a"], 1), run_fast.select_modules([], include_slow=False))
            self.assertEqual((["tests.test_a", "tests.test_slow"], 0), run_fast.select_modules([], include_slow=True))
            self.assertEqual((["tests.test_slow"], 0), run_fast.select_modules(["tests.test_slow"], include_slow=False))


class BatchResultTest(unittest.TestCase):
    def test_counts_and_failure_summary_are_parsed(self) -> None:
        completed = mock.Mock(
            returncode=1,
            stdout="",
            stderr="....F\n----\nRan 5 tests in 0.1s\n\nFAILED (failures=1)\n",
        )
        with mock.patch.object(run_fast.subprocess, "run", return_value=completed) as run:
            result = run_fast.run_batch(["tests.test_a"], python="py")
        self.assertEqual(5, result.ran)
        self.assertEqual("failures=1", result.failed)
        self.assertEqual(["py", "-m", "unittest", "tests.test_a"], run.call_args.args[0])
        self.assertEqual("0", run.call_args.kwargs["env"]["AUTO_MANUAL_ENV_PREFLIGHT"])


if __name__ == "__main__":
    unittest.main()
