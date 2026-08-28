"""Four renderer projections for the shared Overview ComponentSpec."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from tools.component_specs.model import ComponentSpec, ComponentSpecError
from tools.component_specs.overview import overview_semantic_projection
from tools.component_specs.registry import adapter_binding


_EXPECTED_ADAPTER_KEYS = {
    "web": "hb_overview",
    "latex": "hb_latex_overview",
    "idml": "idml_overview",
    "word": "word_overview",
}


def _require_instance(spec: ComponentSpec, instance: Mapping[str, Any]) -> None:
    geometry_ref = str(spec.slot("geometry_ref").content)
    if str(instance.get("instance_id") or "") != geometry_ref:
        raise ComponentSpecError(
            f"{spec.component_id}: expected geometry instance {geometry_ref!r}; "
            f"got {instance.get('instance_id')!r}"
        )
    if instance.get("component_id") != spec.component_id:
        raise ComponentSpecError(
            f"{spec.component_id}: geometry instance component does not match"
        )


def _projection(
    spec: ComponentSpec,
    renderer: str,
    instance: Mapping[str, Any],
) -> dict[str, Any]:
    binding = adapter_binding(spec, renderer)
    expected = _EXPECTED_ADAPTER_KEYS[renderer]
    if binding.get("key") != expected:
        raise ComponentSpecError(
            f"{spec.component_id}: expected {renderer} adapter {expected!r}; "
            f"got {binding.get('key')!r}"
        )
    _require_instance(spec, instance)
    projection = overview_semantic_projection(spec)
    instance_views = {
        str(view["id"]): view
        for view in instance["views"]
    }
    for semantic_view in projection["views"]:
        view_id = str(semantic_view["id"])
        geometry = instance_views.get(view_id)
        if geometry is None:
            raise ComponentSpecError(
                f"{spec.component_id}: geometry is missing view {view_id!r}"
            )
        semantic_ids = [str(item["id"]) for item in semantic_view["callouts"]]
        geometry_ids = [str(item["id"]) for item in geometry["callouts"]]
        if semantic_ids != geometry_ids:
            raise ComponentSpecError(
                f"{spec.component_id}: {view_id} callout order does not match geometry"
            )
    return projection


def web_overview_projection(
    spec: ComponentSpec,
    instance: Mapping[str, Any],
) -> dict[str, Any]:
    projection = _projection(spec, "web", instance)
    geometry_views = {str(view["id"]): view for view in instance["views"]}
    views: list[dict[str, Any]] = []
    for view in projection["views"]:
        geometry = geometry_views[str(view["id"])]
        callout_geometry = {
            str(item["id"]): item["web"] for item in geometry["callouts"]
        }
        views.append(
            {
                **deepcopy(view),
                "image_key": str(geometry["image_key"]),
                "web_replace_key": str(geometry["web_replace_key"]),
                "composite_locales": deepcopy(geometry["composite_locales"]),
                "aspect_ratio": float(geometry["web"]["aspect_ratio"]),
                "decorative_leaders": deepcopy(
                    geometry["web"]["decorative_leaders"]
                ),
                "callouts": [
                    {**deepcopy(callout), **deepcopy(callout_geometry[str(callout["id"])])}
                    for callout in view["callouts"]
                ],
            }
        )
    return {**projection, "views": views}


def latex_overview_projection(
    spec: ComponentSpec,
    instance: Mapping[str, Any],
) -> dict[str, Any]:
    projection = _projection(spec, "latex", instance)
    return {
        **projection,
        "panels": [
            {
                "macro": "HBOverviewPanel",
                "arguments": [
                    str(view["title"]),
                    str(view["image_ref"]),
                    deepcopy(view["callouts"]),
                ],
            }
            for view in projection["views"]
        ],
    }


def idml_overview_projection(
    spec: ComponentSpec,
    instance: Mapping[str, Any],
) -> dict[str, Any]:
    projection = _projection(spec, "idml", instance)
    geometry_views = {str(view["id"]): view for view in instance["views"]}
    views: list[dict[str, Any]] = []
    for view in projection["views"]:
        geometry = geometry_views[str(view["id"])]
        callout_geometry = {
            str(item["id"]): item["idml"] for item in geometry["callouts"]
        }
        projected_view = {
                **deepcopy(view),
                "art_rect": deepcopy(geometry["idml"]["art_rect"]),
                "heading_text_y": float(geometry["idml"]["heading_text_y"]),
                "heading_bullet_rect": deepcopy(
                    geometry["idml"]["heading_bullet_rect"]
                ),
                "callouts": [
                    {**deepcopy(callout), **deepcopy(callout_geometry[str(callout["id"])])}
                    for callout in view["callouts"]
                ],
            }
        if "heading_text_rect" in geometry["idml"]:
            projected_view["heading_text_rect"] = deepcopy(
                geometry["idml"]["heading_text_rect"]
            )
        views.append(projected_view)
    semantic_leaders = {
        f"{view['id']}.{callout['id']}": {
            "id": str(callout["id"]),
            "points": deepcopy(callout["leader"]),
            "stroke_weight": 0.3,
        }
        for view in views
        for callout in view["callouts"]
    }
    decorative_leaders = {
        f"decorative.{leader['id']}": deepcopy(leader)
        for leader in instance["idml_decorative_leaders"]
    }
    leader_lookup = {**semantic_leaders, **decorative_leaders}
    return {
        **projection,
        "views": views,
        "page": deepcopy(instance["page"]),
        "leaders": [
            deepcopy(leader_lookup[leader_id])
            for leader_id in instance["idml_leader_order"]
        ],
    }


def word_overview_projection(
    spec: ComponentSpec,
    instance: Mapping[str, Any],
) -> dict[str, Any]:
    projection = _projection(spec, "word", instance)
    return {
        **projection,
        "section_class": "hb-overview-word-section",
        "view_class": "hb-overview-word-view",
    }


__all__ = [
    "idml_overview_projection",
    "latex_overview_projection",
    "web_overview_projection",
    "word_overview_projection",
]
