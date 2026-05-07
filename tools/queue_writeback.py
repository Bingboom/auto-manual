from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from tools.queue_transitions import (
    QueueTransitionFields,
    build_failure_result_transition,
    build_failure_writeback_transition,
    build_running_transition,
    build_success_transition,
    format_queue_result,
)


def _format_queue_result(
    *,
    prefix: str,
    version: str = "",
    workflow_action: str | None = None,
    workflow_action_label: Callable[[Any], str | None] | None = None,
    timestamp_label: str = "",
    timestamp: datetime | None = None,
    data_sync_status: str = "",
    status_notes: tuple[str, ...] = (),
    message: str = "",
) -> str:
    return format_queue_result(
        prefix=prefix,
        version=version,
        workflow_action=workflow_action,
        workflow_action_label=workflow_action_label,
        timestamp_label=timestamp_label,
        timestamp=timestamp,
        data_sync_status=data_sync_status,
        status_notes=status_notes,
        message=message,
    )


def build_success_fields(
    *,
    version: str,
    word_output_path: Path,
    document_link_url: str,
    built_at: datetime,
    document_link_dd_url: str = "",
    workflow_action: str | None,
    doc_phase: str | None,
    data_sync_status: str = "",
    status_notes: tuple[str, ...] = (),
    normalize_workflow_action: Callable[[Any], str | None],
    normalize_doc_phase: Callable[[Any], str | None],
    workflow_action_label: Callable[[Any], str | None],
    result_field: str,
    document_directory_field: str,
    document_link_field: str,
    document_link_dd_field: str,
    trigger_field: str,
    done_trigger_value: str,
    immediate_trigger_field: str,
    force_phase2_refresh_field: str,
    data_sync_field: str,
    success_prefix: str,
) -> dict[str, Any]:
    return build_success_transition(
        fields=QueueTransitionFields(
            result_field=result_field,
            document_directory_field=document_directory_field,
            document_link_field=document_link_field,
            document_link_dd_field=document_link_dd_field,
            trigger_field=trigger_field,
            done_trigger_value=done_trigger_value,
            immediate_trigger_field=immediate_trigger_field,
            force_phase2_refresh_field=force_phase2_refresh_field,
            data_sync_field=data_sync_field,
            success_prefix=success_prefix,
        ),
        version=version,
        word_output_path=word_output_path,
        document_link_url=document_link_url,
        document_link_dd_url=document_link_dd_url,
        built_at=built_at,
        workflow_action=workflow_action,
        data_sync_status=data_sync_status,
        status_notes=status_notes,
        workflow_action_label=workflow_action_label,
    )


def build_started_fields(
    *,
    started_at: datetime,
    version: str = "",
    workflow_action: str | None = None,
    doc_phase: str | None = None,
    data_sync_status: str = "",
    normalize_workflow_action: Callable[[Any], str | None],
    normalize_doc_phase: Callable[[Any], str | None],
    workflow_action_label: Callable[[Any], str | None],
    build_started_at_field: str,
    result_field: str,
    running_prefix: str,
) -> dict[str, Any]:
    return build_running_transition(
        fields=QueueTransitionFields(
            result_field=result_field,
            build_started_at_field=build_started_at_field,
            running_prefix=running_prefix,
        ),
        started_at=started_at,
        version=version,
        workflow_action=workflow_action,
        doc_phase=doc_phase,
        data_sync_status=data_sync_status,
        normalize_workflow_action=normalize_workflow_action,
        normalize_doc_phase=normalize_doc_phase,
        workflow_action_label=workflow_action_label,
    )


def build_failure_fields(
    *,
    version: str,
    message: str,
    workflow_action: str | None,
    doc_phase: str | None,
    data_sync_status: str = "",
    normalize_workflow_action: Callable[[Any], str | None],
    normalize_doc_phase: Callable[[Any], str | None],
    workflow_action_label: Callable[[Any], str | None],
    result_field: str,
    failed_prefix: str,
) -> dict[str, Any]:
    return build_failure_result_transition(
        fields=QueueTransitionFields(
            result_field=result_field,
            failed_prefix=failed_prefix,
        ),
        version=version,
        message=message,
        workflow_action=workflow_action,
        data_sync_status=data_sync_status,
        workflow_action_label=workflow_action_label,
    )


def build_failure_writeback_fields(
    *,
    version: str,
    message: str,
    workflow_action: str | None,
    doc_phase: str | None,
    data_sync_status: str = "",
    word_output_path: Path | None,
    document_link_url: str | None,
    document_link_dd_url: str | None,
    build_failure_fields: Callable[..., dict[str, Any]],
    result_field: str,
    document_directory_field: str,
    document_link_field: str,
    document_link_dd_field: str,
    immediate_trigger_field: str,
    force_phase2_refresh_field: str,
    data_sync_field: str,
) -> dict[str, Any]:
    fields = build_failure_fields(
        version=version,
        message=message,
        workflow_action=workflow_action,
        doc_phase=doc_phase,
        data_sync_status=data_sync_status,
    )
    transition_fields = QueueTransitionFields(
        result_field=result_field,
        document_directory_field=document_directory_field,
        document_link_field=document_link_field,
        document_link_dd_field=document_link_dd_field,
        immediate_trigger_field=immediate_trigger_field,
        force_phase2_refresh_field=force_phase2_refresh_field,
        data_sync_field=data_sync_field,
    )
    transition_payload = build_failure_writeback_transition(
        fields=transition_fields,
        version=version,
        message=message,
        workflow_action=workflow_action,
        data_sync_status=data_sync_status,
        word_output_path=word_output_path,
        document_link_url=document_link_url,
        document_link_dd_url=document_link_dd_url,
        workflow_action_label=lambda value: None,
    )
    transition_payload[result_field] = fields[result_field]
    if document_link_url:
        transition_payload[result_field] += " | latest_drive_link_preserved"
    return transition_payload
