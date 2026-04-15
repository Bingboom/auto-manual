#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class _TableSyncResultLike(Protocol):
    logical_name: str
    row_count: int
    changed: bool
    previous_sha256: str | None
    sha256: str
    target_path: Path


class _SyncRunResultLike(Protocol):
    dry_run: bool
    provider: str
    export_root: Path
    manifest_path: Path
    skipped_tables: tuple[str, ...]
    synced_tables: tuple[_TableSyncResultLike, ...]
    derived_files: tuple[_TableSyncResultLike, ...]


def build_sync_run_output_lines(result: _SyncRunResultLike) -> list[str]:
    lines = [
        f"[sync-data] {'DRY-RUN' if result.dry_run else 'SYNCED'} provider={result.provider} export_root={result.export_root}"
    ]
    for table in result.synced_tables:
        old_sha = table.previous_sha256 or "-"
        lines.append(
            "[sync-data] "
            f"{table.logical_name}: rows={table.row_count} changed={'yes' if table.changed else 'no'} "
            f"old_sha={old_sha} new_sha={table.sha256} path={table.target_path}"
        )
    for derived in result.derived_files:
        old_sha = derived.previous_sha256 or "-"
        lines.append(
            "[sync-data] "
            f"{derived.logical_name}: rows={derived.row_count} changed={'yes' if derived.changed else 'no'} "
            f"old_sha={old_sha} new_sha={derived.sha256} path={derived.target_path}"
        )
    lines.append(f"[sync-data] manifest={result.manifest_path}")
    if result.skipped_tables:
        lines.append(f"[sync-data] skipped_tables={','.join(result.skipped_tables)}")
    return lines
