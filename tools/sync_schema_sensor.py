from __future__ import annotations

from typing import Any, Protocol


class _SchemaLike(Protocol):
    columns: tuple[str, ...]


MISSING_COLUMNS_WARNING_CODE = "MISSING_COLUMNS"

# Snapshot column -> the live field name(s) that carry its value. Single source of
# truth: the sensor skips the drift warning for these, and ``sync_data_records``
# copies the value across, so an alias can never silence a warning while still
# dropping the data.
FIELD_NAME_ALIASES: dict[str, dict[str, frozenset[str]]] = {
    # The source table historically exposed the Brazilian Portuguese field as
    # ``pt-BR`` while the normalized snapshot uses ``Text_pt-BR``.
    # ``Type`` is spelled lowercase in the footnote table while its sibling
    # ``spec_notes`` uses ``Type``; without the alias the column syncs empty and
    # ``csv_pages`` silently falls back to its "footnote" default.
    "spec_footnotes": {
        "Text_pt-BR": frozenset({"pt-BR"}),
        "Type": frozenset({"type"}),
    },
}

# Snapshot columns that no live field backs. Either the sync derives them, or they
# are legacy columns kept for readers that still accept them. Both are permanent by
# construction, so leaving them in the drift check trains everyone to ignore it.
NON_SOURCE_COLUMNS: dict[str, frozenset[str]] = {
    # Derived while merging the split spec sources (tools/spec_master_sources.py).
    "spec_master": frozenset({"spec_row_key", "Model", "Region"}),
    # Legacy pt-BR aliases (the live table exposes ``icon_pt-BR`` /
    # ``icon_desc_pt-BR``) plus a preview column the table never carried.
    "lcd_icons": frozenset({"icon_br", "icon_desc_br", "render_preview_en"}),
    # Superseded by ``source_value`` / ``Value``.
    "variable_lang_overrides": frozenset({"from_prefix", "to_prefix"}),
}


def apply_source_field_aliases(logical_name: str, values: dict[str, Any]) -> dict[str, Any]:
    """Fill schema columns from their aliased live field names, in place."""
    for column, aliases in FIELD_NAME_ALIASES.get(logical_name, {}).items():
        if str(values.get(column) or "").strip():
            continue
        for alias in aliases:
            aliased = values.get(alias)
            if str(aliased or "").strip():
                values[column] = aliased
                break
    return values


def source_field_names(source: object, *, base_token: str, table_id: str) -> set[str] | None:
    field_names = getattr(source, "field_names", None)
    if not callable(field_names):
        return None
    raw_names = field_names(base_token=base_token, table_id=table_id)
    if isinstance(raw_names, str):
        return {raw_names.strip()} if raw_names.strip() else set()
    return {str(name).strip() for name in raw_names if str(name).strip()}


def missing_schema_columns(
    logical_name: str,
    schema: _SchemaLike,
    source_field_names: set[str],
) -> tuple[str, ...]:
    aliases_by_column = FIELD_NAME_ALIASES.get(logical_name, {})
    non_source_columns = NON_SOURCE_COLUMNS.get(logical_name, frozenset())
    return tuple(
        column
        for column in schema.columns
        if column not in source_field_names
        and column not in non_source_columns
        and not source_field_names.intersection(aliases_by_column.get(column, frozenset()))
    )


def missing_columns_warning(
    logical_name: str,
    schema: _SchemaLike,
    source_field_names: set[str] | None,
) -> dict[str, Any] | None:
    if source_field_names is None:
        return None
    missing_columns = missing_schema_columns(logical_name, schema, source_field_names)
    if not missing_columns:
        return None
    return {
        "code": MISSING_COLUMNS_WARNING_CODE,
        "logical_name": logical_name,
        "missing_columns": list(missing_columns),
    }


def append_missing_columns_warning(
    warnings: list[dict[str, Any]],
    *,
    logical_name: str,
    schema: _SchemaLike,
    source: object,
    base_token: str,
    table_id: str,
) -> None:
    warning = missing_columns_warning(
        logical_name,
        schema,
        source_field_names(source, base_token=base_token, table_id=table_id),
    )
    if warning is not None:
        warnings.append(warning)


def append_missing_columns_warning_for_sources(
    warnings: list[dict[str, Any]],
    *,
    logical_name: str,
    schema: _SchemaLike,
    source: object,
    base_token: str,
    table_ids: tuple[str, ...],
) -> None:
    field_sets = [
        source_field_names(source, base_token=base_token, table_id=table_id)
        for table_id in table_ids
    ]
    if any(field_names is None for field_names in field_sets):
        return
    warning = missing_columns_warning(
        logical_name,
        schema,
        set().union(*(field_names or set() for field_names in field_sets)),
    )
    if warning is not None:
        warnings.append(warning)
