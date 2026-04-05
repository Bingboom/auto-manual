from __future__ import annotations

import json
import subprocess
import threading
from collections import deque
from pathlib import Path
from typing import Any, Callable


class BuildQueueWorker:
    def __init__(
        self,
        *,
        cfg: dict[str, Any],
        config_path: Path,
        data_root: str,
        process_build_queue: Callable[..., int],
        stderr: Any,
    ) -> None:
        self.cfg = cfg
        self.config_path = config_path
        self.data_root = data_root
        self._process_build_queue = process_build_queue
        self._stderr = stderr
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
                exit_code = self._process_build_queue(
                    cfg=self.cfg,
                    config_path=self.config_path,
                    data_root=self.data_root,
                    dry_run=False,
                )
                if exit_code:
                    print(f"[build-queue-listener] Queue run finished with exit_code={exit_code}", file=self._stderr)
            except Exception as exc:
                print(f"[build-queue-listener] Queue run failed: {exc}", file=self._stderr)

            with self._lock:
                if self._pending:
                    self._pending = False
                    continue
                self._running = False
                return


def listen_for_build_queue_events(
    *,
    repo_root: Path,
    subscribe_command: list[str],
    base_token: str,
    table_id: str,
    immediate_field_id: str,
    event_type: str,
    max_seen_event_ids: int,
    worker: BuildQueueWorker,
    event_requests_immediate_build: Callable[..., bool],
    stderr_pump: Callable[[Any], None],
    stderr: Any,
) -> int:
    print(f"[build-queue-listener] Listening for {event_type} on base={base_token} table={table_id}")
    proc = subprocess.Popen(
        subscribe_command,
        cwd=str(repo_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )
    stderr_thread = threading.Thread(target=stderr_pump, args=(proc.stderr,), daemon=True)
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
                print(f"[build-queue-listener] Ignoring non-JSON event line: {line}", file=stderr)
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
                if len(seen_queue) > max_seen_event_ids:
                    seen_ids.discard(seen_queue.popleft())

            if event_requests_immediate_build(
                payload,
                base_token=base_token,
                table_id=table_id,
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
