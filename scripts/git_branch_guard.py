#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence


ALLOWED_DIRTY_PREFIXES = (
    ".tmp/",
    "docs/_build/",
    "reports/version_tracking/",
    "reports/releases/",
)


class GitCommandError(RuntimeError):
    pass


def _print_error(message: str) -> None:
    print(message, file=sys.stderr)


def run_git(
    repo_root: Path,
    args: Sequence[str],
    *,
    capture_output: bool = True,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        capture_output=capture_output,
    )
    if check and completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "").strip()
        if message:
            raise GitCommandError(f"git {' '.join(args)} failed.\n{message}")
        raise GitCommandError(f"git {' '.join(args)} failed.")
    return completed


def git_stdout(repo_root: Path, args: Sequence[str]) -> str:
    return run_git(repo_root, args).stdout.strip()


def resolve_repo_root(raw_repo_root: str | None) -> Path:
    if raw_repo_root:
        return Path(raw_repo_root).resolve()
    return Path(git_stdout(Path.cwd(), ["rev-parse", "--show-toplevel"])).resolve()


def extract_status_path(status_line: str) -> str:
    if len(status_line) >= 4:
        path_text = status_line[3:].strip()
    else:
        path_text = status_line.strip()
    if " -> " in path_text:
        path_text = path_text.split(" -> ", 1)[1].strip()
    if path_text.startswith('"') and path_text.endswith('"') and len(path_text) >= 2:
        path_text = path_text[1:-1]
    return path_text.replace("\\", "/")


def is_allowed_dirty_path(repo_relative_path: str) -> bool:
    return any(repo_relative_path.startswith(prefix) for prefix in ALLOWED_DIRTY_PREFIXES)


def collect_disallowed_dirty_lines(status_lines: Sequence[str]) -> list[str]:
    dirty_lines: list[str] = []
    for line in status_lines:
        if not line.strip():
            continue
        if not is_allowed_dirty_path(extract_status_path(line)):
            dirty_lines.append(line)
    return dirty_lines


def get_disallowed_dirty_lines(repo_root: Path) -> list[str]:
    completed = run_git(
        repo_root,
        ["status", "--porcelain=v1", "--untracked-files=all"],
    )
    return collect_disallowed_dirty_lines(completed.stdout.splitlines())


def ensure_branch_absent(repo_root: Path, branch_name: str, remote: str) -> None:
    local = run_git(
        repo_root,
        ["show-ref", "--verify", "--quiet", f"refs/heads/{branch_name}"],
        capture_output=False,
        check=False,
    )
    if local.returncode == 0:
        raise RuntimeError(f"Local branch '{branch_name}' already exists.")

    remote_ref = run_git(
        repo_root,
        ["show-ref", "--verify", "--quiet", f"refs/remotes/{remote}/{branch_name}"],
        capture_output=False,
        check=False,
    )
    if remote_ref.returncode == 0:
        raise RuntimeError(f"Remote branch '{remote}/{branch_name}' already exists.")


def current_branch(repo_root: Path) -> str:
    completed = run_git(
        repo_root,
        ["symbolic-ref", "--quiet", "--short", "HEAD"],
        check=False,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def ensure_remote_base_ref(repo_root: Path, remote: str, base_branch: str) -> str:
    run_git(repo_root, ["fetch", remote, base_branch], capture_output=False)
    remote_base_ref = f"{remote}/{base_branch}"
    remote_ref = run_git(
        repo_root,
        ["rev-parse", "--verify", "--quiet", remote_base_ref],
        check=False,
    )
    if remote_ref.returncode != 0:
        raise RuntimeError(
            f"Missing {remote_base_ref}; cannot verify that this branch starts from the latest base."
        )
    return remote_base_ref


def ensure_local_base_branch(repo_root: Path, remote_base_ref: str, base_branch: str) -> None:
    local_ref = run_git(
        repo_root,
        ["show-ref", "--verify", "--quiet", f"refs/heads/{base_branch}"],
        capture_output=False,
        check=False,
    )
    if local_ref.returncode == 0:
        run_git(repo_root, ["switch", base_branch], capture_output=False)
        return
    run_git(repo_root, ["switch", "--track", "-c", base_branch, remote_base_ref], capture_output=False)


def start_branch_command(args: argparse.Namespace) -> int:
    repo_root = resolve_repo_root(args.repo_root)
    if not args.allow_dirty:
        dirty_lines = get_disallowed_dirty_lines(repo_root)
        if dirty_lines:
            raise RuntimeError(
                "Refusing to create a new branch from a dirty worktree. "
                "Commit, stash, or clean these paths first:\n" + "\n".join(dirty_lines)
            )

    remote_base_ref = ensure_remote_base_ref(repo_root, args.remote, args.base_branch)
    ensure_branch_absent(repo_root, args.branch, args.remote)
    ensure_local_base_branch(repo_root, remote_base_ref, args.base_branch)
    run_git(repo_root, ["pull", "--ff-only", args.remote, args.base_branch], capture_output=False)
    run_git(repo_root, ["switch", "-c", args.branch], capture_output=False)

    head_sha = git_stdout(repo_root, ["rev-parse", "--short", "HEAD"])
    print(f"[start-branch] Created {args.branch} from {remote_base_ref} at {head_sha}")
    return 0


def pre_push_command(args: argparse.Namespace) -> int:
    repo_root = resolve_repo_root(args.repo_root)
    branch_name = current_branch(repo_root)
    if not branch_name or branch_name in {"main", "master"}:
        return 0

    if os.environ.get("AUTO_MANUAL_SKIP_BRANCH_BASE_CHECK") == "1":
        return 0

    remote = args.remote or "origin"
    base_branch = args.base_branch or os.environ.get("AUTO_MANUAL_BASE_BRANCH", "main")

    try:
        remote_base_ref = ensure_remote_base_ref(repo_root, remote, base_branch)
    except RuntimeError as exc:
        message = str(exc)
        if message.startswith("git fetch"):
            _print_error(f"[pre-push] Unable to fetch {remote}/{base_branch} to verify the branch base.")
            _print_error("[pre-push] Push blocked. Retry after network/auth is fixed, or bypass intentionally with --no-verify.")
            return 1
        _print_error(f"[pre-push] {message}")
        _print_error("[pre-push] Push blocked. Check the remote/base-branch setting first.")
        return 1

    merge_base = git_stdout(repo_root, ["merge-base", "HEAD", remote_base_ref])
    remote_base_sha = git_stdout(repo_root, ["rev-parse", remote_base_ref])
    if merge_base != remote_base_sha:
        _print_error(f"[pre-push] Current branch does not contain the latest {remote_base_ref}.")
        _print_error("[pre-push] Start new work with:")
        _print_error("[pre-push]   powershell -ExecutionPolicy Bypass -File scripts/start_branch.ps1 codex/<topic>")
        _print_error("[pre-push]   ./scripts/start_branch.sh codex/<topic>")
        _print_error("[pre-push] Or update this branch before pushing:")
        _print_error(f"[pre-push]   git fetch {remote}")
        _print_error(f"[pre-push]   git rebase {remote_base_ref}")
        _print_error("[pre-push] Intentional bypass: git push --no-verify")
        return 1

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cross-platform branch freshness guard helpers.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start-branch", help="Create a new branch from the latest remote base branch.")
    start.add_argument("--repo-root")
    start.add_argument("--branch", required=True)
    start.add_argument("--remote", default="origin")
    start.add_argument("--base-branch", default="main")
    start.add_argument("--allow-dirty", action="store_true")
    start.set_defaults(func=start_branch_command)

    pre_push = subparsers.add_parser("pre-push", help="Block pushes from branches that do not contain the latest base.")
    pre_push.add_argument("--repo-root")
    pre_push.add_argument("--remote", default="origin")
    pre_push.add_argument("--base-branch", default=os.environ.get("AUTO_MANUAL_BASE_BRANCH", "main"))
    pre_push.set_defaults(func=pre_push_command)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (GitCommandError, RuntimeError) as exc:
        _print_error(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
