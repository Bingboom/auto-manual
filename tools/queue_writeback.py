from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Callable


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
    action_label = workflow_action_label(workflow_action) if workflow_action_label else None
    return " | ".join(
        part
        for part in (
            prefix,
            f"version={version}" if version else "",
            f"workflow_action={action_label}" if action_label else "",
            f"{timestamp_label}={timestamp.isoformat(timespec='seconds')}" if timestamp_label and timestamp else "",
            f"data_sync={data_sync_status}" if data_sync_status else "",
            *[note.strip() for note in status_notes if note.strip()],
            message.strip(),
        )
        if part
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
    fields = {
        result_field: _format_queue_result(
            prefix=success_prefix,
            version=version,
            workflow_action=workflow_action,
            workflow_action_label=workflow_action_label,
            timestamp_label="built_at",
            timestamp=built_at,
            data_sync_status=data_sync_status,
            status_notes=status_notes,
        ),
        document_directory_field: word_output_path.resolve(strict=False).as_posix(),
        document_link_field: document_link_url.strip(),
        trigger_field: [done_trigger_value],
        immediate_trigger_field: False,
    }
    if document_link_dd_field:
        fields[document_link_dd_field] = document_link_dd_url.strip()
    if force_phase2_refresh_field:
        fields[force_phase2_refresh_field] = False
    if data_sync_field and data_sync_status:
        fields[data_sync_field] = data_sync_status
    return fields


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
    normalized_workflow_action = normalize_workflow_action(workflow_action)
    normalized_doc_phase = normalize_doc_phase(doc_phase)
    return {
        build_started_at_field: int(started_at.timestamp() * 1000),
        result_field: _format_queue_result(
            prefix=running_prefix,
            version=version,
            workflow_action=normalized_workflow_action or normalized_doc_phase,
            workflow_action_label=workflow_action_label,
            timestamp_label="started_at",
            timestamp=started_at,
            data_sync_status=data_sync_status,
        ),
    }


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
    return {
        result_field: _format_queue_result(
            prefix=failed_prefix,
            version=version,
            workflow_action=workflow_action,
            workflow_action_label=workflow_action_label,
            data_sync_status=data_sync_status,
            message=message,
        )
    }


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
    if word_output_path is not None:
        fields[document_directory_field] = word_output_path.resolve(strict=False).as_posix()
    if document_link_url:
        fields[document_link_field] = document_link_url
        fields[result_field] += " | latest_drive_link_preserved"
    if document_link_dd_field:
        fields[document_link_dd_field] = (document_link_dd_url or "").strip()
    fields[immediate_trigger_field] = False
    if force_phase2_refresh_field:
        fields[force_phase2_refresh_field] = False
    if data_sync_field and data_sync_status:
        fields[data_sync_field] = data_sync_status
    return fields
