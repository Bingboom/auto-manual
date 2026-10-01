#!/usr/bin/env python3
"""Fail-closed ratchet for ``zip()`` calls without ``strict=`` (ruff ``B905``).

A ``zip`` over iterables of different lengths silently drops the tail.  Plan
item CQ-4.4 audits each call (``strict=True`` where the lengths must match,
``strict=False`` with a comment where truncation is intended) before ``B905``
joins the ruff ``select``.  Until then this check keeps the count from growing,
per source file, with the same rules as the broad-except ratchet:

- a file missing from the baseline may not add an unmarked ``zip``;
- a baselined file may not have more than recorded;
- a lower count must be written back in the same change.

Counted: ``zip(...)`` calls with two or more positional (or any starred)
arguments and no ``strict=`` keyword, which matches ruff ``B905`` on this repo.
Scanned: ``build.py``, ``integrations/``, ``tools/``, ``tests/``, ``scripts/``
(the ruff lint scope)::

    python tools/check_zip_strict_ratchet.py check
    python tools/check_zip_strict_ratchet.py update
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path
from typing import Callable, Iterable

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.check_broad_except_ratchet import FileCount, RatchetResult, compare, load_baseline


REPO_ROOT = _REPO_ROOT
DEFAULT_BASELINE = REPO_ROOT / "data" / "zip_strict_baseline.tsv"
SOURCE_DIRS = ("integrations", "tools", "tests", "scripts")


def _is_unmarked_zip(node: ast.AST) -> bool:
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "zip"):
        return False
    if any(keyword.arg == "strict" for keyword in node.keywords):
        return False
    return len(node.args) >= 2 or any(isinstance(arg, ast.Starred) for arg in node.args)


def count_file(path: Path) -> tuple[int, int]:
    """Return (unmarked zip count, first such line) for one source file."""

    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        raise RuntimeError(f"Cannot inspect Python source: {path}") from exc
    lines = sorted(node.lineno for node in ast.walk(tree) if _is_unmarked_zip(node))
    return len(lines), (lines[0] if lines else 0)


def source_paths(repo_root: Path) -> Iterable[Path]:
    entry = repo_root / "build.py"
    if entry.exists():
        yield entry
    for name in SOURCE_DIRS:
        root = repo_root / name
        if root.exists():
            yield from sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def collect_counts(repo_root: Path = REPO_ROOT) -> tuple[FileCount, ...]:
    results = []
    for path in source_paths(repo_root):
        count, first_line = count_file(path)
        if count:
            results.append(FileCount(path.relative_to(repo_root).as_posix(), count, first_line))
    return tuple(results)


def write_baseline(path: Path, counts: Iterable[FileCount]) -> Path:
    header = (
        "# Per-file count of zip() calls without strict= (ruff B905) in build.py,\n"
        "# integrations/, tools/, tests/ and scripts/. No file may grow, unlisted files\n"
        "# may not add one, and a lower count must be written back. Regenerate\n"
        "# intentionally with:\n"
        "#   python tools/check_zip_strict_ratchet.py update\n"
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
) -> RatchetResult:
    path = baseline_path or (repo_root / DEFAULT_BASELINE.relative_to(REPO_ROOT))
    counts = collect_counts(repo_root)
    baseline = load_baseline(path)
    if baseline is None:
        printer(f"[zip-strict] ERROR missing baseline: {path}")
        return RatchetResult(counts, (), (), (), (), baseline_missing=True)

    existing = [item.relative_to(repo_root).as_posix() for item in source_paths(repo_root)]
    result = compare(counts, baseline, existing)
    for item in result.new:
        printer(
            f"[zip-strict] NEW {item.path}:{item.first_line} adds {item.count} zip() call(s) "
            "without strict=; pass strict=True, or strict=False with a comment if truncation is intended"
        )
    for item, recorded in result.grown:
        printer(f"[zip-strict] GREW {item.path}:{item.first_line} zip() without strict= {recorded} -> {item.count}")
    for item, recorded in result.improved:
        printer(
            f"[zip-strict] IMPROVED {item.path} zip() without strict= {recorded} -> {item.count}; "
            "lock it in with `python tools/check_zip_strict_ratchet.py update`"
        )
    for entry in result.stale:
        printer(f"[zip-strict] stale-baseline {entry}")
    printer(
        f"[zip-strict] {len(result.new)} new, {len(result.grown)} grown, "
        f"{len(result.improved)} improved, {len(result.stale)} stale, "
        f"{sum(baseline.values())} baselined calls in {len(baseline)} files"
    )
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ratchet zip() calls without strict= against a reviewed baseline.")
    subcommands = parser.add_subparsers(dest="command", required=True)
    for command, help_text in (
        ("check", "fail on new, grown, or unrecorded-improved zip() calls"),
        ("update", "rewrite the baseline from the current source"),
    ):
        subcommand = subcommands.add_parser(command, help=help_text)
        subcommand.add_argument("--repo-root", type=Path, default=REPO_ROOT)
        subcommand.add_argument("--baseline", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    baseline = args.baseline or (repo_root / DEFAULT_BASELINE.relative_to(REPO_ROOT))
    if args.command == "update":
        path = write_baseline(baseline, collect_counts(repo_root))
        print(f"[zip-strict] wrote {path}")
        return 0
    return check_repository(repo_root, baseline_path=baseline).exit_code


if __name__ == "__main__":
    sys.exit(main())
