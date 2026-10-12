"""Source-authored text reference tables without fabricated icon assets."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy

from tools.component_specs.model import ComponentSpec, ComponentSlot, ComponentSpecError
from tools.component_specs.registry import adapter_binding, require_valid_component_spec
from tools.component_specs.theme import require_component_theme_roles


COMPONENT_ID = "HB-TABLE-REFERENCE"
# Variant semantics, not language/model heuristics, determine table geometry.
VARIANTS = {"lcd-descriptions": (2, False), "lcd-legend": (3, True), "lcd-actions": (3, True), "lcd-actions-compact": (2, True), "symbol-meanings": (2, False), "plain-inventory": (3, False)}


def _cells(cells: Sequence[Mapping[str, str]], columns: int) -> list[dict[str, str]]:
    if len(cells) != columns:
        raise ComponentSpecError(f"{COMPONENT_ID}: expected {columns} cells")
    result = []
    for cell in cells:
        if set(cell) != {"html", "text"} or not all(isinstance(v, str) for v in cell.values()):
            raise ComponentSpecError(f"{COMPONENT_ID}: rich cells require HTML and text")
        result.append(dict(cell))
    return result


def reference_table_component_spec(
    *, variant: str, label: str, headers: Sequence[Mapping[str, str]],
    rows: Sequence[Sequence[Mapping[str, str]]], source_ref: str, language: str,
) -> ComponentSpec:
    if variant not in VARIANTS:
        raise ComponentSpecError(f"{COMPONENT_ID}: unsupported variant {variant!r}")
    columns, has_headers = VARIANTS[variant]
    if not label.strip() or not rows or bool(headers) != has_headers:
        raise ComponentSpecError(f"{COMPONENT_ID}: label, rows and variant header policy required")
    normalized_headers = _cells(headers, columns) if has_headers else []
    normalized_rows = [_cells(row, columns) for row in rows]
    if variant == "plain-inventory" and (len(normalized_rows) != 1 or
            any(not cell["text"].strip() for cell in normalized_rows[0])):
        raise ComponentSpecError(f"{COMPONENT_ID}: plain inventory requires three nonempty items")
    if any(not any(cell["text"].strip() for cell in row) for row in normalized_rows):
        raise ComponentSpecError(f"{COMPONENT_ID}: empty rows are not meaningful")
    spec = ComponentSpec(
        component_id=COMPONENT_ID, variant=variant, source_ref=source_ref,
        language=language, assets=(), token_roles=("component.table.reference",),
        slots=(ComponentSlot("accessibility_label", "inline_text", label),
               ComponentSlot("headers", "ordered_headers", normalized_headers),
               ComponentSlot("rows", "ordered_rows", normalized_rows)),
    )
    return require_component_theme_roles(require_valid_component_spec(spec))


def reference_table_projection(spec: ComponentSpec, renderer: str = "web") -> dict:
    binding = adapter_binding(spec, renderer)
    if spec.component_id != COMPONENT_ID or binding["key"] != f"{renderer}_reference_table":
        raise ComponentSpecError("unexpected reference table adapter")
    # Revalidate semantic geometry on frozen replay, not only at ingestion.
    validated = reference_table_component_spec(
        variant=spec.variant, label=spec.slot("accessibility_label").content,
        headers=spec.slot("headers").content, rows=spec.slot("rows").content,
        source_ref=spec.source_ref, language=spec.language,
    )
    return {"variant": validated.variant,
            "label": validated.slot("accessibility_label").content,
            "headers": deepcopy(validated.slot("headers").content),
            "rows": deepcopy(validated.slot("rows").content)}
