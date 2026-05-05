from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.phase2_support import load_config
from tools.queue_query import (
    QueueQueryRow,
    apply_inferred_queue_query,
    collect_queue_query_rows,
    filter_queue_query_rows,
)

_CONTROL_LAYER_CLI = (
    "node",
    "integrations/openclaw/auto-manual-control-layer/cli.mjs",
)
_TERMINAL_CONCLUSIONS = {
    "success",
    "failure",
    "cancelled",
    "timed_out",
    "startup_failure",
    "action_required",
    "neutral",
    "skipped",
}
_SUCCESS_CONCLUSIONS = {"success", "neutral", "skipped"}


def _null_text(value: str) -> str:
    return value if value else "null"


def _namespace_with(args: argparse.Namespace, **updates: Any) -> argparse.Namespace:
    payload = dict(vars(args))
    payload.update(updates)
    return argparse.Namespace(**payload)


def _row_brief(row: QueueQueryRow) -> str:
    pieces = [
        row.record_id,
        row.document_id or row.document_key or "-",
        row.workflow_action or row.normalized_workflow_action or "-",
    ]
    if row.git_ref:
        pieces.append(row.git_ref)
    return " | ".join(pieces)


def select_unique_queue_row(args: argparse.Namespace, rows: list[QueueQueryRow]) -> tuple[argparse.Namespace, QueueQueryRow]:
    resolved_args = apply_inferred_queue_query(args)
    selection_args = _namespace_with(
        resolved_args,
        limit=max(int(getattr(resolved_args, "limit", 10) or 10), 50),
    )
    filtered = filter_queue_query_rows(selection_args, rows)
    if not filtered:
        request_text = str(getattr(args, "query_text", "") or "").strip()
        details = f" for request `{request_text}`" if request_text else ""
        raise RuntimeError(f"queue-execute could not resolve one queue row{details}.")
    if len(filtered) > 1:
        preview = "\n".join(f"- {_row_brief(row)}" for row in filtered[:5])
        raise RuntimeError(
            "queue-execute found multiple matching queue rows. Narrow the request first:\n" + preview
        )
    return resolved_args, filtered[0]


def dispatch_command_for_row(row: QueueQueryRow) -> str:
    mapping = {
        "start_review": "start-review",
        "draft": "build-draft",
        "publish": "publish",
    }
    command = mapping.get(row.normalized_workflow_action or "")
    if command:
        return command
    raise RuntimeError(
        f"queue-execute cannot map queue row {row.record_id} to a dispatch command. "
        f"workflow_action={row.workflow_action!r}"
    )


def _normalized_review_status(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").strip().lower())


def is_completed_start_review_row(row: QueueQueryRow) -> bool:
    if (row.normalized_workflow_action or "") != "start_review":
        return False
    if row.review_trigger_enabled is True:
        return False
    return bool(row.git_ref.strip()) and _normalized_review_status(row.review_status) in {
        "inreview",
        "readyforpublish",
    }


def ensure_start_review_dispatchable(row: QueueQueryRow) -> None:
    if (row.normalized_workflow_action or "") != "start_review":
        return
    if not str(row.document_key or "").strip():
        raise RuntimeError(
            "queue-execute resolved a Start Review row without a Document_Key value. "
            f"record_id={row.record_id} document_key={row.document_key or '-'}"
        )
    if row.review_trigger_enabled is True:
        return
    if is_completed_start_review_row(row):
        return
    raise RuntimeError(
        "queue-execute resolved a Start Review row that is not pending and has not completed. "
        f"record_id={row.record_id} review_status={row.review_status or '-'} git_ref={row.git_ref or '-'}"
    )


def ensure_publish_confirmation(args: argparse.Namespace, row: QueueQueryRow) -> None:
    if (row.normalized_workflow_action or "") != "publish":
        return
    if getattr(args, "confirm_publish", False):
        return
    raise RuntimeError(
        "queue-execute resolved a Publish row. Re-run with `--confirm-publish` to dispatch the Publish worker."
    )


def ensure_build_trigger_requested(row: QueueQueryRow) -> None:
    if (row.normalized_workflow_action or "") not in {"draft", "publish"}:
        return
    if row.build_trigger_requested is True:
        return
    raise RuntimeError(
        "queue-execute resolved a Build Draft Package / Publish row, but `是否触发文档构建` is not enabled. "
        f"record_id={row.record_id} document_id={row.document_id or '-'} workflow_action={row.workflow_action or '-'}"
    )


def parse_control_layer_output(text: str) -> dict[str, str]:
    payload: dict[str, str] = {"raw": text.strip()}
    notes: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            normalized_key = key.strip().lower().replace(" ", "_")
            payload[normalized_key] = value.strip()
            continue
        if "workflow_name" not in payload:
            payload["workflow_name"] = line
        else:
            notes.append(line)
    if notes:
        payload["notes"] = " ".join(notes)
    return payload


def is_terminal_status(status_payload: dict[str, str]) -> bool:
    status = str(status_payload.get("status", "")).strip().lower()
    conclusion = str(status_payload.get("conclusion", "")).strip().lower()
    return status == "completed" or conclusion in _TERMINAL_CONCLUSIONS


def is_successful_status(status_payload: dict[str, str]) -> bool:
    conclusion = str(status_payload.get("conclusion", "")).strip().lower()
    if not conclusion:
        return False
    return conclusion in _SUCCESS_CONCLUSIONS


def has_structured_failure(status_payload: dict[str, str]) -> bool:
    return bool(str(status_payload.get("failure_message", "")).strip())


def build_queue_execute_failure_message(
    *,
    row: QueueQueryRow,
    status_payload: dict[str, str],
    dispatch_payload: dict[str, str],
) -> str:
    run_url = status_payload.get("run", "") or dispatch_payload.get("run", "")
    run_id = status_payload.get("run_id", "") or dispatch_payload.get("run_id", "")
    conclusion = status_payload.get("conclusion", "") or status_payload.get("status", "unknown")
    failure_message = str(status_payload.get("failure_message", "")).strip()
    failure_next_step = str(status_payload.get("failure_next_step", "")).strip()
    if failure_message:
        parts = [failure_message]
        if failure_next_step:
            parts.append(failure_next_step)
        parts.append(f"record_id={row.record_id}")
        if run_id:
            parts.append(f"run_id={run_id}")
        if run_url:
            parts.append(f"run={run_url}")
        return " ".join(parts)
    return (
        "queue-execute dispatched the workflow, but GitHub finished without Feishu writeback. "
        f"record_id={row.record_id} conclusion={conclusion or 'unknown'}"
        + (f" run_id={run_id}" if run_id else "")
        + (f" run={run_url}" if run_url else "")
    )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def render_queue_execute_result(
    row: QueueQueryRow,
    *,
    as_json: bool,
    dispatch_payload: dict[str, str] | None = None,
    accepted_at: str = "",
) -> str:
    dispatch_payload = dispatch_payload or {}
    if as_json:
        payload = {
            "record_id": row.record_id,
            "git_ref": row.git_ref,
            "result": row.result,
            "document_link": row.document_link,
            "freshness_status": row.freshness_status,
        }
        if row.result_built_at:
            payload["result_built_at"] = row.result_built_at
        if row.result_is_fresh is not None:
            payload["result_is_fresh"] = row.result_is_fresh
        if row.build_started_at:
            payload["build_started_at"] = row.build_started_at
        if accepted_at:
            payload["accepted_at"] = accepted_at
        if dispatch_payload.get("run_id"):
            payload["run_id"] = dispatch_payload["run_id"]
        if dispatch_payload.get("run"):
            payload["run_url"] = dispatch_payload["run"]
        if row.pr_url:
            payload["pr_url"] = row.pr_url
        if row.review_status:
            payload["review_status"] = row.review_status
        return json.dumps(payload, ensure_ascii=False, indent=2)
    lines = [
        f"record_id: {_null_text(row.record_id)}",
        f"Git_ref: {_null_text(row.git_ref)}",
    ]
    if row.pr_url:
        lines.append(f"PR_url: {row.pr_url}")
    if row.review_status:
        lines.append(f"Review_status: {row.review_status}")
    if accepted_at:
        lines.append(f"accepted_at: {accepted_at}")
    if dispatch_payload.get("run_id"):
        lines.append(f"run_id: {dispatch_payload['run_id']}")
    if dispatch_payload.get("run"):
        lines.append(f"run: {dispatch_payload['run']}")
    lines.extend(
        [
            f"构建结果: {_null_text(row.result)}",
            f"Document link: {_null_text(row.document_link)}",
            f"freshness_status: {_null_text(row.freshness_status)}",
        ]
    )
    return "\n".join(lines)


def _run_control_layer_cli(repo_root: Path, *cli_args: str) -> dict[str, str]:
    completed = subprocess.run(
        [*_CONTROL_LAYER_CLI, *cli_args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    if completed.returncode != 0:
        details = stderr or stdout or "unknown control-layer error"
        raise RuntimeError(
            "queue-execute control-layer command failed:\n"
            f"$ {' '.join([*_CONTROL_LAYER_CLI, *cli_args])}\n"
            f"{details}"
        )
    return parse_control_layer_output(stdout)


def _refresh_queue_row(cfg: dict[str, Any], row: QueueQueryRow, *, fresh_since: str = "") -> QueueQueryRow:
    refresh_args = argparse.Namespace(
        query_text=None,
        record_id=row.record_id,
        document_id=None,
        document_key=None,
        build_family=None,
        lang=None,
        langs=None,
        document_version=None,
        query_workflow_action=None,
        git_ref_contains=None,
        result_contains=None,
        fresh_since=fresh_since or None,
        limit=1,
        json=False,
        queue_scope=row.queue_scope,
    )
    rows = collect_queue_query_rows(cfg, queue_scope=row.queue_scope)
    filtered = filter_queue_query_rows(refresh_args, rows)
    if not filtered:
        raise RuntimeError(f"queue-execute could not re-read queue row {row.record_id}.")
    return filtered[0]


def run_queue_execute(args: argparse.Namespace, *, config_path: Path, repo_root: Path) -> None:
    cfg = load_config(config_path)
    rows = collect_queue_query_rows(cfg, queue_scope=getattr(args, "queue_scope", "all"))
    resolved_args, row = select_unique_queue_row(args, rows)
    ensure_build_trigger_requested(row)
    ensure_publish_confirmation(resolved_args, row)
    dispatch_command = dispatch_command_for_row(row)
    if is_completed_start_review_row(row):
        print(render_queue_execute_result(row, as_json=bool(getattr(resolved_args, "json", False))))
        return
    ensure_start_review_dispatchable(row)
    accepted_at = str(getattr(resolved_args, "fresh_since", "") or "").strip() or _now_iso()
    if dispatch_command == "publish":
        dispatch_payload = _run_control_layer_cli(repo_root, "dispatch", dispatch_command, row.record_id, "confirm")
    else:
        dispatch_payload = _run_control_layer_cli(repo_root, "dispatch", dispatch_command, row.record_id)
    if dispatch_payload.get("accepted_at"):
        accepted_at = dispatch_payload["accepted_at"]
    final_status_payload = {
        "status": "",
        "conclusion": "",
        "run": dispatch_payload.get("run", ""),
        "run_id": dispatch_payload.get("run_id", ""),
    }

    if getattr(args, "wait_for_completion", True):
        deadline = time.monotonic() + max(int(getattr(args, "wait_timeout_seconds", 420) or 420), 1)
        status_target = str(dispatch_payload.get("run_id", "") or "last")
        while True:
            status_payload = _run_control_layer_cli(repo_root, "status", status_target)
            final_status_payload = status_payload
            resolved_run_id = str(status_payload.get("run_id", "")).strip()
            if resolved_run_id:
                status_target = resolved_run_id
            if is_terminal_status(status_payload):
                break
            if time.monotonic() >= deadline:
                run_url = status_payload.get("run", "") or dispatch_payload.get("run", "")
                raise RuntimeError(
                    "queue-execute timed out before the GitHub workflow reached a terminal state."
                    + (f" run={run_url}" if run_url else "")
                )
            time.sleep(max(float(getattr(args, "status_poll_seconds", 3.0) or 3.0), 0.5))

    refreshed_row = _refresh_queue_row(cfg, row, fresh_since=accepted_at)
    if (
        getattr(args, "wait_for_completion", True)
        and (has_structured_failure(final_status_payload) or not is_successful_status(final_status_payload))
        and refreshed_row.result_is_fresh is not True
    ):
        raise RuntimeError(
            build_queue_execute_failure_message(
                row=refreshed_row,
                status_payload=final_status_payload,
                dispatch_payload=dispatch_payload,
            )
        )
    print(
        render_queue_execute_result(
            refreshed_row,
            as_json=bool(getattr(resolved_args, "json", False)),
            dispatch_payload=dispatch_payload,
            accepted_at=accepted_at,
        )
    )


if __name__ == "__main__":
    raise SystemExit("Use `python build.py queue-execute ...`.")
