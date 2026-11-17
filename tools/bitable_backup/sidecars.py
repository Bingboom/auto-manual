# -*- coding: utf-8 -*-
"""Structured attachment inventory, link sidecars, and two-pass link restore."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from tools import bitable_schema as bs

ATTACHMENTS_MANIFEST = "attachments_manifest.json"
LINKS_MANIFEST = "links_manifest.json"
ATTACHMENTS_SCHEMA_VERSION = "bitable-attachments-backup/v1"
LINKS_SCHEMA_VERSION = "bitable-links-backup/v1"
LINK_FIELD_TYPES = frozenset({"link", "one_way_link", "two_way_link"})
_KEY_PRIORITY_TYPES = ("text", "number", "select")


@dataclass(frozen=True)
class TableExportData:
    """In-memory snapshot of one exported Bitable table."""

    table_name: str
    table_id: str
    ftypes: dict[str, str]
    rows: list[dict[str, Any]]
    rids: list[str]


@dataclass(frozen=True)
class _LiveTable:
    """Live table records indexed by record_id for link resolution and readback."""

    table_id: str
    rows: list[dict[str, Any]]
    rids: list[str]
    row_by_rid: dict[str, dict[str, Any]]


def _primary_key_column(cols: list[str], ftypes: dict[str, str]) -> str:
    """Choose the table's primary business-key column (first text/simple column)."""
    for ftype in _KEY_PRIORITY_TYPES:
        for col in cols:
            if ftypes.get(col) == ftype:
                return col
    for col in cols:
        if ftypes.get(col) in bs.SIMPLE_TYPES:
            return col
    return cols[0] if cols else ""


def _ordered_key_columns(cols: list[str], ftypes: dict[str, str], default_pk: str) -> list[str]:
    """Order candidate primary-key columns for per-row non-empty fallback."""
    ordered: list[str] = [default_pk] if default_pk else []
    for ftype in _KEY_PRIORITY_TYPES:
        ordered.extend(col for col in cols if ftypes.get(col) == ftype and col not in ordered)
    ordered.extend(col for col in cols if ftypes.get(col) in bs.SIMPLE_TYPES and col not in ordered)
    return ordered


def _row_primary_key(row: dict[str, Any], ordered_cols: list[str], default_pk: str) -> tuple[str, str]:
    """Return ``(pk_field, pk_value)`` for one row using the first non-empty key column."""
    for col in ordered_cols:
        val = bs._norm_cell(row.get(col))
        if val:
            return col, val
    return default_pk, ""


def _parse_size(raw_size: Any) -> int | float | None:
    """Normalize an attachment byte size when present."""
    if isinstance(raw_size, (int, float)) and not isinstance(raw_size, bool):
        return raw_size
    if isinstance(raw_size, str) and raw_size.strip().isdigit():
        return int(raw_size.strip())
    return None


def _normalize_attachment_item(item: dict[str, Any]) -> dict[str, Any]:
    """Normalize one Feishu attachment dict into the manifest schema."""
    return {
        "file_token": str(item.get("file_token") or item.get("token") or "").strip(),
        "name": str(item.get("name") or item.get("file_name") or "").strip(),
        "size": _parse_size(item.get("size")),
        "type": str(item.get("type") or item.get("mime_type") or "").strip(),
    }


def normalize_attachments(raw: Any) -> list[dict[str, Any]]:
    """Normalize a raw Feishu attachment cell into a list of attachment dicts."""
    if raw is None or raw == "" or raw == [] or raw == {}:
        return []
    if isinstance(raw, dict):
        return [_normalize_attachment_item(raw)]
    if isinstance(raw, list):
        out: list[dict[str, Any]] = []
        for item in raw:
            if isinstance(item, dict):
                out.append(_normalize_attachment_item(item))
            elif isinstance(item, str) and item.strip():
                out.append({"file_token": item.strip(), "name": "", "size": None, "type": ""})
        return out
    return []


def _extract_ids_from_item(item: Any) -> list[str]:
    """Extract raw record IDs from one element of a Feishu link cell."""
    if isinstance(item, str):
        stripped = item.strip()
        return [stripped] if stripped else []
    if not isinstance(item, dict):
        return []
    out: list[str] = []
    for list_key in ("record_ids", "link_record_ids"):
        raw_list = item.get(list_key)
        if isinstance(raw_list, list):
            out.extend(str(rid).strip() for rid in raw_list if str(rid).strip())
    for single_key in ("record_id", "id"):
        raw_id = item.get(single_key)
        if raw_id is not None and str(raw_id).strip():
            out.append(str(raw_id).strip())
    return out


def normalize_link_record_ids(raw: Any) -> list[str]:
    """Normalize a raw Feishu link cell into an ordered, deduplicated list of record IDs."""
    if raw is None or raw == "" or raw == [] or raw == {}:
        return []
    candidates = raw if isinstance(raw, list) else [raw]
    seen: set[str] = set()
    ordered: list[str] = []
    for item in candidates:
        for rid in _extract_ids_from_item(item):
            if rid not in seen:
                seen.add(rid)
                ordered.append(rid)
    return ordered


def build_attachments_manifest(
    tables: list[TableExportData],
    label: str,
    generated_at: str,
) -> dict[str, Any]:
    """Build ``attachments_manifest.json`` payload from exported table snapshots."""
    entries: list[dict[str, Any]] = []
    for tbl in tables:
        cols = list(tbl.ftypes)
        att_cols = [col for col in cols if tbl.ftypes.get(col) == "attachment"]
        if not att_cols:
            continue
        default_pk = _primary_key_column(cols, tbl.ftypes)
        ordered_keys = _ordered_key_columns(cols, tbl.ftypes, default_pk)
        for row, rid in zip(tbl.rows, tbl.rids, strict=True):
            pk_field, pk_val = _row_primary_key(row, ordered_keys, default_pk)
            _append_row_attachment_entries(entries, tbl, rid, pk_field, pk_val, att_cols, row)
    total_attachments = sum(len(entry["attachments"]) for entry in entries)
    missing_token_count = sum(int(entry["missing_token_count"]) for entry in entries)
    return {
        "schema_version": ATTACHMENTS_SCHEMA_VERSION,
        "label": label,
        "generated_at": generated_at,
        "total_attachments": total_attachments,
        "missing_token_count": missing_token_count,
        "entries": entries,
    }


def _append_row_attachment_entries(
    entries: list[dict[str, Any]],
    tbl: TableExportData,
    rid: str,
    pk_field: str,
    pk_val: str,
    att_cols: list[str],
    row: dict[str, Any],
) -> None:
    """Append non-empty attachment cell records for a single row."""
    for col in att_cols:
        items = normalize_attachments(row.get(col))
        if not items:
            continue
        missing = sum(1 for item in items if not item["file_token"])
        entries.append(
            {
                "table": tbl.table_name,
                "table_id": tbl.table_id,
                "record_id": rid,
                "primary_key_field": pk_field,
                "primary_key_value": pk_val,
                "column": col,
                "attachments": items,
                "missing_token_count": missing,
            }
        )


def build_record_key_index(tables: list[TableExportData]) -> dict[str, tuple[str, str, str]]:
    """Map ``record_id -> (table_name, primary_key_field, primary_key_value)`` across tables."""
    index: dict[str, tuple[str, str, str]] = {}
    for tbl in tables:
        cols = list(tbl.ftypes)
        default_pk = _primary_key_column(cols, tbl.ftypes)
        ordered_keys = _ordered_key_columns(cols, tbl.ftypes, default_pk)
        for row, rid in zip(tbl.rows, tbl.rids, strict=True):
            pk_field, pk_val = _row_primary_key(row, ordered_keys, default_pk)
            index[rid] = (tbl.table_name, pk_field, pk_val)
    return index


def _resolve_target_ref(
    target_rid: str,
    record_index: dict[str, tuple[str, str, str]],
) -> dict[str, Any]:
    """Resolve one source target record_id to its business-key metadata when exported."""
    hit = record_index.get(target_rid)
    if hit is None:
        return {
            "target_table": None,
            "target_primary_field": None,
            "target_primary_value": None,
            "source_target_record_id": target_rid,
            "resolved": False,
        }
    target_table, target_field, target_value = hit
    return {
        "target_table": target_table,
        "target_primary_field": target_field,
        "target_primary_value": target_value,
        "source_target_record_id": target_rid,
        "resolved": bool(target_value),
    }


def build_links_manifest(
    tables: list[TableExportData],
    label: str,
    generated_at: str,
) -> dict[str, Any]:
    """Build ``links_manifest.json`` payload resolving link record_ids to business keys."""
    record_index = build_record_key_index(tables)
    entries: list[dict[str, Any]] = []
    for tbl in tables:
        cols = list(tbl.ftypes)
        link_cols = [col for col in cols if tbl.ftypes.get(col) in LINK_FIELD_TYPES]
        if not link_cols:
            continue
        default_pk = _primary_key_column(cols, tbl.ftypes)
        ordered_keys = _ordered_key_columns(cols, tbl.ftypes, default_pk)
        for row, rid in zip(tbl.rows, tbl.rids, strict=True):
            pk_field, pk_val = _row_primary_key(row, ordered_keys, default_pk)
            _append_row_link_entries(entries, tbl, rid, pk_field, pk_val, link_cols, row, record_index)
    resolved_targets = sum(1 for e in entries for t in e["targets"] if t.get("resolved"))
    unresolved_targets = sum(1 for e in entries for t in e["targets"] if not t.get("resolved"))
    return {
        "schema_version": LINKS_SCHEMA_VERSION,
        "label": label,
        "generated_at": generated_at,
        "total_link_cells": len(entries),
        "resolved_targets": resolved_targets,
        "unresolved_targets": unresolved_targets,
        "entries": entries,
    }


def _append_row_link_entries(
    entries: list[dict[str, Any]],
    tbl: TableExportData,
    rid: str,
    pk_field: str,
    pk_val: str,
    link_cols: list[str],
    row: dict[str, Any],
    record_index: dict[str, tuple[str, str, str]],
) -> None:
    """Append non-empty link cell entries for a single row."""
    for col in link_cols:
        target_rids = normalize_link_record_ids(row.get(col))
        if not target_rids:
            continue
        entries.append(
            {
                "table": tbl.table_name,
                "table_id": tbl.table_id,
                "record_id": rid,
                "primary_key_field": pk_field,
                "primary_key_value": pk_val,
                "column": col,
                "field_type": tbl.ftypes[col],
                "targets": [_resolve_target_ref(trid, record_index) for trid in target_rids],
            }
        )


def write_backup_sidecars(
    dest: Path,
    label: str,
    generated_at: str,
    tables: list[TableExportData],
    report: dict[str, Any],
) -> None:
    """Write attachment and link sidecar manifests and record them in ``report``."""
    att_manifest = build_attachments_manifest(tables, label, generated_at)
    (dest / ATTACHMENTS_MANIFEST).write_text(
        json.dumps(att_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    links_manifest = build_links_manifest(tables, label, generated_at)
    (dest / LINKS_MANIFEST).write_text(
        json.dumps(links_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report["attachments_manifest"] = ATTACHMENTS_MANIFEST
    report["total_attachments"] = att_manifest["total_attachments"]
    report["links_manifest"] = LINKS_MANIFEST


def load_attachment_expectations(backup_dir: Path) -> dict[str, Any] | None:
    """Load ``attachments_manifest.json`` if present, else ``None`` for legacy backups."""
    path = backup_dir / ATTACHMENTS_MANIFEST
    if not path.is_file():
        return None
    return dict(json.loads(path.read_text(encoding="utf-8")))


def apply_attachment_verification(
    row: dict[str, Any],
    att_manifest: dict[str, Any] | None,
    table_name: str,
    field_types: dict[str, str],
    live_rows: list[dict[str, Any]],
) -> None:
    """Verify live attachment counts and non-empty ``file_token``s against the sidecar."""
    if att_manifest is None:
        return
    entries = [e for e in att_manifest.get("entries", []) if e.get("table") == table_name]
    att_cols = sorted(
        {col for col, ftype in field_types.items() if ftype == "attachment"}
        | {str(e.get("column") or "") for e in entries if e.get("column")}
    )
    backup_attachments = sum(len(e.get("attachments") or []) for e in entries)
    live_attachments = 0
    live_missing_tokens = 0
    for live_row in live_rows:
        for col in att_cols:
            items = normalize_attachments(live_row.get(col))
            live_attachments += len(items)
            live_missing_tokens += sum(1 for item in items if not item["file_token"])
    attachments_match = (live_missing_tokens == 0) and (live_attachments >= backup_attachments)
    row["backup_attachments"] = backup_attachments
    row["live_attachments"] = live_attachments
    row["live_missing_tokens"] = live_missing_tokens
    row["attachments_match"] = attachments_match
    row["match"] = bool(row["match"]) and attachments_match


def _load_live_tables(
    table_names: Iterable[str],
    base_token: str,
    lark_cli: str,
) -> dict[str, _LiveTable | None]:
    """Fetch live table IDs and records once per referenced table name."""
    live: dict[str, _LiveTable | None] = {}
    for name in sorted({n for n in table_names if n}):
        tid = bs._resolve_table_id(base_token, name, lark_cli)
        if not tid:
            live[name] = None
            continue
        rows, rids = bs._read_records(base_token, tid, lark_cli)
        live[name] = _LiveTable(
            table_id=tid,
            rows=rows,
            rids=rids,
            row_by_rid=dict(zip(rids, rows, strict=True)),
        )
    return live


def _match_unique_record(
    live_table: _LiveTable | None,
    key_field: str,
    key_value: str,
    role: str,
) -> tuple[str | None, str | None]:
    """Resolve ``(key_field, key_value)`` to a single live record_id or abstain."""
    if live_table is None:
        return None, f"{role}_table_missing"
    if not key_field or not key_value:
        return None, f"{role}_empty_key"
    matches = [
        rid
        for row, rid in zip(live_table.rows, live_table.rids, strict=True)
        if bs._norm_cell(row.get(key_field)) == key_value
    ]
    if not matches:
        return None, f"{role}_not_found"
    if len(matches) > 1:
        return None, f"{role}_ambiguous"
    return matches[0], None


def _resolve_targets_for_entry(
    targets: list[dict[str, Any]],
    live_tables: dict[str, _LiveTable | None],
) -> tuple[list[str], str | None, str]:
    """Resolve all linked target rows by business key; abstain on any unresolved/ambiguous target."""
    resolved_rids: list[str] = []
    seen: set[str] = set()
    for target in targets:
        if not target.get("resolved"):
            return [], "target_unresolved", str(target.get("source_target_record_id") or "")
        t_table = str(target.get("target_table") or "")
        t_field = str(target.get("target_primary_field") or "")
        t_value = str(target.get("target_primary_value") or "")
        t_rid, reason = _match_unique_record(live_tables.get(t_table), t_field, t_value, "target")
        if reason or t_rid is None:
            return [], reason or "target_not_found", f"{t_table}.{t_field}={t_value}"
        if t_rid not in seen:
            seen.add(t_rid)
            resolved_rids.append(t_rid)
    if not resolved_rids:
        return [], "no_targets", ""
    return resolved_rids, None, ""


def _abstained_record(entry: dict[str, Any], reason: str, detail: str) -> dict[str, Any]:
    """Format one abstained link entry."""
    return {
        "table": entry.get("table"),
        "column": entry.get("column"),
        "primary_key_field": entry.get("primary_key_field"),
        "primary_key_value": entry.get("primary_key_value"),
        "reason": reason,
        "detail": detail,
    }


def _plan_link_entry(
    entry: dict[str, Any],
    live_tables: dict[str, _LiveTable | None],
) -> tuple[str, dict[str, Any]]:
    """Classify one link sidecar entry as planned, already_linked, or abstained."""
    src_table = str(entry.get("table") or "")
    pk_field = str(entry.get("primary_key_field") or "")
    pk_val = str(entry.get("primary_key_value") or "")
    col = str(entry.get("column") or "")
    src_live = live_tables.get(src_table)
    src_rid, src_reason = _match_unique_record(src_live, pk_field, pk_val, "source")
    if src_reason or src_rid is None or src_live is None:
        return "abstained", _abstained_record(entry, src_reason or "source_not_found", f"{src_table}.{pk_field}={pk_val}")

    target_rids, tgt_reason, tgt_detail = _resolve_targets_for_entry(entry.get("targets") or [], live_tables)
    if tgt_reason:
        return "abstained", _abstained_record(entry, tgt_reason, tgt_detail)

    current_rids = normalize_link_record_ids(src_live.row_by_rid[src_rid].get(col))
    payload = {
        "table": src_table,
        "table_id": src_live.table_id,
        "source_record_id": src_rid,
        "primary_key_field": pk_field,
        "primary_key_value": pk_val,
        "column": col,
        "target_record_ids": target_rids,
    }
    if current_rids == target_rids:
        return "already_linked", payload
    return "planned", payload


def _apply_planned_links(
    planned: list[dict[str, Any]],
    base_token: str,
    lark_cli: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Write planned link updates and verify each persisted via table readback."""
    attempted: list[dict[str, Any]] = []
    touched_tids: set[str] = set()
    errors: list[dict[str, Any]] = []
    for item in planned:
        resp = bs._lark(
            [
                "base",
                "+record-upsert",
                "--base-token",
                base_token,
                "--table-id",
                item["table_id"],
                "--record-id",
                item["source_record_id"],
                "--json",
                json.dumps({item["column"]: item["target_record_ids"]}, ensure_ascii=False),
                "--format",
                "json",
                "--as",
                "bot",
            ],
            lark_cli,
        )
        if resp.get("ok") is False or (resp.get("code") not in (None, 0)):
            errors.append({**item, "error": str(resp)[:200]})
            continue
        attempted.append(item)
        touched_tids.add(item["table_id"])

    readbacks: dict[str, dict[str, dict[str, Any]]] = {}
    for tid in sorted(touched_tids):
        rb_rows, rb_rids = bs._read_records(base_token, tid, lark_cli)
        readbacks[tid] = dict(zip(rb_rids, rb_rows, strict=True))

    written: list[dict[str, Any]] = []
    verify_failed: list[dict[str, Any]] = []
    for item in attempted:
        rb_row = readbacks.get(item["table_id"], {}).get(item["source_record_id"])
        rb_rids = normalize_link_record_ids(rb_row.get(item["column"])) if rb_row is not None else []
        expected = item["target_record_ids"]
        if rb_row is None or (expected and not rb_rids) or (set(expected) - set(rb_rids)):
            verify_failed.append({**item, "readback_record_ids": rb_rids, "reason": "verify_failed"})
        else:
            written.append({**item, "readback_record_ids": rb_rids})
    return written, verify_failed, errors


def plan_and_restore_links(
    backup_dir: Path,
    base_token: str,
    *,
    tables: list[str] | None = None,
    write: bool = False,
    lark_cli: str = "lark-cli",
) -> dict[str, Any]:
    """Plan and optionally apply pass-2 business-key link restoration."""
    manifest_path = backup_dir / LINKS_MANIFEST
    if not manifest_path.is_file():
        raise FileNotFoundError(f"links manifest not found: {manifest_path}")
    links_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    selected_tables = set(tables) if tables is not None else None
    entries = [
        entry
        for entry in links_manifest.get("entries", [])
        if selected_tables is None or entry.get("table") in selected_tables
    ]
    needed_tables = {str(e.get("table") or "") for e in entries} | {
        str(t.get("target_table") or "")
        for e in entries
        for t in (e.get("targets") or [])
        if t.get("target_table")
    }
    live_tables = _load_live_tables(needed_tables, base_token, lark_cli)

    buckets: dict[str, list[dict[str, Any]]] = {
        "planned": [],
        "already_linked": [],
        "abstained": [],
    }
    for entry in entries:
        bucket, item = _plan_link_entry(entry, live_tables)
        buckets[bucket].append(item)

    written: list[dict[str, Any]] = []
    verify_failed: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    if write and buckets["planned"]:
        written, verify_failed, errors = _apply_planned_links(buckets["planned"], base_token, lark_cli)

    return {
        "write": bool(write),
        "backup_dir": str(backup_dir),
        "base_token": base_token,
        "planned": buckets["planned"],
        "written": written,
        "already_linked": buckets["already_linked"],
        "abstained": buckets["abstained"],
        "verify_failed": verify_failed,
        "errors": errors,
    }
