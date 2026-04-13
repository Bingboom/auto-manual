from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Any

from tools.queue_build_execution import (
    build_document_for_task as _build_document_for_task_impl,
    sync_phase2_snapshot_before_queue as _sync_phase2_snapshot_before_queue_impl,
)
from tools.queue_dry_run import print_dry_run_groups as _print_dry_run_groups_impl
from tools.queue_group_processing import process_queue_record_group as _process_queue_record_group_impl
from tools.queue_lark_ops import (
    host_root_from_url as _host_root_from_url_impl,
    move_drive_file_to_wiki as _move_drive_file_to_wiki_impl,
    move_result_entry_from_task_payload as _move_result_entry_from_task_payload_impl,
    resolve_wiki_destination as _resolve_wiki_destination_impl,
    upload_word_to_drive as _upload_word_to_drive_impl,
    wait_for_wiki_move_task as _wait_for_wiki_move_task_impl,
    wiki_url_from_host_root as _wiki_url_from_host_root_impl,
)
from tools.queue_orchestration import process_build_queue as _process_build_queue_impl
from tools.queue_session import (
    bootstrap_queue_session as _bootstrap_queue_session_impl,
    load_pending_queue_state as _load_pending_queue_state_impl,
    print_no_pending_message as _print_no_pending_message_impl,
    resolve_and_report_wiki_destination as _resolve_and_report_wiki_destination_impl,
)
from tools.queue_writeback import (
    build_failure_fields as _build_failure_fields_impl,
    build_failure_writeback_fields as _build_failure_writeback_fields_impl,
    build_started_fields as _build_started_fields_impl,
    build_success_fields as _build_success_fields_impl,
)


def upload_word_to_drive(module: Any, *, cli_bin: str, word_output_path: Path, identity: str) -> tuple[str, str]:
    return _upload_word_to_drive_impl(
        cli_bin=cli_bin,
        word_output_path=word_output_path,
        identity=identity,
        repo_root=module.ROOT,
        run_lark_cli_json=module._run_lark_cli_json,
        cli_relative_file_arg=lambda *, repo_root, path: module._cli_relative_file_arg(path),
    )


def resolve_wiki_destination(
    module: Any,
    *,
    cli_bin: str,
    identity: str,
    binding: Any,
) -> Any:
    return _resolve_wiki_destination_impl(
        cli_bin=cli_bin,
        identity=identity,
        binding=binding,
        get_wiki_node=module.get_wiki_node,
        wiki_destination_factory=module.WikiDestination,
    )


def wait_for_wiki_move_task(
    module: Any,
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
        run_lark_cli_json=module._run_lark_cli_json,
        move_result_entry_from_task_payload=_move_result_entry_from_task_payload_impl,
        wiki_url_from_host_root=_wiki_url_from_host_root_impl,
        sleep=time.sleep,
    )


def move_drive_file_to_wiki(
    module: Any,
    *,
    cli_bin: str,
    identity: str,
    file_token: str,
    drive_url: str,
    destination: Any,
) -> str:
    return _move_drive_file_to_wiki_impl(
        cli_bin=cli_bin,
        identity=identity,
        file_token=file_token,
        drive_url=drive_url,
        destination=destination,
        run_lark_cli_json=module._run_lark_cli_json,
        host_root_from_url=_host_root_from_url_impl,
        wiki_url_from_host_root=_wiki_url_from_host_root_impl,
        wait_for_wiki_move_task=module.wait_for_wiki_move_task,
    )
def build_py_target_command(
    module: Any,
    *,
    repo_root: Path,
    action: str,
    config_path: Path,
    model: str,
    region: str,
    data_root: str | None,
    source: str | None = None,
    no_clean: bool = False,
) -> list[str]:
    return module._bound_build_py_target_command(
        repo_root=repo_root,
        action=action,
        config_path=config_path,
        model=model,
        region=region,
        data_root=data_root,
        source=source,
        no_clean=no_clean,
    )


def build_py_sync_data_command(
    module: Any,
    *,
    repo_root: Path,
    config_path: Path,
    data_root: str | None,
) -> list[str]:
    return module._bound_build_py_sync_data_command(repo_root=repo_root, config_path=config_path, data_root=data_root)


def sync_phase2_snapshot_before_queue(module: Any, *, config_path: Path, data_root: str | None) -> None:
    _sync_phase2_snapshot_before_queue_impl(
        repo_root=module.ROOT,
        config_path=config_path,
        data_root=data_root,
        run_command=module._run_command,
        build_py_sync_data_command=module._build_py_sync_data_command,
    )


def build_document_for_task(
    module: Any,
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
        repo_root=module.ROOT,
        config_path=config_path,
        model=model,
        region=region,
        data_root=data_root,
        doc_phase=doc_phase,
        version=version,
        git_ref=git_ref,
        normalize_workflow_action=module.normalize_workflow_action,
        prepare_git_ref_worktree=module._prepare_git_ref_worktree,
        remove_worktree=module._remove_worktree,
        config_path_in_repo_root=module._config_path_in_repo_root,
        run_command=module._run_command,
        build_py_target_command=module._build_py_target_command,
        resolve_word_output_path_for_target=module.resolve_word_output_path_for_target,
        versioned_word_output_path=module._versioned_word_output_path,
        resolve_html_output_dir_for_target=module.resolve_html_output_dir_for_target,
        stage_publish_assets_to_host_repo=module._stage_publish_assets_to_host_repo,
        stage_draft_word_output_to_host_repo=module._stage_draft_word_output_to_host_repo,
    )


def build_success_fields(
    module: Any,
    *,
    version: str,
    word_output_path: Path,
    document_link_url: str,
    built_at: datetime,
    document_link_dd_url: str = "",
    workflow_action: str | None = None,
    doc_phase: str | None = None,
    data_sync_status: str = "",
    status_notes: tuple[str, ...] = (),
    clear_force_phase2_refresh: bool = True,
    write_data_sync: bool = True,
    write_document_link_dd: bool = False,
) -> dict[str, Any]:
    return _build_success_fields_impl(
        version=version,
        word_output_path=word_output_path,
        document_link_url=document_link_url,
        document_link_dd_url=document_link_dd_url,
        built_at=built_at,
        workflow_action=workflow_action,
        doc_phase=doc_phase,
        data_sync_status=data_sync_status,
        status_notes=status_notes,
        normalize_workflow_action=module.normalize_workflow_action,
        normalize_doc_phase=module.normalize_doc_phase,
        workflow_action_label=module.workflow_action_label,
        result_field=module.RESULT_FIELD,
        document_directory_field=module.DOCUMENT_DIRECTORY_FIELD,
        document_link_field=module.DOCUMENT_LINK_FIELD,
        document_link_dd_field=module.DOCUMENT_LINK_DD_FIELD if write_document_link_dd else "",
        trigger_field=module.TRIGGER_FIELD,
        done_trigger_value=module.DONE_TRIGGER_VALUE,
        immediate_trigger_field=module.IMMEDIATE_TRIGGER_FIELD,
        force_phase2_refresh_field=module.FORCE_PHASE2_REFRESH_FIELD if clear_force_phase2_refresh else "",
        data_sync_field=module.DATA_SYNC_FIELD if write_data_sync else "",
        success_prefix=module.SUCCESS_PREFIX,
    )


def build_started_fields(module: Any, *, started_at: datetime) -> dict[str, Any]:
    return _build_started_fields_impl(started_at=started_at, build_started_at_field=module.BUILD_STARTED_AT_FIELD)


def build_failure_fields(
    module: Any,
    *,
    version: str,
    message: str,
    workflow_action: str | None = None,
    doc_phase: str | None = None,
    data_sync_status: str = "",
) -> dict[str, Any]:
    return _build_failure_fields_impl(
        version=version,
        message=message,
        workflow_action=workflow_action,
        doc_phase=doc_phase,
        data_sync_status=data_sync_status,
        normalize_workflow_action=module.normalize_workflow_action,
        normalize_doc_phase=module.normalize_doc_phase,
        workflow_action_label=module.workflow_action_label,
        result_field=module.RESULT_FIELD,
        failed_prefix=module.FAILED_PREFIX,
    )


def build_failure_writeback_fields(
    module: Any,
    *,
    version: str,
    message: str,
    workflow_action: str | None = None,
    doc_phase: str | None = None,
    data_sync_status: str = "",
    word_output_path: Path | None = None,
    document_link_url: str | None = None,
    document_link_dd_url: str | None = None,
    clear_force_phase2_refresh: bool = True,
    write_data_sync: bool = True,
    write_document_link_dd: bool = False,
) -> dict[str, Any]:
    return _build_failure_writeback_fields_impl(
        version=version,
        message=message,
        workflow_action=workflow_action,
        doc_phase=doc_phase,
        data_sync_status=data_sync_status,
        word_output_path=word_output_path,
        document_link_url=document_link_url,
        document_link_dd_url=document_link_dd_url,
        build_failure_fields=module.build_failure_fields,
        result_field=module.RESULT_FIELD,
        document_directory_field=module.DOCUMENT_DIRECTORY_FIELD,
        document_link_field=module.DOCUMENT_LINK_FIELD,
        document_link_dd_field=module.DOCUMENT_LINK_DD_FIELD if write_document_link_dd else "",
        immediate_trigger_field=module.IMMEDIATE_TRIGGER_FIELD,
        force_phase2_refresh_field=module.FORCE_PHASE2_REFRESH_FIELD if clear_force_phase2_refresh else "",
        data_sync_field=module.DATA_SYNC_FIELD if write_data_sync else "",
    )


def best_effort_queue_workflow_action(module: Any, record: Any) -> str | None:
    return module._best_effort_queue_workflow_action(
        workflow_action=record.workflow_action,
        doc_phase=record.doc_phase,
        record_id=record.record_id,
    )


def _bootstrap_queue_session(module: Any, **kwargs: Any) -> Any:
    return _bootstrap_queue_session_impl(
        **kwargs,
        collect_queue_preflight_errors=module.collect_queue_preflight_errors,
        resolve_document_link_binding=module.resolve_document_link_binding,
        cli_bin=module._cli_bin,
        phase2_identity=module._phase2_identity,
        source_factory=module.LarkCliSource,
        normalize_cli_queue_action=module.normalize_cli_queue_action,
        warn_legacy_cli_doc_phase=module.warn_legacy_cli_doc_phase,
    )


def process_build_queue(
    module: Any,
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
    return _process_build_queue_impl(
        cfg=cfg,
        config_path=config_path,
        data_root=data_root,
        dry_run=dry_run,
        immediate_only=immediate_only,
        workflow_action=workflow_action,
        doc_phase=doc_phase,
        record_id=record_id,
        bootstrap_queue_session=lambda **kwargs: _bootstrap_queue_session(module, **kwargs),
        load_pending_queue_state=_load_pending_queue_state_impl,
        print_no_pending_message=_print_no_pending_message_impl,
        print_dry_run_groups=_print_dry_run_groups_impl,
        sync_phase2_snapshot_before_queue=module.sync_phase2_snapshot_before_queue,
        resolve_and_report_wiki_destination=_resolve_and_report_wiki_destination_impl,
        process_queue_record_group=_process_queue_record_group_impl,
        build_started_at_field=module.BUILD_STARTED_AT_FIELD,
        force_phase2_refresh_field=module.FORCE_PHASE2_REFRESH_FIELD,
        data_sync_field=module.DATA_SYNC_FIELD,
        document_link_dd_field=module.DOCUMENT_LINK_DD_FIELD,
        upload_dingtalk_field=module.UPLOAD_DINGTALK_FIELD,
        available_field_names=module._available_field_names,
        select_pending_queue_records=module.select_pending_queue_records,
        group_pending_queue_records=module.group_pending_queue_records,
        warn_legacy_record_doc_phase=module.warn_legacy_record_doc_phase,
        resolve_target_for_record=module.resolve_target_for_record,
        queue_group_lang=module.queue_group_lang,
        queue_group_build_family=module.queue_group_build_family,
        queue_group_dingtalk_target_node_url=module.queue_group_dingtalk_target_node_url,
        queue_group_force_phase2_refresh=module.queue_group_force_phase2_refresh,
        queue_group_upload_dingtalk=module.queue_group_upload_dingtalk,
        validate_queue_record_group=module.validate_queue_record_group,
        resolve_config_path_for_task=module.resolve_config_path_for_task,
        queue_record_key=module.queue_record_key,
        workflow_action_label=module.workflow_action_label,
        queue_record_action_source=module.queue_record_action_source,
        queue_record_legacy_doc_phase=module.queue_record_legacy_doc_phase,
        resolve_wiki_destination=module.resolve_artifact_destination,
        resolve_lark_wiki_destination=module.resolve_wiki_destination,
        resolve_row_artifact_destination=module.resolve_artifact_destination,
        resolve_artifact_mirror_provider=module.resolve_artifact_mirror_provider,
        resolve_dingtalk_mirror_destination=module.resolve_dingtalk_mirror_destination,
        build_started_fields=module.build_started_fields,
        build_document_for_task=module.build_document_for_task,
        publish_word_artifact=module.publish_word_artifact,
        build_success_fields=module.build_success_fields,
        publish_release_latest_dir_for_target=module._publish_release_latest_dir_for_target,
        write_publish_release_metadata=module.write_publish_release_metadata,
        build_failure_writeback_fields=module.build_failure_writeback_fields,
        best_effort_queue_workflow_action=module.best_effort_queue_workflow_action,
        resolve_queue_workflow_action=module.resolve_queue_workflow_action,
        stderr=module.sys.stderr,
    )
