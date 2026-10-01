#!/usr/bin/env python3
"""Fail-closed ratchet for untyped-def mypy errors in the CQ-4.5 packages.

Plan item CQ-4.5 moves ``tools/manual_ir``, ``tools/component_specs`` and
``tools/csv_pages`` toward a strict mypy override.  Until each package reaches
zero, this check runs ``mypy --disallow-untyped-defs`` over them and keeps the
error count from growing, per source file, with the same rules as the other
ratchets:

- a file missing from the baseline may not add an error;
- a baselined file may not have more errors than recorded;
- a lower count must be written back in the same change.

Only errors reported inside the scoped packages count; errors mypy reports in
imported modules elsewhere are ignored, so unrelated edits cannot trip this
check.  mypy is not in ``requirements.lock``: CI runs this in the ``type-check``
job, which installs the version pinned there (keep ``MYPY_VERSION`` in step)::

    python tools/check_mypy_ratchet.py check
    python tools/check_mypy_ratchet.py update
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Callable, Iterable

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.check_broad_except_ratchet import FileCount, RatchetResult, compare, load_baseline


REPO_ROOT = _REPO_ROOT
DEFAULT_BASELINE = REPO_ROOT / "data" / "mypy_untyped_baseline.tsv"
PACKAGES = ("tools/manual_ir", "tools/component_specs", "tools/csv_pages")
MYPY_VERSION = "2.3.1"
_ERROR_LINE = re.compile(r"^(?P<path>[^:\s][^:]*\.pyi?):(?P<line>\d+):(?:\d+:)? error:")


def parse_mypy_output(output: str, packages: Iterable[str] = PACKAGES) -> tuple[FileCount, ...]:
    """Count mypy ``error:`` lines per file inside ``packages``."""

    prefixes = tuple(package.rstrip("/") + "/" for package in packages)
    counts: Counter[str] = Counter()
    first: dict[str, int] = {}
    for raw in output.splitlines():
        match = _ERROR_LINE.match(raw.strip())
        if not match:
            continue
        path = match.group("path").replace("\\", "/")
        if not path.startswith(prefixes):
            continue
        counts[path] += 1
        line = int(match.group("line"))
        first[path] = min(line, first.get(path, line))
    return tuple(FileCount(path, counts[path], first[path]) for path in sorted(counts))


def run_mypy(repo_root: Path) -> str:
    """Run mypy over the scoped packages and return its stdout."""

    try:
        import mypy  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            f"mypy is not installed; run `python -m pip install mypy=={MYPY_VERSION}`"
        ) from exc
    proc = subprocess.run(
        [sys.executable, "-m", "mypy", "--disallow-untyped-defs", "--no-error-summary", *PACKAGES],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode not in (0, 1):
        raise RuntimeError(f"mypy failed (exit {proc.returncode}):\n{proc.stderr or proc.stdout}")
    return proc.stdout


def installed_mypy_version() -> str:
    try:
        from mypy.version import __version__
    except ImportError:
        return ""
    return str(__version__).split("+")[0]


def source_paths(repo_root: Path) -> Iterable[str]:
    for package in PACKAGES:
        root = repo_root / package
        if root.exists():
            for path in sorted(root.rglob("*.py")):
                if "__pycache__" not in path.parts:
                    yield path.relative_to(repo_root).as_posix()


def write_baseline(path: Path, counts: Iterable[FileCount]) -> Path:
    header = (
        "# Per-file count of `mypy --disallow-untyped-defs` errors in tools/manual_ir,\n"
        f"# tools/component_specs and tools/csv_pages (mypy {MYPY_VERSION}). No file may grow,\n"
        "# unlisted files may not add one, and a lower count must be written back.\n"
        "# Regenerate intentionally with:\n"
        "#   python tools/check_mypy_ratchet.py update\n"
    )
    body = "".join(f"{item.path}\t{item.count}\n" for item in sorted(counts, key=lambda item: item.path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + body, encoding="utf-8")
    return path


def check_repository(
    repo_root: Path = REPO_ROOT,
    *,
    baseline_path: Path | None = None,
    printer: Callable[[str], None] = print,
    mypy_output: str | None = None,
) -> RatchetResult:
    path = baseline_path or (repo_root / DEFAULT_BASELINE.relative_to(REPO_ROOT))
    baseline = load_baseline(path)
    if baseline is None:
        printer(f"[mypy-ratchet] ERROR missing baseline: {path}")
        return RatchetResult((), (), (), (), (), baseline_missing=True)
    if mypy_output is None:
        version = installed_mypy_version()
        if version and version != MYPY_VERSION:
            printer(f"[mypy-ratchet] WARN mypy {version} installed; the baseline was recorded with {MYPY_VERSION}")
        mypy_output = run_mypy(repo_root)

    result = compare(parse_mypy_output(mypy_output), baseline, source_paths(repo_root))
    for item in result.new:
        printer(f"[mypy-ratchet] NEW {item.path}:{item.first_line} adds {item.count} untyped-def mypy error(s)")
    for item, recorded in result.grown:
        printer(f"[mypy-ratchet] GREW {item.path}:{item.first_line} mypy errors {recorded} -> {item.count}")
    for item, recorded in result.improved:
        printer(
            f"[mypy-ratchet] IMPROVED {item.path} mypy errors {recorded} -> {item.count}; "
            "lock it in with `python tools/check_mypy_ratchet.py update`"
        )
    for entry in result.stale:
        printer(f"[mypy-ratchet] stale-baseline {entry}")
    printer(
        f"[mypy-ratchet] {len(result.new)} new, {len(result.grown)} grown, "
        f"{len(result.improved)} improved, {len(result.stale)} stale, "
        f"{sum(baseline.values())} baselined errors in {len(baseline)} files"
    )
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ratchet untyped-def mypy errors against a reviewed baseline.")
    subcommands = parser.add_subparsers(dest="command", required=True)
    for command, help_text in (
        ("check", "fail on new, grown, or unrecorded-improved mypy errors"),
        ("update", "rewrite the baseline from a fresh mypy run"),
    ):
        subcommand = subcommands.add_parser(command, help=help_text)
        subcommand.add_argument("--repo-root", type=Path, default=REPO_ROOT)
        subcommand.add_argument("--baseline", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    baseline = args.baseline or (repo_root / DEFAULT_BASELINE.relative_to(REPO_ROOT))
    try:
        if args.command == "update":
            path = write_baseline(baseline, parse_mypy_output(run_mypy(repo_root)))
            print(f"[mypy-ratchet] wrote {path}")
            return 0
        return check_repository(repo_root, baseline_path=baseline).exit_code
    except RuntimeError as exc:
        print(f"[mypy-ratchet] ERROR {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
