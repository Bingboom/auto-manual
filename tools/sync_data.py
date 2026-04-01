#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import shlex
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.data_snapshot import (  # noqa: E402
    resolve_phase2_export_root,
    resolve_phase2_manifest_path,
)

TABLE_ORDER = (
    "spec_titles",
    "spec_footnotes",
    "spec_notes",
    "symbols_blocks",
    "spec_master",
)
SUPPORTED_PROVIDERS = {"lark_cli", "lark-cli", "cli"}


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
    if not config_path.exists():
        raise RuntimeError(f"Config not found: {config_path}")
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover - matches existing repo behavior
        raise RuntimeError("PyYAML not installed. Please run: pip install pyyaml") from exc
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise RuntimeError(f"Config root must be a mapping: {config_path}")
    return data


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


def resolve_table_binding(cfg: dict[str, Any], logical_name: str) -> TableBinding:
    if logical_name not in TABLE_SCHEMAS:
        raise RuntimeError(f"Unknown sync table: {logical_name}")
    phase2_cfg = _sync_phase2_cfg(cfg)
    tables_cfg = _phase2_tables_cfg(cfg)
    table_cfg_raw = tables_cfg.get(logical_name, {})
    table_cfg = table_cfg_raw if isinstance(table_cfg_raw, dict) else {}

    base_token_env = str(
        table_cfg.get("base_token_env") or phase2_cfg.get("base_token_env") or ""
    ).strip()
    table_id_env = str(table_cfg.get("table_id_env") or "").strip()
    view_id_env = str(table_cfg.get("view_id_env") or "").strip() or None

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
    def __init__(self, *, cli_bin: str):
        self.cli_bin = cli_bin

    def _run_api(self, *, path: str, params: dict[str, Any]) -> dict[str, Any]:
        cmd = [
            *shlex.split(self.cli_bin),
            "api",
            "GET",
            path,
            "--format",
            "json",
        ]
        if params:
            cmd += ["--params", json.dumps(params, ensure_ascii=False, separators=(",", ":"))]
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

    def fetch_records(
        self,
        *,
        base_token: str,
        table_id: str,
        view_id: str | None,
    ) -> list[dict[str, Any]]:
        path = f"/open-apis/bitable/v1/apps/{base_token}/tables/{table_id}/records"
        records: list[dict[str, Any]] = []
        page_token: str | None = None
        while True:
            params: dict[str, Any] = {"page_size": 500}
            if view_id:
                params["view_id"] = view_id
            if page_token:
                params["page_token"] = page_token
            payload = self._run_api(path=path, params=params)
            data = payload.get("data")
            if not isinstance(data, dict):
                raise RuntimeError("Lark CLI API response is missing data payload")
            items = data.get("items", [])
            if not isinstance(items, list):
                raise RuntimeError("Lark CLI API response has invalid record list")
            for item in items:
                if not isinstance(item, dict):
                    raise RuntimeError("Lark CLI API response contains a non-object record")
                records.append(item)
            has_more = bool(data.get("has_more"))
            if not has_more:
                break
            next_page_token = str(data.get("page_token") or "").strip()
            if not next_page_token:
                raise RuntimeError("Lark CLI API response signaled pagination without page_token")
            page_token = next_page_token
        return records


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


def _normalized_cell(schema: TableSchema, column: str, raw_value: Any) -> str:
    value = _coerce_scalar(raw_value).replace("\r\n", "\n").replace("\r", "\n")
    if schema.logical_name == "spec_master" and column == "Is_Latest":
        return _normalize_boolish(value, style="upper_bool")
    if schema.logical_name in {"spec_footnotes", "spec_notes"} and column in {"Is_Latest", "Enabled"}:
        return _normalize_boolish(value, style="upper_bool")
    if schema.logical_name == "symbols_blocks" and column == "enabled":
        return _normalize_boolish(value, style="digit_bool")
    return value


def _record_values(record: dict[str, Any]) -> dict[str, Any]:
    fields_raw = record.get("fields", {})
    fields = fields_raw if isinstance(fields_raw, dict) else {}
    values = {str(key): value for key, value in record.items() if isinstance(key, str)}
    for key, value in fields.items():
        if isinstance(key, str):
            values[key] = value
    return values


def normalize_records(schema: TableSchema, raw_records: list[dict[str, Any]]) -> list[dict[str, str]]:
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


def _row_sort_key(schema: TableSchema, row: dict[str, str]) -> tuple[Any, ...]:
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
            _text_sort_token(row.get("column_group", "")),
            _numeric_sort_token(row.get("order", "")),
            _text_sort_token(row.get("symbol_key", "")),
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


def _csv_text(schema: TableSchema, rows: list[dict[str, str]]) -> str:
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=list(schema.columns), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({column: row.get(column, "") for column in schema.columns})
    return handle.getvalue()


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


def _manifest_payload(
    *,
    export_root: Path,
    manifest_path: Path,
    provider: str,
    cli_bin: str,
    requested_tables: tuple[str, ...],
    skipped_tables: tuple[str, ...],
    synced_tables: tuple[TableSyncResult, ...],
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
    export_root = resolve_phase2_export_root(cfg, repo_root=ROOT, data_root=data_root)
    manifest_path = resolve_phase2_manifest_path(cfg, repo_root=ROOT, data_root=data_root)
    resolved_source = source or LarkCliSource(cli_bin=cli_bin)
    run_at = built_at or datetime.now(timezone.utc)

    table_results: list[TableSyncResult] = []
    written_files: list[tuple[Path, str]] = []

    for logical_name in selected_tables:
        binding = resolve_table_binding(cfg, logical_name)
        raw_records = resolved_source.fetch_records(
            base_token=binding.base_token,
            table_id=binding.table_id,
            view_id=binding.view_id,
        )
        normalized_rows = normalize_records(binding.schema, raw_records)
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

    skipped_tables = tuple(name for name in TABLE_ORDER if name not in selected_tables)
    manifest = _manifest_payload(
        export_root=export_root,
        manifest_path=manifest_path,
        provider=provider,
        cli_bin=cli_bin,
        requested_tables=selected_tables,
        skipped_tables=skipped_tables,
        synced_tables=tuple(table_results),
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
        manifest=manifest,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Sync structured content snapshot CSVs from Feishu/Lark base tables.")
    ap.add_argument("--config", default="config.yaml", help="Config YAML path")
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
    print(f"[sync-data] manifest={result.manifest_path}")
    if result.skipped_tables:
        print(f"[sync-data] skipped_tables={','.join(result.skipped_tables)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
