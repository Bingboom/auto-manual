"""Mirror the Feishu asset-definition table into the tracked build registry.

``data/asset_registry.csv`` is the control plane the asset resolver reads
(tools/asset_registry.py). Two authorities meet in that one file:

* the Feishu ``04_资产定义`` table owns *what an asset is and whether it may
  build* — category, language dimension, status, scopes, textless debt;
* the repository owns *which export files exist* (``导出物路径`` and
  ``内容哈希`` describe committed bytes) and the maintenance history in
  ``备注`` — the Base's own notes are intake/gate rationale, a different
  record that must not overwrite it.

So sync-data overlays only the first set, and never deletes: an asset
vanishing from the Base must not silently drop a registry row that
templates still resolve through. The merged CSV is parsed back with the
resolver's own loader before it is written, so bad Base data fails the
sync instead of landing a registry the build would reject later.

Table coordinates come from the frozen ``data/asset_base_bindings.json``
(the Phase B artifact) rather than a new secret, with an env override for
tenants whose asset tables live elsewhere.
"""
from __future__ import annotations

import csv
import io
import json
from typing import Any, NamedTuple

from tools.utils.path_utils import PathSegments

BINDINGS_FILE_NAME = "asset_base_bindings.json"
DEFINITIONS_TABLE_KEY = "asset_definitions"

# Feishu field -> registry column. Columns outside this map stay
# repo-owned; see the module docstring.
OWNED_COLUMNS: tuple[tuple[str, str], ...] = (
    ("category", "类别"),
    ("language_dimension", "语言维度"),
    ("status", "状态"),
    ("textless_pending", "待无字化"),
    ("model_scope", "适用机型"),
    ("region_scope", "适用区域"),
    ("language_variants", "语言变体"),
)
_CHECKBOX_COLUMNS = frozenset({"待无字化"})


class MergeStats(NamedTuple):
    """What the overlay changed, for the sync log."""

    updated: tuple[str, ...]
    appended: tuple[str, ...]
    managed: int


def _text(value: Any) -> str:
    """Flatten one Feishu cell to its registry-CSV spelling.

    Rich text arrives as segments that concatenate; select fields arrive as
    a list of option names that join with the registry's comma separator.
    """
    if isinstance(value, list):
        if all(isinstance(seg, dict) for seg in value):
            return "".join(str(seg.get("text") or "") for seg in value).strip()
        parts = (str(seg).strip() for seg in value)
        return ",".join(part for part in parts if part)
    if value is None:
        return ""
    if value is True:
        return "TRUE"
    if value is False:
        return "FALSE"
    return str(value).strip()


def definition_rows(records: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    """Raw definition records -> asset_key -> the Base-owned columns."""
    rows: dict[str, dict[str, str]] = {}
    for record in records:
        fields = record.get("fields", record)
        asset_key = _text(fields.get("asset_key"))
        if not asset_key:
            continue
        row: dict[str, str] = {}
        for field, column in OWNED_COLUMNS:
            value = _text(fields.get(field))
            if not value and column in _CHECKBOX_COLUMNS:
                value = "FALSE"
            row[column] = value
        rows[asset_key] = row
    return rows


def merge_registry_csv(
    existing_text: str, records: list[dict[str, Any]]
) -> tuple[str, MergeStats]:
    """Overlay the Base-owned columns onto the tracked registry CSV.

    Existing column and row order are preserved so the git diff shows only
    what the Base actually changed; unmanaged rows pass through untouched.
    """
    reader = csv.DictReader(io.StringIO(existing_text, newline=""))
    fieldnames = list(reader.fieldnames or ())
    if not fieldnames:
        raise ValueError("asset registry CSV has no header row")
    missing = [column for _, column in OWNED_COLUMNS if column not in fieldnames]
    if missing:
        raise ValueError(
            f"asset registry CSV is missing columns: {', '.join(missing)}"
        )
    rows: list[dict[str, str]] = []
    for raw in reader:
        raw.pop(None, None)  # tolerate a stray unquoted comma rather than crash
        rows.append({name: (raw.get(name) or "") for name in fieldnames})

    overlay = definition_rows(records)
    updated: list[str] = []
    seen: set[str] = set()
    for row in rows:
        asset_key = row["asset_key"].strip()
        managed = overlay.get(asset_key)
        if managed is None:
            continue
        seen.add(asset_key)
        if any(row[column] != value for column, value in managed.items()):
            updated.append(asset_key)
        row.update(managed)

    appended: list[str] = []
    for asset_key in sorted(set(overlay) - seen):
        new_row = {name: "" for name in fieldnames}
        new_row["asset_key"] = asset_key
        new_row.update(overlay[asset_key])
        rows.append(new_row)
        appended.append(asset_key)

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue(), MergeStats(
        updated=tuple(updated), appended=tuple(appended), managed=len(overlay)
    )


def _bindings_table(repo_root: Any) -> tuple[str, str | None]:
    """Read the frozen table/view coordinates for the definition table."""
    bindings_path = repo_root / PathSegments.DATA / BINDINGS_FILE_NAME
    if not bindings_path.exists():
        raise RuntimeError(
            "sync.phase2.asset_registry is configured but "
            f"{bindings_path} is missing and no table_id_env is set"
        )
    payload = json.loads(bindings_path.read_text(encoding="utf-8"))
    table = (payload.get("tables") or {}).get(DEFINITIONS_TABLE_KEY) or {}
    table_id = str(table.get("table_id") or "").strip()
    if not table_id:
        raise RuntimeError(
            f"{bindings_path} has no {DEFINITIONS_TABLE_KEY}.table_id"
        )
    view_id = str(table.get("default_view_id") or "").strip() or None
    return table_id, view_id


def sync_asset_registry_mirror(
    cfg: dict[str, Any],
    *,
    source: Any,
    repo_root: Any,
    sha256_text: Any,
    sha256_file: Any,
    result_cls: Any,
):
    """Fetch the definition table and overlay the tracked registry CSV.

    Returns (result, (path, csv_text)) or (None, None) when the config
    block is absent, so older configs keep working unchanged.
    """
    import os

    phase2_cfg = (cfg.get("sync") or {}).get("phase2") or {}
    registry_cfg = phase2_cfg.get("asset_registry")
    if registry_cfg is None:
        return None, None
    if not isinstance(registry_cfg, dict):
        raise RuntimeError("sync.phase2.asset_registry must be a mapping")
    # An empty block is "enabled with the frozen coordinates", not "absent" —
    # this mirror needs no per-table env of its own.
    base_token_env = str(
        registry_cfg.get("base_token_env") or phase2_cfg.get("base_token_env") or ""
    ).strip()
    base_token = os.environ.get(base_token_env, "").strip() if base_token_env else ""
    if not base_token:
        raise RuntimeError(
            "sync.phase2.asset_registry is configured but "
            f"{base_token_env or 'base_token_env'} is not set in the environment"
        )
    table_id_env = str(registry_cfg.get("table_id_env") or "").strip()
    view_id_env = str(registry_cfg.get("view_id_env") or "").strip()
    table_id = os.environ.get(table_id_env, "").strip() if table_id_env else ""
    view_id = os.environ.get(view_id_env, "").strip() if view_id_env else ""
    if not table_id:
        # No secret required: Phase B froze these coordinates in the repo.
        table_id, bound_view_id = _bindings_table(repo_root)
        view_id = view_id or (bound_view_id or "")

    target_path = repo_root / PathSegments.DATA / "asset_registry.csv"
    if not target_path.exists():
        raise RuntimeError(f"asset registry mirror target is missing: {target_path}")
    records = source.fetch_records(
        base_token=base_token, table_id=table_id, view_id=view_id or None
    )
    csv_text, stats = merge_registry_csv(
        target_path.read_text(encoding="utf-8"), records
    )
    # Validate through the resolver's own parser: a bad Base row must fail
    # the sync, not land a registry the build would reject later.
    from tools.asset_registry import load_registry_bytes

    load_registry_bytes(csv_text.encode("utf-8"), source=target_path)

    if stats.updated or stats.appended:
        # The git diff is the review surface; this line just says where to look.
        print(
            f"[sync-data] asset registry: {len(stats.updated)} updated, "
            f"{len(stats.appended)} appended, {stats.managed} Base-managed"
        )
    sha256 = sha256_text(csv_text)
    previous_sha256 = sha256_file(target_path)
    result = result_cls(
        logical_name="asset_registry",
        file_name=target_path.name,
        target_path=target_path,
        row_count=max(0, csv_text.count("\n") - 1),
        sha256=sha256,
        previous_sha256=previous_sha256,
        changed=sha256 != previous_sha256,
    )
    return result, (target_path, csv_text)
