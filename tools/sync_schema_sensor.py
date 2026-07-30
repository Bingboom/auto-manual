from __future__ import annotations

from typing import Any, Protocol


class _SchemaLike(Protocol):
    columns: tuple[str, ...]


MISSING_COLUMNS_WARNING_CODE = "MISSING_COLUMNS"
_FIELD_NAME_ALIASES: dict[str, dict[str, frozenset[str]]] = {
    # The source table historically exposed the Brazilian Portuguese field as
    # ``pt-BR`` while the normalized snapshot uses ``Text_pt-BR``.
    "spec_footnotes": {"Text_pt-BR": frozenset({"pt-BR"})},
}


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
    aliases_by_column = _FIELD_NAME_ALIASES.get(logical_name, {})
    return tuple(
        column
        for column in schema.columns
        if column not in source_field_names
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
