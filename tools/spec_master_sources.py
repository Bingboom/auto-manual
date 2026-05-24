from __future__ import annotations

import json
import os
import re
from typing import Any, Mapping


SOURCE_SPEC_PAGE = "specifications"
SPEC_ROWS_ENV = "FEISHU_PHASE2_SPEC_ROWS_SOURCE_TABLE_ID"
PLACEHOLDERS_ENV = "FEISHU_PHASE2_PAGE_PLACEHOLDERS_SOURCE_TABLE_ID"
FOOTNOTE_REF_COLUMNS = (
    "Row_label_footnote_refs",
    "Param_footnote_refs",
    "Value_footnote_refs",
)


def spec_master_sources_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    phase2 = cfg.get("sync", {}).get("phase2", {}) if isinstance(cfg.get("sync"), dict) else {}
    source_cfg = phase2.get("spec_master_sources", {}) if isinstance(phase2, dict) else {}
    if not isinstance(source_cfg, dict):
        return {}
    return source_cfg


def source_table_ids_from_cfg(cfg: dict[str, Any], *, environ: Mapping[str, str] | None = None) -> tuple[str, str]:
    env = environ if environ is not None else os.environ
    source_cfg = spec_master_sources_cfg(cfg)
    spec_id = str(source_cfg.get("spec_rows_source_table_id") or env.get(SPEC_ROWS_ENV, "")).strip()
    placeholder_id = str(
        source_cfg.get("page_placeholders_source_table_id") or env.get(PLACEHOLDERS_ENV, "")
    ).strip()
    return spec_id, placeholder_id


def has_source_table_ids(cfg: dict[str, Any], *, environ: Mapping[str, str] | None = None) -> bool:
    spec_id, placeholder_id = source_table_ids_from_cfg(cfg, environ=environ)
    return bool(spec_id and placeholder_id)


def scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        if not value:
            return ""
        return scalar(value[0])
    if isinstance(value, dict):
        for key in ("text", "name", "value"):
            if value.get(key):
                return str(value[key]).strip()
        if value.get("id"):
            return str(value["id"]).strip()
    return str(value).strip()


def page_tokens(value: Any) -> list[str]:
    if isinstance(value, list):
        return [scalar(item) for item in value if scalar(item)]
    return [token.strip() for token in scalar(value).split(",") if token.strip()]


def _display_text_for_key(raw: str) -> str:
    match = re.fullmatch(r"\[([^\]]+)\]\(([^)]+)\)", raw)
    if match and match.group(1) == match.group(2):
        return match.group(1)
    return raw


def _key_token(value: Any, *, fallback: str, lower: bool = False) -> str:
    raw = _display_text_for_key(scalar(value).strip())
    if lower:
        raw = raw.lower()
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", raw).strip("_")
    return cleaned or fallback


def _num_token(value: Any) -> str:
    raw = scalar(value)
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
            scalar(fields.get("document_key")),
            "v" + (_key_token(fields.get("Version"), fallback="na")),
            _key_token(fields.get("Page"), fallback="page"),
            "s" + _num_token(fields.get("Section_order")),
            "r" + _num_token(fields.get("Row_order")),
            _key_token(fields.get("Row_key"), fallback="row", lower=True),
            slot,
            "l" + _num_token(fields.get("Line_order")),
        )
    )


def model_region_from_document_key(document_key: Any) -> tuple[str, str]:
    value = scalar(document_key)
    if "_" not in value:
        return value, ""
    model, region = value.rsplit("_", 1)
    return model, region


def fill_model_region_from_document_key(row: dict[str, str]) -> None:
    if row.get("Model") and row.get("Region"):
        return
    model, region = model_region_from_document_key(row.get("document_key"))
    if not row.get("Model"):
        row["Model"] = model
    if not row.get("Region"):
        row["Region"] = region


def normalize_spec_master_source_rows(rows: list[dict[str, str]]) -> None:
    for row in rows:
        fill_model_region_from_document_key(row)
        if not row.get("spec_row_key"):
            row["spec_row_key"] = spec_row_key(row)


def is_spec_page_row(row: dict[str, Any]) -> bool:
    return SOURCE_SPEC_PAGE in {token.lower() for token in page_tokens(row.get("Page"))}


def footnote_record_id_to_id_map(raw_records: list[dict[str, Any]]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for record in raw_records:
        record_id = str(record.get("record_id") or "").strip()
        fields_raw = record.get("fields")
        fields = fields_raw if isinstance(fields_raw, dict) else {}
        footnote_id = str(fields.get("Footnote_id") or fields.get("footnote_id") or "").strip()
        if record_id and footnote_id:
            mapping[record_id] = footnote_id
    return mapping


def record_id_from_ref_token(token: str) -> str | None:
    raw = (token or "").strip()
    if not raw:
        return None
    if raw.startswith("rec"):
        return raw
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if isinstance(payload, dict):
        record_id = str(payload.get("id") or "").strip()
        return record_id or None
    return None


def collect_footnote_record_id_refs(rows: list[dict[str, str]]) -> list[str]:
    refs: list[str] = []
    for row in rows:
        for column in FOOTNOTE_REF_COLUMNS:
            for token in str(row.get(column) or "").split(","):
                record_id = record_id_from_ref_token(token)
                if record_id and record_id not in refs:
                    refs.append(record_id)
    return refs


def normalize_footnote_ref_value(value: str, mapping: dict[str, str]) -> str:
    raw = (value or "").strip()
    if not raw:
        return value

    refs: list[str] = []
    for token in raw.split(","):
        item = token.strip()
        if not item:
            continue
        mapped = mapping.get(record_id_from_ref_token(item) or "", item)
        if mapped not in refs:
            refs.append(mapped)
    return ", ".join(refs)


def normalize_spec_master_footnote_refs(rows: list[dict[str, str]], mapping: dict[str, str]) -> None:
    if not mapping:
        return
    for row in rows:
        for column in FOOTNOTE_REF_COLUMNS:
            row[column] = normalize_footnote_ref_value(str(row.get(column) or ""), mapping)
