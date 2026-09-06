"""Four renderer projections for shared manual table ComponentSpecs."""
from __future__ import annotations

from typing import Any

from tools.component_specs.manual_tables import (
    LCD_ICON_COMPONENT_ID,
    SYMBOL_ICON_COMPONENT_ID,
    SYMBOL_SIGNAL_COMPONENT_ID,
    TROUBLESHOOTING_COMPONENT_ID,
    manual_table_semantic_projection,
)
from tools.component_specs.model import ComponentSpec, ComponentSpecError
from tools.component_specs.registry import adapter_binding


_EXPECTED_KEYS = {
    LCD_ICON_COMPONENT_ID: {
        "web": "hb_lcd_icon",
        "latex": "hb_latex_lcd_icon",
        "idml": "idml_lcd_icon",
        "word": "word_lcd_icon",
    },
    TROUBLESHOOTING_COMPONENT_ID: {
        "web": "hb_troubleshooting",
        "latex": "hb_latex_troubleshooting",
        "idml": "idml_troubleshooting",
        "word": "word_troubleshooting",
    },
    SYMBOL_SIGNAL_COMPONENT_ID: {
        "web": "hb_symbol_signal",
        "latex": "hb_latex_symbol_signal",
        "idml": "idml_symbol_signal",
        "word": "word_symbol_signal",
    },
    SYMBOL_ICON_COMPONENT_ID: {
        "web": "hb_symbol_icon",
        "latex": "hb_latex_symbol_icon",
        "idml": "idml_symbol_icon",
        "word": "word_symbol_icon",
    },
}


def _projection(spec: ComponentSpec, renderer: str) -> dict[str, Any]:
    try:
        expected = _EXPECTED_KEYS[spec.component_id][renderer]
    except KeyError as exc:
        raise ComponentSpecError(
            f"unsupported manual table adapter for {spec.component_id!r}"
        ) from exc
    binding = adapter_binding(spec, renderer)
    if binding.get("key") != expected:
        raise ComponentSpecError(
            f"{spec.component_id}: expected {renderer} adapter {expected!r}; "
            f"got {binding.get('key')!r}"
        )
    return manual_table_semantic_projection(spec)


def web_manual_table_projection(spec: ComponentSpec) -> dict[str, Any]:
    classes = {
        LCD_ICON_COMPONENT_ID: "hb-lcd-table-composition",
        TROUBLESHOOTING_COMPONENT_ID: "hb-troubleshooting-composition",
        SYMBOL_SIGNAL_COMPONENT_ID: "hb-symbol-signal-composition",
        SYMBOL_ICON_COMPONENT_ID: "hb-symbol-pair-composition",
    }
    return {**_projection(spec, "web"), "component_class": classes[spec.component_id]}


def latex_manual_table_projection(spec: ComponentSpec) -> dict[str, Any]:
    environments = {
        LCD_ICON_COMPONENT_ID: "HBLcdIconTable",
        TROUBLESHOOTING_COMPONENT_ID: "HBTroubleshootingTable",
        SYMBOL_SIGNAL_COMPONENT_ID: "HBSymbolTable",
        SYMBOL_ICON_COMPONENT_ID: "HBSymbolTwoColumnTables",
    }
    return {**_projection(spec, "latex"), "environment": environments[spec.component_id]}


def idml_manual_table_payload(spec: ComponentSpec) -> dict[str, Any]:
    projection = _projection(spec, "idml")
    if spec.component_id == LCD_ICON_COMPONENT_ID:
        return {
            "kind": "lcd_icons",
            "rows": [
                {
                    "no": row["number_text"],
                    "figure": projection["assets"][row["asset_index"]],
                    "name": row["name_text"],
                    "desc": row["description_text"],
                }
                for row in projection["rows"]
            ],
        }
    if spec.component_id == TROUBLESHOOTING_COMPONENT_ID:
        return {
            "kind": "troubleshooting",
            "headers": [header["content_text"] for header in projection["headers"]],
            "rows": [
                [row["code_text"], row["measures_text"]]
                for row in projection["rows"]
            ],
        }
    if spec.component_id == SYMBOL_SIGNAL_COMPONENT_ID:
        return {
            "kind": "symbol_signals",
            "headers": [header["content_text"] for header in projection["headers"]],
            "rows": [
                {
                    "signal_key": row["label"].casefold(),
                    "label": row["label"],
                    "text": row["meaning_text"],
                }
                for row in projection["rows"]
            ],
        }
    rows = []
    for panel_index, panel in enumerate(projection["panels"]):
        for row in panel:
            rows.append(
                {
                    "figure": projection["assets"][row["asset_index"]],
                    "text": row["meaning_text"],
                    "column": "left" if panel_index == 0 else "right",
                    "continuation": False,
                }
            )
    return {
        "kind": "symbol_icons",
        "headers": [
            projection["headers"][0]["content_text"],
            projection["headers"][1]["content_text"],
        ],
        "rows": rows,
    }


def word_manual_table_projection(spec: ComponentSpec) -> dict[str, Any]:
    return {
        **_projection(spec, "word"),
        "editable": True,
        "table_class": {
            LCD_ICON_COMPONENT_ID: "hb-lcd-icon-word-table",
            TROUBLESHOOTING_COMPONENT_ID: "hb-troubleshooting-word-table",
            SYMBOL_SIGNAL_COMPONENT_ID: "hb-symbol-signal-word-table",
            SYMBOL_ICON_COMPONENT_ID: "hb-symbol-icon-word-table",
        }[spec.component_id],
    }


__all__ = [
    "idml_manual_table_payload",
    "latex_manual_table_projection",
    "web_manual_table_projection",
    "word_manual_table_projection",
]
