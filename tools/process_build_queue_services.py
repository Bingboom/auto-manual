from __future__ import annotations

import os
import sys
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
from tools.queue_cloud_doc_finalize import (
    finalize_cloud_doc as _finalize_cloud_doc_impl,
    grant_doc_full_access as _grant_doc_full_access_impl,
    resolve_cloud_doc_grantee as _resolve_cloud_doc_grantee_impl,
)
from tools.queue_lark_ops import (
    host_root_from_url as _host_root_from_url_impl,
    import_markdown_to_cloud_doc as _import_markdown_to_cloud_doc_impl,
    move_drive_file_to_wiki as _move_drive_file_to_wiki_impl,
    move_result_entry_from_task_payload as _move_result_entry_from_task_payload_impl,
    resolve_wiki_destination as _resolve_wiki_destination_impl,
    upload_word_to_drive as _upload_word_to_drive_impl,
    wait_for_wiki_move_task as _wait_for_wiki_move_task_impl,
    wiki_url_from_host_root as _wiki_url_from_host_root_impl,
)
from tools.queue_orchestration import process_build_queue as _process_build_queue_impl
from tools.queue_artifact_sink import (
    ArtifactDestination,
    ArtifactPublishError,
    ArtifactPublishResult,
    artifact_sink_provider,
    dingtalk_alidocs_env_names,
    resolve_dingtalk_artifact_destination,
)
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


def import_markdown_to_cloud_doc(
    module: Any,
    *,
    cli_bin: str,
    source_path: Path,
    identity: str,
    doc_name: str | None = None,
) -> tuple[str, str]:
    return _import_markdown_to_cloud_doc_impl(
        cli_bin=cli_bin,
        source_path=source_path,
        identity=identity,
        repo_root=module.ROOT,
        run_lark_cli_json=module._run_lark_cli_json,
        cli_relative_file_arg=lambda *, repo_root, path: module._cli_relative_file_arg(path),
        doc_name=doc_name,
    )


def _wiki_node_token_from_ref(raw: str) -> str:
    """Extract a wiki node token from a `.../wiki/<token>?...` URL, or pass a bare token through."""
    raw = (raw or "").strip()
    if not raw:
        return ""
    if "/" in raw:
        return raw.split("?", 1)[0].rstrip("/").split("/")[-1]
    return raw


def review_doc_wiki_destination(module: Any, *, cli_bin: str, identity: str) -> Any:
    """The dedicated wiki node for review cloud docs (`FEISHU_REVIEW_DOC_WIKI_NODE`).

    Review docs live in their own knowledge-base node — NOT co-located with the Word
    artifact (which sits under the build table's node). Returns a ``WikiDestination``,
    or ``None`` when the env is unset (then the doc is left in the bot's drive)."""
    token = _wiki_node_token_from_ref(os.environ.get("FEISHU_REVIEW_DOC_WIKI_NODE", ""))
    if not token:
        return None
    node = module.get_wiki_node(cli_bin=cli_bin, identity=identity, token=token)
    space_id = str(node.get("space_id") or "").strip()
    if not space_id:
        return None
    return module.WikiDestination(space_id=space_id, parent_wiki_token=token)


def finalize_cloud_doc(
    module: Any,
    *,
    cli_bin: str,
    identity: str,
    cloud_doc_token: str,
    cloud_doc_url: str,
    member_union_id: str,
    destination: Any,  # the Word's destination — NOT used for the review doc (see below)
    grant: bool = True,
) -> str:
    """Grant the operator edit access on the bot-owned cloud doc + place it in the
    dedicated review-doc wiki node (``FEISHU_REVIEW_DOC_WIKI_NODE``), not the Word's
    node. Best-effort; returns the doc URL (wiki URL after the move).

    ``grant=False`` places the doc without granting edit access — used for the
    frozen baseline (R0) doc, which must stay un-edited."""
    grantee_member_id, grantee_member_type = (
        _resolve_cloud_doc_grantee_impl(
            operator_union_id=member_union_id,
            default_editor=os.environ.get("FEISHU_CLOUD_DOC_DEFAULT_EDITOR", ""),
        )
        if grant
        else ("", "")
    )
    review_dest = review_doc_wiki_destination(module, cli_bin=cli_bin, identity=identity)
    return _finalize_cloud_doc_impl(
        cloud_doc_token=cloud_doc_token,
        cloud_doc_url=cloud_doc_url,
        grantee_member_id=grantee_member_id,
        grantee_member_type=grantee_member_type,
        destination=review_dest,
        grant_full_access=lambda *, doc_token, member_id, member_type: _grant_doc_full_access_impl(
            cli_bin=cli_bin,
            identity=identity,
            doc_token=doc_token,
            member_id=member_id,
            member_type=member_type,
            run_lark_cli_json=module._run_lark_cli_json,
        ),
        move_to_wiki=lambda *, obj_token, doc_url: _move_drive_file_to_wiki_impl(
            cli_bin=cli_bin,
            identity=identity,
            file_token=obj_token,
            drive_url=doc_url,
            destination=review_dest,
            obj_type="docx",
            run_lark_cli_json=module._run_lark_cli_json,
            host_root_from_url=_host_root_from_url_impl,
            wiki_url_from_host_root=_wiki_url_from_host_root_impl,
            wait_for_wiki_move_task=module.wait_for_wiki_move_task,
        ),
        on_warning=lambda message: print(f"[build-queue] WARNING {message}", file=module.sys.stderr),
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


def resolve_artifact_destination(
    module: Any,
    *,
    cfg: dict[str, Any],
    cli_bin: str,
    identity: str,
    binding: Any,
    target_node_url: str | None = None,
) -> Any:
    provider = artifact_sink_provider(cfg, environ=os.environ)
    if provider == "dingtalk_alidocs_session":
        return resolve_dingtalk_artifact_destination(
            cfg,
            environ=os.environ,
            target_node_url=target_node_url,
            allow_missing_target_node_url=target_node_url is None,
        )
    return module.resolve_wiki_destination(
        cli_bin=cli_bin,
        identity=identity,
        binding=binding,
    )


def resolve_dingtalk_mirror_destination(
    module: Any,
    *,
    cfg: dict[str, Any],
    target_node_url: str | None = None,
    allow_missing_target_node_url: bool = False,
) -> ArtifactDestination:
    return resolve_dingtalk_artifact_destination(
        cfg,
        environ=os.environ,
        target_node_url=target_node_url,
        allow_missing_target_node_url=allow_missing_target_node_url,
    )


def ensure_dingtalk_session_ready(
    module: Any,
    *,
    cfg: dict[str, Any],
    operator_union_id: str = "",
) -> None:
    env_names = dingtalk_alidocs_env_names(cfg)
    module.load_session_config_for_operator_union_id(
        operator_union_id=operator_union_id,
        environ=os.environ,
        a_token_env=env_names["a_token_env"],
        xsrf_token_env=env_names["xsrf_token_env"],
        cookie_env=env_names["cookie_env"],
        bx_version_env=env_names["bx_version_env"],
    )


def publish_word_artifact(
    module: Any,
    *,
    cfg: dict[str, Any],
    cli_bin: str,
    artifact_output_path: Path | None = None,
    word_output_path: Path | None = None,
    identity: str,
    artifact_destination: Any,
    dingtalk_mirror_destination: ArtifactDestination | None = None,
    dingtalk_operator_union_id: str = "",
    artifact_label: str = "artifact",
) -> ArtifactPublishResult:
    resolved_artifact_output_path = artifact_output_path or word_output_path
    if resolved_artifact_output_path is None:
        raise RuntimeError("publish_word_artifact requires artifact_output_path")
    provider = artifact_sink_provider(cfg, environ=os.environ)
    if provider == "dingtalk_alidocs_session":
        env_names = dingtalk_alidocs_env_names(cfg)
        session = module.load_session_config_for_operator_union_id(
            operator_union_id=dingtalk_operator_union_id,
            environ=os.environ,
            a_token_env=env_names["a_token_env"],
            xsrf_token_env=env_names["xsrf_token_env"],
            cookie_env=env_names["cookie_env"],
            bx_version_env=env_names["bx_version_env"],
        )
        target_node_url = (
            artifact_destination.runtime_target
            if isinstance(artifact_destination, ArtifactDestination)
            else None
        )
        if not target_node_url:
            raise RuntimeError("DingTalk artifact destination is missing target_node_url")
        committed = module.upload_file_to_node(
            session=session,
            file_path=resolved_artifact_output_path,
            parent_node_url=str(target_node_url),
        )
        return ArtifactPublishResult(
            provider="dingtalk_alidocs_session",
            reference_id=committed.dentry_uuid,
            latest_link_url=committed.node_url,
            document_link_url=committed.node_url,
            document_link_dd_url=committed.node_url,
            status_notes=(f"published_artifact={artifact_label}", "dingtalk_sync=ok"),
        )

    file_token, drive_url = module.upload_word_to_drive(
        cli_bin=cli_bin,
        word_output_path=resolved_artifact_output_path,
        identity=identity,
    )
    try:
        document_link_url = module.move_drive_file_to_wiki(
            cli_bin=cli_bin,
            identity=identity,
            file_token=file_token,
            drive_url=drive_url,
            destination=artifact_destination,
        )
    except Exception as exc:
        recovered_message = str(exc).strip()
        if "permission denied" not in recovered_message.lower():
            raise ArtifactPublishError(recovered_message, latest_link_url=drive_url) from exc
        print(
            f"[build-queue] WARNING wiki attach failed; using Drive link {drive_url}",
            file=sys.stderr,
        )
        result = ArtifactPublishResult(
            provider="lark_drive",
            reference_id=file_token,
            latest_link_url=drive_url,
            document_link_url=drive_url,
            status_notes=(f"published_artifact={artifact_label}", "drive_only", f"wiki_attach_failed={recovered_message}"),
        )
    else:
        result = ArtifactPublishResult(
            provider="lark_drive",
            reference_id=file_token,
            latest_link_url=drive_url,
            document_link_url=document_link_url,
            status_notes=(f"published_artifact={artifact_label}",),
        )

    if dingtalk_mirror_destination is None:
        return result

    env_names = dingtalk_alidocs_env_names(cfg)
    session = module.load_session_config_for_operator_union_id(
        operator_union_id=dingtalk_operator_union_id,
        environ=os.environ,
        a_token_env=env_names["a_token_env"],
        xsrf_token_env=env_names["xsrf_token_env"],
        cookie_env=env_names["cookie_env"],
        bx_version_env=env_names["bx_version_env"],
    )
    target_node_url = str(dingtalk_mirror_destination.runtime_target or "").strip()
    if not target_node_url:
        raise RuntimeError("DingTalk mirror destination is missing target_node_url")
    try:
        committed = module.upload_file_to_node(
            session=session,
            file_path=resolved_artifact_output_path,
            parent_node_url=target_node_url,
        )
    except Exception as exc:
        message = str(exc).strip()
        status_notes = (*result.status_notes, "dingtalk_sync=failed", f"dingtalk_sync_error={message}")
        return ArtifactPublishResult(
            provider=result.provider,
            reference_id=result.reference_id,
            latest_link_url=result.latest_link_url,
            document_link_url=result.document_link_url,
            document_link_dd_url="",
            status_notes=status_notes,
        )
    status_notes = (*result.status_notes, "dingtalk_sync=ok")
    return ArtifactPublishResult(
        provider=result.provider,
        reference_id=result.reference_id,
        latest_link_url=result.latest_link_url,
        document_link_url=result.document_link_url,
        document_link_dd_url=committed.node_url,
        status_notes=status_notes,
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
    lang: str | None = None,
    source: str | None = None,
    no_clean: bool = False,
    idml_mode: str | None = None,
) -> list[str]:
    return module._bound_build_py_target_command(
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
    lang: str | None = None,
    version: str = "",
    git_ref: str = "",
) -> Any:
    return _build_document_for_task_impl(
        repo_root=module.ROOT,
        config_path=config_path,
        model=model,
        region=region,
        data_root=data_root,
        doc_phase=doc_phase,
        lang=lang,
        version=version,
        git_ref=git_ref,
        normalize_workflow_action=module.normalize_workflow_action,
        prepare_git_ref_worktree=module._prepare_git_ref_worktree,
        remove_worktree=module._remove_worktree,
        config_path_in_repo_root=module._config_path_in_repo_root,
        run_command=module._run_command,
        build_py_target_command=module._build_py_target_command,
        resolve_word_output_path_for_target=module.resolve_word_output_path_for_target,
        resolve_pdf_output_path_for_target=module.resolve_pdf_output_path_for_target,
        resolve_md_output_path_for_target=module.resolve_md_output_path_for_target,
        versioned_pdf_output_path=module._versioned_pdf_output_path,
        versioned_word_output_path=module._versioned_word_output_path,
        versioned_md_output_path=module._versioned_md_output_path,
        resolve_html_output_dir_for_target=module.resolve_html_output_dir_for_target,
        stage_publish_assets_to_host_repo=module._stage_publish_assets_to_host_repo,
        stage_draft_word_output_to_host_repo=module._stage_draft_word_output_to_host_repo,
        stage_draft_md_output_to_host_repo=module._stage_draft_md_output_to_host_repo,
    )


def build_success_fields(
    module: Any,
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
    return _build_success_fields_impl(
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
        normalize_workflow_action=module.normalize_workflow_action,
        normalize_doc_phase=module.normalize_doc_phase,
        workflow_action_label=module.workflow_action_label,
        result_field=module.RESULT_FIELD,
        document_directory_field=module.DOCUMENT_DIRECTORY_FIELD,
        document_link_field=module.DOCUMENT_LINK_FIELD,
        document_link_dd_field=module.DOCUMENT_LINK_DD_FIELD if write_document_link_dd else "",
        feishu_cloud_doc_field=module.FEISHU_CLOUD_DOC_FIELD if write_feishu_cloud_doc else "",
        trigger_field=module.TRIGGER_FIELD,
        done_trigger_value=module.DONE_TRIGGER_VALUE,
        immediate_trigger_field=module.IMMEDIATE_TRIGGER_FIELD,
        force_phase2_refresh_field=module.FORCE_PHASE2_REFRESH_FIELD if clear_force_phase2_refresh else "",
        data_sync_field=module.DATA_SYNC_FIELD if write_data_sync else "",
        success_prefix=module.SUCCESS_PREFIX,
    )


def build_started_fields(
    module: Any,
    *,
    started_at: datetime,
    version: str = "",
    workflow_action: str | None = None,
    doc_phase: str | None = None,
    data_sync_status: str = "",
) -> dict[str, Any]:
    return _build_started_fields_impl(
        started_at=started_at,
        version=version,
        workflow_action=workflow_action,
        doc_phase=doc_phase,
        data_sync_status=data_sync_status,
        normalize_workflow_action=module.normalize_workflow_action,
        normalize_doc_phase=module.normalize_doc_phase,
        workflow_action_label=module.workflow_action_label,
        build_started_at_field=module.BUILD_STARTED_AT_FIELD,
        result_field=module.RESULT_FIELD,
        running_prefix=module.RUNNING_PREFIX,
    )


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
    feishu_cloud_doc_url: str | None = None,
    clear_force_phase2_refresh: bool = True,
    write_data_sync: bool = True,
    write_document_link_dd: bool = False,
    write_feishu_cloud_doc: bool = False,
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
        feishu_cloud_doc_url=feishu_cloud_doc_url,
        build_failure_fields=module.build_failure_fields,
        result_field=module.RESULT_FIELD,
        document_directory_field=module.DOCUMENT_DIRECTORY_FIELD,
        document_link_field=module.DOCUMENT_LINK_FIELD,
        document_link_dd_field=module.DOCUMENT_LINK_DD_FIELD if write_document_link_dd else "",
        feishu_cloud_doc_field=module.FEISHU_CLOUD_DOC_FIELD if write_feishu_cloud_doc else "",
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
        feishu_cloud_doc_field=module.FEISHU_CLOUD_DOC_FIELD,
        upload_dingtalk_field=module.UPLOAD_DINGTALK_FIELD,
        available_field_names=module._available_field_names,
        select_pending_queue_records=module.select_pending_queue_records,
        group_pending_queue_records=module.group_pending_queue_records,
        warn_legacy_record_doc_phase=module.warn_legacy_record_doc_phase,
        resolve_target_for_record=module.resolve_target_for_record,
        queue_group_lang=module.queue_group_lang,
        queue_group_build_family=module.queue_group_build_family,
        queue_group_dingtalk_target_node_url=module.queue_group_dingtalk_target_node_url,
        queue_group_operator_union_id=module.queue_group_operator_union_id,
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
        ensure_dingtalk_session_ready=module.ensure_dingtalk_session_ready,
        build_started_fields=module.build_started_fields,
        build_document_for_task=module.build_document_for_task,
        publish_word_artifact=module.publish_word_artifact,
        import_markdown_to_cloud_doc=module.import_markdown_to_cloud_doc,
        finalize_cloud_doc=module.finalize_cloud_doc,
        build_success_fields=module.build_success_fields,
        publish_release_latest_dir_for_target=module._publish_release_latest_dir_for_target,
        write_publish_release_metadata=module.write_publish_release_metadata,
        build_failure_writeback_fields=module.build_failure_writeback_fields,
        best_effort_queue_workflow_action=module.best_effort_queue_workflow_action,
        resolve_queue_workflow_action=module.resolve_queue_workflow_action,
        stderr=module.sys.stderr,
    )
