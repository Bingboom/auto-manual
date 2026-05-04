from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Any

from tools.phase2_support import load_config
from tools.queue_execute import dispatch_command_for_row
from tools.queue_query import (
    QueueQueryRow,
    apply_inferred_queue_query,
    collect_queue_query_rows,
    filter_queue_query_rows,
)


_STATUS_QUERY_RE = (
    "status",
    "state",
    "progress",
    "done",
    "finished",
    "complete",
    "completed",
    "latest link",
    "result",
    "failure",
    "failed",
    "状态",
    "进度",
    "好了",
    "好了吗",
    "好了没",
    "跑完",
    "完成",
    "完成了吗",
    "结果",
    "链接",
    "失败",
    "为什么",
    "怎么回事",
    "到哪",
    "查",
    "看一下",
)


def _is_status_query_text(raw_text: str | None) -> bool:
    text = str(raw_text or "").strip().lower()
    if not text:
        return False
    return any(token in text for token in _STATUS_QUERY_RE)


def _compact_selector_payload(args: argparse.Namespace) -> dict[str, str]:
    fields = (
        "query_text",
        "queue_scope",
        "record_id",
        "task_id",
        "task_id_prefix",
        "document_id",
        "document_key",
        "build_family",
        "lang",
        "document_version",
        "market_group",
        "query_workflow_action",
        "git_ref_contains",
        "result_contains",
    )
    payload: dict[str, str] = {}
    for field_name in fields:
        value = str(getattr(args, field_name, "") or "").strip()
        if value:
            payload[field_name] = value
    return payload


def _action_name_from_request(resolved_args: argparse.Namespace, row: QueueQueryRow | None) -> str:
    requested = str(getattr(resolved_args, "query_workflow_action", "") or "").strip().lower()
    aliases = {
        "start-review": "start_review",
        "start_review": "start_review",
        "start review": "start_review",
        "build-draft": "build_draft_package",
        "build draft": "build_draft_package",
        "build-draft-package": "build_draft_package",
        "build draft package": "build_draft_package",
        "draft": "build_draft_package",
        "publish": "publish",
    }
    if requested and _is_status_query_text(getattr(resolved_args, "query_text", None)):
        return "query_status"
    if requested:
        return aliases.get(requested, "query_status")
    return "query_status"


def _action_label(action_name: str) -> str:
    labels = {
        "query_status": "Query Status",
        "start_review": "Start Review",
        "build_draft_package": "Build Draft Package",
        "publish": "Publish",
    }
    return labels.get(action_name, action_name)


def _dispatch_command_for_action_name(action_name: str) -> str | None:
    mapping = {
        "start_review": "start-review",
        "build_draft_package": "build-draft",
        "publish": "publish",
    }
    return mapping.get(action_name)


def _missing_fields_for_action(action_name: str, row: QueueQueryRow | None) -> list[str]:
    if row is None:
        return []
    missing: list[str] = []
    if action_name in {"start_review", "build_draft_package", "publish"} and not row.build_family:
        missing.append("build_family")
    if action_name in {"build_draft_package", "publish"} and not row.git_ref:
        missing.append("git_ref")
    if action_name in {"build_draft_package", "publish"} and row.build_trigger_requested is False:
        missing.append("是否触发文档构建")
    return missing


def _requires_confirmation(action_name: str, args: argparse.Namespace) -> bool:
    return action_name == "publish" and not bool(getattr(args, "confirm_publish", False))


@dataclass(frozen=True)
class QueueActionCandidate:
    record_id: str
    task_id: str
    queue_scope: str
    document_id: str
    document_key: str
    build_family: str
    workflow_action: str
    git_ref: str
    result: str
    review_status: str
    lang: str = ""
    version: str = ""
    market_group: str = ""


@dataclass(frozen=True)
class QueueActionResolution:
    resolution_status: str
    action_name: str
    queue_scope: str
    matched_count: int
    ready: bool
    requires_confirmation: bool
    dispatch_command: str | None
    selectors: dict[str, str]
    missing_fields: list[str]
    summary: str
    next_step: str
    row: dict[str, Any] | None
    candidates: list[QueueActionCandidate]


def _candidate_from_row(row: QueueQueryRow) -> QueueActionCandidate:
    return QueueActionCandidate(
        record_id=row.record_id,
        task_id=row.task_id or f"{row.document_id}_{row.workflow_action}".strip("_"),
        queue_scope=row.queue_scope,
        document_id=row.document_id,
        document_key=row.document_key,
        build_family=row.build_family,
        workflow_action=row.workflow_action,
        git_ref=row.git_ref,
        result=row.result,
        review_status=row.review_status,
        lang=row.lang,
        version=row.version,
        market_group=row.market_group,
    )


def _batch_missing_fields(action_name: str, rows: list[QueueQueryRow]) -> list[str]:
    missing: list[str] = []
    for row in rows:
        for field_name in _missing_fields_for_action(action_name, row):
            missing.append(f"{row.record_id}.{field_name}")
    return missing


def _common_queue_scope(rows: list[QueueQueryRow], fallback: str) -> str:
    scopes = {row.queue_scope for row in rows if row.queue_scope}
    if len(scopes) == 1:
        return next(iter(scopes))
    return fallback


def resolve_queue_action(args: argparse.Namespace, rows: list[QueueQueryRow]) -> QueueActionResolution:
    resolved_args = apply_inferred_queue_query(args)
    filtered = filter_queue_query_rows(resolved_args, rows)
    selected_row = filtered[0] if len(filtered) == 1 else None
    action_name = _action_name_from_request(resolved_args, selected_row)
    dispatch_command = (
        dispatch_command_for_row(selected_row)
        if selected_row is not None and action_name != "query_status"
        else _dispatch_command_for_action_name(action_name)
    )
    selectors = _compact_selector_payload(resolved_args)

    if not filtered:
        return QueueActionResolution(
            resolution_status="target_not_found",
            action_name=action_name,
            queue_scope=str(getattr(resolved_args, "queue_scope", "all") or "all"),
            matched_count=0,
            ready=False,
            requires_confirmation=False,
            dispatch_command=dispatch_command,
            selectors=selectors,
            missing_fields=[],
            summary="No queue row matched the current selectors.",
            next_step="Refine one exact selector such as record_id, Task_id, Document_ID, Build_family, or Workflow_action.",
            row=None,
            candidates=[],
        )

    if len(filtered) > 1 and bool(getattr(resolved_args, "allow_multiple", False)) and action_name != "query_status":
        missing_fields = _batch_missing_fields(action_name, filtered)
        queue_scope = _common_queue_scope(filtered, str(getattr(resolved_args, "queue_scope", "all") or "all"))
        if missing_fields:
            return QueueActionResolution(
                resolution_status="missing_required_field",
                action_name=action_name,
                queue_scope=queue_scope,
                matched_count=len(filtered),
                ready=False,
                requires_confirmation=False,
                dispatch_command=dispatch_command,
                selectors=selectors,
                missing_fields=missing_fields,
                summary="Resolved multiple queue rows, but some required fields are still missing.",
                next_step="Fill the missing queue fields and resolve again. Batch Build Draft Package rows require Git_ref and 是否触发文档构建=Y.",
                row=None,
                candidates=[_candidate_from_row(row) for row in filtered],
            )
        if _requires_confirmation(action_name, resolved_args):
            return QueueActionResolution(
                resolution_status="confirmation_required",
                action_name=action_name,
                queue_scope=queue_scope,
                matched_count=len(filtered),
                ready=False,
                requires_confirmation=True,
                dispatch_command=dispatch_command,
                selectors=selectors,
                missing_fields=[],
                summary=f"Resolved {len(filtered)} Publish rows. Explicit confirmation is still required before dispatch.",
                next_step="Re-run with --confirm-publish before dispatching a batch Publish.",
                row=None,
                candidates=[_candidate_from_row(row) for row in filtered],
            )
        return QueueActionResolution(
            resolution_status="resolved_batch",
            action_name=action_name,
            queue_scope=queue_scope,
            matched_count=len(filtered),
            ready=True,
            requires_confirmation=False,
            dispatch_command=dispatch_command,
            selectors=selectors,
            missing_fields=[],
            summary=f"Resolved {len(filtered)} {_action_label(action_name)} rows.",
            next_step="This batch is ready for the OpenClaw dispatch layer.",
            row=None,
            candidates=[_candidate_from_row(row) for row in filtered],
        )

    if len(filtered) > 1:
        return QueueActionResolution(
            resolution_status="ambiguous_target",
            action_name=action_name,
            queue_scope=str(getattr(resolved_args, "queue_scope", "all") or "all"),
            matched_count=len(filtered),
            ready=False,
            requires_confirmation=False,
            dispatch_command=dispatch_command,
            selectors=selectors,
            missing_fields=[],
            summary="Multiple queue rows matched the current selectors.",
            next_step="Resolve one exact record_id or narrow the request with Task_id, Workflow_action, Build_family, or Git_ref.",
            row=None,
            candidates=[_candidate_from_row(row) for row in filtered[:5]],
        )

    missing_fields = _missing_fields_for_action(action_name, selected_row)
    if missing_fields:
        return QueueActionResolution(
            resolution_status="missing_required_field",
            action_name=action_name,
            queue_scope=selected_row.queue_scope,
            matched_count=1,
            ready=False,
            requires_confirmation=False,
            dispatch_command=dispatch_command,
            selectors=selectors,
            missing_fields=missing_fields,
            summary=f"Resolved one {_action_label(action_name)} row, but required fields are still missing.",
            next_step="Fill the missing queue fields and resolve again. Build Draft Package and Publish require Git_ref.",
            row=asdict(selected_row),
            candidates=[],
        )

    if _requires_confirmation(action_name, resolved_args):
        return QueueActionResolution(
            resolution_status="confirmation_required",
            action_name=action_name,
            queue_scope=selected_row.queue_scope,
            matched_count=1,
            ready=False,
            requires_confirmation=True,
            dispatch_command=dispatch_command,
            selectors=selectors,
            missing_fields=[],
            summary="Resolved one Publish row. Explicit confirmation is still required before dispatch.",
            next_step="Re-run with --confirm-publish or use `/publish rec_xxx confirm` from OpenClaw.",
            row=asdict(selected_row),
            candidates=[],
        )

    next_step = (
        "Read the returned writeback fields."
        if action_name == "query_status"
        else "This action is ready for queue-execute or the OpenClaw dispatch layer."
    )
    return QueueActionResolution(
        resolution_status="resolved",
        action_name=action_name,
        queue_scope=selected_row.queue_scope,
        matched_count=1,
        ready=True,
        requires_confirmation=False,
        dispatch_command=dispatch_command,
        selectors=selectors,
        missing_fields=[],
        summary=f"Resolved one {_action_label(action_name)} row.",
        next_step=next_step,
        row=asdict(selected_row),
        candidates=[],
    )


def render_queue_action_resolution(resolution: QueueActionResolution, *, as_json: bool) -> str:
    if as_json:
        return json.dumps(asdict(resolution), ensure_ascii=False, indent=2)

    lines = [
        f"resolution_status: {resolution.resolution_status}",
        f"action_name: {resolution.action_name}",
        f"queue_scope: {resolution.queue_scope}",
        f"matched_count: {resolution.matched_count}",
        f"ready: {str(resolution.ready).lower()}",
        f"requires_confirmation: {str(resolution.requires_confirmation).lower()}",
        f"summary: {resolution.summary}",
        f"next_step: {resolution.next_step}",
    ]
    if resolution.dispatch_command:
        lines.append(f"dispatch_command: {resolution.dispatch_command}")
    if resolution.selectors:
        for key, value in resolution.selectors.items():
            lines.append(f"selector_{key}: {value}")
    if resolution.missing_fields:
        lines.append(f"missing_fields: {', '.join(resolution.missing_fields)}")
    if resolution.row:
        row = resolution.row
        lines.append(f"record_id: {row.get('record_id', '')}")
        if row.get("task_id"):
            lines.append(f"task_id: {row['task_id']}")
        if row.get("document_id"):
            lines.append(f"document_id: {row['document_id']}")
        if row.get("build_family"):
            lines.append(f"build_family: {row['build_family']}")
        if row.get("git_ref"):
            lines.append(f"git_ref: {row['git_ref']}")
    if resolution.candidates:
        lines.append("candidates:")
        for candidate in resolution.candidates:
            lines.append(
                "  - "
                + " | ".join(
                    part
                    for part in (
                        candidate.record_id,
                        candidate.task_id or "-",
                        candidate.document_id or candidate.document_key or "-",
                        candidate.workflow_action or "-",
                        candidate.git_ref or "-",
                    )
                    if part
                )
            )
    return "\n".join(lines)


def run_queue_resolve_action(args: argparse.Namespace, *, config_path) -> None:
    cfg = load_config(config_path)
    rows = collect_queue_query_rows(cfg, queue_scope=getattr(args, "queue_scope", "all"))
    resolution = resolve_queue_action(args, rows)
    print(render_queue_action_resolution(resolution, as_json=bool(getattr(args, "json", False))))


if __name__ == "__main__":
    raise SystemExit("Use `python build.py queue-resolve-action ...`.")
