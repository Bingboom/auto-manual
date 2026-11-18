from __future__ import annotations

import unittest
from collections import Counter
from collections.abc import Iterator
from unittest import mock

from tests import run_fast


def _iter_cases(suite: unittest.TestSuite) -> Iterator[unittest.TestCase]:
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _iter_cases(item)
        else:
            yield item


def _timings(**modules: float) -> run_fast.Timings:
    return run_fast.Timings(
        modules={f"tests.{name}": secs for name, secs in modules.items()},
        default_seconds=5.0,
        zero_test_modules=frozenset({"tests.test_empty"}),
    )


class DiscoveryCompletenessTest(unittest.TestCase):
    """The shard planner must see every module that `python -m unittest` runs."""

    @classmethod
    def setUpClass(cls) -> None:
        suite = unittest.TestLoader().discover(start_dir=str(run_fast.ROOT), top_level_dir=str(run_fast.ROOT))
        cls.discovered = Counter(type(case).__module__ for case in _iter_cases(suite))
        cls.planned = run_fast.discover_modules()

    def test_discovery_imports_every_module_cleanly(self) -> None:
        self.assertNotIn("unittest.loader", self.discovered, "a test module fails to import under discovery")

    def test_every_discovered_module_is_planned(self) -> None:
        self.assertEqual(set(), set(self.discovered) - set(self.planned))

    def test_planned_modules_without_tests_are_declared(self) -> None:
        timings = run_fast.load_timings()
        empty = set(self.planned) - set(self.discovered)
        self.assertEqual(set(timings.zero_test_modules), empty, "update zero_test_modules in tests/unit_timings.json")

    def test_shards_partition_the_real_module_list(self) -> None:
        timings = run_fast.load_timings()
        for count in range(1, 9):
            with self.subTest(shards=count):
                shards = run_fast.plan_shards(self.planned, count, timings)
                flat = [name for shard in shards for name in shard]
                self.assertEqual(count, len(shards))
                self.assertEqual(sorted(self.planned), sorted(flat))
                self.assertEqual(len(flat), len(set(flat)))
                self.assertEqual(shards, run_fast.plan_shards(list(reversed(self.planned)), count, timings))


class PlanTest(unittest.TestCase):
    def test_heavy_modules_are_spread_and_unknown_modules_get_the_default(self) -> None:
        timings = _timings(test_a=100.0, test_b=90.0, test_c=10.0, test_d=1.0)
        self.assertEqual(5.0, timings.weight("tests.test_new"))
        shards = run_fast.plan_shards(
            ["tests.test_a", "tests.test_b", "tests.test_c", "tests.test_d", "tests.test_new"], 2, timings
        )
        self.assertEqual([["tests.test_a", "tests.test_new"], ["tests.test_b", "tests.test_c", "tests.test_d"]], shards)

    def test_more_shards_than_modules_leaves_empty_shards(self) -> None:
        self.assertEqual([["tests.test_a"], []], run_fast.plan_shards(["tests.test_a"], 2, _timings()))

    def test_shard_argument_is_validated(self) -> None:
        self.assertEqual((2, 4), run_fast.parse_shard("2/4"))
        for bad in ("0/4", "5/4", "1/0", "x", "2"):
            with self.subTest(bad=bad), self.assertRaises(Exception):
                run_fast.parse_shard(bad)

    def test_fast_tier_skips_slow_modules_unless_all_shard_or_named(self) -> None:
        timings = _timings(test_a=1.0, test_slow=run_fast.SLOW_SECONDS)
        with mock.patch.object(run_fast, "discover_modules", return_value=["tests.test_a", "tests.test_slow"]):
            self.assertEqual(["tests.test_a"], run_fast.select_modules(run_fast.parse_args([]), timings)[0])
            everything = ["tests.test_a", "tests.test_slow"]
            self.assertEqual(everything, run_fast.select_modules(run_fast.parse_args(["--all"]), timings)[0])
            self.assertEqual(everything, run_fast.select_modules(run_fast.parse_args(["--shard", "1/1"]), timings)[0])
            named = run_fast.parse_args(["tests.test_slow"])
            self.assertEqual(["tests.test_slow"], run_fast.select_modules(named, timings)[0])

    def test_write_timings_requires_a_complete_run(self) -> None:
        for argv in (["--write-timings"], ["--all", "--shard", "1/2", "--write-timings"], ["--all", "tests.test_a", "--write-timings"]):
            with self.subTest(argv=argv), mock.patch("sys.stderr"), self.assertRaises(SystemExit):
                run_fast.parse_args(argv)


class JudgeTest(unittest.TestCase):
    ZERO = frozenset({"tests.test_empty"})

    def _result(self, module: str = "tests.test_a", returncode: int = 0, **counts: int) -> run_fast.ModuleResult:
        base = {"expected": 3, "ran": 3, "failures": 0, "errors": 0, "skipped": 0, "unexpected_successes": 0}
        return run_fast.ModuleResult(module, 1.0, returncode, "", {**base, **counts})

    def test_verdicts(self) -> None:
        self.assertEqual("", run_fast.judge(self._result(), self.ZERO))
        cases = {
            "failures=1, errors=2": self._result(returncode=1, failures=1, errors=2),
            "process exited 3": self._result(returncode=3),
            "ran 2 of 3 collected tests": self._result(ran=2),
            "ran no tests": self._result(expected=0, ran=0),
        }
        for expected, result in cases.items():
            with self.subTest(expected=expected):
                self.assertTrue(run_fast.judge(result, self.ZERO).startswith(expected))

    def test_declared_empty_module_passes_and_missing_result_fails(self) -> None:
        self.assertEqual("", run_fast.judge(self._result("tests.test_empty", expected=0, ran=0), self.ZERO))
        crashed = run_fast.ModuleResult("tests.test_a", 1.0, -9, "", {})
        self.assertEqual("no result (process exited -9)", run_fast.judge(crashed, self.ZERO))


class WorkerProcessTest(unittest.TestCase):
    def test_module_runs_in_its_own_process_and_reports_counts(self) -> None:
        result = run_fast.run_module("tests.test_listen_build_queue", frozenset())
        self.assertEqual("", result.problem, result.output)
        self.assertEqual(result.counts["expected"], result.ran)
        self.assertGreater(result.ran, 0)
        self.assertIn("Ran ", result.output)

    def test_import_failure_is_reported_as_a_failed_module(self) -> None:
        result = run_fast.run_module("tests.test_does_not_exist_anywhere", frozenset())
        self.assertNotEqual("", result.problem)
        self.assertIn("test_does_not_exist_anywhere", result.output)


if __name__ == "__main__":
    unittest.main()
