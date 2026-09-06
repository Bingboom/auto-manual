"""Four renderer projections for governed reference figures."""
from __future__ import annotations

from typing import Any, Mapping

from tools.component_specs.model import ComponentSpec, ComponentSpecError
from tools.component_specs.reference_figure import reference_figure_semantic_projection
from tools.component_specs.registry import adapter_binding


_EXPECTED = {
    "web": "hb_reference_figure",
    "latex": "hb_latex_reference_figure",
    "idml": "idml_reference_figure",
    "word": "word_reference_figure",
}


def _require(spec: ComponentSpec, renderer: str) -> Mapping[str, Any]:
    binding = adapter_binding(spec, renderer)
    if binding.get("key") != _EXPECTED[renderer]:
        raise ComponentSpecError(
            f"{spec.component_id}: expected {renderer} adapter {_EXPECTED[renderer]!r}"
        )
    return binding


def web_reference_figure_projection(spec: ComponentSpec) -> dict[str, Any]:
    _require(spec, "web")
    return {**reference_figure_semantic_projection(spec), "component_id": spec.component_id}


def latex_reference_figure_projection(spec: ComponentSpec) -> dict[str, Any]:
    _require(spec, "latex")
    return {
        **reference_figure_semantic_projection(spec),
        "adapter": "includegraphics",
        "image": spec.assets[0].asset_ref,
    }


def idml_reference_figure_payload(spec: ComponentSpec) -> dict[str, Any]:
    _require(spec, "idml")
    payload = reference_figure_semantic_projection(spec)
    payload.update(
        {
            "kind": "referencefigure",
            "layout": payload["reference_id"].replace("-", "_"),
            "image": payload["source_art"],
        }
    )
    return payload


def word_reference_figure_projection(spec: ComponentSpec) -> dict[str, Any]:
    _require(spec, "word")
    return {**reference_figure_semantic_projection(spec), "editable": True}


__all__ = [
    "idml_reference_figure_payload",
    "latex_reference_figure_projection",
    "web_reference_figure_projection",
    "word_reference_figure_projection",
]
