#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_docs import build_root_for_target, render_build_template, resolve_output_path  # noqa: E402
from tools.data_snapshot import resolve_phase2_export_root  # noqa: E402
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


@dataclass(frozen=True)
class DocumentLinkBinding:
    base_token_env: str
    table_id_env: str
    view_id_env: str | None
    wiki_parent_token_env: str | None
    base_token: str
    table_id: str
    view_id: str | None
    wiki_parent_token: str | None


@dataclass(frozen=True)
class QueueRecord:
    record_id: str
    document_id: str
    document_key: str
    version: str
    lang: str
    workflow_action: str = ""
    doc_phase: str = ""
    git_ref: str = ""
    trigger_value: str = ""
    immediate_trigger_value: Any = None
    build_family: str = ""

    @property
    def label(self) -> str:
        return self.document_id or f"{self.document_key}_{self.lang}"


@dataclass(frozen=True)
class WikiDestination:
    space_id: str
    parent_wiki_token: str


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


def _scalar_text(value: Any) -> str:
    return _scalar_text_impl(value)


def _field_value(fields: dict[str, Any], *field_names: str) -> Any:
    return _field_value_impl(fields, *field_names)


def _available_field_names(raw_records: list[dict[str, Any]]) -> set[str]:
    return _available_field_names_impl(raw_records)


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


def _is_immediate_trigger_enabled(value: Any) -> bool:
    return _is_immediate_trigger_enabled_impl(value)


def _is_trigger_requested(value: Any) -> bool:
    return _is_trigger_requested_impl(value, trigger_values=TRIGGER_VALUES)


def normalize_workflow_action(value: Any) -> str | None:
    return _normalize_workflow_action(value)


def normalize_doc_phase(value: Any) -> str | None:
    return _normalize_doc_phase(value)


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


def workflow_action_label(value: str | None) -> str | None:
    return _workflow_action_label(value)


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


def parse_document_key(document_key: str) -> tuple[str, str]:
    return _parse_document_key_impl(document_key)


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


def queue_record_key(record: QueueRecord) -> str:
    return _queue_record_key_impl(record)


def queue_group_lang(records: list[QueueRecord]) -> str:
    return _queue_group_lang_impl(records)


def queue_group_build_family(records: list[QueueRecord]) -> str:
    return _queue_group_build_family_impl(records)


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


def _normalize_version_for_filename(version: str) -> str:
    return normalize_release_token(version)


def _versioned_word_output_path(word_output_path: Path, *, version: str, doc_phase: str | None = None) -> Path:
    return _versioned_word_output_path_impl(
        word_output_path,
        version=version,
        doc_phase=doc_phase,
        normalize_release_token=_normalize_version_for_filename,
        normalize_workflow_action=normalize_workflow_action,
    )


def _config_path_in_repo_root(config_path: Path, *, repo_root: Path) -> Path:
    return _config_path_in_repo_root_impl(config_path, repo_root=repo_root)


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


def _slug_ref_token(value: str) -> str:
    return _slug_ref_token_impl(value)


def _format_command(cmd: list[str]) -> str:
    return _format_command_impl(cmd)


def _command_failure_message(cmd: list[str], stdout: str, stderr: str, returncode: int) -> str:
    return _command_failure_message_impl(cmd, stdout, stderr, returncode)


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


def _wiki_node_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return _wiki_node_from_payload_impl(payload)


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


def _host_root_from_url(url: str) -> str:
    return _host_root_from_url_impl(url)


def _wiki_url_from_host_root(host_root: str, wiki_token: str) -> str:
    return _wiki_url_from_host_root_impl(host_root, wiki_token)


def _move_result_entry_from_task_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return _move_result_entry_from_task_payload_impl(payload)


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
    cmd = [
        sys.executable,
        str(repo_root / "build.py"),
        action,
        "--config",
        str(config_path),
        "--model",
        model,
        "--region",
        region,
    ]
    if source:
        cmd += ["--source", source]
    if no_clean:
        cmd.append("--no-clean")
    if data_root:
        cmd += ["--data-root", data_root]
    return cmd


def _build_py_sync_data_command(*, repo_root: Path = ROOT, config_path: Path, data_root: str | None) -> list[str]:
    cmd = [
        sys.executable,
        str(repo_root / "build.py"),
        "sync-data",
        "--config",
        str(config_path),
    ]
    if data_root:
        cmd += ["--data-root", data_root]
    return cmd


def sync_phase2_snapshot_before_queue(*, config_path: Path, data_root: str | None) -> None:
    _run_command(
        _build_py_sync_data_command(
            repo_root=ROOT,
            config_path=config_path,
            data_root=data_root,
        )
    )


def _copy_tree(src: Path, dst: Path) -> None:
    _copy_tree_impl(src, dst)


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
    normalized_doc_phase = normalize_workflow_action(doc_phase)
    repo_root = ROOT
    effective_config_path = config_path
    worktree: Path | None = None
    if git_ref.strip():
        worktree = _prepare_git_ref_worktree(git_ref.strip())
        repo_root = worktree
        effective_config_path = _config_path_in_repo_root(config_path, repo_root=worktree)

    try:
        if normalized_doc_phase == "draft":
            _run_command(
                _build_py_target_command(
                    repo_root=repo_root,
                    action="check",
                    config_path=effective_config_path,
                    model=model,
                    region=region,
                    data_root=data_root,
                    source="review",
                ),
                cwd=repo_root,
            )
            _run_command(
                _build_py_target_command(
                    repo_root=repo_root,
                    action="word",
                    config_path=effective_config_path,
                    model=model,
                    region=region,
                    data_root=data_root,
                    source="review",
                    no_clean=True,
                ),
                cwd=repo_root,
            )
        elif normalized_doc_phase == "publish":
            _run_command(
                _build_py_target_command(
                    repo_root=repo_root,
                    action="publish",
                    config_path=effective_config_path,
                    model=model,
                    region=region,
                    data_root=data_root,
                ),
                cwd=repo_root,
            )
            _run_command(
                _build_py_target_command(
                    repo_root=repo_root,
                    action="html",
                    config_path=effective_config_path,
                    model=model,
                    region=region,
                    data_root=data_root,
                    source="review",
                    no_clean=True,
                ),
                cwd=repo_root,
            )
        else:
            _run_command(
                _build_py_target_command(
                    repo_root=repo_root,
                    action="check",
                    config_path=effective_config_path,
                    model=model,
                    region=region,
                    data_root=data_root,
                ),
                cwd=repo_root,
            )
            _run_command(
                _build_py_target_command(
                    repo_root=repo_root,
                    action="word",
                    config_path=effective_config_path,
                    model=model,
                    region=region,
                    data_root=data_root,
                    no_clean=True,
                ),
                cwd=repo_root,
            )

        word_output_path = resolve_word_output_path_for_target(
            config_path=effective_config_path,
            model=model,
            region=region,
        )
        if not word_output_path.exists():
            raise RuntimeError(f"Word output was not created: {word_output_path}")
        versioned_path = _versioned_word_output_path(
            word_output_path,
            version=version,
            doc_phase=normalized_doc_phase,
        )
        if versioned_path != word_output_path:
            versioned_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(word_output_path, versioned_path)
            word_output_path = versioned_path
        if normalized_doc_phase == "publish":
            html_output_dir = resolve_html_output_dir_for_target(
                config_path=effective_config_path,
                model=model,
                region=region,
            )
            if not html_output_dir.exists():
                raise RuntimeError(f"HTML output was not created for publish: {html_output_dir}")
            host_config_path = _config_path_in_repo_root(config_path, repo_root=ROOT)
            staged_word_output_path, _latest_html_dir = _stage_publish_assets_to_host_repo(
                built_word_output_path=word_output_path,
                built_html_dir=html_output_dir,
                host_config_path=host_config_path,
                model=model,
                region=region,
                version=version,
            )
            return staged_word_output_path
        if repo_root != ROOT:
            return _stage_draft_word_output_to_host_repo(
                built_word_output_path=word_output_path,
                host_config_path=_config_path_in_repo_root(config_path, repo_root=ROOT),
                model=model,
                region=region,
                version=version,
                doc_phase=normalized_doc_phase,
            )
        return word_output_path
    finally:
        if worktree is not None:
            _remove_worktree(worktree)


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
    errors = collect_queue_preflight_errors(cfg)
    if errors:
        raise RuntimeError("process-build-queue preflight failed:\n- " + "\n- ".join(errors))

    binding = resolve_document_link_binding(cfg)
    cli_bin = _cli_bin(cfg)
    identity = _phase2_identity()
    source = LarkCliSource(cli_bin=cli_bin, identity=identity)
    raw_records = source.fetch_records_with_ids(
        base_token=binding.base_token,
        table_id=binding.table_id,
        view_id=binding.view_id,
    )
    normalized_cli_action = normalize_cli_queue_action(workflow_action=workflow_action, doc_phase=doc_phase)
    warn_legacy_cli_doc_phase(doc_phase, workflow_action)
    pending = select_pending_queue_records(
        raw_records,
        immediate_only=immediate_only,
        workflow_action=normalized_cli_action,
        record_id=record_id,
    )
    if not pending:
        if immediate_only:
            print("[build-queue] No pending immediate build tasks found.")
        else:
            print("[build-queue] No pending build tasks found.")
        return 0
    pending_groups = group_pending_queue_records(pending)
    available_fields = _available_field_names(raw_records)
    can_write_started_at = BUILD_STARTED_AT_FIELD in available_fields

    if dry_run:
        for group in pending_groups:
            record = group[0]
            warn_legacy_record_doc_phase(record)
            model, region = resolve_target_for_record(record)
            group_lang = queue_group_lang(group)
            group_build_family = queue_group_build_family(group)
            validate_queue_record_group(group)
            resolved_config_path = resolve_config_path_for_task(
                region=region,
                lang=group_lang,
                build_family=group_build_family,
            )
            print(
                "[build-queue] DRY-RUN "
                + json.dumps(
                    {
                        "record_ids": [item.record_id for item in group],
                        "record_id": record.record_id,
                        "label": record.label,
                        "document_key": queue_record_key(record),
                        "model": model,
                        "region": region,
                        "lang": group_lang,
                        "build_family": group_build_family,
                        "langs": [item.lang for item in group if item.lang.strip()],
                        "version": record.version,
                        "workflow_action": workflow_action_label(record.workflow_action or record.doc_phase) or "Legacy/Unspecified",
                        "workflow_action_source": queue_record_action_source(record),
                        "legacy_doc_phase": queue_record_legacy_doc_phase(record),
                        "git_ref": record.git_ref,
                        "config": str(resolved_config_path),
                        "data_root": data_root,
                    },
                    ensure_ascii=False,
                )
            )
        return 0

    print("[build-queue] Syncing latest phase2 snapshot before building queued documents.")
    sync_phase2_snapshot_before_queue(
        config_path=config_path,
        data_root=data_root,
    )
    raw_records = source.fetch_records_with_ids(
        base_token=binding.base_token,
        table_id=binding.table_id,
        view_id=binding.view_id,
    )
    pending = select_pending_queue_records(
        raw_records,
        immediate_only=immediate_only,
        workflow_action=normalized_cli_action,
        record_id=record_id,
    )
    if not pending:
        print("[build-queue] Queue changed during sync; no pending build tasks remain.")
        return 0
    pending_groups = group_pending_queue_records(pending)
    available_fields = _available_field_names(raw_records)
    can_write_started_at = BUILD_STARTED_AT_FIELD in available_fields

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

    failures: list[str] = []
    processed = 0
    for group in pending_groups:
        record = group[0]
        word_output_path: Path | None = None
        drive_url: str | None = None
        try:
            warn_legacy_record_doc_phase(record)
            validate_queue_record_group(group)
            model, region = resolve_target_for_record(record)
            group_lang = queue_group_lang(group)
            group_build_family = queue_group_build_family(group)
            resolved_config_path = resolve_config_path_for_task(
                region=region,
                lang=group_lang,
                build_family=group_build_family,
            )
            effective_doc_phase = resolve_queue_workflow_action(record)
            started_at = datetime.now().astimezone()
            if can_write_started_at:
                start_fields = build_started_fields(started_at=started_at)
                for group_record in group:
                    try:
                        source.upsert_record(
                            base_token=binding.base_token,
                            table_id=binding.table_id,
                            record_id=group_record.record_id,
                            record=start_fields,
                        )
                    except Exception as exc:
                        print(
                            f"[build-queue] WARNING start-time writeback failed for {group_record.label}: {exc}",
                            file=sys.stderr,
                        )
                print(
                    "[build-queue] Marked start time for "
                    f"{queue_record_key(record)} ({len(group)} row(s)): {started_at.isoformat(timespec='seconds')}"
                )
            word_output_path = build_document_for_task(
                config_path=resolved_config_path,
                model=model,
                region=region,
                data_root=data_root,
                doc_phase=effective_doc_phase,
                version=record.version,
                git_ref=record.git_ref,
            )
            file_token, drive_url = upload_word_to_drive(
                cli_bin=cli_bin,
                word_output_path=word_output_path,
                identity=identity,
            )
            document_link_url = move_drive_file_to_wiki(
                cli_bin=cli_bin,
                identity=identity,
                file_token=file_token,
                drive_url=drive_url,
                destination=wiki_destination,
            )
            built_at = datetime.now().astimezone()
            success_fields = build_success_fields(
                version=record.version,
                word_output_path=word_output_path,
                document_link_url=document_link_url,
                built_at=built_at,
                workflow_action=effective_doc_phase,
                doc_phase=queue_record_legacy_doc_phase(record),
            )
            for group_record in group:
                source.upsert_record(
                    base_token=binding.base_token,
                    table_id=binding.table_id,
                    record_id=group_record.record_id,
                    record=success_fields,
                )
            if effective_doc_phase == "publish":
                latest_html_dir = _publish_release_latest_dir_for_target(
                    config_path=resolved_config_path,
                    model=model,
                    region=region,
                ) / "html"
                write_publish_release_metadata(
                    config_path=resolved_config_path,
                    model=model,
                    region=region,
                    version=record.version,
                    git_ref=record.git_ref,
                    built_at=built_at,
                    word_output_path=word_output_path,
                    html_dir=latest_html_dir,
                    document_link_url=document_link_url,
                )
            processed += len(group)
            print(
                f"[build-queue] {workflow_action_label(effective_doc_phase) or 'Updated'} "
                f"{queue_record_key(record)} ({len(group)} row(s)): {word_output_path} -> {document_link_url}"
            )
        except Exception as exc:
            message = str(exc).strip()
            failures.append(
                f"{workflow_action_label(record.workflow_action or record.doc_phase) or 'Queue task'} "
                f"{queue_record_key(record)} ({len(group)} row(s)): {message}"
            )
            try:
                if drive_url:
                    print(
                        f"[build-queue] WARNING wiki attach failed for {queue_record_key(record)}; preserving latest Drive link {drive_url}",
                        file=sys.stderr,
                    )
                failure_fields = build_failure_writeback_fields(
                    version=record.version,
                    message=message,
                    workflow_action=best_effort_queue_workflow_action(record),
                    doc_phase=queue_record_legacy_doc_phase(record),
                    word_output_path=word_output_path,
                    document_link_url=drive_url,
                )
                for group_record in group:
                    source.upsert_record(
                        base_token=binding.base_token,
                        table_id=binding.table_id,
                        record_id=group_record.record_id,
                        record=failure_fields,
                    )
            except Exception as writeback_exc:
                failures[-1] += f" | writeback_failed={writeback_exc}"
                print(
                    f"[build-queue] ERROR writeback failed for {queue_record_key(record)}: {writeback_exc}",
                    file=sys.stderr,
                )

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
