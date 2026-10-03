#!/usr/bin/env python3
"""Fail-closed ratchet for tests that patch names on facade modules.

The orchestration facades (``build_docs``, ``process_build_queue``,
``process_review_start_queue``, ``backport.cloud_doc``) keep forwarders and
re-exports alive only because tests patch those names on the facade instead of
on the module that actually looks them up.  Every such patch pins a forwarder
in place.  This check counts them per test file and enforces:

- a test file missing from the baseline may not patch a facade at all;
- a baselined file may not patch facades more often than recorded;
- a file that dropped facade patches must have its lower count written back in
  the same change, so the gain cannot be silently spent later.

Counted forms (aliases are resolved from the file's imports)::

    patch.object(<facade module>, "name")      # also mock.patch.object
    patch.multiple(<facade module>, ...)
    patch("tools.<facade>.name")               # also mock.patch(...)

Baseline entries for files that no longer exist are reported as stale and do
not fail::

    python -m tools.check_facade_patch_ratchet check
    python -m tools.check_facade_patch_ratchet update
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = REPO_ROOT / "data" / "facade_patch_baseline.tsv"
FACADE_MODULES = (
    "tools.build.docs",
    "tools.backport.cloud_doc",
    "tools.build_queue.process_build_queue",
    "tools.build_queue.process_review_start_queue",
)
_TARGET_PATCHERS = frozenset({"object", "multiple"})


@dataclass(frozen=True)
class FilePatchCount:
    path: str
    count: int
    first_line: int


@dataclass(frozen=True)
class RatchetResult:
    current: tuple[FilePatchCount, ...]
    new: tuple[FilePatchCount, ...]
    grown: tuple[tuple[FilePatchCount, int], ...]
    improved: tuple[tuple[FilePatchCount, int], ...]
    stale: tuple[str, ...]
    baseline_missing: bool = False

    @property
    def exit_code(self) -> int:
        if self.baseline_missing:
            return 2
        return 1 if (self.new or self.grown or self.improved) else 0


def _dotted(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        return f"{base}.{node.attr}" if base else None
    return None


def _facade_aliases(tree: ast.Module) -> dict[str, str]:
    """Map local dotted names to the facade module they are bound to."""

    aliases = {module: module for module in FACADE_MODULES}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in FACADE_MODULES and alias.asname:
                    aliases[alias.asname] = alias.name
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            for alias in node.names:
                qualified = f"{node.module}.{alias.name}"
                if qualified in FACADE_MODULES:
                    aliases[alias.asname or alias.name] = qualified
    return aliases


def _is_facade_patch(call: ast.Call, aliases: dict[str, str]) -> bool:
    callee = _dotted(call.func)
    if not callee or not call.args:
        return False
    first = call.args[0]
    head, _, tail = callee.rpartition(".")
    if tail in _TARGET_PATCHERS and head.rpartition(".")[2] == "patch":
        return _dotted(first) in aliases
    if tail == "patch" or callee == "patch":
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            owner = first.value.rpartition(".")[0]
            return owner in FACADE_MODULES
    return False


def count_file(path: Path) -> tuple[int, int]:
    """Return (facade patch count, first offending line) for one test file."""

    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        raise RuntimeError(f"Cannot inspect Python source: {path}") from exc
    aliases = _facade_aliases(tree)
    lines = sorted(
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _is_facade_patch(node, aliases)
    )
    return len(lines), (lines[0] if lines else 0)


def _test_paths(repo_root: Path) -> Iterable[Path]:
    tests_root = repo_root / "tests"
    if tests_root.exists():
        yield from sorted(tests_root.rglob("*.py"))


def collect_counts(repo_root: Path = REPO_ROOT) -> tuple[FilePatchCount, ...]:
    results = []
    for path in _test_paths(repo_root):
        count, first_line = count_file(path)
        if count:
            results.append(FilePatchCount(path.relative_to(repo_root).as_posix(), count, first_line))
    return tuple(results)


def load_baseline(path: Path) -> dict[str, int] | None:
    if not path.exists():
        return None
    baseline: dict[str, int] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        source, value = line.split("\t")
        baseline[source] = int(value)
    return baseline


def write_baseline(path: Path, counts: Iterable[FilePatchCount]) -> Path:
    header = (
        "# Per-test-file count of patches applied to facade modules\n"
        f"# ({', '.join(FACADE_MODULES)}).\n"
        "# No file may grow, unlisted files may not patch facades, and a lower\n"
        "# count must be written back. Regenerate intentionally with:\n"
        "#   python -m tools.check_facade_patch_ratchet update\n"
    )
    body = "".join(f"{item.path}\t{item.count}\n" for item in sorted(counts, key=lambda item: item.path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + body, encoding="utf-8")
    return path


def compare(
    counts: Iterable[FilePatchCount],
    baseline: dict[str, int],
    existing: Iterable[str] = (),
) -> RatchetResult:
    """Compare current counts with the baseline.

    ``existing`` lists every test file present now, so a baselined file that
    dropped to zero patches reads as an improvement rather than as stale.
    """

    current = tuple(counts)
    present = set(existing) | {item.path for item in current}
    new: list[FilePatchCount] = []
    grown: list[tuple[FilePatchCount, int]] = []
    improved: list[tuple[FilePatchCount, int]] = []
    by_path = {item.path: item for item in current}
    for item in current:
        recorded = baseline.get(item.path)
        if recorded is None:
            new.append(item)
        elif item.count > recorded:
            grown.append((item, recorded))
        elif item.count < recorded:
            improved.append((item, recorded))
    for source, recorded in sorted(baseline.items()):
        if source in present and source not in by_path:
            improved.append((FilePatchCount(source, 0, 0), recorded))
    stale = tuple(sorted(source for source in baseline if source not in present))
    return RatchetResult(current, tuple(new), tuple(grown), tuple(improved), stale)


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
        printer(f"[facade-patch] ERROR missing baseline: {path}")
        return RatchetResult(counts, (), (), (), (), baseline_missing=True)

    existing = [item.relative_to(repo_root).as_posix() for item in _test_paths(repo_root)]
    result = compare(counts, baseline, existing)
    for item in result.new:
        printer(
            f"[facade-patch] NEW {item.path}:{item.first_line} patches a facade module "
            f"{item.count} time(s); patch the module that looks the name up instead"
        )
    for item, recorded in result.grown:
        printer(
            f"[facade-patch] GREW {item.path}:{item.first_line} facade patches "
            f"{recorded} -> {item.count}"
        )
    for item, recorded in result.improved:
        printer(
            f"[facade-patch] IMPROVED {item.path} facade patches {recorded} -> {item.count}; "
            "lock it in with `python -m tools.check_facade_patch_ratchet update`"
        )
    for entry in result.stale:
        printer(f"[facade-patch] stale-baseline {entry}")
    printer(
        f"[facade-patch] {len(result.new)} new, {len(result.grown)} grown, "
        f"{len(result.improved)} improved, {len(result.stale)} stale, "
        f"{sum(baseline.values())} baselined patches in {len(baseline)} files"
    )
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ratchet test patches applied to facade modules against a reviewed baseline."
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    for command, help_text in (
        ("check", "fail on new, grown, or unrecorded-improved facade patches"),
        ("update", "rewrite the baseline from the current tests"),
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
        print(f"[facade-patch] wrote {path}")
        return 0
    return check_repository(repo_root, baseline_path=baseline).exit_code


if __name__ == "__main__":
    sys.exit(main())
