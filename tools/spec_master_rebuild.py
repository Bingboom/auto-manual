#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.config_loader import load_config_mapping  # noqa: E402
from tools.data_snapshot import resolve_phase2_export_root  # noqa: E402
from tools.sync_data import LarkCliSource, _phase2_identity, resolve_table_binding  # noqa: E402
from tools.sync_data_config import cli_bin as _cli_bin  # noqa: E402
from tools.sync_data_models import TABLE_SCHEMAS  # noqa: E402
from tools.sync_data_records import _dict_rows_csv_text, _write_atomic_text, normalize_records  # noqa: E402
from tools.spec_master_sources import (  # noqa: E402
    collect_footnote_record_id_refs,
    footnote_record_id_to_id_map,
    normalize_spec_master_footnote_refs,
    source_table_bindings_from_cfg,
)


SPEC_ROWS_SOURCE_NAME = "规格参数明细"
PLACEHOLDERS_SOURCE_NAME = "页面占位参数"
DOCUMENT_KEY_TABLE_ENV = "FEISHU_PHASE2_DOCUMENT_KEY_TABLE_ID"
ROW_KEY_TABLE_ENV = "FEISHU_PHASE2_ROW_KEY_TABLE_ID"
SOURCE_SPEC_PAGE = "specifications"
SPEC_ROWS_ENV = "FEISHU_PHASE2_SPEC_ROWS_SOURCE_TABLE_ID"
PLACEHOLDERS_ENV = "FEISHU_PHASE2_PAGE_PLACEHOLDERS_SOURCE_TABLE_ID"
SOURCE_PRIMARY_FIELD = "source_row_key"

SOURCE_FIELD_ORDER = (
    "Document_key_link",
    "document_key",
    "Source_lang",
    "Version",
    "Is_Latest",
    "Page",
    "Section",
    "Section_order",
    "Row_order",
    "Row_key_link",
    "Slot_key",
    "Line_order",
    "No.",
    "Row_label_source",
    "Row_label_footnote_refs",
    "Param_source",
    "Param_footnote_refs",
    "Value_source",
    "Value_footnote_refs",
    "Row_label_fr",
    "Param_fr",
    "Value_fr",
    "Row_label_es",
    "Param_es",
    "Value_es",
    "Row_label_br",
    "Param_br",
    "Value_br",
    "Row_label_de",
    "Param_de",
    "Value_de",
    "Row_label_it",
    "Param_it",
    "Value_it",
    "Row_label_uk",
    "Param_uk",
    "Value_uk",
)


def _required_env(env_name: str) -> str:
    value = str(os.environ.get(env_name, "")).strip()
    if not value:
        raise RuntimeError(f"Required environment variable is not set: {env_name}")
    return value


def _document_key_table_id() -> str:
    return _required_env(DOCUMENT_KEY_TABLE_ENV)


def _row_key_table_id() -> str:
    return _required_env(ROW_KEY_TABLE_ENV)

SPEC_MASTER_VISIBLE_ORDER = (
    "spec_row_key",
    "document_key",
    "Model",
    "Region",
    "Source_lang",
    "Version",
    "Page",
    "Section",
    "Section_order",
    "Row_order",
    "Row_key",
    "Slot_key",
    "Line_order",
    "Is_Latest",
    "Row_label_source",
    "Row_label_footnote_refs",
    "Param_source",
    "Param_footnote_refs",
    "Value_source",
    "Value_footnote_refs",
    "Row_label_fr",
    "Param_fr",
    "Value_fr",
    "Row_label_es",
    "Param_es",
    "Value_es",
    "Row_label_br",
    "Param_br",
    "Value_br",
    "Row_label_de",
    "Param_de",
    "Value_de",
    "Row_label_it",
    "Param_it",
    "Value_it",
    "Row_label_uk",
    "Param_uk",
    "Value_uk",
    "No.",
)

def _run_lark_base(cli_bin: str, args: list[str], *, input_json: Any | None = None) -> dict[str, Any]:
    command = [*shlex.split(cli_bin), "base", *args]
    payload_path: Path | None = None
    if input_json is not None:
        (ROOT / ".tmp").mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(ROOT / ".tmp"), delete=False, suffix=".json") as handle:
            payload_path = Path(handle.name)
            handle.write(json.dumps(input_json, ensure_ascii=False, separators=(",", ":")))
        command += ["--json", "@" + payload_path.relative_to(ROOT).as_posix()]
    try:
        proc = subprocess.run(
            command,
            cwd=str(ROOT),
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except subprocess.CalledProcessError as exc:
        details = "\n".join(part for part in (exc.stdout.strip(), exc.stderr.strip()) if part)
        raise RuntimeError(f"lark-cli failed: {_format_command_for_log(command)}\n{details}") from exc
    finally:
        if payload_path is not None:
            payload_path.unlink(missing_ok=True)
    text = proc.stdout.strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        start = min((idx for idx in (text.find("{"), text.find("[")) if idx != -1), default=-1)
        end = max(text.rfind("}"), text.rfind("]"))
        if start < 0 or end < start:
            raise RuntimeError(f"lark-cli returned non-JSON output: {text}")
        payload = json.loads(text[start : end + 1])
    if isinstance(payload, dict) and payload.get("ok") is False:
        raise RuntimeError(json.dumps(payload.get("error") or payload, ensure_ascii=False))
    return payload if isinstance(payload, dict) else {"data": payload}


def _format_command_for_log(command: list[str]) -> str:
    redacted: list[str] = []
    hide_next = False
    for part in command:
        if hide_next:
            redacted.append("<redacted>")
            hide_next = False
            continue
        redacted.append(part)
        if part == "--base-token":
            hide_next = True
    return " ".join(redacted)


def _data_items(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    data = payload.get("data")
    if not isinstance(data, dict):
        return []
    items = data.get(key) or data.get("items") or data.get("fields") or []
    return [item for item in items if isinstance(item, dict)]


def _field_list(cli_bin: str, base_token: str, table_id: str) -> list[dict[str, Any]]:
    payload = _run_lark_base(
        cli_bin,
        [
            "+field-list",
            "--as",
            _phase2_identity(),
            "--base-token",
            base_token,
            "--table-id",
            table_id,
            "--limit",
            "500",
        ],
    )
    return _data_items(payload, "fields")


def _field_by_name(fields: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(field.get("name") or field.get("field_name") or ""): field for field in fields}


def _table_list(cli_bin: str, base_token: str) -> list[dict[str, Any]]:
    payload = _run_lark_base(
        cli_bin,
        [
            "+table-list",
            "--as",
            _phase2_identity(),
            "--base-token",
            base_token,
            "--limit",
            "200",
        ],
    )
    return _data_items(payload, "tables")


def _table_id_by_name(cli_bin: str, base_token: str, table_name: str) -> str | None:
    for table in _table_list(cli_bin, base_token):
        if str(table.get("name") or "") == table_name:
            return str(table.get("id") or "").strip() or None
    return None


def _create_table(cli_bin: str, base_token: str, table_name: str) -> str:
    payload = _run_lark_base(
        cli_bin,
        [
            "+table-create",
            "--as",
            _phase2_identity(),
            "--base-token",
            base_token,
            "--name",
            table_name,
        ],
    )
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    table = data.get("table") if isinstance(data.get("table"), dict) else data
    table_id = str(table.get("id") or table.get("table_id") or "").strip()
    if table_id:
        return table_id
    found = _table_id_by_name(cli_bin, base_token, table_name)
    if not found:
        raise RuntimeError(f"Created table '{table_name}' but could not resolve its table id")
    return found


def _create_field(cli_bin: str, base_token: str, table_id: str, field: dict[str, Any]) -> None:
    args = [
        "+field-create",
        "--as",
        _phase2_identity(),
        "--base-token",
        base_token,
        "--table-id",
        table_id,
    ]
    if field.get("type") in {"formula", "lookup"}:
        args.append("--i-have-read-guide")
    _run_lark_base(cli_bin, args, input_json=field)


def _update_field(cli_bin: str, base_token: str, table_id: str, field_id: str, field: dict[str, Any]) -> None:
    args = [
        "+field-update",
        "--as",
        _phase2_identity(),
        "--base-token",
        base_token,
        "--table-id",
        table_id,
        "--field-id",
        field_id,
    ]
    if field.get("type") in {"formula", "lookup"}:
        args.append("--i-have-read-guide")
    _run_lark_base(
        cli_bin,
        args,
        input_json=field,
    )


def _base_field_definition(name: str, total_fields: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if name == "Document_key_link":
        return {"name": name, "type": "link", "link_table": _document_key_table_id(), "bidirectional": False}
    if name == "Row_key_link":
        return {"name": name, "type": "link", "link_table": _row_key_table_id(), "bidirectional": False}
    source = total_fields.get(name)
    if source:
        result: dict[str, Any] = {"name": name, "type": source.get("type", "text")}
        for key in ("multiple", "options", "link_table", "bidirectional"):
            if key in source and source.get(key) is not None:
                result[key] = source[key]
        return result
    return {"name": name, "type": "text"}


def _row_key_lookup_definition(fields_by_name: dict[str, dict[str, Any]], row_key_fields: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if "Row_key_link" not in fields_by_name:
        raise RuntimeError("Cannot build Row_key lookup; missing source field: Row_key_link")
    row_key = row_key_fields.get("Row_key")
    if not row_key:
        raise RuntimeError("Cannot build Row_key lookup; missing dictionary field: Row_key")
    row_key_field_id = str(row_key.get("id") or row_key.get("field_id") or "").strip()
    if not row_key_field_id:
        raise RuntimeError("Cannot build Row_key lookup; dictionary Row_key field has no id")
    return {
        "name": "Row_key",
        "type": "lookup",
        "from": "参数名",
        "select": row_key_field_id,
        "aggregate": "unique",
        "where": {
            "logic": "and",
            "conditions": [
                ["Row_label_source", "intersects", {"type": "field_ref", "field": "Row_key_link"}],
            ],
        },
    }


def _ensure_row_key_lookup(
    cli_bin: str,
    base_token: str,
    table_id: str,
    fields_by_name: dict[str, dict[str, Any]],
) -> None:
    row_key_fields = _field_by_name(_field_list(cli_bin, base_token, _row_key_table_id()))
    lookup_field = _row_key_lookup_definition(fields_by_name, row_key_fields)
    if "Row_key" in fields_by_name:
        field_id = str(fields_by_name["Row_key"].get("id") or fields_by_name["Row_key"].get("field_id") or "").strip()
        if field_id:
            _update_field(cli_bin, base_token, table_id, field_id, lookup_field)
    else:
        _create_field(cli_bin, base_token, table_id, lookup_field)


def _ensure_source_fields(cli_bin: str, base_token: str, table_id: str, total_fields: dict[str, dict[str, Any]]) -> None:
    fields = _field_list(cli_bin, base_token, table_id)
    existing = _field_by_name(fields)
    if SOURCE_PRIMARY_FIELD not in existing and len(fields) == 1:
        field_id = str(fields[0].get("id") or fields[0].get("field_id") or "").strip()
        if field_id:
            _update_field(cli_bin, base_token, table_id, field_id, {"name": SOURCE_PRIMARY_FIELD, "type": "text"})
            existing = _field_by_name(_field_list(cli_bin, base_token, table_id))
    for name in SOURCE_FIELD_ORDER:
        if name not in existing:
            _create_field(cli_bin, base_token, table_id, _base_field_definition(name, total_fields))
            existing[name] = {"name": name}
    fields_by_name = _field_by_name(_field_list(cli_bin, base_token, table_id))
    _ensure_row_key_lookup(cli_bin, base_token, table_id, fields_by_name)
    fields_by_name = _field_by_name(_field_list(cli_bin, base_token, table_id))
    formula_field = {
        "name": SOURCE_PRIMARY_FIELD,
        "type": "formula",
        "expression": _spec_row_key_formula(table_id, fields_by_name),
    }
    if SOURCE_PRIMARY_FIELD in fields_by_name:
        field_id = str(
            fields_by_name[SOURCE_PRIMARY_FIELD].get("id")
            or fields_by_name[SOURCE_PRIMARY_FIELD].get("field_id")
            or ""
        ).strip()
        if field_id:
            _update_field(cli_bin, base_token, table_id, field_id, formula_field)
    else:
        _create_field(cli_bin, base_token, table_id, formula_field)


def _ensure_source_table(
    *,
    cli_bin: str,
    base_token: str,
    table_name: str,
    total_fields: dict[str, dict[str, Any]],
) -> str:
    table_id = _table_id_by_name(cli_bin, base_token, table_name)
    if not table_id:
        table_id = _create_table(cli_bin, base_token, table_name)
    _ensure_source_fields(cli_bin, base_token, table_id, total_fields)
    return table_id


def _fetch_records_with_ids(source: LarkCliSource, *, base_token: str, table_id: str, view_id: str | None = None) -> list[dict[str, Any]]:
    return source.fetch_records_with_ids(base_token=base_token, table_id=table_id, view_id=view_id)


def _scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        if not value:
            return ""
        return _scalar(value[0])
    if isinstance(value, dict):
        for key in ("text", "name", "value"):
            if value.get(key):
                return str(value[key]).strip()
        if value.get("id"):
            return str(value["id"]).strip()
    return str(value).strip()


def _record_id_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    record_ids: list[str] = []
    for item in value:
        record_id = ""
        if isinstance(item, dict):
            record_id = str(item.get("id") or item.get("record_id") or "").strip()
        else:
            record_id = str(item or "").strip()
        if record_id and record_id not in record_ids:
            record_ids.append(record_id)
    return record_ids


def _page_tokens(value: Any) -> list[str]:
    if isinstance(value, list):
        return [_scalar(item) for item in value if _scalar(item)]
    return [token.strip() for token in _scalar(value).split(",") if token.strip()]


def _display_text_for_key(raw: str) -> str:
    match = re.fullmatch(r"\[([^\]]+)\]\(([^)]+)\)", raw)
    if match and match.group(1) == match.group(2):
        return match.group(1)
    return raw


def _key_token(value: Any, *, fallback: str, lower: bool = False) -> str:
    raw = _display_text_for_key(_scalar(value).strip())
    if lower:
        raw = raw.lower()
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", raw).strip("_")
    return cleaned or fallback


def _num_token(value: Any) -> str:
    raw = _scalar(value)
    if not raw:
        return "00"
    try:
        return str(int(float(raw))).zfill(2)
    except ValueError:
        return _key_token(raw, fallback="00", lower=True)


def spec_row_key(fields: dict[str, Any]) -> str:
    slot = _key_token(fields.get("Slot_key"), fallback="main")
    return "__".join(
        (
            _scalar(fields.get("document_key")),
            "v" + (_key_token(fields.get("Version"), fallback="na")),
            _key_token(fields.get("Page"), fallback="page"),
            "s" + _num_token(fields.get("Section_order")),
            "r" + _num_token(fields.get("Row_order")),
            _key_token(fields.get("Row_key"), fallback="row", lower=True),
            slot,
            "l" + _num_token(fields.get("Line_order")),
        )
    )


def _model_region_from_document_key(document_key: Any) -> tuple[str, str]:
    value = _scalar(document_key)
    if "_" not in value:
        return value, ""
    model, region = value.rsplit("_", 1)
    return model, region


def _fill_model_region_from_document_key(row: dict[str, str]) -> None:
    if row.get("Model") and row.get("Region"):
        return
    model, region = _model_region_from_document_key(row.get("document_key"))
    if not row.get("Model"):
        row["Model"] = model
    if not row.get("Region"):
        row["Region"] = region


def _is_spec_row(fields: dict[str, Any]) -> bool:
    return SOURCE_SPEC_PAGE in {token.lower() for token in _page_tokens(fields.get("Page"))}


def _rows_by_split(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    spec_rows: list[dict[str, Any]] = []
    placeholders: list[dict[str, Any]] = []
    for record in records:
        fields = record.get("fields") if isinstance(record.get("fields"), dict) else {}
        (spec_rows if _is_spec_row(fields) else placeholders).append(record)
    return spec_rows, placeholders


def _row_key_dictionary(source: LarkCliSource, *, base_token: str) -> dict[str, str]:
    records = _fetch_records_with_ids(source, base_token=base_token, table_id=_row_key_table_id())
    mapping: dict[str, str] = {}
    for record in records:
        fields = record.get("fields") if isinstance(record.get("fields"), dict) else {}
        key = _scalar(fields.get("Row_key")).lower()
        record_id = str(record.get("record_id") or "").strip()
        if key and record_id and key not in mapping:
            mapping[key] = record_id
    return mapping


def _document_key_dictionary(source: LarkCliSource, *, base_token: str) -> dict[str, str]:
    records = _fetch_records_with_ids(source, base_token=base_token, table_id=_document_key_table_id())
    mapping: dict[str, str] = {}
    for record in records:
        fields = record.get("fields") if isinstance(record.get("fields"), dict) else {}
        key = _scalar(fields.get("Document_key") or fields.get("document_key"))
        record_id = str(record.get("record_id") or "").strip()
        if key and record_id:
            mapping[key] = record_id
    return mapping


def _create_missing_row_key_records(
    cli_bin: str,
    base_token: str,
    records: list[dict[str, Any]],
    row_key_map: dict[str, str],
) -> None:
    missing: dict[str, str] = {}
    for record in records:
        fields = record.get("fields") if isinstance(record.get("fields"), dict) else {}
        row_key = _scalar(fields.get("Row_key")).lower()
        if row_key and row_key not in row_key_map:
            missing.setdefault(row_key, _scalar(fields.get("Row_label_source")) or row_key)
    if not missing:
        return
    rows = [
        [row_key, label, "Auto-created during spec_master source-table split"]
        for row_key, label in sorted(missing.items())
    ]
    _batch_create(cli_bin, base_token, _row_key_table_id(), ["Row_key", "Row_label_source", "Remark"], rows)


def _api_value(field_name: str, value: Any, total_fields: dict[str, dict[str, Any]]) -> Any:
    field = total_fields.get(field_name, {})
    field_type = field.get("type")
    if field_type == "link":
        return _record_id_list(value)
    if field_type == "select":
        if isinstance(value, list):
            return [_scalar(item) for item in value if _scalar(item)]
        scalar = _scalar(value)
        return [scalar] if scalar else []
    if field_type == "number":
        scalar = _scalar(value)
        if not scalar:
            return None
        try:
            number = float(scalar)
        except ValueError:
            return None
        return int(number) if number.is_integer() else number
    scalar = _scalar(value)
    return scalar if scalar else None


def _source_row_values(
    record: dict[str, Any],
    *,
    document_key_map: dict[str, str],
    row_key_map: dict[str, str],
    total_fields: dict[str, dict[str, Any]],
) -> list[Any]:
    fields = record.get("fields") if isinstance(record.get("fields"), dict) else {}
    row_key = _scalar(fields.get("Row_key")).lower()
    document_key = _scalar(fields.get("document_key"))
    values: list[Any] = []
    for name in SOURCE_FIELD_ORDER:
        if name == "Document_key_link":
            values.append([document_key_map[document_key]] if document_key in document_key_map else [])
        elif name == "Row_key_link":
            values.append([row_key_map[row_key]] if row_key in row_key_map else [])
        else:
            values.append(_api_value(name, fields.get(name), total_fields))
    return values


def _batch_create(cli_bin: str, base_token: str, table_id: str, fields: list[str], rows: list[list[Any]]) -> None:
    for start in range(0, len(rows), 200):
        _run_lark_base(
            cli_bin,
            [
                "+record-batch-create",
                "--as",
                _phase2_identity(),
                "--base-token",
                base_token,
                "--table-id",
                table_id,
            ],
            input_json={"fields": fields, "rows": rows[start : start + 200]},
        )


def _delete_records(cli_bin: str, base_token: str, table_id: str, records: list[dict[str, Any]]) -> None:
    ids = [str(record.get("record_id") or "").strip() for record in records if str(record.get("record_id") or "").strip()]
    for start in range(0, len(ids), 500):
        _run_lark_base(
            cli_bin,
            [
                "+record-delete",
                "--as",
                _phase2_identity(),
                "--base-token",
                base_token,
                "--table-id",
                table_id,
                "--yes",
            ],
            input_json={"record_id_list": ids[start : start + 500]},
        )


def _seed_source_table(
    *,
    cli_bin: str,
    base_token: str,
    source: LarkCliSource,
    table_id: str,
    records: list[dict[str, Any]],
    document_key_map: dict[str, str],
    row_key_map: dict[str, str],
    total_fields: dict[str, dict[str, Any]],
    force_reseed: bool,
) -> None:
    existing = _fetch_records_with_ids(source, base_token=base_token, table_id=table_id)
    if existing and not force_reseed:
        print(f"[spec-master-rebuild] source table {table_id} already has {len(existing)} rows; skip seeding")
        return
    if existing:
        _delete_records(cli_bin, base_token, table_id, existing)
    rows = [
        _source_row_values(
            record,
            document_key_map=document_key_map,
            row_key_map=row_key_map,
            total_fields=total_fields,
        )
        for record in records
    ]
    _batch_create(cli_bin, base_token, table_id, list(SOURCE_FIELD_ORDER), rows)


def _record_patch(cli_bin: str, base_token: str, table_id: str, record_id: str, patch: dict[str, Any]) -> None:
    _run_lark_base(
        cli_bin,
        [
            "+record-upsert",
            "--as",
            _phase2_identity(),
            "--base-token",
            base_token,
            "--table-id",
            table_id,
            "--record-id",
            record_id,
        ],
        input_json=patch,
    )


def _repair_total_rows(cli_bin: str, base_token: str, table_id: str, records: list[dict[str, Any]]) -> int:
    repairs: list[tuple[str, dict[str, Any]]] = []
    for record in records:
        fields = record.get("fields") if isinstance(record.get("fields"), dict) else {}
        record_id = str(record.get("record_id") or "").strip()
        if not record_id:
            continue
        patch: dict[str, Any] = {}
        if not _scalar(fields.get("Line_order")):
            if (
                _scalar(fields.get("document_key")) == "JE-2000E_US"
                and "storage" in {token.lower() for token in _page_tokens(fields.get("Page"))}
                and _scalar(fields.get("Row_key")) == "storage_temperature"
            ):
                storage_order = {"1 month": 1, "3 months": 2, "12 months": 3}
                patch["Line_order"] = storage_order.get(_scalar(fields.get("Param_source")), 1)
            else:
                patch["Line_order"] = 1
        if _scalar(fields.get("document_key")) == "JE-2000E_US" and not _scalar(fields.get("Row_key")):
            row_label = _scalar(fields.get("Row_label_source"))
            page = {token.lower() for token in _page_tokens(fields.get("Page"))}
            if "operation_guide" in page and row_label == "USB-C 100W Port":
                patch["Row_key"] = "usb_c_high_power_port"
            elif SOURCE_SPEC_PAGE in page and row_label == "1 × DC Expansion Port":
                patch["Row_key"] = "dc_expansion_port"
        if patch:
            repairs.append((record_id, patch))
    for record_id, patch in repairs:
        _record_patch(cli_bin, base_token, table_id, record_id, patch)
    return len(repairs)


def _formula_ref(table_id: str, field: dict[str, Any]) -> str:
    field_id = str(field.get("id") or field.get("field_id") or "").strip()
    return f"bitable::$table[{table_id}].$field[{field_id}]"


def _spec_row_key_formula(table_id: str, fields: dict[str, dict[str, Any]]) -> str:
    def ref(name: str) -> str:
        if name not in fields:
            raise RuntimeError(f"Cannot build spec_row_key formula; missing field: {name}")
        return _formula_ref(table_id, fields[name])

    return (
        "CONCATENATE("
        f"{ref('document_key')},\"__v\",{ref('Version')},\"__\",SUBSTITUTE({ref('Page')},\" \",\"_\"),"
        f"\"__s\",RIGHT(CONCATENATE(\"00\",{ref('Section_order')}),2),"
        f"\"__r\",RIGHT(CONCATENATE(\"00\",{ref('Row_order')}),2),"
        f"\"__\",{ref('Row_key')},\"__\",IF(ISBLANK({ref('Slot_key')}),\"main\",SUBSTITUTE({ref('Slot_key')},\" \",\"_\")),"
        f"\"__l\",RIGHT(CONCATENATE(\"00\",{ref('Line_order')}),2))"
    )


def _ensure_spec_row_key_field(cli_bin: str, base_token: str, table_id: str) -> None:
    fields = _field_by_name(_field_list(cli_bin, base_token, table_id))
    if "spec_row_key" in fields:
        return
    _create_field(
        cli_bin,
        base_token,
        table_id,
        {
            "name": "spec_row_key",
            "type": "formula",
            "expression": _spec_row_key_formula(table_id, fields),
        },
    )


def _set_total_visible_fields(cli_bin: str, base_token: str, table_id: str, view_id: str | None) -> None:
    if not view_id:
        return
    fields = _field_by_name(_field_list(cli_bin, base_token, table_id))
    ordered_names = [name for name in SPEC_MASTER_VISIBLE_ORDER if name in fields]
    ordered_names.extend(name for name in fields if name not in ordered_names)
    field_ids = [str(fields[name].get("id") or fields[name].get("field_id")) for name in ordered_names]
    _run_lark_base(
        cli_bin,
        [
            "+view-set-visible-fields",
            "--as",
            _phase2_identity(),
            "--base-token",
            base_token,
            "--table-id",
            table_id,
            "--view-id",
            view_id,
        ],
        input_json={"visible_fields": field_ids},
    )


def _spec_master_sources_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    phase2 = cfg.get("sync", {}).get("phase2", {}) if isinstance(cfg.get("sync"), dict) else {}
    source_cfg = phase2.get("spec_master_sources", {}) if isinstance(phase2, dict) else {}
    if not isinstance(source_cfg, dict):
        return {}
    return source_cfg


def _source_table_bindings_from_cfg(cfg: dict[str, Any]) -> tuple[str, str | None, str, str | None]:
    return source_table_bindings_from_cfg(cfg)


def _base_token_from_cfg(cfg: dict[str, Any]) -> str:
    sync_cfg = cfg.get("sync", {}) if isinstance(cfg.get("sync"), dict) else {}
    phase2 = sync_cfg.get("phase2", {}) if isinstance(sync_cfg.get("phase2"), dict) else {}
    env_name = str(phase2.get("base_token_env") or "").strip()
    if not env_name:
        tables = phase2.get("tables", {}) if isinstance(phase2.get("tables"), dict) else {}
        spec_master_cfg = tables.get("spec_master", {}) if isinstance(tables.get("spec_master"), dict) else {}
        env_name = str(spec_master_cfg.get("base_token_env") or "").strip()
    if not env_name:
        raise RuntimeError("sync.phase2.base_token_env is required for spec-master-rebuild source-table reads")
    value = str(os.environ.get(env_name, "")).strip()
    if not value:
        raise RuntimeError(f"Required environment variable is not set: {env_name}")
    return value


def _write_merged_csv(
    cfg: dict[str, Any],
    *,
    data_root: str | None,
    rows: list[dict[str, str]],
) -> Path:
    export_root = resolve_phase2_export_root(cfg, repo_root=ROOT, data_root=data_root)
    path = export_root / TABLE_SCHEMAS["spec_master"].file_name
    _write_atomic_text(path, _dict_rows_csv_text(TABLE_SCHEMAS["spec_master"].columns, rows))
    return path


def _merged_rows_from_sources(
    source: LarkCliSource,
    *,
    base_token: str,
    spec_rows_table_id: str,
    spec_rows_view_id: str | None = None,
    placeholders_table_id: str,
    placeholders_view_id: str | None = None,
) -> list[dict[str, str]]:
    spec_records = source.fetch_records(base_token=base_token, table_id=spec_rows_table_id, view_id=spec_rows_view_id)
    placeholder_records = source.fetch_records(
        base_token=base_token,
        table_id=placeholders_table_id,
        view_id=placeholders_view_id,
    )
    rows = normalize_records(TABLE_SCHEMAS["spec_master"], [*spec_records, *placeholder_records])
    for row in rows:
        _fill_model_region_from_document_key(row)
        if not row.get("spec_row_key"):
            row["spec_row_key"] = spec_row_key(row)
    return rows


def _source_records_for_rebuild(
    source: LarkCliSource,
    *,
    base_token: str,
    spec_rows_table_id: str,
    placeholders_table_id: str,
) -> list[dict[str, Any]]:
    return [
        *_fetch_records_with_ids(source, base_token=base_token, table_id=spec_rows_table_id),
        *_fetch_records_with_ids(source, base_token=base_token, table_id=placeholders_table_id),
    ]


def _normalize_footnote_refs_from_cfg(
    cfg: dict[str, Any],
    source: LarkCliSource,
    rows: list[dict[str, str]],
) -> None:
    if not collect_footnote_record_id_refs(rows):
        return
    try:
        footnote_binding = resolve_table_binding(cfg, "spec_footnotes")
    except RuntimeError as exc:
        raise RuntimeError(
            "spec_master source rows contain Feishu linked-record footnote refs; "
            "configure sync.phase2.tables.spec_footnotes so they can be mapped to Footnote_id values"
        ) from exc
    footnote_records = _fetch_records_with_ids(
        source,
        base_token=footnote_binding.base_token,
        table_id=footnote_binding.table_id,
        view_id=footnote_binding.view_id,
    )
    normalize_spec_master_footnote_refs(rows, footnote_record_id_to_id_map(footnote_records))
    unresolved = collect_footnote_record_id_refs(rows)
    if unresolved:
        raise RuntimeError(
            "Could not resolve Feishu linked-record footnote refs to Footnote_id values: "
            + ", ".join(unresolved[:10])
        )


def _records_by_spec_row_key(records: list[dict[str, Any]]) -> dict[str, str]:
    result: dict[str, str] = {}
    duplicates: list[str] = []
    for record in records:
        fields = record.get("fields") if isinstance(record.get("fields"), dict) else {}
        key = spec_row_key(fields)
        record_id = str(record.get("record_id") or "").strip()
        if key in result:
            duplicates.append(key)
        elif record_id:
            result[key] = record_id
    if duplicates:
        raise RuntimeError("Duplicate total-table spec_row_key candidates: " + ", ".join(sorted(set(duplicates))[:10]))
    return result


def _total_patch_from_source_record(record: dict[str, Any], total_fields: dict[str, dict[str, Any]]) -> dict[str, Any]:
    fields = record.get("fields") if isinstance(record.get("fields"), dict) else {}
    patch: dict[str, Any] = {}
    for name in TABLE_SCHEMAS["spec_master"].columns:
        if name == "spec_row_key" or name not in total_fields:
            continue
        if name in {"Model", "Region"} and not _scalar(fields.get(name)):
            model, region = _model_region_from_document_key(fields.get("document_key"))
            patch[name] = _api_value(name, model if name == "Model" else region, total_fields)
        else:
            patch[name] = _api_value(name, fields.get(name), total_fields)
    return patch


def _write_back_total_table(
    *,
    cli_bin: str,
    base_token: str,
    total_table_id: str,
    total_view_id: str | None,
    source: LarkCliSource,
    source_records: list[dict[str, Any]],
) -> tuple[int, int]:
    total_fields = _field_by_name(_field_list(cli_bin, base_token, total_table_id))
    current_records = _fetch_records_with_ids(
        source,
        base_token=base_token,
        table_id=total_table_id,
        view_id=total_view_id,
    )
    current_by_key = _records_by_spec_row_key(current_records)
    creates: list[list[Any]] = []
    create_fields = [name for name in TABLE_SCHEMAS["spec_master"].columns if name != "spec_row_key" and name in total_fields]
    updated = 0
    for record in source_records:
        fields = record.get("fields") if isinstance(record.get("fields"), dict) else {}
        key = spec_row_key(fields)
        patch = _total_patch_from_source_record(record, total_fields)
        record_id = current_by_key.get(key)
        if record_id:
            _record_patch(cli_bin, base_token, total_table_id, record_id, patch)
            updated += 1
        else:
            creates.append([patch.get(field) for field in create_fields])
    if creates:
        _batch_create(cli_bin, base_token, total_table_id, create_fields, creates)
    return updated, len(creates)


def _validate_merged_rows(rows: list[dict[str, str]], *, expect_spec_rows: int | None, expect_placeholder_rows: int | None) -> None:
    spec_count = sum(1 for row in rows if SOURCE_SPEC_PAGE in {token.lower() for token in _page_tokens(row.get("Page"))})
    placeholder_count = len(rows) - spec_count
    if expect_spec_rows is not None and spec_count != expect_spec_rows:
        raise RuntimeError(f"Expected {expect_spec_rows} spec rows, got {spec_count}")
    if expect_placeholder_rows is not None and placeholder_count != expect_placeholder_rows:
        raise RuntimeError(f"Expected {expect_placeholder_rows} placeholder rows, got {placeholder_count}")
    keys = [row.get("spec_row_key", "").strip() for row in rows]
    if any(not key for key in keys):
        raise RuntimeError("spec_row_key must not be blank")
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    if duplicates:
        raise RuntimeError("Duplicate spec_row_key values: " + ", ".join(duplicates[:10]))


def _bootstrap_sources(args: argparse.Namespace, cfg: dict[str, Any], source: LarkCliSource, binding: Any) -> tuple[str, str]:
    cli_bin = _cli_bin(cfg)
    total_fields = _field_by_name(_field_list(cli_bin, binding.base_token, binding.table_id))
    records = _fetch_records_with_ids(source, base_token=binding.base_token, table_id=binding.table_id, view_id=binding.view_id)
    repaired = _repair_total_rows(cli_bin, binding.base_token, binding.table_id, records)
    if repaired:
        records = _fetch_records_with_ids(source, base_token=binding.base_token, table_id=binding.table_id, view_id=binding.view_id)

    spec_records, placeholder_records = _rows_by_split(records)
    if args.expect_spec_rows is not None and len(spec_records) != args.expect_spec_rows:
        raise RuntimeError(f"Expected {args.expect_spec_rows} spec rows, got {len(spec_records)}")
    if args.expect_placeholder_rows is not None and len(placeholder_records) != args.expect_placeholder_rows:
        raise RuntimeError(f"Expected {args.expect_placeholder_rows} placeholder rows, got {len(placeholder_records)}")

    row_key_map = _row_key_dictionary(source, base_token=binding.base_token)
    _create_missing_row_key_records(_cli_bin(cfg), binding.base_token, records, row_key_map)
    row_key_map = _row_key_dictionary(source, base_token=binding.base_token)
    document_key_map = _document_key_dictionary(source, base_token=binding.base_token)

    spec_table_id = args.spec_rows_table_id or _table_id_by_name(cli_bin, binding.base_token, SPEC_ROWS_SOURCE_NAME)
    placeholder_table_id = args.page_placeholders_table_id or _table_id_by_name(
        cli_bin, binding.base_token, PLACEHOLDERS_SOURCE_NAME
    )
    if not spec_table_id:
        spec_table_id = _ensure_source_table(
            cli_bin=cli_bin,
            base_token=binding.base_token,
            table_name=SPEC_ROWS_SOURCE_NAME,
            total_fields=total_fields,
        )
    else:
        _ensure_source_fields(cli_bin, binding.base_token, spec_table_id, total_fields)
    if not placeholder_table_id:
        placeholder_table_id = _ensure_source_table(
            cli_bin=cli_bin,
            base_token=binding.base_token,
            table_name=PLACEHOLDERS_SOURCE_NAME,
            total_fields=total_fields,
        )
    else:
        _ensure_source_fields(cli_bin, binding.base_token, placeholder_table_id, total_fields)

    _seed_source_table(
        cli_bin=cli_bin,
        base_token=binding.base_token,
        source=source,
        table_id=spec_table_id,
        records=spec_records,
        document_key_map=document_key_map,
        row_key_map=row_key_map,
        total_fields=total_fields,
        force_reseed=args.force_reseed,
    )
    _seed_source_table(
        cli_bin=cli_bin,
        base_token=binding.base_token,
        source=source,
        table_id=placeholder_table_id,
        records=placeholder_records,
        document_key_map=document_key_map,
        row_key_map=row_key_map,
        total_fields=total_fields,
        force_reseed=args.force_reseed,
    )
    _ensure_spec_row_key_field(cli_bin, binding.base_token, binding.table_id)
    try:
        _set_total_visible_fields(cli_bin, binding.base_token, binding.table_id, binding.view_id)
    except RuntimeError as exc:
        print(f"[spec-master-rebuild] WARN: could not update spec_master view field order: {exc}")
    print(f"[spec-master-rebuild] repaired_total_rows={repaired}")
    print(f"[spec-master-rebuild] spec_rows_source_table_id={spec_table_id}")
    print(f"[spec-master-rebuild] page_placeholders_source_table_id={placeholder_table_id}")
    print(f"[spec-master-rebuild] seeded_spec_rows={len(spec_records)}")
    print(f"[spec-master-rebuild] seeded_placeholder_rows={len(placeholder_records)}")
    return spec_table_id, placeholder_table_id


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rebuild spec_master from split source tables.")
    parser.add_argument("--config", default="configs/config.ja.yaml")
    parser.add_argument("--data-root", default=None)
    parser.add_argument("--spec-rows-table-id", default=None)
    parser.add_argument("--page-placeholders-table-id", default=None)
    parser.add_argument("--expect-spec-rows", type=int, default=None)
    parser.add_argument("--expect-placeholder-rows", type=int, default=None)
    parser.add_argument("--bootstrap-source-tables", action="store_true")
    parser.add_argument("--write-back", action="store_true")
    parser.add_argument("--force-reseed", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = ROOT / config_path
    try:
        cfg = load_config_mapping(config_path)
        source = LarkCliSource(cli_bin=_cli_bin(cfg), identity=_phase2_identity())
        binding = resolve_table_binding(cfg, "spec_master") if (args.bootstrap_source_tables or args.write_back) else None
        base_token = binding.base_token if binding is not None else _base_token_from_cfg(cfg)
        spec_view_id = None
        placeholder_view_id = None
        if args.bootstrap_source_tables:
            if args.dry_run:
                raise RuntimeError("--bootstrap-source-tables cannot be combined with --dry-run")
            if binding is None:
                raise RuntimeError("--bootstrap-source-tables requires sync.phase2.tables.spec_master")
            spec_table_id, placeholder_table_id = _bootstrap_sources(args, cfg, source, binding)
        else:
            spec_table_id, placeholder_table_id = (
                args.spec_rows_table_id,
                args.page_placeholders_table_id,
            )
            if not spec_table_id or not placeholder_table_id:
                cfg_spec_table_id, cfg_spec_view_id, cfg_placeholder_table_id, cfg_placeholder_view_id = (
                    _source_table_bindings_from_cfg(cfg)
                )
                spec_table_id = spec_table_id or cfg_spec_table_id
                placeholder_table_id = placeholder_table_id or cfg_placeholder_table_id
                spec_view_id = cfg_spec_view_id
                placeholder_view_id = cfg_placeholder_view_id
            if not spec_table_id or not placeholder_table_id:
                raise RuntimeError(
                    "Source table ids are required. Pass --spec-rows-table-id and "
                    "--page-placeholders-table-id, configure sync.phase2.spec_master_sources, "
                    f"or set {SPEC_ROWS_ENV}/{PLACEHOLDERS_ENV}."
                )
        rows = _merged_rows_from_sources(
            source,
            base_token=base_token,
            spec_rows_table_id=spec_table_id,
            spec_rows_view_id=spec_view_id,
            placeholders_table_id=placeholder_table_id,
            placeholders_view_id=placeholder_view_id,
        )
        _normalize_footnote_refs_from_cfg(cfg, source, rows)
        _validate_merged_rows(
            rows,
            expect_spec_rows=args.expect_spec_rows,
            expect_placeholder_rows=args.expect_placeholder_rows,
        )
        if not args.dry_run:
            output_path = _write_merged_csv(cfg, data_root=args.data_root, rows=rows)
            print(f"[spec-master-rebuild] wrote={output_path}")
            if args.write_back:
                if binding is None:
                    raise RuntimeError("--write-back requires sync.phase2.tables.spec_master")
                source_records = _source_records_for_rebuild(
                    source,
                    base_token=base_token,
                    spec_rows_table_id=spec_table_id,
                    placeholders_table_id=placeholder_table_id,
                )
                updated, created = _write_back_total_table(
                    cli_bin=_cli_bin(cfg),
                    base_token=binding.base_token,
                    total_table_id=binding.table_id,
                    total_view_id=binding.view_id,
                    source=source,
                    source_records=source_records,
                )
                print(f"[spec-master-rebuild] write_back_updated={updated}")
                print(f"[spec-master-rebuild] write_back_created={created}")
        print(f"[spec-master-rebuild] merged_rows={len(rows)}")
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"[spec-master-rebuild] ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
