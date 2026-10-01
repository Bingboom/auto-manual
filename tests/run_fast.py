"""Local fast test tier: run test modules in parallel, skipping the slow ones.

``python -m unittest`` stays the full, single-process run that CI uses. This
runner is for local iteration only::

    python -m tests.run_fast              # fast tier, one worker per CPU
    python -m tests.run_fast -j 2         # fewer workers
    python -m tests.run_fast --all        # every module, still in parallel
    python -m tests.run_fast tests.test_x # only the named modules

Modules listed in ``tests/slow_modules.txt`` (real Sphinx builds, IDML golden
exports, frozen-AI replays) are skipped unless ``--all`` or named explicitly.
Each worker runs a batch of modules with ``python -m unittest`` in its own
process, so module-level state never leaks between batches.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
ROOT = TESTS_DIR.parent
SLOW_LIST = TESTS_DIR / "slow_modules.txt"

_RAN = re.compile(r"^Ran (\d+) tests? in", re.M)
_FAILED = re.compile(r"^FAILED \((.*)\)$", re.M)


def load_slow_modules(path: Path = SLOW_LIST) -> set[str]:
    names = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            name = line.split()[0]
            names.add(name if name.startswith("tests.") else f"tests.{name}")
    return names


def discover_modules(tests_dir: Path = TESTS_DIR) -> list[str]:
    return sorted(f"tests.{path.stem}" for path in tests_dir.glob("test_*.py"))


def plan_batches(modules: list[str], workers: int) -> list[list[str]]:
    """Deal modules round-robin into small batches so workers stay busy."""

    count = max(1, min(len(modules), workers * 4))
    batches: list[list[str]] = [[] for _ in range(count)]
    for index, module in enumerate(modules):
        batches[index % count].append(module)
    return [batch for batch in batches if batch]


@dataclass
class BatchResult:
    modules: list[str]
    returncode: int
    ran: int
    failed: str
    output: str


def run_batch(modules: list[str], python: str = sys.executable) -> BatchResult:
    env = dict(os.environ, AUTO_MANUAL_ENV_PREFLIGHT="0")
    proc = subprocess.run(
        [python, "-m", "unittest", *modules],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    output = proc.stdout + proc.stderr
    ran = sum(int(match) for match in _RAN.findall(output))
    failed = ", ".join(_FAILED.findall(output))
    return BatchResult(modules, proc.returncode, ran, failed, output)


def select_modules(requested: list[str], include_slow: bool) -> tuple[list[str], int]:
    if requested:
        return requested, 0
    modules = discover_modules()
    if include_slow:
        return modules, 0
    slow = load_slow_modules()
    kept = [module for module in modules if module not in slow]
    return kept, len(modules) - len(kept)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local fast test tier in parallel.")
    parser.add_argument("modules", nargs="*", help="test modules to run (default: all but slow_modules.txt)")
    parser.add_argument("-j", "--jobs", type=int, default=os.cpu_count() or 2, help="parallel workers")
    parser.add_argument("--all", action="store_true", help="include the modules in slow_modules.txt")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    modules, skipped = select_modules(args.modules, args.all)
    workers = max(1, args.jobs)
    batches = plan_batches(modules, workers)
    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(run_batch, batches))
    elapsed = time.monotonic() - started

    failures = [result for result in results if result.returncode != 0]
    for result in failures:
        print(f"\n===== FAILED batch: {' '.join(result.modules)} ({result.failed or 'no summary'})")
        print(result.output.rstrip())
    total = sum(result.ran for result in results)
    note = f", {skipped} slow module(s) skipped (--all to include)" if skipped else ""
    status = "FAILED" if failures else "OK"
    print(
        f"\n[run-fast] {status}: {total} tests in {len(modules)} modules, "
        f"{workers} workers, {elapsed:.0f}s{note}"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
