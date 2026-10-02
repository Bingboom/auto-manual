#!/usr/bin/env python3
"""Fail-closed ratchet for broad exception handlers.

``except Exception`` (and ``except BaseException``) catches everything, so a
handler that only meant to absorb one failure also hides bugs.  Some are
legitimate top-level boundaries; the audit in plan item CQ-5.3 sorts the rest
into "narrow it" and "stop swallowing it".  Until that audit is done this check
keeps the count from growing, per source file:

- a file missing from the baseline may not add a broad handler;
- a baselined file may not have more broad handlers than recorded;
- a file whose count fell must have its lower count written back in the same
  change, so the gain cannot be silently spent later.

Counted: ``except Exception``, ``except BaseException`` and tuples containing
either (bare ``except:`` is already rejected by ruff ``E722``), unless the
handler is audited:

- its body ends in ``raise`` (cleanup-and-reraise or wrap-and-reraise), so it
  does not swallow the error; or
- its ``except`` line carries ``# noqa: BLE001 - <reason>``, naming why this
  is a boundary that must absorb any failure (a CLI ``main``, a per-row batch,
  a best-effort side channel, a diagnostic probe).  Scanned:
``build.py``, ``tools/``, ``scripts/`` and ``integrations/``.  Baseline entries
for files that no longer exist are reported as stale and do not fail::

    python tools/check_broad_except_ratchet.py check
    python tools/check_broad_except_ratchet.py update
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = REPO_ROOT / "data" / "broad_except_baseline.tsv"
SOURCE_DIRS = ("tools", "scripts", "integrations")
BROAD_NAMES = frozenset({"Exception", "BaseException"})
AUDITED_MARKER = re.compile(r"#\s*noqa:\s*BLE001\s+-\s+\S")


@dataclass(frozen=True)
class FileCount:
    path: str
    count: int
    first_line: int


@dataclass(frozen=True)
class RatchetResult:
    current: tuple[FileCount, ...]
    new: tuple[FileCount, ...]
    grown: tuple[tuple[FileCount, int], ...]
    improved: tuple[tuple[FileCount, int], ...]
    stale: tuple[str, ...]
    baseline_missing: bool = False

    @property
    def exit_code(self) -> int:
        if self.baseline_missing:
            return 2
        return 1 if (self.new or self.grown or self.improved) else 0


def _is_broad(handler_type: ast.expr | None) -> bool:
    if isinstance(handler_type, ast.Name):
        return handler_type.id in BROAD_NAMES
    if isinstance(handler_type, ast.Attribute):
        return handler_type.attr in BROAD_NAMES and isinstance(handler_type.value, ast.Name) and handler_type.value.id == "builtins"
    if isinstance(handler_type, ast.Tuple):
        return any(_is_broad(element) for element in handler_type.elts)
    return False


def _is_audited(handler: ast.ExceptHandler, source_lines: list[str]) -> bool:
    """A handler that re-raises, or whose ``except`` line names its reason."""

    if handler.body and isinstance(handler.body[-1], ast.Raise):
        return True
    return bool(AUDITED_MARKER.search(source_lines[handler.lineno - 1]))


def count_file(path: Path) -> tuple[int, int]:
    """Return (broad handler count, first such line) for one source file."""

    try:
        source = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError) as exc:
        raise RuntimeError(f"Cannot inspect Python source: {path}") from exc
    source_lines = source.splitlines()
    lines = sorted(
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.ExceptHandler)
        and _is_broad(node.type)
        and not _is_audited(node, source_lines)
    )
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


def write_baseline(path: Path, counts: Iterable[FileCount]) -> Path:
    header = (
        "# Per-file count of broad exception handlers (except Exception / BaseException)\n"
        "# in build.py, tools/, scripts/ and integrations/. No file may grow, unlisted\n"
        "# files may not add one, and a lower count must be written back. Regenerate\n"
        "# intentionally with:\n"
        "#   python tools/check_broad_except_ratchet.py update\n"
    )
    body = "".join(f"{item.path}\t{item.count}\n" for item in sorted(counts, key=lambda item: item.path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + body, encoding="utf-8")
    return path


def compare(
    counts: Iterable[FileCount],
    baseline: dict[str, int],
    existing: Iterable[str] = (),
) -> RatchetResult:
    """Compare current counts with the baseline.

    ``existing`` lists every scanned file present now, so a baselined file that
    dropped to zero handlers reads as an improvement rather than as stale.
    """

    current = tuple(counts)
    by_path = {item.path: item for item in current}
    present = set(existing) | set(by_path)
    new: list[FileCount] = []
    grown: list[tuple[FileCount, int]] = []
    improved: list[tuple[FileCount, int]] = []
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
            improved.append((FileCount(source, 0, 0), recorded))
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
        printer(f"[broad-except] ERROR missing baseline: {path}")
        return RatchetResult(counts, (), (), (), (), baseline_missing=True)

    existing = [item.relative_to(repo_root).as_posix() for item in source_paths(repo_root)]
    result = compare(counts, baseline, existing)
    for item in result.new:
        printer(
            f"[broad-except] NEW {item.path}:{item.first_line} adds {item.count} broad exception "
            "handler(s); catch the specific exception, or re-raise after logging"
        )
    for item, recorded in result.grown:
        printer(
            f"[broad-except] GREW {item.path}:{item.first_line} broad exception handlers "
            f"{recorded} -> {item.count}"
        )
    for item, recorded in result.improved:
        printer(
            f"[broad-except] IMPROVED {item.path} broad exception handlers {recorded} -> {item.count}; "
            "lock it in with `python tools/check_broad_except_ratchet.py update`"
        )
    for entry in result.stale:
        printer(f"[broad-except] stale-baseline {entry}")
    printer(
        f"[broad-except] {len(result.new)} new, {len(result.grown)} grown, "
        f"{len(result.improved)} improved, {len(result.stale)} stale, "
        f"{sum(baseline.values())} baselined handlers in {len(baseline)} files"
    )
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ratchet broad exception handlers against a reviewed baseline."
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    for command, help_text in (
        ("check", "fail on new, grown, or unrecorded-improved broad handlers"),
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
        print(f"[broad-except] wrote {path}")
        return 0
    return check_repository(repo_root, baseline_path=baseline).exit_code


if __name__ == "__main__":
    sys.exit(main())
