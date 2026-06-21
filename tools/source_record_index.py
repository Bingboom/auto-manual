"""Source record index sidecar (Milestone F, PR F1).

`sync-data` can emit a ``source_record_index.json`` sidecar next to the phase2
CSV snapshot. The sidecar maps each indexed source table's business key to its
live Feishu ``record_id`` so that downstream consumers (``content_lint`` today,
the approval-gated backport writer later) can resolve a finding to an exact live
row.

Design constraints (see ``code-as-doc/dev/closed_loop_qc_implementation_plan.md``
M2 and ``code-as-doc/architecture/Feishu_Cloud_Doc_Backport_Design.md`` R9):

- **No CSV schema change.** The sidecar is a separate file; no ``record_id``
  column is added to any existing CSV contract.
- **Exact-or-abstain.** A key that maps to zero rows resolves to ``unresolved``;
  a key that maps to more than one distinct ``record_id`` resolves to
  ``ambiguous``. The sidecar never guesses.
- **Optional derived file.** It is not in ``PHASE2_REQUIRED_DERIVED_FILES`` and a
  snapshot without it is still valid; consumers degrade to ``snapshot_only``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SIDECAR_FILENAME = "source_record_index.json"
SCHEMA_VERSION = "source-record-index/v1"

# Reserved key under which `normalize_records` stows a row's live Feishu record_id so it
# **travels with the row through the normalize-time sort** (the row's business key and its
# record_id must stay together). Not a CSV column — the CSV writers filter to the schema's
# columns, so it never leaks into the snapshot.
SOURCE_RECORD_ID_KEY = "__source_record_id__"

# Unit Separator. Unlikely to appear inside a business-key value, so it makes a
# stable composite-key string for JSON object keys.
_KEY_SEP = "\x1f"

# index table name -> the CSV columns whose tuple uniquely identifies a row.
# Keep the column names identical to what ``content_lint`` reads from the CSV.
TABLE_KEY_FIELDS: dict[str, tuple[str, ...]] = {
    # icon_en + Model + Version uniquely identifies an LCD icon row.
    "lcd_icons_blocks": ("icon_en", "Model", "Version"),
    # document_key + Row_key + Slot_key uniquely identifies a Spec_Master row
    # (Slot_key disambiguates the usb_c 30w/100w collision class).
    "Spec_Master": ("document_key", "Row_key", "Slot_key"),
    # copy_key identifies the authoring row in Manual_Copy_Source. A
    # Localized_Copy value (the rendered derivative) is written back here by
    # copy_key (operator decision: source-of-truth is the authoring table, not
    # the localized derivative). Historical rows are filtered out at index time
    # (see TABLE_ROW_FILTERS) so only the current authoring row is keyed; a
    # genuine cross-row copy_key collision still abstains.
    "Manual_Copy_Source": ("copy_key",),
}

# sync logical table name -> index table name used in the sidecar / source_ref.
INDEXED_LOGICAL_TABLES: dict[str, str] = {
    "lcd_icons": "lcd_icons_blocks",
    "spec_master": "Spec_Master",
    "manual_copy_source": "Manual_Copy_Source",
}

# content_lint source_ref ``kind`` -> (index table, ((source_ref_field, key_field), ...)).
# The key_field order must match ``TABLE_KEY_FIELDS`` for that table so the
# composite key built here matches the one built at sync time.
KIND_RESOLUTION: dict[str, tuple[str, tuple[tuple[str, str], ...]]] = {
    "lcd_icon": (
        "lcd_icons_blocks",
        (("key", "icon_en"), ("model", "Model"), ("version", "Version")),
    ),
}


# Resolve a source_ref by its ``table`` directly, for F2/F6 source_refs that
# carry a table + key fields but no content_lint ``kind``. The map value is
# ``(index_table, ((source_ref_field, index_key_field), ...))`` so the *origin*
# table named in a source_ref can resolve against a *different* index table — a
# Localized_Copy-origin value writes back to its Manual_Copy_Source authoring
# row. The index-key-field order must match that index table's
# ``TABLE_KEY_FIELDS``.
TABLE_RESOLUTION: dict[str, tuple[str, tuple[tuple[str, str], ...]]] = {
    "Spec_Master": (
        "Spec_Master",
        (("document_key", "document_key"), ("row_key", "Row_key"), ("slot_key", "Slot_key")),
    ),
    "Localized_Copy": ("Manual_Copy_Source", (("copy_key", "copy_key"),)),
}


def _is_latest(row: dict[str, Any]) -> bool:
    """Whether an authoring row is the current version.

    Coverage-safe: a row is treated as current unless ``Is_Latest`` is an
    explicit false-marker. A blank/absent column keeps the row (the snapshot may
    not populate it), so the filter never silently empties an index — genuine
    duplicate keys still abstain downstream.
    """

    raw = _clean(row.get("Is_Latest")).lower()
    return raw not in {"false", "0", "no", "n", "off"}


# Optional per-index-table row predicate applied when collecting index rows.
# A row that fails the predicate is not indexed, so non-current authoring rows
# never shadow the current row nor create false ambiguity.
TABLE_ROW_FILTERS: dict[str, Any] = {
    "Manual_Copy_Source": _is_latest,
}


def _join_key(values: list[str]) -> str:
    return _KEY_SEP.join(values)


def _clean(value: Any) -> str:
    return str(value if value is not None else "").strip()


def build_index(rows_by_table: dict[str, list[tuple[dict[str, Any], str]]]) -> dict[str, Any]:
    """Build the sidecar payload.

    ``rows_by_table`` maps an index table name to a list of
    ``(normalized_row, record_id)`` pairs. ``normalized_row`` uses the same column
    names as the emitted CSV.
    """

    tables: dict[str, Any] = {}
    for table, key_fields in TABLE_KEY_FIELDS.items():
        pairs = rows_by_table.get(table) or []
        records: dict[str, str] = {}
        ambiguous: set[str] = set()
        for row, record_id in pairs:
            rid = _clean(record_id)
            values = [_clean(row.get(field)) for field in key_fields]
            if not rid or not all(values):
                # Incomplete key or missing id -> cannot resolve safely: abstain.
                continue
            key = _join_key(values)
            existing = records.get(key)
            if existing is None and key not in ambiguous:
                records[key] = rid
            elif existing is not None and existing != rid:
                ambiguous.add(key)
        for key in ambiguous:
            records.pop(key, None)
        tables[table] = {
            "key_fields": list(key_fields),
            "records": records,
            "ambiguous": sorted(ambiguous),
        }
    return {"schema_version": SCHEMA_VERSION, "tables": tables}


def collect_index_rows(
    normalized_rows_by_table: dict[str, list[dict[str, Any]]],
    raw_records_by_table: dict[str, list[dict[str, Any]]],
) -> dict[str, list[tuple[dict[str, Any], str]]]:
    """Pair normalized rows with their live ``record_id``, keyed by index table.

    The record_id is read from the row's ``SOURCE_RECORD_ID_KEY`` — which
    ``normalize_records`` threads onto each row so it **survives the normalize-time
    sort** (a row's business key and its record_id must stay together; pairing the
    *sorted* normalized list positionally with the *unsorted* raw records mapped each
    key to the wrong record). It falls back to positional pairing with ``raw_records``
    only for rows that do not carry the key (legacy callers / a fetch without ids).
    Raw records without a ``record_id`` contribute an empty id, which ``build_index``
    then abstains on.
    """

    out: dict[str, list[tuple[dict[str, Any], str]]] = {}
    for logical_name, index_table in INDEXED_LOGICAL_TABLES.items():
        normalized = normalized_rows_by_table.get(logical_name)
        if not normalized:
            continue
        raws = raw_records_by_table.get(logical_name) or []
        row_filter = TABLE_ROW_FILTERS.get(index_table)
        pairs: list[tuple[dict[str, Any], str]] = []
        for index, row in enumerate(normalized):
            if row_filter is not None and not row_filter(row):
                continue
            record_id = _clean(row.get(SOURCE_RECORD_ID_KEY))
            if not record_id and index < len(raws):
                record_id = _clean((raws[index] or {}).get("record_id"))
            pairs.append((row, record_id))
        out[index_table] = pairs
    return out


def index_json_text(index: dict[str, Any]) -> str:
    """Deterministic JSON text for the sidecar (stable for reproducible snapshots)."""

    return json.dumps(index, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def record_count(index: dict[str, Any]) -> int:
    return sum(len((t or {}).get("records") or {}) for t in (index.get("tables") or {}).values())


def load_index(root: Path) -> dict[str, Any] | None:
    """Load the sidecar from ``root`` if present and well-formed, else ``None``."""

    path = Path(root) / SIDECAR_FILENAME
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or not isinstance(payload.get("tables"), dict):
        return None
    return payload


def resolve(index: dict[str, Any], *, kind: str, source_ref: dict[str, Any]) -> tuple[str | None, str]:
    """Resolve one finding's ``source_ref`` to ``(record_id, resolution_status)``.

    ``resolution_status`` is one of ``resolved`` / ``unresolved`` / ``ambiguous``.
    Callers handle the no-sidecar ``snapshot_only`` case before calling this.
    """

    spec = KIND_RESOLUTION.get(kind)
    if spec is None:
        return None, "unresolved"
    table, field_map = spec
    table_index = (index.get("tables") or {}).get(table)
    if not isinstance(table_index, dict):
        return None, "unresolved"
    values = [_clean(source_ref.get(ref_field)) for ref_field, _ in field_map]
    if not all(values):
        return None, "unresolved"
    key = _join_key(values)
    if key in (table_index.get("ambiguous") or []):
        return None, "ambiguous"
    record_id = (table_index.get("records") or {}).get(key)
    if record_id:
        return record_id, "resolved"
    return None, "unresolved"


def resolve_by_table(index: dict[str, Any], source_ref: dict[str, Any]) -> tuple[str | None, str]:
    """Resolve a `source_ref` that has a `table` + key fields but no `kind`
    (the shape F2/F6 produce). Returns `(record_id, resolution_status)`.

    The source_ref's origin ``table`` may resolve against a different index
    table (e.g. a Localized_Copy value resolves to its Manual_Copy_Source
    authoring row); ``TABLE_RESOLUTION`` carries that index-table redirect.
    """
    table = source_ref.get("table")
    resolution = TABLE_RESOLUTION.get(str(table) if table else "")
    if resolution is None:
        return None, "unresolved"
    index_table, field_map = resolution
    table_index = (index.get("tables") or {}).get(index_table)
    if not isinstance(table_index, dict):
        return None, "unresolved"
    values = [_clean(source_ref.get(ref_field)) for ref_field, _ in field_map]
    if not all(values):
        return None, "unresolved"
    key = _join_key(values)
    if key in (table_index.get("ambiguous") or []):
        return None, "ambiguous"
    record_id = (table_index.get("records") or {}).get(key)
    if record_id:
        return record_id, "resolved"
    return None, "unresolved"


# content_lint ``source_ref`` ``kind`` -> (index table, ((source_ref_field, key_field), ...))
# for ROW-LEVEL findings: a finding about a whole spec row (the sidecar indexes at
# Slot_key granularity, so a row maps to MANY slot records). The fields here are a
# *prefix* of the index table's key — unlisted key fields (e.g. Slot_key) act as
# wildcards. Resolution returns the LIST of the row's slot record_ids.
ROW_KIND_RESOLUTION: dict[str, tuple[str, tuple[tuple[str, str], ...]]] = {
    "spec_master_row": ("Spec_Master", (("document_key", "document_key"), ("key", "Row_key"))),
}


def resolve_row_record_ids(
    index: dict[str, Any], *, kind: str, source_ref: dict[str, Any]
) -> tuple[list[str], str]:
    """Resolve a row-level finding to ALL matching slot record_ids.

    The finding fixes a whole row that spans multiple ``Slot_key`` records, so a
    single ``record_id`` does not exist; this returns the de-duplicated list of
    the row's slot record_ids. 0 matches -> ``unresolved``; otherwise ``resolved``.
    """
    spec = ROW_KIND_RESOLUTION.get(kind)
    if spec is None:
        return [], "unresolved"
    table, field_map = spec
    table_index = (index.get("tables") or {}).get(table)
    if not isinstance(table_index, dict):
        return [], "unresolved"
    key_fields = list(table_index.get("key_fields") or [])
    want = {key_field: _clean(source_ref.get(ref_field)) for ref_field, key_field in field_map}
    if not all(want.values()):
        return [], "unresolved"
    out: list[str] = []
    seen: set[str] = set()
    for composite, record_id in (table_index.get("records") or {}).items():
        parts = dict(zip(key_fields, composite.split(_KEY_SEP)))
        if all(parts.get(key_field) == value for key_field, value in want.items()):
            if record_id not in seen:
                seen.add(record_id)
                out.append(record_id)
    return out, ("resolved" if out else "unresolved")


def resolve_findings(findings: list[dict[str, Any]], root: Path) -> list[dict[str, Any]]:
    """Fill ``record_id`` / ``record_ids`` / ``resolution_status`` on findings using
    the sidecar.

    - A single-record kind (e.g. ``lcd_icon``) sets ``record_id``.
    - A row-level kind (e.g. ``spec_master_row``) sets ``record_ids`` (the row's
      slot records) and also ``record_id`` when the row has exactly one slot.
    - Other kinds are left as-is (``snapshot_only``) rather than marked unresolved
      against a sidecar that never tried to resolve them.

    When no sidecar exists the findings are returned unchanged. ``record_id`` /
    ``record_ids`` are not part of the finding hash, so resolving in place does not
    change ``finding_hash``.
    """

    index = load_index(root)
    if index is None:
        return findings
    for finding in findings:
        source_ref = finding.get("source_ref") or {}
        kind = source_ref.get("kind")
        if kind and kind in KIND_RESOLUTION:
            record_id, status = resolve(index, kind=str(kind), source_ref=source_ref)
            finding["resolution_status"] = status
            if record_id is not None:
                finding["record_id"] = record_id
        elif kind and kind in ROW_KIND_RESOLUTION:
            record_ids, status = resolve_row_record_ids(index, kind=str(kind), source_ref=source_ref)
            finding["resolution_status"] = status
            if record_ids:
                finding["record_ids"] = record_ids
                if len(record_ids) == 1:
                    finding["record_id"] = record_ids[0]
    return findings
