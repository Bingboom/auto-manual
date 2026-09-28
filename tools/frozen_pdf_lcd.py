"""Bind native PDF LCD rows to the existing four-column shared component.

Only independent, governed icon refs enter this adapter. Native number, name
and description strings remain unchanged, including both numbered-22 rows.
"""
from __future__ import annotations

from collections.abc import Mapping
from html import escape
from typing import Any

from tools.component_specs.manual_tables import lcd_icon_component_spec
from tools.manual_ir.components import component_flow_node


# These are source row identities, not the older asset filenames' numbering.
# Low battery/percentage and the tail after energy saving differ in the PDF.
_LCD_ROWS = (
    (1, "wifi"), (2, "bluetooth"), (3, "quiet-charging"),
    (4, "charging-plan"), (5, "self-powered"), (6, "tou"), (7, "ups"),
    (8, "ac-power"), (9, "output-voltage-frequency"), (10, "input-power"),
    (11, "remaining-charge-time"), (12, "ac-wall-charging"),
    (13, "car-charging"), (14, "solar-charging"), (15, "battery-saving"),
    (16, "charging-power-limit"), (17, "battery-power"), (18, "low-battery"),
    (19, "remaining-battery-percentage"), (20, "discharge-timer"),
    (21, "energy-saving"), (22, "high-temperature"), (22, "low-temperature"),
    (23, "fault-code"), (24, "output-power"), (25, "remaining-discharge-time"),
)
LCD_ICON_ASSET_KEYS = tuple(f"lcd.icon.{identity}" for _, identity in _LCD_ROWS)


def _pair(role: str, value: str) -> dict[str, str]:
    return {f"{role}_text": value, f"{role}_html": f"<p>{escape(value)}</p>"}


def lcd_icon_flow(
    record: Mapping[str, Any], *, assets: Mapping[str, Mapping[str, Any]],
    accessibility_label: str, source_ref: str, language: str,
) -> list[dict[str, Any]]:
    """Keep the source's 26 ordered rows and bind each semantic icon explicitly."""
    rows = record["rows"]
    if [row["number"] for row in rows] != [number for number, _ in _LCD_ROWS]:
        raise ValueError("LCD icon rows must cover 1-25 with both numbered-22 entries")
    positions = [(row["physical_page"], row["label_bbox"][1]) for row in rows]
    if positions != sorted(set(positions)):
        raise ValueError("LCD icon rows must retain native PDF visual order")
    values, refs, provenance = [], [], []
    for index, (row, key) in enumerate(zip(rows, LCD_ICON_ASSET_KEYS, strict=True)):
        ref = str(assets.get(key, {}).get("asset_ref") or "").strip()
        if not ref:
            raise ValueError(f"missing governed LCD icon: {key}")
        refs.append(ref)
        values.append({
            **_pair("number", str(row["number"])),
            **_pair("name", row["label"]), **_pair("description", row["meaning"]),
            "asset_index": index, "icon_alt": row["label"],
        })
        provenance.append({
            "number": row["number"], "physical_page": row["physical_page"],
            "label_bbox": list(row["label_bbox"]), "meaning_bbox": list(row["meaning_bbox"]),
            "asset_key": key,
        })
    spec = lcd_icon_component_spec(
        accessibility_label=accessibility_label, rows=values, icon_refs=refs,
        source_ref=source_ref, language=language, icon_locale_policy="shared",
        metadata={"source_kind": "native-pdf-lcd-copy", "source_rows": provenance},
    )
    return [component_flow_node(spec, root=True)]


__all__ = ["LCD_ICON_ASSET_KEYS", "lcd_icon_flow"]
