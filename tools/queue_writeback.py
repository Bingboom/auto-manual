from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Callable


def build_success_fields(
    *,
    version: str,
    word_output_path: Path,
    document_link_url: str,
    built_at: datetime,
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
    trigger_field: str,
    done_trigger_value: str,
    immediate_trigger_field: str,
    force_phase2_refresh_field: str,
    data_sync_field: str,
    success_prefix: str,
) -> dict[str, Any]:
    action_label = workflow_action_label(workflow_action)
    fields = {
        result_field: " | ".join(
            part
            for part in (
                success_prefix,
                f"version={version}" if version else "",
                f"workflow_action={action_label}" if action_label else "",
                f"built_at={built_at.isoformat(timespec='seconds')}",
                f"data_sync={data_sync_status}" if data_sync_status else "",
                *[note.strip() for note in status_notes if note.strip()],
            )
            if part
        ),
        document_directory_field: word_output_path.resolve(strict=False).as_posix(),
        document_link_field: document_link_url.strip(),
        trigger_field: [done_trigger_value],
        immediate_trigger_field: False,
    }
    if force_phase2_refresh_field:
        fields[force_phase2_refresh_field] = False
    if data_sync_field and data_sync_status:
        fields[data_sync_field] = data_sync_status
    return fields


def build_started_fields(*, started_at: datetime, build_started_at_field: str) -> dict[str, Any]:
    return {
        build_started_at_field: int(started_at.timestamp() * 1000),
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
    action_label = workflow_action_label(workflow_action)
    return {
        result_field: " | ".join(
            part
            for part in (
                failed_prefix,
                f"version={version}" if version else "",
                f"workflow_action={action_label}" if action_label else "",
                f"data_sync={data_sync_status}" if data_sync_status else "",
                message.strip(),
            )
            if part
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
    build_failure_fields: Callable[..., dict[str, Any]],
    result_field: str,
    document_directory_field: str,
    document_link_field: str,
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
    fields[immediate_trigger_field] = False
    if force_phase2_refresh_field:
        fields[force_phase2_refresh_field] = False
    if data_sync_field and data_sync_status:
        fields[data_sync_field] = data_sync_status
    return fields
