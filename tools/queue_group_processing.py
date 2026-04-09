from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class QueueGroupProcessingResult:
    processed_rows: int
    failure_message: str | None = None


def _is_recoverable_wiki_attach_failure(message: str) -> bool:
    text = str(message or "").strip().lower()
    return "permission denied" in text


def process_queue_record_group(
    *,
    group: list[Any],
    source: Any,
    binding: Any,
    data_root: str | None,
    can_write_started_at: bool,
    cli_bin: str,
    identity: str,
    wiki_destination: Any,
    warn_legacy_record_doc_phase: Callable[[Any], None],
    validate_queue_record_group: Callable[[list[Any]], None],
    resolve_target_for_record: Callable[[Any], tuple[str, str]],
    queue_group_lang: Callable[[list[Any]], str],
    queue_group_build_family: Callable[[list[Any]], str],
    resolve_config_path_for_task: Callable[..., Path],
    resolve_queue_workflow_action: Callable[[Any], str | None],
    build_started_fields: Callable[..., dict[str, Any]],
    build_document_for_task: Callable[..., Path],
    upload_word_to_drive: Callable[..., tuple[str, str]],
    move_drive_file_to_wiki: Callable[..., str],
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
    drive_url: str | None = None
    wiki_attach_warning: str | None = None
    group_key = queue_record_key(record)
    row_count = len(group)
    try:
        warn_legacy_record_doc_phase(record)
        validate_queue_record_group(group)
        model, region = resolve_target_for_record(record)
        group_lang = queue_group_lang(group)
        group_build_family = queue_group_build_family(group)
        effective_doc_phase = resolve_queue_workflow_action(record)
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
        file_token, drive_url = upload_word_to_drive(
            cli_bin=cli_bin,
            word_output_path=word_output_path,
            identity=identity,
        )
        try:
            document_link_url = move_drive_file_to_wiki(
                cli_bin=cli_bin,
                identity=identity,
                file_token=file_token,
                drive_url=drive_url,
                destination=wiki_destination,
            )
        except Exception as exc:
            recovered_message = str(exc).strip()
            if not drive_url or not _is_recoverable_wiki_attach_failure(recovered_message):
                raise
            wiki_attach_warning = recovered_message
            document_link_url = drive_url
            print(
                f"[build-queue] WARNING wiki attach failed for {group_key}; using Drive link {drive_url}",
                file=stderr,
            )
        built_at = datetime.now().astimezone()
        success_fields = build_success_fields(
            version=record.version,
            word_output_path=word_output_path,
            document_link_url=document_link_url,
            built_at=built_at,
            workflow_action=effective_doc_phase,
            doc_phase=queue_record_legacy_doc_phase(record),
            status_notes=(
                (
                    "drive_only",
                    f"wiki_attach_failed={wiki_attach_warning}",
                )
                if wiki_attach_warning
                else ()
            ),
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
        message = str(exc).strip()
        failure_message = (
            f"{workflow_action_label(record.workflow_action or record.doc_phase) or 'Queue task'} "
            f"{group_key} ({row_count} row(s)): {message}"
        )
        try:
            if drive_url:
                print(
                    f"[build-queue] WARNING wiki attach failed for {group_key}; preserving latest Drive link {drive_url}",
                    file=stderr,
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
            failure_message += f" | writeback_failed={writeback_exc}"
            print(
                f"[build-queue] ERROR writeback failed for {group_key}: {writeback_exc}",
                file=stderr,
            )
        return QueueGroupProcessingResult(processed_rows=0, failure_message=failure_message)
