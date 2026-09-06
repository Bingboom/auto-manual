"""Renderer-neutral hybrid LCD screen-mode table."""
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


LCD_MODE_COMPONENT_ID = "HB-TABLE-LCD-MODE"
LCD_MODE_VARIANT = "two-state-three-action"


def _text_pair(raw: Mapping[str, Any], prefix: str) -> tuple[str, str]:
    html = str(raw.get(f"{prefix}_html") or "").strip()
    text = str(raw.get(f"{prefix}_text") or "").strip()
    if not html or not text:
        raise ComponentSpecError(
            f"{LCD_MODE_COMPONENT_ID}: {prefix} HTML and text are required"
        )
    return html, text


def _normalize_groups(groups: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if len(groups) != 2:
        raise ComponentSpecError(f"{LCD_MODE_COMPONENT_ID}: exactly two states are required")
    normalized: list[dict[str, Any]] = []
    for index, raw_group in enumerate(groups, start=1):
        state_html, state_text = _text_pair(raw_group, "state")
        raw_actions = raw_group.get("actions")
        if (
            not isinstance(raw_actions, Sequence)
            or isinstance(raw_actions, (str, bytes))
            or len(raw_actions) != 3
        ):
            raise ComponentSpecError(
                f"{LCD_MODE_COMPONENT_ID}: state {index} needs three actions"
            )
        actions: list[dict[str, str]] = []
        for raw_action in raw_actions:
            if not isinstance(raw_action, Mapping):
                raise ComponentSpecError(
                    f"{LCD_MODE_COMPONENT_ID}: action must be a mapping"
                )
            action_html, action_text = _text_pair(raw_action, "action")
            description_html, description_text = _text_pair(raw_action, "description")
            actions.append(
                {
                    "action_html": action_html,
                    "action_text": action_text,
                    "description_html": description_html,
                    "description_text": description_text,
                }
            )
        normalized.append(
            {
                "state_html": state_html,
                "state_text": state_text,
                "actions": actions,
            }
        )
    return normalized


def lcd_mode_component_spec(
    *,
    accessibility_label: str,
    groups: Sequence[Mapping[str, Any]],
    artwork_ref: str,
    source_ref: str,
    language: str,
    artwork_locale_policy: str = "shared",
    metadata: Mapping[str, Any] | None = None,
    registry: Mapping[str, Any] | None = None,
    theme: Mapping[str, Any] | None = None,
) -> ComponentSpec:
    label = str(accessibility_label).strip()
    art = str(artwork_ref).strip()
    if not label or not art:
        raise ComponentSpecError(
            f"{LCD_MODE_COMPONENT_ID}: accessibility label and artwork are required"
        )
    active_registry = registry or load_component_registry()
    active_theme = theme or load_manual_theme(component_registry=active_registry)
    spec = ComponentSpec(
        component_id=LCD_MODE_COMPONENT_ID,
        variant=LCD_MODE_VARIANT,
        source_ref=str(source_ref),
        language=str(language or "und"),
        slots=(
            ComponentSlot("accessibility_label", "inline_text", label),
            ComponentSlot("groups", "ordered_groups", _normalize_groups(groups)),
        ),
        assets=(
            ComponentAsset(
                role="artwork",
                asset_ref=art,
                locale_policy=artwork_locale_policy,
            ),
        ),
        token_roles=tuple(
            active_registry["components"][LCD_MODE_COMPONENT_ID]["token_roles"]
        ),
        metadata=dict(metadata or {}),
    )
    require_valid_component_spec(spec, active_registry)
    return require_component_theme_roles(spec, active_theme)


def lcd_mode_semantic_projection(spec: ComponentSpec) -> dict[str, Any]:
    return {
        "accessibility_label": str(spec.slot("accessibility_label").content),
        "groups": deepcopy(spec.slot("groups").content),
        "artwork_ref": spec.assets[0].asset_ref,
    }


__all__ = [
    "LCD_MODE_COMPONENT_ID",
    "LCD_MODE_VARIANT",
    "lcd_mode_component_spec",
    "lcd_mode_semantic_projection",
]
