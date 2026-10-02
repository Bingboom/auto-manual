#!/usr/bin/env python3
"""Print the next free MA or REV number, counting main, open PRs and this checkout (read-only).

Parallel windows take numbers from the same two tables:

- ``ma``: the merge-authorization registry, ``code-as-doc/dev/merge_authorizations.md``;
- ``rev``: the execution ledger, ``code-as-doc/dev/manual_revitalization_execution.md``.

Taking "the next one after main" collided three times on one day, because an
open PR had already reserved it. This tool counts a number as used when it is
on ``origin/main``, in this checkout's copy of the file, or new in the added
lines of any open pull request that touches the file. A row an open PR only
edits (a status flip, say) is already on main and reserves nothing new.

Run it right before pushing, and again if the push races another window
(REV-45 decision 16.10):

    python tools/next_registry_id.py ma
    python tools/next_registry_id.py rev
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable, NamedTuple

_REPO_ROOT = Path(__file__).resolve().parents[1]


class Table(NamedTuple):
    path: str
    row: re.Pattern[str]
    prefix: str
    width: int


TABLES = {
    "ma": Table("code-as-doc/dev/merge_authorizations.md", re.compile(r"^\+?\| (MA-(\d+)) \|"), "MA", 3),
    "rev": Table("code-as-doc/dev/manual_revitalization_execution.md",
                 re.compile(r'^\+?\| <a id="rev-\d+"></a>(REV-(\d+)) \|'), "REV", 2),
}

Run = Callable[[list[str]], str]


def numbers(lines: list[str], table: Table, *, added_only: bool = False) -> set[int]:
    """The row numbers in ``lines``; with ``added_only``, only diff lines that add a row."""
    found = set()
    for line in lines:
        if added_only and not line.startswith("+"):
            continue
        match = table.row.match(line)
        if match:
            found.add(int(match.group(2)))
    return found


def label(table: Table, number: int) -> str:
    return f"{table.prefix}-{number:0{table.width}d}"


def reservations(table: Table, *, run: Run, on_main: set[int]) -> dict[int, list[int]]:
    """New numbers each open PR adds to the table, by number, with the PRs that add it."""
    listing = json.loads(run(["gh", "pr", "list", "--state", "open", "--limit", "200", "--json", "number,files"]))
    reserved: dict[int, list[int]] = {}
    for pr in listing:
        if not any(item.get("path") == table.path for item in pr.get("files") or []):
            continue
        diff = run(["gh", "pr", "diff", str(pr["number"])])
        for number in numbers(diff.splitlines(), table, added_only=True) - on_main:
            reserved.setdefault(number, []).append(int(pr["number"]))
    return reserved


def next_free(used: set[int]) -> int:
    return max(used, default=0) + 1


def report(kind: str, *, run: Run, root: Path, fetch: bool = True) -> tuple[str, str]:
    """``(next id, one-line explanation)`` for the table named by ``kind``."""
    table = TABLES[kind]
    if fetch:
        run(["git", "-C", str(root), "fetch", "-q", "origin", "main"])
    on_main = numbers(run(["git", "-C", str(root), "show", f"origin/main:{table.path}"]).splitlines(), table)
    local_path = root / table.path
    local = numbers(local_path.read_text(encoding="utf-8").splitlines(), table) if local_path.is_file() else set()
    reserved = reservations(table, run=run, on_main=on_main)
    nxt = next_free(on_main | local | set(reserved))
    parts = [f"main has up to {label(table, max(on_main))}" if on_main else "main has none"]
    if local - on_main:
        parts.append("this checkout adds " + ", ".join(label(table, n) for n in sorted(local - on_main)))
    if reserved:
        parts.append("open PRs reserve " + ", ".join(
            f"{label(table, n)} ({', '.join(f'#{pr}' for pr in sorted(prs))})" for n, prs in sorted(reserved.items())))
    return label(table, nxt), "; ".join(parts)


def _run(args: list[str]) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print the next free MA or REV number (read-only).")
    parser.add_argument("kind", choices=sorted(TABLES), help="ma: merge-authorization registry; rev: execution ledger")
    parser.add_argument("--no-fetch", action="store_true", help="use the local origin/main without fetching")
    args = parser.parse_args(argv)
    try:
        nxt, why = report(args.kind, run=_run, root=_REPO_ROOT, fetch=not args.no_fetch)
    except (subprocess.CalledProcessError, OSError, ValueError) as exc:
        print(f"ERROR   {exc}", file=sys.stderr)
        return 1
    print(nxt)
    print(why, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
