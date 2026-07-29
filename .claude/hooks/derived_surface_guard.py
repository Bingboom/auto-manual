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
- Checks ``git status --porcelain`` for the three derived surfaces.
- Clean, unmatched, or any internal error -> exit 0, silent.
- Dirty -> exit 2 with a short reminder on stderr (PostToolUse exit 2 feeds
  stderr back to the agent; the tool already ran, nothing is blocked).

Owner: repo maintainers (added with the hooks first wave, 2026-07).
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

TRIGGER = re.compile(r"build\.py\s+(?:check|sync-review|publish)\b")
SURFACES = ("docs/_build", "docs/index.rst", "docs/_review")


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

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or "."
    try:
        out = subprocess.run(
            ["git", "-C", project_dir, "status", "--porcelain", "--", *SURFACES],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        ).stdout
    except Exception:
        return 0

    dirty = [line[3:] for line in out.splitlines() if line.strip()]
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
        "[derived-surface-guard] the build command left tracked derived surfaces "
        f"dirty: {summary}. If these are verification side-effects, restore them "
        "before committing (e.g. `git restore docs/_build docs/index.rst`; review "
        "`git diff docs/_review` — token rotations from sync-review are not review "
        "edits) and keep them out of unrelated PRs (AGENTS.md §6).",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
