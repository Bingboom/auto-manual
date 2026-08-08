"""Structured HB-TABLE-SPEC instances and renderer adapter projections."""
from __future__ import annotations

from copy import deepcopy
import re
from collections.abc import Mapping, Sequence
from typing import Any

from tools.component_specs.model import ComponentSlot, ComponentSpec, ComponentSpecError
from tools.component_specs.registry import (
    adapter_binding,
    load_component_registry,
    require_valid_component_spec,
)
from tools.component_specs.theme import load_manual_theme, require_component_theme_roles


COMPONENT_ID = "HB-TABLE-SPEC"
VARIANT = "vertical"
_CIRCLED_REFERENCE_RE = re.compile(r"[\u2460-\u2473]")
_EXPECTED_ADAPTER_KEYS = {
    "web": "hb_spec_table",
    "latex": "hb_latex_spec_table",
    "idml": "idml_spec_table",
    "word": "word_spec_table",
}


def _references(text: str) -> list[str]:
    return list(dict.fromkeys(_CIRCLED_REFERENCE_RE.findall(text)))


def _structured_groups(rows: Sequence[Sequence[str]]) -> list[dict[str, Any]]:
    normalized = [[str(cell) for cell in row] for row in rows]
    for index, row in enumerate(normalized):
        if len(row) != 2:
            raise ComponentSpecError(
                f"{COMPONENT_ID}: row {index + 1} must contain exactly label and value"
            )
    groups: list[dict[str, Any]] = []
    index = 0
    while index < len(normalized):
        label, value = normalized[index]
        if not label.strip():
            raise ComponentSpecError(
                f"{COMPONENT_ID}: row {index + 1} has no preceding label to span"
            )
        values = [{"text": value, "references": _references(value)}]
        span = 1
        while index + span < len(normalized) and not normalized[index + span][0].strip():
            continued_value = normalized[index + span][1]
            values.append(
                {
                    "text": continued_value,
                    "references": _references(continued_value),
                }
            )
            span += 1
        groups.append(
            {
                "label": label,
                "label_rowspan": span,
                "values": values,
                "references": _references(label),
            }
        )
        index += span
    return groups


def spec_table_component_spec(
    *,
    section_title: str,
    rows: Sequence[Sequence[str]],
    source_ref: str,
    language: str,
    metadata: Mapping[str, Any] | None = None,
    registry: Mapping[str, Any] | None = None,
    theme: Mapping[str, Any] | None = None,
) -> ComponentSpec:
    active_registry = registry or load_component_registry()
    active_theme = theme or load_manual_theme(component_registry=active_registry)
    title = str(section_title)
    if not title.strip():
        raise ComponentSpecError(f"{COMPONENT_ID}: section_title must be source-authored")
    spec = ComponentSpec(
        component_id=COMPONENT_ID,
        variant=VARIANT,
        source_ref=str(source_ref),
        language=str(language or "und"),
        slots=(
            ComponentSlot("section_title", "inline_text", title),
            ComponentSlot("rows", "structured_rows", _structured_groups(rows)),
        ),
        assets=(),
        token_roles=tuple(active_registry["components"][COMPONENT_ID]["token_roles"]),
        metadata=dict(metadata or {}),
    )
    require_valid_component_spec(spec, active_registry)
    return require_component_theme_roles(spec, active_theme)


def _require_adapter(spec: ComponentSpec, renderer: str) -> None:
    binding = adapter_binding(spec, renderer)
    expected = _EXPECTED_ADAPTER_KEYS[renderer]
    if binding.get("key") != expected:
        raise ComponentSpecError(
            f"{spec.component_id}: expected {renderer} adapter {expected!r}; "
            f"got {binding.get('key')!r}"
        )


def spec_table_groups(spec: ComponentSpec, renderer: str) -> list[dict[str, Any]]:
    _require_adapter(spec, renderer)
    content = spec.slot("rows").content
    if not isinstance(content, list):  # registry validates kind; enforce shape here
        raise ComponentSpecError(f"{COMPONENT_ID}: rows slot must contain a list")
    return deepcopy(content)


def spec_table_legacy_rows(spec: ComponentSpec, renderer: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for group in spec_table_groups(spec, renderer):
        label = str(group["label"])
        values = group["values"]
        for index, value in enumerate(values):
            rows.append((label if index == 0 else "", str(value["text"])))
    return rows


def web_spec_table_projection(spec: ComponentSpec) -> dict[str, Any]:
    return {
        "composition_class": "hb-spec-table-composition",
        "table_classes": "manual-table manual-spec-table hb-spec-table",
        "label_classes": "manual-spec-label hb-spec-label",
        "value_classes": "manual-spec-value hb-spec-value",
        "groups": spec_table_groups(spec, "web"),
    }


def latex_spec_table_rows(spec: ComponentSpec) -> list[tuple[str, str]]:
    return spec_table_legacy_rows(spec, "latex")


def idml_spec_table_rows(spec: ComponentSpec) -> list[tuple[str, str]]:
    return spec_table_legacy_rows(spec, "idml")


def word_spec_table_projection(spec: ComponentSpec) -> dict[str, Any]:
    return {
        "title": str(spec.slot("section_title").content),
        "groups": spec_table_groups(spec, "word"),
    }


__all__ = [
    "COMPONENT_ID",
    "VARIANT",
    "idml_spec_table_rows",
    "latex_spec_table_rows",
    "spec_table_component_spec",
    "spec_table_groups",
    "spec_table_legacy_rows",
    "web_spec_table_projection",
    "word_spec_table_projection",
]
