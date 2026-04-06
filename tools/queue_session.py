from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class QueueSessionBootstrap:
    binding: Any
    cli_bin: str
    identity: str
    source: Any
    normalized_cli_action: str | None


@dataclass(frozen=True)
class QueuePendingState:
    pending_groups: list[list[Any]]
    can_write_started_at: bool


def bootstrap_queue_session(
    *,
    cfg: dict[str, Any],
    workflow_action: str | None,
    doc_phase: str | None,
    collect_queue_preflight_errors: Callable[[dict[str, Any]], list[str]],
    resolve_document_link_binding: Callable[[dict[str, Any]], Any],
    cli_bin: Callable[[dict[str, Any]], str],
    phase2_identity: Callable[[], str],
    source_factory: Callable[..., Any],
    normalize_cli_queue_action: Callable[..., str | None],
    warn_legacy_cli_doc_phase: Callable[[str | None, str | None], None],
) -> QueueSessionBootstrap:
    errors = collect_queue_preflight_errors(cfg)
    if errors:
        raise RuntimeError("process-build-queue preflight failed:\n- " + "\n- ".join(errors))

    binding = resolve_document_link_binding(cfg)
    resolved_cli_bin = cli_bin(cfg)
    identity = phase2_identity()
    source = source_factory(cli_bin=resolved_cli_bin, identity=identity)
    normalized_cli_action = normalize_cli_queue_action(workflow_action=workflow_action, doc_phase=doc_phase)
    warn_legacy_cli_doc_phase(doc_phase, workflow_action)
    return QueueSessionBootstrap(
        binding=binding,
        cli_bin=resolved_cli_bin,
        identity=identity,
        source=source,
        normalized_cli_action=normalized_cli_action,
    )


def load_pending_queue_state(
    *,
    source: Any,
    binding: Any,
    immediate_only: bool,
    workflow_action: str | None,
    record_id: str | None,
    select_pending_queue_records: Callable[..., list[Any]],
    group_pending_queue_records: Callable[[list[Any]], list[list[Any]]],
    available_field_names: Callable[[list[dict[str, Any]]], set[str]],
    build_started_at_field: str,
) -> QueuePendingState | None:
    raw_records = source.fetch_records_with_ids(
        base_token=binding.base_token,
        table_id=binding.table_id,
        view_id=binding.view_id,
    )
    pending = select_pending_queue_records(
        raw_records,
        immediate_only=immediate_only,
        workflow_action=workflow_action,
        record_id=record_id,
    )
    if not pending:
        return None
    pending_groups = group_pending_queue_records(pending)
    can_write_started_at = build_started_at_field in available_field_names(raw_records)
    return QueuePendingState(
        pending_groups=pending_groups,
        can_write_started_at=can_write_started_at,
    )


def print_no_pending_message(*, immediate_only: bool) -> None:
    if immediate_only:
        print("[build-queue] No pending immediate build tasks found.")
    else:
        print("[build-queue] No pending build tasks found.")


def resolve_and_report_wiki_destination(
    *,
    cli_bin: str,
    identity: str,
    binding: Any,
    resolve_wiki_destination: Callable[..., Any],
) -> Any:
    wiki_destination = resolve_wiki_destination(
        cli_bin=cli_bin,
        identity=identity,
        binding=binding,
    )
    print(
        "[build-queue] Wiki destination "
        + json.dumps(
            {
                "space_id": wiki_destination.space_id,
                "parent_wiki_token": wiki_destination.parent_wiki_token,
            },
            ensure_ascii=False,
        )
    )
    return wiki_destination
