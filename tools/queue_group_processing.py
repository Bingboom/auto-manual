from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from tools.delivery_outbox import drop_publish_delivery_outbox
from tools.document_link_queue import scalar_text
from tools.queue_contract import BASELINE_DOC_FIELD
from tools.queue_transitions import (
    append_writeback_failed,
    has_active_queue_claim,
    queue_claim_is_owned,
)


@dataclass(frozen=True)
class QueueGroupProcessingResult:
    processed_rows: int
    failure_message: str | None = None


def _write_terminal_queue_fields(
    *,
    source: Any,
    base_token: str,
    table_id: str,
    group: list[Any],
    fields: dict[str, Any],
    result_field: str,
    claim_token: str,
) -> None:
    """Write terminal fields only while no competing runner owns each row's claim.

    A runner that acquired a claim must still hold it. A failure raised before the
    claim was ever acquired (a malformed group rejected by group validation) carries
    no token; that row keeps its FAILED writeback so the failure stays visible on the
    row, but only while nobody else holds an active claim on it.
    """

    for group_record in group:
        raw_records = source.fetch_records_with_ids(
            base_token=base_token,
            table_id=table_id,
            view_id=None,
        )
        latest_record = next(
            (
                raw
                for raw in raw_records
                if isinstance(raw, dict) and str(raw.get("record_id") or "").strip() == group_record.record_id
            ),
            None,
        )
        latest_fields = latest_record.get("fields", {}) if isinstance(latest_record, dict) else {}
        latest_result = scalar_text(latest_fields.get(result_field)) if isinstance(latest_fields, dict) else ""
        if claim_token:
            if not queue_claim_is_owned(latest_result, claim_token=claim_token):
                raise RuntimeError(
                    "claim ownership lost before terminal writeback: "
                    f"record_id={group_record.record_id}"
                )
        elif has_active_queue_claim(latest_result):
            raise RuntimeError(
                "row is claimed by another runner; terminal writeback skipped: "
                f"record_id={group_record.record_id}"
            )
        source.upsert_record(
            base_token=base_token,
            table_id=table_id,
            record_id=group_record.record_id,
            record=fields,
        )


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
    can_write_feishu_cloud_doc: bool,
    has_upload_dingtalk_field: bool,
    cli_bin: str,
    identity: str,
    artifact_destination: Any,
    acquire_queue_claim: Callable[..., Any],
    result_field: str,
    queue_claim_ttl_seconds: int,
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
    ensure_dingtalk_session_ready: Callable[..., None],
    build_started_fields: Callable[..., dict[str, Any]],
    build_document_for_task: Callable[..., Any],
    publish_word_artifact: Callable[..., Any],
    import_markdown_to_cloud_doc: Callable[..., tuple[str, str]],
    finalize_cloud_doc: Callable[..., str],
    build_success_fields: Callable[..., dict[str, Any]],
    queue_record_legacy_doc_phase: Callable[[Any], str | None],
    publish_release_latest_dir_for_target: Callable[..., Path],
    write_publish_release_metadata: Callable[..., Path],
    write_web_publish_metadata: Callable[..., Path] | None = None,
    workflow_action_label: Callable[[str | None], str | None],
    queue_record_key: Callable[[Any], str],
    build_failure_writeback_fields: Callable[..., dict[str, Any]],
    best_effort_queue_workflow_action: Callable[[Any], str | None],
    stderr: Any,
) -> QueueGroupProcessingResult:
    record = group[0]
    word_output_path: Path | None = None
    pdf_output_path: Path | None = None
    md_output_path: Path | None = None
    latex_output_dir: Path | None = None
    html_output_dir: Path | None = None
    artifact_output_path: Path | None = None
    latest_link_url: str | None = None
    latest_document_link_dd_url: str | None = None
    latest_feishu_cloud_doc_url: str | None = None
    group_key = queue_record_key(record)
    row_count = len(group)
    data_sync_status = "skipped"
    claim_attempted = False
    claim_owned = False
    claim_token = ""
    try:
        warn_legacy_record_doc_phase(record)
        validate_queue_record_group(group)
        effective_doc_phase = resolve_queue_workflow_action(record)
        force_phase2_refresh = queue_group_force_phase2_refresh(group)
        refresh_phase2 = force_phase2_refresh or effective_doc_phase == "web_publish"
        started_at = datetime.now(timezone.utc)
        claim_token = uuid4().hex
        claim_expires_at = started_at + timedelta(seconds=queue_claim_ttl_seconds)
        start_fields = build_started_fields(
            started_at=started_at,
            version=record.version,
            workflow_action=effective_doc_phase,
            doc_phase=queue_record_legacy_doc_phase(record),
            data_sync_status="pending" if refresh_phase2 else "skipped",
            claim_token=claim_token,
            claim_expires_at=claim_expires_at,
            write_started_at=can_write_started_at,
        )
        claim_attempted = True
        claim_attempt = acquire_queue_claim(
            source=source,
            base_token=binding.base_token,
            table_id=binding.table_id,
            records=group,
            claim_fields=start_fields,
            result_field=result_field,
            claim_token=claim_token,
        )
        if not claim_attempt.acquired:
            print(
                f"[build-queue] Skipping {group_key} ({row_count} row(s)); {claim_attempt.reason}."
            )
            return QueueGroupProcessingResult(processed_rows=0)
        claim_owned = True
        print(
            f"[build-queue] Acquired queue claim for {group_key} ({row_count} row(s)): "
            f"expires_at={claim_expires_at.isoformat(timespec='seconds')}"
        )
        model, region = resolve_target_for_record(record)
        group_lang = queue_group_lang(group)
        group_build_family = queue_group_build_family(group)
        dingtalk_target_node_url = queue_group_dingtalk_target_node_url(group)
        dingtalk_operator_union_id = queue_group_operator_union_id(group)
        upload_dingtalk = queue_group_upload_dingtalk(group)
        effective_artifact_destination = artifact_destination
        dingtalk_mirror_destination = None
        deferred_status_notes: tuple[str, ...] = ()
        primary_provider = str(getattr(artifact_destination, "provider", "") or "lark_drive")
        mirror_provider = (
            resolve_artifact_mirror_provider(cfg=cfg)
            if effective_doc_phase != "web_publish"
            else None
        )
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
                try:
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
                    ensure_dingtalk_session_ready(
                        cfg=cfg,
                        operator_union_id=dingtalk_operator_union_id,
                    )
                except Exception as exc:
                    message = str(exc).strip()
                    deferred_status_notes = (
                        *deferred_status_notes,
                        "dingtalk_sync=failed",
                        f"dingtalk_sync_error={message}",
                    )
                    dingtalk_mirror_destination = None
                    print(
                        f"[build-queue] WARNING DingTalk sync unavailable for {group_key} ({row_count} row(s)); "
                        f"using Feishu/wiki only: {message}",
                        file=stderr,
                    )
        if (
            effective_doc_phase != "web_publish"
            and str(getattr(effective_artifact_destination, "provider", "") or "")
            == "dingtalk_alidocs_session"
        ):
            ensure_dingtalk_session_ready(
                cfg=cfg,
                operator_union_id=dingtalk_operator_union_id,
            )
        resolved_config_path = resolve_config_path_for_task(
            region=region,
            lang=group_lang,
            build_family=group_build_family,
            workflow_action=effective_doc_phase,
        )
        if effective_doc_phase in {"draft", "web_publish"} and not record.git_ref.strip():
            raise RuntimeError(
                f"{workflow_action_label(effective_doc_phase)} queue rows require Git_ref "
                "so the worker can fetch the review branch"
            )
        if refresh_phase2:
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
        built_outputs = build_document_for_task(
            config_path=resolved_config_path,
            model=model,
            region=region,
            data_root=data_root,
            doc_phase=effective_doc_phase,
            lang=group_lang,
            version=record.version,
            git_ref=record.git_ref,
        )
        if isinstance(built_outputs, Path):
            word_output_path = built_outputs
            artifact_output_path = built_outputs
            pdf_output_path = built_outputs if built_outputs.suffix.lower() == ".pdf" else None
        else:
            word_output_path = built_outputs.word_output_path
            pdf_output_path = built_outputs.pdf_output_path
            md_output_path = built_outputs.md_output_path
            latex_output_dir = built_outputs.latex_output_dir
            html_output_dir = built_outputs.html_output_dir
            artifact_output_path = built_outputs.upload_output_path
        # Upload the built artifact to the knowledge base ONLY in publish: the IDML
        # file's link lands in the idml_file field. In review the deliverable is the
        # Feishu cloud doc (below), so the Word is NOT uploaded to the KB.
        artifact_status_notes: tuple[str, ...] = ()
        document_link_url = ""
        document_link_dd_url = ""
        if effective_doc_phase == "publish":
            _suffix = artifact_output_path.suffix.lower() if artifact_output_path else ""
            artifact_result = publish_word_artifact(
                cfg=cfg,
                cli_bin=cli_bin,
                artifact_output_path=artifact_output_path,
                identity=identity,
                artifact_destination=effective_artifact_destination,
                dingtalk_mirror_destination=dingtalk_mirror_destination,
                dingtalk_operator_union_id=dingtalk_operator_union_id,
                artifact_label={".zip": "handoff", ".idml": "idml", ".pdf": "pdf"}.get(_suffix, "docx"),
            )
            latest_link_url = artifact_result.latest_link_url
            document_link_url = artifact_result.document_link_url
            document_link_dd_url = artifact_result.document_link_dd_url
            latest_document_link_dd_url = document_link_dd_url or None
            artifact_status_notes = artifact_result.status_notes
        built_at = datetime.now().astimezone()
        # Delivery outbox is an additive side channel: the DingTalk delivery agent
        # consumes it out of band, so a drop failure must never fail a build whose
        # artifact already reached the knowledge base. It stays visible through the
        # row's status notes, same contract as dingtalk_sync=*.
        delivery_status_notes: tuple[str, ...] = ()
        if effective_doc_phase == "publish":
            delivery_status_notes = drop_publish_delivery_outbox(
                model=model,
                region=region,
                lang=group_lang,
                version=record.version,
                git_ref=record.git_ref,
                workflow_action=effective_doc_phase,
                built_at=built_at,
                queue_record_ids=tuple(group_record.record_id for group_record in group),
                document_link_url=document_link_url,
                artifact_output_path=artifact_output_path,
                word_output_path=word_output_path,
                pdf_output_path=pdf_output_path,
                md_output_path=md_output_path,
                stderr=stderr,
            )
        feishu_cloud_doc_url = ""
        baseline_doc_url = ""
        cloud_doc_status_notes: tuple[str, ...] = ()
        # Cloud doc (+ frozen baseline) is a REVIEW deliverable only; publish emits
        # IDML/HTML/PDF and does not build a Feishu cloud doc.
        if can_write_feishu_cloud_doc and effective_doc_phase == "draft":
            if md_output_path is None:
                raise RuntimeError("Markdown output was not created for Feishu cloud doc import")
            # Import the built Word .docx (images embedded) — NOT the Markdown, whose
            # local relative image paths Feishu cannot resolve (blank images). Keep the
            # Markdown's versioned stem as the cloud-doc display name.
            _cloud_doc_token, feishu_cloud_doc_url = import_markdown_to_cloud_doc(
                cli_bin=cli_bin,
                source_path=word_output_path,
                identity=identity,
                doc_name=md_output_path.stem,
            )
            # Grant the operator edit access (the bot owns the import, so without
            # this they can only make a 副本) and co-locate it in the Word's wiki
            # node. Best-effort: returns the wiki URL after a move, else the import
            # URL. Both never fail the build.
            feishu_cloud_doc_url = finalize_cloud_doc(
                cli_bin=cli_bin,
                identity=identity,
                cloud_doc_token=_cloud_doc_token,
                cloud_doc_url=feishu_cloud_doc_url,
                member_union_id=dingtalk_operator_union_id,
                destination=effective_artifact_destination,
            )
            latest_feishu_cloud_doc_url = feishu_cloud_doc_url
            # Frozen baseline (R0): a second import of the same Word .docx, placed in
            # the review-doc node WITHOUT an edit grant. Backport later diffs the
            # editable 飞书云文档 against this (render-vs-render → only the reviewer's
            # edits). Suffix the name with _基线<YYYYMMDD> so the frozen baseline is
            # distinguishable from the identically-sourced editable 飞书云文档.
            _baseline_token, baseline_doc_url = import_markdown_to_cloud_doc(
                cli_bin=cli_bin,
                source_path=word_output_path,
                identity=identity,
                doc_name=f"{md_output_path.stem}_基线{built_at:%Y%m%d}",
            )
            baseline_doc_url = finalize_cloud_doc(
                cli_bin=cli_bin,
                identity=identity,
                cloud_doc_token=_baseline_token,
                cloud_doc_url=baseline_doc_url,
                member_union_id="",
                destination=effective_artifact_destination,
                grant=False,
            )
            cloud_doc_status_notes = ("cloud_doc=ok", "baseline_doc=ok")
        success_fields = build_success_fields(
            version=record.version,
            word_output_path=word_output_path,
            document_link_url=document_link_url,
            document_link_dd_url=document_link_dd_url,
            feishu_cloud_doc_url=feishu_cloud_doc_url,
            built_at=built_at,
            workflow_action=effective_doc_phase,
            doc_phase=queue_record_legacy_doc_phase(record),
            data_sync_status=data_sync_status,
            status_notes=(
                *artifact_status_notes,
                *cloud_doc_status_notes,
                *delivery_status_notes,
                *deferred_status_notes,
            ),
            clear_force_phase2_refresh=can_write_force_phase2_refresh,
            write_data_sync=can_write_data_sync,
            write_document_link_dd=can_write_document_link_dd,
            write_feishu_cloud_doc=can_write_feishu_cloud_doc,
            write_document_directory=effective_doc_phase != "web_publish",
            write_document_link=effective_doc_phase != "web_publish",
        )
        # Record the frozen baseline doc link alongside the editable one (success_fields
        # is a plain dict). Backport reads 基线文档 from the row to diff against.
        if can_write_feishu_cloud_doc and baseline_doc_url:
            success_fields[BASELINE_DOC_FIELD] = baseline_doc_url
        _write_terminal_queue_fields(
            source=source,
            base_token=binding.base_token,
            table_id=binding.table_id,
            group=group,
            fields=success_fields,
            result_field=result_field,
            claim_token=claim_token,
        )
        if effective_doc_phase == "publish":
            write_publish_release_metadata(
                config_path=resolved_config_path,
                model=model,
                region=region,
                version=record.version,
                git_ref=record.git_ref,
                built_at=built_at,
                word_output_path=word_output_path,
                pdf_output_path=pdf_output_path or artifact_output_path,
                md_output_path=md_output_path,
                handoff_package_path=artifact_output_path,
                latex_dir=latex_output_dir,
                html_dir=None,
                document_link_url=document_link_url,
                queue_record_ids=tuple(group_record.record_id for group_record in group),
            )
        elif effective_doc_phase == "web_publish":
            if md_output_path is None or html_output_dir is None:
                raise RuntimeError("Web Publish output is missing Markdown source or HTML verification output")
            if write_web_publish_metadata is None:
                raise RuntimeError("Web Publish metadata writer is not configured")
            write_web_publish_metadata(
                config_path=resolved_config_path,
                model=model,
                region=region,
                version=record.version,
                git_ref=record.git_ref,
                built_at=built_at,
                md_output_path=md_output_path,
                html_dir=html_output_dir,
                queue_record_ids=tuple(group_record.record_id for group_record in group),
            )
        print(
            f"[build-queue] {workflow_action_label(effective_doc_phase) or 'Updated'} "
            f"{group_key} ({row_count} row(s)): "
            f"{artifact_output_path or md_output_path}"
            + (f" -> {document_link_url}" if document_link_url else "")
        )
        return QueueGroupProcessingResult(processed_rows=row_count)
    except Exception as exc:
        latest_link_url = getattr(exc, "latest_link_url", None) or latest_link_url
        message = str(exc).strip()
        failure_message = (
            f"{workflow_action_label(record.workflow_action or record.doc_phase) or 'Queue task'} "
            f"{group_key} ({row_count} row(s)): {message}"
        )
        if claim_attempted and not claim_owned:
            print(
                f"[build-queue] ERROR queue claim failed for {group_key}: {message}",
                file=stderr,
            )
            return QueueGroupProcessingResult(processed_rows=0, failure_message=failure_message)
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
                feishu_cloud_doc_url=latest_feishu_cloud_doc_url,
                clear_force_phase2_refresh=can_write_force_phase2_refresh,
                write_data_sync=can_write_data_sync,
                write_document_link_dd=can_write_document_link_dd,
                write_feishu_cloud_doc=can_write_feishu_cloud_doc,
            )
            _write_terminal_queue_fields(
                source=source,
                base_token=binding.base_token,
                table_id=binding.table_id,
                group=group,
                fields=failure_fields,
                result_field=result_field,
                claim_token=claim_token,
            )
        except Exception as writeback_exc:
            failure_message = append_writeback_failed(failure_message, writeback_exc)
            print(
                f"[build-queue] ERROR writeback failed for {group_key}: {writeback_exc}",
                file=stderr,
            )
        return QueueGroupProcessingResult(processed_rows=0, failure_message=failure_message)
