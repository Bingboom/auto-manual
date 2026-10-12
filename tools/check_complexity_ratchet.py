#!/usr/bin/env python3
"""Fail-closed ratchet for per-function cyclomatic complexity.

The hotspot line caps in ``check_maintainability_guardrails.py`` stop files
from regrowing, but a function can keep gaining branches inside a file whose
length stays flat.  This check records the current complexity of every
function above ``MAX_NEW_COMPLEXITY`` and enforces three rules:

- a function missing from the baseline may not exceed ``MAX_NEW_COMPLEXITY``;
- a baselined function may not grow past its recorded value;
- a baselined function that got simpler must have its lower value written back
  in the same change, so the gain cannot be silently spent later.

Baseline entries whose function no longer exists are reported as stale and do
not fail.  The metric is a McCabe-style count computed with the standard
library only, so the guardrail job needs no extra dependency::

    python tools/check_complexity_ratchet.py check
    python tools/check_complexity_ratchet.py update
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = REPO_ROOT / "data" / "complexity_baseline.tsv"
MAX_NEW_COMPLEXITY = 20

_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
_BRANCHES = (
    ast.If,
    ast.IfExp,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.ExceptHandler,
    ast.match_case,
)


@dataclass(frozen=True)
class FunctionComplexity:
    path: str
    qualname: str
    complexity: int
    line: int

    @property
    def key(self) -> str:
        return f"{self.path}\t{self.qualname}"


@dataclass(frozen=True)
class RatchetResult:
    current: tuple[FunctionComplexity, ...]
    new: tuple[FunctionComplexity, ...]
    grown: tuple[tuple[FunctionComplexity, int], ...]
    improved: tuple[tuple[FunctionComplexity, int], ...]
    stale: tuple[str, ...]
    baseline_missing: bool = False

    @property
    def exit_code(self) -> int:
        if self.baseline_missing:
            return 2
        return 1 if (self.new or self.grown or self.improved) else 0


def _source_paths(repo_root: Path) -> Iterable[Path]:
    build_entrypoint = repo_root / "build.py"
    if build_entrypoint.exists():
        yield build_entrypoint
    tools_root = repo_root / "tools"
    if tools_root.exists():
        yield from sorted(tools_root.rglob("*.py"))


def _own_nodes(function: ast.AST) -> Iterable[ast.AST]:
    """Yield nodes in a function body without entering nested scopes."""

    stack = list(ast.iter_child_nodes(function))
    while stack:
        node = stack.pop()
        yield node
        if isinstance(node, _SCOPES):
            continue
        stack.extend(ast.iter_child_nodes(node))


def function_complexity(function: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """Return 1 + decision points; nested functions are measured separately."""

    complexity = 1
    for node in _own_nodes(function):
        if isinstance(node, _BRANCHES):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1
        elif isinstance(node, ast.comprehension):
            complexity += 1 + len(node.ifs)
    return complexity


def _functions(tree: ast.Module) -> Iterable[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]:
    def walk(node: ast.AST, prefix: str) -> Iterable[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = f"{prefix}{child.name}"
                yield name, child
                yield from walk(child, f"{name}.")
            elif isinstance(child, ast.ClassDef):
                yield from walk(child, f"{prefix}{child.name}.")
            else:
                yield from walk(child, prefix)

    yield from walk(tree, "")


def collect_complexities(repo_root: Path = REPO_ROOT) -> tuple[FunctionComplexity, ...]:
    results: list[FunctionComplexity] = []
    for path in _source_paths(repo_root):
        relative = path.relative_to(repo_root).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as exc:
            raise RuntimeError(f"Cannot inspect Python source: {path}") from exc
        seen: Counter[str] = Counter()
        for qualname, function in _functions(tree):
            seen[qualname] += 1
            # Same-named functions (e.g. per-branch helpers) get a stable suffix.
            unique = qualname if seen[qualname] == 1 else f"{qualname}#{seen[qualname]}"
            results.append(
                FunctionComplexity(relative, unique, function_complexity(function), function.lineno)
            )
    return tuple(sorted(results, key=lambda item: item.key))


def load_baseline(path: Path) -> dict[str, int] | None:
    if not path.exists():
        return None
    baseline: dict[str, int] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        source, qualname, value = line.split("\t")
        baseline[f"{source}\t{qualname}"] = int(value)
    return baseline


def write_baseline(path: Path, functions: Iterable[FunctionComplexity]) -> Path:
    entries = sorted(
        (item for item in functions if item.complexity > MAX_NEW_COMPLEXITY),
        key=lambda item: item.key,
    )
    header = (
        "# Per-function cyclomatic complexity baseline.\n"
        f"# Functions above {MAX_NEW_COMPLEXITY} are listed; none may grow, new ones\n"
        "# may not exceed the limit, and a lower value must be written back.\n"
        "# Regenerate intentionally with:\n"
        "#   python tools/check_complexity_ratchet.py update\n"
    )
    body = "".join(f"{item.key}\t{item.complexity}\n" for item in entries)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + body, encoding="utf-8")
    return path


def compare(functions: Iterable[FunctionComplexity], baseline: dict[str, int]) -> RatchetResult:
    current = tuple(functions)
    new: list[FunctionComplexity] = []
    grown: list[tuple[FunctionComplexity, int]] = []
    improved: list[tuple[FunctionComplexity, int]] = []
    for item in current:
        recorded = baseline.get(item.key)
        if recorded is None:
            if item.complexity > MAX_NEW_COMPLEXITY:
                new.append(item)
        elif item.complexity > recorded:
            grown.append((item, recorded))
        elif item.complexity < recorded:
            improved.append((item, recorded))
    current_keys = {item.key for item in current}
    stale = tuple(sorted(key for key in baseline if key not in current_keys))
    return RatchetResult(current, tuple(new), tuple(grown), tuple(improved), stale)


def check_repository(
    repo_root: Path = REPO_ROOT,
    *,
    baseline_path: Path | None = None,
    printer: Callable[[str], None] = print,
) -> RatchetResult:
    path = baseline_path or (repo_root / DEFAULT_BASELINE.relative_to(REPO_ROOT))
    functions = collect_complexities(repo_root)
    baseline = load_baseline(path)
    if baseline is None:
        printer(f"[complexity] ERROR missing baseline: {path}")
        return RatchetResult(functions, (), (), (), (), baseline_missing=True)

    result = compare(functions, baseline)
    for item in result.new:
        printer(
            f"[complexity] NEW {item.path}:{item.line} {item.qualname} "
            f"complexity {item.complexity} > limit {MAX_NEW_COMPLEXITY}"
        )
    for item, recorded in result.grown:
        printer(
            f"[complexity] GREW {item.path}:{item.line} {item.qualname} "
            f"complexity {recorded} -> {item.complexity}"
        )
    for item, recorded in result.improved:
        printer(
            f"[complexity] IMPROVED {item.path}:{item.line} {item.qualname} "
            f"complexity {recorded} -> {item.complexity}; lock it in with "
            "`python tools/check_complexity_ratchet.py update`"
        )
    for entry in result.stale:
        printer(f"[complexity] stale-baseline {entry}")
    printer(
        f"[complexity] {len(result.new)} new, {len(result.grown)} grown, "
        f"{len(result.improved)} improved, {len(result.stale)} stale, "
        f"{len(baseline)} baselined"
    )
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ratchet per-function cyclomatic complexity against a reviewed baseline."
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    for command, help_text in (
        ("check", "fail on new, grown, or unrecorded-improved complex functions"),
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
        path = write_baseline(baseline, collect_complexities(repo_root))
        print(f"[complexity] wrote {path}")
        return 0
    return check_repository(repo_root, baseline_path=baseline).exit_code


if __name__ == "__main__":
    sys.exit(main())
