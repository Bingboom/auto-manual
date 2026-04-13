#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import git_branch_guard as branch_guard


class OpenClawGitGuardError(RuntimeError):
    pass


def emit_payload(payload: dict[str, Any]) -> None:
    text = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode("utf-8"))
        sys.stdout.buffer.write(b"\n")
        sys.stdout.flush()


def current_head_sha(repo_root: Path) -> str:
    return branch_guard.git_stdout(repo_root, ["rev-parse", "--short", "HEAD"])


def tracking_branch(repo_root: Path) -> str:
    completed = branch_guard.run_git(
        repo_root,
        ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"],
        check=False,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def get_status_lines(repo_root: Path) -> list[str]:
    completed = branch_guard.run_git(
        repo_root,
        ["status", "--porcelain=v1", "--untracked-files=all"],
    )
    return [line for line in completed.stdout.splitlines() if line.strip()]


def status_payload(repo_root: Path) -> dict[str, Any]:
    status_lines = get_status_lines(repo_root)
    allowed_dirty_lines = [
        line
        for line in status_lines
        if branch_guard.is_allowed_dirty_path(branch_guard.extract_status_path(line))
    ]
    disallowed_dirty_lines = branch_guard.collect_disallowed_dirty_lines(status_lines)
    return {
        "ok": True,
        "command": "status",
        "repo_root": repo_root.as_posix(),
        "branch": branch_guard.current_branch(repo_root),
        "head_sha": current_head_sha(repo_root),
        "tracking_branch": tracking_branch(repo_root),
        "dirty": bool(status_lines),
        "allowed_dirty_lines": allowed_dirty_lines,
        "disallowed_dirty_lines": disallowed_dirty_lines,
        "safe_to_switch": not disallowed_dirty_lines,
    }


def ensure_safe_worktree(repo_root: Path) -> None:
    disallowed_dirty_lines = branch_guard.get_disallowed_dirty_lines(repo_root)
    if disallowed_dirty_lines:
        raise OpenClawGitGuardError(
            "Refusing to switch branches from a dirty worktree. "
            "Commit, stash, or clean these paths first:\n" + "\n".join(disallowed_dirty_lines)
        )


def ensure_valid_branch_name(repo_root: Path, branch_name: str) -> None:
    completed = branch_guard.run_git(
        repo_root,
        ["check-ref-format", "--branch", branch_name],
        check=False,
    )
    if completed.returncode != 0:
        raise OpenClawGitGuardError(f"Invalid branch name '{branch_name}'.")


def local_branch_exists(repo_root: Path, branch_name: str) -> bool:
    completed = branch_guard.run_git(
        repo_root,
        ["show-ref", "--verify", "--quiet", f"refs/heads/{branch_name}"],
        capture_output=False,
        check=False,
    )
    return completed.returncode == 0


def remote_branch_exists(repo_root: Path, remote: str, branch_name: str) -> bool:
    completed = branch_guard.run_git(
        repo_root,
        ["show-ref", "--verify", "--quiet", f"refs/remotes/{remote}/{branch_name}"],
        capture_output=False,
        check=False,
    )
    return completed.returncode == 0


def switch_command(args: argparse.Namespace) -> int:
    repo_root = branch_guard.resolve_repo_root(args.repo_root)
    ensure_safe_worktree(repo_root)
    ensure_valid_branch_name(repo_root, args.branch)

    before_branch = branch_guard.current_branch(repo_root)
    before_sha = current_head_sha(repo_root)

    branch_guard.run_git(repo_root, ["fetch", "--prune", args.remote])

    created_local_branch = False
    has_local_branch = local_branch_exists(repo_root, args.branch)
    has_remote_branch = remote_branch_exists(repo_root, args.remote, args.branch)

    if has_local_branch:
        branch_guard.run_git(repo_root, ["switch", args.branch])
    elif has_remote_branch:
        branch_guard.run_git(repo_root, ["switch", "--track", "-c", args.branch, f"{args.remote}/{args.branch}"])
        created_local_branch = True
    else:
        raise OpenClawGitGuardError(
            f"Branch '{args.branch}' does not exist locally or on {args.remote}."
        )

    pulled = False
    if args.pull:
        if not has_remote_branch:
            raise OpenClawGitGuardError(
                f"Branch '{args.branch}' has no matching {args.remote}/{args.branch} ref, so --pull is not allowed."
            )
        branch_guard.run_git(repo_root, ["pull", "--ff-only", args.remote, args.branch])
        pulled = True

    payload = {
        "ok": True,
        "command": "switch",
        "repo_root": repo_root.as_posix(),
        "from_branch": before_branch,
        "from_head_sha": before_sha,
        "to_branch": branch_guard.current_branch(repo_root),
        "to_head_sha": current_head_sha(repo_root),
        "tracking_branch": tracking_branch(repo_root),
        "remote": args.remote,
        "created_local_branch": created_local_branch,
        "performed_fetch": True,
        "performed_pull": pulled,
    }
    emit_payload(payload)
    return 0


def status_command(args: argparse.Namespace) -> int:
    repo_root = branch_guard.resolve_repo_root(args.repo_root)
    emit_payload(status_payload(repo_root))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bounded git operations for OpenClaw/Feishu local repo control.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("status", help="Return the current branch, HEAD, and dirty-worktree summary.")
    status.add_argument("--repo-root")
    status.set_defaults(func=status_command)

    switch = subparsers.add_parser(
        "switch",
        help="Safely switch to an existing local/remote branch and optionally fast-forward pull it.",
    )
    switch.add_argument("--repo-root")
    switch.add_argument("--branch", required=True)
    switch.add_argument("--remote", default="origin")
    switch.add_argument("--pull", action="store_true")
    switch.set_defaults(func=switch_command)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (branch_guard.GitCommandError, OpenClawGitGuardError, RuntimeError) as exc:
        repo_root = None
        try:
            repo_root = branch_guard.resolve_repo_root(getattr(args, "repo_root", None))
        except Exception:
            repo_root = None
        emit_payload(
            {
                "ok": False,
                "command": getattr(args, "command", ""),
                "repo_root": repo_root.as_posix() if isinstance(repo_root, Path) else "",
                "error": str(exc),
            }
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
