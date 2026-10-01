from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class QueueDeps:
    """Collaborators of one build-queue run, passed in instead of patched on the facade.

    The four required fields are the external boundaries the session and build
    callbacks already accept.  Every optional field replaces the facade name of the
    same meaning for this run only; ``None`` keeps the facade lookup.  Tests build
    one with ``dataclasses.replace(default_queue_deps(process_build_queue), ...)``
    inside the test body, so the defaults see any facade patch still in force.
    """

    source_factory: Callable[..., Any]
    run_command: Callable[..., None]
    prepare_git_ref_worktree: Callable[..., Path]
    remove_worktree: Callable[[Path], None]
    collect_queue_preflight_errors: Callable[..., list[str]] | None = None
    resolve_document_link_binding: Callable[..., Any] | None = None
    phase2_identity: Callable[[], str] | None = None
    sync_phase2_snapshot_before_queue: Callable[..., None] | None = None
    build_document_for_task: Callable[..., Any] | None = None
    resolve_artifact_destination: Callable[..., Any] | None = None
    resolve_dingtalk_mirror_destination: Callable[..., Any] | None = None
    ensure_dingtalk_session_ready: Callable[..., Any] | None = None
    publish_word_artifact: Callable[..., Any] | None = None
    import_markdown_to_cloud_doc: Callable[..., Any] | None = None
    finalize_cloud_doc: Callable[..., Any] | None = None


def default_queue_deps(module: Any) -> QueueDeps:
    """Resolve the facade's current names when defaults are requested."""
    return QueueDeps(
        source_factory=module.LarkCliSource,
        run_command=module._run_command,
        prepare_git_ref_worktree=module._prepare_git_ref_worktree,
        remove_worktree=module._remove_worktree,
    )


def queue_dep(deps: QueueDeps | None, field: str, module: Any, facade_name: str) -> Any:
    """Return ``deps.<field>`` when set, else the facade's current ``facade_name``."""
    value = getattr(deps, field) if deps is not None else None
    return value if value is not None else getattr(module, facade_name)
