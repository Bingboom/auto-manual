"""Live lark-cli transports for F6 / F8 (Milestone F activation enablers).

These wrap the proven `tools/sync_data.LarkCliSource` record primitives — the only
record verbs in-repo are `+record-upsert` and `+record-list` — so the operator can
plug a real transport into the source-table-sync (F6) and QC_Report (F8) executors
without re-writing lark-cli plumbing.

Construct with a live `LarkCliSource`, e.g.::

    from tools.sync_data import LarkCliSource
    source = LarkCliSource(cli_bin="lark-cli", identity="bot")
    f6 = SourceTableLarkTransport(source=source, binding_for=lambda t: (BASE, TABLE_IDS[t]))
    apply_change_requests(reqs, approved_hashes=approved, transport=f6, write=True)

All paths reuse `LarkCliSource` primitives: F6 `upsert`/`get` via `+record-upsert`
/ `+record-list`; F8 `append_row` via `+record-batch-create` (`create_record`) and
`list_finding_hashes` via `+record-list`. All verbs were verified live against the
test base on 2026-06-19.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Protocol


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
