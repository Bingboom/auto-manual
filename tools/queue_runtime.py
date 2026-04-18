from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable


def slug_ref_token(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return text or "queue"


def format_command(cmd: list[str]) -> str:
    return subprocess.list2cmdline([str(part) for part in cmd])


def command_failure_message(cmd: list[str], stdout: str, stderr: str, returncode: int) -> str:
    for stream in (stderr, stdout):
        raw = stream.strip()
        if raw:
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = None
            if isinstance(payload, dict):
                error = payload.get("error")
                if isinstance(error, dict):
                    parts: list[str] = []
                    error_type = str(error.get("type") or "").strip()
                    error_code = str(error.get("code") or "").strip()
                    error_message = str(error.get("message") or "").strip()
                    if error_type:
                        parts.append(error_type)
                    if error_message:
                        parts.append(error_message)
                    if error_code and error_code not in error_message:
                        parts.append(f"code={error_code}")
                    detail = error.get("detail")
                    if isinstance(detail, dict):
                        violations = detail.get("permission_violations")
                        if isinstance(violations, list):
                            subjects = [
                                str(item.get("subject") or "").strip()
                                for item in violations
                                if isinstance(item, dict) and str(item.get("subject") or "").strip()
                            ]
                            if subjects:
                                parts.append("subjects=" + ",".join(subjects))
                    if parts:
                        return f"{' | '.join(parts)} (exit={returncode}, cmd={format_command(cmd)})"
        lines = [line.strip() for line in stream.splitlines() if line.strip()]
        if lines:
            return f"{lines[-1]} (exit={returncode}, cmd={format_command(cmd)})"
    return f"command failed with exit={returncode}: {format_command(cmd)}"


def run_command(
    cmd: list[str],
    *,
    cwd: Path,
    prefix: str,
    command_failure_message: Callable[[list[str], str, str, int], str] = command_failure_message,
) -> None:
    print(f"{prefix} {format_command(cmd)}")
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    if proc.returncode:
        raise RuntimeError(command_failure_message(cmd, proc.stdout or "", proc.stderr or "", proc.returncode))


def run_git(
    args: list[str],
    *,
    repo_root: Path,
    run_command: Callable[..., None],
) -> None:
    run_command(["git", *args], cwd=repo_root)


def worktree_dir_for_git_ref(*, repo_root: Path, git_ref: str) -> Path:
    return repo_root / ".tmp" / "process-build-queue-worktrees" / slug_ref_token(git_ref)


def remove_worktree(*, repo_root: Path, path: Path) -> None:
    if not path.exists():
        return
    proc = subprocess.run(
        ["git", "worktree", "remove", "--force", str(path)],
        cwd=str(repo_root),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode != 0 and path.exists():
        shutil.rmtree(path, ignore_errors=True)


def git_ref_exists(*, repo_root: Path, ref: str) -> bool:
    proc = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", ref],
        cwd=str(repo_root),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return proc.returncode == 0


def prepare_git_ref_worktree(
    *,
    repo_root: Path,
    git_ref: str,
    run_git: Callable[..., None],
    worktree_dir_for_git_ref: Callable[..., Path],
    remove_worktree: Callable[..., None],
    git_ref_exists: Callable[..., bool] = git_ref_exists,
    sleep: Callable[[float], None] = time.sleep,
) -> Path:
    def _fetch_args(*extra: str) -> list[str]:
        return [
            "-c",
            "http.version=HTTP/1.1",
            "-c",
            "http.schannelCheckRevoke=false",
            "fetch",
            "origin",
            *extra,
        ]

    def _is_retryable_fetch_error(message: str) -> bool:
        text = str(message or "").strip().lower()
        return any(
            marker in text
            for marker in (
                "could not resolve host",
                "failed to connect",
                "recv failure",
                "connection was reset",
                "timed out",
                "timeout",
            )
        )

    def _run_git_fetch(args: list[str]) -> None:
        delays = (1.0, 2.0, 4.0)
        for attempt in range(1, len(delays) + 2):
            try:
                run_git(args)
                return
            except RuntimeError as exc:
                if attempt > len(delays) or not _is_retryable_fetch_error(str(exc)):
                    raise
                delay = delays[attempt - 1]
                print(
                    f"[build-queue] WARNING git fetch failed; retrying in {delay:.1f}s "
                    f"({attempt}/{len(delays) + 1})..."
                )
                sleep(delay)

    branch_name = git_ref.strip()
    if not branch_name:
        raise RuntimeError("Git_ref is required when preparing a queue build worktree")
    base_ref = "origin/main"
    source_ref = f"origin/{branch_name}"
    cached_remote_ref = f"refs/remotes/origin/{branch_name}"
    local_branch_ref = f"refs/heads/{branch_name}"
    if git_ref_exists(repo_root=repo_root, ref=local_branch_ref):
        source_ref = branch_name
        print(
            f"[build-queue] Using local Git_ref branch {branch_name}",
            file=sys.stderr,
        )
    else:
        try:
            _run_git_fetch(_fetch_args("--prune"))
            _run_git_fetch(_fetch_args(f"refs/heads/{branch_name}:refs/remotes/origin/{branch_name}"))
        except RuntimeError:
            if git_ref_exists(repo_root=repo_root, ref=cached_remote_ref):
                print(
                    f"[build-queue] WARNING git fetch failed; reusing cached remote ref origin/{branch_name}",
                    file=sys.stderr,
                )
            else:
                raise
    worktree = worktree_dir_for_git_ref(repo_root=repo_root, git_ref=branch_name)
    remove_worktree(repo_root=repo_root, path=worktree)
    worktree.parent.mkdir(parents=True, exist_ok=True)
    run_git(["worktree", "add", "--force", "--detach", str(worktree), base_ref])
    # Review branches are content branches under docs/_review. Seed the worktree from
    # current main so queue builds use the latest toolchain, then overlay review content.
    run_git(["-C", str(worktree), "checkout", source_ref, "--", "docs/_review"])
    return worktree
