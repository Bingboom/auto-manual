"""Semantic button combinations with shared three-column presentation."""
from __future__ import annotations

from collections.abc import Sequence
from copy import deepcopy

from tools.component_specs.model import ComponentSlot, ComponentSpec, ComponentSpecError
from tools.component_specs.registry import adapter_binding, load_component_registry, require_valid_component_spec
from tools.component_specs.theme import load_manual_theme, require_component_theme_roles


COMPONENT_ID = "HB-TABLE-KEY-COMBINATIONS"
_ADAPTERS = {"web": "hb_key_combinations", "latex": "hb_latex_key_combinations",
             "idml": "idml_key_combinations", "word": "word_key_combinations"}


def _copy(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> dict[str, list[object]]:
    if len(headers) != 3 or len(rows) < 3 or any(len(row) != 3 for row in rows):
        raise ComponentSpecError("key-combinations requires three headers and three-column rows")
    if any(not isinstance(value, str) or not value.strip()
           for value in [*headers, *(value for row in rows for value in row)]):
        raise ComponentSpecError("key-combinations copy must contain non-empty text")
    return {"headers": list(headers), "rows": [list(row) for row in rows]}


def key_combinations_component_spec(
    *, headers: Sequence[str], rows: Sequence[Sequence[str]],
    source_ref: str, language: str,
) -> ComponentSpec:
    copy = _copy(headers, rows)
    registry = load_component_registry()
    spec = ComponentSpec(
        component_id=COMPONENT_ID, variant="three-column",
        source_ref=source_ref, language=language,
        slots=(ComponentSlot("headers", "ordered_headers", copy["headers"]),
               ComponentSlot("rows", "ordered_rows", copy["rows"])),
        assets=(), token_roles=("component.table.key-combinations",),
    )
    require_valid_component_spec(spec, registry)
    return require_component_theme_roles(spec, load_manual_theme(component_registry=registry))


def key_combinations_projection(spec: ComponentSpec, renderer: str) -> dict:
    """Expose the same copy to every adapter; only Web is rendered here."""
    if spec.component_id != COMPONENT_ID or adapter_binding(spec, renderer)["key"] != _ADAPTERS[renderer]:
        raise ComponentSpecError("unexpected key-combinations component or adapter")
    return deepcopy(_copy(spec.slot("headers").content, spec.slot("rows").content))
