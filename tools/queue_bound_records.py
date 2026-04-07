from __future__ import annotations

from pathlib import Path
from typing import Any

_DEFAULT_ROOT = Path(__file__).resolve().parents[1]
_repo_root_provider = lambda: _DEFAULT_ROOT
_config_loader_provider = lambda: load_config
_resolve_config_path_func_provider = lambda: resolve_config_path_for_task

from tools.document_link_actions import (
    legacy_doc_phase_value as _legacy_doc_phase_value,
    normalize_cli_queue_action as _normalize_cli_queue_action,
    resolve_workflow_action as _resolve_workflow_action,
    workflow_action_source as _workflow_action_source,
    workflow_action_uses_legacy_doc_phase as _workflow_action_uses_legacy_doc_phase,
)
from tools.document_link_queue import (
    is_immediate_trigger_enabled as _is_immediate_trigger_enabled_impl,
    is_trigger_requested as _is_trigger_requested_impl,
    parse_document_key,
    parse_queue_records as _parse_queue_records_impl,
    queue_group_build_family,
    queue_group_lang,
    queue_record_key,
    resolve_target_for_record as _resolve_target_for_record_impl,
    select_pending_queue_records as _select_pending_queue_records_impl,
    validate_queue_record_group as _validate_queue_record_group_impl,
)
from tools.phase2_support import load_config
from tools.queue_config_resolution import (
    queue_by_document_key as _queue_by_document_key,
    resolve_config_path_for_task as _resolve_config_path_for_task_impl,
)
from tools.queue_contract import (
    BUILD_FAMILY_FIELD,
    DOC_PHASE_FIELD,
    DOCUMENT_ID_FIELD,
    DOCUMENT_KEY_FIELD,
    GIT_REF_FIELD,
    IMMEDIATE_TRIGGER_FIELD,
    LANG_FIELD,
    LEGACY_TRIGGER_FIELDS,
    TRIGGER_FIELD,
    TRIGGER_VALUES,
    VERSION_FIELD,
    WORKFLOW_ACTION_FIELD,
    QueueRecord,
)
from tools.queue_grouping import group_pending_queue_records as _group_pending_queue_records_impl


def set_repo_root_provider(provider) -> None:
    global _repo_root_provider
    _repo_root_provider = provider


def set_config_loader_provider(provider) -> None:
    global _config_loader_provider
    _config_loader_provider = provider


def set_resolve_config_path_provider(provider) -> None:
    global _resolve_config_path_func_provider
    _resolve_config_path_func_provider = provider


def _repo_root() -> Path:
    return Path(_repo_root_provider())


def parse_queue_records(raw_records: list[dict[str, Any]]) -> list[QueueRecord]:
    return _parse_queue_records_impl(
        raw_records,
        queue_record_factory=QueueRecord,
        document_id_field=DOCUMENT_ID_FIELD,
        document_key_field=DOCUMENT_KEY_FIELD,
        version_field=VERSION_FIELD,
        lang_field=LANG_FIELD,
        build_family_field=BUILD_FAMILY_FIELD,
        workflow_action_field=WORKFLOW_ACTION_FIELD,
        doc_phase_field=DOC_PHASE_FIELD,
        git_ref_field=GIT_REF_FIELD,
        trigger_field=TRIGGER_FIELD,
        legacy_trigger_fields=LEGACY_TRIGGER_FIELDS,
        immediate_trigger_field=IMMEDIATE_TRIGGER_FIELD,
    )


def is_trigger_requested(value: Any) -> bool:
    return _is_trigger_requested_impl(value, trigger_values=TRIGGER_VALUES)


is_immediate_trigger_enabled = _is_immediate_trigger_enabled_impl


def queue_record_uses_legacy_doc_phase(record: QueueRecord) -> bool:
    return _workflow_action_uses_legacy_doc_phase(
        workflow_action=record.workflow_action,
        doc_phase=record.doc_phase,
    )


def queue_record_action_source(record: QueueRecord) -> str:
    return _workflow_action_source(
        workflow_action=record.workflow_action,
        doc_phase=record.doc_phase,
    )


def queue_record_legacy_doc_phase(record: QueueRecord) -> str | None:
    return _legacy_doc_phase_value(
        workflow_action=record.workflow_action,
        doc_phase=record.doc_phase,
    )


def resolve_queue_workflow_action(record: QueueRecord) -> str | None:
    return _resolve_workflow_action(
        workflow_action=record.workflow_action,
        doc_phase=record.doc_phase,
        record_id=record.record_id,
    )


def pending_queue_records(raw_records: list[dict[str, Any]]) -> list[QueueRecord]:
    return select_pending_queue_records(raw_records)


def pending_immediate_queue_records(raw_records: list[dict[str, Any]]) -> list[QueueRecord]:
    return select_pending_queue_records(raw_records, immediate_only=True)


def select_pending_queue_records(
    raw_records: list[dict[str, Any]],
    *,
    immediate_only: bool = False,
    workflow_action: str | None = None,
    doc_phase: str | None = None,
    record_id: str | None = None,
) -> list[QueueRecord]:
    return _select_pending_queue_records_impl(
        raw_records,
        immediate_only=immediate_only,
        workflow_action=workflow_action,
        doc_phase=doc_phase,
        record_id=record_id,
        parse_queue_records=parse_queue_records,
        normalize_cli_queue_action=_normalize_cli_queue_action,
        resolve_queue_workflow_action=resolve_queue_workflow_action,
        is_trigger_requested=is_trigger_requested,
        is_immediate_trigger_enabled=is_immediate_trigger_enabled,
    )


def document_key_from_document_id(*, document_id: str, lang: str, version: str) -> str:
    candidate = document_id.strip()
    version_text = version.strip()
    lang_text = lang.strip().lower()
    if version_text and candidate.endswith("_" + version_text):
        candidate = candidate[: -(len(version_text) + 1)]
    if lang_text and candidate.lower().endswith("_" + lang_text):
        candidate = candidate[: -(len(lang_text) + 1)]
    return candidate.strip()


def resolve_target_for_record(record: QueueRecord) -> tuple[str, str]:
    return _resolve_target_for_record_impl(record, parse_document_key=parse_document_key)


def resolve_config_path_for_task(
    *,
    region: str,
    lang: str | None,
    build_family: str | None = None,
    workflow_action: str | None = None,
) -> Path:
    return _resolve_config_path_for_task_impl(
        repo_root=_repo_root(),
        region=region,
        lang=lang,
        build_family=build_family,
        workflow_action=workflow_action,
        config_loader=_config_loader_provider(),
    )


def group_pending_queue_records(records: list[QueueRecord]) -> list[list[QueueRecord]]:
    return _group_pending_queue_records_impl(
        records,
        resolve_target_for_record=resolve_target_for_record,
        resolve_config_path_for_task=_resolve_config_path_func_provider(),
        config_loader=_config_loader_provider(),
        queue_by_document_key=_queue_by_document_key,
        queue_record_key=queue_record_key,
        resolve_queue_workflow_action=resolve_queue_workflow_action,
    )


def validate_queue_record_group(records: list[QueueRecord]) -> None:
    _validate_queue_record_group_impl(
        records,
        queue_record_key=queue_record_key,
        resolve_queue_workflow_action=resolve_queue_workflow_action,
    )
