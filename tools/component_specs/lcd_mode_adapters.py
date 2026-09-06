"""Four renderer projections for the LCD Mode ComponentSpec."""
from __future__ import annotations

from typing import Any

from tools.component_specs.lcd_mode import lcd_mode_semantic_projection
from tools.component_specs.model import ComponentSpec, ComponentSpecError
from tools.component_specs.registry import adapter_binding


_EXPECTED_KEYS = {
    "web": "hb_lcd_mode",
    "latex": "hb_latex_lcd_mode",
    "idml": "idml_lcd_mode",
    "word": "word_lcd_mode",
}


def _projection(spec: ComponentSpec, renderer: str) -> dict[str, Any]:
    binding = adapter_binding(spec, renderer)
    expected = _EXPECTED_KEYS[renderer]
    if binding.get("key") != expected:
        raise ComponentSpecError(
            f"{spec.component_id}: expected {renderer} adapter {expected!r}; "
            f"got {binding.get('key')!r}"
        )
    return lcd_mode_semantic_projection(spec)


def web_lcd_mode_projection(spec: ComponentSpec) -> dict[str, Any]:
    return {
        **_projection(spec, "web"),
        "composition_class": "hb-lcd-mode-composition",
        "art_panel_class": "hb-lcd-mode-art-panel",
        "table_panel_class": "hb-lcd-mode-table-panel",
        "table_class": "hb-lcd-mode-table",
    }


def latex_lcd_mode_projection(spec: ComponentSpec) -> dict[str, Any]:
    projection = _projection(spec, "latex")
    return {
        **projection,
        "environment": "HBLcdModeTable",
        "group_macros": ["HBLcdModeFirstGroup", "HBLcdModeSecondGroup"],
    }


def idml_lcd_mode_payload(spec: ComponentSpec) -> dict[str, Any]:
    projection = _projection(spec, "idml")
    return {
        "kind": "lcdmode",
        "img": projection["artwork_ref"],
        "groups": [
            {
                "state": group["state_text"],
                "actions": [
                    [action["action_text"], action["description_text"]]
                    for action in group["actions"]
                ],
            }
            for group in projection["groups"]
        ],
    }


def word_lcd_mode_projection(spec: ComponentSpec) -> dict[str, Any]:
    return {
        **_projection(spec, "word"),
        "editable_table": True,
        "table_class": "hb-lcd-mode-word-table",
        "art_class": "hb-lcd-mode-word-art",
    }


__all__ = [
    "idml_lcd_mode_payload",
    "latex_lcd_mode_projection",
    "web_lcd_mode_projection",
    "word_lcd_mode_projection",
]
