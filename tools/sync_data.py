#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Protocol

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.config_loader import load_config_mapping
from tools.data_snapshot import (  # noqa: E402
    resolve_data_snapshot_paths,
    resolve_phase2_export_root,
    resolve_phase2_manifest_path,
)
from tools.sync_data_records import (  # noqa: E402
    _csv_text,
    _dict_rows_csv_text,
    _normalized_cell,
    _read_existing_mapping_rows,
    _sha256_file,
    _sha256_text,
    _write_atomic_text,
    normalize_records,
)
from tools.utils.spec_master import build_row_label_row_key_mapping_rows  # noqa: E402

TABLE_ORDER = (
    "spec_titles",
    "spec_footnotes",
    "spec_notes",
    "symbols_blocks",
    "spec_master",
)
SUPPORTED_PROVIDERS = {"lark_cli", "lark-cli", "cli"}
SUPPORTED_IDENTITIES = {"user", "bot"}
ROW_KEY_MAPPING_FIELDNAMES = ("Row_label_source", "Line_order", "Row_key", "Remark")


class RecordSource(Protocol):
    def fetch_records(
        self,
        *,
        base_token: str,
        table_id: str,
        view_id: str | None,
    ) -> list[dict[str, Any]]:
        ...


@dataclass(frozen=True)
class TableSchema:
    logical_name: str
    file_name: str
    columns: tuple[str, ...]


@dataclass(frozen=True)
class TableBinding:
    logical_name: str
    schema: TableSchema
    base_token_env: str
    table_id_env: str
    view_id_env: str | None
    base_token: str
    table_id: str
    view_id: str | None


@dataclass(frozen=True)
class TableSyncResult:
    logical_name: str
    file_name: str
    target_path: Path
    row_count: int
    sha256: str
    previous_sha256: str | None
    changed: bool


@dataclass(frozen=True)
class SyncRunResult:
    export_root: Path
    manifest_path: Path
    dry_run: bool
    provider: str
    cli_bin: str
    requested_tables: tuple[str, ...]
    skipped_tables: tuple[str, ...]
    synced_tables: tuple[TableSyncResult, ...]
    derived_files: tuple[TableSyncResult, ...]
    manifest: dict[str, Any]


TABLE_SCHEMAS: dict[str, TableSchema] = {
    "spec_master": TableSchema(
        logical_name="spec_master",
        file_name="Spec_Master.csv",
        columns=(
            "document_key",
            "Region",
            "Is_Latest",
            "Page",
            "Section",
            "Section_order",
            "Row_order",
            "Row_key",
            "Slot_key",
            "Row_label_source",
            "Row_label_footnote_refs",
            "Line_order",
            "Param_source",
            "Param_footnote_refs",
            "Value_source",
            "Value_footnote_refs",
            "Row_label_fr",
            "Param_fr",
            "Value_fr",
            "Row_label_es",
            "Model",
            "Param_es",
            "Value_es",
            "Source_lang",
        ),
    ),
    "spec_footnotes": TableSchema(
        logical_name="spec_footnotes",
        file_name="Spec_Footnotes.csv",
        columns=(
            "Footnote_id",
            "Region",
            "Model",
            "Source_lang",
            "Is_Latest",
            "Page",
            "Footnote_order",
            "Text_en",
            "Text_fr",
            "Text_es",
            "Text_ja",
            "Enabled",
        ),
    ),
    "spec_notes": TableSchema(
        logical_name="spec_notes",
        file_name="Spec_Notes.csv",
        columns=(
            "Note_id",
            "Region",
            "Model",
            "Source_lang",
            "Is_Latest",
            "Page",
            "Note_order",
            "Text_en",
            "Text_fr",
            "Text_es",
            "Text_ja",
            "Enabled",
        ),
    ),
    "spec_titles": TableSchema(
        logical_name="spec_titles",
        file_name="spec_titles.csv",
        columns=("title_en", "section_order", "title_zh", "title_jp", "title_fr", "title_es"),
    ),
    "symbols_blocks": TableSchema(
        logical_name="symbols_blocks",
        file_name="symbols_blocks.csv",
        columns=(
            "page_id",
            "image_path",
            "symbol_key",
            "text_en",
            "text_fr",
            "text_es",
            "enabled",
            "block_type",
            "column_group",
            "order",
            "Region",
            "Model",
            "Source_lang",
        ),
    ),
}


def load_config(config_path: Path) -> dict[str, Any]:
    return load_config_mapping(config_path)


def _sync_phase2_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    sync_cfg_raw = cfg.get("sync", {})
    sync_cfg = sync_cfg_raw if isinstance(sync_cfg_raw, dict) else {}
    phase2_raw = sync_cfg.get("phase2", {})
    return phase2_raw if isinstance(phase2_raw, dict) else {}


def _phase2_tables_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    phase2_cfg = _sync_phase2_cfg(cfg)
    tables_raw = phase2_cfg.get("tables", {})
    return tables_raw if isinstance(tables_raw, dict) else {}


def _provider_name(cfg: dict[str, Any]) -> str:
    raw = str(_sync_phase2_cfg(cfg).get("provider", "lark_cli")).strip().lower() or "lark_cli"
    if raw not in SUPPORTED_PROVIDERS:
        raise RuntimeError(f"Unsupported sync.phase2.provider: {raw}")
    return "lark_cli"


def _cli_bin(cfg: dict[str, Any]) -> str:
    raw = str(_sync_phase2_cfg(cfg).get("cli_bin", "lark-cli")).strip()
    return raw or "lark-cli"


def _phase2_identity() -> str:
    raw = str(os.environ.get("FEISHU_PHASE2_IDENTITY", "user")).strip().lower() or "user"
    if raw not in SUPPORTED_IDENTITIES:
        raise RuntimeError(
            "FEISHU_PHASE2_IDENTITY must be one of: " + ", ".join(sorted(SUPPORTED_IDENTITIES))
        )
    return raw


def _selected_tables(raw_tables: list[str]) -> tuple[str, ...]:
    if not raw_tables:
        return TABLE_ORDER
    selected: list[str] = []
    for raw in raw_tables:
        name = str(raw).strip().lower()
        if name not in TABLE_SCHEMAS:
            raise RuntimeError(
                "Unsupported --table value: "
                + name
                + ". Expected one of: "
                + ", ".join(TABLE_ORDER)
            )
        if name not in selected:
            selected.append(name)
    return tuple(name for name in TABLE_ORDER if name in selected)


def _env_value(env_name: str) -> str:
    value = os.environ.get(env_name, "").strip()
    if not value:
        raise RuntimeError(f"Required environment variable is not set: {env_name}")
    return value


def _table_cfg(cfg: dict[str, Any], logical_name: str) -> dict[str, Any]:
    tables_cfg = _phase2_tables_cfg(cfg)
    table_cfg_raw = tables_cfg.get(logical_name, {})
    return table_cfg_raw if isinstance(table_cfg_raw, dict) else {}


def _table_env_names(cfg: dict[str, Any], logical_name: str) -> tuple[str, str, str | None]:
    phase2_cfg = _sync_phase2_cfg(cfg)
    table_cfg = _table_cfg(cfg, logical_name)
    base_token_env = str(
        table_cfg.get("base_token_env") or phase2_cfg.get("base_token_env") or ""
    ).strip()
    table_id_env = str(table_cfg.get("table_id_env") or "").strip()
    view_id_env = str(table_cfg.get("view_id_env") or "").strip() or None
    return base_token_env, table_id_env, view_id_env


def _cli_command_parts(cli_bin: str) -> list[str]:
    parts = shlex.split(cli_bin)
    if not parts:
        raise RuntimeError("sync.phase2.cli_bin must not be empty")
    return parts


def _resolved_cli_command_parts(cli_bin: str) -> list[str]:
    parts = _cli_command_parts(cli_bin)
    command = parts[0]
    command_path = Path(command)
    if command_path.is_absolute():
        resolved_command = command
    else:
        # On Windows, subprocess cannot launch a bare command name like
        # "lark-cli" even when shutil.which() resolves it to a .cmd shim.
        # Resolve the executable up front so the same config works cross-platform.
        resolved_command = shutil.which(command) or command
    return [resolved_command, *parts[1:]]


def _cli_command_exists(cli_bin: str) -> bool:
    command = _cli_command_parts(cli_bin)[0]
    command_path = Path(command)
    if command_path.is_absolute():
        return command_path.exists()
    return shutil.which(command) is not None


def collect_sync_preflight_errors(
    cfg: dict[str, Any],
    *,
    table_names: list[str] | tuple[str, ...] | None = None,
    environ: Mapping[str, str] | None = None,
    require_cli: bool = True,
) -> list[str]:
    selected_tables = _selected_tables(list(table_names or []))
    env_map = environ if environ is not None else os.environ
    errors: list[str] = []

    if require_cli:
        cli_bin = _cli_bin(cfg)
        try:
            command = _cli_command_parts(cli_bin)[0]
        except RuntimeError as exc:
            errors.append(str(exc))
        else:
            if not _cli_command_exists(cli_bin):
                errors.append(
                    f"sync.phase2.cli_bin executable is not available: {command}"
                )

    required_env_names: list[str] = []
    seen_env_names: set[str] = set()
    for logical_name in selected_tables:
        base_token_env, table_id_env, view_id_env = _table_env_names(cfg, logical_name)
        if not base_token_env:
            errors.append(
                f"sync.phase2.tables.{logical_name}.base_token_env is required, "
                "or provide sync.phase2.base_token_env"
            )
        elif base_token_env not in seen_env_names:
            seen_env_names.add(base_token_env)
            required_env_names.append(base_token_env)
        if not table_id_env:
            errors.append(f"sync.phase2.tables.{logical_name}.table_id_env is required")
        elif table_id_env not in seen_env_names:
            seen_env_names.add(table_id_env)
            required_env_names.append(table_id_env)
        if view_id_env and view_id_env not in seen_env_names:
            seen_env_names.add(view_id_env)
            required_env_names.append(view_id_env)

    missing_env_names = [
        env_name
        for env_name in required_env_names
        if not str(env_map.get(env_name, "")).strip()
    ]
    if missing_env_names:
        errors.append(
            "Required environment variables are not set: "
            + ", ".join(missing_env_names)
        )
    return errors


def resolve_table_binding(cfg: dict[str, Any], logical_name: str) -> TableBinding:
    if logical_name not in TABLE_SCHEMAS:
        raise RuntimeError(f"Unknown sync table: {logical_name}")
    base_token_env, table_id_env, view_id_env = _table_env_names(cfg, logical_name)

    if not base_token_env:
        raise RuntimeError(
            f"sync.phase2.tables.{logical_name}.base_token_env is required, "
            "or provide sync.phase2.base_token_env"
        )
    if not table_id_env:
        raise RuntimeError(f"sync.phase2.tables.{logical_name}.table_id_env is required")

    return TableBinding(
        logical_name=logical_name,
        schema=TABLE_SCHEMAS[logical_name],
        base_token_env=base_token_env,
        table_id_env=table_id_env,
        view_id_env=view_id_env,
        base_token=_env_value(base_token_env),
        table_id=_env_value(table_id_env),
        view_id=_env_value(view_id_env) if view_id_env else None,
    )


def _parse_json_payload(raw: str) -> dict[str, Any]:
    text = (raw or "").strip()
    if not text:
        raise RuntimeError("Lark CLI returned empty output")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        start = min((idx for idx in (text.find("{"), text.find("[")) if idx != -1), default=-1)
        end = max(text.rfind("}"), text.rfind("]"))
        if start == -1 or end < start:
            raise RuntimeError("Lark CLI output is not valid JSON")
        payload = json.loads(text[start : end + 1])
    if not isinstance(payload, dict):
        raise RuntimeError("Lark CLI JSON payload must be an object")
    return payload


class LarkCliSource:
    def __init__(self, *, cli_bin: str, identity: str = "user"):
        self.cli_bin = cli_bin
        self.identity = identity
        self._field_name_cache: dict[tuple[str, str], dict[str, str]] = {}

    def _run_base_command(
        self,
        *,
        args: list[str],
    ) -> dict[str, Any]:
        cmd = [
            *_resolved_cli_command_parts(self.cli_bin),
            "base",
            *args,
        ]
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT),
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        payload = _parse_json_payload(proc.stdout)
        code = payload.get("code")
        if code not in (None, 0):
            message = str(payload.get("msg") or payload.get("message") or "Lark CLI API request failed")
            raise RuntimeError(f"Lark CLI API request failed: {message}")
        return payload

    def _field_name_map(self, *, base_token: str, table_id: str) -> dict[str, str]:
        cache_key = (base_token, table_id)
        cached = self._field_name_cache.get(cache_key)
        if cached is not None:
            return cached

        offset = 0
        limit = 500
        field_name_map: dict[str, str] = {}
        while True:
            payload = self._run_base_command(
                args=[
                    "+field-list",
                    "--as",
                    self.identity,
                    "--base-token",
                    base_token,
                    "--table-id",
                    table_id,
                    "--limit",
                    str(limit),
                    "--offset",
                    str(offset),
                ]
            )
            data = payload.get("data")
            if not isinstance(data, dict):
                raise RuntimeError("Lark CLI field list response is missing data payload")
            items = data.get("items", [])
            if not isinstance(items, list):
                raise RuntimeError("Lark CLI field list response has invalid items payload")
            for item in items:
                if not isinstance(item, dict):
                    raise RuntimeError("Lark CLI field list response contains a non-object field")
                field_id = str(item.get("field_id") or "").strip()
                field_name = str(item.get("field_name") or "").strip()
                if field_id and field_name:
                    field_name_map[field_id] = field_name
            total = int(data.get("total") or len(field_name_map))
            offset += len(items)
            if not items or offset >= total:
                break

        self._field_name_cache[cache_key] = field_name_map
        return field_name_map

    def _run_record_list(
        self,
        *,
        base_token: str,
        table_id: str,
        view_id: str | None,
        offset: int,
        limit: int,
    ) -> dict[str, Any]:
        args = [
            "+record-list",
            "--as",
            self.identity,
            "--base-token",
            base_token,
            "--table-id",
            table_id,
            "--limit",
            str(limit),
        ]
        if view_id:
            args += ["--view-id", view_id]
        if offset:
            args += ["--offset", str(offset)]
        return self._run_base_command(args=args)

    def fetch_records(
        self,
        *,
        base_token: str,
        table_id: str,
        view_id: str | None,
    ) -> list[dict[str, Any]]:
        return self._fetch_records(
            base_token=base_token,
            table_id=table_id,
            view_id=view_id,
            include_record_ids=False,
        )

    def fetch_records_with_ids(
        self,
        *,
        base_token: str,
        table_id: str,
        view_id: str | None,
    ) -> list[dict[str, Any]]:
        return self._fetch_records(
            base_token=base_token,
            table_id=table_id,
            view_id=view_id,
            include_record_ids=True,
        )

    def _fetch_records(
        self,
        *,
        base_token: str,
        table_id: str,
        view_id: str | None,
        include_record_ids: bool,
    ) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        offset = 0
        limit = 500
        field_name_map = self._field_name_map(base_token=base_token, table_id=table_id)
        while True:
            payload = self._run_record_list(
                base_token=base_token,
                table_id=table_id,
                view_id=view_id,
                offset=offset,
                limit=limit,
            )
            data = payload.get("data")
            if not isinstance(data, dict):
                raise RuntimeError("Lark CLI API response is missing data payload")
            field_ids = data.get("field_id_list", [])
            if not isinstance(field_ids, list) or not all(isinstance(field_id, str) for field_id in field_ids):
                raise RuntimeError("Lark CLI record list response has invalid field id list")
            display_field_names = data.get("fields", [])
            if not isinstance(display_field_names, list) or not all(
                isinstance(name, str) for name in display_field_names
            ):
                raise RuntimeError("Lark CLI record list response has invalid field list")
            if len(field_ids) != len(display_field_names):
                raise RuntimeError("Lark CLI record list response field metadata is misaligned")
            field_names = [
                field_name_map.get(field_id, display_name)
                for field_id, display_name in zip(field_ids, display_field_names)
            ]
            rows = data.get("data", [])
            if not isinstance(rows, list):
                raise RuntimeError("Lark CLI API response has invalid record list")
            record_ids = data.get("record_id_list", [])
            if record_ids not in (None, []):
                if not isinstance(record_ids, list) or not all(isinstance(record_id, str) for record_id in record_ids):
                    raise RuntimeError("Lark CLI record list response has invalid record id list")
                if len(record_ids) != len(rows):
                    raise RuntimeError("Lark CLI record list response record ids are misaligned")
            for row in rows:
                if not isinstance(row, list):
                    raise RuntimeError("Lark CLI record list response contains a non-list row")
                row_index = len(records) - offset
                fields = {
                    field_name: row[index] if index < len(row) else None
                    for index, field_name in enumerate(field_names)
                }
                record: dict[str, Any] = {"fields": fields}
                if include_record_ids:
                    if not isinstance(record_ids, list) or row_index >= len(record_ids):
                        raise RuntimeError("Lark CLI record list response is missing record ids")
                    record["record_id"] = record_ids[row_index]
                records.append(record)
            has_more = bool(data.get("has_more"))
            if not has_more:
                break
            if not rows:
                raise RuntimeError("Lark CLI record list response signaled pagination without rows")
            offset += len(rows)
        return records

    def upsert_record(
        self,
        *,
        base_token: str,
        table_id: str,
        record_id: str,
        record: dict[str, Any],
    ) -> dict[str, Any]:
        if not record_id.strip():
            raise RuntimeError("Lark CLI record upsert requires a non-empty record id")
        payload_dir = ROOT / ".tmp"
        payload_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            delete=False,
            dir=str(payload_dir),
            prefix="lark-upsert-",
            suffix=".json",
        ) as handle:
            payload_path = Path(handle.name)
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))

        try:
            return self._run_base_command(
                args=[
                    "+record-upsert",
                    "--as",
                    self.identity,
                    "--base-token",
                    base_token,
                    "--table-id",
                    table_id,
                    "--record-id",
                    record_id.strip(),
                    "--json",
                    "@" + payload_path.relative_to(ROOT).as_posix(),
                ]
            )
        finally:
            payload_path.unlink(missing_ok=True)


def _resolve_existing_row_key_mapping_path(
    cfg: dict[str, Any],
    *,
    data_root: str | None,
    target_path: Path,
) -> Path:
    if target_path.exists():
        return target_path

    default_path = resolve_data_snapshot_paths(
        cfg,
        repo_root=ROOT,
        data_root=None,
    ).row_key_mapping_csv
    if default_path == target_path:
        return target_path
    if default_path.exists():
        return default_path
    return target_path


def _manifest_payload(
    *,
    export_root: Path,
    manifest_path: Path,
    provider: str,
    cli_bin: str,
    requested_tables: tuple[str, ...],
    skipped_tables: tuple[str, ...],
    synced_tables: tuple[TableSyncResult, ...],
    derived_files: tuple[TableSyncResult, ...],
    built_at: datetime,
    dry_run: bool,
) -> dict[str, Any]:
    return {
        "provider": provider,
        "cli_bin": cli_bin,
        "generated_at": built_at.isoformat(),
        "export_root": export_root.relative_to(ROOT).as_posix() if export_root.is_relative_to(ROOT) else export_root.as_posix(),
        "manifest_path": manifest_path.relative_to(ROOT).as_posix() if manifest_path.is_relative_to(ROOT) else manifest_path.as_posix(),
        "dry_run": dry_run,
        "requested_tables": list(requested_tables),
        "skipped_tables": list(skipped_tables),
        "tables": [
            {
                "logical_name": result.logical_name,
                "file_name": result.file_name,
                "path": result.target_path.relative_to(ROOT).as_posix() if result.target_path.is_relative_to(ROOT) else result.target_path.as_posix(),
                "row_count": result.row_count,
                "sha256": result.sha256,
                "previous_sha256": result.previous_sha256,
                "changed": result.changed,
            }
            for result in synced_tables
        ],
        "derived_files": [
            {
                "logical_name": result.logical_name,
                "file_name": result.file_name,
                "path": result.target_path.relative_to(ROOT).as_posix() if result.target_path.is_relative_to(ROOT) else result.target_path.as_posix(),
                "row_count": result.row_count,
                "sha256": result.sha256,
                "previous_sha256": result.previous_sha256,
                "changed": result.changed,
            }
            for result in derived_files
        ],
    }


def sync_phase2_snapshot(
    *,
    cfg: dict[str, Any],
    config_path: Path,
    data_root: str | None = None,
    table_names: list[str] | None = None,
    dry_run: bool = False,
    source: RecordSource | None = None,
    built_at: datetime | None = None,
) -> SyncRunResult:
    provider = _provider_name(cfg)
    if provider != "lark_cli":
        raise RuntimeError(f"Unsupported sync provider implementation: {provider}")
    cli_bin = _cli_bin(cfg)
    selected_tables = _selected_tables(table_names or [])
    preflight_errors = collect_sync_preflight_errors(
        cfg,
        table_names=selected_tables,
        require_cli=source is None,
    )
    if preflight_errors:
        raise RuntimeError("sync-data preflight failed:\n- " + "\n- ".join(preflight_errors))
    export_root = resolve_phase2_export_root(cfg, repo_root=ROOT, data_root=data_root)
    manifest_path = resolve_phase2_manifest_path(cfg, repo_root=ROOT, data_root=data_root)
    resolved_source = source or LarkCliSource(cli_bin=cli_bin, identity=_phase2_identity())
    run_at = built_at or datetime.now(timezone.utc)

    table_results: list[TableSyncResult] = []
    derived_results: list[TableSyncResult] = []
    written_files: list[tuple[Path, str]] = []
    normalized_rows_by_table: dict[str, list[dict[str, str]]] = {}

    for logical_name in selected_tables:
        binding = resolve_table_binding(cfg, logical_name)
        raw_records = resolved_source.fetch_records(
            base_token=binding.base_token,
            table_id=binding.table_id,
            view_id=binding.view_id,
        )
        normalized_rows = normalize_records(binding.schema, raw_records)
        normalized_rows_by_table[logical_name] = normalized_rows
        csv_text = _csv_text(binding.schema, normalized_rows)
        sha256 = _sha256_text(csv_text)
        target_path = export_root / binding.schema.file_name
        previous_sha256 = _sha256_file(target_path)
        table_results.append(
            TableSyncResult(
                logical_name=logical_name,
                file_name=binding.schema.file_name,
                target_path=target_path,
                row_count=len(normalized_rows),
                sha256=sha256,
                previous_sha256=previous_sha256,
                changed=sha256 != previous_sha256,
            )
        )
        written_files.append((target_path, csv_text))

    if "spec_master" in normalized_rows_by_table:
        snapshot_paths = resolve_data_snapshot_paths(
            cfg,
            repo_root=ROOT,
            data_root=str(export_root),
        )
        row_key_mapping_path = snapshot_paths.row_key_mapping_csv
        existing_mapping_path = _resolve_existing_row_key_mapping_path(
            cfg,
            data_root=data_root,
            target_path=row_key_mapping_path,
        )
        existing_mapping_rows = _read_existing_mapping_rows(existing_mapping_path)
        mapping_rows = build_row_label_row_key_mapping_rows(
            normalized_rows_by_table["spec_master"],
            existing_rows=existing_mapping_rows,
        )
        mapping_csv_text = _dict_rows_csv_text(ROW_KEY_MAPPING_FIELDNAMES, mapping_rows)
        mapping_sha256 = _sha256_text(mapping_csv_text)
        previous_mapping_sha256 = _sha256_file(row_key_mapping_path)
        derived_results.append(
            TableSyncResult(
                logical_name="row_key_mapping",
                file_name=row_key_mapping_path.name,
                target_path=row_key_mapping_path,
                row_count=len(mapping_rows),
                sha256=mapping_sha256,
                previous_sha256=previous_mapping_sha256,
                changed=mapping_sha256 != previous_mapping_sha256,
            )
        )
        written_files.append((row_key_mapping_path, mapping_csv_text))

    skipped_tables = tuple(name for name in TABLE_ORDER if name not in selected_tables)
    manifest = _manifest_payload(
        export_root=export_root,
        manifest_path=manifest_path,
        provider=provider,
        cli_bin=cli_bin,
        requested_tables=selected_tables,
        skipped_tables=skipped_tables,
        synced_tables=tuple(table_results),
        derived_files=tuple(derived_results),
        built_at=run_at,
        dry_run=dry_run,
    )

    if not dry_run:
        for target_path, csv_text in written_files:
            _write_atomic_text(target_path, csv_text)
        _write_atomic_text(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    return SyncRunResult(
        export_root=export_root,
        manifest_path=manifest_path,
        dry_run=dry_run,
        provider=provider,
        cli_bin=cli_bin,
        requested_tables=selected_tables,
        skipped_tables=skipped_tables,
        synced_tables=tuple(table_results),
        derived_files=tuple(derived_results),
        manifest=manifest,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Sync structured content snapshot CSVs from Feishu/Lark base tables.")
    ap.add_argument("--config", default="config.us.yaml", help="Config YAML path")
    ap.add_argument("--data-root", default=None, help="Override phase2 export root")
    ap.add_argument(
        "--table",
        action="append",
        default=[],
        choices=list(TABLE_ORDER),
        help="Logical table id to sync; defaults to all content tables",
    )
    ap.add_argument("--dry-run", action="store_true", help="Validate and compare without writing CSV files")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = ROOT / config_path

    try:
        cfg = load_config(config_path)
        result = sync_phase2_snapshot(
            cfg=cfg,
            config_path=config_path,
            data_root=args.data_root,
            table_names=args.table,
            dry_run=args.dry_run,
        )
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"[sync-data] ERROR: {exc}", file=sys.stderr)
        return 1

    mode = "DRY-RUN" if result.dry_run else "SYNCED"
    print(f"[sync-data] {mode} provider={result.provider} export_root={result.export_root}")
    for table in result.synced_tables:
        old_sha = table.previous_sha256 or "-"
        print(
            "[sync-data] "
            f"{table.logical_name}: rows={table.row_count} changed={'yes' if table.changed else 'no'} "
            f"old_sha={old_sha} new_sha={table.sha256} path={table.target_path}"
        )
    for derived in result.derived_files:
        old_sha = derived.previous_sha256 or "-"
        print(
            "[sync-data] "
            f"{derived.logical_name}: rows={derived.row_count} changed={'yes' if derived.changed else 'no'} "
            f"old_sha={old_sha} new_sha={derived.sha256} path={derived.target_path}"
        )
    print(f"[sync-data] manifest={result.manifest_path}")
    if result.skipped_tables:
        print(f"[sync-data] skipped_tables={','.join(result.skipped_tables)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
