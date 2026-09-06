"""Four renderer projections for operation-panel ComponentSpecs."""
from __future__ import annotations

import re
from typing import Any, Mapping

from bs4 import BeautifulSoup

from tools.component_specs.model import ComponentSpec, ComponentSpecError
from tools.component_specs.operation import operation_semantic_projection
from tools.component_specs.registry import adapter_binding


_EXPECTED_KEYS = {
    "web": "hb_operation",
    "latex": "hb_latex_operation",
    "idml": "idml_operation",
    "word": "word_operation",
}


def _projection(spec: ComponentSpec, renderer: str) -> dict[str, Any]:
    binding = adapter_binding(spec, renderer)
    expected = _EXPECTED_KEYS[renderer]
    if binding.get("key") != expected:
        raise ComponentSpecError(
            f"{spec.component_id}: expected {renderer} adapter {expected!r}; "
            f"got {binding.get('key')!r}"
        )
    return operation_semantic_projection(spec)


def _plain_html(value: str) -> str:
    text = BeautifulSoup(value, "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+([:;,.!?])", r"\1", text)


def web_operation_projection(
    spec: ComponentSpec,
    presentation: Mapping[str, Any],
) -> dict[str, Any]:
    projection = _projection(spec, "web")
    if str(presentation.get("id") or "") != projection["operation_id"]:
        raise ComponentSpecError(
            f"{spec.component_id}: Web presentation does not match operation id"
        )
    expected_steps = [str(value) for value in presentation.get("step_ids", [])]
    actual_steps = [str(value["id"]) for value in projection["steps"]]
    if expected_steps != actual_steps:
        raise ComponentSpecError(
            f"{spec.component_id}: Web presentation step order changed: {expected_steps}"
        )
    if str(presentation.get("layout") or "") != projection["layout"]:
        raise ComponentSpecError(
            f"{spec.component_id}: Web presentation layout does not match"
        )
    return {
        **projection,
        "composition_class": "hb-operation-figure",
        "stage_class": "hb-operation-stage",
        "art_class": "hb-operation-art",
        "steps_class": "hb-operation-steps",
        "image_key": str(presentation.get("image_key") or ""),
        "web_replace_key": str(presentation.get("web_replace_key") or ""),
    }


def latex_operation_projection(spec: ComponentSpec) -> dict[str, Any]:
    projection = _projection(spec, "latex")
    step_lines = [
        " ".join(part["text"] for part in step["parts"])
        for step in projection["steps"]
    ]
    return {
        **projection,
        "macro": "HBOperationPanel",
        "arguments": [
            projection["artwork_ref"],
            _plain_html(projection["prerequisite_html"]),
            "\\par ".join(step_lines),
            "\\par ".join(_plain_html(value) for value in projection["supporting_copy"]),
        ],
    }


def _legacy_rows(steps: list[dict[str, Any]]) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for step in steps:
        parts = step["parts"]
        if [part["role"] for part in parts] == ["label", "instruction"]:
            rows.append((str(parts[0]["text"]), str(parts[1]["text"])))
            continue
        summary = str(parts[0]["text"])
        label, separator, instruction = summary.partition(":")
        rows.append(
            (label.strip(), instruction.strip())
            if separator and label.strip() and instruction.strip()
            else ("", summary)
        )
    return rows


def idml_operation_payload(spec: ComponentSpec) -> dict[str, Any]:
    projection = _projection(spec, "idml")
    rows = _legacy_rows(projection["steps"])
    prereq = _plain_html(projection["prerequisite_html"])
    support = [_plain_html(value) for value in projection["supporting_copy"]]
    layout = projection["layout"]
    if layout == "footer-overlay":
        return {
            "kind": "oppanel",
            "layout": "energy_saving",
            "image": projection["artwork_ref"],
            "action": rows[0][1] if rows else "",
            "guidance": support,
        }
    if layout == "footer-panel":
        return {
            "kind": "oppanel",
            "layout": "led_light",
            "image": projection["artwork_ref"],
            "lead": prereq,
            "steps": [instruction or label for label, instruction in rows],
        }
    return {
        "kind": "oppanel",
        "image": projection["artwork_ref"],
        "prereq": prereq,
        "rows": rows,
        "tail": "\n".join(support),
    }


def word_operation_projection(spec: ComponentSpec) -> dict[str, Any]:
    return {
        **_projection(spec, "word"),
        "editable": True,
        "panel_class": "hb-operation-word-panel",
        "art_class": "hb-operation-word-art",
        "step_class": "hb-operation-word-step",
    }


__all__ = [
    "idml_operation_payload",
    "latex_operation_projection",
    "web_operation_projection",
    "word_operation_projection",
]
