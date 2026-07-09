#!/usr/bin/env python3
"""Advisory guardrail: shared template / manifest edits vs in-flight review branches.

A review branch (``review/<MODEL>-<REGION>``) holds a *frozen* derivative under
``docs/_review/...`` plus a mirrored copy of the shared source. Editing a shared
JP/region template (``docs/templates/page_<lang>/**``) or a manual manifest
(``docs/manifests/manual_<lang>.yaml``) on ``main`` does NOT reach those open
review branches until each one inherits the change and is rebuilt — so the
in-review docs silently drift from the templates (2026-07-08 UPS/安全須知 drift).

This check is a **notice, not an auto-refresh**: a full ``review-init`` /
``--refresh-review`` would clobber the reviewers' authored edits, so the safe
path is a human-run ``sync-review`` (merge_params) that preserves authored
content — except on ``|PLACEHOLDER|``-bearing lines, which merge_params rewrites
from the template and can therefore overwrite an authored edit on that same line.

Exit code is 0 by default (advisory). Pass ``--strict`` to exit 1 when the
change touches shared source AND open review branches exist.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Shared-source paths whose edits drift from in-review branch derivatives.
# Shared source that drifts from in-review derivatives: ALL templates + manifests.
_SHARED_RE = re.compile(r"^docs/templates/.+$|^docs/manifests/.+\.ya?ml$")
# A lang/region token narrows the blast radius; paths without one (page_shared/,
# snippets/, word_template/, contracts/, top-level *_template.rst, …) are
# region-agnostic and affect every open review branch.
_LANG_TOKEN_RES = (
    re.compile(r"^docs/templates/page_([a-z0-9-]+)/"),
    re.compile(r"^docs/templates/recipes/([a-z0-9-]+)/"),
    re.compile(r"^docs/manifests/manual_([a-z0-9-]+)\.ya?ml$"),
)
_ALL_SCOPE = "*"  # region-agnostic shared source
_REVIEW_BRANCH_RE = re.compile(r"^review/.+-([A-Za-z0-9]+)$")


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=False
    )


def changed_files(base: str, cwd: Path) -> list[str]:
    """Files changed relative to ``base`` (merge-base diff, then plain diff)."""
    for diff_args in (["diff", "--name-only", f"{base}...HEAD"], ["diff", "--name-only", base]):
        proc = _git(diff_args, cwd)
        if proc.returncode == 0:
            return [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    return []


def scope_hits(paths: list[str]) -> dict[str, list[str]]:
    """Map each shared-source scope token to the paths that touched it.

    Token is a lang/region (``jp``, ``us-en``, …) when the path carries one, else
    ``*`` (region-agnostic — affects every review branch).
    """
    hits: dict[str, list[str]] = {}
    for path in paths:
        if not _SHARED_RE.match(path):
            continue
        token = _ALL_SCOPE
        for pattern in _LANG_TOKEN_RES:
            match = pattern.match(path)
            if match:
                token = match.group(1)
                break
        if token == "shared":  # page_shared/ is region-agnostic, not a lang
            token = _ALL_SCOPE
        hits.setdefault(token, []).append(path)
    return hits


def open_review_branches(remote: str, cwd: Path) -> list[str] | None:
    """Return ``review/*`` branch names on ``remote``, or None if unreachable."""
    proc = _git(["ls-remote", "--heads", remote, "refs/heads/review/*"], cwd)
    if proc.returncode != 0:
        return None
    branches: list[str] = []
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].startswith("refs/heads/"):
            branches.append(parts[1][len("refs/heads/") :])
    return sorted(branches)


def region_of(branch: str) -> str | None:
    """``review/JE-1000F-JP`` -> ``JP``."""
    match = _REVIEW_BRANCH_RE.match(branch)
    return match.group(1).upper() if match else None


def token_matches_region(token: str, region: str | None) -> bool:
    """Loose match: token ``jp`` / ``jp-...`` matches region ``JP``."""
    if not region:
        return False
    primary = token.upper().split("-", 1)[0]
    return region == primary or region.startswith(primary)


def build_report(hits: dict[str, list[str]], branches: list[str] | None) -> tuple[str, bool]:
    """Return (message, has_affected_branches)."""
    lines = [
        "[review-branch-sync] NOTICE: shared template/manifest edits detected.",
        "  In-flight review branches hold FROZEN derivatives + a mirrored manifest;",
        "  they will NOT pick up these edits until each is rebased on the updated",
        "  source and rebuilt. Refresh with `sync-review` (merge_params, preserves",
        "  authored edits) — NOT `--refresh-review` (clobbers authored edits).",
        "  Then check any |PLACEHOLDER|-bearing line for authored edits it may overwrite.",
        "",
        "  Shared source touched:",
    ]
    for token in sorted(hits):
        label = "ALL (region-agnostic)" if token == _ALL_SCOPE else token.upper()
        for path in sorted(hits[token]):
            lines.append(f"    - {path}  (scope: {label})")

    all_scope = _ALL_SCOPE in hits
    region_tokens = set(hits) - {_ALL_SCOPE}
    affected = False
    if branches is None:
        lines += ["", "  Open review branches: (remote unreachable — list them manually)"]
    elif not branches:
        lines += ["", "  Open review branches: none found."]
    else:
        lines += ["", "  Open review branches to consider refreshing:"]
        for branch in branches:
            region = region_of(branch)
            match = all_scope or any(token_matches_region(tok, region) for tok in region_tokens)
            flag = "  <-- likely affected" if match else ""
            affected = affected or match
            lines.append(f"    - {branch}{flag}")
    return "\n".join(lines), affected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="origin/main", help="base ref to diff against")
    parser.add_argument("--remote", default="hello-docs", help="remote hosting review/* branches")
    parser.add_argument("--repo-root", default=".", help="repo root")
    parser.add_argument("--strict", action="store_true", help="exit 1 when affected branches exist")
    args = parser.parse_args(argv)

    cwd = Path(args.repo_root).resolve()
    hits = scope_hits(changed_files(args.base, cwd))
    if not hits:
        print("[review-branch-sync] OK: no shared template/manifest edits.")
        return 0

    branches = open_review_branches(args.remote, cwd)
    message, affected = build_report(hits, branches)
    print(message)
    return 1 if (args.strict and affected) else 0


if __name__ == "__main__":
    sys.exit(main())
