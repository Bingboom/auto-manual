from __future__ import annotations

import os
import re
import subprocess
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, MutableMapping

SOURCE_DATE_EPOCH_ENV = "SOURCE_DATE_EPOCH"
REVIEW_OVERLAY_REF_ENV = "AUTO_MANUAL_REVIEW_OVERLAY_REF"
REVIEW_OVERLAY_SHA_ENV = "AUTO_MANUAL_REVIEW_OVERLAY_SHA"
REVIEW_OVERLAY_PATH_ENV = "AUTO_MANUAL_REVIEW_OVERLAY_PATH"
REPRODUCIBILITY_SCHEMA_VERSION = 1
REPRODUCIBILITY_POLICY = "git-commit-source-date-epoch-v1"
_FULL_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class ReviewOverlayProvenance:
    source_ref: str
    source_sha: str
    target_path: str
    tree_sha: str

    def as_record(self) -> dict[str, str]:
        return {
            "source_ref": self.source_ref,
            "source_sha": self.source_sha,
            "target_path": self.target_path,
            "tree_sha": self.tree_sha,
        }


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


def _review_overlay_target(repo_root: Path, raw: str) -> tuple[str, Path]:
    relative = Path(raw)
    if relative.is_absolute():
        raise RuntimeError(f"review overlay path must be repository-relative: {raw}")
    normalized = relative.as_posix().strip("/")
    required_prefix = "docs/_review/"
    if not normalized.startswith(required_prefix) or normalized == required_prefix.rstrip("/"):
        raise RuntimeError(
            "review overlay path must target one docs/_review/<model>/<region> subtree"
        )
    resolved = (repo_root / normalized).resolve(strict=False)
    try:
        resolved.relative_to(repo_root.resolve(strict=False))
    except ValueError as exc:
        raise RuntimeError(f"review overlay path escapes the repository: {raw}") from exc
    return normalized, resolved


def _validate_review_overlay_tree(
    repo_root: Path,
    *,
    source_sha: str,
    target_path: str,
    target_root: Path,
) -> str:
    _run_git(repo_root, ["cat-file", "-e", f"{source_sha}^{{commit}}"])
    tree_sha = _run_git(repo_root, ["rev-parse", f"{source_sha}:{target_path}"])
    raw_tree = _run_git(
        repo_root,
        ["ls-tree", "-r", "--full-tree", source_sha, "--", target_path],
    )
    expected: dict[str, str] = {}
    for line in raw_tree.splitlines():
        metadata, separator, path = line.partition("\t")
        parts = metadata.split()
        if not separator or len(parts) != 3 or parts[1] != "blob":
            raise RuntimeError(f"review overlay contains an unsupported Git tree entry: {line}")
        expected[path] = parts[2]

    actual_paths: set[str] = set()
    if target_root.exists():
        for candidate in target_root.rglob("*"):
            if candidate.is_symlink():
                raise RuntimeError(f"review overlay must not contain symlinks: {candidate}")
            if candidate.is_file():
                actual_paths.add(
                    candidate.resolve(strict=False)
                    .relative_to(repo_root.resolve(strict=False))
                    .as_posix()
                )
    if actual_paths != set(expected):
        missing = sorted(set(expected) - actual_paths)
        extra = sorted(actual_paths - set(expected))
        raise RuntimeError(
            "review overlay files do not match the recorded source commit; "
            f"missing={missing[:3]} extra={extra[:3]}"
        )
    for relative_path, expected_blob in expected.items():
        actual_blob = _run_git(repo_root, ["hash-object", str(repo_root / relative_path)])
        if actual_blob != expected_blob:
            raise RuntimeError(
                "review overlay bytes do not match the recorded source commit: "
                f"{relative_path}"
            )
    return tree_sha


def review_overlay_from_environment(
    repo_root: Path,
    environ: MutableMapping[str, str] | None = None,
) -> ReviewOverlayProvenance | None:
    env = environ if environ is not None else os.environ
    values = {
        "source_ref": str(env.get(REVIEW_OVERLAY_REF_ENV, "")).strip(),
        "source_sha": str(env.get(REVIEW_OVERLAY_SHA_ENV, "")).strip().lower(),
        "target_path": str(env.get(REVIEW_OVERLAY_PATH_ENV, "")).strip(),
    }
    populated = [name for name, value in values.items() if value]
    if not populated:
        return None
    if len(populated) != len(values):
        raise RuntimeError(
            "review overlay provenance requires ref, full SHA, and target path together"
        )
    if not _FULL_GIT_SHA_RE.fullmatch(values["source_sha"]):
        raise RuntimeError("review overlay source SHA must be a full 40-character Git commit")
    target_path, target_root = _review_overlay_target(repo_root, values["target_path"])
    tree_sha = _validate_review_overlay_tree(
        repo_root,
        source_sha=values["source_sha"],
        target_path=target_path,
        target_root=target_root,
    )
    return ReviewOverlayProvenance(
        source_ref=values["source_ref"],
        source_sha=values["source_sha"],
        target_path=target_path,
        tree_sha=tree_sha,
    )


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


def ensure_tracked_worktree_clean(
    repo_root: Path,
    *,
    review_overlay: ReviewOverlayProvenance | None = None,
) -> None:
    status = _run_git(repo_root, ["status", "--porcelain", "--untracked-files=no"])
    if not status:
        return
    paths = []
    for line in status.splitlines():
        parts = line.split(maxsplit=1)
        raw_path = parts[1] if len(parts) == 2 else line
        paths.extend(part.strip() for part in raw_path.split(" -> ") if part.strip())
    if review_overlay is not None:
        target = review_overlay.target_path.rstrip("/")
        unexpected = [
            path
            for path in paths
            if path != target and not path.startswith(f"{target}/")
        ]
        if not unexpected:
            return
        paths = unexpected
    if paths:
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
        review_overlay = review_overlay_from_environment(repo_root, env)
        ensure_tracked_worktree_clean(repo_root, review_overlay=review_overlay)
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


def build_reproducibility_record(
    source_date_epoch: int | None,
    *,
    review_overlay: ReviewOverlayProvenance | None = None,
) -> dict[str, object]:
    record: dict[str, object] = {
        "schema_version": REPRODUCIBILITY_SCHEMA_VERSION,
        "policy": REPRODUCIBILITY_POLICY,
        "source_date_epoch": source_date_epoch,
        "artifact_contract": "sha256-byte-equivalence",
        "artifacts": ["word_output", "md_output", "pdf_output"],
    }
    if review_overlay is not None:
        record["review_overlay"] = review_overlay.as_record()
    return record
