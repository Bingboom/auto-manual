#!/usr/bin/env python3
"""Pre-push advisory: warn when pushed commits touch derived surfaces.

Git-layer counterpart of ``.claude/hooks/derived_surface_guard.py``. The Claude
hook fires at the moment a build command dirties the tracked derived surfaces
(``docs/_build``, ``docs/index.rst``, ``docs/_review``); this check fires at the
last gate before publication — ``git push`` — and therefore covers EVERY agent
and human using the repo hooks (Claude Code, Codex, manual pushes), as long as
``git config core.hooksPath .githooks`` is set (AGENTS.md §8.2).

Advisory only, by design: legitimate branches DO commit derived surfaces
(review/* and backport/* own ``docs/_review``; asset/IDML branches submit
``docs/_build`` sources; RTD reads committed review bundles). Those branches
are exempted or the warning is informational — the check never fails a push,
mirroring the existing shared-template reminder in ``.githooks/pre-push``.

Input: the standard pre-push stdin lines
``<local_ref> <local_sha> <remote_ref> <remote_sha>``.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ZERO_SHA = "0" * 40
SURFACES = ("docs/_build", "docs/index.rst", "docs/_review")
EXEMPT_BRANCH_PREFIXES = ("review/", "backport/")


def _run_git(repo_root: Path, *args: str) -> str | None:
    """Run git, returning stdout, or None on any failure (advisory never breaks)."""
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except Exception:
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout


def _branch_name(local_ref: str) -> str | None:
    prefix = "refs/heads/"
    if local_ref.startswith(prefix):
        return local_ref[len(prefix) :]
    return None


def _diff_base(repo_root: Path, local_sha: str, remote_sha: str, base_branch: str) -> str | None:
    """Existing remote ref -> the remote sha; new branch -> merge-base with the base branch."""
    if remote_sha != ZERO_SHA:
        return remote_sha
    out = _run_git(repo_root, "merge-base", local_sha, f"origin/{base_branch}")
    return out.strip() if out else None


def _touched_surface_paths(repo_root: Path, base: str, local_sha: str) -> list[str]:
    out = _run_git(repo_root, "diff", "--name-only", f"{base}..{local_sha}", "--", *SURFACES)
    if not out:
        return []
    return [line for line in out.splitlines() if line.strip()]


def _surface_counts(paths: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in paths:
        for surface in SURFACES:
            if path == surface or path.startswith(surface + "/"):
                counts[surface] = counts.get(surface, 0) + 1
                break
    return counts


def check_push(lines: list[str], repo_root: Path, base_branch: str = "main") -> str | None:
    """Return the advisory message for the pushed refs, or None when silent."""
    findings: list[str] = []
    for line in lines:
        parts = line.split()
        if len(parts) != 4:
            continue
        local_ref, local_sha, _remote_ref, remote_sha = parts
        if local_sha == ZERO_SHA:  # ref deletion
            continue
        branch = _branch_name(local_ref)
        if branch is None:  # tags etc.
            continue
        if branch == base_branch or branch.startswith(EXEMPT_BRANCH_PREFIXES):
            continue
        base = _diff_base(repo_root, local_sha, remote_sha, base_branch)
        if base is None:
            continue
        paths = _touched_surface_paths(repo_root, base, local_sha)
        if not paths:
            continue
        counts = _surface_counts(paths)
        summary = ", ".join(f"{surface} ({n})" for surface, n in counts.items())
        findings.append(f"{branch}: {summary}")
    if not findings:
        return None
    detail = "; ".join(findings)
    return (
        "[derived-surface-guard] this push touches tracked derived surfaces — "
        f"{detail}. Intentional submissions (asset/IDML sources, review bundles) "
        "are fine; verification side-effects from `build.py check`/`sync-review` "
        "are not — restore them before the PR (AGENTS.md §6)."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="repository root")
    parser.add_argument("--base-branch", default="main", help="base branch name")
    args = parser.parse_args(argv)
    try:
        message = check_push(
            sys.stdin.read().splitlines(), Path(args.repo_root), args.base_branch
        )
    except Exception:
        return 0  # advisory: never break a push
    if message:
        print(message, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
