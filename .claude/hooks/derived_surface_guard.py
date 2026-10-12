#!/usr/bin/env python3
"""PostToolUse(Bash) hook: warn when a build command dirtied derived surfaces.

Problem this guards: verification commands overwrite git-TRACKED derived
surfaces — ``build.py check`` rewrites ``docs/_build`` products and
``docs/index.rst``; its sync-review step rotates Feishu attachment tokens
into ``docs/_review`` — and those side-effect diffs have repeatedly leaked
into unrelated PRs (AGENTS.md §6 working-tree safety).

Behavior (deliberately narrow, per .claude/hooks/README.md):

- Reads the PostToolUse JSON from stdin; acts ONLY when the Bash command
  that just ran matches ``build.py {check|sync-review|publish}``.
- Resolves the checkout the build ran in: ``cd`` steps before the build
  (``&&``/``;``-joined, absolute or relative, optionally inside ``( … )``) and
  a directory in the ``build.py`` path itself, starting from the hook's
  ``cwd``. Agents work in per-window worktrees while the project directory is
  the shared primary checkout, so checking the project directory reported
  another window's files — and the old advice to restore them destroyed work.
- Checks ``git status --porcelain`` for the three derived surfaces in that
  checkout only, and names the checkout in the message.
- Clean, unmatched, or any internal error -> exit 0, silent.
- Dirty -> exit 2 with a short reminder on stderr (PostToolUse exit 2 feeds
  stderr back to the agent; the tool already ran, nothing is blocked).

Owner: repo maintainers (added with the hooks first wave, 2026-07).
Tests: tests/test_derived_surface_guard.py.
Manual test:
  echo '{"tool_name":"Bash","tool_input":{"command":"python build.py check"}}' \
    | CLAUDE_PROJECT_DIR=. python3 .claude/hooks/derived_surface_guard.py
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

TRIGGER = re.compile(r"build\.py\s+(?:check|sync-review|publish)\b")
SURFACES = ("docs/_build", "docs/index.rst", "docs/_review")
_SEGMENTS = re.compile(r"&&|\|\||;|\n")
_CD = re.compile(r"""^\s*\(?\s*cd\s+(?P<dir>"[^"]+"|'[^']+'|[^\s;&|()]+)\s*\)?\s*$""")
_BUILD = re.compile(r"""(?P<script>"[^"]*build\.py"|'[^']*build\.py'|[^\s"';&|()]*build\.py)\s+(?:check|sync-review|publish)\b""")


def _path(raw: str) -> Path:
    return Path(os.path.expanduser(os.path.expandvars(raw.strip("\"'"))))


def build_directory(command: str, start: Path) -> Path:
    """The directory the build ran from: follow ``cd`` steps, then the script's own directory."""
    cwd = start
    for segment in _SEGMENTS.split(command):
        cd = _CD.match(segment)
        if cd:
            target = _path(cd.group("dir"))
            cwd = target if target.is_absolute() else cwd / target
            continue
        build = _BUILD.search(segment)
        if build:
            script_dir = _path(build.group("script")).parent
            if str(script_dir) not in ("", "."):
                return script_dir if script_dir.is_absolute() else cwd / script_dir
            return cwd
    return cwd


def _git(directory: Path, *args: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(directory), *args],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except Exception:
        return None
    return completed.stdout if completed.returncode == 0 else None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    if payload.get("tool_name") != "Bash":
        return 0
    command = str((payload.get("tool_input") or {}).get("command") or "")
    if not TRIGGER.search(command):
        return 0

    start = Path(payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or ".")
    checkout = (_git(build_directory(command, start), "rev-parse", "--show-toplevel") or "").strip()
    if not checkout:
        return 0
    out = _git(Path(checkout), "status", "--porcelain", "--", *SURFACES)
    dirty = [line[3:] for line in (out or "").splitlines() if line.strip()]
    if not dirty:
        return 0

    counts: dict[str, int] = {}
    for path in dirty:
        for surface in SURFACES:
            if path == surface or path.startswith(surface + "/"):
                counts[surface] = counts.get(surface, 0) + 1
                break
    summary = ", ".join(f"{surface} ({n})" for surface, n in counts.items())
    print(
        f"[derived-surface-guard] tracked derived surfaces are dirty in {checkout}: {summary}. "
        "Restore only what this build changed, and keep it out of unrelated PRs (AGENTS.md §6): "
        f"compare `git -C {checkout} status` with what you expected, then restore those paths. "
        "Files that were already dirty before this command may belong to another window: leave them. "
        "Token rotations from sync-review in docs/_review are not review edits.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
