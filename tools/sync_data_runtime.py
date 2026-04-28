#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Protocol


class _SchemaLike(Protocol):
    file_name: str


class _BindingLike(Protocol):
    base_token: str
    table_id: str
    view_id: str | None
    schema: _SchemaLike


class _RecordSourceLike(Protocol):
    def fetch_records(
        self,
        *,
        base_token: str,
        table_id: str,
        view_id: str | None,
    ) -> list[dict[str, Any]]:
        ...


class _RecordSourceWithIdsLike(_RecordSourceLike, Protocol):
    def fetch_records_with_ids(
        self,
        *,
        base_token: str,
        table_id: str,
        view_id: str | None,
    ) -> list[dict[str, Any]]:
        ...


class _DriveFileDownloaderLike(_RecordSourceLike, Protocol):
    def download_drive_file(
        self,
        *,
        file_token: str,
        output_path: Path,
        overwrite: bool = False,
    ) -> None:
        ...


class _TableSyncResultLike(Protocol):
    logical_name: str
    file_name: str
    target_path: Path
    row_count: int
    sha256: str
    previous_sha256: str | None
    changed: bool


@dataclass(frozen=True)
class SyncRuntimeDeps:
    repo_root: Path
    table_order: tuple[str, ...]
    row_key_mapping_fieldnames: tuple[str, ...]
    provider_name: Callable[..., str]
    cli_bin: Callable[..., str]
    selected_tables: Callable[..., tuple[str, ...]]
    collect_sync_preflight_errors: Callable[..., list[str]]
    resolve_phase2_export_root: Callable[..., Path]
    resolve_phase2_manifest_path: Callable[..., Path]
    phase2_identity: Callable[..., str]
    source_factory: Callable[..., _RecordSourceLike]
    resolve_table_binding: Callable[..., _BindingLike]
    normalize_records: Callable[..., list[dict[str, str]]]
    csv_text: Callable[..., str]
    sha256_text: Callable[..., str]
    sha256_file: Callable[..., str | None]
    resolve_data_snapshot_paths: Callable[..., Any]
    read_existing_mapping_rows: Callable[..., list[dict[str, str]]]
    build_row_label_row_key_mapping_rows: Callable[..., list[dict[str, str]]]
    dict_rows_csv_text: Callable[..., str]
    write_atomic_text: Callable[..., None]
    table_sync_result_cls: Callable[..., Any]
    sync_run_result_cls: Callable[..., Any]


def _display_path(path: Path, *, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix() if path.is_relative_to(repo_root) else path.as_posix()


def resolve_existing_row_key_mapping_path(
    cfg: dict[str, Any],
    *,
    data_root: str | None,
    target_path: Path,
    repo_root: Path,
    resolve_data_snapshot_paths_fn: Callable[..., Any],
) -> Path:
    if target_path.exists():
        return target_path

    default_path = resolve_data_snapshot_paths_fn(
        cfg,
        repo_root=repo_root,
        data_root=None,
    ).row_key_mapping_csv
    if default_path == target_path:
        return target_path
    if default_path.exists():
        return default_path
    return target_path


def manifest_payload(
    *,
    export_root: Path,
    manifest_path: Path,
    provider: str,
    cli_bin: str,
    requested_tables: tuple[str, ...],
    skipped_tables: tuple[str, ...],
    synced_tables: tuple[_TableSyncResultLike, ...],
    derived_files: tuple[_TableSyncResultLike, ...],
    built_at: datetime,
    dry_run: bool,
    repo_root: Path,
) -> dict[str, Any]:
    def _result_entry(result: _TableSyncResultLike) -> dict[str, Any]:
        return {
            "logical_name": result.logical_name,
            "file_name": result.file_name,
            "path": _display_path(result.target_path, repo_root=repo_root),
            "row_count": result.row_count,
            "sha256": result.sha256,
            "previous_sha256": result.previous_sha256,
            "changed": result.changed,
        }

    return {
        "provider": provider,
        "cli_bin": cli_bin,
        "generated_at": built_at.isoformat(),
        "export_root": _display_path(export_root, repo_root=repo_root),
        "manifest_path": _display_path(manifest_path, repo_root=repo_root),
        "dry_run": dry_run,
        "requested_tables": list(requested_tables),
        "skipped_tables": list(skipped_tables),
        "tables": [_result_entry(result) for result in synced_tables],
        "derived_files": [_result_entry(result) for result in derived_files],
    }


def _record_source_with_ids(source: _RecordSourceLike) -> _RecordSourceWithIdsLike | None:
    fetch_records_with_ids = getattr(source, "fetch_records_with_ids", None)
    if not callable(fetch_records_with_ids):
        return None
    return source  # type: ignore[return-value]


def _footnote_record_id_to_id_map(raw_records: list[dict[str, Any]]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for record in raw_records:
        record_id = str(record.get("record_id") or "").strip()
        fields_raw = record.get("fields")
        fields = fields_raw if isinstance(fields_raw, dict) else {}
        footnote_id = str(fields.get("Footnote_id") or fields.get("footnote_id") or "").strip()
        if record_id and footnote_id:
            mapping[record_id] = footnote_id
    return mapping


def _record_id_from_ref_token(token: str) -> str | None:
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


def _normalize_footnote_ref_value(value: str, mapping: dict[str, str]) -> str:
    raw = (value or "").strip()
    if not raw:
        return value

    refs: list[str] = []
    for token in raw.split(","):
        item = token.strip()
        if not item:
            continue
        mapped = mapping.get(_record_id_from_ref_token(item) or "", item)
        if mapped not in refs:
            refs.append(mapped)
    return ", ".join(refs)


def _normalize_spec_master_footnote_refs(
    rows: list[dict[str, str]],
    *,
    footnote_record_id_map: dict[str, str],
) -> None:
    if not footnote_record_id_map:
        return
    for row in rows:
        for column in (
            "Row_label_footnote_refs",
            "Param_footnote_refs",
            "Value_footnote_refs",
        ):
            row[column] = _normalize_footnote_ref_value(
                str(row.get(column) or ""),
                footnote_record_id_map,
            )


def _drive_file_downloader(source: _RecordSourceLike) -> _DriveFileDownloaderLike | None:
    download_drive_file = getattr(source, "download_drive_file", None)
    if not callable(download_drive_file):
        return None
    return source  # type: ignore[return-value]


def _safe_filename_part(value: str, *, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", (value or "").strip())
    cleaned = cleaned.strip("._-")
    return cleaned or fallback


def _attachment_items_from_cell(value: str) -> list[dict[str, Any]]:
    raw = (value or "").strip()
    if not raw:
        return []
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return []
    items = payload if isinstance(payload, list) else [payload]
    return [item for item in items if isinstance(item, dict)]


def _extension_from_attachment(item: dict[str, Any]) -> str:
    name = str(item.get("name") or item.get("file_name") or "").strip()
    suffix = Path(name).suffix.lower()
    if suffix:
        return suffix
    mime_type = str(item.get("mime_type") or item.get("type") or "").strip().lower()
    return {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/svg+xml": ".svg",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }.get(mime_type, ".png")


def _lcd_icon_attachment_path(
    row: dict[str, str],
    item: dict[str, Any],
    *,
    export_root: Path,
) -> Path | None:
    file_token = str(item.get("file_token") or item.get("token") or "").strip()
    if not file_token:
        return None
    no_part = _safe_filename_part(row.get("No.") or row.get("No") or "", fallback="row")
    name_part = _safe_filename_part(row.get("icon_en") or "", fallback="icon")
    token_part = _safe_filename_part(file_token, fallback="file")
    return export_root / "_attachments" / "lcd_icons" / f"{no_part}_{name_part}_{token_part}{_extension_from_attachment(item)}"


def _symbols_attachment_path(
    row: dict[str, str],
    item: dict[str, Any],
    *,
    export_root: Path,
) -> Path | None:
    file_token = str(item.get("file_token") or item.get("token") or "").strip()
    if not file_token:
        return None
    order_part = _safe_filename_part(row.get("order") or "", fallback="row")
    key_part = _safe_filename_part(row.get("symbol_key") or "", fallback="symbol")
    token_part = _safe_filename_part(file_token, fallback="file")
    return export_root / "_attachments" / "symbols" / f"{order_part}_{key_part}_{token_part}{_extension_from_attachment(item)}"


def _materialize_lcd_icon_attachments(
    rows: list[dict[str, str]],
    *,
    export_root: Path,
    repo_root: Path,
    source: _RecordSourceLike,
    dry_run: bool,
) -> None:
    downloader = _drive_file_downloader(source)

    for row in rows:
        items = _attachment_items_from_cell(row.get("figure", ""))
        if not items:
            continue
        target_path = _lcd_icon_attachment_path(row, items[0], export_root=export_root)
        if target_path is None:
            continue
        row["figure"] = _display_path(target_path, repo_root=repo_root)
        if dry_run:
            continue
        if downloader is None:
            raise RuntimeError("lcd_icons figure attachments require the sync source to support drive file downloads")
        downloader.download_drive_file(
            file_token=str(items[0].get("file_token") or items[0].get("token") or "").strip(),
            output_path=target_path,
            overwrite=True,
        )


def _materialize_symbols_attachments(
    rows: list[dict[str, str]],
    *,
    export_root: Path,
    repo_root: Path,
    source: _RecordSourceLike,
    dry_run: bool,
) -> None:
    downloader = _drive_file_downloader(source)

    for row in rows:
        items = _attachment_items_from_cell(row.get("Figure") or row.get("figure") or "")
        if not items:
            continue
        target_path = _symbols_attachment_path(row, items[0], export_root=export_root)
        if target_path is None:
            continue
        display_path = _display_path(target_path, repo_root=repo_root)
        row["Figure"] = display_path
        row["image_path"] = display_path
        if dry_run:
            continue
        if downloader is None:
            raise RuntimeError("symbols_blocks Figure attachments require the sync source to support drive file downloads")
        downloader.download_drive_file(
            file_token=str(items[0].get("file_token") or items[0].get("token") or "").strip(),
            output_path=target_path,
            overwrite=True,
        )


def sync_phase2_snapshot(
    *,
    cfg: dict[str, Any],
    config_path: Path,
    data_root: str | None = None,
    table_names: list[str] | None = None,
    dry_run: bool = False,
    source: _RecordSourceLike | None = None,
    built_at: datetime | None = None,
    deps: SyncRuntimeDeps,
) -> Any:
    del config_path

    provider = deps.provider_name(cfg)
    if provider != "lark_cli":
        raise RuntimeError(f"Unsupported sync provider implementation: {provider}")
    cli_bin = deps.cli_bin(cfg)
    selected_tables = deps.selected_tables(table_names or [])
    preflight_errors = deps.collect_sync_preflight_errors(
        cfg,
        table_names=selected_tables,
        require_cli=source is None,
    )
    if preflight_errors:
        raise RuntimeError("sync-data preflight failed:\n- " + "\n- ".join(preflight_errors))

    export_root = deps.resolve_phase2_export_root(cfg, repo_root=deps.repo_root, data_root=data_root)
    manifest_path = deps.resolve_phase2_manifest_path(cfg, repo_root=deps.repo_root, data_root=data_root)
    resolved_source = source or deps.source_factory(cli_bin=cli_bin, identity=deps.phase2_identity())
    run_at = built_at or datetime.now(timezone.utc)

    table_results: list[Any] = []
    derived_results: list[Any] = []
    written_files: list[tuple[Path, str]] = []
    bindings_by_table: dict[str, _BindingLike] = {}
    raw_records_by_table: dict[str, list[dict[str, Any]]] = {}
    normalized_rows_by_table: dict[str, list[dict[str, str]]] = {}

    for logical_name in selected_tables:
        binding = deps.resolve_table_binding(cfg, logical_name)
        bindings_by_table[logical_name] = binding
        source_with_ids = _record_source_with_ids(resolved_source)
        if logical_name == "spec_footnotes" and source_with_ids is not None:
            raw_records = source_with_ids.fetch_records_with_ids(
                base_token=binding.base_token,
                table_id=binding.table_id,
                view_id=binding.view_id,
            )
        else:
            raw_records = resolved_source.fetch_records(
                base_token=binding.base_token,
                table_id=binding.table_id,
                view_id=binding.view_id,
            )
        raw_records_by_table[logical_name] = raw_records
        normalized_rows = deps.normalize_records(binding.schema, raw_records)
        normalized_rows_by_table[logical_name] = normalized_rows

    if "spec_master" in normalized_rows_by_table:
        if "spec_footnotes" in raw_records_by_table:
            _normalize_spec_master_footnote_refs(
                normalized_rows_by_table["spec_master"],
                footnote_record_id_map=_footnote_record_id_to_id_map(raw_records_by_table["spec_footnotes"]),
            )

    if "lcd_icons" in normalized_rows_by_table:
        _materialize_lcd_icon_attachments(
            normalized_rows_by_table["lcd_icons"],
            export_root=export_root,
            repo_root=deps.repo_root,
            source=resolved_source,
            dry_run=dry_run,
        )

    if "symbols_blocks" in normalized_rows_by_table:
        _materialize_symbols_attachments(
            normalized_rows_by_table["symbols_blocks"],
            export_root=export_root,
            repo_root=deps.repo_root,
            source=resolved_source,
            dry_run=dry_run,
        )

    for logical_name in selected_tables:
        binding = bindings_by_table[logical_name]
        normalized_rows = normalized_rows_by_table[logical_name]
        csv_text = deps.csv_text(binding.schema, normalized_rows)
        sha256 = deps.sha256_text(csv_text)
        target_path = export_root / binding.schema.file_name
        previous_sha256 = deps.sha256_file(target_path)
        table_results.append(
            deps.table_sync_result_cls(
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
        snapshot_paths = deps.resolve_data_snapshot_paths(
            cfg,
            repo_root=deps.repo_root,
            data_root=str(export_root),
        )
        row_key_mapping_path = snapshot_paths.row_key_mapping_csv
        existing_mapping_path = resolve_existing_row_key_mapping_path(
            cfg,
            data_root=data_root,
            target_path=row_key_mapping_path,
            repo_root=deps.repo_root,
            resolve_data_snapshot_paths_fn=deps.resolve_data_snapshot_paths,
        )
        existing_mapping_rows = deps.read_existing_mapping_rows(existing_mapping_path)
        mapping_rows = deps.build_row_label_row_key_mapping_rows(
            normalized_rows_by_table["spec_master"],
            existing_rows=existing_mapping_rows,
        )
        mapping_csv_text = deps.dict_rows_csv_text(deps.row_key_mapping_fieldnames, mapping_rows)
        mapping_sha256 = deps.sha256_text(mapping_csv_text)
        previous_mapping_sha256 = deps.sha256_file(row_key_mapping_path)
        derived_results.append(
            deps.table_sync_result_cls(
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

    skipped_tables = tuple(name for name in deps.table_order if name not in selected_tables)
    manifest = manifest_payload(
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
        repo_root=deps.repo_root,
    )

    if not dry_run:
        for target_path, csv_text in written_files:
            deps.write_atomic_text(target_path, csv_text)
        deps.write_atomic_text(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    return deps.sync_run_result_cls(
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
