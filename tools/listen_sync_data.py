#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.data_snapshot import resolve_phase2_export_root  # noqa: E402
from tools.listen_build_queue import (  # noqa: E402
    EVENT_TYPE,
    FILE_TYPE,
    MAX_SEEN_EVENT_IDS,
    _stderr_pump,
    build_event_subscribe_command,
    ensure_drive_event_subscription,
)
from tools.sync_data import (  # noqa: E402
    _cli_bin,
    _selected_tables,
    collect_sync_preflight_errors,
    load_config,
    resolve_table_binding,
    sync_phase2_snapshot,
)


@dataclass(frozen=True)
class WatchedTable:
    logical_name: str
    base_token: str
    table_id: str


def resolve_watched_tables(
    cfg: dict[str, Any],
    *,
    table_names: list[str] | tuple[str, ...] | None = None,
) -> tuple[WatchedTable, ...]:
    selected_tables = _selected_tables(list(table_names or []))
    watched: list[WatchedTable] = []
    for logical_name in selected_tables:
        binding = resolve_table_binding(cfg, logical_name)
        watched.append(
            WatchedTable(
                logical_name=logical_name,
                base_token=binding.base_token,
                table_id=binding.table_id,
            )
        )
    return tuple(watched)


def watched_table_lookup(
    watched_tables: tuple[WatchedTable, ...],
) -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    for table in watched_tables:
        per_base = lookup.setdefault(table.base_token, {})
        per_base[table.table_id] = table.logical_name
    return lookup


def event_requests_sync(
    payload: dict[str, Any],
    *,
    watched_tables_by_base: dict[str, dict[str, str]],
) -> str | None:
    header = payload.get("header")
    event = payload.get("event")
    if not isinstance(header, dict) or not isinstance(event, dict):
        return None
    if str(header.get("event_type") or "").strip() != EVENT_TYPE:
        return None
    if str(event.get("file_type") or "").strip() != FILE_TYPE:
        return None
    base_token = str(event.get("file_token") or "").strip()
    if not base_token:
        return None
    tables_for_base = watched_tables_by_base.get(base_token)
    if not tables_for_base:
        return None
    table_id = str(event.get("table_id") or "").strip()
    logical_name = tables_for_base.get(table_id)
    if not logical_name:
        return None
    action_list = event.get("action_list", [])
    if not isinstance(action_list, list):
        return None
    for action in action_list:
        if not isinstance(action, dict):
            continue
        action_name = str(action.get("action") or "").strip()
        if action_name in {"record_added", "record_edited", "record_deleted"}:
            return logical_name
    return None


class SyncDataWorker:
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
                print(f"[sync-data-listener] Coalesced trigger while sync is running: {reason}")
                return
            self._running = True
        print(f"[sync-data-listener] Triggered sync-data: {reason}")
        thread = threading.Thread(target=self._run_loop, daemon=True)
        thread.start()

    def _run_loop(self) -> None:
        while True:
            try:
                result = sync_phase2_snapshot(
                    cfg=self.cfg,
                    config_path=self.config_path,
                    data_root=self.data_root,
                    dry_run=False,
                )
                changed = [
                    item.logical_name
                    for item in (*result.synced_tables, *result.derived_files)
                    if item.changed
                ]
                print(
                    "[sync-data-listener] Sync finished "
                    + json.dumps(
                        {
                            "changed": changed,
                            "export_root": str(result.export_root),
                            "manifest": str(result.manifest_path),
                        },
                        ensure_ascii=False,
                    )
                )
            except Exception as exc:
                print(f"[sync-data-listener] Sync failed: {exc}", file=sys.stderr)

            with self._lock:
                if self._pending:
                    self._pending = False
                    continue
                self._running = False
                return


def listen_sync_data(
    *,
    cfg: dict[str, Any],
    config_path: Path,
    data_root: str,
    table_names: list[str] | tuple[str, ...] | None = None,
) -> int:
    selected_tables = _selected_tables(list(table_names or []))
    errors = collect_sync_preflight_errors(cfg, table_names=selected_tables)
    if errors:
        raise RuntimeError("listen-sync-data preflight failed:\n- " + "\n- ".join(errors))

    cli_bin = _cli_bin(cfg)
    watched_tables = resolve_watched_tables(cfg, table_names=selected_tables)
    watched_by_base = watched_table_lookup(watched_tables)
    for base_token in watched_by_base:
        ensure_drive_event_subscription(cli_bin=cli_bin, base_token=base_token)

    worker = SyncDataWorker(cfg=cfg, config_path=config_path, data_root=data_root)
    cmd = build_event_subscribe_command(cli_bin=cli_bin)
    watched_summary = [
        {"logical_name": table.logical_name, "table_id": table.table_id}
        for table in watched_tables
    ]
    print("[sync-data-listener] Watching " + json.dumps(watched_summary, ensure_ascii=False))
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
                print(f"[sync-data-listener] Ignoring non-JSON event line: {line}", file=sys.stderr)
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

            matched_table = event_requests_sync(payload, watched_tables_by_base=watched_by_base)
            if matched_table:
                worker.trigger(reason=f"{matched_table}:{event_id or 'bitable_record_changed'}")
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
        description="Listen for phase2 source-table change events and trigger local sync-data runs."
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
        return listen_sync_data(
            cfg=cfg,
            config_path=config_path,
            data_root=resolved_data_root,
            table_names=args.table,
        )
    except RuntimeError as exc:
        print(f"[sync-data-listener] ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
