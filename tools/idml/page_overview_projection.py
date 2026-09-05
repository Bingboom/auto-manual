"""Small semantic/geometry helpers for the shared overview projection."""
from __future__ import annotations

import re
from typing import Any, Mapping

Block = tuple[str, object]

_VEHICLE_LINE_START = re.compile(
    r"\s+(?=(?:Car|Coche|Vehículo|Véhicule|Voiture|Auto|Veículo)\s*:)",
    re.IGNORECASE,
)


def break_vehicle_spec(value: str) -> str:
    """Keep the vehicle-input specification on its own visual line."""
    return _VEHICLE_LINE_START.sub("\n", value)


def overview_semantic_blocks(
    blocks: list[Block],
    *,
    h1: str,
    h2s: list[str],
    image_count: int,
    show_view_headings: bool,
) -> tuple[list[Block], list[str]]:
    """Supply semantic view titles when the target hides their visible frames."""
    if not (h1 and not h2s and image_count == 2 and not show_view_headings):
        return list(blocks), h2s
    result: list[Block] = []
    image_index = 0
    for block in blocks:
        if block[0] == "image":
            result.append(("h2", ("front", "right")[image_index]))
            image_index += 1
        result.append(block)
    return result, ["front", "right"]


def geometry_rect(values: object) -> tuple[float, float, float, float]:
    """Validate and normalize one four-value overview rectangle."""
    if not isinstance(values, list) or len(values) != 4:
        raise ValueError("product overview geometry rectangle must have four values")
    return tuple(float(value) for value in values)  # type: ignore[return-value]


def projection_cells(view: Mapping[str, Any]) -> list[tuple[str, str]]:
    """Project governed callout slots to the editable IDML label cells."""
    result: list[tuple[str, str]] = []
    for callout in view["callouts"]:
        value = "\n".join(str(item) for item in callout.get("body", []))
        if callout["id"] == "dc_input":
            value = break_vehicle_spec(value)
        result.append((str(callout["label"]), value))
    return result
