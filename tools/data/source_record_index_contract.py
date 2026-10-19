"""Registry-closure checks for the source-record index sidecar.

This module keeps the invariant checks separate from the sidecar builder so
the resolver remains a small runtime component. The caller supplies the
registries explicitly, which also makes the checks safe to exercise in tests
without importing or mutating a second copy of the resolver state.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any


def _clean(value: Any) -> str:
    return str(value if value is not None else "").strip()


def registry_issues(
    *,
    table_key_fields: Mapping[str, tuple[str, ...]],
    table_optional_key_fields: Mapping[str, frozenset[str]],
    table_fallback_key_fields: Mapping[str, tuple[tuple[str, str], ...]],
    indexed_logical_tables: Mapping[str, str],
    kind_resolution: Mapping[str, tuple[str, tuple[tuple[str, str], ...]]],
    table_resolution: Mapping[str, tuple[str, tuple[tuple[str, str], ...]]],
    row_kind_resolution: Mapping[str, tuple[str, tuple[tuple[str, str], ...]]],
    table_row_filters: Mapping[str, Callable[[dict[str, Any]], bool]],
) -> tuple[str, ...]:
    """Return drift across all source-record index registries."""

    issues: list[str] = []

    for table, fields in table_key_fields.items():
        if not fields:
            issues.append(f"TABLE_KEY_FIELDS[{table!r}] has no key fields")
        if len(fields) != len(set(fields)):
            issues.append(f"TABLE_KEY_FIELDS[{table!r}] repeats a key field")
        if any(not _clean(field) for field in fields):
            issues.append(f"TABLE_KEY_FIELDS[{table!r}] contains an empty field")

    for registry_name, registry in (
        ("TABLE_OPTIONAL_KEY_FIELDS", table_optional_key_fields),
        ("TABLE_FALLBACK_KEY_FIELDS", table_fallback_key_fields),
    ):
        for table in registry:
            if table not in table_key_fields:
                issues.append(f"{registry_name}[{table!r}] targets an unknown index table")

    for table, fields in table_optional_key_fields.items():
        unknown = sorted(set(fields) - set(table_key_fields.get(table, ())))
        if unknown:
            issues.append(f"TABLE_OPTIONAL_KEY_FIELDS[{table!r}] has non-key field(s): {unknown}")

    for table, specs in table_fallback_key_fields.items():
        csv_fields = [pair[0] for pair in specs if isinstance(pair, tuple) and len(pair) == 2]
        ref_fields = [pair[1] for pair in specs if isinstance(pair, tuple) and len(pair) == 2]
        if len(csv_fields) != len(specs) or any(not _clean(field) for field in [*csv_fields, *ref_fields]):
            issues.append(f"TABLE_FALLBACK_KEY_FIELDS[{table!r}] has an invalid field mapping")
        if len(ref_fields) != len(set(ref_fields)):
            issues.append(f"TABLE_FALLBACK_KEY_FIELDS[{table!r}] repeats a source-ref field")

    indexed_targets = list(indexed_logical_tables.values())
    if len(indexed_targets) != len(set(indexed_targets)):
        issues.append("INDEXED_LOGICAL_TABLES maps multiple logical tables to one index table")
    for logical_name, table in indexed_logical_tables.items():
        if not _clean(logical_name) or table not in table_key_fields:
            issues.append(f"INDEXED_LOGICAL_TABLES[{logical_name!r}] targets an unknown index table")

    def check_resolution_map(
        registry_name: str,
        registry: Mapping[str, tuple[str, tuple[tuple[str, str], ...]]],
        *,
        exact_key_fields: bool,
    ) -> None:
        for source_name, spec in registry.items():
            if not isinstance(spec, tuple) or len(spec) != 2:
                issues.append(f"{registry_name}[{source_name!r}] has an invalid resolver entry")
                continue
            table, field_map = spec
            key_fields = table_key_fields.get(table)
            if key_fields is None:
                issues.append(f"{registry_name}[{source_name!r}] targets an unknown index table")
                continue
            if any(
                not isinstance(pair, tuple)
                or len(pair) != 2
                or not _clean(pair[0])
                or not _clean(pair[1])
                for pair in field_map
            ):
                issues.append(f"{registry_name}[{source_name!r}] has an invalid field mapping")
                continue
            source_fields = [source_field for source_field, _ in field_map]
            key_fields_for_mapping = [key_field for _, key_field in field_map]
            if len(source_fields) != len(set(source_fields)):
                issues.append(f"{registry_name}[{source_name!r}] repeats a source-ref field")
            if any(field not in key_fields for field in key_fields_for_mapping):
                issues.append(f"{registry_name}[{source_name!r}] maps to a non-key field")
            expected = tuple(key_fields)
            actual = tuple(key_fields_for_mapping)
            matches_expected = actual == expected if exact_key_fields else actual == expected[: len(actual)]
            if not matches_expected:
                issues.append(
                    f"{registry_name}[{source_name!r}] key order {list(actual)} "
                    f"does not match {list(expected)}"
                )

    check_resolution_map("KIND_RESOLUTION", kind_resolution, exact_key_fields=True)
    check_resolution_map("TABLE_RESOLUTION", table_resolution, exact_key_fields=True)
    check_resolution_map("ROW_KIND_RESOLUTION", row_kind_resolution, exact_key_fields=False)

    for table, predicate in table_row_filters.items():
        if table not in table_key_fields or not callable(predicate):
            issues.append(f"TABLE_ROW_FILTERS[{table!r}] is not bound to an indexed table")

    return tuple(issues)


def registry_issues_from_namespace(namespace: Mapping[str, Any]) -> tuple[str, ...]:
    """Run :func:`registry_issues` against a resolver module namespace."""

    return registry_issues(
        table_key_fields=namespace["TABLE_KEY_FIELDS"],
        table_optional_key_fields=namespace["TABLE_OPTIONAL_KEY_FIELDS"],
        table_fallback_key_fields=namespace["TABLE_FALLBACK_KEY_FIELDS"],
        indexed_logical_tables=namespace["INDEXED_LOGICAL_TABLES"],
        kind_resolution=namespace["KIND_RESOLUTION"],
        table_resolution=namespace["TABLE_RESOLUTION"],
        row_kind_resolution=namespace["ROW_KIND_RESOLUTION"],
        table_row_filters=namespace["TABLE_ROW_FILTERS"],
    )


def validate_namespace(namespace: Mapping[str, Any]) -> None:
    """Raise when a resolver module's registries drift apart."""

    issues = registry_issues_from_namespace(namespace)
    if issues:
        raise RuntimeError("source_record_index registry drift: " + "; ".join(issues))
