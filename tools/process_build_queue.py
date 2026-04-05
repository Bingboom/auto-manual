#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_docs import build_root_for_target, render_build_template, resolve_output_path  # noqa: E402
from tools.data_snapshot import resolve_phase2_export_root  # noqa: E402
from tools.queue_contract import (  # noqa: E402
    BUILD_FAMILY_FIELD as _QC_BUILD_FAMILY_FIELD,
    BUILD_STARTED_AT_FIELD as _QC_BUILD_STARTED_AT_FIELD,
    DOCUMENT_DIRECTORY_FIELD as _QC_DOCUMENT_DIRECTORY_FIELD,
    DOCUMENT_ID_FIELD as _QC_DOCUMENT_ID_FIELD,
    DOCUMENT_KEY_FIELD as _QC_DOCUMENT_KEY_FIELD,
    DOCUMENT_LINK_FIELD as _QC_DOCUMENT_LINK_FIELD,
    DOC_PHASE_FIELD as _QC_DOC_PHASE_FIELD,
    DONE_TRIGGER_VALUE as _QC_DONE_TRIGGER_VALUE,
    FAILED_PREFIX as _QC_FAILED_PREFIX,
    GIT_REF_FIELD as _QC_GIT_REF_FIELD,
    IMMEDIATE_TRIGGER_FIELD as _QC_IMMEDIATE_TRIGGER_FIELD,
    LANG_FIELD as _QC_LANG_FIELD,
    LEGACY_TRIGGER_FIELDS as _QC_LEGACY_TRIGGER_FIELDS,
    RESULT_FIELD as _QC_RESULT_FIELD,
    SUCCESS_PREFIX as _QC_SUCCESS_PREFIX,
    TRIGGER_FIELD as _QC_TRIGGER_FIELD,
    TRIGGER_VALUES as _QC_TRIGGER_VALUES,
    VERSION_FIELD as _QC_VERSION_FIELD,
    WORKFLOW_ACTION_FIELD as _QC_WORKFLOW_ACTION_FIELD,
    DocumentLinkBinding,
    QueueRecord,
    WikiDestination,
)
from tools.document_link_queue import (  # noqa: E402
    available_field_names as _available_field_names_impl,
    collect_queue_preflight_errors as _collect_queue_preflight_errors_impl,
    document_link_cfg as _document_link_cfg_impl,
    document_link_env_names as _document_link_env_names_impl,
    document_link_wiki_parent_token_env as _document_link_wiki_parent_token_env_impl,
    field_value as _field_value_impl,
    is_immediate_trigger_enabled as _is_immediate_trigger_enabled_impl,
    is_trigger_requested as _is_trigger_requested_impl,
    parse_document_key as _parse_document_key_impl,
    parse_queue_records as _parse_queue_records_impl,
    queue_group_build_family as _queue_group_build_family_impl,
    queue_group_lang as _queue_group_lang_impl,
    queue_record_key as _queue_record_key_impl,
    resolve_document_link_binding as _resolve_document_link_binding_impl,
    resolve_target_for_record as _resolve_target_for_record_impl,
    scalar_text as _scalar_text_impl,
    select_pending_queue_records as _select_pending_queue_records_impl,
    validate_queue_record_group as _validate_queue_record_group_impl,
)
from tools.document_link_actions import (  # noqa: E402
    DRAFT_PACKAGE_ACTION_LABEL,
    PUBLISH_ACTION_LABEL,
    best_effort_queue_workflow_action as _best_effort_queue_workflow_action,
    legacy_doc_phase_value as _legacy_doc_phase_value,
    normalize_cli_queue_action as _normalize_cli_queue_action,
    normalize_doc_phase as _normalize_doc_phase,
    normalize_workflow_action as _normalize_workflow_action,
    resolve_workflow_action as _resolve_workflow_action,
    warn_legacy_cli_doc_phase as _warn_legacy_cli_doc_phase,
    warn_legacy_record_doc_phase as _warn_legacy_record_doc_phase,
    workflow_action_label as _workflow_action_label,
    workflow_action_source as _workflow_action_source,
    workflow_action_uses_legacy_doc_phase as _workflow_action_uses_legacy_doc_phase,
)
from tools.queue_config_resolution import (  # noqa: E402
    build_languages as _build_languages,
    queue_by_document_key as _queue_by_document_key,
    resolve_config_path_for_task as _resolve_config_path_for_task,
)
from tools.queue_outputs import (  # noqa: E402
    config_path_in_repo_root as _config_path_in_repo_root_impl,
    copy_tree as _copy_tree_impl,
    publish_release_latest_dir_for_target as _publish_release_latest_dir_for_target_impl,
    publish_release_root_for_target as _publish_release_root_for_target_impl,
    publish_release_version_dir_for_target as _publish_release_version_dir_for_target_impl,
    repo_relative as _repo_relative_impl,
    resolve_docs_dir_for_config as _resolve_docs_dir_for_config_impl,
    resolve_html_output_dir_for_target as _resolve_html_output_dir_for_target_impl,
    resolve_word_output_path_for_target as _resolve_word_output_path_for_target_impl,
    stage_draft_word_output_to_host_repo as _stage_draft_word_output_to_host_repo_impl,
    stage_publish_assets_to_host_repo as _stage_publish_assets_to_host_repo_impl,
    versioned_word_output_path as _versioned_word_output_path_impl,
    write_publish_release_metadata as _write_publish_release_metadata_impl,
)
from tools.queue_build_execution import (  # noqa: E402
    build_document_for_task as _build_document_for_task_impl,
    build_py_sync_data_command as _build_py_sync_data_command_impl,
    build_py_target_command as _build_py_target_command_impl,
    sync_phase2_snapshot_before_queue as _sync_phase2_snapshot_before_queue_impl,
)
from tools.queue_dry_run import print_dry_run_groups as _print_dry_run_groups_impl  # noqa: E402
from tools.queue_group_processing import (  # noqa: E402
    process_queue_record_group as _process_queue_record_group_impl,
)
from tools.queue_session import (  # noqa: E402
    bootstrap_queue_session as _bootstrap_queue_session_impl,
    load_pending_queue_state as _load_pending_queue_state_impl,
    print_no_pending_message as _print_no_pending_message_impl,
    resolve_and_report_wiki_destination as _resolve_and_report_wiki_destination_impl,
)
from tools.queue_lark_ops import (  # noqa: E402
    cli_relative_file_arg as _cli_relative_file_arg_impl,
    get_wiki_node as _get_wiki_node_impl,
    host_root_from_url as _host_root_from_url_impl,
    move_drive_file_to_wiki as _move_drive_file_to_wiki_impl,
    move_result_entry_from_task_payload as _move_result_entry_from_task_payload_impl,
    resolve_wiki_destination as _resolve_wiki_destination_impl,
    run_lark_cli_json as _run_lark_cli_json_impl,
    upload_word_to_drive as _upload_word_to_drive_impl,
    wait_for_wiki_move_task as _wait_for_wiki_move_task_impl,
    wiki_node_from_payload as _wiki_node_from_payload_impl,
    wiki_url_from_host_root as _wiki_url_from_host_root_impl,
)
from tools.queue_runtime import (  # noqa: E402
    command_failure_message as _command_failure_message_impl,
    format_command as _format_command_impl,
    prepare_git_ref_worktree as _prepare_git_ref_worktree_impl,
    remove_worktree as _remove_worktree_impl,
    run_command as _run_command_impl,
    run_git as _run_git_impl,
    slug_ref_token as _slug_ref_token_impl,
    worktree_dir_for_git_ref as _worktree_dir_for_git_ref_impl,
)
from tools.queue_writeback import (  # noqa: E402
    build_failure_fields as _build_failure_fields,
    build_failure_writeback_fields as _build_failure_writeback_fields,
    build_started_fields as _build_started_fields,
    build_success_fields as _build_success_fields,
)
from tools.release_contract import (  # noqa: E402
    normalize_release_token,
    release_lang_for_config,
    release_latest_dir_for_target,
    release_root_for_target,
    release_version_dir_for_target,
)
from tools.sync_data import (  # noqa: E402
    LarkCliSource,
    _cli_bin,
    _cli_command_exists,
    _cli_command_parts,
    _env_value,
    _phase2_identity,
    _parse_json_payload,
    _provider_name,
    _resolved_cli_command_parts,
    _sync_phase2_cfg,
    load_config,
)
from tools.utils.targets import resolve_output_lang  # noqa: E402

TRIGGER_FIELD = "是否触发文档构建"
LEGACY_TRIGGER_FIELDS = ("是否构建文档？",)
RESULT_FIELD = "构建结果"
DOCUMENT_ID_FIELD = "Document_ID"
DOCUMENT_KEY_FIELD = "Document_Key"
VERSION_FIELD = "Version"
LANG_FIELD = "Lang"
BUILD_FAMILY_FIELD = "Build_family"
WORKFLOW_ACTION_FIELD = "Workflow_action"
DOC_PHASE_FIELD = "Doc_phase"
GIT_REF_FIELD = "Git_ref"
BUILD_STARTED_AT_FIELD = "开始构建时间"
DOCUMENT_DIRECTORY_FIELD = "Document directory"
DOCUMENT_LINK_FIELD = "Document link"
IMMEDIATE_TRIGGER_FIELD = "是否立即构建"

SUCCESS_PREFIX = "SUCCESS"
FAILED_PREFIX = "FAILED"
TRIGGER_VALUES = {"1", "true", "y", "yes"}
DONE_TRIGGER_VALUE = "已构建"


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
DOCUMENT_DIRECTORY_FIELD = _QC_DOCUMENT_DIRECTORY_FIELD
DOCUMENT_LINK_FIELD = _QC_DOCUMENT_LINK_FIELD
IMMEDIATE_TRIGGER_FIELD = _QC_IMMEDIATE_TRIGGER_FIELD
SUCCESS_PREFIX = _QC_SUCCESS_PREFIX
FAILED_PREFIX = _QC_FAILED_PREFIX
TRIGGER_VALUES = _QC_TRIGGER_VALUES
DONE_TRIGGER_VALUE = _QC_DONE_TRIGGER_VALUE


def _document_link_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    return _document_link_cfg_impl(cfg, sync_phase2_cfg=_sync_phase2_cfg)


def _document_link_env_names(cfg: dict[str, Any]) -> tuple[str, str, str | None]:
    return _document_link_env_names_impl(cfg, sync_phase2_cfg=_sync_phase2_cfg)


def _document_link_wiki_parent_token_env(cfg: dict[str, Any]) -> str | None:
    return _document_link_wiki_parent_token_env_impl(cfg, sync_phase2_cfg=_sync_phase2_cfg)


def collect_queue_preflight_errors(cfg: dict[str, Any]) -> list[str]:
    return _collect_queue_preflight_errors_impl(
        cfg,
        provider_name=_provider_name,
        cli_bin=_cli_bin,
        cli_command_parts=_cli_command_parts,
        cli_command_exists=_cli_command_exists,
        sync_phase2_cfg=_sync_phase2_cfg,
        environ=os.environ,
    )


def resolve_document_link_binding(cfg: dict[str, Any]) -> DocumentLinkBinding:
    return _resolve_document_link_binding_impl(
        cfg,
        sync_phase2_cfg=_sync_phase2_cfg,
        binding_factory=DocumentLinkBinding,
        env_value=_env_value,
        environ=os.environ,
    )


_scalar_text = _scalar_text_impl
_field_value = _field_value_impl
_available_field_names = _available_field_names_impl


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


_is_immediate_trigger_enabled = _is_immediate_trigger_enabled_impl


def _is_trigger_requested(value: Any) -> bool:
    return _is_trigger_requested_impl(value, trigger_values=TRIGGER_VALUES)


normalize_workflow_action = _normalize_workflow_action
normalize_doc_phase = _normalize_doc_phase


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


workflow_action_label = _workflow_action_label


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
        normalize_cli_queue_action=normalize_cli_queue_action,
        resolve_queue_workflow_action=resolve_queue_workflow_action,
        is_trigger_requested=_is_trigger_requested,
        is_immediate_trigger_enabled=_is_immediate_trigger_enabled,
    )


parse_document_key = _parse_document_key_impl


def _document_key_from_document_id(*, document_id: str, lang: str, version: str) -> str:
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


queue_record_key = _queue_record_key_impl
queue_group_lang = _queue_group_lang_impl
queue_group_build_family = _queue_group_build_family_impl


def resolve_config_path_for_task(*, region: str, lang: str | None, build_family: str | None = None) -> Path:
    return _resolve_config_path_for_task(
        repo_root=ROOT,
        region=region,
        lang=lang,
        build_family=build_family,
        config_loader=load_config,
    )


def group_pending_queue_records(records: list[QueueRecord]) -> list[list[QueueRecord]]:
    grouped: list[list[QueueRecord]] = []
    index_by_key: dict[str, int] = {}
    for record in records:
        model, region = resolve_target_for_record(record)
        config_path = resolve_config_path_for_task(region=region, lang=record.lang, build_family=record.build_family)
        cfg = load_config(config_path)
        if _queue_by_document_key(cfg):
            key = queue_record_key(record)
        else:
            key = record.record_id
        existing_index = index_by_key.get(key)
        if existing_index is None:
            index_by_key[key] = len(grouped)
            grouped.append([record])
            continue
        grouped[existing_index].append(record)
    return grouped


def validate_queue_record_group(records: list[QueueRecord]) -> None:
    _validate_queue_record_group_impl(
        records,
        queue_record_key=queue_record_key,
        resolve_queue_workflow_action=resolve_queue_workflow_action,
    )


def _resolve_docs_dir_for_config(config_path: Path, cfg: dict[str, Any] | None = None) -> Path:
    return _resolve_docs_dir_for_config_impl(
        config_path=config_path,
        repo_root=ROOT,
        cfg=cfg,
        config_loader=load_config,
    )


def resolve_word_output_path_for_target(*, config_path: Path, model: str, region: str) -> Path:
    return _resolve_word_output_path_for_target_impl(
        config_path=config_path,
        model=model,
        region=region,
        repo_root=ROOT,
        config_loader=load_config,
        build_languages=_build_languages,
        resolve_output_lang=resolve_output_lang,
        build_root_for_target=build_root_for_target,
        render_build_template=render_build_template,
        resolve_output_path=resolve_output_path,
    )


def resolve_html_output_dir_for_target(*, config_path: Path, model: str, region: str) -> Path:
    return _resolve_html_output_dir_for_target_impl(
        config_path=config_path,
        model=model,
        region=region,
        repo_root=ROOT,
        config_loader=load_config,
        resolve_output_lang=resolve_output_lang,
        build_root_for_target=build_root_for_target,
    )


_normalize_version_for_filename = normalize_release_token


def _versioned_word_output_path(word_output_path: Path, *, version: str, doc_phase: str | None = None) -> Path:
    return _versioned_word_output_path_impl(
        word_output_path,
        version=version,
        doc_phase=doc_phase,
        normalize_release_token=_normalize_version_for_filename,
        normalize_workflow_action=normalize_workflow_action,
    )


_config_path_in_repo_root = _config_path_in_repo_root_impl


def _repo_relative(path: Path) -> str:
    return _repo_relative_impl(path, repo_root=ROOT)


def _publish_release_root_for_target(*, config_path: Path, model: str, region: str) -> Path:
    return _publish_release_root_for_target_impl(
        repo_root=ROOT,
        config_path=config_path,
        model=model,
        region=region,
        config_loader=load_config,
        release_root_for_target=release_root_for_target,
    )


def _publish_release_version_dir_for_target(*, config_path: Path, model: str, region: str, version: str) -> Path:
    return _publish_release_version_dir_for_target_impl(
        repo_root=ROOT,
        config_path=config_path,
        model=model,
        region=region,
        version=version,
        config_loader=load_config,
        release_version_dir_for_target=release_version_dir_for_target,
    )


def _publish_release_latest_dir_for_target(*, config_path: Path, model: str, region: str) -> Path:
    return _publish_release_latest_dir_for_target_impl(
        repo_root=ROOT,
        config_path=config_path,
        model=model,
        region=region,
        config_loader=load_config,
        release_latest_dir_for_target=release_latest_dir_for_target,
    )


_slug_ref_token = _slug_ref_token_impl
_format_command = _format_command_impl
_command_failure_message = _command_failure_message_impl


def _run_command(cmd: list[str], *, cwd: Path = ROOT) -> None:
    _run_command_impl(
        cmd,
        cwd=cwd,
        prefix="[build-queue]",
        command_failure_message=_command_failure_message,
    )


def _run_git(args: list[str], *, cwd: Path = ROOT) -> None:
    _run_git_impl(args, repo_root=cwd, run_command=_run_command)


def _worktree_dir_for_git_ref(git_ref: str) -> Path:
    return _worktree_dir_for_git_ref_impl(repo_root=ROOT, git_ref=git_ref)


def _remove_worktree(path: Path) -> None:
    _remove_worktree_impl(repo_root=ROOT, path=path)


def _prepare_git_ref_worktree(git_ref: str) -> Path:
    return _prepare_git_ref_worktree_impl(
        repo_root=ROOT,
        git_ref=git_ref,
        run_git=_run_git,
        worktree_dir_for_git_ref=_worktree_dir_for_git_ref,
        remove_worktree=lambda *, repo_root, path: _remove_worktree(path),
    )


def _run_lark_cli_json(*, cli_bin: str, args: list[str]) -> dict[str, Any]:
    return _run_lark_cli_json_impl(
        cli_bin=cli_bin,
        args=args,
        repo_root=ROOT,
        resolved_cli_command_parts=_resolved_cli_command_parts,
        parse_json_payload=_parse_json_payload,
        format_command=_format_command,
        command_failure_message=_command_failure_message,
    )


def _cli_relative_file_arg(path: Path) -> str:
    return _cli_relative_file_arg_impl(repo_root=ROOT, path=path)


def upload_word_to_drive(*, cli_bin: str, word_output_path: Path, identity: str) -> tuple[str, str]:
    return _upload_word_to_drive_impl(
        cli_bin=cli_bin,
        word_output_path=word_output_path,
        identity=identity,
        repo_root=ROOT,
        run_lark_cli_json=_run_lark_cli_json,
        cli_relative_file_arg=lambda *, repo_root, path: _cli_relative_file_arg(path),
    )


_wiki_node_from_payload = _wiki_node_from_payload_impl


def get_wiki_node(
    *,
    cli_bin: str,
    identity: str,
    token: str,
    obj_type: str | None = None,
) -> dict[str, Any]:
    return _get_wiki_node_impl(
        cli_bin=cli_bin,
        identity=identity,
        token=token,
        obj_type=obj_type,
        run_lark_cli_json=_run_lark_cli_json,
    )


def resolve_wiki_destination(
    *,
    cli_bin: str,
    identity: str,
    binding: DocumentLinkBinding,
) -> WikiDestination:
    return _resolve_wiki_destination_impl(
        cli_bin=cli_bin,
        identity=identity,
        binding=binding,
        get_wiki_node=get_wiki_node,
        wiki_destination_factory=WikiDestination,
    )


_host_root_from_url = _host_root_from_url_impl
_wiki_url_from_host_root = _wiki_url_from_host_root_impl
_move_result_entry_from_task_payload = _move_result_entry_from_task_payload_impl


def wait_for_wiki_move_task(
    *,
    cli_bin: str,
    identity: str,
    task_id: str,
    host_root: str,
) -> str:
    return _wait_for_wiki_move_task_impl(
        cli_bin=cli_bin,
        identity=identity,
        task_id=task_id,
        host_root=host_root,
        run_lark_cli_json=_run_lark_cli_json,
        move_result_entry_from_task_payload=_move_result_entry_from_task_payload,
        wiki_url_from_host_root=_wiki_url_from_host_root,
        sleep=time.sleep,
    )


def move_drive_file_to_wiki(
    *,
    cli_bin: str,
    identity: str,
    file_token: str,
    drive_url: str,
    destination: WikiDestination,
) -> str:
    return _move_drive_file_to_wiki_impl(
        cli_bin=cli_bin,
        identity=identity,
        file_token=file_token,
        drive_url=drive_url,
        destination=destination,
        run_lark_cli_json=_run_lark_cli_json,
        host_root_from_url=_host_root_from_url,
        wiki_url_from_host_root=_wiki_url_from_host_root,
        wait_for_wiki_move_task=wait_for_wiki_move_task,
    )


def _build_py_target_command(
    *,
    repo_root: Path = ROOT,
    action: str,
    config_path: Path,
    model: str,
    region: str,
    data_root: str | None,
    source: str | None = None,
    no_clean: bool = False,
) -> list[str]:
    return _build_py_target_command_impl(
        repo_root=repo_root,
        action=action,
        config_path=config_path,
        model=model,
        region=region,
        data_root=data_root,
        source=source,
        no_clean=no_clean,
    )


def _build_py_sync_data_command(*, repo_root: Path = ROOT, config_path: Path, data_root: str | None) -> list[str]:
    return _build_py_sync_data_command_impl(repo_root=repo_root, config_path=config_path, data_root=data_root)


def sync_phase2_snapshot_before_queue(*, config_path: Path, data_root: str | None) -> None:
    _sync_phase2_snapshot_before_queue_impl(
        repo_root=ROOT,
        config_path=config_path,
        data_root=data_root,
        run_command=_run_command,
        build_py_sync_data_command=_build_py_sync_data_command,
    )


_copy_tree = _copy_tree_impl


def _stage_draft_word_output_to_host_repo(
    *,
    built_word_output_path: Path,
    host_config_path: Path,
    model: str,
    region: str,
    version: str,
    doc_phase: str | None,
) -> Path:
    return _stage_draft_word_output_to_host_repo_impl(
        built_word_output_path=built_word_output_path,
        host_config_path=host_config_path,
        model=model,
        region=region,
        version=version,
        doc_phase=doc_phase,
        resolve_word_output_path_for_target=resolve_word_output_path_for_target,
        versioned_word_output_path=_versioned_word_output_path,
    )


def _stage_publish_assets_to_host_repo(
    *,
    built_word_output_path: Path,
    built_html_dir: Path,
    host_config_path: Path,
    model: str,
    region: str,
    version: str,
) -> tuple[Path, Path]:
    return _stage_publish_assets_to_host_repo_impl(
        built_word_output_path=built_word_output_path,
        built_html_dir=built_html_dir,
        host_config_path=host_config_path,
        model=model,
        region=region,
        version=version,
        publish_release_version_dir_for_target=_publish_release_version_dir_for_target,
        publish_release_latest_dir_for_target=_publish_release_latest_dir_for_target,
        copy_tree=_copy_tree,
    )


def write_publish_release_metadata(
    *,
    config_path: Path,
    model: str,
    region: str,
    version: str,
    git_ref: str,
    built_at: datetime,
    word_output_path: Path,
    html_dir: Path,
    document_link_url: str,
) -> Path:
    return _write_publish_release_metadata_impl(
        config_path=config_path,
        model=model,
        region=region,
        version=version,
        git_ref=git_ref,
        built_at=built_at,
        word_output_path=word_output_path,
        html_dir=html_dir,
        document_link_url=document_link_url,
        publish_release_version_dir_for_target=_publish_release_version_dir_for_target,
        publish_release_latest_dir_for_target=_publish_release_latest_dir_for_target,
        release_lang_for_config=release_lang_for_config,
        repo_relative=_repo_relative,
    )


def build_document_for_task(
    *,
    config_path: Path,
    model: str,
    region: str,
    data_root: str | None,
    doc_phase: str | None,
    version: str = "",
    git_ref: str = "",
) -> Path:
    return _build_document_for_task_impl(
        repo_root=ROOT,
        config_path=config_path,
        model=model,
        region=region,
        data_root=data_root,
        doc_phase=doc_phase,
        version=version,
        git_ref=git_ref,
        normalize_workflow_action=normalize_workflow_action,
        prepare_git_ref_worktree=_prepare_git_ref_worktree,
        remove_worktree=_remove_worktree,
        config_path_in_repo_root=_config_path_in_repo_root,
        run_command=_run_command,
        build_py_target_command=_build_py_target_command,
        resolve_word_output_path_for_target=resolve_word_output_path_for_target,
        versioned_word_output_path=_versioned_word_output_path,
        resolve_html_output_dir_for_target=resolve_html_output_dir_for_target,
        stage_publish_assets_to_host_repo=_stage_publish_assets_to_host_repo,
        stage_draft_word_output_to_host_repo=_stage_draft_word_output_to_host_repo,
    )


def build_success_fields(
    *,
    version: str,
    word_output_path: Path,
    document_link_url: str,
    built_at: datetime,
    workflow_action: str | None = None,
    doc_phase: str | None = None,
) -> dict[str, Any]:
    return _build_success_fields(
        version=version,
        word_output_path=word_output_path,
        document_link_url=document_link_url,
        built_at=built_at,
        workflow_action=workflow_action,
        doc_phase=doc_phase,
        normalize_workflow_action=normalize_workflow_action,
        normalize_doc_phase=normalize_doc_phase,
        workflow_action_label=workflow_action_label,
        result_field=RESULT_FIELD,
        document_directory_field=DOCUMENT_DIRECTORY_FIELD,
        document_link_field=DOCUMENT_LINK_FIELD,
        trigger_field=TRIGGER_FIELD,
        done_trigger_value=DONE_TRIGGER_VALUE,
        immediate_trigger_field=IMMEDIATE_TRIGGER_FIELD,
        success_prefix=SUCCESS_PREFIX,
    )


def build_started_fields(*, started_at: datetime) -> dict[str, Any]:
    return _build_started_fields(started_at=started_at, build_started_at_field=BUILD_STARTED_AT_FIELD)


def build_failure_fields(
    *,
    version: str,
    message: str,
    workflow_action: str | None = None,
    doc_phase: str | None = None,
) -> dict[str, Any]:
    return _build_failure_fields(
        version=version,
        message=message,
        workflow_action=workflow_action,
        doc_phase=doc_phase,
        normalize_workflow_action=normalize_workflow_action,
        normalize_doc_phase=normalize_doc_phase,
        workflow_action_label=workflow_action_label,
        result_field=RESULT_FIELD,
        failed_prefix=FAILED_PREFIX,
    )


def build_failure_writeback_fields(
    *,
    version: str,
    message: str,
    workflow_action: str | None = None,
    doc_phase: str | None = None,
    word_output_path: Path | None = None,
    document_link_url: str | None = None,
) -> dict[str, Any]:
    return _build_failure_writeback_fields(
        version=version,
        message=message,
        workflow_action=workflow_action,
        doc_phase=doc_phase,
        word_output_path=word_output_path,
        document_link_url=document_link_url,
        build_failure_fields=build_failure_fields,
        result_field=RESULT_FIELD,
        document_directory_field=DOCUMENT_DIRECTORY_FIELD,
        document_link_field=DOCUMENT_LINK_FIELD,
        immediate_trigger_field=IMMEDIATE_TRIGGER_FIELD,
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
    return _best_effort_queue_workflow_action(
        workflow_action=record.workflow_action,
        doc_phase=record.doc_phase,
        record_id=record.record_id,
    )


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
    session = _bootstrap_queue_session_impl(
        cfg=cfg,
        workflow_action=workflow_action,
        doc_phase=doc_phase,
        collect_queue_preflight_errors=collect_queue_preflight_errors,
        resolve_document_link_binding=resolve_document_link_binding,
        cli_bin=_cli_bin,
        phase2_identity=_phase2_identity,
        source_factory=LarkCliSource,
        normalize_cli_queue_action=normalize_cli_queue_action,
        warn_legacy_cli_doc_phase=warn_legacy_cli_doc_phase,
    )
    pending_state = _load_pending_queue_state_impl(
        source=session.source,
        binding=session.binding,
        immediate_only=immediate_only,
        workflow_action=session.normalized_cli_action,
        record_id=record_id,
        select_pending_queue_records=select_pending_queue_records,
        group_pending_queue_records=group_pending_queue_records,
        available_field_names=_available_field_names,
        build_started_at_field=BUILD_STARTED_AT_FIELD,
    )
    if pending_state is None:
        _print_no_pending_message_impl(immediate_only=immediate_only)
        return 0

    if dry_run:
        _print_dry_run_groups_impl(
            groups=pending_state.pending_groups,
            data_root=data_root,
            warn_legacy_record_doc_phase=warn_legacy_record_doc_phase,
            resolve_target_for_record=resolve_target_for_record,
            queue_group_lang=queue_group_lang,
            queue_group_build_family=queue_group_build_family,
            validate_queue_record_group=validate_queue_record_group,
            resolve_config_path_for_task=resolve_config_path_for_task,
            queue_record_key=queue_record_key,
            workflow_action_label=workflow_action_label,
            queue_record_action_source=queue_record_action_source,
            queue_record_legacy_doc_phase=queue_record_legacy_doc_phase,
        )
        return 0

    print("[build-queue] Syncing latest phase2 snapshot before building queued documents.")
    sync_phase2_snapshot_before_queue(
        config_path=config_path,
        data_root=data_root,
    )
    pending_state = _load_pending_queue_state_impl(
        source=session.source,
        binding=session.binding,
        immediate_only=immediate_only,
        workflow_action=session.normalized_cli_action,
        record_id=record_id,
        select_pending_queue_records=select_pending_queue_records,
        group_pending_queue_records=group_pending_queue_records,
        available_field_names=_available_field_names,
        build_started_at_field=BUILD_STARTED_AT_FIELD,
    )
    if pending_state is None:
        print("[build-queue] Queue changed during sync; no pending build tasks remain.")
        return 0

    wiki_destination = _resolve_and_report_wiki_destination_impl(
        cli_bin=session.cli_bin,
        identity=session.identity,
        binding=session.binding,
        resolve_wiki_destination=resolve_wiki_destination,
    )

    failures: list[str] = []
    processed = 0
    for group in pending_state.pending_groups:
        result = _process_queue_record_group_impl(
            group=group,
            source=session.source,
            binding=session.binding,
            data_root=data_root,
            can_write_started_at=pending_state.can_write_started_at,
            cli_bin=session.cli_bin,
            identity=session.identity,
            wiki_destination=wiki_destination,
            warn_legacy_record_doc_phase=warn_legacy_record_doc_phase,
            validate_queue_record_group=validate_queue_record_group,
            resolve_target_for_record=resolve_target_for_record,
            queue_group_lang=queue_group_lang,
            queue_group_build_family=queue_group_build_family,
            resolve_config_path_for_task=resolve_config_path_for_task,
            resolve_queue_workflow_action=resolve_queue_workflow_action,
            build_started_fields=build_started_fields,
            build_document_for_task=build_document_for_task,
            upload_word_to_drive=upload_word_to_drive,
            move_drive_file_to_wiki=move_drive_file_to_wiki,
            build_success_fields=build_success_fields,
            queue_record_legacy_doc_phase=queue_record_legacy_doc_phase,
            publish_release_latest_dir_for_target=_publish_release_latest_dir_for_target,
            write_publish_release_metadata=write_publish_release_metadata,
            workflow_action_label=workflow_action_label,
            queue_record_key=queue_record_key,
            build_failure_writeback_fields=build_failure_writeback_fields,
            best_effort_queue_workflow_action=best_effort_queue_workflow_action,
            stderr=sys.stderr,
        )
        processed += result.processed_rows
        if result.failure_message:
            failures.append(result.failure_message)

    print(f"[build-queue] Summary: processed={processed} failed={len(failures)}")
    for failure in failures:
        print(f"[build-queue] FAILURE {failure}", file=sys.stderr)
    return 1 if failures else 0


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
        help="Deprecated compatibility filter for legacy Doc_phase rows; prefer --workflow-action",
    )
    ap.add_argument("--record-id", default=None, help="Only consume one Document_link record_id")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = ROOT / config_path
    cfg = load_config(config_path)
    resolved_data_root = str(
        resolve_phase2_export_root(
            cfg,
            repo_root=ROOT,
            data_root=args.data_root,
        )
    )
    try:
        return process_build_queue(
            cfg=cfg,
            config_path=config_path,
            data_root=resolved_data_root,
            dry_run=bool(args.dry_run),
            workflow_action=args.workflow_action,
            doc_phase=args.doc_phase,
            record_id=(args.record_id or "").strip() or None,
        )
    except RuntimeError as exc:
        print(f"[build-queue] ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
