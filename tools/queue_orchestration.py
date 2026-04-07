from __future__ import annotations

from typing import Any, Callable


def process_build_queue(
    *,
    cfg: dict[str, Any],
    config_path: Any,
    data_root: str | None,
    dry_run: bool,
    immediate_only: bool,
    workflow_action: str | None,
    doc_phase: str | None,
    record_id: str | None,
    bootstrap_queue_session: Callable[..., Any],
    load_pending_queue_state: Callable[..., Any],
    print_no_pending_message: Callable[..., None],
    print_dry_run_groups: Callable[..., None],
    sync_phase2_snapshot_before_queue: Callable[..., None],
    resolve_and_report_wiki_destination: Callable[..., Any],
    process_queue_record_group: Callable[..., Any],
    build_started_at_field: str,
    available_field_names: Callable[..., Any],
    select_pending_queue_records: Callable[..., Any],
    group_pending_queue_records: Callable[..., Any],
    warn_legacy_record_doc_phase: Callable[..., None],
    resolve_target_for_record: Callable[..., Any],
    queue_group_lang: Callable[..., Any],
    queue_group_build_family: Callable[..., Any],
    validate_queue_record_group: Callable[..., None],
    resolve_config_path_for_task: Callable[..., Any],
    queue_record_key: Callable[..., Any],
    workflow_action_label: Callable[..., Any],
    queue_record_action_source: Callable[..., Any],
    queue_record_legacy_doc_phase: Callable[..., Any],
    resolve_wiki_destination: Callable[..., Any],
    build_started_fields: Callable[..., Any],
    build_document_for_task: Callable[..., Any],
    upload_word_to_drive: Callable[..., Any],
    move_drive_file_to_wiki: Callable[..., Any],
    build_success_fields: Callable[..., Any],
    publish_release_latest_dir_for_target: Callable[..., Any],
    write_publish_release_metadata: Callable[..., Any],
    build_failure_writeback_fields: Callable[..., Any],
    best_effort_queue_workflow_action: Callable[..., Any],
    resolve_queue_workflow_action: Callable[..., Any],
    stderr: Any,
) -> int:
    session = bootstrap_queue_session(
        cfg=cfg,
        workflow_action=workflow_action,
        doc_phase=doc_phase,
    )
    pending_state = load_pending_queue_state(
        source=session.source,
        binding=session.binding,
        immediate_only=immediate_only,
        workflow_action=session.normalized_cli_action,
        record_id=record_id,
        select_pending_queue_records=select_pending_queue_records,
        group_pending_queue_records=group_pending_queue_records,
        available_field_names=available_field_names,
        build_started_at_field=build_started_at_field,
    )
    if pending_state is None:
        print_no_pending_message(immediate_only=immediate_only)
        return 0

    if dry_run:
        print_dry_run_groups(
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
            resolve_queue_workflow_action=resolve_queue_workflow_action,
        )
        return 0

    print("[build-queue] Syncing latest phase2 snapshot before building queued documents.")
    sync_phase2_snapshot_before_queue(
        config_path=config_path,
        data_root=data_root,
    )
    pending_state = load_pending_queue_state(
        source=session.source,
        binding=session.binding,
        immediate_only=immediate_only,
        workflow_action=session.normalized_cli_action,
        record_id=record_id,
        select_pending_queue_records=select_pending_queue_records,
        group_pending_queue_records=group_pending_queue_records,
        available_field_names=available_field_names,
        build_started_at_field=build_started_at_field,
    )
    if pending_state is None:
        print("[build-queue] Queue changed during sync; no pending build tasks remain.")
        return 0

    wiki_destination = resolve_and_report_wiki_destination(
        cli_bin=session.cli_bin,
        identity=session.identity,
        binding=session.binding,
        resolve_wiki_destination=resolve_wiki_destination,
    )

    failures: list[str] = []
    processed = 0
    for group in pending_state.pending_groups:
        result = process_queue_record_group(
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
            publish_release_latest_dir_for_target=publish_release_latest_dir_for_target,
            write_publish_release_metadata=write_publish_release_metadata,
            workflow_action_label=workflow_action_label,
            queue_record_key=queue_record_key,
            build_failure_writeback_fields=build_failure_writeback_fields,
            best_effort_queue_workflow_action=best_effort_queue_workflow_action,
            stderr=stderr,
        )
        processed += result.processed_rows
        if result.failure_message:
            failures.append(result.failure_message)

    print(f"[build-queue] Summary: processed={processed} failed={len(failures)}")
    for failure in failures:
        print(f"[build-queue] FAILURE {failure}", file=stderr)
    return 1 if failures else 0
