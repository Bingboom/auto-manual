from __future__ import annotations

import os
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, MutableMapping

SOURCE_DATE_EPOCH_ENV = "SOURCE_DATE_EPOCH"
REPRODUCIBILITY_SCHEMA_VERSION = 1
REPRODUCIBILITY_POLICY = "git-commit-source-date-epoch-v1"


def _run_git(repo_root: Path, args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(repo_root),
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = ""
        if isinstance(exc, subprocess.CalledProcessError):
            detail = str(exc.stderr or exc.stdout or "").strip()
        suffix = f": {detail}" if detail else ""
        raise RuntimeError(f"git {' '.join(args)} failed{suffix}") from exc
    return (result.stdout or "").strip()


def git_commit_epoch(repo_root: Path, git_ref: str = "HEAD") -> int:
    raw = _run_git(repo_root, ["show", "-s", "--format=%ct", git_ref])
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"Git commit {git_ref!r} did not provide a Unix timestamp") from exc
    if value < 0:
        raise RuntimeError(f"Git commit {git_ref!r} has an invalid negative timestamp")
    return value


def source_date_epoch_from_environment(
    environ: MutableMapping[str, str] | None = None,
    *,
    required: bool = False,
) -> int | None:
    env = environ if environ is not None else os.environ
    raw = str(env.get(SOURCE_DATE_EPOCH_ENV, "")).strip()
    if not raw:
        if required:
            raise RuntimeError(
                f"{SOURCE_DATE_EPOCH_ENV} is required for a versioned release; "
                "run the release through 'python build.py publish --version ...'"
            )
        return None
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{SOURCE_DATE_EPOCH_ENV} must be an integer Unix timestamp") from exc
    if value < 0:
        raise RuntimeError(f"{SOURCE_DATE_EPOCH_ENV} must not be negative")
    return value


def ensure_tracked_worktree_clean(repo_root: Path) -> None:
    status = _run_git(repo_root, ["status", "--porcelain", "--untracked-files=no"])
    if status:
        paths = []
        for line in status.splitlines():
            parts = line.split(maxsplit=1)
            paths.append(parts[1] if len(parts) == 2 else line)
        preview = ", ".join(paths[:5])
        if len(paths) > 5:
            preview += f", ... (+{len(paths) - 5})"
        raise RuntimeError(
            "versioned publish requires a clean tracked worktree so git_sha can rebuild the release; "
            f"commit or restore these paths first: {preview}"
        )


@contextmanager
def deterministic_release_environment(
    *,
    repo_root: Path,
    git_ref: str = "HEAD",
    environ: MutableMapping[str, str] | None = None,
    require_clean: bool = False,
) -> Iterator[int]:
    env = environ if environ is not None else os.environ
    if require_clean:
        ensure_tracked_worktree_clean(repo_root)
    epoch = git_commit_epoch(repo_root, git_ref)
    sentinel = object()
    previous: object = env.get(SOURCE_DATE_EPOCH_ENV, sentinel)
    env[SOURCE_DATE_EPOCH_ENV] = str(epoch)
    try:
        yield epoch
    finally:
        if previous is sentinel:
            env.pop(SOURCE_DATE_EPOCH_ENV, None)
        else:
            env[SOURCE_DATE_EPOCH_ENV] = str(previous)


def build_reproducibility_record(source_date_epoch: int | None) -> dict[str, object]:
    return {
        "schema_version": REPRODUCIBILITY_SCHEMA_VERSION,
        "policy": REPRODUCIBILITY_POLICY,
        "source_date_epoch": source_date_epoch,
        "artifact_contract": "sha256-byte-equivalence",
        "artifacts": ["word_output", "md_output", "pdf_output"],
    }
