"""Run the queue build step with the facade's collaborators and explicit overrides."""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path
from unittest import mock

from tools.build_queue import process_build_queue, bound_lark_ops as queue_bound_lark_ops, bound_outputs as queue_bound_outputs, bound_records as queue_bound_records, bound_runtime as queue_bound_runtime, build_execution as queue_build_execution

_BOUND_MODULES = (queue_bound_outputs, queue_bound_runtime, queue_bound_lark_ops, queue_bound_records)


@contextmanager
def bound_repo_root(root: Path) -> Iterator[None]:
    """Point the queue's bound modules at ``root``, where they look the repo root up.

    Use this instead of patching the facade's ``ROOT``: the bound modules read the
    root through their own provider, which the facade only wires at import time.
    """
    with ExitStack() as stack:
        for module in _BOUND_MODULES:
            stack.enter_context(mock.patch.object(module, "_repo_root_provider", lambda: root))
        yield

BUILD_DOCUMENT_COLLABORATORS = {
    "normalize_workflow_action": "normalize_workflow_action",
    "prepare_git_ref_worktree": "_prepare_git_ref_worktree",
    "remove_worktree": "_remove_worktree",
    "config_path_in_repo_root": "_config_path_in_repo_root",
    "run_command": "_run_command",
    "build_py_target_command": "_build_py_target_command",
    "resolve_word_output_path_for_target": "resolve_word_output_path_for_target",
    "resolve_pdf_output_path_for_target": "resolve_pdf_output_path_for_target",
    "resolve_md_output_path_for_target": "resolve_md_output_path_for_target",
    "versioned_pdf_output_path": "_versioned_pdf_output_path",
    "versioned_word_output_path": "_versioned_word_output_path",
    "versioned_md_output_path": "_versioned_md_output_path",
    "resolve_html_output_dir_for_target": "resolve_html_output_dir_for_target",
    "stage_publish_assets_to_host_repo": "_stage_publish_assets_to_host_repo",
    "stage_web_publish_assets_to_host_repo": "_stage_web_publish_assets_to_host_repo",
    "stage_draft_word_output_to_host_repo": "_stage_draft_word_output_to_host_repo",
    "stage_draft_md_output_to_host_repo": "_stage_draft_md_output_to_host_repo",
}


def build_document_for_task(**kwargs: object) -> object:
    """Run the build step with the facade's collaborators, overriding any passed in by impl name.

    ``repo_root`` defaults to the facade's ``ROOT``.  Pass it to build against a temporary
    root instead of patching the facade: the bound modules are pointed at it too, exactly
    as a patched facade ``ROOT`` would have done.
    """
    collaborators = {
        name: kwargs.pop(name) if name in kwargs else getattr(process_build_queue, facade_name)
        for name, facade_name in BUILD_DOCUMENT_COLLABORATORS.items()
    }
    if "repo_root" not in kwargs:
        return queue_build_execution.build_document_for_task(
            repo_root=process_build_queue.ROOT,
            **collaborators,  # type: ignore[arg-type]
            **kwargs,  # type: ignore[arg-type]
        )
    root = Path(kwargs.pop("repo_root"))  # type: ignore[arg-type]
    with bound_repo_root(root):
        return queue_build_execution.build_document_for_task(
            repo_root=root,
            **collaborators,  # type: ignore[arg-type]
            **kwargs,  # type: ignore[arg-type]
        )
