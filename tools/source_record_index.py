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

# Unit Separator. Unlikely to appear inside a business-key value, so it makes a
# stable composite-key string for JSON object keys.
_KEY_SEP = "\x1f"

# index table name -> the CSV columns whose tuple uniquely identifies a row.
# Keep the column names identical to what ``content_lint`` reads from the CSV.
TABLE_KEY_FIELDS: dict[str, tuple[str, ...]] = {
    # icon_en + Model + Version uniquely identifies an LCD icon row.
    "lcd_icons_blocks": ("icon_en", "Model", "Version"),
    # NOTE: Spec_Master is intentionally not indexed yet: (document_key, Row_key)
    # is non-unique by design (Slot_key disambiguation), so it would always
    # abstain. Add it once findings carry Slot_key.
}

# sync logical table name -> index table name used in the sidecar / source_ref.
INDEXED_LOGICAL_TABLES: dict[str, str] = {
    "lcd_icons": "lcd_icons_blocks",
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

    Both inputs are keyed by the sync *logical* table name and are positionally
    aligned (row ``i`` corresponds to raw record ``i``). Raw records without a
    ``record_id`` contribute an empty id, which ``build_index`` then abstains on.
    """

    out: dict[str, list[tuple[dict[str, Any], str]]] = {}
    for logical_name, index_table in INDEXED_LOGICAL_TABLES.items():
        normalized = normalized_rows_by_table.get(logical_name)
        raws = raw_records_by_table.get(logical_name)
        if not normalized or not raws:
            continue
        pairs: list[tuple[dict[str, Any], str]] = []
        for index in range(min(len(normalized), len(raws))):
            record_id = _clean((raws[index] or {}).get("record_id"))
            pairs.append((normalized[index], record_id))
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


def resolve_findings(findings: list[dict[str, Any]], root: Path) -> list[dict[str, Any]]:
    """Fill ``record_id`` / ``resolution_status`` on findings using the sidecar.

    When no sidecar exists the findings are returned unchanged (they keep their
    ``snapshot_only`` status). ``record_id`` is not part of the finding hash, so
    resolving in place does not change ``finding_hash``.
    """

    index = load_index(root)
    if index is None:
        return findings
    for finding in findings:
        source_ref = finding.get("source_ref") or {}
        kind = source_ref.get("kind")
        if not kind or kind not in KIND_RESOLUTION:
            # Leave kinds we do not index as snapshot_only rather than marking them
            # unresolved against a sidecar that never tried to resolve them.
            continue
        record_id, status = resolve(index, kind=str(kind), source_ref=source_ref)
        finding["resolution_status"] = status
        if record_id is not None:
            finding["record_id"] = record_id
    return findings
