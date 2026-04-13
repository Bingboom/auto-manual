from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class QueueGroupProcessingResult:
    processed_rows: int
    failure_message: str | None = None


def process_queue_record_group(
    *,
    group: list[Any],
    cfg: dict[str, Any],
    config_path: Path,
    source: Any,
    binding: Any,
    data_root: str | None,
    can_write_started_at: bool,
    can_write_force_phase2_refresh: bool,
    can_write_data_sync: bool,
    can_write_document_link_dd: bool,
    has_upload_dingtalk_field: bool,
    cli_bin: str,
    identity: str,
    artifact_destination: Any,
    warn_legacy_record_doc_phase: Callable[[Any], None],
    validate_queue_record_group: Callable[[list[Any]], None],
    resolve_target_for_record: Callable[[Any], tuple[str, str]],
    queue_group_lang: Callable[[list[Any]], str],
    queue_group_build_family: Callable[[list[Any]], str],
    queue_group_dingtalk_target_node_url: Callable[[list[Any]], str],
    queue_group_operator_union_id: Callable[[list[Any]], str],
    queue_group_force_phase2_refresh: Callable[[list[Any]], bool],
    queue_group_upload_dingtalk: Callable[[list[Any]], bool],
    resolve_config_path_for_task: Callable[..., Path],
    resolve_queue_workflow_action: Callable[[Any], str | None],
    sync_phase2_snapshot_before_queue: Callable[..., None],
    resolve_lark_wiki_destination: Callable[..., Any],
    resolve_row_artifact_destination: Callable[..., Any],
    resolve_artifact_mirror_provider: Callable[..., str | None],
    resolve_dingtalk_mirror_destination: Callable[..., Any],
    build_started_fields: Callable[..., dict[str, Any]],
    build_document_for_task: Callable[..., Path],
    publish_word_artifact: Callable[..., Any],
    build_success_fields: Callable[..., dict[str, Any]],
    queue_record_legacy_doc_phase: Callable[[Any], str | None],
    publish_release_latest_dir_for_target: Callable[..., Path],
    write_publish_release_metadata: Callable[..., Path],
    workflow_action_label: Callable[[str | None], str | None],
    queue_record_key: Callable[[Any], str],
    build_failure_writeback_fields: Callable[..., dict[str, Any]],
    best_effort_queue_workflow_action: Callable[[Any], str | None],
    stderr: Any,
) -> QueueGroupProcessingResult:
    record = group[0]
    word_output_path: Path | None = None
    latest_link_url: str | None = None
    latest_document_link_dd_url: str | None = None
    group_key = queue_record_key(record)
    row_count = len(group)
    try:
        warn_legacy_record_doc_phase(record)
        validate_queue_record_group(group)
        model, region = resolve_target_for_record(record)
        group_lang = queue_group_lang(group)
        group_build_family = queue_group_build_family(group)
        dingtalk_target_node_url = queue_group_dingtalk_target_node_url(group)
        dingtalk_operator_union_id = queue_group_operator_union_id(group)
        force_phase2_refresh = queue_group_force_phase2_refresh(group)
        upload_dingtalk = queue_group_upload_dingtalk(group)
        data_sync_status = "skipped"
        effective_doc_phase = resolve_queue_workflow_action(record)
        effective_artifact_destination = artifact_destination
        dingtalk_mirror_destination = None
        deferred_status_notes: tuple[str, ...] = ()
        primary_provider = str(getattr(artifact_destination, "provider", "") or "lark_drive")
        mirror_provider = resolve_artifact_mirror_provider(cfg=cfg)
        if primary_provider == "dingtalk_alidocs_session" and has_upload_dingtalk_field:
            if upload_dingtalk:
                if dingtalk_target_node_url:
                    effective_artifact_destination = resolve_row_artifact_destination(
                        cfg=cfg,
                        cli_bin=cli_bin,
                        identity=identity,
                        binding=binding,
                        target_node_url=dingtalk_target_node_url,
                    )
                    print(
                        f"[build-queue] Using DingTalk upload for {group_key} ({row_count} row(s)) "
                        f"with row target {dingtalk_target_node_url}."
                    )
                else:
                    if not getattr(effective_artifact_destination, "runtime_target", None):
                        raise RuntimeError(
                            "DingTalk target node URL is required: provide row DingTalk_target_node_url "
                            "or configure DINGTALK_DOCS_TARGET_NODE_URL for the remote worker"
                        )
                    print(f"[build-queue] Using DingTalk upload for {group_key} ({row_count} row(s)) with default target.")
            else:
                print(f"[build-queue] Skipping DingTalk upload for {group_key} ({row_count} row(s)); using Feishu/wiki upload.")
                effective_artifact_destination = resolve_lark_wiki_destination(
                    cli_bin=cli_bin,
                    identity=identity,
                    binding=binding,
                )
        elif primary_provider == "lark_drive" and mirror_provider == "dingtalk_alidocs_session":
            if has_upload_dingtalk_field and not upload_dingtalk:
                print(f"[build-queue] Skipping DingTalk sync for {group_key} ({row_count} row(s)); using Feishu/wiki only.")
                deferred_status_notes = ("dingtalk_sync=skipped",)
            else:
                if dingtalk_target_node_url:
                    dingtalk_mirror_destination = resolve_dingtalk_mirror_destination(
                        cfg=cfg,
                        target_node_url=dingtalk_target_node_url,
                    )
                    print(
                        f"[build-queue] Syncing DingTalk upload for {group_key} ({row_count} row(s)) "
                        f"with row target {dingtalk_target_node_url}."
                    )
                else:
                    dingtalk_mirror_destination = resolve_dingtalk_mirror_destination(cfg=cfg)
                    print(f"[build-queue] Syncing DingTalk upload for {group_key} ({row_count} row(s)) with default target.")
        resolved_config_path = resolve_config_path_for_task(
            region=region,
            lang=group_lang,
            build_family=group_build_family,
            workflow_action=effective_doc_phase,
        )
        if effective_doc_phase == "draft" and not record.git_ref.strip():
            raise RuntimeError(
                "Build Draft Package queue rows require Git_ref so the worker can fetch the review branch"
            )
        if force_phase2_refresh:
            print(
                f"[build-queue] Syncing latest phase2 snapshot before {group_key} ({row_count} row(s))."
            )
            try:
                sync_phase2_snapshot_before_queue(
                    config_path=config_path,
                    data_root=data_root,
                )
            except Exception:
                data_sync_status = "failed"
                raise
            data_sync_status = "refreshed"
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
                        file=stderr,
                    )
            print(
                "[build-queue] Marked start time for "
                f"{group_key} ({row_count} row(s)): {started_at.isoformat(timespec='seconds')}"
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
        artifact_result = publish_word_artifact(
            cfg=cfg,
            cli_bin=cli_bin,
            word_output_path=word_output_path,
            identity=identity,
            artifact_destination=effective_artifact_destination,
            dingtalk_mirror_destination=dingtalk_mirror_destination,
            dingtalk_operator_union_id=dingtalk_operator_union_id,
        )
        latest_link_url = artifact_result.latest_link_url
        document_link_url = artifact_result.document_link_url
        document_link_dd_url = artifact_result.document_link_dd_url
        latest_document_link_dd_url = document_link_dd_url or None
        built_at = datetime.now().astimezone()
        success_fields = build_success_fields(
            version=record.version,
            word_output_path=word_output_path,
            document_link_url=document_link_url,
            document_link_dd_url=document_link_dd_url,
            built_at=built_at,
            workflow_action=effective_doc_phase,
            doc_phase=queue_record_legacy_doc_phase(record),
            data_sync_status=data_sync_status,
            status_notes=(*artifact_result.status_notes, *deferred_status_notes),
            clear_force_phase2_refresh=can_write_force_phase2_refresh,
            write_data_sync=can_write_data_sync,
            write_document_link_dd=can_write_document_link_dd,
        )
        for group_record in group:
            source.upsert_record(
                base_token=binding.base_token,
                table_id=binding.table_id,
                record_id=group_record.record_id,
                record=success_fields,
            )
        if effective_doc_phase == "publish":
            latest_html_dir = publish_release_latest_dir_for_target(
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
        print(
            f"[build-queue] {workflow_action_label(effective_doc_phase) or 'Updated'} "
            f"{group_key} ({row_count} row(s)): {word_output_path} -> {document_link_url}"
        )
        return QueueGroupProcessingResult(processed_rows=row_count)
    except Exception as exc:
        latest_link_url = getattr(exc, "latest_link_url", None) or latest_link_url
        message = str(exc).strip()
        failure_message = (
            f"{workflow_action_label(record.workflow_action or record.doc_phase) or 'Queue task'} "
            f"{group_key} ({row_count} row(s)): {message}"
        )
        try:
            if latest_link_url:
                print(
                    f"[build-queue] WARNING artifact publish failed for {group_key}; preserving latest link {latest_link_url}",
                    file=stderr,
                )
            failure_fields = build_failure_writeback_fields(
                version=record.version,
                message=message,
                workflow_action=best_effort_queue_workflow_action(record),
                doc_phase=queue_record_legacy_doc_phase(record),
                data_sync_status=data_sync_status,
                word_output_path=word_output_path,
                document_link_url=latest_link_url,
                document_link_dd_url=latest_document_link_dd_url,
                clear_force_phase2_refresh=can_write_force_phase2_refresh,
                write_data_sync=can_write_data_sync,
                write_document_link_dd=can_write_document_link_dd,
            )
            for group_record in group:
                source.upsert_record(
                    base_token=binding.base_token,
                    table_id=binding.table_id,
                    record_id=group_record.record_id,
                    record=failure_fields,
                )
        except Exception as writeback_exc:
            failure_message += f" | writeback_failed={writeback_exc}"
            print(
                f"[build-queue] ERROR writeback failed for {group_key}: {writeback_exc}",
                file=stderr,
            )
        return QueueGroupProcessingResult(processed_rows=0, failure_message=failure_message)
