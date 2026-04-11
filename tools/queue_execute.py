from __future__ import annotations

import argparse
import json
import subprocess
import time
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


def render_queue_execute_result(row: QueueQueryRow, *, as_json: bool) -> str:
    if as_json:
        return json.dumps(
            {
                "record_id": row.record_id,
                "git_ref": row.git_ref,
                "result": row.result,
                "document_link": row.document_link,
            },
            ensure_ascii=False,
            indent=2,
        )
    return "\n".join(
        [
            f"record_id: {_null_text(row.record_id)}",
            f"Git_ref: {_null_text(row.git_ref)}",
            f"构建结果: {_null_text(row.result)}",
            f"Document link: {_null_text(row.document_link)}",
        ]
    )


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


def _refresh_queue_row(cfg: dict[str, Any], row: QueueQueryRow) -> QueueQueryRow:
    refresh_args = argparse.Namespace(
        query_text=None,
        record_id=row.record_id,
        document_id=None,
        document_key=None,
        build_family=None,
        lang=None,
        document_version=None,
        query_workflow_action=None,
        git_ref_contains=None,
        result_contains=None,
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
    dispatch_command = dispatch_command_for_row(row)
    dispatch_payload = _run_control_layer_cli(repo_root, "dispatch", dispatch_command, row.record_id)
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

    refreshed_row = _refresh_queue_row(cfg, row)
    if (
        getattr(args, "wait_for_completion", True)
        and not is_successful_status(final_status_payload)
        and not refreshed_row.result
        and not refreshed_row.document_link
    ):
        run_url = final_status_payload.get("run", "") or dispatch_payload.get("run", "")
        run_id = final_status_payload.get("run_id", "") or dispatch_payload.get("run_id", "")
        conclusion = final_status_payload.get("conclusion", "") or final_status_payload.get("status", "unknown")
        raise RuntimeError(
            "queue-execute dispatched the workflow, but GitHub finished without Feishu writeback. "
            f"record_id={refreshed_row.record_id} conclusion={conclusion or 'unknown'}"
            + (f" run_id={run_id}" if run_id else "")
            + (f" run={run_url}" if run_url else "")
        )
    print(render_queue_execute_result(refreshed_row, as_json=bool(getattr(resolved_args, "json", False))))


if __name__ == "__main__":
    raise SystemExit("Use `python build.py queue-execute ...`.")
