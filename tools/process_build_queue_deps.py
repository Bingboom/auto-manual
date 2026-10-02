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
    # Also looked up inside other facade services (artifact destination and
    # publish), so a set value is routed through ``FacadeOverrides`` as well.
    resolve_wiki_destination: Callable[..., Any] | None = None
    upload_word_to_drive: Callable[..., Any] | None = None
    move_drive_file_to_wiki: Callable[..., Any] | None = None


NESTED_FIELDS = ("resolve_wiki_destination", "upload_word_to_drive", "move_drive_file_to_wiki")


class FacadeOverrides:
    """A facade module with some names replaced, for services that take ``module``."""

    def __init__(self, module: Any, overrides: dict[str, Any]) -> None:
        self._module = module
        self._overrides = overrides

    def __getattr__(self, name: str) -> Any:
        if name in self._overrides:
            return self._overrides[name]
        return getattr(self._module, name)


def default_queue_deps(module: Any) -> QueueDeps:
    """Resolve the facade's current names when defaults are requested."""
    return QueueDeps(
        source_factory=module.LarkCliSource,
        run_command=module._run_command,
        prepare_git_ref_worktree=module._prepare_git_ref_worktree,
        remove_worktree=module._remove_worktree,
    )


def nested_overrides(deps: QueueDeps | None) -> dict[str, Any]:
    """The nested-lookup fields ``deps`` sets, keyed by their facade name."""
    if deps is None:
        return {}
    return {name: getattr(deps, name) for name in NESTED_FIELDS if getattr(deps, name) is not None}


def queue_dep(deps: QueueDeps | None, field: str, module: Any, facade_name: str) -> Any:
    """Return ``deps.<field>`` when set, else the facade's current ``facade_name``."""
    value = getattr(deps, field) if deps is not None else None
    return value if value is not None else getattr(module, facade_name)
