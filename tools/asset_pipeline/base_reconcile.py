"""Reconcile the staged 04_资产* rows with a read-only snapshot of the live tables.

The operator saves the snapshot with lark-cli, read-only (the recipe is in
code-as-doc/dev/asset_base_inventory.md §11): ``<table>_records_<n>.json``
pages from ``base +record-list --format json`` for each of ``sources``,
``definitions`` and ``exports``. This module only reads those files; it never
calls Feishu.

Each staged row gets an action: a Git file the Base already holds with the
same bytes is kept, or filled where the Base row has blanks; changed bytes
update the row's attachment; anything else is created. Proposed definitions
wait for registry promotion. What the Base and the repository disagree on is
reported, never overwritten.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
import json
from pathlib import Path
import re
from typing import Any

TABLES = ("sources", "definitions", "exports")
# The namespace of the Git-file rows already in 04_资产导出物; new Git-file rows use it too.
GIT_EXPORT_PREFIX = "registry::"
# Export fields a kept row may still be missing; filling them changes nothing else on the row.
FILLABLE_EXPORT_FIELDS = (
    "artifact_kind", "gate_status", "build_eligible", "visual_review_required", "size_bytes",
    "source_key", "source_page", "pixel_size", "has_alpha",
)
CHECKBOX_FIELDS = frozenset({"build_eligible", "visual_review_required", "has_alpha"})

_PAGE = re.compile(r"_records_(\d+)\.json$")

Finder = Callable[[str, str, str], None]


class SnapshotError(ValueError):
    """The live snapshot directory is missing a table or holds unreadable pages."""


def cell_text(value: Any) -> str:
    """One live cell as text: option lists join with commas, links give record ids, files give names."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, list):
        parts = (cell_text(item) for item in value)
        return ",".join(part for part in parts if part)
    if isinstance(value, dict):
        for key in ("text", "name", "id", "record_id", "file_token"):
            if value.get(key):
                return str(value[key]).strip()
        return ""
    return str(value).strip()


@dataclass(frozen=True)
class LiveRecord:
    record_id: str
    fields: dict[str, Any]

    def text(self, name: str) -> str:
        return cell_text(self.fields.get(name))


@dataclass
class LiveIndex:
    sources: dict[str, LiveRecord] = field(default_factory=dict)
    definitions: dict[str, LiveRecord] = field(default_factory=dict)
    # repo_path -> the Git-file row (export_key registry::<repo_path>)
    git_exports: dict[str, LiveRecord] = field(default_factory=dict)
    # repo_path -> intake or composite rows that name a repository file
    other_exports: dict[str, list[LiveRecord]] = field(default_factory=dict)
    duplicates: list[tuple[str, str]] = field(default_factory=list)


def _records(path: Path) -> list[LiveRecord]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))["data"]
        names = list(data["fields"])
        return [LiveRecord(str(record_id), dict(zip(names, values, strict=True)))
                for record_id, values in zip(data["record_id_list"], data["data"], strict=True)]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise SnapshotError(f"cannot read live snapshot page {path}: {exc}") from exc


def _page_number(path: Path) -> int:
    match = _PAGE.search(path.name)
    return int(match.group(1)) if match else -1


def _table(directory: Path, table: str) -> list[LiveRecord]:
    pages = sorted((path for path in directory.glob(f"{table}_records_*.json") if _page_number(path) >= 0),
                   key=_page_number)
    if not pages:
        raise SnapshotError(f"live snapshot {directory} has no {table}_records_<n>.json pages")
    return [record for path in pages for record in _records(path)]


def _keyed(records: Iterable[LiveRecord], key: str, index: LiveIndex, table: str) -> dict[str, LiveRecord]:
    keyed: dict[str, LiveRecord] = {}
    for record in records:
        value = record.text(key)
        if not value:
            continue
        if value in keyed:
            index.duplicates.append((table, value))
            continue
        keyed[value] = record
    return keyed


def load_snapshot(directory: Path) -> LiveIndex:
    """Index the three live tables by source_key, asset_key and repository path."""
    index = LiveIndex()
    index.sources = _keyed(_table(directory, "sources"), "source_key", index, "04_资产源文件")
    index.definitions = _keyed(_table(directory, "definitions"), "asset_key", index, "04_资产定义")
    git_rows, other_rows = [], []
    for record in _table(directory, "exports"):
        if not record.text("repo_path"):
            continue
        (git_rows if record.text("export_key").startswith(GIT_EXPORT_PREFIX) else other_rows).append(record)
    index.git_exports = _keyed(git_rows, "repo_path", index, "04_资产导出物")
    for record in other_rows:
        index.other_exports.setdefault(record.text("repo_path"), []).append(record)
    return index


def _needs_fill(live: LiveRecord, name: str, staged: str) -> bool:
    if not staged:
        return False
    if name in CHECKBOX_FIELDS:
        return staged == "TRUE" and live.text(name) != "TRUE"
    return not live.text(name)


def _export_action(row: dict[str, str], live: LiveRecord | None, find: Finder) -> None:
    if live is None:
        row.update(action="create", live_record_id="", fill_fields="")
        return
    row["live_record_id"] = live.record_id
    if live.text("content_sha256") != row["content_sha256"]:
        row.update(action="update-file", fill_fields="")
        find("stale-attachment", row["repo_path"], f"Base row {live.record_id} carries "
             f"{live.text('content_sha256')[:12]}, the file is {row['content_sha256'][:12]}")
        return
    blanks = [name for name in FILLABLE_EXPORT_FIELDS if _needs_fill(live, name, row.get(name, ""))]
    row.update(action="fill" if blanks else "keep", fill_fields=";".join(blanks))


def reconcile_exports(rows: list[dict[str, str]], index: LiveIndex, find: Finder) -> None:
    """Give each staged export its action against the Git-file rows the Base already holds."""
    staged = {row["repo_path"] for row in rows}
    for row in rows:
        live = index.git_exports.get(row["repo_path"])
        _export_action(row, live, find)
        if live is not None and live.text("asset_key") and live.text("asset_key") != row["asset_key"]:
            row["needs_review"] = "TRUE"
            find("live-key-differs", row["repo_path"],
                 f"Base row {live.record_id} uses {live.text('asset_key')}; the staged row uses {row['asset_key']}")
        for other in index.other_exports.get(row["repo_path"], ()):
            if other.text("content_sha256") != row["content_sha256"]:
                find("stale-intake-export", row["repo_path"], f"{other.text('export_key')} carries "
                     f"{other.text('content_sha256')[:12]}, the file is now {row['content_sha256'][:12]}")
    for repo_path, live in sorted(index.git_exports.items()):
        if repo_path not in staged:
            find("orphan-export", repo_path, f"Base row {live.record_id} names a file the four folders no longer hold")


def reconcile_definitions(rows: dict[str, dict[str, Any]], index: LiveIndex, registry_keys: set[str],
                          drift: Callable[[str, LiveRecord], list[str]], find: Finder) -> None:
    """Definitions already in the Base are kept; registry rows are created; proposals wait for promotion."""
    for key, row in rows.items():
        live = index.definitions.get(key)
        if live is not None:
            row.update(action="keep", live_record_id=live.record_id)
            differences = drift(key, live) if key in registry_keys else []
            if differences:
                find("base-drift", key, "the next sync-data writes the Base values into the registry: "
                     + "; ".join(differences))
            continue
        row.update(action="create" if key in registry_keys else "propose", live_record_id="")
    for key in sorted(set(index.definitions) - registry_keys):
        find("base-only-definition", key, "the next sync-data appends this Base definition to the registry")


def reconcile_sources(rows: dict[str, dict[str, Any]], index: LiveIndex) -> None:
    for key, row in rows.items():
        live = index.sources.get(key)
        if live is None:
            row.update(action="create", live_record_id="")
        else:
            # A kept master stays as the Base has it, archive status included.
            row.update(action="keep", live_record_id=live.record_id, archive_status=live.text("archive_status"))


def report_duplicates(index: LiveIndex, find: Finder) -> None:
    for table, key in index.duplicates:
        find("duplicate-live-row", key, f"{table} holds more than one row for this key; only the first is used")


__all__ = [
    "GIT_EXPORT_PREFIX", "LiveIndex", "LiveRecord", "SnapshotError", "cell_text", "load_snapshot",
    "reconcile_definitions", "reconcile_exports", "reconcile_sources", "report_duplicates",
]
