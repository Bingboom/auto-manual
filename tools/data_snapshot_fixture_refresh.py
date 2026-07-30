#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Refresh one document target in the committed phase2 fixture snapshot.

The live ``data/phase2`` mirror is allowed to contain many products while the
CI fixture should stay small and deterministic.  This helper replaces only
the rows belonging to one ``document_key`` (plus shared rows) and refreshes
the manifest hashes without copying unrelated product rows.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.data_snapshot import (
    PHASE2_REQUIRED_DERIVED_FILES,
    PHASE2_REQUIRED_TABLE_FILES,
    SNAPSHOT_MANIFEST_FILE,
)

_TARGET_FIELDS = ("document_key", "Model", "Model_key", "Region", "Market")
_ATTACHMENT_MARKER = "data/phase2/_attachments/"


@dataclass(frozen=True)
class FixtureRefreshResult:
    document_key: str
    source_root: Path
    fixture_root: Path
    dry_run: bool
    changed_files: tuple[str, ...]
    refreshed_files: tuple[str, ...]
    skipped_files: tuple[str, ...]
    copied_attachments: tuple[str, ...]
    manifest_changed: bool
    rows_replaced: int
    rows_added: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "document_key": self.document_key,
            "source_root": str(self.source_root),
            "fixture_root": str(self.fixture_root),
            "dry_run": self.dry_run,
            "changed_files": list(self.changed_files),
            "refreshed_files": list(self.refreshed_files),
            "skipped_files": list(self.skipped_files),
            "copied_attachments": list(self.copied_attachments),
            "manifest_changed": self.manifest_changed,
            "rows_replaced": self.rows_replaced,
            "rows_added": self.rows_added,
        }


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        if not fieldnames:
            raise ValueError(f"CSV has no header: {path}")
        return fieldnames, [dict(row) for row in reader]


def _csv_text(fieldnames: list[str], rows: list[dict[str, str]]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
        extrasaction="ignore",
        lineterminator="\r\n",
    )
    writer.writeheader()
    writer.writerows({field: row.get(field, "") or "" for field in fieldnames} for row in rows)
    return output.getvalue()


def _write_atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="", dir=str(path.parent), delete=False
    ) as handle:
        handle.write(text)
        temporary = Path(handle.name)
    temporary.replace(path)


def _field_value(row: dict[str, str], name: str) -> str:
    expected = name.casefold()
    for key, value in row.items():
        if str(key).casefold() == expected:
            return str(value or "").strip()
    return ""


def _has_field(fieldnames: list[str], name: str) -> bool:
    expected = name.casefold()
    return any(str(field).casefold() == expected for field in fieldnames)


def _contains_token(value: str, token: str) -> bool:
    if not value or not token:
        return False
    pattern = rf"(?<![A-Za-z0-9]){re.escape(token)}(?![A-Za-z0-9])"
    return re.search(pattern, value, flags=re.IGNORECASE) is not None


def _target_parts(document_key: str) -> tuple[str, str]:
    parts = document_key.split("_")
    if len(parts) not in {2, 3}:
        raise ValueError(
            f"document_key must use MODEL_REGION or MODEL_REGION_SOURCE_LANG form, "
            f"got {document_key!r}"
        )
    model, region = parts[:2]
    if not model or not region:
        raise ValueError(
            f"document_key must use MODEL_REGION or MODEL_REGION_SOURCE_LANG form, "
            f"got {document_key!r}"
        )
    return model, region


def _is_global_row(row: dict[str, str], fieldnames: list[str]) -> bool:
    values = {_field_value(row, name).casefold() for name in _TARGET_FIELDS}
    values.discard("")
    if not values:
        return True
    return values <= {"all", "global", "*"}


def row_matches_document_key(
    row: dict[str, str],
    fieldnames: list[str],
    document_key: str,
    *,
    include_global: bool = True,
) -> bool:
    """Return whether a snapshot row belongs to one target or is shared."""
    model, region = _target_parts(document_key)
    document_value = _field_value(row, "document_key")
    if document_value:
        return document_value.casefold() == document_key.casefold()

    has_model = _has_field(fieldnames, "Model") or _has_field(fieldnames, "Model_key")
    has_region = _has_field(fieldnames, "Region")
    if has_model or has_region:
        row_model = _field_value(row, "Model") or _field_value(row, "Model_key")
        row_region = _field_value(row, "Region")
        model_match = not row_model or row_model.casefold() in {"all", "global", "*"}
        if row_model and not model_match:
            model_match = _contains_token(row_model, model)
        region_match = not row_region or row_region.casefold() in {"all", "global", "*"}
        if row_region and not region_match:
            region_match = _contains_token(row_region, region)
        if model_match and region_match and (row_model or row_region):
            return True
        return include_global and _is_global_row(row, fieldnames)

    return True


def _merge_fieldnames(source_fields: list[str], fixture_fields: list[str]) -> list[str]:
    """Use source order while retaining fixture-only compatibility columns."""
    merged = list(source_fields)
    merged.extend(field for field in fixture_fields if field not in merged)
    return merged


def _attachment_references(rows: list[dict[str, str]]) -> set[Path]:
    references: set[Path] = set()
    for row in rows:
        for value in row.values():
            text = str(value or "")
            if _ATTACHMENT_MARKER not in text:
                continue
            suffix = text.split(_ATTACHMENT_MARKER, 1)[1].split("\"", 1)[0]
            if suffix:
                references.add(Path("_attachments") / suffix)
    return references


def _copy_attachment(source_root: Path, fixture_root: Path, relative: Path, *, dry_run: bool) -> bool:
    source = source_root / relative
    destination = fixture_root / relative
    if not source.is_file():
        return False
    if destination.is_file() and destination.read_bytes() == source.read_bytes():
        return False
    if dry_run:
        return True
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.fixture-refresh.tmp")
    shutil.copyfile(source, temporary)
    temporary.replace(destination)
    return True


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv_row_count(path: Path) -> int | None:
    if path.suffix.casefold() != ".csv":
        return None
    _, rows = _read_csv(path)
    return len(rows)


def _read_text_preserving_newlines(path: Path) -> str:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return handle.read()


def _refresh_manifest(
    fixture_root: Path,
    *,
    dry_run: bool,
    planned_file_stats: dict[str, tuple[str, int | None]] | None = None,
) -> tuple[bool, list[str]]:
    manifest_path = fixture_root / SNAPSHOT_MANIFEST_FILE
    if not manifest_path.is_file():
        raise FileNotFoundError(f"fixture snapshot manifest not found: {manifest_path}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"fixture snapshot manifest root must be a mapping: {manifest_path}")

    changed = False
    changed_files: list[str] = []
    for bucket in ("tables", "derived_files"):
        entries = payload.get(bucket, [])
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            file_name = str(entry.get("file_name") or "").strip()
            if not file_name:
                continue
            path = fixture_root / file_name
            if not path.is_file():
                continue
            if planned_file_stats and file_name in planned_file_stats:
                current_sha, current_count = planned_file_stats[file_name]
            else:
                current_sha = _sha256(path)
                current_count = _csv_row_count(path)
            entry_changed = current_sha != str(entry.get("sha256") or "")
            if current_count is not None:
                entry_changed = entry_changed or current_count != entry.get("row_count")
            if not entry_changed:
                continue
            changed = True
            changed_files.append(file_name)
            if not dry_run:
                entry["previous_sha256"] = entry.get("sha256")
                entry["sha256"] = current_sha
                if current_count is not None:
                    entry["row_count"] = current_count
                entry["changed"] = True

    if changed and not dry_run:
        payload["generated_at"] = datetime.now(timezone.utc).isoformat()
        payload["dry_run"] = False
        _write_atomic_text(manifest_path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return changed, sorted(set(changed_files))


def refresh_fixture_by_document_key(
    *,
    source_root: Path,
    fixture_root: Path,
    document_key: str,
    write: bool = False,
) -> FixtureRefreshResult:
    """Plan or apply a target-scoped fixture refresh.

    ``write=False`` is a dry-run.  The source and fixture roots must be
    distinct, and a source row with no target match is never allowed to erase
    fixture rows for that target.
    """
    source_root = source_root.resolve()
    fixture_root = fixture_root.resolve()
    _target_parts(document_key)
    if source_root == fixture_root:
        raise ValueError("source_root and fixture_root must be different directories")
    if not source_root.is_dir():
        raise FileNotFoundError(f"source snapshot root not found: {source_root}")
    if not fixture_root.is_dir():
        raise FileNotFoundError(f"fixture snapshot root not found: {fixture_root}")

    changed_files: list[str] = []
    refreshed_files: list[str] = []
    skipped_files: list[str] = []
    copied_attachments: list[str] = []
    rows_replaced = 0
    rows_added = 0
    planned_file_stats: dict[str, tuple[str, int | None]] = {}

    file_names = tuple(dict.fromkeys((*PHASE2_REQUIRED_TABLE_FILES.values(), *PHASE2_REQUIRED_DERIVED_FILES.values())))
    target_rows_for_assets: list[dict[str, str]] = []
    for file_name in file_names:
        source_path = source_root / file_name
        fixture_path = fixture_root / file_name
        if not source_path.is_file() or not fixture_path.is_file():
            skipped_files.append(f"{file_name}: missing source or fixture file")
            continue

        source_fields, source_rows = _read_csv(source_path)
        fixture_fields, fixture_rows = _read_csv(fixture_path)
        source_matches = [
            row for row in source_rows
            if row_matches_document_key(row, source_fields, document_key)
        ]
        if not source_matches:
            skipped_files.append(f"{file_name}: no rows for {document_key}")
            continue

        source_global = not any(_has_field(source_fields, field) for field in _TARGET_FIELDS)
        fixture_matches = [
            index for index, row in enumerate(fixture_rows)
            if source_global or row_matches_document_key(row, fixture_fields, document_key)
        ]
        merged_fields = _merge_fieldnames(source_fields, fixture_fields)
        merged_rows = list(fixture_rows)
        if fixture_matches:
            first = fixture_matches[0]
            fixture_match_set = set(fixture_matches)
            merged_rows = [
                *fixture_rows[:first],
                *source_matches,
                *[
                    row
                    for index, row in enumerate(fixture_rows)
                    if index not in fixture_match_set and index >= first
                ],
            ]
            rows_replaced += len(fixture_matches)
            rows_added += len(source_matches)
        else:
            merged_rows.extend(source_matches)
            rows_added += len(source_matches)

        new_text = _csv_text(merged_fields, merged_rows)
        old_text = _read_text_preserving_newlines(fixture_path)
        refreshed_files.append(file_name)
        planned_file_stats[file_name] = (
            hashlib.sha256(new_text.encode("utf-8")).hexdigest(),
            len(merged_rows) if fixture_path.suffix.casefold() == ".csv" else None,
        )
        if new_text != old_text:
            changed_files.append(file_name)
            if write:
                _write_atomic_text(fixture_path, new_text)
        target_rows_for_assets.extend(source_matches)

    for relative in sorted(_attachment_references(target_rows_for_assets)):
        if _copy_attachment(source_root, fixture_root, relative, dry_run=not write):
            copied_attachments.append(relative.as_posix())

    manifest_changed, manifest_files = _refresh_manifest(
        fixture_root,
        dry_run=not write,
        planned_file_stats=planned_file_stats if not write else None,
    )
    changed_files.extend(manifest_files)
    if manifest_changed and SNAPSHOT_MANIFEST_FILE not in changed_files:
        changed_files.append(SNAPSHOT_MANIFEST_FILE)

    return FixtureRefreshResult(
        document_key=document_key,
        source_root=source_root,
        fixture_root=fixture_root,
        dry_run=not write,
        changed_files=tuple(sorted(set(changed_files))),
        refreshed_files=tuple(sorted(set(refreshed_files))),
        skipped_files=tuple(sorted(skipped_files)),
        copied_attachments=tuple(copied_attachments),
        manifest_changed=manifest_changed,
        rows_replaced=rows_replaced,
        rows_added=rows_added,
    )


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Refresh one document_key in the CI phase2 fixture snapshot.")
    parser.add_argument("--source-root", type=Path, default=Path("data/phase2"))
    parser.add_argument("--fixture-root", type=Path, default=Path("tests/fixtures/phase2"))
    parser.add_argument("--document-key", required=True)
    parser.add_argument("--write", action="store_true", help="Apply the refresh; default is dry-run.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    result = refresh_fixture_by_document_key(
        source_root=args.source_root,
        fixture_root=args.fixture_root,
        document_key=args.document_key,
        write=args.write,
    )
    if args.as_json:
        print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
    else:
        mode = "WROTE" if args.write else "DRY-RUN"
        print(f"[fixture-refresh] {mode} document_key={result.document_key}")
        print(f"[fixture-refresh] refreshed={len(result.refreshed_files)} changed={len(result.changed_files)}")
        print(f"[fixture-refresh] rows_replaced={result.rows_replaced} rows_added={result.rows_added}")
        if result.skipped_files:
            print(f"[fixture-refresh] skipped={len(result.skipped_files)}")
        if result.copied_attachments:
            print(f"[fixture-refresh] attachments={len(result.copied_attachments)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
