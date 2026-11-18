"""Parallel test runner: the CI ``unit`` shards and the local fast tier.

Each test module runs in its own ``python`` process, so a module can neither
lean on nor leak into another module's imports or global state. Modules are
spread over worker processes (one per CPU by default), heaviest first::

    python -m tests.run_fast                      # local fast tier (skips slow modules)
    python -m tests.run_fast --all                # every module: the whole CI unit check
    python -m tests.run_fast --shard 2/4          # exactly what CI shard 2 of 4 runs
    python -m tests.run_fast --shard 2/4 --list   # show that shard's modules, run nothing
    python -m tests.run_fast tests.test_x         # only the named modules
    python -m tests.run_fast --all --write-timings  # refresh tests/unit_timings.json

Shards are assigned deterministically from ``tests/unit_timings.json`` (recorded
per-module seconds; an unknown module weighs ``default_seconds``), so every
module lands in exactly one shard. The fast tier skips modules whose recorded
time is at least ``SLOW_SECONDS``. A module that runs zero tests is an error
unless the manifest lists it under ``zero_test_modules``.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
ROOT = TESTS_DIR.parent
TIMINGS_PATH = TESTS_DIR / "unit_timings.json"
SLOW_SECONDS = 5.0
REFRESH_COMMAND = "python -m tests.run_fast --all --write-timings"


@dataclass(frozen=True)
class Timings:
    modules: dict[str, float]
    default_seconds: float
    zero_test_modules: frozenset[str]

    def weight(self, module: str) -> float:
        return self.modules.get(module, self.default_seconds)


def load_timings(path: Path = TIMINGS_PATH) -> Timings:
    data = json.loads(path.read_text(encoding="utf-8"))
    return Timings(
        modules={name: float(secs) for name, secs in data["modules"].items()},
        default_seconds=float(data["default_seconds"]),
        zero_test_modules=frozenset(data.get("zero_test_modules", [])),
    )


def discover_modules(tests_dir: Path = TESTS_DIR) -> list[str]:
    """Every module ``python -m unittest`` discovery imports (``tests/test*.py``)."""

    return sorted(f"tests.{path.stem}" for path in tests_dir.glob("test*.py"))


def by_weight(modules: list[str], timings: Timings) -> list[str]:
    """Heaviest first, ties by name: the scheduling order for workers and shards."""

    return sorted(modules, key=lambda name: (-timings.weight(name), name))


def plan_shards(modules: list[str], count: int, timings: Timings) -> list[list[str]]:
    """Deal modules into ``count`` shards, each to the currently lightest shard."""

    shards: list[list[str]] = [[] for _ in range(count)]
    loads = [0.0] * count
    for module in by_weight(modules, timings):
        index = min(range(count), key=lambda i: (loads[i], i))
        shards[index].append(module)
        loads[index] += timings.weight(module)
    return [sorted(shard) for shard in shards]


def parse_shard(text: str) -> tuple[int, int]:
    index_text, _, total_text = text.partition("/")
    try:
        index, total = int(index_text), int(total_text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected K/N, got {text!r}") from None
    if total < 1 or not 1 <= index <= total:
        raise argparse.ArgumentTypeError(f"shard {text!r} is out of range (1 <= K <= N)")
    return index, total


@dataclass
class ModuleResult:
    module: str
    seconds: float
    returncode: int
    output: str
    counts: dict[str, int] = field(default_factory=dict)
    problem: str = ""

    @property
    def ran(self) -> int:
        return self.counts.get("ran", 0)

    @property
    def ok(self) -> bool:
        return not self.problem


def judge(result: ModuleResult, zero_test_modules: frozenset[str]) -> str:
    """Return why a module run counts as failed, or ``""`` when it passed."""

    counts = result.counts
    if not counts:
        return f"no result (process exited {result.returncode})"
    problems = [f"{key}={counts[key]}" for key in ("failures", "errors", "unexpected_successes") if counts[key]]
    if problems:
        return ", ".join(problems)
    if result.returncode != 0:
        return f"process exited {result.returncode}"
    if counts["ran"] != counts["expected"]:
        return f"ran {counts['ran']} of {counts['expected']} collected tests"
    if counts["ran"] == 0 and result.module not in zero_test_modules:
        return "ran no tests (list it under zero_test_modules only if that is intended)"
    return ""


def run_module(module: str, zero_test_modules: frozenset[str], python: str = sys.executable) -> ModuleResult:
    env = dict(os.environ, AUTO_MANUAL_ENV_PREFLIGHT="0", PYTHONDONTWRITEBYTECODE="1")
    with tempfile.TemporaryDirectory(prefix="run-fast-") as tmp:
        result_file = Path(tmp) / "result.json"
        started = time.monotonic()
        proc = subprocess.run(
            [python, "-m", "tests.run_fast", "--worker", module, "--result-file", str(result_file)],
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        seconds = time.monotonic() - started
        counts = json.loads(result_file.read_text(encoding="utf-8")) if result_file.exists() else {}
    result = ModuleResult(module, seconds, proc.returncode, proc.stdout, counts)
    result.problem = judge(result, zero_test_modules)
    return result


def worker(module: str, result_file: Path) -> int:
    """Run one module in this process the way ``python -m unittest <module>`` would."""

    sys.argv = [sys.argv[0]]  # tests see no runner arguments, as under `python -m unittest`
    suite = unittest.defaultTestLoader.loadTestsFromName(module)
    expected = suite.countTestCases()
    outcome = unittest.TextTestRunner(stream=sys.stderr, verbosity=1).run(suite)
    counts = {
        "expected": expected,
        "ran": outcome.testsRun,
        "failures": len(outcome.failures),
        "errors": len(outcome.errors),
        "skipped": len(outcome.skipped),
        "expected_failures": len(outcome.expectedFailures),
        "unexpected_successes": len(outcome.unexpectedSuccesses),
    }
    result_file.write_text(json.dumps(counts), encoding="utf-8")
    return 0 if outcome.wasSuccessful() else 1


def write_timings(results: list[ModuleResult], path: Path = TIMINGS_PATH) -> None:
    current = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    current["refresh_command"] = REFRESH_COMMAND
    current["measured"] = {
        "date": time.strftime("%Y-%m-%d"),
        "python": ".".join(map(str, sys.version_info[:3])),
        "workers": f"{os.cpu_count()} CPUs",
    }
    current.setdefault("default_seconds", SLOW_SECONDS)
    current.setdefault("zero_test_modules", [])
    current["modules"] = {r.module: round(r.seconds, 1) for r in sorted(results, key=lambda r: r.module)}
    path.write_text(json.dumps(current, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def select_modules(args: argparse.Namespace, timings: Timings) -> tuple[list[str], str]:
    if args.modules:
        return list(args.modules), "named modules"
    modules = discover_modules()
    if args.shard:
        index, total = args.shard
        return plan_shards(modules, total, timings)[index - 1], f"shard {index}/{total}"
    if args.all:
        return modules, "all modules"
    kept = [name for name in modules if timings.weight(name) < SLOW_SECONDS]
    return kept, f"fast tier, {len(modules) - len(kept)} slow module(s) skipped (--all to include)"


def print_progress(done: int, total: int, result: ModuleResult) -> None:
    status = "ok  " if result.ok else "FAIL"
    tail = f"{result.ran} tests" if result.ok else result.problem
    print(f"[run-fast] {done:>4}/{total} {status} {result.seconds:6.1f}s {result.module} ({tail})", flush=True)


def report(results: list[ModuleResult], label: str, workers: int, elapsed: float, durations: int) -> int:
    failed = [r for r in results if not r.ok]
    slowest = sorted(results, key=lambda r: -r.seconds)
    shown = slowest if durations == 0 else slowest[:durations]
    print(f"\n[run-fast] slowest {len(shown)} of {len(results)} modules:")
    for r in shown:
        print(f"  {r.seconds:7.1f}s  {r.module}")
    for r in failed:
        print(f"\n===== FAILED {r.module}: {r.problem}\n{r.output.rstrip()}")
        if os.environ.get("GITHUB_ACTIONS") == "true":
            print(f"::error title=unit test module failed::{r.module}: {r.problem}")
    totals = {key: sum(r.counts.get(key, 0) for r in results) for key in ("ran", "skipped")}
    status = f"FAILED ({len(failed)} module(s): {', '.join(r.module for r in failed)})" if failed else "OK"
    print(
        f"\n[run-fast] {status}: {totals['ran']} tests ({totals['skipped']} skipped) in {len(results)} modules"
        f" [{label}], {workers} workers on {os.cpu_count()} CPUs, {elapsed:.0f}s wall,"
        f" {sum(r.seconds for r in results):.0f}s summed"
    )
    return 1 if failed else 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run test modules in parallel processes (CI unit shards, local fast tier).")
    parser.add_argument("modules", nargs="*", help="test modules to run (default: the fast tier)")
    parser.add_argument("-j", "--jobs", type=int, default=os.cpu_count() or 2, help="worker processes (default: CPU count)")
    parser.add_argument("--all", action="store_true", help="run every module, including slow ones")
    parser.add_argument("--shard", type=parse_shard, metavar="K/N", help="run shard K of N (implies --all)")
    parser.add_argument("--list", action="store_true", help="print the selected modules and their weights, run nothing")
    parser.add_argument("--durations", type=int, default=20, metavar="N", help="list the N slowest modules (0: all)")
    parser.add_argument("--write-timings", action="store_true", help=f"rewrite {TIMINGS_PATH.name} from this run (needs --all)")
    parser.add_argument("--worker", metavar="MODULE", help=argparse.SUPPRESS)
    parser.add_argument("--result-file", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.write_timings and (args.modules or args.shard or not args.all):
        parser.error("--write-timings needs a complete run: use --all without --shard or module names")
    if args.shard and args.modules:
        parser.error("--shard selects modules itself; do not name modules too")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.worker:
        return worker(args.worker, args.result_file)
    timings = load_timings()
    modules, label = select_modules(args, timings)
    if args.list:
        for name in by_weight(modules, timings):
            print(f"{timings.weight(name):7.1f}s  {name}")
        print(f"[run-fast] {len(modules)} modules [{label}], {sum(map(timings.weight, modules)):.0f}s recorded")
        return 0
    workers = max(1, args.jobs)
    print(f"[run-fast] {len(modules)} modules [{label}], {workers} workers, os.cpu_count()={os.cpu_count()}", flush=True)
    started = time.monotonic()
    results: list[ModuleResult] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(run_module, name, timings.zero_test_modules) for name in by_weight(modules, timings)]
        for future in as_completed(futures):
            results.append(future.result())
            print_progress(len(results), len(modules), results[-1])
    status = report(results, label, workers, time.monotonic() - started, args.durations)
    if args.write_timings:
        write_timings(results)
        print(f"[run-fast] wrote {TIMINGS_PATH.relative_to(ROOT)}")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
