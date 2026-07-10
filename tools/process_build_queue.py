#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Any

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)


def _service_module() -> Any:
    return sys.modules[__name__]

from tools.data_snapshot import resolve_phase2_export_root  # noqa: E402
from tools.process_build_queue_main import run_main as _run_main_impl  # noqa: E402
from tools.queue_contract import (  # noqa: E402
    BUILD_FAMILY_FIELD as _QC_BUILD_FAMILY_FIELD,
    BUILD_STARTED_AT_FIELD as _QC_BUILD_STARTED_AT_FIELD,
    DATA_SYNC_FIELD as _QC_DATA_SYNC_FIELD,
    DINGTALK_TARGET_NODE_URL_FIELD as _QC_DINGTALK_TARGET_NODE_URL_FIELD,
    DOCUMENT_DIRECTORY_FIELD as _QC_DOCUMENT_DIRECTORY_FIELD,
    DOCUMENT_LINK_DD_FIELD as _QC_DOCUMENT_LINK_DD_FIELD,
    DOCUMENT_ID_FIELD as _QC_DOCUMENT_ID_FIELD,
    DOCUMENT_KEY_FIELD as _QC_DOCUMENT_KEY_FIELD,
    BASELINE_DOC_FIELD as _QC_BASELINE_DOC_FIELD,
    DOCUMENT_LINK_FIELD as _QC_DOCUMENT_LINK_FIELD,
    FEISHU_CLOUD_DOC_FIELD as _QC_FEISHU_CLOUD_DOC_FIELD,
    HTML_LINK_FIELD as _QC_HTML_LINK_FIELD,
    DOC_PHASE_FIELD as _QC_DOC_PHASE_FIELD,
    DONE_TRIGGER_VALUE as _QC_DONE_TRIGGER_VALUE,
    FAILED_PREFIX as _QC_FAILED_PREFIX,
    FORCE_PHASE2_REFRESH_FIELD as _QC_FORCE_PHASE2_REFRESH_FIELD,
    GIT_REF_FIELD as _QC_GIT_REF_FIELD,
    IMMEDIATE_TRIGGER_FIELD as _QC_IMMEDIATE_TRIGGER_FIELD,
    LANG_FIELD as _QC_LANG_FIELD,
    LEGACY_TRIGGER_FIELDS as _QC_LEGACY_TRIGGER_FIELDS,
    OPERATOR_UNION_ID_FIELD as _QC_OPERATOR_UNION_ID_FIELD,
    RESULT_FIELD as _QC_RESULT_FIELD,
    RUNNING_PREFIX as _QC_RUNNING_PREFIX,
    SUCCESS_PREFIX as _QC_SUCCESS_PREFIX,
    TRIGGER_FIELD as _QC_TRIGGER_FIELD,
    TRIGGER_VALUES as _QC_TRIGGER_VALUES,
    UPLOAD_DINGTALK_FIELD as _QC_UPLOAD_DINGTALK_FIELD,
    VERSION_FIELD as _QC_VERSION_FIELD,
    WORKFLOW_ACTION_FIELD as _QC_WORKFLOW_ACTION_FIELD,
    DocumentLinkBinding,
    QueueRecord,
    WikiDestination,
)
from tools.document_link_queue import (  # noqa: E402
    available_field_names as _available_field_names_impl,
    field_value as _field_value_impl,
    parse_document_key as _parse_document_key_impl,
    scalar_text as _scalar_text_impl,
)
from tools.document_link_actions import (  # noqa: E402
    DRAFT_PACKAGE_ACTION_LABEL,
    PUBLISH_ACTION_LABEL,
    best_effort_queue_workflow_action as _best_effort_queue_workflow_action,
    normalize_cli_queue_action as _normalize_cli_queue_action,
    normalize_doc_phase as _normalize_doc_phase,
    normalize_workflow_action as _normalize_workflow_action,
    warn_legacy_cli_doc_phase as _warn_legacy_cli_doc_phase,
    warn_legacy_record_doc_phase as _warn_legacy_record_doc_phase,
    workflow_action_label as _workflow_action_label,
)
from tools.phase2_support import (  # noqa: E402
    LarkCliSource,
    cli_bin as _cli_bin,
    load_config,
    phase2_identity as _phase2_identity,
)
from tools.process_build_queue_bootstrap import configure_queue_bound_providers  # noqa: E402
from tools.process_build_queue_services import (  # noqa: E402
    best_effort_queue_workflow_action as _best_effort_queue_workflow_action_service,
    build_document_for_task as _build_document_for_task_service,
    build_failure_fields as _build_failure_fields_service,
    build_failure_writeback_fields as _build_failure_writeback_fields_service,
    build_py_sync_data_command as _build_py_sync_data_command_service,
    build_py_target_command as _build_py_target_command_service,
    build_started_fields as _build_started_fields_service,
    build_success_fields as _build_success_fields_service,
    ensure_dingtalk_session_ready as _ensure_dingtalk_session_ready_service,
    finalize_cloud_doc as _finalize_cloud_doc_service,
    import_markdown_to_cloud_doc as _import_markdown_to_cloud_doc_service,
    move_drive_file_to_wiki as _move_drive_file_to_wiki_service,
    publish_word_artifact as _publish_word_artifact_service,
    process_build_queue as _process_build_queue_service,
    resolve_artifact_destination as _resolve_artifact_destination_service,
    resolve_dingtalk_mirror_destination as _resolve_dingtalk_mirror_destination_service,
    resolve_wiki_destination as _resolve_wiki_destination_service,
    sync_phase2_snapshot_before_queue as _sync_phase2_snapshot_before_queue_service,
    upload_word_to_drive as _upload_word_to_drive_service,
    wait_for_wiki_move_task as _wait_for_wiki_move_task_service,
)
from tools.queue_build_execution import BuiltDocumentOutputs  # noqa: E402
from tools.dingtalk.alidocs_session import (  # noqa: E402
    load_session_config_for_operator_union_id,
    upload_file_to_node,
)
from tools.queue_artifact_sink import (  # noqa: E402
    ArtifactDestination,
    ArtifactPublishResult,
    artifact_mirror_provider,
    collect_artifact_sink_preflight_errors,
)
from tools.queue_bound_outputs import (  # noqa: E402
    publish_release_latest_dir_for_target as _publish_release_latest_dir_for_target,
    publish_release_root_for_target as _publish_release_root_for_target,
    publish_release_version_dir_for_target as _publish_release_version_dir_for_target,
    repo_relative as _repo_relative,
    resolve_docs_dir_for_config as _resolve_docs_dir_for_config,
    resolve_html_output_dir_for_target,
    resolve_md_output_path_for_target,
    resolve_pdf_output_path_for_target,
    resolve_word_output_path_for_target,
    stage_draft_md_output_to_host_repo as _stage_draft_md_output_to_host_repo,
    stage_draft_word_output_to_host_repo as _stage_draft_word_output_to_host_repo,
    stage_publish_assets_to_host_repo as _stage_publish_assets_to_host_repo,
    versioned_md_output_path as _versioned_md_output_path,
    versioned_pdf_output_path as _versioned_pdf_output_path,
    versioned_word_output_path as _versioned_word_output_path,
    write_publish_release_metadata,
)
from tools.queue_bound_lark_ops import (  # noqa: E402
    cli_relative_file_arg as _cli_relative_file_arg,
    get_wiki_node,
    run_lark_cli_json as _run_lark_cli_json,
)
from tools.queue_bound_binding import (  # noqa: E402
    collect_queue_preflight_errors as _collect_queue_preflight_errors_impl,
    document_link_cfg as _document_link_cfg,
    document_link_env_names as _document_link_env_names,
    document_link_wiki_parent_token_env as _document_link_wiki_parent_token_env,
    resolve_document_link_binding,
)
from tools.queue_bound_runtime import (  # noqa: E402
    build_py_sync_data_command as _bound_build_py_sync_data_command,
    build_py_target_command as _bound_build_py_target_command,
    prepare_git_ref_worktree as _prepare_git_ref_worktree,
    remove_worktree as _remove_worktree,
    run_command as _run_command,
    run_git as _run_git,
    worktree_dir_for_git_ref as _worktree_dir_for_git_ref,
)
from tools.queue_bound_records import (  # noqa: E402
    group_pending_queue_records,
    is_immediate_trigger_enabled as _is_immediate_trigger_enabled,
    is_trigger_requested as _is_trigger_requested,
    parse_queue_records,
    queue_group_dingtalk_target_node_url,
    queue_group_force_phase2_refresh,
    queue_group_upload_dingtalk,
    pending_immediate_queue_records,
    pending_queue_records,
    queue_group_build_family,
    queue_group_lang,
    queue_group_operator_union_id,
    queue_record_action_source,
    queue_record_key,
    queue_record_legacy_doc_phase,
    queue_record_uses_legacy_doc_phase,
    resolve_config_path_for_task,
    resolve_queue_workflow_action,
    resolve_target_for_record,
    select_pending_queue_records,
    validate_queue_record_group,
)
from tools.queue_outputs import config_path_in_repo_root as _config_path_in_repo_root_impl  # noqa: E402
from tools.queue_runtime import command_failure_message as _command_failure_message  # noqa: E402

configure_queue_bound_providers(
    repo_root_provider=lambda: ROOT,
    config_loader_provider=lambda: load_config,
    resolve_config_path_provider=lambda: _service_module().resolve_config_path_for_task,
)


def collect_queue_preflight_errors(cfg: dict[str, Any]) -> list[str]:
    errors = _collect_queue_preflight_errors_impl(cfg)
    errors.extend(collect_artifact_sink_preflight_errors(cfg, environ=os.environ))
    return errors


def resolve_artifact_mirror_provider(cfg: dict[str, Any]) -> str | None:
    return artifact_mirror_provider(cfg, environ=os.environ)

TRIGGER_FIELD = _QC_TRIGGER_FIELD
LEGACY_TRIGGER_FIELDS = _QC_LEGACY_TRIGGER_FIELDS
RESULT_FIELD = _QC_RESULT_FIELD
DOCUMENT_ID_FIELD = _QC_DOCUMENT_ID_FIELD
DOCUMENT_KEY_FIELD = _QC_DOCUMENT_KEY_FIELD
VERSION_FIELD = _QC_VERSION_FIELD
LANG_FIELD = _QC_LANG_FIELD
BUILD_FAMILY_FIELD = _QC_BUILD_FAMILY_FIELD
WORKFLOW_ACTION_FIELD = _QC_WORKFLOW_ACTION_FIELD
DOC_PHASE_FIELD = _QC_DOC_PHASE_FIELD
GIT_REF_FIELD = _QC_GIT_REF_FIELD
BUILD_STARTED_AT_FIELD = _QC_BUILD_STARTED_AT_FIELD
DATA_SYNC_FIELD = _QC_DATA_SYNC_FIELD
DOCUMENT_DIRECTORY_FIELD = _QC_DOCUMENT_DIRECTORY_FIELD
DOCUMENT_LINK_FIELD = _QC_DOCUMENT_LINK_FIELD
DOCUMENT_LINK_DD_FIELD = _QC_DOCUMENT_LINK_DD_FIELD
FEISHU_CLOUD_DOC_FIELD = _QC_FEISHU_CLOUD_DOC_FIELD
BASELINE_DOC_FIELD = _QC_BASELINE_DOC_FIELD
HTML_LINK_FIELD = _QC_HTML_LINK_FIELD
DINGTALK_TARGET_NODE_URL_FIELD = _QC_DINGTALK_TARGET_NODE_URL_FIELD
FORCE_PHASE2_REFRESH_FIELD = _QC_FORCE_PHASE2_REFRESH_FIELD
UPLOAD_DINGTALK_FIELD = _QC_UPLOAD_DINGTALK_FIELD
IMMEDIATE_TRIGGER_FIELD = _QC_IMMEDIATE_TRIGGER_FIELD
OPERATOR_UNION_ID_FIELD = _QC_OPERATOR_UNION_ID_FIELD
SUCCESS_PREFIX = _QC_SUCCESS_PREFIX
RUNNING_PREFIX = _QC_RUNNING_PREFIX
FAILED_PREFIX = _QC_FAILED_PREFIX
TRIGGER_VALUES = _QC_TRIGGER_VALUES
DONE_TRIGGER_VALUE = _QC_DONE_TRIGGER_VALUE


_scalar_text = _scalar_text_impl
_field_value = _field_value_impl
_available_field_names = _available_field_names_impl


normalize_workflow_action = _normalize_workflow_action
normalize_doc_phase = _normalize_doc_phase


workflow_action_label = _workflow_action_label


parse_document_key = _parse_document_key_impl


_config_path_in_repo_root = _config_path_in_repo_root_impl


upload_word_to_drive = partial(_upload_word_to_drive_service, _service_module())
resolve_wiki_destination = partial(_resolve_wiki_destination_service, _service_module())
resolve_artifact_destination = partial(_resolve_artifact_destination_service, _service_module())
resolve_dingtalk_mirror_destination = partial(_resolve_dingtalk_mirror_destination_service, _service_module())
ensure_dingtalk_session_ready = partial(_ensure_dingtalk_session_ready_service, _service_module())
wait_for_wiki_move_task = partial(_wait_for_wiki_move_task_service, _service_module())
move_drive_file_to_wiki = partial(_move_drive_file_to_wiki_service, _service_module())
publish_word_artifact = partial(_publish_word_artifact_service, _service_module())
import_markdown_to_cloud_doc = partial(_import_markdown_to_cloud_doc_service, _service_module())
finalize_cloud_doc = partial(_finalize_cloud_doc_service, _service_module())


def _build_py_target_command(
    *,
    repo_root: Path = ROOT,
    action: str,
    config_path: Path,
    model: str,
    region: str,
    data_root: str | None,
    lang: str | None = None,
    source: str | None = None,
    no_clean: bool = False,
    idml_mode: str | None = None,
) -> list[str]:
    return _build_py_target_command_service(
        _service_module(),
        repo_root=repo_root,
        action=action,
        config_path=config_path,
        model=model,
        region=region,
        data_root=data_root,
        lang=lang,
        source=source,
        no_clean=no_clean,
        idml_mode=idml_mode,
    )


def _build_py_sync_data_command(*, repo_root: Path = ROOT, config_path: Path, data_root: str | None) -> list[str]:
    return _build_py_sync_data_command_service(
        _service_module(),
        repo_root=repo_root,
        config_path=config_path,
        data_root=data_root,
    )


def sync_phase2_snapshot_before_queue(*, config_path: Path, data_root: str | None) -> None:
    _sync_phase2_snapshot_before_queue_service(
        _service_module(),
        config_path=config_path,
        data_root=data_root,
    )


def build_document_for_task(
    *,
    config_path: Path,
    model: str,
    region: str,
    data_root: str | None,
    doc_phase: str | None,
    lang: str | None = None,
    version: str = "",
    git_ref: str = "",
) -> Any:
    return _build_document_for_task_service(
        _service_module(),
        config_path=config_path,
        model=model,
        region=region,
        data_root=data_root,
        doc_phase=doc_phase,
        lang=lang,
        version=version,
        git_ref=git_ref,
    )


def build_success_fields(
    *,
    version: str,
    word_output_path: Path,
    document_link_url: str,
    built_at: datetime,
    document_link_dd_url: str = "",
    feishu_cloud_doc_url: str = "",
    workflow_action: str | None = None,
    doc_phase: str | None = None,
    data_sync_status: str = "",
    status_notes: tuple[str, ...] = (),
    clear_force_phase2_refresh: bool = True,
    write_data_sync: bool = True,
    write_document_link_dd: bool = False,
    write_feishu_cloud_doc: bool = False,
) -> dict[str, Any]:
    return _build_success_fields_service(
        _service_module(),
        version=version,
        word_output_path=word_output_path,
        document_link_url=document_link_url,
        document_link_dd_url=document_link_dd_url,
        feishu_cloud_doc_url=feishu_cloud_doc_url,
        built_at=built_at,
        workflow_action=workflow_action,
        doc_phase=doc_phase,
        data_sync_status=data_sync_status,
        status_notes=status_notes,
        clear_force_phase2_refresh=clear_force_phase2_refresh,
        write_data_sync=write_data_sync,
        write_document_link_dd=write_document_link_dd,
        write_feishu_cloud_doc=write_feishu_cloud_doc,
    )


def build_started_fields(
    *,
    started_at: datetime,
    version: str = "",
    workflow_action: str | None = None,
    doc_phase: str | None = None,
    data_sync_status: str = "",
) -> dict[str, Any]:
    return _build_started_fields_service(
        _service_module(),
        started_at=started_at,
        version=version,
        workflow_action=workflow_action,
        doc_phase=doc_phase,
        data_sync_status=data_sync_status,
    )


def build_failure_fields(
    *,
    version: str,
    message: str,
    workflow_action: str | None = None,
    doc_phase: str | None = None,
    data_sync_status: str = "",
) -> dict[str, Any]:
    return _build_failure_fields_service(
        _service_module(),
        version=version,
        message=message,
        workflow_action=workflow_action,
        doc_phase=doc_phase,
        data_sync_status=data_sync_status,
    )


def build_failure_writeback_fields(
    *,
    version: str,
    message: str,
    workflow_action: str | None = None,
    doc_phase: str | None = None,
    data_sync_status: str = "",
    word_output_path: Path | None = None,
    document_link_url: str | None = None,
    document_link_dd_url: str | None = None,
    feishu_cloud_doc_url: str | None = None,
    clear_force_phase2_refresh: bool = True,
    write_data_sync: bool = True,
    write_document_link_dd: bool = False,
    write_feishu_cloud_doc: bool = False,
) -> dict[str, Any]:
    return _build_failure_writeback_fields_service(
        _service_module(),
        version=version,
        message=message,
        workflow_action=workflow_action,
        doc_phase=doc_phase,
        data_sync_status=data_sync_status,
        word_output_path=word_output_path,
        document_link_url=document_link_url,
        document_link_dd_url=document_link_dd_url,
        feishu_cloud_doc_url=feishu_cloud_doc_url,
        clear_force_phase2_refresh=clear_force_phase2_refresh,
        write_data_sync=write_data_sync,
        write_document_link_dd=write_document_link_dd,
        write_feishu_cloud_doc=write_feishu_cloud_doc,
    )


def normalize_cli_queue_action(*, workflow_action: str | None = None, doc_phase: str | None = None) -> str | None:
    return _normalize_cli_queue_action(workflow_action=workflow_action, doc_phase=doc_phase)


def warn_legacy_cli_doc_phase(doc_phase: str | None, workflow_action: str | None) -> None:
    _warn_legacy_cli_doc_phase(doc_phase, workflow_action)


def warn_legacy_record_doc_phase(record: QueueRecord) -> None:
    _warn_legacy_record_doc_phase(
        record_id=record.record_id,
        workflow_action=record.workflow_action,
        doc_phase=record.doc_phase,
    )


def best_effort_queue_workflow_action(record: QueueRecord) -> str | None:
    return _best_effort_queue_workflow_action_service(_service_module(), record)


def process_build_queue(
    *,
    cfg: dict[str, Any],
    config_path: Path,
    data_root: str | None,
    dry_run: bool,
    immediate_only: bool = False,
    workflow_action: str | None = None,
    doc_phase: str | None = None,
    record_id: str | None = None,
) -> int:
    return _process_build_queue_service(
        _service_module(),
        cfg=cfg,
        config_path=config_path,
        data_root=data_root,
        dry_run=dry_run,
        immediate_only=immediate_only,
        workflow_action=workflow_action,
        doc_phase=doc_phase,
        record_id=record_id,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Consume Document_link build tasks and write draft-package or publish results back to Feishu.")
    ap.add_argument("--config", required=True, help="Config YAML path")
    ap.add_argument("--data-root", default=None, help="Override structured content snapshot root")
    ap.add_argument("--dry-run", action="store_true", help="List pending tasks without building or writing back")
    ap.add_argument(
        "--workflow-action",
        choices=("build-draft-package", "draft", "publish"),
        default=None,
        help="Only consume queue rows for one normalized Workflow_action (Build Draft Package or Publish)",
    )
    ap.add_argument(
        "--doc-phase",
        choices=("draft", "publish"),
        default=None,
        help="Unsupported legacy filter; use --workflow-action and keep queue rows on Workflow_action only",
    )
    ap.add_argument("--record-id", default=None, help="Only consume one Document_link record_id")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    return _run_main_impl(
        argv,
        parse_args=parse_args,
        repo_root=ROOT,
        load_config=load_config,
        resolve_phase2_export_root=resolve_phase2_export_root,
        process_build_queue=process_build_queue,
    )


if __name__ == "__main__":
    raise SystemExit(main())
