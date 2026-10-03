from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from tools.delivery_outbox import drop_publish_delivery_outbox
from tools.document_link_queue import scalar_text
from tools.build_queue.contract import BASELINE_DOC_FIELD
from tools.build_queue.transitions import (
    append_writeback_failed,
    has_active_queue_claim,
    queue_claim_is_owned,
)
from tools.utils.log import get_logger

_LOG = get_logger("build-queue")


def utc_now() -> datetime:
    """The default queue clock: the current time as an aware UTC ``datetime``."""
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class QueueGroupProcessingResult:
    processed_rows: int
    failure_message: str | None = None
    workspace_deliveries: tuple[str, ...] = ()
    workspace_error: str | None = None


def _workspace_group_result(source, binding, group, success_fields, row_count):
    from tools.workspace_refresh_trigger import delivery_readback

    try:
        delivered = delivery_readback(source, binding, group, success_fields)
    except Exception:  # noqa: BLE001 - preserve production success; refresh is independently retryable
        return QueueGroupProcessingResult(processed_rows=row_count, workspace_error="source-readback failed")
    return QueueGroupProcessingResult(processed_rows=row_count, workspace_deliveries=tuple(delivered))


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


@dataclass
class _GroupRunState:
    """How far one queue group got; the failure writeback reports what was reached."""

    word_output_path: Path | None = None
    pdf_output_path: Path | None = None
    md_output_path: Path | None = None
    latex_output_dir: Path | None = None
    html_output_dir: Path | None = None
    language_projection_evidence_path: Path | None = None
    built_target_lang: str | None = None
    artifact_output_path: Path | None = None
    latest_link_url: str | None = None
    latest_document_link_dd_url: str | None = None
    latest_feishu_cloud_doc_url: str | None = None
    data_sync_status: str = "skipped"
    claim_attempted: bool = False
    claim_owned: bool = False
    claim_token: str = ""


def _primary_dingtalk_destination(
    *,
    cfg: dict[str, Any],
    cli_bin: str,
    identity: str,
    binding: Any,
    label: str,
    artifact_destination: Any,
    upload_dingtalk: bool,
    dingtalk_target_node_url: str,
    resolve_row_artifact_destination: Callable[..., Any],
    resolve_lark_wiki_destination: Callable[..., Any],
) -> Any:
    """Pick the upload target when DingTalk is the primary artifact provider."""

    if not upload_dingtalk:
        _LOG.info(f"[build-queue] Skipping DingTalk upload for {label}; using Feishu/wiki upload.")
        return resolve_lark_wiki_destination(
            cli_bin=cli_bin,
            identity=identity,
            binding=binding,
        )
    if dingtalk_target_node_url:
        destination = resolve_row_artifact_destination(
            cfg=cfg,
            cli_bin=cli_bin,
            identity=identity,
            binding=binding,
            target_node_url=dingtalk_target_node_url,
        )
        _LOG.info(
            f"[build-queue] Using DingTalk upload for {label} "
            f"with row target {dingtalk_target_node_url}."
        )
        return destination
    if not getattr(artifact_destination, "runtime_target", None):
        raise RuntimeError(
            "DingTalk target node URL is required: provide row DingTalk_target_node_url "
            "or configure DINGTALK_DOCS_TARGET_NODE_URL for the remote worker"
        )
    _LOG.info(f"[build-queue] Using DingTalk upload for {label} with default target.")
    return artifact_destination


def _dingtalk_mirror_destination(
    *,
    cfg: dict[str, Any],
    label: str,
    dingtalk_target_node_url: str,
    dingtalk_operator_union_id: str,
    resolve_dingtalk_mirror_destination: Callable[..., Any],
    ensure_dingtalk_session_ready: Callable[..., None],
    stderr: Any,
) -> tuple[Any, tuple[str, ...]]:
    """Resolve the DingTalk mirror; a failure only downgrades to Feishu/wiki."""

    try:
        if dingtalk_target_node_url:
            destination = resolve_dingtalk_mirror_destination(
                cfg=cfg,
                target_node_url=dingtalk_target_node_url,
            )
            _LOG.info(
                f"[build-queue] Syncing DingTalk upload for {label} "
                f"with row target {dingtalk_target_node_url}."
            )
        else:
            destination = resolve_dingtalk_mirror_destination(cfg=cfg)
            _LOG.info(f"[build-queue] Syncing DingTalk upload for {label} with default target.")
        ensure_dingtalk_session_ready(
            cfg=cfg,
            operator_union_id=dingtalk_operator_union_id,
        )
    except Exception as exc:  # noqa: BLE001 - DingTalk mirror is a side channel recorded in status notes
        message = str(exc).strip()
        print(
            f"[build-queue] WARNING DingTalk sync unavailable for {label}; "
            f"using Feishu/wiki only: {message}",
            file=stderr,
        )
        return None, ("dingtalk_sync=failed", f"dingtalk_sync_error={message}")
    return destination, ()


def _resolve_upload_destinations(
    *,
    cfg: dict[str, Any],
    cli_bin: str,
    identity: str,
    binding: Any,
    label: str,
    artifact_destination: Any,
    effective_doc_phase: str | None,
    has_upload_dingtalk_field: bool,
    upload_dingtalk: bool,
    dingtalk_target_node_url: str,
    dingtalk_operator_union_id: str,
    resolve_artifact_mirror_provider: Callable[..., str | None],
    resolve_row_artifact_destination: Callable[..., Any],
    resolve_lark_wiki_destination: Callable[..., Any],
    resolve_dingtalk_mirror_destination: Callable[..., Any],
    ensure_dingtalk_session_ready: Callable[..., None],
    stderr: Any,
) -> tuple[Any, Any, tuple[str, ...]]:
    """Return ``(artifact destination, DingTalk mirror destination, status notes)``."""

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
        effective_artifact_destination = _primary_dingtalk_destination(
            cfg=cfg,
            cli_bin=cli_bin,
            identity=identity,
            binding=binding,
            label=label,
            artifact_destination=artifact_destination,
            upload_dingtalk=upload_dingtalk,
            dingtalk_target_node_url=dingtalk_target_node_url,
            resolve_row_artifact_destination=resolve_row_artifact_destination,
            resolve_lark_wiki_destination=resolve_lark_wiki_destination,
        )
    elif primary_provider == "lark_drive" and mirror_provider == "dingtalk_alidocs_session":
        if has_upload_dingtalk_field and not upload_dingtalk:
            _LOG.info(f"[build-queue] Skipping DingTalk sync for {label}; using Feishu/wiki only.")
            deferred_status_notes = ("dingtalk_sync=skipped",)
        else:
            dingtalk_mirror_destination, deferred_status_notes = _dingtalk_mirror_destination(
                cfg=cfg,
                label=label,
                dingtalk_target_node_url=dingtalk_target_node_url,
                dingtalk_operator_union_id=dingtalk_operator_union_id,
                resolve_dingtalk_mirror_destination=resolve_dingtalk_mirror_destination,
                ensure_dingtalk_session_ready=ensure_dingtalk_session_ready,
                stderr=stderr,
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
    return effective_artifact_destination, dingtalk_mirror_destination, deferred_status_notes


def _sync_phase2_snapshot(
    state: _GroupRunState,
    *,
    label: str,
    config_path: Path,
    data_root: str | None,
    sync_phase2_snapshot_before_queue: Callable[..., None],
) -> None:
    _LOG.info(f"[build-queue] Syncing latest phase2 snapshot before {label}.")
    try:
        sync_phase2_snapshot_before_queue(
            config_path=config_path,
            data_root=data_root,
        )
    except Exception:
        state.data_sync_status = "failed"
        raise
    state.data_sync_status = "refreshed"


def _record_built_outputs(state: _GroupRunState, built_outputs: Any) -> None:
    if isinstance(built_outputs, Path):
        state.word_output_path = built_outputs
        state.artifact_output_path = built_outputs
        state.pdf_output_path = built_outputs if built_outputs.suffix.lower() == ".pdf" else None
        return
    state.word_output_path = built_outputs.word_output_path
    state.pdf_output_path = built_outputs.pdf_output_path
    state.md_output_path = built_outputs.md_output_path
    state.latex_output_dir = built_outputs.latex_output_dir
    state.html_output_dir = built_outputs.html_output_dir
    state.language_projection_evidence_path = getattr(
        built_outputs, "language_projection_evidence_path", None
    )
    state.built_target_lang = getattr(built_outputs, "target_lang", None)
    state.artifact_output_path = built_outputs.upload_output_path


def _publish_artifact(
    state: _GroupRunState,
    *,
    cfg: dict[str, Any],
    cli_bin: str,
    identity: str,
    artifact_destination: Any,
    dingtalk_mirror_destination: Any,
    dingtalk_operator_union_id: str,
    publish_word_artifact: Callable[..., Any],
) -> tuple[str, str, tuple[str, ...]]:
    """Upload the publish artifact; return ``(link, DingTalk link, status notes)``."""

    artifact_output_path = state.artifact_output_path
    suffix = artifact_output_path.suffix.lower() if artifact_output_path else ""
    artifact_result = publish_word_artifact(
        cfg=cfg,
        cli_bin=cli_bin,
        artifact_output_path=artifact_output_path,
        identity=identity,
        artifact_destination=artifact_destination,
        dingtalk_mirror_destination=dingtalk_mirror_destination,
        dingtalk_operator_union_id=dingtalk_operator_union_id,
        artifact_label={".zip": "handoff", ".idml": "idml", ".pdf": "pdf"}.get(suffix, "docx"),
    )
    state.latest_link_url = artifact_result.latest_link_url
    document_link_url = artifact_result.document_link_url
    document_link_dd_url = artifact_result.document_link_dd_url
    state.latest_document_link_dd_url = document_link_dd_url or None
    return document_link_url, document_link_dd_url, artifact_result.status_notes


def _create_review_cloud_docs(
    state: _GroupRunState,
    *,
    cli_bin: str,
    identity: str,
    operator_union_id: str,
    destination: Any,
    built_at: datetime,
    import_markdown_to_cloud_doc: Callable[..., tuple[str, str]],
    finalize_cloud_doc: Callable[..., str],
) -> tuple[str, str]:
    """Import the editable review cloud doc and its frozen baseline; return both URLs."""

    md_output_path = state.md_output_path
    if md_output_path is None:
        raise RuntimeError("Markdown output was not created for Feishu cloud doc import")
    # Import the built Word .docx (images embedded) — NOT the Markdown, whose
    # local relative image paths Feishu cannot resolve (blank images). Keep the
    # Markdown's versioned stem as the cloud-doc display name.
    cloud_doc_token, feishu_cloud_doc_url = import_markdown_to_cloud_doc(
        cli_bin=cli_bin,
        source_path=state.word_output_path,
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
        cloud_doc_token=cloud_doc_token,
        cloud_doc_url=feishu_cloud_doc_url,
        member_union_id=operator_union_id,
        destination=destination,
    )
    state.latest_feishu_cloud_doc_url = feishu_cloud_doc_url
    # Frozen baseline (R0): a second import of the same Word .docx, placed in
    # the review-doc node WITHOUT an edit grant. Backport later diffs the
    # editable 飞书云文档 against this (render-vs-render → only the reviewer's
    # edits). Suffix the name with _基线<YYYYMMDD> so the frozen baseline is
    # distinguishable from the identically-sourced editable 飞书云文档.
    baseline_token, baseline_doc_url = import_markdown_to_cloud_doc(
        cli_bin=cli_bin,
        source_path=state.word_output_path,
        identity=identity,
        doc_name=f"{md_output_path.stem}_基线{built_at:%Y%m%d}",
    )
    baseline_doc_url = finalize_cloud_doc(
        cli_bin=cli_bin,
        identity=identity,
        cloud_doc_token=baseline_token,
        cloud_doc_url=baseline_doc_url,
        member_union_id="",
        destination=destination,
        grant=False,
    )
    return feishu_cloud_doc_url, baseline_doc_url


def _write_web_publish_outputs(
    state: _GroupRunState,
    *,
    write_web_publish_metadata: Callable[..., Path] | None,
    config_path: Path,
    model: str,
    region: str,
    record: Any,
    built_at: datetime,
    queue_record_ids: tuple[str, ...],
) -> None:
    if state.md_output_path is None or state.html_output_dir is None:
        raise RuntimeError("Web Publish output is missing Markdown source or HTML verification output")
    if write_web_publish_metadata is None:
        raise RuntimeError("Web Publish metadata writer is not configured")
    write_web_publish_metadata(
        config_path=config_path,
        model=model,
        region=region,
        version=record.version,
        git_ref=record.git_ref,
        built_at=built_at,
        md_output_path=state.md_output_path,
        html_dir=state.html_output_dir,
        queue_record_ids=queue_record_ids,
        target_lang=state.built_target_lang,
        language_projection_evidence_path=state.language_projection_evidence_path,
    )


def _report_group_failure(
    exc: Exception,
    state: _GroupRunState,
    *,
    record: Any,
    group: list[Any],
    label: str,
    group_key: str,
    source: Any,
    binding: Any,
    result_field: str,
    can_write_force_phase2_refresh: bool,
    can_write_data_sync: bool,
    can_write_document_link_dd: bool,
    can_write_feishu_cloud_doc: bool,
    workflow_action_label: Callable[[str | None], str | None],
    queue_record_legacy_doc_phase: Callable[[Any], str | None],
    build_failure_writeback_fields: Callable[..., dict[str, Any]],
    best_effort_queue_workflow_action: Callable[[Any], str | None],
    stderr: Any,
) -> QueueGroupProcessingResult:
    """Write a group failure back to its rows (unless another runner owns them)."""

    latest_link_url = getattr(exc, "latest_link_url", None) or state.latest_link_url
    message = str(exc).strip()
    failure_message = (
        f"{workflow_action_label(record.workflow_action or record.doc_phase) or 'Queue task'} "
        f"{label}: {message}"
    )
    if state.claim_attempted and not state.claim_owned:
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
            data_sync_status=state.data_sync_status,
            word_output_path=state.word_output_path,
            document_link_url=latest_link_url,
            document_link_dd_url=state.latest_document_link_dd_url,
            feishu_cloud_doc_url=state.latest_feishu_cloud_doc_url,
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
            claim_token=state.claim_token,
        )
    except Exception as writeback_exc:  # noqa: BLE001 - writeback failure is appended to the reported failure
        failure_message = append_writeback_failed(failure_message, writeback_exc)
        print(
            f"[build-queue] ERROR writeback failed for {group_key}: {writeback_exc}",
            file=stderr,
        )
    return QueueGroupProcessingResult(processed_rows=0, failure_message=failure_message)


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
    clock: Callable[[], datetime] = utc_now,
) -> QueueGroupProcessingResult:
    record = group[0]
    state = _GroupRunState()
    group_key = queue_record_key(record)
    row_count = len(group)
    label = f"{group_key} ({row_count} row(s))"
    try:
        warn_legacy_record_doc_phase(record)
        validate_queue_record_group(group)
        effective_doc_phase = resolve_queue_workflow_action(record)
        force_phase2_refresh = queue_group_force_phase2_refresh(group)
        refresh_phase2 = force_phase2_refresh or effective_doc_phase == "web_publish"
        started_at = clock()
        state.claim_token = uuid4().hex
        claim_expires_at = started_at + timedelta(seconds=queue_claim_ttl_seconds)
        start_fields = build_started_fields(
            started_at=started_at,
            version=record.version,
            workflow_action=effective_doc_phase,
            doc_phase=queue_record_legacy_doc_phase(record),
            data_sync_status="pending" if refresh_phase2 else "skipped",
            claim_token=state.claim_token,
            claim_expires_at=claim_expires_at,
            write_started_at=can_write_started_at,
        )
        state.claim_attempted = True
        claim_attempt = acquire_queue_claim(
            source=source,
            base_token=binding.base_token,
            table_id=binding.table_id,
            records=group,
            claim_fields=start_fields,
            result_field=result_field,
            claim_token=state.claim_token,
        )
        if not claim_attempt.acquired:
            _LOG.info(f"[build-queue] Skipping {label}; {claim_attempt.reason}.")
            return QueueGroupProcessingResult(processed_rows=0)
        state.claim_owned = True
        _LOG.info(
            f"[build-queue] Acquired queue claim for {label}: "
            f"expires_at={claim_expires_at.isoformat(timespec='seconds')}"
        )
        model, region = resolve_target_for_record(record)
        group_lang = queue_group_lang(group)
        group_build_family = queue_group_build_family(group)
        dingtalk_target_node_url = queue_group_dingtalk_target_node_url(group)
        dingtalk_operator_union_id = queue_group_operator_union_id(group)
        upload_dingtalk = queue_group_upload_dingtalk(group)
        effective_artifact_destination, dingtalk_mirror_destination, deferred_status_notes = (
            _resolve_upload_destinations(
                cfg=cfg,
                cli_bin=cli_bin,
                identity=identity,
                binding=binding,
                label=label,
                artifact_destination=artifact_destination,
                effective_doc_phase=effective_doc_phase,
                has_upload_dingtalk_field=has_upload_dingtalk_field,
                upload_dingtalk=upload_dingtalk,
                dingtalk_target_node_url=dingtalk_target_node_url,
                dingtalk_operator_union_id=dingtalk_operator_union_id,
                resolve_artifact_mirror_provider=resolve_artifact_mirror_provider,
                resolve_row_artifact_destination=resolve_row_artifact_destination,
                resolve_lark_wiki_destination=resolve_lark_wiki_destination,
                resolve_dingtalk_mirror_destination=resolve_dingtalk_mirror_destination,
                ensure_dingtalk_session_ready=ensure_dingtalk_session_ready,
                stderr=stderr,
            )
        )
        resolved_config_path = resolve_config_path_for_task(
            model=model,
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
            _sync_phase2_snapshot(
                state,
                label=label,
                config_path=config_path,
                data_root=data_root,
                sync_phase2_snapshot_before_queue=sync_phase2_snapshot_before_queue,
            )
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
        _record_built_outputs(state, built_outputs)
        # Upload the built artifact to the knowledge base ONLY in publish: the IDML
        # file's link lands in the idml_file field. In review the deliverable is the
        # Feishu cloud doc (below), so the Word is NOT uploaded to the KB.
        artifact_status_notes: tuple[str, ...] = ()
        document_link_url = ""
        document_link_dd_url = ""
        if effective_doc_phase == "publish":
            document_link_url, document_link_dd_url, artifact_status_notes = _publish_artifact(
                state,
                cfg=cfg,
                cli_bin=cli_bin,
                identity=identity,
                artifact_destination=effective_artifact_destination,
                dingtalk_mirror_destination=dingtalk_mirror_destination,
                dingtalk_operator_union_id=dingtalk_operator_union_id,
                publish_word_artifact=publish_word_artifact,
            )
        built_at = clock().astimezone()
        queue_record_ids = tuple(group_record.record_id for group_record in group)
        # Delivery outbox is an additive side channel: the DingTalk delivery agent
        # consumes it out of band, so a drop failure must never fail a build whose
        # artifact already reached the knowledge base. It stays visible through the
        # row's status notes, same contract as dingtalk_sync=*.
        delivery_status_notes: tuple[str, ...] = ()
        if effective_doc_phase == "publish":
            delivery_status_notes = drop_publish_delivery_outbox(
                model=model,
                region=region,
                version=record.version,
                git_ref=record.git_ref,
                workflow_action=effective_doc_phase,
                built_at=built_at,
                queue_record_ids=queue_record_ids,
                document_link_url=document_link_url,
                artifact_output_path=state.artifact_output_path,
                word_output_path=state.word_output_path,
                pdf_output_path=state.pdf_output_path,
                md_output_path=state.md_output_path,
                stderr=stderr,
            )
        feishu_cloud_doc_url = ""
        baseline_doc_url = ""
        cloud_doc_status_notes: tuple[str, ...] = ()
        # Cloud doc (+ frozen baseline) is a REVIEW deliverable only; publish emits
        # IDML/HTML/PDF and does not build a Feishu cloud doc.
        if can_write_feishu_cloud_doc and effective_doc_phase == "draft":
            feishu_cloud_doc_url, baseline_doc_url = _create_review_cloud_docs(
                state,
                cli_bin=cli_bin,
                identity=identity,
                operator_union_id=dingtalk_operator_union_id,
                destination=effective_artifact_destination,
                built_at=built_at,
                import_markdown_to_cloud_doc=import_markdown_to_cloud_doc,
                finalize_cloud_doc=finalize_cloud_doc,
            )
            cloud_doc_status_notes = ("cloud_doc=ok", "baseline_doc=ok")
        success_fields = build_success_fields(
            version=record.version,
            word_output_path=state.word_output_path,
            document_link_url=document_link_url,
            document_link_dd_url=document_link_dd_url,
            feishu_cloud_doc_url=feishu_cloud_doc_url,
            built_at=built_at,
            workflow_action=effective_doc_phase,
            doc_phase=queue_record_legacy_doc_phase(record),
            data_sync_status=state.data_sync_status,
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
        if effective_doc_phase == "web_publish":
            _write_web_publish_outputs(
                state,
                write_web_publish_metadata=write_web_publish_metadata,
                config_path=resolved_config_path,
                model=model,
                region=region,
                record=record,
                built_at=built_at,
                queue_record_ids=queue_record_ids,
            )
        _write_terminal_queue_fields(
            source=source,
            base_token=binding.base_token,
            table_id=binding.table_id,
            group=group,
            fields=success_fields,
            result_field=result_field,
            claim_token=state.claim_token,
        )
        if effective_doc_phase == "publish":
            write_publish_release_metadata(
                config_path=resolved_config_path,
                model=model,
                region=region,
                version=record.version,
                git_ref=record.git_ref,
                built_at=built_at,
                word_output_path=state.word_output_path,
                pdf_output_path=state.pdf_output_path or state.artifact_output_path,
                md_output_path=state.md_output_path,
                handoff_package_path=state.artifact_output_path,
                latex_dir=state.latex_output_dir,
                html_dir=None,
                document_link_url=document_link_url,
                queue_record_ids=queue_record_ids,
            )
        _LOG.info(
            f"[build-queue] {workflow_action_label(effective_doc_phase) or 'Updated'} "
            f"{label}: "
            f"{state.artifact_output_path or state.md_output_path}"
            + (f" -> {document_link_url}" if document_link_url else "")
        )
        return _workspace_group_result(source, binding, group, success_fields, row_count)
    except Exception as exc:  # noqa: BLE001 - group boundary: failure is written back to the row
        return _report_group_failure(
            exc,
            state,
            record=record,
            group=group,
            label=label,
            group_key=group_key,
            source=source,
            binding=binding,
            result_field=result_field,
            can_write_force_phase2_refresh=can_write_force_phase2_refresh,
            can_write_data_sync=can_write_data_sync,
            can_write_document_link_dd=can_write_document_link_dd,
            can_write_feishu_cloud_doc=can_write_feishu_cloud_doc,
            workflow_action_label=workflow_action_label,
            queue_record_legacy_doc_phase=queue_record_legacy_doc_phase,
            build_failure_writeback_fields=build_failure_writeback_fields,
            best_effort_queue_workflow_action=best_effort_queue_workflow_action,
            stderr=stderr,
        )
