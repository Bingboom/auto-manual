#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.config_loader import load_config_mapping
from tools.sync_data_config import (  # noqa: E402
    cli_bin as _cli_bin_impl,
    cli_command_exists as _cli_command_exists_impl,
    cli_command_parts as _cli_command_parts_impl,
    collect_sync_preflight_errors as _collect_sync_preflight_errors_impl,
    env_value as _env_value_impl,
    phase2_identity as _phase2_identity_impl,
    phase2_tables_cfg as _phase2_tables_cfg_impl,
    provider_name as _provider_name_impl,
    resolved_cli_command_parts as _resolved_cli_command_parts_impl,
    resolve_table_binding_kwargs as _resolve_table_binding_kwargs_impl,
    selected_tables as _selected_tables_impl,
    sync_phase2_cfg as _sync_phase2_cfg_impl,
    table_cfg as _table_cfg_impl,
    table_env_names as _table_env_names_impl,
)
from tools.sync_data_cli import build_sync_run_output_lines  # noqa: E402
from tools.data_snapshot import (  # noqa: E402
    resolve_data_snapshot_paths,
    resolve_phase2_export_root,
    resolve_phase2_manifest_path,
)
from tools.sync_data_entry import parse_args as _parse_args_impl, run_main as _run_main_impl  # noqa: E402
from tools.sync_data_models import (  # noqa: E402
    ROW_KEY_MAPPING_FIELDNAMES,
    SUPPORTED_IDENTITIES,
    SUPPORTED_PROVIDERS,
    SyncRunResult,
    TABLE_ORDER,
    TABLE_SCHEMAS,
    RecordSource,
    TableBinding,
    TableSchema,
    TableSyncResult,
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
from tools.sync_data_runtime import (  # noqa: E402
    SyncRuntimeDeps,
    manifest_payload as _manifest_payload_impl,
    resolve_existing_row_key_mapping_path as _resolve_existing_row_key_mapping_path_impl,
    sync_phase2_snapshot as _sync_phase2_snapshot_impl,
)
from tools.utils.spec_master import build_row_label_row_key_mapping_rows  # noqa: E402


def load_config(config_path: Path) -> dict[str, Any]:
    return load_config_mapping(config_path)


def _sync_phase2_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    return _sync_phase2_cfg_impl(cfg)


def _phase2_tables_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    return _phase2_tables_cfg_impl(cfg)


def _provider_name(cfg: dict[str, Any]) -> str:
    return _provider_name_impl(cfg, supported_providers=SUPPORTED_PROVIDERS)


def _cli_bin(cfg: dict[str, Any]) -> str:
    return _cli_bin_impl(cfg)


def _phase2_identity() -> str:
    return _phase2_identity_impl(os.environ, supported_identities=SUPPORTED_IDENTITIES)


def _phase2_base_token(cfg: dict[str, Any]) -> str:
    phase2_cfg = _sync_phase2_cfg(cfg)
    env_name = str(phase2_cfg.get("base_token_env") or "").strip()
    if not env_name:
        raise RuntimeError(
            "sync.phase2.base_token_env is required when spec_master is sourced from split source tables"
        )
    return _env_value(env_name)


def _selected_tables(raw_tables: list[str]) -> tuple[str, ...]:
    return _selected_tables_impl(raw_tables, table_order=TABLE_ORDER, table_schemas=TABLE_SCHEMAS)


def _env_value(env_name: str) -> str:
    return _env_value_impl(env_name, os.environ)


def _table_cfg(cfg: dict[str, Any], logical_name: str) -> dict[str, Any]:
    return _table_cfg_impl(cfg, logical_name)


def _table_env_names(cfg: dict[str, Any], logical_name: str) -> tuple[str, str, str | None]:
    return _table_env_names_impl(cfg, logical_name)


def _cli_command_parts(cli_bin: str) -> list[str]:
    return _cli_command_parts_impl(cli_bin, split_command=shlex.split)


def _resolved_cli_command_parts(cli_bin: str) -> list[str]:
    return _resolved_cli_command_parts_impl(
        cli_bin,
        split_command=shlex.split,
        which=shutil.which,
        path_type=Path,
    )


def _cli_command_exists(cli_bin: str) -> bool:
    return _cli_command_exists_impl(
        cli_bin,
        split_command=shlex.split,
        which=shutil.which,
        path_type=Path,
    )


def collect_sync_preflight_errors(
    cfg: dict[str, Any],
    *,
    table_names: list[str] | tuple[str, ...] | None = None,
    environ: Mapping[str, str] | None = None,
    require_cli: bool = True,
) -> list[str]:
    env_map = environ if environ is not None else os.environ
    return _collect_sync_preflight_errors_impl(
        cfg,
        table_names=table_names,
        environ=env_map,
        require_cli=require_cli,
        table_order=TABLE_ORDER,
        table_schemas=TABLE_SCHEMAS,
        cli_bin_fn=_cli_bin,
        cli_command_parts_fn=_cli_command_parts,
        cli_command_exists_fn=_cli_command_exists,
        table_env_names_fn=_table_env_names,
    )


def resolve_table_binding(cfg: dict[str, Any], logical_name: str) -> TableBinding:
    return TableBinding(
        **_resolve_table_binding_kwargs_impl(
            cfg,
            logical_name,
            table_schemas=TABLE_SCHEMAS,
            table_env_names_fn=_table_env_names,
            env_value_fn=_env_value,
        )
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


def _is_unknown_format_flag_error(exc: RuntimeError) -> bool:
    return "unknown flag: --format" in str(exc)


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
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(ROOT),
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        except subprocess.CalledProcessError as exc:
            details = []
            if exc.stdout:
                details.append(f"stdout={exc.stdout.strip()}")
            if exc.stderr:
                details.append(f"stderr={exc.stderr.strip()}")
            suffix = "; " + "; ".join(details) if details else ""
            raise RuntimeError(f"Lark CLI base command failed with exit code {exc.returncode}{suffix}") from exc
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
            items = data.get("items")
            if items is None:
                items = data.get("fields", [])
            if not isinstance(items, list):
                raise RuntimeError("Lark CLI field list response has invalid items payload")
            for item in items:
                if not isinstance(item, dict):
                    raise RuntimeError("Lark CLI field list response contains a non-object field")
                field_id = str(item.get("field_id") or item.get("id") or "").strip()
                field_name = str(item.get("field_name") or item.get("name") or "").strip()
                if field_id and field_name:
                    field_name_map[field_id] = field_name
            total = int(data.get("total") or len(items) or len(field_name_map))
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
        base_args = [
            "+record-list",
            "--as",
            self.identity,
            "--base-token",
            base_token,
            "--table-id",
            table_id,
        ]
        args = [
            *base_args,
            "--format",
            "json",
            "--jq",
            ".",
            "--limit",
            str(limit),
        ]
        if view_id:
            args += ["--view-id", view_id]
        if offset:
            args += ["--offset", str(offset)]
        try:
            return self._run_base_command(args=args)
        except RuntimeError as exc:
            if not _is_unknown_format_flag_error(exc):
                raise

        fallback_args = [
            *base_args,
            "--jq",
            ".",
            "--limit",
            str(limit),
        ]
        if view_id:
            fallback_args += ["--view-id", view_id]
        if offset:
            fallback_args += ["--offset", str(offset)]
        return self._run_base_command(args=fallback_args)

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

    def download_drive_file(
        self,
        *,
        file_token: str,
        output_path: Path,
        overwrite: bool = False,
    ) -> None:
        token = (file_token or "").strip()
        if not token:
            raise RuntimeError("Drive download requires a non-empty file_token")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            output_arg = output_path.relative_to(ROOT).as_posix()
        except ValueError:
            output_arg = output_path.as_posix()
        cmd = [
            *_resolved_cli_command_parts(self.cli_bin),
            "api",
            "GET",
            f"/open-apis/drive/v1/medias/{token}/download",
            "--as",
            self.identity,
            "--output",
            output_arg,
        ]
        if output_path.exists() and not overwrite:
            return
        subprocess.run(
            cmd,
            cwd=str(ROOT),
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
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
        limit = 200
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
    return _resolve_existing_row_key_mapping_path_impl(
        cfg,
        data_root=data_root,
        target_path=target_path,
        repo_root=ROOT,
        resolve_data_snapshot_paths_fn=resolve_data_snapshot_paths,
    )


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
    return _manifest_payload_impl(
        export_root=export_root,
        manifest_path=manifest_path,
        provider=provider,
        cli_bin=cli_bin,
        requested_tables=requested_tables,
        skipped_tables=skipped_tables,
        synced_tables=synced_tables,
        derived_files=derived_files,
        built_at=built_at,
        dry_run=dry_run,
        repo_root=ROOT,
    )


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
    return _sync_phase2_snapshot_impl(
        cfg=cfg,
        config_path=config_path,
        data_root=data_root,
        table_names=table_names,
        dry_run=dry_run,
        source=source,
        built_at=built_at,
        deps=SyncRuntimeDeps(
            repo_root=ROOT,
            table_order=TABLE_ORDER,
            table_schemas=TABLE_SCHEMAS,
            row_key_mapping_fieldnames=ROW_KEY_MAPPING_FIELDNAMES,
            provider_name=_provider_name,
            cli_bin=_cli_bin,
            selected_tables=_selected_tables,
            collect_sync_preflight_errors=collect_sync_preflight_errors,
            resolve_phase2_export_root=resolve_phase2_export_root,
            resolve_phase2_manifest_path=resolve_phase2_manifest_path,
            phase2_base_token=_phase2_base_token,
            phase2_identity=_phase2_identity,
            source_factory=lambda *, cli_bin, identity: LarkCliSource(cli_bin=cli_bin, identity=identity),
            resolve_table_binding=resolve_table_binding,
            normalize_records=normalize_records,
            csv_text=_csv_text,
            sha256_text=_sha256_text,
            sha256_file=_sha256_file,
            resolve_data_snapshot_paths=resolve_data_snapshot_paths,
            read_existing_mapping_rows=_read_existing_mapping_rows,
            build_row_label_row_key_mapping_rows=build_row_label_row_key_mapping_rows,
            dict_rows_csv_text=_dict_rows_csv_text,
            write_atomic_text=_write_atomic_text,
            table_sync_result_cls=TableSyncResult,
            sync_run_result_cls=SyncRunResult,
        ),
    )


def parse_args(argv: list[str] | None = None):
    return _parse_args_impl(argv, table_choices=list(TABLE_ORDER))


def main(argv: list[str] | None = None) -> int:
    return _run_main_impl(
        argv,
        root=ROOT,
        table_choices=list(TABLE_ORDER),
        load_config_fn=load_config,
        sync_phase2_snapshot_fn=sync_phase2_snapshot,
        build_sync_run_output_lines_fn=build_sync_run_output_lines,
    )


if __name__ == "__main__":
    raise SystemExit(main())
