#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.data_snapshot import (  # noqa: E402
    PHASE2_REQUIRED_DERIVED_FILES,
    PHASE2_REQUIRED_TABLE_FILES,
    SNAPSHOT_MANIFEST_FILE,
)
from tools.queue_contract import (  # noqa: E402
    BUILD_STARTED_AT_FIELD,
    DATA_SYNC_FIELD,
    DOCUMENT_DIRECTORY_FIELD,
    DOCUMENT_LINK_FIELD,
    FORCE_PHASE2_REFRESH_FIELD,
    IMMEDIATE_TRIGGER_FIELD,
    RESULT_FIELD,
    TRIGGER_FIELD,
)
from tools.source_intake_model import (  # noqa: E402
    MANUAL_COPY_TEXT_FIELDS,
    SPEC_TEXT_FIELDS,
    TARGET_MANUAL_COPY,
    TARGET_PAGE_PLACEHOLDERS,
    TARGET_SPEC_MASTER,
    UPDATE_CAPABLE_TABLES,
)
from tools.source_record_index import (  # noqa: E402
    TABLE_FALLBACK_KEY_FIELDS,
    TABLE_KEY_FIELDS,
    TABLE_OPTIONAL_KEY_FIELDS,
)
from tools.source_table_contract import (  # noqa: E402
    DEFAULT_CONTRACT_PATH,
    load_source_table_contract,
    source_table_by_name,
    source_tables,
    validate_source_table_contract,
)

REQUIRED_CSV_HEADERS: dict[str, tuple[str, ...]] = {
    "spec_master": ("document_key", "Region", "Model", "Page", "Row_key"),
    "spec_footnotes": ("Footnote_id", "Region", "Model", "Page", "Text_en", "Enabled"),
    "spec_notes": ("Note_id", "Region", "Model", "Page", "Text_en", "Enabled"),
    "spec_titles": ("title_en", "section_order"),
    "symbols_blocks": ("symbol_key", "text_en", "block_type"),
    "lcd_icons": ("No.", "Model", "icon_en", "icon_desc_en", "figure"),
    "troubleshooting": ("No.", "Region", "Model", "error_code", "corrective_measures_en"),
    "variable_defaults": ("Variable_key", "Value", "is_default"),
    "variable_lang_overrides": ("Variable_key", "lang", "Value"),
    "manual_copy_source": ("copy_key", "page_id", "copy_type", "Is_Latest", "source_text"),
    "localized_copy": ("copy_key", "page_id", "copy_type", "Is_Latest", "text_en"),
    "status_words": ("en", "是否为 status word"),
    "row_key_mapping": ("Row_label_source", "Line_order", "Row_key"),
}

REQUIRED_QUEUE_WRITABLE_FIELDS = (
    BUILD_STARTED_AT_FIELD,
    RESULT_FIELD,
    DOCUMENT_DIRECTORY_FIELD,
    DOCUMENT_LINK_FIELD,
    TRIGGER_FIELD,
    IMMEDIATE_TRIGGER_FIELD,
    FORCE_PHASE2_REFRESH_FIELD,
    DATA_SYNC_FIELD,
)

EXPECTED_WRITABLE_FIELDS_BY_SOURCE_TABLE: dict[str, tuple[str, ...]] = {
    TARGET_SPEC_MASTER: SPEC_TEXT_FIELDS,
    TARGET_PAGE_PLACEHOLDERS: SPEC_TEXT_FIELDS,
    TARGET_MANUAL_COPY: MANUAL_COPY_TEXT_FIELDS,
}


@dataclass(frozen=True)
class SchemaDriftIssue:
    code: str
    message: str
    surface: str = ""
    missing: tuple[str, ...] = ()

    def format(self) -> str:
        return f"{self.code}: {self.message}"


@dataclass(frozen=True)
class SchemaDriftResult:
    issues: tuple[SchemaDriftIssue, ...]

    @property
    def valid(self) -> bool:
        return not self.issues


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{path} is not valid JSON: {exc.msg}") from exc
    except OSError as exc:
        raise RuntimeError(f"{path} cannot be read: {exc}") from exc


def _manifest_names(raw_entries: Any) -> set[str]:
    if not isinstance(raw_entries, list):
        return set()
    names: set[str] = set()
    for entry in raw_entries:
        if not isinstance(entry, dict):
            continue
        logical_name = str(entry.get("logical_name") or "").strip()
        if logical_name:
            names.add(logical_name)
    return names


def _csv_headers(path: Path) -> set[str]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
    except OSError as exc:
        raise RuntimeError(f"{path} cannot be read: {exc}") from exc
    return {str(item).strip() for item in header if str(item).strip()}


def _contract_path(path: Path | None) -> Path | None:
    return path


def _contract_snapshot_file_by_logical(payload: dict[str, Any]) -> dict[str, set[str]]:
    files_by_logical: dict[str, set[str]] = {}
    for table in source_tables(payload):
        snapshot = table.get("snapshot") if isinstance(table.get("snapshot"), dict) else {}
        logical_name = str((snapshot or {}).get("logical_name") or "").strip()
        file_name = str((snapshot or {}).get("file") or "").strip()
        if logical_name and file_name:
            files_by_logical.setdefault(logical_name, set()).add(file_name)
    return files_by_logical


def _source_contract_base_issues(contract_path: Path | None) -> tuple[list[SchemaDriftIssue], dict[str, Any] | None]:
    resolved = _contract_path(contract_path)
    if resolved is None:
        return [], None
    try:
        contract = load_source_table_contract(resolved)
    except RuntimeError as exc:
        return [SchemaDriftIssue("source_contract.load_failed", str(exc), surface=str(resolved))], None

    issues: list[SchemaDriftIssue] = []
    validation = validate_source_table_contract(contract)
    for issue in validation.issues:
        issues.append(
            SchemaDriftIssue(
                f"source_contract.{issue.code}",
                issue.message,
                surface=issue.table or "source_table_contract",
            )
        )

    files_by_logical = _contract_snapshot_file_by_logical(contract)
    for logical_name, file_name in PHASE2_REQUIRED_TABLE_FILES.items():
        contract_files = files_by_logical.get(logical_name, set())
        if file_name not in contract_files:
            issues.append(
                SchemaDriftIssue(
                    "source_contract.snapshot_file_missing",
                    f"contract must map {logical_name} to {file_name}",
                    surface=logical_name,
                    missing=(file_name,),
                )
            )

    tables_by_name = source_table_by_name(contract)
    update_tables = {
        name
        for name, table in tables_by_name.items()
        if isinstance(table.get("writeback"), dict) and table["writeback"].get("change_request_update")
    }
    missing_update = tuple(sorted(set(UPDATE_CAPABLE_TABLES) - update_tables))
    extra_update = tuple(sorted(update_tables - set(UPDATE_CAPABLE_TABLES)))
    if missing_update:
        issues.append(
            SchemaDriftIssue(
                "source_contract.update_table_missing",
                "contract is missing update-capable source table(s): " + ", ".join(missing_update),
                surface="source_table_contract.writeback",
                missing=missing_update,
            )
        )
    if extra_update:
        issues.append(
            SchemaDriftIssue(
                "source_contract.update_table_extra",
                "contract marks unsupported update table(s): " + ", ".join(extra_update),
                surface="source_table_contract.writeback",
                missing=extra_update,
            )
        )

    for table_name, expected_fields in EXPECTED_WRITABLE_FIELDS_BY_SOURCE_TABLE.items():
        table = tables_by_name.get(table_name)
        writeback = table.get("writeback") if isinstance(table, dict) and isinstance(table.get("writeback"), dict) else {}
        actual = tuple(str(item) for item in (writeback or {}).get("writable_fields") or [])
        if actual != tuple(expected_fields):
            issues.append(
                SchemaDriftIssue(
                    "source_contract.writable_fields_drift",
                    f"{table_name} writable_fields {list(actual)} != {list(expected_fields)}",
                    surface=table_name,
                )
            )

    for table_name, key_fields in TABLE_KEY_FIELDS.items():
        table = tables_by_name.get(table_name)
        identity = table.get("identity") if isinstance(table, dict) and isinstance(table.get("identity"), dict) else {}
        actual_keys = tuple(str(item) for item in (identity or {}).get("business_key_fields") or [])
        if actual_keys != tuple(key_fields):
            issues.append(
                SchemaDriftIssue(
                    "source_contract.source_record_key_drift",
                    f"{table_name} business_key_fields {list(actual_keys)} != {list(key_fields)}",
                    surface=table_name,
                )
            )
        actual_optional = tuple(sorted(str(item) for item in (identity or {}).get("optional_key_fields") or []))
        expected_optional = tuple(sorted(TABLE_OPTIONAL_KEY_FIELDS.get(table_name, frozenset())))
        if actual_optional != expected_optional:
            issues.append(
                SchemaDriftIssue(
                    "source_contract.optional_key_drift",
                    f"{table_name} optional_key_fields {list(actual_optional)} != {list(expected_optional)}",
                    surface=table_name,
                )
            )
        actual_fallback = tuple(str(item) for item in (identity or {}).get("fallback_key_fields") or [])
        expected_fallback = tuple(csv_field for csv_field, _ in TABLE_FALLBACK_KEY_FIELDS.get(table_name, ()))
        if actual_fallback != expected_fallback:
            issues.append(
                SchemaDriftIssue(
                    "source_contract.fallback_key_drift",
                    f"{table_name} fallback_key_fields {list(actual_fallback)} != {list(expected_fallback)}",
                    surface=table_name,
                )
            )
    return issues, contract


def _source_contract_required_headers(contract: dict[str, Any]) -> dict[str, dict[str, set[str]]]:
    required: dict[str, dict[str, set[str]]] = {}
    for table in source_tables(contract):
        table_name = str(table.get("contract_name") or "").strip()
        snapshot = table.get("snapshot") if isinstance(table.get("snapshot"), dict) else {}
        logical_name = str((snapshot or {}).get("logical_name") or "").strip()
        if not table_name or not logical_name:
            continue
        identity = table.get("identity") if isinstance(table.get("identity"), dict) else {}
        writeback = table.get("writeback") if isinstance(table.get("writeback"), dict) else {}
        fields = {
            str(item).strip()
            for item in [
                *((identity or {}).get("business_key_fields") or []),
                *((writeback or {}).get("writable_fields") or []),
            ]
            if str(item).strip()
        }
        if not fields:
            continue
        required.setdefault(logical_name, {}).setdefault(table_name, set()).update(fields)
    return required


def _source_contract_header_issues(
    *,
    contract: dict[str, Any],
    csv_headers_by_logical: dict[str, set[str]],
) -> list[SchemaDriftIssue]:
    issues: list[SchemaDriftIssue] = []
    for logical_name, required_by_table in _source_contract_required_headers(contract).items():
        actual_headers = csv_headers_by_logical.get(logical_name, set())
        if not actual_headers:
            issues.append(
                SchemaDriftIssue(
                    "source_contract.csv_headers_missing",
                    f"no CSV headers available for contract logical table: {logical_name}",
                    surface=logical_name,
                )
            )
            continue
        for table_name, required_fields in required_by_table.items():
            missing = tuple(sorted(required_fields - actual_headers))
            if missing:
                issues.append(
                    SchemaDriftIssue(
                        "source_contract.required_header_missing",
                        f"{table_name} contract field(s) missing from {logical_name}: " + ", ".join(missing),
                        surface=table_name,
                        missing=missing,
                    )
                )
    return issues


def inspect_phase2_schema(*, phase2_root: Path, manifest_path: Path | None = None) -> list[SchemaDriftIssue]:
    manifest_file = manifest_path or (phase2_root / SNAPSHOT_MANIFEST_FILE)
    payload = _load_json(manifest_file)
    if not isinstance(payload, dict):
        return [SchemaDriftIssue("manifest.root", f"{manifest_file} root must be a mapping")]

    issues: list[SchemaDriftIssue] = []
    required_tables = set(PHASE2_REQUIRED_TABLE_FILES)
    required_derived = set(PHASE2_REQUIRED_DERIVED_FILES)
    requested_tables = {
        str(item).strip()
        for item in payload.get("requested_tables", [])
        if str(item).strip()
    }
    skipped_tables = {
        str(item).strip()
        for item in payload.get("skipped_tables", [])
        if str(item).strip()
    }
    synced_tables = _manifest_names(payload.get("tables"))
    derived_files = _manifest_names(payload.get("derived_files"))

    missing_requested = sorted(required_tables - requested_tables)
    for logical_name in missing_requested:
        issues.append(
            SchemaDriftIssue(
                "manifest.required_table_not_requested",
                f"phase2 required table is not requested: {logical_name}",
            )
        )
    for logical_name in sorted(required_tables & skipped_tables):
        issues.append(
            SchemaDriftIssue(
                "manifest.required_table_skipped",
                f"phase2 required table is skipped: {logical_name}",
            )
        )
    for logical_name in sorted(required_tables - synced_tables):
        issues.append(
            SchemaDriftIssue(
                "manifest.required_table_missing",
                f"phase2 required table is missing from manifest tables: {logical_name}",
            )
        )
    for logical_name in sorted(required_derived - derived_files):
        issues.append(
            SchemaDriftIssue(
                "manifest.required_derived_missing",
                f"phase2 required derived file is missing from manifest: {logical_name}",
            )
        )

    file_map = {**PHASE2_REQUIRED_TABLE_FILES, **PHASE2_REQUIRED_DERIVED_FILES}
    for logical_name, file_name in file_map.items():
        path = phase2_root / file_name
        if not path.exists():
            issues.append(
                SchemaDriftIssue(
                    "csv.required_file_missing",
                    f"{logical_name} CSV is missing: {path}",
                )
            )
            continue
        expected_headers = set(REQUIRED_CSV_HEADERS.get(logical_name, ()))
        if not expected_headers:
            continue
        actual_headers = _csv_headers(path)
        missing_headers = sorted(expected_headers - actual_headers)
        for header in missing_headers:
            issues.append(
                SchemaDriftIssue(
                    "csv.required_header_missing",
                    f"{logical_name} is missing required CSV header: {header}",
                )
            )
    return issues


def _field_names_from_payload(payload: Any) -> set[str]:
    if isinstance(payload, dict):
        if isinstance(payload.get("fields"), list):
            return _field_names_from_payload(payload["fields"])
        if isinstance(payload.get("items"), list):
            return _field_names_from_payload(payload["items"])
    if isinstance(payload, list):
        names: set[str] = set()
        for item in payload:
            if isinstance(item, str):
                text = item.strip()
            elif isinstance(item, dict):
                text = str(item.get("field_name") or item.get("name") or item.get("label") or "").strip()
            else:
                text = ""
            if text:
                names.add(text)
        return names
    return set()


def inspect_queue_writable_fields(
    field_names: Iterable[str],
    *,
    required_fields: Iterable[str] = REQUIRED_QUEUE_WRITABLE_FIELDS,
) -> list[SchemaDriftIssue]:
    available = {str(item).strip() for item in field_names if str(item).strip()}
    issues: list[SchemaDriftIssue] = []
    for field_name in sorted(set(required_fields) - available):
        issues.append(
            SchemaDriftIssue(
                "queue.writable_field_missing",
                f"Document_link writable field is missing: {field_name}",
            )
        )
    return issues


def inspect_queue_fields_payload(path: Path) -> list[SchemaDriftIssue]:
    payload = _load_json(path)
    field_names = _field_names_from_payload(payload)
    if not field_names:
        return [SchemaDriftIssue("queue.field_payload_empty", f"{path} does not contain field names")]
    return inspect_queue_writable_fields(field_names)


def load_schema_drift_payload(path: Path) -> dict[str, Any]:
    payload = _load_json(path)
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} root must be a mapping")
    return payload


def _payload_manifest_issues(payload: dict[str, Any]) -> list[SchemaDriftIssue]:
    manifest = payload.get("snapshot_manifest")
    if not isinstance(manifest, dict):
        return [
            SchemaDriftIssue(
                "missing_snapshot_manifest",
                "payload must contain snapshot_manifest mapping",
                surface="snapshot_manifest",
            )
        ]
    tables = _manifest_names(manifest.get("tables"))
    missing_tables = tuple(sorted(set(PHASE2_REQUIRED_TABLE_FILES) - tables))
    if not missing_tables:
        return []
    return [
        SchemaDriftIssue(
            "missing_required_logical_table",
            "snapshot_manifest.tables is missing required logical table(s): "
            + ", ".join(missing_tables),
            surface="snapshot_manifest.tables",
            missing=missing_tables,
        )
    ]


def _payload_csv_header_issues(payload: dict[str, Any]) -> list[SchemaDriftIssue]:
    raw_csv_headers = payload.get("csv_headers")
    if not isinstance(raw_csv_headers, dict):
        return [
            SchemaDriftIssue(
                "missing_csv_headers",
                "payload must contain csv_headers mapping",
                surface="csv_headers",
            )
        ]
    issues: list[SchemaDriftIssue] = []
    for logical_name, required_headers in REQUIRED_CSV_HEADERS.items():
        raw_headers = raw_csv_headers.get(logical_name)
        actual_headers = {str(item).strip() for item in raw_headers} if isinstance(raw_headers, list) else set()
        missing_headers = tuple(sorted(set(required_headers) - actual_headers))
        if missing_headers:
            issues.append(
                SchemaDriftIssue(
                    "missing_csv_header",
                    f"{logical_name} is missing required CSV header(s): "
                    + ", ".join(missing_headers),
                    surface=logical_name,
                    missing=missing_headers,
                )
            )
    return issues


def _payload_queue_field_issues(payload: dict[str, Any]) -> list[SchemaDriftIssue]:
    raw_queue_fields = payload.get("queue_fields")
    if not isinstance(raw_queue_fields, dict):
        return [
            SchemaDriftIssue(
                "missing_queue_fields",
                "payload must contain queue_fields mapping",
                surface="queue_fields",
            )
        ]
    raw_document_link = raw_queue_fields.get("document_link")
    available_fields = _field_names_from_payload(raw_document_link)
    missing_fields = tuple(sorted(set(REQUIRED_QUEUE_WRITABLE_FIELDS) - available_fields))
    if not missing_fields:
        return []
    return [
        SchemaDriftIssue(
            "missing_queue_writable_field",
            "document_link is missing writable field(s): " + ", ".join(missing_fields),
            surface="document_link",
            missing=missing_fields,
        )
    ]


def _payload_source_contract_issues(
    payload: dict[str, Any],
    *,
    source_table_contract_path: Path | None = DEFAULT_CONTRACT_PATH,
) -> list[SchemaDriftIssue]:
    issues, contract = _source_contract_base_issues(source_table_contract_path)
    if contract is None:
        return issues
    raw_csv_headers = payload.get("csv_headers")
    if not isinstance(raw_csv_headers, dict):
        return issues
    csv_headers_by_logical = {
        str(logical_name).strip(): {str(item).strip() for item in headers if str(item).strip()}
        for logical_name, headers in raw_csv_headers.items()
        if str(logical_name).strip() and isinstance(headers, list)
    }
    return [
        *issues,
        *_source_contract_header_issues(
            contract=contract,
            csv_headers_by_logical=csv_headers_by_logical,
        ),
    ]


def check_schema_drift_payload(
    payload: dict[str, Any],
    *,
    source_table_contract_path: Path | None = DEFAULT_CONTRACT_PATH,
) -> SchemaDriftResult:
    issues = [
        *_payload_manifest_issues(payload),
        *_payload_csv_header_issues(payload),
        *_payload_queue_field_issues(payload),
        *_payload_source_contract_issues(
            payload,
            source_table_contract_path=source_table_contract_path,
        ),
    ]
    return SchemaDriftResult(issues=tuple(issues))


def render_schema_drift_report(result: SchemaDriftResult) -> str:
    if result.valid:
        return "[schema-drift] OK"
    return "\n".join(f"[schema-drift] ERROR {issue.format()}" for issue in result.issues)


def inspect_schema_drift(
    *,
    phase2_root: Path,
    manifest_path: Path | None = None,
    queue_fields_path: Path | None = None,
    source_table_contract_path: Path | None = DEFAULT_CONTRACT_PATH,
) -> list[SchemaDriftIssue]:
    issues = inspect_phase2_schema(phase2_root=phase2_root, manifest_path=manifest_path)
    if queue_fields_path is not None:
        issues.extend(inspect_queue_fields_payload(queue_fields_path))
    contract_issues, contract = _source_contract_base_issues(source_table_contract_path)
    issues.extend(contract_issues)
    if contract is not None:
        csv_headers_by_logical: dict[str, set[str]] = {}
        for logical_name, file_name in {**PHASE2_REQUIRED_TABLE_FILES, **PHASE2_REQUIRED_DERIVED_FILES}.items():
            path = phase2_root / file_name
            if path.exists():
                csv_headers_by_logical[logical_name] = _csv_headers(path)
        issues.extend(
            _source_contract_header_issues(
                contract=contract,
                csv_headers_by_logical=csv_headers_by_logical,
            )
        )
    return issues


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check local phase2 and queue schema drift from fixtures or dry-run payloads.")
    parser.add_argument("--payload", default=None, help="Optional combined schema-drift JSON payload fixture.")
    parser.add_argument("--phase2-root", default="data/phase2", help="Phase2 snapshot root to inspect.")
    parser.add_argument("--manifest", default=None, help="Optional snapshot manifest path override.")
    parser.add_argument("--queue-fields", default=None, help="Optional JSON field-list fixture or dry-run payload.")
    parser.add_argument(
        "--source-table-contract",
        default=str(DEFAULT_CONTRACT_PATH.relative_to(ROOT)),
        help="Source-table contract JSON to validate alongside schema drift checks.",
    )
    parser.add_argument(
        "--no-source-table-contract",
        action="store_true",
        help="Skip source-table contract validation.",
    )
    args = parser.parse_args(argv)

    source_table_contract_path = None
    if not args.no_source_table_contract:
        source_table_contract_path = Path(args.source_table_contract)
        if not source_table_contract_path.is_absolute():
            source_table_contract_path = ROOT / source_table_contract_path

    if args.payload:
        payload_path = Path(args.payload)
        if not payload_path.is_absolute():
            payload_path = ROOT / payload_path
        try:
            result = check_schema_drift_payload(
                load_schema_drift_payload(payload_path),
                source_table_contract_path=source_table_contract_path,
            )
        except RuntimeError as exc:
            print(f"[schema-drift] ERROR {exc}", file=sys.stderr)
            return 1
        print(render_schema_drift_report(result), file=sys.stderr if not result.valid else sys.stdout)
        return 0 if result.valid else 1

    phase2_root = Path(args.phase2_root)
    if not phase2_root.is_absolute():
        phase2_root = ROOT / phase2_root
    manifest_path = Path(args.manifest) if args.manifest else None
    if manifest_path is not None and not manifest_path.is_absolute():
        manifest_path = ROOT / manifest_path
    queue_fields_path = Path(args.queue_fields) if args.queue_fields else None
    if queue_fields_path is not None and not queue_fields_path.is_absolute():
        queue_fields_path = ROOT / queue_fields_path

    try:
        issues = inspect_schema_drift(
            phase2_root=phase2_root,
            manifest_path=manifest_path,
            queue_fields_path=queue_fields_path,
            source_table_contract_path=source_table_contract_path,
        )
    except RuntimeError as exc:
        print(f"[schema-drift] ERROR {exc}", file=sys.stderr)
        return 1

    if issues:
        for issue in issues:
            print(f"[schema-drift] ERROR {issue.format()}", file=sys.stderr)
        return 1
    print("[schema-drift] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
