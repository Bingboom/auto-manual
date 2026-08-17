from __future__ import annotations

import collections
import copy
import json
from pathlib import Path
from typing import Any, Iterable

from tools.source_intake_model import normalize_space


STAGING_PLAN_SCHEMA_VERSION = "source-intake-staging-plan/v1"
STAGING_OVERRIDE_SCHEMA_VERSION = "source-intake-staging-overrides/v1"

_STATUS_TO_LARK = {
    "direct": "✅直通",
    "transformed": "🔧已变换",
    "needs_review": "⚠️需确认",
    "✅直通": "✅直通",
    "🔧已变换": "🔧已变换",
    "⚠️需确认": "⚠️需确认",
}
_STAGING_FIELDS = (
    "行标签",
    "Page",
    "入库结果",
    "行标签_{lang}",
    "状态",
    "Source_lang",
    "确认",
    "章节",
    "Line_order",
    "document_key",
    "Slot_key",
    "手册值",
    "备注",
    "规格书字段",
    "Row_key",
    "规格书原值",
    "手册值_{lang}",
)


def _scalar(value: Any) -> str:
    if isinstance(value, list):
        if not value:
            return ""
        if len(value) == 1:
            return _scalar(value[0])
        return ", ".join(_scalar(item) for item in value)
    if isinstance(value, dict):
        return normalize_space(value.get("text") or value.get("name") or value.get("id"))
    return normalize_space(value)


def _line_order(value: Any) -> int:
    token = _scalar(value).split(".")[0]
    if not token.isdigit() or int(token) < 1:
        raise ValueError(f"invalid Line_order: {value!r}")
    return int(token)


def _row_line_order(row: dict[str, Any]) -> int:
    value = row.get("Line_order")
    if value is None or value == [] or (isinstance(value, str) and not value.strip()):
        value = 1
    return _line_order(value)


def decode_record_rows(payload: Any) -> list[dict[str, Any]]:
    """Decode a lark-cli record-list envelope or accept a list of row dicts."""
    if isinstance(payload, list):
        if not all(isinstance(row, dict) for row in payload):
            raise ValueError("record rows must be JSON objects")
        return [copy.deepcopy(row) for row in payload]
    if not isinstance(payload, dict):
        raise ValueError("record payload must be a list or lark-cli JSON envelope")
    if payload.get("ok") is False:
        raise ValueError(f"lark-cli record-list failed: {payload.get('error')}")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError("lark-cli envelope is missing data")
    fields = data.get("fields")
    records = data.get("data")
    record_ids = data.get("record_id_list") or []
    if not isinstance(fields, list) or not isinstance(records, list):
        raise ValueError("lark-cli envelope must contain data.fields and data.data")
    out: list[dict[str, Any]] = []
    for index, values in enumerate(records):
        if not isinstance(values, list) or len(values) != len(fields):
            raise ValueError(f"record {index + 1} does not align with projected fields")
        row = dict(zip((str(field) for field in fields), values, strict=True))
        if index < len(record_ids):
            row["_record_id"] = record_ids[index]
        out.append(row)
    return out


def staging_key(row: dict[str, Any]) -> tuple[str, str, str, str, int]:
    return (
        _scalar(row.get("Page")),
        _scalar(row.get("Section")),
        _scalar(row.get("Row_key")),
        _scalar(row.get("Slot_key")),
        _row_line_order(row),
    )


def _key_label(key: tuple[str, str, str, str, int]) -> str:
    page, section, row_key, slot_key, line_order = key
    return f"{page}/{section}/{row_key}/{slot_key or 'main'}/L{line_order}"


def _index_rows(rows: Iterable[dict[str, Any]], *, label: str) -> dict[tuple[str, str, str, str, int], dict[str, Any]]:
    index: dict[tuple[str, str, str, str, int], dict[str, Any]] = {}
    for row in rows:
        key = staging_key(row)
        if not all(key[:3]):
            raise ValueError(f"{label} row is missing Page/Section/Row_key: {row}")
        if key in index:
            raise ValueError(f"duplicate {label} logical row: {_key_label(key)}")
        index[key] = row
    return index


def _base_row(
    row: dict[str, Any],
    *,
    document_key: str,
    source_lang: str,
    localized_lang: str,
    inherited: bool,
) -> dict[str, Any]:
    localized_label = f"Row_label_{localized_lang}" if localized_lang else ""
    localized_value = f"Value_{localized_lang}" if localized_lang else ""
    localized_param = f"Param_{localized_lang}" if localized_lang else ""
    return {
        "Page": _scalar(row.get("Page")),
        "Section": _scalar(row.get("Section")),
        "Row_key": _scalar(row.get("Row_key")),
        "Slot_key": _scalar(row.get("Slot_key")),
        "Line_order": _row_line_order(row),
        "label": _scalar(row.get("Row_label_source")),
        "value": _scalar(row.get("Value_source")),
        "param": _scalar(row.get("Param_source")),
        "label_localized": _scalar(row.get(localized_label)) if localized_label else "",
        "value_localized": _scalar(row.get(localized_value)) if localized_value else "",
        "param_localized": _scalar(row.get(localized_param)) if localized_param else "",
        "spec_field": "sibling placeholder" if inherited else "",
        "raw": "not present in supplied spec" if inherited else "",
        "status": "needs_review" if inherited else "",
        "note": "Inherited from region sibling; unconfirmed by the supplied spec." if inherited else "",
        "document_key": document_key,
        "Source_lang": source_lang,
    }


def _merge_spec_candidate(target: dict[str, Any], candidate: dict[str, Any]) -> None:
    target["spec_field"] = _scalar(candidate.get("spec_field"))
    target["raw"] = _scalar(candidate.get("raw"))
    target["status"] = _scalar(candidate.get("status")) or "needs_review"
    candidate_label = _scalar(candidate.get("label"))
    candidate_value = _scalar(candidate.get("value"))
    if candidate_label and candidate_label != target["label"]:
        target["label"] = candidate_label
        target["label_localized"] = ""
        target["note"] = "Source label differs from sibling; localized label requires an override."
    if target["status"] in {"direct", "transformed"} and candidate_value:
        if candidate_value != target["value"]:
            target["value"] = candidate_value
            target["value_localized"] = ""
            target["note"] = "Source value differs from sibling; localized value requires an override."
    elif candidate_value and candidate_value != target["value"]:
        target["value"] = ""
        target["value_localized"] = ""
        target["note"] = "Manual candidate differs from sibling; approver must supply the manual values."


def _override_rows(payload: Any) -> list[dict[str, Any]]:
    if payload in (None, {}, []):
        return []
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        raise ValueError("overrides must be a list or object")
    version = payload.get("schema_version")
    if version and version != STAGING_OVERRIDE_SCHEMA_VERSION:
        raise ValueError(f"unsupported staging override schema: {version}")
    rows = payload.get("rows") or []
    if not isinstance(rows, list):
        raise ValueError("overrides.rows must be a list")
    return rows


def _apply_overrides(
    rows: list[dict[str, Any]],
    overrides: Any,
    *,
    localized_lang: str,
) -> None:
    index = _index_rows(rows, label="staging candidate")
    aliases = {
        "Row_label_source": "label",
        "Value_source": "value",
        "raw": "raw",
        "spec_field": "spec_field",
        "status": "status",
        "note": "note",
        "label": "label",
        "value": "value",
        "label_localized": "label_localized",
        "value_localized": "value_localized",
        "param": "param",
        "param_localized": "param_localized",
    }
    if localized_lang:
        aliases[f"Row_label_{localized_lang}"] = "label_localized"
        aliases[f"Value_{localized_lang}"] = "value_localized"
        aliases[f"Param_{localized_lang}"] = "param_localized"
    seen: set[tuple[str, str, str, str, int]] = set()
    for number, item in enumerate(_override_rows(overrides), 1):
        if not isinstance(item, dict) or not isinstance(item.get("key"), dict):
            raise ValueError(f"override {number} must contain key and fields objects")
        key = staging_key(item["key"])
        if key in seen:
            raise ValueError(f"duplicate override: {_key_label(key)}")
        seen.add(key)
        if key not in index:
            raise ValueError(f"override does not match a sibling row: {_key_label(key)}")
        fields = item.get("fields")
        if not isinstance(fields, dict):
            raise ValueError(f"override {number} fields must be an object")
        target = index[key]
        for raw_name, value in fields.items():
            name = aliases.get(str(raw_name))
            if not name:
                raise ValueError(f"override {_key_label(key)} has unsupported field: {raw_name}")
            target[name] = _scalar(value)


def _validate_rows(rows: list[dict[str, Any]], *, localized_lang: str) -> None:
    _index_rows(rows, label="staging candidate")
    for row in rows:
        key = staging_key(row)
        if not row.get("label"):
            raise ValueError(f"staging row is missing source label: {_key_label(key)}")
        if row.get("status") not in _STATUS_TO_LARK:
            raise ValueError(f"staging row has invalid status at {_key_label(key)}: {row.get('status')!r}")
        if localized_lang:
            source_value = _scalar(row.get("value"))
            localized_value = _scalar(row.get("value_localized"))
            if bool(source_value) != bool(localized_value):
                raise ValueError(
                    f"localized value must move with Value_source at {_key_label(key)}; "
                    f"provide the matching Value_{localized_lang} in the override"
                )
            if row["Page"] == "specifications":
                source_label = _scalar(row.get("label"))
                localized_label = _scalar(row.get("label_localized"))
                if bool(source_label) != bool(localized_label):
                    raise ValueError(
                        f"localized spec label must move with Row_label_source at {_key_label(key)}; "
                        f"provide the matching Row_label_{localized_lang} in the override"
                    )


def build_staging_plan(
    *,
    spec_candidates: list[dict[str, Any]],
    spec_sibling: Any,
    placeholder_sibling: Any,
    overrides: Any,
    document_key: str,
    source_lang: str = "en",
    localized_lang: str = "",
) -> dict[str, Any]:
    document_key = normalize_space(document_key)
    source_lang = normalize_space(source_lang) or "en"
    localized_lang = normalize_space(localized_lang)
    if not document_key:
        raise ValueError("document_key is required")
    spec_reference = decode_record_rows(spec_sibling)
    placeholder_reference = decode_record_rows(placeholder_sibling)
    spec_index = _index_rows(spec_reference, label="spec sibling")
    candidate_index = _index_rows(spec_candidates, label="spec candidate")
    missing = sorted(spec_index.keys() - candidate_index.keys())
    extra = sorted(candidate_index.keys() - spec_index.keys())
    if missing or extra:
        details = []
        if missing:
            details.append("missing=" + ", ".join(_key_label(key) for key in missing))
        if extra:
            details.append("extra=" + ", ".join(_key_label(key) for key in extra))
        raise ValueError("spec candidates do not match the region sibling structure: " + "; ".join(details))

    rows: list[dict[str, Any]] = []
    for key, reference in spec_index.items():
        target = _base_row(
            reference,
            document_key=document_key,
            source_lang=source_lang,
            localized_lang=localized_lang,
            inherited=False,
        )
        _merge_spec_candidate(target, candidate_index[key])
        rows.append(target)
    for reference in placeholder_reference:
        rows.append(
            _base_row(
                reference,
                document_key=document_key,
                source_lang=source_lang,
                localized_lang=localized_lang,
                inherited=True,
            )
        )

    expected_keys = set(spec_index) | set(_index_rows(placeholder_reference, label="placeholder sibling"))
    if len(rows) != len(expected_keys):
        raise ValueError("spec and placeholder sibling structures overlap; Page must remain part of the logical key")
    _apply_overrides(rows, overrides, localized_lang=localized_lang)
    _validate_rows(rows, localized_lang=localized_lang)
    status_counts = collections.Counter(_STATUS_TO_LARK[row["status"]] for row in rows)
    return {
        "schema_version": STAGING_PLAN_SCHEMA_VERSION,
        "document_key": document_key,
        "source_lang": source_lang,
        "localized_lang": localized_lang,
        "summary": {
            "row_count": len(rows),
            "spec_count": len(spec_reference),
            "placeholder_count": len(placeholder_reference),
            "status_counts": dict(status_counts),
            "completeness": f"complete: {len(rows)} rows cover region siblings ({len(expected_keys)})",
        },
        "rows": sorted(rows, key=staging_key),
    }


def _note_with_params(row: dict[str, Any]) -> str:
    note = _scalar(row.get("note"))
    params = []
    if row.get("param"):
        params.append(f"Param_source={row['param']}")
    if row.get("param_localized"):
        params.append(f"Param_localized={row['param_localized']}")
    if params:
        note = "; ".join(part for part in (note, ", ".join(params)) if part)
    return note


def build_lark_staging_payload(plan: dict[str, Any]) -> dict[str, Any]:
    localized_lang = _scalar(plan.get("localized_lang"))
    localized_label = f"行标签_{localized_lang}" if localized_lang else ""
    localized_value = f"手册值_{localized_lang}" if localized_lang else ""
    field_names = [name.format(lang=localized_lang) for name in _STAGING_FIELDS]
    if not localized_lang:
        field_names = [name for name in field_names if name not in {"行标签_", "手册值_"}]
    records = []
    for row in plan.get("rows") or []:
        record = {
            "行标签": row["label"],
            "Page": row["Page"],
            "入库结果": None,
            "状态": _STATUS_TO_LARK[row["status"]],
            "Source_lang": row["Source_lang"],
            "确认": False,
            "章节": row["Section"],
            "Line_order": row["Line_order"],
            "document_key": row["document_key"],
            "Slot_key": row["Slot_key"],
            "手册值": row["value"],
            "备注": _note_with_params(row),
            "规格书字段": row["spec_field"],
            "Row_key": row["Row_key"],
            "规格书原值": row["raw"],
        }
        if localized_lang:
            record[localized_label] = row["label_localized"]
            record[localized_value] = row["value_localized"]
        records.append({name: record[name] for name in field_names})
    return {"create_records": records}


def _md(value: Any) -> str:
    return _scalar(value).replace("|", "\\|").replace("\n", "<br>")


def staging_review_markdown(plan: dict[str, Any]) -> str:
    localized_lang = _scalar(plan.get("localized_lang")) or "localized"
    lines = [
        f"# Staging review: {plan['document_key']}",
        "",
        f"- {plan['summary']['completeness']}",
        f"- Statuses: {json.dumps(plan['summary']['status_counts'], ensure_ascii=False, sort_keys=True)}",
        "",
        f"| # | Page | Row key | Slot | Line | Status | Value_source | Value_{localized_lang} | Note |",
        "| ---: | --- | --- | --- | ---: | --- | --- | --- | --- |",
    ]
    for number, row in enumerate(plan.get("rows") or [], 1):
        lines.append(
            "| " + " | ".join([
                str(number),
                _md(row["Page"]),
                _md(row["Row_key"]),
                _md(row["Slot_key"]),
                str(row["Line_order"]),
                _md(_STATUS_TO_LARK[row["status"]]),
                _md(row["value"]),
                _md(row["value_localized"]),
                _md(_note_with_params(row)),
            ]) + " |"
        )
    return "\n".join(lines) + "\n"


def write_staging_outputs(plan: dict[str, Any], out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "plan": out_dir / "spec_intake_staging_plan.json",
        "payload": out_dir / "spec_intake_staging_payload.json",
        "review": out_dir / "spec_intake_staging_review.md",
    }
    paths["plan"].write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["payload"].write_text(
        json.dumps(build_lark_staging_payload(plan), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    paths["review"].write_text(staging_review_markdown(plan), encoding="utf-8")
    return paths
