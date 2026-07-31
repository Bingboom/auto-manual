"""Shared lark-cli transport boundary for queue operations and F6 / F8.

Queue, listener, spec-master, and schema callers use :func:`run_lark_cli_json`
for the subprocess and Feishu response boundary. F6 / F8 transports continue to
wrap the proven `tools/sync_data.LarkCliSource` record primitives.

Construct an F6 transport with a live `LarkCliSource`, e.g.::

    from tools.sync_data import LarkCliSource
    source = LarkCliSource(cli_bin="lark-cli", identity="bot")
    f6 = SourceTableLarkTransport(source=source, binding_for=lambda t: (BASE, TABLE_IDS[t]))
    apply_change_requests(reqs, approved_hashes=approved, transport=f6, write=True)

F6 `upsert`/`get` use `+record-upsert` / `+record-list`; F8 `append_row` uses
`+record-batch-create` (`create_record`) and `list_finding_hashes` uses
`+record-list`. Retry/backoff, pagination, and snapshot locking remain separate
K8 slices.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol


def _default_command_failure_message(
    cmd: list[str], stdout: str, stderr: str, returncode: int,
    format_command: Callable[[list[str]], str] | None = None,
) -> str:
    details = []
    if stdout:
        details.append(f"stdout={stdout.strip()}")
    if stderr:
        details.append(f"stderr={stderr.strip()}")
    suffix = "; " + "; ".join(details) if details else ""
    command_text = format_command(cmd) if format_command is not None else " ".join(cmd)
    return f"Lark CLI command failed with exit code {returncode}: {command_text}{suffix}"


def run_lark_cli_json(
    *,
    cli_bin: str,
    args: list[str],
    repo_root: Path,
    resolved_cli_command_parts: Callable[[str], list[str]],
    parse_json_payload: Callable[[str], dict[str, Any]],
    format_command: Callable[[list[str]], str] | None = None,
    command_failure_message: Callable[[list[str], str, str, int], str] | None = None,
    on_command: Callable[[list[str]], None] | None = None,
    environment: Mapping[str, str] | None = None,
    parse_process_output: Callable[[str, str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run one lark-cli JSON command for queue and listener callers.

    Callers retain dependency injection for tests, command formatting, environment
    routing, and dual-stream parsing, but subprocess execution and common Feishu
    response validation live in this module.
    Retry/backoff and pagination remain separate K8 slices.
    """
    cmd = [*resolved_cli_command_parts(cli_bin), *args]
    if on_command is not None:
        on_command(cmd)
    elif format_command is not None:
        print(f"[build-queue] {format_command(cmd)}")
    run_kwargs: dict[str, Any] = {
        "cwd": str(repo_root),
        "check": False,
        "capture_output": True,
        "text": True,
        "encoding": "utf-8",
    }
    if environment is not None:
        run_kwargs["env"] = dict(environment)
    process = subprocess.run(cmd, **run_kwargs)
    if process.returncode:
        if command_failure_message is not None:
            message = command_failure_message(cmd, process.stdout or "", process.stderr or "", process.returncode)
        else:
            message = _default_command_failure_message(
                cmd, process.stdout or "", process.stderr or "", process.returncode, format_command
            )
        raise RuntimeError(message)
    if parse_process_output is not None:
        payload = parse_process_output(process.stdout or "", process.stderr or "")
    else:
        payload = parse_json_payload(process.stdout or process.stderr or "")
    code = payload.get("code")
    if code not in (None, 0):
        message = str(payload.get("msg") or payload.get("message") or "Lark CLI API request failed")
        raise RuntimeError(f"Lark CLI API request failed: {message}")
    return payload


def _as_cell(value: Any) -> str:
    """Coerce a row value to a text cell: dict/list -> JSON string, None -> ''."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


class _RecordSource(Protocol):
    def upsert_record(self, *, base_token: str, table_id: str, record_id: str, record: dict[str, Any]) -> Any: ...
    def fetch_records_with_ids(self, *, base_token: str, table_id: str, view_id: str | None) -> list[dict[str, Any]]: ...
    def create_record(self, *, base_token: str, table_id: str, fields: dict[str, Any]) -> str: ...


class SourceTableLarkTransport:
    """F6 transport: satisfies `source_table_sync._Transport` (`upsert` + `get`).

    Routes each call's `table` to a `(base_token, table_id)` via `binding_for`
    (the operator supplies the resolver, e.g. from the phase2 config bindings).
    """

    def __init__(self, *, source: _RecordSource, binding_for: Callable[[str], tuple[str, str]]) -> None:
        self._source = source
        self._binding_for = binding_for

    def upsert(self, *, table: str, record_id: str, field: str, value: Any) -> None:
        base_token, table_id = self._binding_for(table)
        self._source.upsert_record(
            base_token=base_token, table_id=table_id, record_id=record_id, record={field: value}
        )

    def get(self, *, table: str, record_id: str, field: str) -> Any:
        base_token, table_id = self._binding_for(table)
        for record in self._source.fetch_records_with_ids(base_token=base_token, table_id=table_id, view_id=None):
            if record.get("record_id") == record_id:
                return (record.get("fields") or {}).get(field)
        return None


class QcReportLarkTransport:
    """F8 transport: satisfies `qc_report._Transport` (`append_row` +
    `list_finding_hashes`) over the operator-created `QC_Report` table."""

    def __init__(
        self,
        *,
        source: _RecordSource,
        base_token: str,
        table_id: str,
        finding_hash_field: str = "finding_hash",
    ) -> None:
        self._source = source
        self._base_token = base_token
        self._table_id = table_id
        self._finding_hash_field = finding_hash_field

    def list_finding_hashes(self) -> set[str]:
        hashes: set[str] = set()
        for record in self._source.fetch_records_with_ids(
            base_token=self._base_token, table_id=self._table_id, view_id=None
        ):
            value = (record.get("fields") or {}).get(self._finding_hash_field)
            if value:
                hashes.add(str(value))
        return hashes

    def append_row(self, *, row: dict[str, Any]) -> str:
        # QC_Report fields are text; serialize dict/list (e.g. source_ref) to JSON.
        fields = {key: _as_cell(value) for key, value in row.items()}
        return self._source.create_record(
            base_token=self._base_token, table_id=self._table_id, fields=fields
        )


class TranslationMemoryLarkTransport:
    """TM transport: satisfies ``translation_memory_sync._TmTransport``
    (``list_records`` + ``write`` + ``get``) over the `Translation_Memory` table.

    Resolution (old translation -> record_id) lives in the executor, which reads
    ``list_records()`` and matches exact-or-abstain — so this stays a thin CRUD
    wrapper over the proven `LarkCliSource` record primitives.
    """

    def __init__(self, *, source: _RecordSource, base_token: str, table_id: str) -> None:
        self._source = source
        self._base_token = base_token
        self._table_id = table_id

    def list_records(self) -> list[dict[str, Any]]:
        return self._source.fetch_records_with_ids(
            base_token=self._base_token, table_id=self._table_id, view_id=None
        )

    def write(self, *, record_id: str, field: str, value: Any) -> None:
        self._source.upsert_record(
            base_token=self._base_token, table_id=self._table_id, record_id=record_id, record={field: _as_cell(value)}
        )

    def get(self, *, record_id: str, field: str) -> Any:
        for record in self.list_records():
            if record.get("record_id") == record_id:
                return (record.get("fields") or {}).get(field)
        return None
