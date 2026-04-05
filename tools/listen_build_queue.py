#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.data_snapshot import resolve_phase2_export_root  # noqa: E402
from tools.listen_build_queue_events import (  # noqa: E402
    event_field_value_truthy as _event_field_value_truthy_impl,
    event_requests_immediate_build as _event_requests_immediate_build_impl,
)
from tools.listen_build_queue_lark import (  # noqa: E402
    build_event_subscribe_command as _build_event_subscribe_command_impl,
    ensure_drive_event_subscription as _ensure_drive_event_subscription_impl,
    fetch_field_id_map as _fetch_field_id_map_impl,
    format_command as _format_command_impl,
    run_lark_cli_json as _run_lark_cli_json_impl,
    stderr_pump as _stderr_pump_impl,
)
from tools.listen_build_queue_runtime import (  # noqa: E402
    BuildQueueWorker as _BuildQueueWorkerImpl,
    listen_for_build_queue_events as _listen_for_build_queue_events_impl,
)
from tools.process_build_queue import (  # noqa: E402
    IMMEDIATE_TRIGGER_FIELD,
    collect_queue_preflight_errors,
    process_build_queue,
    resolve_document_link_binding,
)
from tools.phase2_support import (  # noqa: E402
    cli_bin as _cli_bin,
    load_config,
    parse_json_payload as _parse_json_payload,
    resolved_cli_command_parts as _resolved_cli_command_parts,
)

EVENT_TYPE = "drive.file.bitable_record_changed_v1"
FILE_TYPE = "bitable"
MAX_SEEN_EVENT_IDS = 256
EVENT_SUBSCRIPTION_IDENTITY = "user"


def _format_command(cmd: list[str]) -> str:
    return _format_command_impl(cmd)


def _run_lark_cli_json(*, cli_bin: str, args: list[str]) -> dict[str, Any]:
    return _run_lark_cli_json_impl(
        cli_bin=cli_bin,
        args=args,
        repo_root=ROOT,
        resolved_cli_command_parts=_resolved_cli_command_parts,
        parse_json_payload=_parse_json_payload,
    )


def build_event_subscribe_command(*, cli_bin: str) -> list[str]:
    return _build_event_subscribe_command_impl(
        cli_bin=cli_bin,
        resolved_cli_command_parts=_resolved_cli_command_parts,
        event_subscription_identity=EVENT_SUBSCRIPTION_IDENTITY,
        event_type=EVENT_TYPE,
    )


def ensure_drive_event_subscription(*, cli_bin: str, base_token: str) -> None:
    _ensure_drive_event_subscription_impl(
        cli_bin=cli_bin,
        base_token=base_token,
        run_lark_cli_json=_run_lark_cli_json,
        file_type=FILE_TYPE,
        event_subscription_identity=EVENT_SUBSCRIPTION_IDENTITY,
    )


def fetch_field_id_map(*, cli_bin: str, base_token: str, table_id: str) -> dict[str, str]:
    return _fetch_field_id_map_impl(
        cli_bin=cli_bin,
        base_token=base_token,
        table_id=table_id,
        run_lark_cli_json=_run_lark_cli_json,
    )


def _event_field_value_truthy(value: Any) -> bool:
    return _event_field_value_truthy_impl(value)


def event_requests_immediate_build(
    payload: dict[str, Any],
    *,
    base_token: str,
    table_id: str,
    immediate_field_id: str,
) -> bool:
    return _event_requests_immediate_build_impl(
        payload,
        event_type=EVENT_TYPE,
        file_type=FILE_TYPE,
        base_token=base_token,
        table_id=table_id,
        immediate_field_id=immediate_field_id,
        event_field_value_truthy=_event_field_value_truthy,
    )


class BuildQueueWorker:
    def __new__(cls, *, cfg: dict[str, Any], config_path: Path, data_root: str) -> _BuildQueueWorkerImpl:
        return _BuildQueueWorkerImpl(
            cfg=cfg,
            config_path=config_path,
            data_root=data_root,
            process_build_queue=process_build_queue,
            stderr=sys.stderr,
        )


def _stderr_pump(stream: Any) -> None:
    _stderr_pump_impl(stream, stderr=sys.stderr)


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

    return _listen_for_build_queue_events_impl(
        repo_root=ROOT,
        subscribe_command=build_event_subscribe_command(cli_bin=cli_bin),
        base_token=binding.base_token,
        table_id=binding.table_id,
        immediate_field_id=immediate_field_id,
        event_type=EVENT_TYPE,
        max_seen_event_ids=MAX_SEEN_EVENT_IDS,
        worker=worker,
        event_requests_immediate_build=event_requests_immediate_build,
        stderr_pump=_stderr_pump,
        stderr=sys.stderr,
    )


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
