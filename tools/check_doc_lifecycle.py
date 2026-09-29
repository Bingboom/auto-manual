#!/usr/bin/env python3
"""Ratchet: plan and review docs must declare a lifecycle status.

``code-as-doc/dev/`` and ``code-as-doc/reviews/`` accumulate dated plans,
discovery reports, and runbooks.  Without a status a reader cannot tell a
live plan from a finished record.  Every doc there must carry, within its
first ``HEADER_LINES`` lines, a line such as::

    Status: active · Owner: ... · Created: 2026-09-28

whose first word is one of ``STATUS_KEYWORDS``. ``superseded-by`` must name
a replacement link.  Leading ``>``, ``**`` and backticks are tolerated.

Docs that predate the rule are listed in the reviewed baseline and exempt until
they are fixed; a fixed or deleted doc shows up as stale and can be dropped::

    python tools/check_doc_lifecycle.py check
    python tools/check_doc_lifecycle.py update
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = REPO_ROOT / "data" / "doc_lifecycle_baseline.txt"
DOC_ROOTS = ("code-as-doc/dev", "code-as-doc/reviews")
NAVIGATION_FILES = {"README.md", "AGENTS.md", "CLAUDE.md"}
HEADER_LINES = 15
STATUS_KEYWORDS = ("proposed", "active", "done", "archived", "superseded-by")

_STATUS_RE = re.compile(r"^\s*>?\s*\**Status\**\s*[:：]\s*[*`\s]*([A-Za-z][\w-]*)", re.IGNORECASE)


@dataclass(frozen=True)
class LifecycleResult:
    new: tuple[str, ...]
    known: tuple[str, ...]
    stale: tuple[str, ...]
    baseline_missing: bool = False

    @property
    def exit_code(self) -> int:
        if self.baseline_missing:
            return 2
        return 1 if self.new else 0


def status_keyword(text: str) -> str | None:
    """Return the lower-cased status keyword from the doc header, if any."""

    for line in text.splitlines()[:HEADER_LINES]:
        match = _STATUS_RE.match(line)
        if match:
            return match.group(1).lower()
    return None


def is_compliant(text: str) -> bool:
    keyword = status_keyword(text)
    if keyword is None:
        return False
    if keyword not in STATUS_KEYWORDS:
        return False
    if keyword != "superseded-by":
        return True
    for line in text.splitlines()[:HEADER_LINES]:
        match = _STATUS_RE.match(line)
        if match:
            replacement = line[match.end():].strip(" *`")
            return bool(re.search(r"\[[^\]\n]+\]\([^\s)]+\)|<https?://[^>\s]+>|https?://\S+", replacement))
    return False


def iter_lifecycle_docs(repo_root: Path) -> Iterable[Path]:
    for root in DOC_ROOTS:
        directory = repo_root / root
        if directory.is_dir():
            for path in sorted(directory.rglob("*.md")):
                if path.name not in NAVIGATION_FILES:
                    yield path


def collect_noncompliant(repo_root: Path) -> tuple[str, ...]:
    return tuple(
        path.relative_to(repo_root).as_posix()
        for path in iter_lifecycle_docs(repo_root)
        if not is_compliant(path.read_text(encoding="utf-8", errors="replace"))
    )


def load_baseline(path: Path) -> set[str] | None:
    if not path.exists():
        return None
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def write_baseline(path: Path, entries: Iterable[str]) -> Path:
    header = (
        "# Plan/review docs that predate the lifecycle Status rule.\n"
        "# New docs under code-as-doc/dev/ and code-as-doc/reviews/ must start with\n"
        f"# `Status: <{'|'.join(STATUS_KEYWORDS)}>`; fixed entries become stale.\n"
        "# Regenerate intentionally with:\n"
        "#   python tools/check_doc_lifecycle.py update\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + "".join(f"{entry}\n" for entry in sorted(set(entries))), encoding="utf-8")
    return path


def check_repository(
    repo_root: Path = REPO_ROOT,
    *,
    baseline_path: Path | None = None,
    printer: Callable[[str], None] = print,
) -> LifecycleResult:
    path = baseline_path or (repo_root / DEFAULT_BASELINE.relative_to(REPO_ROOT))
    baseline = load_baseline(path)
    if baseline is None:
        printer(f"[doc-lifecycle] ERROR missing baseline: {path}")
        return LifecycleResult((), (), (), baseline_missing=True)

    current = set(collect_noncompliant(repo_root))
    result = LifecycleResult(
        new=tuple(sorted(current - baseline)),
        known=tuple(sorted(current & baseline)),
        stale=tuple(sorted(baseline - current)),
    )
    for entry in result.new:
        printer(
            f"[doc-lifecycle] MISSING STATUS {entry}: add "
            f"`Status: <{'|'.join(STATUS_KEYWORDS)}>` within the first {HEADER_LINES} lines"
        )
    for entry in result.stale:
        printer(f"[doc-lifecycle] stale-baseline {entry}")
    printer(
        f"[doc-lifecycle] {len(result.new)} new, {len(result.known)} known, "
        f"{len(result.stale)} stale"
    )
    return result


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Require lifecycle Status lines on plan/review docs.")
    subcommands = parser.add_subparsers(dest="command", required=True)
    for command, help_text in (
        ("check", "fail on docs without a lifecycle Status that are missing from the baseline"),
        ("update", "rewrite the baseline from the current docs"),
    ):
        subcommand = subcommands.add_parser(command, help=help_text)
        subcommand.add_argument("--repo-root", type=Path, default=REPO_ROOT)
        subcommand.add_argument("--baseline", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    baseline = args.baseline or (repo_root / DEFAULT_BASELINE.relative_to(REPO_ROOT))
    if args.command == "update":
        path = write_baseline(baseline, collect_noncompliant(repo_root))
        print(f"[doc-lifecycle] wrote {path}")
        return 0
    return check_repository(repo_root, baseline_path=baseline).exit_code


if __name__ == "__main__":
    raise SystemExit(main())
