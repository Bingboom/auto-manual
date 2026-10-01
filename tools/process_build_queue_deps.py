from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class QueueDeps:
    """External boundaries already accepted by queue session/build callbacks."""

    source_factory: Callable[..., Any]
    run_command: Callable[..., None]
    prepare_git_ref_worktree: Callable[..., Path]
    remove_worktree: Callable[[Path], None]


def default_queue_deps(module: Any) -> QueueDeps:
    """Resolve the facade's current names when defaults are requested."""
    return QueueDeps(
        source_factory=module.LarkCliSource,
        run_command=module._run_command,
        prepare_git_ref_worktree=module._prepare_git_ref_worktree,
        remove_worktree=module._remove_worktree,
    )
