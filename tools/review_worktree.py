"""Git-worktree helpers for branch-targeted cloud-doc backport.

A target's ``docs/_review/<model>/<region>/`` tree lives only on its review
branch, so a backport must run in a worktree of that branch. This module owns:

- **the template guard** (``derive_review_source_rel``): the backport source path
  is DERIVED from the resolved review dir + the page, never accepted as an
  arbitrary path — so a backport can only ever write under
  ``docs/_review/<model>/<region>/`` and is hard-refused if it would resolve to
  ``docs/templates/`` or ``docs/_build/`` (the bug where BlockClaw guessed the
  shared template);
- **worktree resolution** (pure ``parse_worktree_for_ref`` / ``worktree_dirname``)
  and ``ensure_review_worktree`` (idempotent: reuse an existing worktree for the
  branch, else fetch + ``git worktree add``).

``ensure_review_worktree`` takes an injectable ``run_git`` so the git orchestration
is unit-testable without a real repo.
"""

from __future__ import annotations

import subprocess
from pathlib import Path, PurePosixPath
from typing import Callable

RunGit = Callable[[list[str]], str]


def worktree_dirname(git_ref: str) -> str:
    """Filesystem-safe directory name for a review branch's worktree."""
    safe = "".join(ch if (ch.isalnum() or ch in "-_.") else "-" for ch in str(git_ref).strip())
    return f"review-{safe}".strip("-") or "review"


def derive_review_source_rel(review_dir: str, page: str) -> str:
    """Derive the repo-relative ``docs/_review/...`` source path for a backport.

    The path is COMPUTED from the resolver's ``review_dir`` + the page; it is
    never an arbitrary caller path. Hard-refuses anything that would escape the
    review dir or land in ``templates`` / ``_build`` — the structural guard that
    a backport can only write the review derivative, never the shared template.
    """
    review_dir = str(review_dir or "").strip().strip("/")
    if not review_dir:
        raise RuntimeError("review_dir is required")
    page = str(page or "").strip()
    if not page:
        raise RuntimeError("page is required")
    candidate = PurePosixPath(page)
    if candidate.is_absolute():
        raise RuntimeError(f"page must be a relative path, got: {page}")
    if ".." in candidate.parts:
        raise RuntimeError(f"page must not contain '..': {page}")
    parts = candidate.parts
    if parts[:1] == ("docs",):
        rel = str(candidate)
        if not (rel == review_dir or rel.startswith(review_dir + "/")):
            raise RuntimeError(f"page {rel} is outside the resolved review dir {review_dir}")
    elif parts[:1] == ("page",):
        rel = f"{review_dir}/{candidate}"
    else:
        rel = f"{review_dir}/page/{candidate}"
    rel_parts = PurePosixPath(rel).parts
    if "templates" in rel_parts or "_build" in rel_parts:
        raise RuntimeError(f"backport must target docs/_review, never templates/_build: {rel}")
    if "_review" not in rel_parts:
        raise RuntimeError(f"resolved path is not under docs/_review: {rel}")
    if not rel.endswith(".rst"):
        raise RuntimeError(f"review source must be an .rst file: {rel}")
    return rel


def parse_worktree_for_ref(porcelain: str, git_ref: str) -> str | None:
    """Return the worktree path checked out on ``git_ref`` from
    ``git worktree list --porcelain`` output, or ``None``."""
    target = f"refs/heads/{git_ref}"
    for block in str(porcelain or "").split("\n\n"):
        path = None
        branch = None
        for line in block.strip().splitlines():
            if line.startswith("worktree "):
                path = line[len("worktree "):].strip()
            elif line.startswith("branch "):
                branch = line[len("branch "):].strip()
        if path and branch == target:
            return path
    return None


def _default_run_git(repo_root: Path, git_bin: str) -> RunGit:
    def run_git(args: list[str]) -> str:
        result = subprocess.run(
            [git_bin, *args], cwd=str(repo_root), capture_output=True, text=True
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
        return result.stdout.strip()
    return run_git


def ensure_review_worktree(
    git_ref: str,
    *,
    worktrees_root: str | Path,
    repo_root: str | Path = ".",
    remote: str = "origin",
    git_bin: str = "git",
    run_git: RunGit | None = None,
    sparse_paths: list[str] | None = None,
) -> str:
    """Return the path to a worktree checked out on ``git_ref``, creating it if
    needed (idempotent). Fetches ``remote/git_ref`` before adding the worktree.

    When ``sparse_paths`` is given the checkout is shrunk to a **cone-mode
    sparse-checkout** limited to those directories (e.g.
    ``docs/_review/<model>/<region>``), so it keeps only the review tree (plus the
    small cone of ancestor root files) instead of the whole repo. An
    already-existing worktree is reused as-is and not re-sparsified.
    """
    if not str(git_ref or "").strip():
        raise RuntimeError("git_ref is required")
    runner = run_git or _default_run_git(Path(repo_root), git_bin)
    existing = parse_worktree_for_ref(runner(["worktree", "list", "--porcelain"]), git_ref)
    if existing:
        return existing
    runner(["fetch", remote, git_ref])
    worktrees_root = Path(worktrees_root)
    worktrees_root.mkdir(parents=True, exist_ok=True)
    path = worktrees_root / worktree_dirname(git_ref)
    try:
        runner(["worktree", "add", str(path), git_ref])
    except RuntimeError:
        # Local branch absent / not DWIM-able: attach detached from the remote ref.
        runner(["worktree", "add", "--detach", str(path), f"{remote}/{git_ref}"])
    if sparse_paths:
        # Shrink the full checkout to a cone-mode sparse-checkout of just the review
        # tree (+ the small cone of ancestor root files) — e.g. 250M -> ~1M.
        runner(["-C", str(path), "sparse-checkout", "set", "--cone", *sparse_paths])
    return str(path)
