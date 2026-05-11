from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class QueueTransitionFields:
    result_field: str
    build_started_at_field: str = ""
    document_directory_field: str = ""
    document_link_field: str = ""
    document_link_dd_field: str = ""
    feishu_cloud_doc_field: str = ""
    trigger_field: str = ""
    done_trigger_value: str = ""
    immediate_trigger_field: str = ""
    force_phase2_refresh_field: str = ""
    data_sync_field: str = ""
    running_prefix: str = "RUNNING"
    success_prefix: str = "SUCCESS"
    failed_prefix: str = "FAILED"


def format_queue_result(
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


def build_running_transition(
    *,
    fields: QueueTransitionFields,
    started_at: datetime,
    version: str = "",
    workflow_action: str | None = None,
    doc_phase: str | None = None,
    data_sync_status: str = "",
    normalize_workflow_action: Callable[[Any], str | None],
    normalize_doc_phase: Callable[[Any], str | None],
    workflow_action_label: Callable[[Any], str | None],
) -> dict[str, Any]:
    normalized_workflow_action = normalize_workflow_action(workflow_action)
    normalized_doc_phase = normalize_doc_phase(doc_phase)
    return {
        fields.build_started_at_field: int(started_at.timestamp() * 1000),
        fields.result_field: format_queue_result(
            prefix=fields.running_prefix,
            version=version,
            workflow_action=normalized_workflow_action or normalized_doc_phase,
            workflow_action_label=workflow_action_label,
            timestamp_label="started_at",
            timestamp=started_at,
            data_sync_status=data_sync_status,
        ),
    }


def build_success_transition(
    *,
    fields: QueueTransitionFields,
    version: str,
    word_output_path: Path,
    document_link_url: str,
    built_at: datetime,
    document_link_dd_url: str = "",
    feishu_cloud_doc_url: str = "",
    workflow_action: str | None,
    data_sync_status: str = "",
    status_notes: tuple[str, ...] = (),
    workflow_action_label: Callable[[Any], str | None],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        fields.result_field: format_queue_result(
            prefix=fields.success_prefix,
            version=version,
            workflow_action=workflow_action,
            workflow_action_label=workflow_action_label,
            timestamp_label="built_at",
            timestamp=built_at,
            data_sync_status=data_sync_status,
            status_notes=status_notes,
        ),
        fields.document_directory_field: word_output_path.resolve(strict=False).as_posix(),
        fields.document_link_field: document_link_url.strip(),
        fields.trigger_field: [fields.done_trigger_value],
        fields.immediate_trigger_field: False,
    }
    if fields.document_link_dd_field:
        payload[fields.document_link_dd_field] = document_link_dd_url.strip()
    if fields.feishu_cloud_doc_field:
        payload[fields.feishu_cloud_doc_field] = feishu_cloud_doc_url.strip()
    if fields.force_phase2_refresh_field:
        payload[fields.force_phase2_refresh_field] = False
    if fields.data_sync_field and data_sync_status:
        payload[fields.data_sync_field] = data_sync_status
    return payload


def build_failure_result_transition(
    *,
    fields: QueueTransitionFields,
    version: str,
    message: str,
    workflow_action: str | None,
    data_sync_status: str = "",
    workflow_action_label: Callable[[Any], str | None],
) -> dict[str, Any]:
    return {
        fields.result_field: format_queue_result(
            prefix=fields.failed_prefix,
            version=version,
            workflow_action=workflow_action,
            workflow_action_label=workflow_action_label,
            data_sync_status=data_sync_status,
            message=message,
        )
    }


def build_failure_writeback_transition(
    *,
    fields: QueueTransitionFields,
    version: str,
    message: str,
    workflow_action: str | None,
    data_sync_status: str = "",
    word_output_path: Path | None,
    document_link_url: str | None,
    document_link_dd_url: str | None,
    feishu_cloud_doc_url: str | None = None,
    workflow_action_label: Callable[[Any], str | None],
) -> dict[str, Any]:
    payload = build_failure_result_transition(
        fields=fields,
        version=version,
        message=message,
        workflow_action=workflow_action,
        data_sync_status=data_sync_status,
        workflow_action_label=workflow_action_label,
    )
    if word_output_path is not None:
        payload[fields.document_directory_field] = word_output_path.resolve(strict=False).as_posix()
    if document_link_url:
        payload[fields.document_link_field] = document_link_url
        payload[fields.result_field] += " | latest_drive_link_preserved"
    if fields.document_link_dd_field:
        payload[fields.document_link_dd_field] = (document_link_dd_url or "").strip()
    if fields.feishu_cloud_doc_field and feishu_cloud_doc_url:
        payload[fields.feishu_cloud_doc_field] = feishu_cloud_doc_url.strip()
    payload[fields.immediate_trigger_field] = False
    if fields.force_phase2_refresh_field:
        payload[fields.force_phase2_refresh_field] = False
    if fields.data_sync_field and data_sync_status:
        payload[fields.data_sync_field] = data_sync_status
    return payload


def format_writeback_failed_note(exc: BaseException | str) -> str:
    return f"writeback_failed={str(exc).strip()}"


def append_writeback_failed(failure_message: str, exc: BaseException | str) -> str:
    return f"{failure_message} | {format_writeback_failed_note(exc)}"
