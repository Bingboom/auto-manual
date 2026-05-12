#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import tempfile
from pathlib import Path
from typing import Any, Protocol


_MARKDOWN_LINK_RE = re.compile(r"^\[(?P<label>[^\]]+)\]\((?P<target>[^)]+)\)$")


class _SchemaLike(Protocol):
    logical_name: str
    columns: tuple[str, ...]


def _coerce_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return format(value, "g")
    if isinstance(value, list):
        return ", ".join(_coerce_scalar(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return str(value)


def _coerce_attachment_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return _coerce_scalar(value)


def _coerce_choice_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        tokens: list[str] = []
        for item in value:
            token = _coerce_choice_cell(item).strip()
            if token:
                tokens.append(token)
        return ", ".join(tokens)
    if isinstance(value, dict):
        for key in ("text", "name", "value"):
            token = _coerce_choice_cell(value.get(key)).strip()
            if token:
                return token
        return _coerce_scalar(value)
    return _coerce_scalar(value)


def _normalize_boolish(value: str, *, style: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    normalized = raw.lower()
    truthy = {"1", "true", "yes", "y"}
    falsy = {"0", "false", "no", "n"}
    if style == "upper_bool":
        if normalized in truthy:
            return "TRUE"
        if normalized in falsy:
            return "FALSE"
        return raw
    if style == "digit_bool":
        if normalized in truthy:
            return "1"
        if normalized in falsy:
            return "0"
        return raw
    return raw


def _normalize_slot_key(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    match = _MARKDOWN_LINK_RE.match(raw)
    if not match:
        return raw
    target = (match.group("target") or "").strip()
    label = (match.group("label") or "").strip()
    return target or label


def _normalized_cell(schema: _SchemaLike, column: str, raw_value: Any) -> str:
    if schema.logical_name == "lcd_icons" and column == "figure":
        return _coerce_attachment_cell(raw_value).replace("\r\n", "\n").replace("\r", "\n")
    if schema.logical_name == "symbols_blocks" and column in {"Figure", "figure"}:
        return _coerce_attachment_cell(raw_value).replace("\r\n", "\n").replace("\r", "\n")
    if schema.logical_name == "symbols_blocks" and column in {"Market", "Model"}:
        return _coerce_choice_cell(raw_value).replace("\r\n", "\n").replace("\r", "\n")
    value = _coerce_scalar(raw_value).replace("\r\n", "\n").replace("\r", "\n")
    if schema.logical_name == "spec_master" and column == "Is_Latest":
        return _normalize_boolish(value, style="upper_bool")
    if schema.logical_name == "spec_master" and column == "Slot_key":
        return _normalize_slot_key(value)
    if schema.logical_name in {"spec_footnotes", "spec_notes"} and column in {"Is_Latest", "Enabled"}:
        return _normalize_boolish(value, style="upper_bool")
    if schema.logical_name == "symbols_blocks" and column == "Is_Latest":
        return _normalize_boolish(value, style="upper_bool")
    if schema.logical_name == "symbols_blocks" and column == "enabled":
        return _normalize_boolish(value, style="digit_bool")
    if schema.logical_name == "lcd_icons" and column in {"Is_latest", "has_variables"}:
        return _normalize_boolish(value, style="upper_bool")
    if schema.logical_name == "variable_defaults" and column == "is_default":
        return _normalize_boolish(value, style="upper_bool")
    return value


def _record_values(record: dict[str, Any]) -> dict[str, Any]:
    fields_raw = record.get("fields", {})
    fields = fields_raw if isinstance(fields_raw, dict) else {}
    values = {str(key): value for key, value in record.items() if isinstance(key, str)}
    for key, value in fields.items():
        if isinstance(key, str):
            values[key] = value
    return values


def normalize_records(schema: _SchemaLike, raw_records: list[dict[str, Any]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for record in raw_records:
        values = _record_values(record)
        normalized.append(
            {
                column: _normalized_cell(schema, column, values.get(column))
                for column in schema.columns
            }
        )
    normalized.sort(key=lambda row: _row_sort_key(schema, row))
    return normalized


def _numeric_sort_token(value: str) -> tuple[int, float | str]:
    raw = (value or "").strip()
    if not raw:
        return (1, "")
    try:
        return (0, float(raw))
    except ValueError:
        return (1, raw.casefold())


def _text_sort_token(value: str) -> str:
    return (value or "").strip().casefold()


def _row_sort_key(schema: _SchemaLike, row: dict[str, str]) -> tuple[Any, ...]:
    if schema.logical_name == "spec_titles":
        return (
            _numeric_sort_token(row.get("section_order", "")),
            _text_sort_token(row.get("title_en", "")),
        )
    if schema.logical_name == "spec_footnotes":
        return (
            _text_sort_token(row.get("Region", "")),
            _text_sort_token(row.get("Model", "")),
            _text_sort_token(row.get("Source_lang", "")),
            _text_sort_token(row.get("Page", "")),
            _numeric_sort_token(row.get("Footnote_order", "")),
            _text_sort_token(row.get("Footnote_id", "")),
        )
    if schema.logical_name == "spec_notes":
        return (
            _text_sort_token(row.get("Region", "")),
            _text_sort_token(row.get("Model", "")),
            _text_sort_token(row.get("Source_lang", "")),
            _text_sort_token(row.get("Page", "")),
            _numeric_sort_token(row.get("Note_order", "")),
            _text_sort_token(row.get("Note_id", "")),
        )
    if schema.logical_name == "symbols_blocks":
        return (
            _text_sort_token(row.get("page_id", "")),
            _text_sort_token(row.get("Region", "")),
            _text_sort_token(row.get("Model", "")),
            _text_sort_token(row.get("Source_lang", "")),
            _text_sort_token(row.get("Market", "")),
            _numeric_sort_token(row.get("order", "")),
            _text_sort_token(row.get("symbol_key", "")),
        )
    if schema.logical_name == "lcd_icons":
        return (
            _numeric_sort_token(row.get("No.", "")),
            _text_sort_token(row.get("icon_en", "")),
        )
    if schema.logical_name == "variable_defaults":
        return (
            _text_sort_token(row.get("Variable_key", "")),
            0 if _normalize_boolish(row.get("is_default", ""), style="upper_bool") != "TRUE" else 1,
            _text_sort_token(row.get("Model", "")),
        )
    if schema.logical_name == "variable_lang_overrides":
        return (
            _text_sort_token(row.get("Variable_key", "")),
            _text_sort_token(row.get("lang", "")),
            _text_sort_token(row.get("source_value", "") or row.get("from_prefix", "")),
        )
    return (
        _text_sort_token(row.get("document_key", "")),
        _text_sort_token(row.get("Page", "")),
        _numeric_sort_token(row.get("Section_order", "")),
        _text_sort_token(row.get("Section", "")),
        _numeric_sort_token(row.get("Row_order", "")),
        _text_sort_token(row.get("Row_key", "")),
        _text_sort_token(row.get("Slot_key", "")),
        _numeric_sort_token(row.get("Line_order", "")),
        _text_sort_token(row.get("Row_label_source", "")),
    )


def _csv_text(schema: _SchemaLike, rows: list[dict[str, str]]) -> str:
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=list(schema.columns), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({column: row.get(column, "") for column in schema.columns})
    return handle.getvalue()


def _dict_rows_csv_text(fieldnames: tuple[str, ...], rows: list[dict[str, str]] | tuple[dict[str, str], ...]) -> str:
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=list(fieldnames), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({column: row.get(column, "") for column in fieldnames})
    return handle.getvalue()


def _read_existing_mapping_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows: list[dict[str, str]] = []
        for row in reader:
            rows.append(
                {
                    "Row_label_source": (row.get("Row_label_source") or "").strip(),
                    "Line_order": (row.get("Line_order") or "").strip(),
                    "Row_key": (row.get("Row_key") or "").strip(),
                    "Remark": (row.get("Remark") or "").strip(),
                }
            )
    return rows


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", dir=str(path.parent), delete=False) as handle:
        handle.write(text)
        temp_path = Path(handle.name)
    temp_path.replace(path)
