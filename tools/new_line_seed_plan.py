"""Build a zero-write source-table seed plan for ``new-line``.

The plan is deliberately narrower than the existing scaffold writer.  It makes
the three source-data prerequisites visible before an operator enters the F6
write path:

* create the target ``Document_key`` dimension row if it is absent;
* clone page-placeholder rows from an explicitly selected source document;
* check the local contract/snapshot and print safe field-create payloads for
  any source-table fields that still need an online structure check.

This module never calls Feishu, never writes ``data/phase2``, and never creates
rows or fields.  A missing snapshot or an ambiguous source document is a
reported input requirement, not a reason to guess.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from tools.utils.path_utils import PathSegments


SCHEMA_VERSION = "new-line-seed-plan/v1"
DOCUMENT_KEY_TABLE = "02_主数据_Document_key"
DOCUMENT_KEY_TABLE_ID = "tbl8FDno2WH4OvpO"
SOURCE_CONTRACT_PATH = (
    Path(PathSegments.DATA) / "source_table_contracts" / "phase2_source_tables.json"
)
PLACEHOLDER_CONTRACT = "Page_Placeholders_Source"
SPEC_CONTRACT = "Spec_Master"

_FIELD_TYPE_HINTS = {
    "Is_Latest": "checkbox",
    "Section_order": "number",
    "Row_order": "number",
    "Line_order": "number",
}


def _relative(path: Path, *, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _resolve_root(raw: str | Path | None, *, root: Path, default: str) -> Path:
    value = Path(raw or default)
    return value.resolve() if value.is_absolute() else (root / value).resolve()


def _load_csv(path: Path) -> tuple[list[dict[str, str]], list[str], str | None]:
    if not path.exists():
        return [], [], "missing"
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            headers = list(reader.fieldnames or [])
            return [dict(row) for row in reader], headers, None
    except (OSError, csv.Error, UnicodeError) as exc:
        return [], [], f"unreadable: {exc}"


def _text(row: dict[str, Any], *names: str) -> str:
    for name in names:
        value = str(row.get(name) or "").strip()
        if value:
            return value
    return ""


def _document_key(row: dict[str, Any]) -> str:
    return _text(row, "document_key", "Document_key", "Document_Key")


def _model_from_document_key(document_key: str) -> str:
    return document_key.rsplit("_", 1)[0] if "_" in document_key else ""


def _is_specification_page(row: dict[str, Any]) -> bool:
    page = _text(row, "Page", "page").casefold()
    return not page or "specification" in page


def _placeholder_rows(rows: list[dict[str, str]], document_key: str) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if _document_key(row) == document_key and not _is_specification_page(row)
    ]


def _row_identity(row: dict[str, str]) -> dict[str, str]:
    return {
        key: _text(row, key)
        for key in ("document_key", "Page", "Section", "Row_key", "Slot_key", "Line_order")
        if _text(row, key)
    }


def _candidate_source_keys(
    rows: list[dict[str, str]], *, model: str, target_document_key: str
) -> list[str]:
    candidates: set[str] = set()
    for row in rows:
        key = _document_key(row)
        if not key or key == target_document_key:
            continue
        row_model = _text(row, "Model") or _model_from_document_key(key)
        if row_model == model:
            candidates.add(key)
    return sorted(candidates)


def _source_selection(
    *,
    candidates: list[str],
    requested: str | None,
    target_document_key: str,
) -> dict[str, Any]:
    requested = str(requested or "").strip()
    if requested:
        if requested == target_document_key:
            return {
                "status": "invalid",
                "requested": requested,
                "candidates": candidates,
                "reason": "source document must differ from target document",
            }
        if requested not in candidates:
            return {
                "status": "missing",
                "requested": requested,
                "candidates": candidates,
                "reason": "requested source document has no matching local snapshot rows",
            }
        return {"status": "selected", "requested": requested, "selected": requested, "candidates": candidates}
    if len(candidates) == 1:
        return {"status": "selected", "selected": candidates[0], "candidates": candidates}
    if not candidates:
        return {
            "status": "missing",
            "selected": None,
            "candidates": [],
            "reason": "no same-model source document was found in the local snapshot",
        }
    return {
        "status": "needs_input",
        "selected": None,
        "candidates": candidates,
        "reason": "source document is ambiguous; pass --seed-source-document-key",
    }


def _load_contract(path: Path) -> tuple[dict[str, Any], str | None]:
    if not path.exists():
        return {}, "missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError) as exc:
        return {}, f"unreadable: {exc}"
    if not isinstance(payload, dict) or not isinstance(payload.get("tables"), list):
        return {}, "invalid contract shape"
    return payload, None


def _field_create_plan(
    *,
    contract: dict[str, Any],
    snapshot_path: Path,
    root: Path,
) -> dict[str, Any]:
    rows, headers, snapshot_error = _load_csv(snapshot_path)
    del rows  # field planning only needs the local header contract
    table_plans: list[dict[str, Any]] = []
    contract_tables = {
        str(table.get("contract_name")): table
        for table in contract.get("tables", [])
        if isinstance(table, dict) and table.get("contract_name")
    }
    for name in (SPEC_CONTRACT, PLACEHOLDER_CONTRACT):
        table = contract_tables.get(name, {})
        intake = table.get("intake") if isinstance(table.get("intake"), dict) else {}
        fields = [str(field) for field in intake.get("candidate_fields", []) if str(field).strip()]
        missing = [field for field in fields if field not in headers]
        field_payloads = [
            {
                "name": field,
                "type_hint": _FIELD_TYPE_HINTS.get(field, "text"),
                "action": "ensure-present",
                "write": "blocked",
            }
            for field in missing
        ]
        table_plans.append(
            {
                "table": name,
                "reference_table_id": table.get("online_table", {}).get("reference_table_id"),
                "snapshot": _relative(snapshot_path, root=root),
                "snapshot_status": snapshot_error or "available",
                "observed_headers": headers,
                "contract_fields": fields,
                "missing_from_snapshot": missing,
                "field_payloads": field_payloads,
                "online_field_list": "required before any create; not queried by this plan",
                "helper_command_template": (
                    "lark-cli base +field-create --base-token <TARGET_BASE> "
                    "--table-id <TARGET_TABLE_ID> --json '<FIELD_PAYLOAD>'"
                ),
                "write": "blocked",
            }
        )
    return {
        "status": "plan-only",
        "contract": _relative(root / SOURCE_CONTRACT_PATH, root=root),
        "contract_schema_version": contract.get("schema_version"),
        "tables": table_plans,
        "write": "blocked",
    }


def build_seed_plan(
    scaffold_plan: Any,
    *,
    root: Path,
    data_root: str | Path | None = None,
    source_document_key: str | None = None,
) -> dict[str, Any]:
    """Return the complete F6 seed plan without external or source writes."""

    root = root.resolve()
    data_path = _resolve_root(data_root, root=root, default="data/phase2")
    model = str(scaffold_plan.target["model"])
    region = str(scaffold_plan.target["region"])
    target_document_key = f"{model}_{region}"
    snapshot_path = data_path / "Spec_Master.csv"
    rows, headers, snapshot_error = _load_csv(snapshot_path)
    target_rows = [row for row in rows if _document_key(row) == target_document_key]
    candidates = _candidate_source_keys(rows, model=model, target_document_key=target_document_key)
    selection = _source_selection(
        candidates=candidates,
        requested=source_document_key,
        target_document_key=target_document_key,
    )
    selected_source = selection.get("selected")
    source_placeholders = _placeholder_rows(rows, str(selected_source or ""))
    target_placeholders = _placeholder_rows(rows, target_document_key)

    contract_path = root / SOURCE_CONTRACT_PATH
    contract, contract_error = _load_contract(contract_path)
    errors: list[str] = []
    warnings: list[str] = []
    if snapshot_error:
        warnings.append("local phase2 snapshot is unavailable; source-row counts are empty")
    if contract_error:
        errors.append(f"source-table contract {contract_error}")
    if selection["status"] in {"needs_input", "missing", "invalid"}:
        warnings.append(str(selection.get("reason") or "source document selection is incomplete"))
    validation_status = "blocked" if errors else ("needs_input" if warnings else "passed")

    document_key_row = {
        "table": DOCUMENT_KEY_TABLE,
        "reference_table_id": DOCUMENT_KEY_TABLE_ID,
        "status": "planned",
        "operation": "create-if-missing",
        "match": {"Document_key": target_document_key},
        "fields": {
            "Document_key": target_document_key,
            "Model": {"selector": model, "resolution": "exact online link lookup"},
            "Region": {"selector": region, "resolution": "exact online link lookup"},
            "Description": f"Seeded by new-line for {target_document_key}",
        },
        "record_id_resolution": "exact-or-abstain; resolve online during approved F6 write",
        "write": "blocked",
    }
    placeholder_clone = {
        "table": PLACEHOLDER_CONTRACT,
        "status": selection["status"],
        "operation": "clone-rows-with-new-document-key",
        "source_document_key": selected_source,
        "source_selection": selection,
        "business_key_fields": ["document_key", "Row_key", "Slot_key"],
        "source_row_count": len(source_placeholders),
        "source_row_identities": [_row_identity(row) for row in source_placeholders],
        "target_existing_row_count": len(target_placeholders),
        "target_existing_row_identities": [_row_identity(row) for row in target_placeholders],
        "preserve_fields": "all source fields except document_key, which becomes the target key",
        "write": "blocked",
    }
    field_create = _field_create_plan(contract=contract, snapshot_path=snapshot_path, root=root)

    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "seed-plan",
        "write_policy": {
            "external_write": False,
            "feishu": "blocked",
            "phase2_snapshot": "blocked",
            "local_report": "allowed when --plan-output is explicitly provided",
            "gate": "approved F6 write PR required for source-table rows/fields",
        },
        "target": {
            "model": model,
            "region": region,
            "languages": list(scaffold_plan.target.get("languages", [])),
            "document_key": target_document_key,
        },
        "scaffold": {
            "schema_version": scaffold_plan.schema_version,
            "source_config": scaffold_plan.source_config,
            "manifest": scaffold_plan.manifest,
        },
        "snapshot": {
            "root": _relative(data_path, root=root),
            "spec_master": _relative(snapshot_path, root=root),
            "status": snapshot_error or "available",
            "headers": headers,
            "target_row_count": len(target_rows),
        },
        "document_key_row": document_key_row,
        "placeholder_clone": placeholder_clone,
        "field_create_helper": field_create,
        "validation": {
            "status": validation_status,
            "errors": errors,
            "warnings": warnings,
        },
    }


def render_seed_plan(plan: dict[str, Any], *, as_json: bool) -> str:
    if as_json:
        return json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True)
    target = plan["target"]
    placeholder = plan["placeholder_clone"]
    validation = plan["validation"]
    return "\n".join(
        (
            f"schema_version={plan['schema_version']}",
            "mode=seed-plan",
            f"target={target['document_key']}[{','.join(target['languages'])}]",
            f"document_key_row={plan['document_key_row']['operation']}",
            f"placeholder_clone={placeholder['status']} source={placeholder.get('source_document_key') or '-'} rows={placeholder['source_row_count']}",
            f"field_create_helper={plan['field_create_helper']['status']}",
            f"external_write={plan['write_policy']['external_write']}",
            f"validation={validation['status']}",
        )
    )
