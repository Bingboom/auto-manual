"""Semantic auto-resume comparison with the approved 3/4 condition geometry."""
from __future__ import annotations

from collections.abc import Sequence
from copy import deepcopy

from tools.component_specs.model import ComponentSlot, ComponentSpec, ComponentSpecError
from tools.component_specs.registry import adapter_binding, load_component_registry, require_valid_component_spec
from tools.component_specs.theme import load_manual_theme, require_component_theme_roles


COMPONENT_ID = "HB-TABLE-AUTO-RESUME"
_ADAPTERS = {"web": "hb_auto_resume", "latex": "hb_latex_auto_resume",
             "idml": "idml_auto_resume", "word": "word_auto_resume"}


def _copy(headers, conditions):
    if (len(headers) != 2 or len(conditions) != 2
            or [len(column) for column in conditions] != [3, 4]):
        raise ComponentSpecError("auto-resume requires two headers and 3/4 conditions")
    if any(not isinstance(value, str) or not value.strip()
           for value in [*headers, *conditions[0], *conditions[1]]):
        raise ComponentSpecError("auto-resume copy must contain non-empty text")
    return {"headers": list(headers), "conditions": [list(column) for column in conditions]}


def auto_resume_component_spec(
    *, headers: Sequence[str], conditions: Sequence[Sequence[str]],
    source_ref: str, language: str,
) -> ComponentSpec:
    copy = _copy(headers, conditions)
    registry = load_component_registry()
    spec = ComponentSpec(
        component_id=COMPONENT_ID, variant="two-column-middle-span",
        source_ref=source_ref, language=language,
        slots=(ComponentSlot("headers", "ordered_headers", copy["headers"]),
               ComponentSlot("conditions", "ordered_columns", copy["conditions"])),
        assets=(), token_roles=("component.table.auto-resume",),
    )
    require_valid_component_spec(spec, registry)
    return require_component_theme_roles(spec, load_manual_theme(component_registry=registry))


def auto_resume_projection(spec: ComponentSpec, renderer: str) -> dict:
    """Expose the same copy to every adapter; only Web is rendered here."""
    if spec.component_id != COMPONENT_ID or adapter_binding(spec, renderer)["key"] != _ADAPTERS[renderer]:
        raise ComponentSpecError("unexpected auto-resume component or adapter")
    return deepcopy(_copy(spec.slot("headers").content, spec.slot("conditions").content))
