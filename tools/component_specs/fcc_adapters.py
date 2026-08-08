"""Four renderer adapters for the FCC ComponentSpec."""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from tools.component_specs.fcc import (
    fcc_semantic_projection,
    fcc_spec_from_legacy_payload,
)
from tools.component_specs.model import ComponentSpec, ComponentSpecError
from tools.component_specs.registry import adapter_binding


_EXPECTED_ADAPTER_KEYS = {
    "web": "hb_fcc",
    "latex": "hb_latex_fcc",
    "idml": "idml_fcc",
    "word": "word_fcc",
}


def _require_adapter(spec: ComponentSpec, renderer: str) -> None:
    binding = adapter_binding(spec, renderer)
    expected = _EXPECTED_ADAPTER_KEYS[renderer]
    if binding.get("key") != expected:
        raise ComponentSpecError(
            f"{spec.component_id}: expected {renderer} adapter {expected!r}; "
            f"got {binding.get('key')!r}"
        )


def _projection(spec: ComponentSpec, renderer: str) -> dict[str, Any]:
    _require_adapter(spec, renderer)
    return fcc_semantic_projection(spec)


def web_fcc_projection(spec: ComponentSpec) -> dict[str, Any]:
    return {
        **_projection(spec, "web"),
        "composition_class": "hb-fcc-composition",
        "grid_class": "hb-fcc-grid",
        "column_class": "hb-fcc-column",
        "mark_class": "hb-fcc-mark",
    }


def _block_text(block: Mapping[str, Any]) -> list[str]:
    if block["kind"] == "list":
        return [f"• {item}" for item in block["items"]]
    label = str(block.get("label") or "").strip()
    text = str(block.get("text") or "").strip()
    return [" ".join(value for value in (label, text) if value)]


def _legacy_arguments(spec: ComponentSpec, renderer: str) -> list[str]:
    legacy = spec.metadata.get("legacy_payload")
    if isinstance(legacy, Mapping):
        texts = [str(value) for value in legacy.get("texts") or []]
        return (texts + ["", ""])[:2]
    projection = _projection(spec, renderer)
    left_lines = [*projection["opening_copy"]]
    for block in projection["left_blocks"]:
        left_lines.extend(_block_text(block))
    right_lines: list[str] = []
    for block in projection["right_blocks"]:
        right_lines.extend(_block_text(block))
    return ["\n".join(left_lines), "\n".join(right_lines)]


def latex_fcc_projection(spec: ComponentSpec) -> dict[str, Any]:
    _require_adapter(spec, "latex")
    return {
        "macro": "HBFccBlock",
        "arguments": _legacy_arguments(spec, "latex"),
        "mark_asset_role": spec.assets[0].role,
    }


def idml_fcc_payload(spec: ComponentSpec) -> dict[str, Any]:
    _require_adapter(spec, "idml")
    legacy = spec.metadata.get("legacy_payload")
    if isinstance(legacy, Mapping):
        return deepcopy(dict(legacy))
    return {"kind": "fcc", "texts": _legacy_arguments(spec, "idml")}


def idml_fcc_payload_from_legacy(
    payload: Mapping[str, Any],
    *,
    source_ref: str,
    language: str,
) -> dict[str, Any]:
    return idml_fcc_payload(
        fcc_spec_from_legacy_payload(
            payload,
            source_ref=source_ref,
            language=language,
        )
    )


def word_fcc_projection(spec: ComponentSpec) -> dict[str, Any]:
    return {
        **_projection(spec, "word"),
        "table_class": "hb-fcc-word-table",
        "left_class": "hb-fcc-word-left",
        "right_class": "hb-fcc-word-right",
    }


__all__ = [
    "idml_fcc_payload",
    "idml_fcc_payload_from_legacy",
    "latex_fcc_projection",
    "web_fcc_projection",
    "word_fcc_projection",
]
