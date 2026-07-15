from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable


def format_command(cmd: list[str]) -> str:
    return subprocess.list2cmdline([str(part) for part in cmd])


def run_lark_cli_json(
    *,
    cli_bin: str,
    args: list[str],
    repo_root: Path,
    resolved_cli_command_parts: Callable[[str], list[str]],
    parse_json_payload: Callable[[str], dict[str, Any]],
) -> dict[str, Any]:
    cmd = [*resolved_cli_command_parts(cli_bin), *args]
    proc = subprocess.run(
        cmd,
        cwd=str(repo_root),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode:
        stderr = (proc.stderr or "").strip()
        stdout = (proc.stdout or "").strip()
        message = stderr or stdout or f"command failed: {format_command(cmd)}"
        raise RuntimeError(message)
    payload = parse_json_payload(proc.stdout or proc.stderr or "")
    code = payload.get("code")
    if code not in (None, 0):
        message = str(payload.get("msg") or payload.get("message") or "Lark CLI API request failed")
        raise RuntimeError(f"Lark CLI API request failed: {message}")
    return payload


def build_event_subscribe_command(
    *,
    cli_bin: str,
    resolved_cli_command_parts: Callable[[str], list[str]],
    event_subscription_identity: str,
    event_type: str,
) -> list[str]:
    return [
        *resolved_cli_command_parts(cli_bin),
        "event",
        "+subscribe",
        "--as",
        event_subscription_identity,
        "--event-types",
        event_type,
        "--quiet",
    ]


def ensure_drive_event_subscription(
    *,
    cli_bin: str,
    base_token: str,
    run_lark_cli_json: Callable[..., dict[str, Any]],
    file_type: str,
    event_subscription_identity: str,
) -> None:
    run_lark_cli_json(
        cli_bin=cli_bin,
        args=[
            "api",
            "POST",
            f"/open-apis/drive/v1/files/{base_token}/subscribe",
            "--params",
            json.dumps({"file_type": file_type}, ensure_ascii=False, separators=(",", ":")),
            "--as",
            event_subscription_identity,
        ],
    )


def fetch_field_id_map(
    *,
    cli_bin: str,
    base_token: str,
    table_id: str,
    identity: str = "user",
    run_lark_cli_json: Callable[..., dict[str, Any]],
) -> dict[str, str]:
    result: dict[str, str] = {}
    offset = 0
    limit = 200  # lark-cli >=1.0.69 caps --limit at 200
    while True:
        payload = run_lark_cli_json(
            cli_bin=cli_bin,
            args=[
                "base",
                "+field-list",
                "--as",
                identity,
                "--base-token",
                base_token,
                "--table-id",
                table_id,
                "--format",
                "json",
                "--limit",
                str(limit),
                "--offset",
                str(offset),
            ],
        )
        data = payload.get("data")
        if not isinstance(data, dict):
            raise RuntimeError("Lark CLI field list response is missing data payload")
        items = data.get("items", [])
        if not isinstance(items, list):
            raise RuntimeError("Lark CLI field list response has invalid items payload")
        for item in items:
            if not isinstance(item, dict):
                continue
            field_id = str(item.get("field_id") or "").strip()
            field_name = str(item.get("field_name") or "").strip()
            if field_id and field_name:
                result[field_name] = field_id
        total = int(data.get("total") or len(result))
        offset += len(items)
        if not items or offset >= total:
            break
    return result


def stderr_pump(stream: Any, *, stderr: Any = sys.stderr) -> None:
    if stream is None:
        return
    for raw_line in stream:
        line = str(raw_line).rstrip()
        if line:
            print(f"[build-queue-listener] {line}", file=stderr)
