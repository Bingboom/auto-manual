#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
from collections import deque
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.data_snapshot import resolve_phase2_export_root  # noqa: E402
from tools.process_build_queue import (  # noqa: E402
    IMMEDIATE_TRIGGER_FIELD,
    collect_queue_preflight_errors,
    process_build_queue,
    resolve_document_link_binding,
)
from tools.sync_data import (  # noqa: E402
    _cli_bin,
    _parse_json_payload,
    _resolved_cli_command_parts,
    load_config,
)

EVENT_TYPE = "drive.file.bitable_record_changed_v1"
FILE_TYPE = "bitable"
MAX_SEEN_EVENT_IDS = 256
EVENT_SUBSCRIPTION_IDENTITY = "user"


def _format_command(cmd: list[str]) -> str:
    return subprocess.list2cmdline([str(part) for part in cmd])


def _run_lark_cli_json(*, cli_bin: str, args: list[str]) -> dict[str, Any]:
    cmd = [*_resolved_cli_command_parts(cli_bin), *args]
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode:
        stderr = (proc.stderr or "").strip()
        stdout = (proc.stdout or "").strip()
        message = stderr or stdout or f"command failed: {_format_command(cmd)}"
        raise RuntimeError(message)
    payload = _parse_json_payload(proc.stdout or proc.stderr or "")
    code = payload.get("code")
    if code not in (None, 0):
        message = str(payload.get("msg") or payload.get("message") or "Lark CLI API request failed")
        raise RuntimeError(f"Lark CLI API request failed: {message}")
    return payload


def build_event_subscribe_command(*, cli_bin: str) -> list[str]:
    return [
        *_resolved_cli_command_parts(cli_bin),
        "event",
        "+subscribe",
        "--as",
        EVENT_SUBSCRIPTION_IDENTITY,
        "--event-types",
        EVENT_TYPE,
        "--quiet",
    ]


def ensure_drive_event_subscription(*, cli_bin: str, base_token: str) -> None:
    _run_lark_cli_json(
        cli_bin=cli_bin,
        args=[
            "api",
            "POST",
            f"/open-apis/drive/v1/files/{base_token}/subscribe",
            "--params",
            json.dumps({"file_type": FILE_TYPE}, ensure_ascii=False, separators=(",", ":")),
            "--as",
            "user",
        ],
    )


def fetch_field_id_map(*, cli_bin: str, base_token: str, table_id: str) -> dict[str, str]:
    payload = _run_lark_cli_json(
        cli_bin=cli_bin,
        args=[
            "base",
            "+field-list",
            "--as",
            "user",
            "--base-token",
            base_token,
            "--table-id",
            table_id,
            "--limit",
            "500",
        ],
    )
    data = payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("Lark CLI field list response is missing data payload")
    items = data.get("items", [])
    if not isinstance(items, list):
        raise RuntimeError("Lark CLI field list response has invalid items payload")
    result: dict[str, str] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        field_id = str(item.get("field_id") or "").strip()
        field_name = str(item.get("field_name") or "").strip()
        if field_id and field_name:
            result[field_name] = field_id
    return result


def _event_field_value_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip()
    if not text:
        return False
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = text
    if isinstance(parsed, bool):
        return parsed
    if isinstance(parsed, (int, float)):
        return bool(parsed)
    return str(parsed).strip().lower() in {"1", "true", "y", "yes", "checked"}


def event_requests_immediate_build(
    payload: dict[str, Any],
    *,
    base_token: str,
    table_id: str,
    immediate_field_id: str,
) -> bool:
    header = payload.get("header")
    event = payload.get("event")
    if not isinstance(header, dict) or not isinstance(event, dict):
        return False
    if str(header.get("event_type") or "").strip() != EVENT_TYPE:
        return False
    if str(event.get("file_token") or "").strip() != base_token:
        return False
    if str(event.get("file_type") or "").strip() != FILE_TYPE:
        return False
    if str(event.get("table_id") or "").strip() != table_id:
        return False

    action_list = event.get("action_list", [])
    if not isinstance(action_list, list):
        return False
    for action in action_list:
        if not isinstance(action, dict):
            continue
        action_name = str(action.get("action") or "").strip()
        if action_name not in {"record_added", "record_edited"}:
            continue
        after_value = action.get("after_value", [])
        if not isinstance(after_value, list):
            continue
        for field_change in after_value:
            if not isinstance(field_change, dict):
                continue
            if str(field_change.get("field_id") or "").strip() != immediate_field_id:
                continue
            if _event_field_value_truthy(field_change.get("field_value")):
                return True
    return False


class BuildQueueWorker:
    def __init__(self, *, cfg: dict[str, Any], config_path: Path, data_root: str) -> None:
        self.cfg = cfg
        self.config_path = config_path
        self.data_root = data_root
        self._lock = threading.Lock()
        self._running = False
        self._pending = False

    def trigger(self, *, reason: str) -> None:
        with self._lock:
            if self._running:
                self._pending = True
                print(f"[build-queue-listener] Coalesced trigger while build is running: {reason}")
                return
            self._running = True
        print(f"[build-queue-listener] Triggered build queue: {reason}")
        thread = threading.Thread(target=self._run_loop, daemon=True)
        thread.start()

    def _run_loop(self) -> None:
        while True:
            try:
                exit_code = process_build_queue(
                    cfg=self.cfg,
                    config_path=self.config_path,
                    data_root=self.data_root,
                    dry_run=False,
                )
                if exit_code:
                    print(f"[build-queue-listener] Queue run finished with exit_code={exit_code}", file=sys.stderr)
            except Exception as exc:
                print(f"[build-queue-listener] Queue run failed: {exc}", file=sys.stderr)

            with self._lock:
                if self._pending:
                    self._pending = False
                    continue
                self._running = False
                return


def _stderr_pump(stream: Any) -> None:
    if stream is None:
        return
    for raw_line in stream:
        line = str(raw_line).rstrip()
        if line:
            print(f"[build-queue-listener] {line}", file=sys.stderr)


def listen_build_queue(
    *,
    cfg: dict[str, Any],
    config_path: Path,
    data_root: str,
) -> int:
    errors = collect_queue_preflight_errors(cfg)
    if errors:
        raise RuntimeError("listen-build-queue preflight failed:\n- " + "\n- ".join(errors))

    binding = resolve_document_link_binding(cfg)
    cli_bin = _cli_bin(cfg)
    field_id_map = fetch_field_id_map(cli_bin=cli_bin, base_token=binding.base_token, table_id=binding.table_id)
    immediate_field_id = field_id_map.get(IMMEDIATE_TRIGGER_FIELD, "").strip()
    if not immediate_field_id:
        raise RuntimeError(
            f"Document_link table is missing the required checkbox field: {IMMEDIATE_TRIGGER_FIELD}"
        )

    ensure_drive_event_subscription(cli_bin=cli_bin, base_token=binding.base_token)
    worker = BuildQueueWorker(cfg=cfg, config_path=config_path, data_root=data_root)

    cmd = build_event_subscribe_command(cli_bin=cli_bin)
    print(f"[build-queue-listener] Listening for {EVENT_TYPE} on base={binding.base_token} table={binding.table_id}")
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )
    stderr_thread = threading.Thread(target=_stderr_pump, args=(proc.stderr,), daemon=True)
    stderr_thread.start()

    seen_ids: set[str] = set()
    seen_queue: deque[str] = deque()
    try:
        assert proc.stdout is not None
        for raw_line in proc.stdout:
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                print(f"[build-queue-listener] Ignoring non-JSON event line: {line}", file=sys.stderr)
                continue
            if not isinstance(payload, dict):
                continue
            header = payload.get("header")
            event_id = str(header.get("event_id") or "").strip() if isinstance(header, dict) else ""
            if event_id:
                if event_id in seen_ids:
                    continue
                seen_ids.add(event_id)
                seen_queue.append(event_id)
                if len(seen_queue) > MAX_SEEN_EVENT_IDS:
                    seen_ids.discard(seen_queue.popleft())

            if event_requests_immediate_build(
                payload,
                base_token=binding.base_token,
                table_id=binding.table_id,
                immediate_field_id=immediate_field_id,
            ):
                worker.trigger(reason=event_id or "bitable_record_changed")
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
    return proc.returncode or 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Listen for immediate Document_link checkbox events and trigger build queue runs."
    )
    ap.add_argument("--config", required=True, help="Config YAML path")
    ap.add_argument("--data-root", default=None, help="Override structured content snapshot root")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = ROOT / config_path
    cfg = load_config(config_path)
    resolved_data_root = str(
        resolve_phase2_export_root(
            cfg,
            repo_root=ROOT,
            data_root=args.data_root,
        )
    )
    try:
        return listen_build_queue(
            cfg=cfg,
            config_path=config_path,
            data_root=resolved_data_root,
        )
    except RuntimeError as exc:
        print(f"[build-queue-listener] ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
