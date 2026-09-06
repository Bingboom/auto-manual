"""Renderer-neutral operation-panel instances."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from tools.component_specs.model import (
    ComponentAsset,
    ComponentSlot,
    ComponentSpec,
    ComponentSpecError,
)
from tools.component_specs.registry import load_component_registry, require_valid_component_spec
from tools.component_specs.theme import load_manual_theme, require_component_theme_roles


OPERATION_COMPONENT_ID = "HB-SPECIAL-OPERATION"
OPERATION_VARIANTS = frozenset({"status-right", "footer-overlay", "footer-panel"})
_PART_ROLES = frozenset({"label", "instruction", "summary"})


def _normalize_steps(steps: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw_step in enumerate(steps, start=1):
        step_id = str(raw_step.get("id") or "").strip()
        parts = raw_step.get("parts")
        if not step_id or step_id in seen:
            raise ComponentSpecError(
                f"{OPERATION_COMPONENT_ID}: step {index} needs a unique id"
            )
        if not isinstance(parts, Sequence) or isinstance(parts, (str, bytes)) or not parts:
            raise ComponentSpecError(
                f"{OPERATION_COMPONENT_ID}: step {step_id!r} needs ordered parts"
            )
        normalized_parts: list[dict[str, str]] = []
        for part_index, raw_part in enumerate(parts, start=1):
            if not isinstance(raw_part, Mapping):
                raise ComponentSpecError(
                    f"{OPERATION_COMPONENT_ID}: step {step_id!r} part "
                    f"{part_index} must be a mapping"
                )
            role = str(raw_part.get("role") or "").strip()
            html = str(raw_part.get("html") or "").strip()
            text = str(raw_part.get("text") or "").strip()
            if role not in _PART_ROLES or not html or not text:
                raise ComponentSpecError(
                    f"{OPERATION_COMPONENT_ID}: step {step_id!r} has an invalid part"
                )
            normalized_parts.append({"role": role, "html": html, "text": text})
        roles = [part["role"] for part in normalized_parts]
        if roles not in (["summary"], ["label", "instruction"]):
            raise ComponentSpecError(
                f"{OPERATION_COMPONENT_ID}: step {step_id!r} must be one summary "
                "or a label/instruction pair"
            )
        normalized.append({"id": step_id, "parts": normalized_parts})
        seen.add(step_id)
    if not normalized:
        raise ComponentSpecError(f"{OPERATION_COMPONENT_ID}: at least one step is required")
    return normalized


def operation_component_spec(
    *,
    operation_id: str,
    accessibility_label: str,
    layout: str,
    steps: Sequence[Mapping[str, Any]],
    prerequisite_html: str,
    supporting_copy: Sequence[str],
    artwork_ref: str,
    source_ref: str,
    language: str,
    artwork_locale_policy: str = "shared",
    metadata: Mapping[str, Any] | None = None,
    registry: Mapping[str, Any] | None = None,
    theme: Mapping[str, Any] | None = None,
) -> ComponentSpec:
    normalized_id = str(operation_id).strip()
    label = str(accessibility_label).strip()
    variant = str(layout).strip()
    art = str(artwork_ref).strip()
    if not normalized_id or not label or not art:
        raise ComponentSpecError(
            f"{OPERATION_COMPONENT_ID}: operation id, label, and artwork are required"
        )
    if variant not in OPERATION_VARIANTS:
        raise ComponentSpecError(
            f"{OPERATION_COMPONENT_ID}: unsupported layout {variant!r}"
        )
    normalized_support = [str(value).strip() for value in supporting_copy]
    if any(not value for value in normalized_support):
        raise ComponentSpecError(
            f"{OPERATION_COMPONENT_ID}: supporting copy cannot contain blanks"
        )
    active_registry = registry or load_component_registry()
    active_theme = theme or load_manual_theme(component_registry=active_registry)
    slots = [
        ComponentSlot("operation_id", "inline_text", normalized_id),
        ComponentSlot("accessibility_label", "inline_text", label),
        ComponentSlot("steps", "ordered_steps", _normalize_steps(steps)),
    ]
    prerequisite = str(prerequisite_html).strip()
    if prerequisite:
        slots.append(ComponentSlot("prerequisite", "rich_text", prerequisite))
    if normalized_support:
        slots.append(ComponentSlot("supporting_copy", "line_items", normalized_support))
    spec = ComponentSpec(
        component_id=OPERATION_COMPONENT_ID,
        variant=variant,
        source_ref=str(source_ref),
        language=str(language or "und"),
        slots=tuple(slots),
        assets=(
            ComponentAsset(
                role="artwork",
                asset_ref=art,
                locale_policy=artwork_locale_policy,
            ),
        ),
        token_roles=tuple(
            active_registry["components"][OPERATION_COMPONENT_ID]["token_roles"]
        ),
        metadata=dict(metadata or {}),
    )
    require_valid_component_spec(spec, active_registry)
    return require_component_theme_roles(spec, active_theme)


def operation_semantic_projection(spec: ComponentSpec) -> dict[str, Any]:
    prerequisite = next(
        (slot.content for slot in spec.slots if slot.role == "prerequisite"),
        "",
    )
    supporting = next(
        (slot.content for slot in spec.slots if slot.role == "supporting_copy"),
        [],
    )
    return {
        "operation_id": str(spec.slot("operation_id").content),
        "accessibility_label": str(spec.slot("accessibility_label").content),
        "layout": spec.variant,
        "steps": deepcopy(spec.slot("steps").content),
        "prerequisite_html": str(prerequisite),
        "supporting_copy": deepcopy(list(supporting)),
        "artwork_ref": spec.assets[0].asset_ref,
    }


__all__ = [
    "OPERATION_COMPONENT_ID",
    "OPERATION_VARIANTS",
    "operation_component_spec",
    "operation_semantic_projection",
]
