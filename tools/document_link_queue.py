from __future__ import annotations

import json
import os
import re
from typing import Any, Callable

from tools.region_aliases import canonical_document_key_region

_EXPLICIT_DOCUMENT_KEY_RE = re.compile(r"[A-Za-z0-9-]+_[A-Za-z0-9-]+")


def scalar_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        for item in value:
            text = scalar_text(item)
            if text:
                return text
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return format(value, "g")
    if isinstance(value, dict):
        for key in ("text", "name", "label", "title", "value"):
            text = scalar_text(value.get(key))
            if text:
                return text
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return str(value).strip()


def field_value(fields: dict[str, Any], *field_names: str) -> Any:
    for field_name in field_names:
        if field_name in fields:
            return fields.get(field_name)
    return None


def available_field_names(raw_records: list[dict[str, Any]]) -> set[str]:
    names: set[str] = set()
    for record in raw_records:
        fields_raw = record.get("fields", {})
        if not isinstance(fields_raw, dict):
            continue
        for key in fields_raw:
            if isinstance(key, str):
                names.add(key)
    return names


def document_link_cfg(cfg: dict[str, Any], *, sync_phase2_cfg: Callable[[dict[str, Any]], dict[str, Any]]) -> dict[str, Any]:
    raw = sync_phase2_cfg(cfg).get("document_link", {})
    return raw if isinstance(raw, dict) else {}


def document_link_env_names(
    cfg: dict[str, Any],
    *,
    sync_phase2_cfg: Callable[[dict[str, Any]], dict[str, Any]],
) -> tuple[str, str, str | None]:
    phase2_cfg = sync_phase2_cfg(cfg)
    current_cfg = document_link_cfg(cfg, sync_phase2_cfg=sync_phase2_cfg)
    base_token_env = str(current_cfg.get("base_token_env") or phase2_cfg.get("base_token_env") or "").strip()
    table_id_env = str(current_cfg.get("table_id_env") or "").strip()
    view_id_env = str(current_cfg.get("view_id_env") or "").strip() or None
    return base_token_env, table_id_env, view_id_env


def document_link_wiki_parent_token_env(
    cfg: dict[str, Any],
    *,
    sync_phase2_cfg: Callable[[dict[str, Any]], dict[str, Any]],
) -> str | None:
    value = str(document_link_cfg(cfg, sync_phase2_cfg=sync_phase2_cfg).get("wiki_parent_token_env") or "").strip()
    return value or None


def collect_queue_preflight_errors(
    cfg: dict[str, Any],
    *,
    provider_name: Callable[[dict[str, Any]], Any],
    cli_bin: Callable[[dict[str, Any]], str],
    cli_command_parts: Callable[[str], list[str]],
    cli_command_exists: Callable[[str], bool],
    sync_phase2_cfg: Callable[[dict[str, Any]], dict[str, Any]],
    environ: dict[str, str] | os._Environ[str],
) -> list[str]:
    errors: list[str] = []
    provider_name(cfg)

    resolved_cli_bin = cli_bin(cfg)
    try:
        command = cli_command_parts(resolved_cli_bin)[0]
    except RuntimeError as exc:
        errors.append(str(exc))
        command = None
    if command and not cli_command_exists(resolved_cli_bin):
        errors.append(f"sync.phase2.cli_bin executable is not available: {command}")

    base_token_env, table_id_env, view_id_env = document_link_env_names(cfg, sync_phase2_cfg=sync_phase2_cfg)
    missing_env_names = [
        env_name
        for env_name in (base_token_env, table_id_env, view_id_env or "")
        if env_name and not str(environ.get(env_name, "")).strip()
    ]
    if not base_token_env:
        errors.append("sync.phase2.document_link.base_token_env is required, or provide sync.phase2.base_token_env")
    if not table_id_env:
        errors.append("sync.phase2.document_link.table_id_env is required")
    if missing_env_names:
        errors.append("Required environment variables are not set: " + ", ".join(missing_env_names))
    return errors


def resolve_document_link_binding(
    cfg: dict[str, Any],
    *,
    sync_phase2_cfg: Callable[[dict[str, Any]], dict[str, Any]],
    binding_factory: Callable[..., Any],
    env_value: Callable[[str], str],
    environ: dict[str, str] | os._Environ[str],
) -> Any:
    base_token_env, table_id_env, view_id_env = document_link_env_names(cfg, sync_phase2_cfg=sync_phase2_cfg)
    wiki_parent_token_env = document_link_wiki_parent_token_env(cfg, sync_phase2_cfg=sync_phase2_cfg)
    if not base_token_env:
        raise RuntimeError("sync.phase2.document_link.base_token_env is required, or provide sync.phase2.base_token_env")
    if not table_id_env:
        raise RuntimeError("sync.phase2.document_link.table_id_env is required")
    return binding_factory(
        base_token_env=base_token_env,
        table_id_env=table_id_env,
        view_id_env=view_id_env,
        wiki_parent_token_env=wiki_parent_token_env,
        base_token=env_value(base_token_env),
        table_id=env_value(table_id_env),
        view_id=env_value(view_id_env) if view_id_env else None,
        wiki_parent_token=env_value(wiki_parent_token_env) if wiki_parent_token_env and str(environ.get(wiki_parent_token_env, "")).strip() else None,
    )


def parse_queue_records(
    raw_records: list[dict[str, Any]],
    *,
    queue_record_factory: Callable[..., Any],
    document_id_field: str,
    document_key_field: str,
    version_field: str,
    lang_field: str,
    build_family_field: str,
    workflow_action_field: str,
    doc_phase_field: str,
    git_ref_field: str,
    trigger_field: str,
    legacy_trigger_fields: tuple[str, ...],
    immediate_trigger_field: str,
    force_phase2_refresh_field: str,
    upload_dingtalk_field: str,
    operator_union_id_fields: tuple[str, ...],
    dingtalk_target_node_url_fields: tuple[str, ...],
) -> list[Any]:
    records: list[Any] = []
    for record in raw_records:
        record_id = str(record.get("record_id") or "").strip()
        if not record_id:
            raise RuntimeError("Document_link record list is missing record_id")
        fields_raw = record.get("fields", {})
        fields = fields_raw if isinstance(fields_raw, dict) else {}
        records.append(
            queue_record_factory(
                record_id=record_id,
                document_id=scalar_text(fields.get(document_id_field)),
                document_key=scalar_text(fields.get(document_key_field)),
                version=scalar_text(fields.get(version_field)),
                lang=scalar_text(fields.get(lang_field)).lower(),
                build_family=scalar_text(fields.get(build_family_field)).lower(),
                workflow_action=scalar_text(fields.get(workflow_action_field)),
                doc_phase=scalar_text(fields.get(doc_phase_field)),
                git_ref=scalar_text(fields.get(git_ref_field)),
                trigger_value=scalar_text(field_value(fields, trigger_field, *legacy_trigger_fields)),
                immediate_trigger_value=fields.get(immediate_trigger_field),
                force_phase2_refresh_value=fields.get(force_phase2_refresh_field),
                upload_dingtalk_value=fields.get(upload_dingtalk_field),
                operator_union_id=scalar_text(field_value(fields, *operator_union_id_fields)),
                dingtalk_target_node_url=scalar_text(field_value(fields, *dingtalk_target_node_url_fields)),
            )
        )
    return records


def is_immediate_trigger_enabled(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = scalar_text(value).strip().lower()
    return text in {"1", "true", "y", "yes", "checked"}


def is_force_phase2_refresh_enabled(value: Any) -> bool:
    return is_immediate_trigger_enabled(value)


def is_upload_dingtalk_enabled(value: Any) -> bool:
    return is_immediate_trigger_enabled(value)


def is_trigger_requested(value: Any, *, trigger_values: set[str]) -> bool:
    return scalar_text(value).strip().lower() in trigger_values


def select_pending_queue_records(
    raw_records: list[dict[str, Any]],
    *,
    immediate_only: bool,
    workflow_action: str | None,
    doc_phase: str | None,
    record_id: str | None,
    parse_queue_records: Callable[[list[dict[str, Any]]], list[Any]],
    normalize_cli_queue_action: Callable[..., str | None],
    resolve_queue_workflow_action: Callable[[Any], str | None],
    is_trigger_requested: Callable[[Any], bool],
    is_immediate_trigger_enabled: Callable[[Any], bool],
) -> list[Any]:
    normalized_filter_doc_phase = normalize_cli_queue_action(
        workflow_action=workflow_action,
        doc_phase=doc_phase,
    )
    selected: list[Any] = []
    targeted_record = None
    for record in parse_queue_records(raw_records):
        if record_id and record.record_id == record_id:
            targeted_record = record
        if not is_trigger_requested(record.trigger_value):
            continue
        if immediate_only and not is_immediate_trigger_enabled(record.immediate_trigger_value):
            continue
        if record_id and record.record_id != record_id:
            continue
        try:
            resolved_action = resolve_queue_workflow_action(record)
        except RuntimeError:
            if record_id:
                raise
            continue
        if resolved_action is None:
            continue
        if normalized_filter_doc_phase is not None:
            if resolved_action != normalized_filter_doc_phase:
                continue
        selected.append(record)
    if record_id and not selected and targeted_record is not None:
        trigger_text = scalar_text(targeted_record.trigger_value).strip() or "<empty>"
        raise RuntimeError(
            "Targeted Document_link row is not pending because `是否触发文档构建` is not enabled. "
            f"record_id={record_id} trigger_value={trigger_text}"
        )
    return selected


def parse_document_key(document_key: str) -> tuple[str, str]:
    model, separator, region = document_key.strip().rpartition("_")
    if not separator or not model.strip() or not region.strip():
        raise RuntimeError(
            "Document_Key must use '<MODEL>_<REGION>' so the build target is unambiguous: "
            + document_key
        )
    return model.strip(), canonical_document_key_region(region)


def document_key_from_document_id(*, document_id: str, lang: str, version: str) -> str:
    candidate = document_id.strip()
    version_text = version.strip()
    lang_text = lang.strip().lower()
    if version_text and candidate.endswith("_" + version_text):
        candidate = candidate[: -(len(version_text) + 1)]
    if lang_text and candidate.lower().endswith("_" + lang_text):
        candidate = candidate[: -(len(lang_text) + 1)]
    return candidate.strip()


def looks_like_explicit_document_key(value: Any) -> bool:
    return bool(_EXPLICIT_DOCUMENT_KEY_RE.fullmatch(str(value or "").strip()))


def explicit_document_key(value: Any) -> str:
    text = str(value or "").strip()
    if looks_like_explicit_document_key(text):
        return text
    return ""


def resolve_target_for_record(record: Any, *, parse_document_key: Callable[[str], tuple[str, str]]) -> tuple[str, str]:
    candidates: list[str] = []
    explicit_key = explicit_document_key(record.document_key)
    if explicit_key:
        candidates.append(explicit_key)
    fallback_key = document_key_from_document_id(
        document_id=record.document_id,
        lang=record.lang,
        version=record.version,
    )
    if looks_like_explicit_document_key(fallback_key) and fallback_key not in candidates:
        candidates.append(fallback_key)

    errors: list[str] = []
    for candidate in candidates:
        try:
            return parse_document_key(candidate)
        except RuntimeError as exc:
            errors.append(str(exc))

    detail = (
        f"Document_ID={record.document_id!r}, Document_Key={record.document_key!r}, "
        f"Lang={record.lang!r}, Build_family={record.build_family!r}"
    )
    if errors:
        raise RuntimeError("Unable to resolve build target for queue record. " + detail + " | " + " | ".join(errors))
    raise RuntimeError("Unable to resolve build target for queue record. " + detail)


def queue_record_key(record: Any) -> str:
    explicit_key = explicit_document_key(record.document_key)
    if explicit_key:
        return explicit_key.upper()
    fallback_key = document_key_from_document_id(
        document_id=record.document_id,
        lang=record.lang,
        version=record.version,
    )
    if looks_like_explicit_document_key(fallback_key):
        return fallback_key.upper()
    return record.record_id


def queue_record_group_key(record: Any) -> str:
    explicit_key = explicit_document_key(record.document_key)
    if explicit_key:
        return explicit_key.upper()
    return record.record_id


def queue_group_lang(records: list[Any]) -> str:
    for record in records:
        if record.lang.strip():
            return record.lang.strip().lower()
    return ""


def queue_group_build_family(records: list[Any]) -> str:
    for record in records:
        if record.build_family.strip():
            return record.build_family.strip().lower()
    return ""


def queue_group_force_phase2_refresh(records: list[Any]) -> bool:
    return any(is_force_phase2_refresh_enabled(getattr(record, "force_phase2_refresh_value", None)) for record in records)


def queue_group_upload_dingtalk(records: list[Any]) -> bool:
    return any(is_upload_dingtalk_enabled(getattr(record, "upload_dingtalk_value", None)) for record in records)


def queue_group_dingtalk_target_node_url(records: list[Any]) -> str:
    for record in records:
        target_node_url = str(getattr(record, "dingtalk_target_node_url", "") or "").strip()
        if target_node_url:
            return target_node_url
    return ""


def queue_group_operator_union_id(records: list[Any]) -> str:
    for record in records:
        operator_union_id = str(getattr(record, "operator_union_id", "") or "").strip()
        if operator_union_id:
            return operator_union_id
    return ""


def validate_queue_record_group(
    records: list[Any],
    *,
    queue_record_key: Callable[[Any], str],
    resolve_queue_workflow_action: Callable[[Any], str | None],
) -> None:
    if not records:
        return
    if len(records) == 1:
        resolve_queue_workflow_action(records[0])
        return

    group_key = queue_record_key(records[0])
    workflow_actions = {resolve_queue_workflow_action(record) or "" for record in records}
    versions = {record.version.strip() for record in records}
    git_refs = {record.git_ref.strip() for record in records}
    build_families = {record.build_family.strip().lower() for record in records if record.build_family.strip()}
    force_phase2_refresh_values = {
        is_force_phase2_refresh_enabled(getattr(record, "force_phase2_refresh_value", None))
        for record in records
    }
    upload_dingtalk_values = {
        is_upload_dingtalk_enabled(getattr(record, "upload_dingtalk_value", None))
        for record in records
    }
    dingtalk_target_node_urls = {
        str(getattr(record, "dingtalk_target_node_url", "") or "").strip()
        for record in records
    }
    operator_union_ids = {
        str(getattr(record, "operator_union_id", "") or "").strip()
        for record in records
    }
    conflicts: list[str] = []
    if len(workflow_actions) > 1:
        conflicts.append("Workflow_action")
    if len(versions) > 1:
        conflicts.append("Version")
    if len(git_refs) > 1:
        conflicts.append("Git_ref")
    if len(build_families) > 1:
        conflicts.append("Build_family")
    if len(force_phase2_refresh_values) > 1:
        conflicts.append("是否强制刷新数据")
    if len(upload_dingtalk_values) > 1:
        conflicts.append("是否上传钉钉")
    if True in upload_dingtalk_values and len(dingtalk_target_node_urls) > 1:
        conflicts.append("DingTalk_target_node_url")
    if True in upload_dingtalk_values and len(operator_union_ids) > 1:
        conflicts.append("operator_union_id")
    if conflicts:
        raise RuntimeError(
            "Queue rows merged by Document_Key must agree on "
            + ", ".join(conflicts)
            + f": {group_key}"
        )
