#!/usr/bin/env python3
"""Print the next free MA or REV number, counting main, open PRs and this checkout (read-only).

Parallel windows take numbers from the same two tables:

- ``ma``: the merge-authorization registry, ``code-as-doc/dev/merge_authorizations.md``,
  plus its archive of expired rows, ``code-as-doc/dev/merge_authorizations_archive.md``;
- ``rev``: the execution ledger, ``code-as-doc/dev/manual_revitalization_execution.md``.

Taking "the next one after main" collided three times on one day, because an
open PR had already reserved it. This tool counts a number as used when it is
on ``origin/main``, in this checkout's copy of the file, or new in the added
lines of any open pull request that touches the file. A row an open PR only
edits (a status flip, say) or moves to the archive is already on main and
reserves nothing new. An archive that main does not have yet counts as empty.

Run it right before pushing, and again if the push races another window
(REV-45 decision 16.10):

    python tools/next_registry_id.py ma
    python tools/next_registry_id.py rev

Open PRs are read with ``gh``. Where ``gh`` cannot run (a cloud session has no
login), they are read from the GitHub REST API instead, with ``GH_TOKEN`` or
``GITHUB_TOKEN`` when one is set.

Two windows that ask at the same moment still get the same number. The
maintainability guardrails therefore run :func:`check_unique`, which fails when
a number is used by more than one row. CI tests a pull request merged with
main, so the second PR to take a number fails before it merges.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, NamedTuple

_REPO_ROOT = Path(__file__).resolve().parents[1]


class Table(NamedTuple):
    path: str
    row: re.Pattern[str]
    prefix: str
    width: int
    archive: str = ""


TABLES = {
    "ma": Table("code-as-doc/dev/merge_authorizations.md", re.compile(r"^\+?\| (MA-(\d+)) \|"), "MA", 3,
                archive="code-as-doc/dev/merge_authorizations_archive.md"),
    "rev": Table("code-as-doc/dev/manual_revitalization_execution.md",
                 re.compile(r'^\+?\| <a id="rev-\d+"></a>(REV-(\d+)) \|'), "REV", 2),
}

Run = Callable[[list[str]], str]
Http = Callable[[str], str]

GITHUB_API = "https://api.github.com"

# Numbers that two rows already shared before check_unique existed. Rows are never
# renumbered or deleted, so each of these stays a pair; any other repeat fails.
KNOWN_DUPLICATES = {"ma": frozenset({67, 77, 81, 201, 225, 281}), "rev": frozenset()}


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


def paths(table: Table) -> tuple[str, ...]:
    """The files that hold the table's rows: the live file, then its archive."""
    return (table.path, table.archive) if table.archive else (table.path,)


def label(table: Table, number: int) -> str:
    return f"{table.prefix}-{number:0{table.width}d}"


def reservations(table: Table, *, run: Run, on_main: set[int]) -> dict[int, list[int]]:
    """New numbers each open PR adds to the table, by number, with the PRs that add it."""
    listing = json.loads(run(["gh", "pr", "list", "--state", "open", "--limit", "200", "--json", "number,files"]))
    reserved: dict[int, list[int]] = {}
    for pr in listing:
        if not any(item.get("path") in paths(table) for item in pr.get("files") or []):
            continue
        diff = run(["gh", "pr", "diff", str(pr["number"])])
        for number in numbers(diff.splitlines(), table, added_only=True) - on_main:
            reserved.setdefault(number, []).append(int(pr["number"]))
    return reserved


def github_slug(*, run: Run, root: Path) -> str:
    """``owner/repo`` of the ``origin`` remote, from an HTTPS, SSH or proxied URL."""
    url = run(["git", "-C", str(root), "remote", "get-url", "origin"]).strip()
    match = re.search(r"[/:]([^/:@]+)/([^/]+?)(?:\.git)?/?$", url)
    if not match:
        raise ValueError("cannot read owner/repo from the origin remote")
    return f"{match.group(1)}/{match.group(2)}"


def _pages(url: str, http: Http) -> list[dict]:
    """Every item of a paginated GitHub list endpoint."""
    items: list[dict] = []
    page = 1
    while True:
        batch = json.loads(http(f"{url}{'&' if '?' in url else '?'}per_page=100&page={page}"))
        items.extend(batch)
        if len(batch) < 100:
            return items
        page += 1


def api_reservations(table: Table, *, http: Http, slug: str, on_main: set[int]) -> dict[int, list[int]]:
    """:func:`reservations` from the GitHub REST API, for when ``gh`` cannot run."""
    def added_by(pr: dict) -> set[int]:
        added: set[int] = set()
        for item in _pages(f"{GITHUB_API}/repos/{slug}/pulls/{pr['number']}/files", http):
            if item.get("filename") not in paths(table):
                continue
            if item.get("patch") is not None:
                added |= numbers(item["patch"].splitlines(), table, added_only=True)
            else:  # GitHub leaves out the patch of a large diff; read the PR's copy of the file
                added |= numbers(http(item["raw_url"]).splitlines(), table)
        return added

    prs = _pages(f"{GITHUB_API}/repos/{slug}/pulls?state=open", http)
    with ThreadPoolExecutor(max_workers=8) as pool:
        added_per_pr = list(pool.map(added_by, prs))
    reserved: dict[int, list[int]] = {}
    for pr, added in zip(prs, added_per_pr, strict=True):
        for number in added - on_main:
            reserved.setdefault(number, []).append(int(pr["number"]))
    return reserved


def _http_get(url: str) -> str:
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def main_text(path: str, *, run: Run, root: Path, optional: bool = False) -> str:
    """``path`` as it is on ``origin/main``; an optional file main lacks reads as empty."""
    try:
        return run(["git", "-C", str(root), "show", f"origin/main:{path}"])
    except subprocess.CalledProcessError:
        if optional:
            return ""
        raise


def next_free(used: set[int]) -> int:
    return max(used, default=0) + 1


def report(kind: str, *, run: Run, root: Path, fetch: bool = True, http: Http = _http_get) -> tuple[str, str]:
    """``(next id, one-line explanation)`` for the table named by ``kind``."""
    table = TABLES[kind]
    if fetch:
        run(["git", "-C", str(root), "fetch", "-q", "origin", "main"])
    on_main: set[int] = set()
    local: set[int] = set()
    for path in paths(table):
        on_main |= numbers(main_text(path, run=run, root=root, optional=path != table.path).splitlines(), table)
        local_path = root / path
        if local_path.is_file():
            local |= numbers(local_path.read_text(encoding="utf-8").splitlines(), table)
    try:
        reserved = reservations(table, run=run, on_main=on_main)
        via_api = False
    except (subprocess.CalledProcessError, OSError):
        reserved = api_reservations(table, http=http, slug=github_slug(run=run, root=root), on_main=on_main)
        via_api = True
    nxt = next_free(on_main | local | set(reserved))
    parts = [f"main has up to {label(table, max(on_main))}" if on_main else "main has none"]
    if local - on_main:
        parts.append("this checkout adds " + ", ".join(label(table, n) for n in sorted(local - on_main)))
    if reserved:
        parts.append("open PRs reserve " + ", ".join(
            f"{label(table, n)} ({', '.join(f'#{pr}' for pr in sorted(prs))})" for n, prs in sorted(reserved.items())))
    if via_api:
        parts.append("open PRs read from the GitHub API (gh unavailable)")
    return label(table, nxt), "; ".join(parts)


def duplicates(root: Path) -> list[tuple[str, int]]:
    """``(id, rows)`` for each number used by more rows than :data:`KNOWN_DUPLICATES` allows."""
    found: list[tuple[str, int]] = []
    for kind, table in TABLES.items():
        counts: dict[int, int] = {}
        for path in paths(table):
            file = root / path
            if file.is_file():
                for line in file.read_text(encoding="utf-8").splitlines():
                    match = table.row.match(line)
                    if match:
                        number = int(match.group(2))
                        counts[number] = counts.get(number, 0) + 1
        allowed = KNOWN_DUPLICATES[kind]
        found += [(label(table, n), c) for n, c in sorted(counts.items()) if c > (2 if n in allowed else 1)]
    return found


def check_unique(root: Path, *, printer: Callable[[str], None] = print) -> int:
    """Guardrail: 1 when two rows share an MA or REV number that is not a known historical pair."""
    found = duplicates(root)
    for ident, rows in found:
        printer(f"[registry-ids] {ident} is used by {rows} rows")
    if found:
        printer("[registry-ids] keep the row main already has: drop a second copy of the same row (archived twice, "
                "say), or renumber a different grant or REV with `python -m tools.next_registry_id ma|rev` and push")
        return 1
    printer("[registry-ids] MA and REV numbers are unique")
    return 0


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
