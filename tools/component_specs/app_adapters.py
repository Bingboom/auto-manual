"""Four renderer projections for App ComponentSpecs."""
from __future__ import annotations

from typing import Any, Mapping

from tools.component_specs.app import app_semantic_projection
from tools.component_specs.model import ComponentSpec, ComponentSpecError
from tools.component_specs.registry import adapter_binding


_EXPECTED = {
    "web": "hb_app",
    "latex": "hb_latex_app",
    "idml": "idml_app",
    "word": "word_app",
}


def _require(spec: ComponentSpec, renderer: str) -> Mapping[str, Any]:
    binding = adapter_binding(spec, renderer)
    if binding.get("key") != _EXPECTED[renderer]:
        raise ComponentSpecError(
            f"{spec.component_id}: expected {renderer} adapter {_EXPECTED[renderer]!r}"
        )
    return binding


def web_app_projection(spec: ComponentSpec) -> dict[str, Any]:
    _require(spec, "web")
    return {**app_semantic_projection(spec), "component_id": spec.component_id}


def latex_app_projection(spec: ComponentSpec) -> dict[str, Any]:
    _require(spec, "latex")
    payload = app_semantic_projection(spec)
    payload["adapter"] = {
        "download": "HBAppAsset",
        "inline-control": "HBAppBody",
        "add-device": "HBAppAsset",
    }[spec.variant]
    return payload


def idml_app_payload(spec: ComponentSpec) -> dict[str, Any]:
    _require(spec, "idml")
    payload = app_semantic_projection(spec)
    payload["kind"] = "body" if spec.variant == "inline-control" else "referencefigure"
    payload["layout"] = {
        "download": "app_download",
        "inline-control": "inline_control",
        "add-device": "app_add_device",
    }[spec.variant]
    return payload


def word_app_projection(spec: ComponentSpec) -> dict[str, Any]:
    _require(spec, "word")
    return {**app_semantic_projection(spec), "editable": True}


__all__ = [
    "idml_app_payload",
    "latex_app_projection",
    "web_app_projection",
    "word_app_projection",
]
