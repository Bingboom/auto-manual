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
from tools.listen_build_queue import (  # noqa: E402
    EVENT_TYPE,
    MAX_SEEN_EVENT_IDS,
    BuildQueueWorker,
    _stderr_pump,
    build_event_subscribe_command,
    ensure_drive_event_subscription,
    event_requests_immediate_build,
    fetch_field_id_map,
)
from tools.listen_sync_data import (  # noqa: E402
    SyncDataWorker,
    event_requests_sync,
    resolve_watched_tables,
    watched_table_lookup,
)
from tools.process_build_queue import (  # noqa: E402
    IMMEDIATE_TRIGGER_FIELD,
    collect_queue_preflight_errors,
    resolve_document_link_binding,
)
from tools.sync_data import (  # noqa: E402
    _cli_bin,
    _selected_tables,
    collect_sync_preflight_errors,
    load_config,
)


def listen_phase2_events(
    *,
    cfg: dict[str, Any],
    config_path: Path,
    data_root: str,
    table_names: list[str] | tuple[str, ...] | None = None,
) -> int:
    selected_tables = _selected_tables(list(table_names or []))
    sync_errors = collect_sync_preflight_errors(cfg, table_names=selected_tables)
    queue_errors = collect_queue_preflight_errors(cfg)
    errors = []
    if sync_errors:
        errors.extend(sync_errors)
    if queue_errors:
        errors.extend(queue_errors)
    if errors:
        raise RuntimeError("listen-phase2-events preflight failed:\n- " + "\n- ".join(errors))

    cli_bin = _cli_bin(cfg)
    sync_watched_tables = resolve_watched_tables(cfg, table_names=selected_tables)
    sync_watched_by_base = watched_table_lookup(sync_watched_tables)

    queue_binding = resolve_document_link_binding(cfg)
    field_id_map = fetch_field_id_map(
        cli_bin=cli_bin,
        base_token=queue_binding.base_token,
        table_id=queue_binding.table_id,
    )
    immediate_field_id = field_id_map.get(IMMEDIATE_TRIGGER_FIELD, "").strip()
    if not immediate_field_id:
        raise RuntimeError(
            f"Document_link table is missing the required checkbox field: {IMMEDIATE_TRIGGER_FIELD}"
        )

    base_tokens = set(sync_watched_by_base)
    base_tokens.add(queue_binding.base_token)
    for base_token in base_tokens:
        ensure_drive_event_subscription(cli_bin=cli_bin, base_token=base_token)

    sync_worker = SyncDataWorker(cfg=cfg, config_path=config_path, data_root=data_root)
    queue_worker = BuildQueueWorker(cfg=cfg, config_path=config_path, data_root=data_root)

    cmd = build_event_subscribe_command(cli_bin=cli_bin)
    sync_summary = [
        {"logical_name": table.logical_name, "table_id": table.table_id}
        for table in sync_watched_tables
    ]
    queue_summary = {
        "table_id": queue_binding.table_id,
        "immediate_field_id": immediate_field_id,
    }
    print("[phase2-event-listener] Sync watch " + json.dumps(sync_summary, ensure_ascii=False))
    print("[phase2-event-listener] Queue watch " + json.dumps(queue_summary, ensure_ascii=False))
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
                print(f"[phase2-event-listener] Ignoring non-JSON event line: {line}", file=sys.stderr)
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

            matched_table = event_requests_sync(payload, watched_tables_by_base=sync_watched_by_base)
            if matched_table:
                sync_worker.trigger(reason=f"{matched_table}:{event_id or 'bitable_record_changed'}")

            if event_requests_immediate_build(
                payload,
                base_token=queue_binding.base_token,
                table_id=queue_binding.table_id,
                immediate_field_id=immediate_field_id,
            ):
                queue_worker.trigger(reason=event_id or "bitable_record_changed")
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
        description="Listen for phase2 source-table changes and build-queue checkbox events on one Feishu event stream."
    )
    ap.add_argument("--config", required=True, help="Config YAML path")
    ap.add_argument("--data-root", default=None, help="Override structured content snapshot root")
    ap.add_argument(
        "--table",
        action="append",
        default=[],
        help="Optional logical phase2 source table to watch; defaults to all synced content tables",
    )
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
        return listen_phase2_events(
            cfg=cfg,
            config_path=config_path,
            data_root=resolved_data_root,
            table_names=args.table,
        )
    except RuntimeError as exc:
        print(f"[phase2-event-listener] ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
