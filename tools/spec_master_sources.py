from __future__ import annotations

import json
import os
import re
from typing import Any, Mapping


SOURCE_SPEC_PAGE = "specifications"
SPEC_ROWS_ENV = "FEISHU_PHASE2_SPEC_ROWS_SOURCE_TABLE_ID"
PLACEHOLDERS_ENV = "FEISHU_PHASE2_PAGE_PLACEHOLDERS_SOURCE_TABLE_ID"
SPEC_ROWS_VIEW_ENV = "FEISHU_PHASE2_SPEC_ROWS_SOURCE_VIEW_ID"
PLACEHOLDERS_VIEW_ENV = "FEISHU_PHASE2_PAGE_PLACEHOLDERS_SOURCE_VIEW_ID"
SPEC_ROWS_ENV_KEY = "spec_rows_source_table_id_env"
PLACEHOLDERS_ENV_KEY = "page_placeholders_source_table_id_env"
SPEC_ROWS_VIEW_ENV_KEY = "spec_rows_source_view_id_env"
PLACEHOLDERS_VIEW_ENV_KEY = "page_placeholders_source_view_id_env"
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


def _text(value: Any) -> str:
    return str(value or "").strip()


def _env_name(source_cfg: dict[str, Any], key: str, default: str) -> str:
    return _text(source_cfg.get(key)) or default


def source_table_env_names_from_cfg(cfg: dict[str, Any]) -> tuple[str, str]:
    source_cfg = spec_master_sources_cfg(cfg)
    return (
        _env_name(source_cfg, SPEC_ROWS_ENV_KEY, SPEC_ROWS_ENV),
        _env_name(source_cfg, PLACEHOLDERS_ENV_KEY, PLACEHOLDERS_ENV),
    )


def source_view_env_names_from_cfg(cfg: dict[str, Any]) -> tuple[str, str]:
    source_cfg = spec_master_sources_cfg(cfg)
    return (
        _env_name(source_cfg, SPEC_ROWS_VIEW_ENV_KEY, SPEC_ROWS_VIEW_ENV),
        _env_name(source_cfg, PLACEHOLDERS_VIEW_ENV_KEY, PLACEHOLDERS_VIEW_ENV),
    )


def source_table_ids_from_cfg(cfg: dict[str, Any], *, environ: Mapping[str, str] | None = None) -> tuple[str, str]:
    env = environ if environ is not None else os.environ
    source_cfg = spec_master_sources_cfg(cfg)
    spec_env, placeholder_env = source_table_env_names_from_cfg(cfg)
    spec_id = _text(source_cfg.get("spec_rows_source_table_id") or env.get(spec_env, ""))
    placeholder_id = _text(
        source_cfg.get("page_placeholders_source_table_id") or env.get(placeholder_env, "")
    )
    return spec_id, placeholder_id


def source_view_ids_from_cfg(
    cfg: dict[str, Any],
    *,
    environ: Mapping[str, str] | None = None,
) -> tuple[str | None, str | None]:
    env = environ if environ is not None else os.environ
    source_cfg = spec_master_sources_cfg(cfg)
    spec_view_env, placeholder_view_env = source_view_env_names_from_cfg(cfg)
    spec_view = _text(source_cfg.get("spec_rows_source_view_id") or env.get(spec_view_env, "")) or None
    placeholder_view = (
        _text(source_cfg.get("page_placeholders_source_view_id") or env.get(placeholder_view_env, ""))
        or None
    )
    return spec_view, placeholder_view


def source_table_bindings_from_cfg(
    cfg: dict[str, Any],
    *,
    environ: Mapping[str, str] | None = None,
) -> tuple[str, str | None, str, str | None]:
    spec_id, placeholder_id = source_table_ids_from_cfg(cfg, environ=environ)
    spec_view, placeholder_view = source_view_ids_from_cfg(cfg, environ=environ)
    return spec_id, spec_view, placeholder_id, placeholder_view


def has_source_table_ids(cfg: dict[str, Any], *, environ: Mapping[str, str] | None = None) -> bool:
    spec_id, placeholder_id = source_table_ids_from_cfg(cfg, environ=environ)
    return bool(spec_id and placeholder_id)


def has_source_table_bindings(cfg: dict[str, Any], *, environ: Mapping[str, str] | None = None) -> bool:
    if has_source_table_ids(cfg, environ=environ):
        return True
    source_cfg = spec_master_sources_cfg(cfg)
    spec_env = _text(source_cfg.get(SPEC_ROWS_ENV_KEY))
    placeholder_env = _text(source_cfg.get(PLACEHOLDERS_ENV_KEY))
    return bool(spec_env and placeholder_env)


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


# A Feishu record id is `rec` + base62 (no underscores/spaces), always long. A
# business Footnote_id that merely starts with "rec" (e.g. `recharge_time`,
# `recycle_note`) must NOT be mistaken for one, or it is collected as an
# unresolvable linked-record ref and aborts the whole sync.
_FEISHU_RECORD_ID_RE = re.compile(r"^rec[A-Za-z0-9]{10,}$")


def _iter_footnote_ref_tokens(value: str) -> list[Any]:
    """Split a footnote-ref cell into tokens (a linked-record dict or a literal id str).

    A linked-record cell arrives as ``", ".join(json.dumps(item))`` (see
    ``_coerce_scalar``), which is a JSON array once wrapped in ``[]``. Parsing the
    whole cell that way keeps a multi-key ``{"id": ..., "text": ...}`` dict intact
    — a bare comma split shreds it into invalid ``{"id": ...`` / ``"text": ...}``
    fragments and silently drops the ref. A plain cell (comma-separated literal
    Footnote_ids) falls back to comma splitting.
    """
    raw = (value or "").strip()
    if not raw:
        return []
    if raw[:1] in "[{":
        candidate = raw if raw[:1] == "[" else "[" + raw + "]"
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            return [parsed]
    return [token.strip() for token in raw.split(",") if token.strip()]


def record_id_from_ref_token(token: Any) -> str | None:
    """The Feishu record id a token points at, or None for a literal Footnote_id.

    A token is a linked-record dict (``{"id": "rec…", ...}``) or a string. A bare
    string is a record id only if it matches the Feishu record-id shape, so a
    literal Footnote_id is never misread as a broken record ref.
    """
    if isinstance(token, dict):
        record_id = str(token.get("id") or "").strip()
        return record_id or None
    raw = str(token or "").strip()
    if not raw:
        return None
    if _FEISHU_RECORD_ID_RE.match(raw):
        return raw
    if raw[:1] == "{":  # defensive: a JSON object handed in as a raw string
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
            for token in _iter_footnote_ref_tokens(str(row.get(column) or "")):
                record_id = record_id_from_ref_token(token)
                if record_id and record_id not in refs:
                    refs.append(record_id)
    return refs


def normalize_footnote_ref_value(value: str, mapping: dict[str, str]) -> str:
    raw = (value or "").strip()
    if not raw:
        return value

    refs: list[str] = []
    for token in _iter_footnote_ref_tokens(raw):
        record_id = record_id_from_ref_token(token)
        if record_id is not None:
            mapped = mapping.get(record_id, record_id)
        else:
            mapped = token if isinstance(token, str) else str(token)
        if mapped not in refs:
            refs.append(mapped)
    return ", ".join(refs)


def normalize_spec_master_footnote_refs(rows: list[dict[str, str]], mapping: dict[str, str]) -> None:
    if not mapping:
        return
    for row in rows:
        for column in FOOTNOTE_REF_COLUMNS:
            row[column] = normalize_footnote_ref_value(str(row.get(column) or ""), mapping)
