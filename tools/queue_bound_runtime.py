from __future__ import annotations

from pathlib import Path

_DEFAULT_ROOT = Path(__file__).resolve().parents[1]
_repo_root_provider = lambda: _DEFAULT_ROOT

from tools.queue_build_execution import (  # noqa: E402
    build_py_sync_data_command as _build_py_sync_data_command_impl,
    build_py_target_command as _build_py_target_command_impl,
)
from tools.queue_runtime import (  # noqa: E402
    command_failure_message,
    format_command,
    prepare_git_ref_worktree as _prepare_git_ref_worktree_impl,
    remove_worktree as _remove_worktree_impl,
    run_command as _run_command_impl,
    run_git as _run_git_impl,
    slug_ref_token,
    worktree_dir_for_git_ref as _worktree_dir_for_git_ref_impl,
)


def set_repo_root_provider(provider) -> None:
    global _repo_root_provider
    _repo_root_provider = provider


def _repo_root() -> Path:
    return Path(_repo_root_provider())


def run_command(cmd: list[str], *, cwd: Path | None = None) -> None:
    _run_command_impl(
        cmd,
        cwd=cwd or _repo_root(),
        prefix="[build-queue]",
        command_failure_message=command_failure_message,
    )


def run_git(args: list[str], *, cwd: Path | None = None) -> None:
    _run_git_impl(args, repo_root=cwd or _repo_root(), run_command=run_command)


def worktree_dir_for_git_ref(git_ref: str) -> Path:
    return _worktree_dir_for_git_ref_impl(repo_root=_repo_root(), git_ref=git_ref)


def remove_worktree(path: Path) -> None:
    _remove_worktree_impl(repo_root=_repo_root(), path=path)


def prepare_git_ref_worktree(git_ref: str) -> Path:
    return _prepare_git_ref_worktree_impl(
        repo_root=_repo_root(),
        git_ref=git_ref,
        run_git=run_git,
        worktree_dir_for_git_ref=lambda *, repo_root, git_ref: worktree_dir_for_git_ref(git_ref),
        remove_worktree=lambda *, repo_root, path: remove_worktree(path),
    )


def build_py_target_command(
    *,
    action: str,
    config_path: Path,
    model: str,
    region: str,
    data_root: str | None,
    lang: str | None = None,
    source: str | None = None,
    no_clean: bool = False,
    idml_mode: str | None = None,
    repo_root: Path | None = None,
) -> list[str]:
    return _build_py_target_command_impl(
        repo_root=repo_root or _repo_root(),
        action=action,
        config_path=config_path,
        model=model,
        region=region,
        data_root=data_root,
        lang=lang,
        source=source,
        no_clean=no_clean,
        idml_mode=idml_mode,
    )


def build_py_sync_data_command(*, config_path: Path, data_root: str | None, repo_root: Path | None = None) -> list[str]:
    return _build_py_sync_data_command_impl(
        repo_root=repo_root or _repo_root(),
        config_path=config_path,
        data_root=data_root,
    )
