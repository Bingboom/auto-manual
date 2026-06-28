#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

SOURCE_TABLE_CONTRACT_SCHEMA_VERSION = "phase2-source-table-contract/v1"
DEFAULT_CONTRACT_PATH = ROOT / "data" / "source_table_contracts" / "phase2_source_tables.json"


@dataclass(frozen=True)
class SourceTableContractIssue:
    code: str
    message: str
    table: str = ""

    def format(self) -> str:
        prefix = f"{self.table}: " if self.table else ""
        return f"{self.code}: {prefix}{self.message}"


@dataclass(frozen=True)
class SourceTableContractValidation:
    issues: tuple[SourceTableContractIssue, ...]

    @property
    def valid(self) -> bool:
        return not self.issues


def load_source_table_contract(path: Path | None = None) -> dict[str, Any]:
    contract_path = path or DEFAULT_CONTRACT_PATH
    try:
        payload = json.loads(contract_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{contract_path} is not valid JSON: {exc.msg}") from exc
    except OSError as exc:
        raise RuntimeError(f"{contract_path} cannot be read: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"{contract_path} root must be a mapping")
    return payload


def source_tables(payload: dict[str, Any]) -> list[dict[str, Any]]:
    raw = payload.get("tables")
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def source_table_by_name(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    tables: dict[str, dict[str, Any]] = {}
    for table in source_tables(payload):
        name = str(table.get("contract_name") or "").strip()
        if name:
            tables[name] = table
    return tables


def intake_target_tables(payload: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for table in source_tables(payload):
        intake = table.get("intake") if isinstance(table.get("intake"), dict) else {}
        target = str((intake or {}).get("target_table") or "").strip()
        if target:
            names.add(target)
    return names


def change_request_update_tables(payload: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for table in source_tables(payload):
        writeback = table.get("writeback") if isinstance(table.get("writeback"), dict) else {}
        if not (writeback or {}).get("change_request_update"):
            continue
        name = str(table.get("contract_name") or "").strip()
        if name:
            names.add(name)
    return names


def _as_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _required_mapping(table: dict[str, Any], key: str) -> dict[str, Any]:
    value = table.get(key)
    return value if isinstance(value, dict) else {}


def _validate_unique_table_names(tables: Iterable[dict[str, Any]]) -> list[SourceTableContractIssue]:
    seen: set[str] = set()
    issues: list[SourceTableContractIssue] = []
    for table in tables:
        name = str(table.get("contract_name") or "").strip()
        if not name:
            issues.append(SourceTableContractIssue("table.name_missing", "table contract_name is required"))
            continue
        if name in seen:
            issues.append(SourceTableContractIssue("table.name_duplicate", "table contract_name is duplicated", name))
        seen.add(name)
    return issues


def validate_source_table_contract(payload: dict[str, Any]) -> SourceTableContractValidation:
    issues: list[SourceTableContractIssue] = []
    if payload.get("schema_version") != SOURCE_TABLE_CONTRACT_SCHEMA_VERSION:
        issues.append(
            SourceTableContractIssue(
                "schema_version.invalid",
                f"expected {SOURCE_TABLE_CONTRACT_SCHEMA_VERSION}",
            )
        )
    tables = source_tables(payload)
    if not tables:
        issues.append(SourceTableContractIssue("tables.empty", "tables must contain at least one source table"))
        return SourceTableContractValidation(tuple(issues))
    issues.extend(_validate_unique_table_names(tables))

    for table in tables:
        name = str(table.get("contract_name") or "").strip()
        online = _required_mapping(table, "online_table")
        snapshot = _required_mapping(table, "snapshot")
        identity = _required_mapping(table, "identity")
        intake = _required_mapping(table, "intake")
        writeback = _required_mapping(table, "writeback")

        for required_key, section in (
            ("display_name", online),
            ("file", snapshot),
            ("business_key_fields", identity),
            ("supported", intake),
            ("change_request_update", writeback),
        ):
            if required_key not in section:
                issues.append(
                    SourceTableContractIssue(
                        "section.required_key_missing",
                        f"missing {required_key}",
                        name,
                    )
                )

        if not _as_str_list(identity.get("business_key_fields")):
            issues.append(SourceTableContractIssue("identity.business_key_missing", "business_key_fields cannot be empty", name))
        if intake.get("supported") and not intake.get("target_table"):
            issues.append(SourceTableContractIssue("intake.target_missing", "supported intake requires target_table", name))
        writable_fields = _as_str_list(writeback.get("writable_fields"))
        if writeback.get("change_request_update") and not writable_fields:
            issues.append(SourceTableContractIssue("writeback.writable_fields_missing", "update-capable table needs writable_fields", name))
        if writable_fields and not writeback.get("change_request_update"):
            issues.append(SourceTableContractIssue("writeback.writable_fields_without_update", "non-update table cannot declare writable_fields", name))

    return SourceTableContractValidation(tuple(issues))
