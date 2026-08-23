"""Versioned target instances for the renderer-neutral Overview component."""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path
from typing import Any, Mapping

from tools.component_specs.model import ComponentSpecError
from tools.utils.path_utils import Paths, repo_root


SCHEMA_VERSION = "overview-component-instances/v1"
COMPONENT_ID = "HB-SPECIAL-OVERVIEW"


def default_overview_instances_path() -> Path:
    return Paths(root=repo_root()).overview_component_instances_contract


def _number_list(value: Any, *, length: int, field: str) -> list[float]:
    if (
        not isinstance(value, list)
        or len(value) != length
        or any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in value)
    ):
        raise ComponentSpecError(f"{field} must contain {length} numbers")
    return [float(item) for item in value]


def _point_list(value: Any, *, field: str) -> list[list[float]]:
    if not isinstance(value, list) or len(value) < 2:
        raise ComponentSpecError(f"{field} must contain at least two points")
    return [
        _number_list(point, length=2, field=f"{field}[{index}]")
        for index, point in enumerate(value)
    ]


def _non_empty(value: Any, *, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ComponentSpecError(f"{field} must be a non-empty string")
    return text


def _validate_instance(instance_id: str, raw: Any) -> dict[str, Any]:
    prefix = f"instances.{instance_id}"
    if not isinstance(raw, Mapping):
        raise ComponentSpecError(f"{prefix} must be a mapping")
    instance = deepcopy(dict(raw))
    if instance.get("component_id") != COMPONENT_ID:
        raise ComponentSpecError(f"{prefix}.component_id must be {COMPONENT_ID!r}")
    target = instance.get("target")
    if not isinstance(target, Mapping):
        raise ComponentSpecError(f"{prefix}.target must be a mapping")
    _non_empty(target.get("model"), field=f"{prefix}.target.model")
    _non_empty(target.get("region"), field=f"{prefix}.target.region")
    source_patterns = instance.get("source_patterns")
    if not isinstance(source_patterns, list) or not source_patterns:
        raise ComponentSpecError(f"{prefix}.source_patterns must be non-empty")
    for index, pattern in enumerate(source_patterns):
        _non_empty(pattern, field=f"{prefix}.source_patterns[{index}]")

    page = instance.get("page")
    if not isinstance(page, Mapping):
        raise ComponentSpecError(f"{prefix}.page must be a mapping")
    _number_list(page.get("title_frame"), length=4, field=f"{prefix}.page.title_frame")
    _number_list(
        page.get("title_text_rect"),
        length=4,
        field=f"{prefix}.page.title_text_rect",
    )

    views = instance.get("views")
    if not isinstance(views, list) or not views:
        raise ComponentSpecError(f"{prefix}.views must be a non-empty list")
    view_ids: set[str] = set()
    asset_roles: set[str] = set()
    all_callout_ids: set[str] = set()
    for view_index, view in enumerate(views):
        view_prefix = f"{prefix}.views[{view_index}]"
        if not isinstance(view, Mapping):
            raise ComponentSpecError(f"{view_prefix} must be a mapping")
        view_id = _non_empty(view.get("id"), field=f"{view_prefix}.id")
        if view_id in view_ids:
            raise ComponentSpecError(f"{prefix}: duplicate view id {view_id!r}")
        view_ids.add(view_id)
        asset_role = _non_empty(
            view.get("asset_role"), field=f"{view_prefix}.asset_role"
        )
        if asset_role in asset_roles:
            raise ComponentSpecError(f"{prefix}: duplicate asset role {asset_role!r}")
        asset_roles.add(asset_role)
        _non_empty(view.get("image_key"), field=f"{view_prefix}.image_key")
        _non_empty(
            view.get("web_replace_key"), field=f"{view_prefix}.web_replace_key"
        )
        locales = view.get("composite_locales")
        if not isinstance(locales, list) or not locales:
            raise ComponentSpecError(
                f"{view_prefix}.composite_locales must be a non-empty list"
            )
        locale_ids: set[str] = set()
        for locale_index, mapping in enumerate(locales):
            locale_prefix = f"{view_prefix}.composite_locales[{locale_index}]"
            if not isinstance(mapping, Mapping):
                raise ComponentSpecError(f"{locale_prefix} must be a mapping")
            locale = _non_empty(mapping.get("locale"), field=f"{locale_prefix}.locale")
            if locale in locale_ids:
                raise ComponentSpecError(
                    f"{view_prefix}: duplicate composite locale {locale!r}"
                )
            locale_ids.add(locale)
            patterns = mapping.get("source_patterns")
            if not isinstance(patterns, list) or not patterns:
                raise ComponentSpecError(
                    f"{locale_prefix}.source_patterns must be non-empty"
                )

        web = view.get("web")
        idml = view.get("idml")
        if not isinstance(web, Mapping) or not isinstance(idml, Mapping):
            raise ComponentSpecError(f"{view_prefix} requires web and idml mappings")
        aspect_ratio = web.get("aspect_ratio")
        if isinstance(aspect_ratio, bool) or not isinstance(aspect_ratio, (int, float)):
            raise ComponentSpecError(f"{view_prefix}.web.aspect_ratio must be numeric")
        decorative = web.get("decorative_leaders")
        if not isinstance(decorative, list):
            raise ComponentSpecError(
                f"{view_prefix}.web.decorative_leaders must be a list"
            )
        for leader_index, points in enumerate(decorative):
            _point_list(
                points,
                field=f"{view_prefix}.web.decorative_leaders[{leader_index}]",
            )
        _number_list(idml.get("art_rect"), length=4, field=f"{view_prefix}.idml.art_rect")
        if isinstance(idml.get("heading_text_y"), bool) or not isinstance(
            idml.get("heading_text_y"), (int, float)
        ):
            raise ComponentSpecError(
                f"{view_prefix}.idml.heading_text_y must be numeric"
            )
        _number_list(
            idml.get("heading_bullet_rect"),
            length=4,
            field=f"{view_prefix}.idml.heading_bullet_rect",
        )
        if "heading_text_rect" in idml:
            _number_list(
                idml.get("heading_text_rect"),
                length=4,
                field=f"{view_prefix}.idml.heading_text_rect",
            )

        callouts = view.get("callouts")
        if not isinstance(callouts, list) or not callouts:
            raise ComponentSpecError(f"{view_prefix}.callouts must be non-empty")
        source_slots: set[str] = set()
        for callout_index, callout in enumerate(callouts):
            callout_prefix = f"{view_prefix}.callouts[{callout_index}]"
            if not isinstance(callout, Mapping):
                raise ComponentSpecError(f"{callout_prefix} must be a mapping")
            callout_id = _non_empty(callout.get("id"), field=f"{callout_prefix}.id")
            qualified_id = f"{view_id}.{callout_id}"
            if qualified_id in all_callout_ids:
                raise ComponentSpecError(
                    f"{prefix}: duplicate qualified callout id {qualified_id!r}"
                )
            all_callout_ids.add(qualified_id)
            source_slot = _non_empty(
                callout.get("source_slot"), field=f"{callout_prefix}.source_slot"
            )
            if source_slot in source_slots:
                raise ComponentSpecError(
                    f"{view_prefix}: duplicate source slot {source_slot!r}"
                )
            source_slots.add(source_slot)
            web_geometry = callout.get("web")
            idml_geometry = callout.get("idml")
            if not isinstance(web_geometry, Mapping) or not isinstance(
                idml_geometry, Mapping
            ):
                raise ComponentSpecError(
                    f"{callout_prefix} requires web and idml geometry"
                )
            _number_list(
                web_geometry.get("rect"),
                length=4,
                field=f"{callout_prefix}.web.rect",
            )
            if web_geometry.get("align") not in {"left", "right"}:
                raise ComponentSpecError(f"{callout_prefix}.web.align is invalid")
            _point_list(
                web_geometry.get("leader"), field=f"{callout_prefix}.web.leader"
            )
            _number_list(
                idml_geometry.get("rect"),
                length=4,
                field=f"{callout_prefix}.idml.rect",
            )
            if idml_geometry.get("align") not in {"LeftAlign", "RightAlign"}:
                raise ComponentSpecError(f"{callout_prefix}.idml.align is invalid")
            if idml_geometry.get("anchor", "natural") not in {
                "natural",
                "above-leader",
            }:
                raise ComponentSpecError(f"{callout_prefix}.idml.anchor is invalid")
            _point_list(
                idml_geometry.get("leader"), field=f"{callout_prefix}.idml.leader"
            )

    if view_ids != {"front", "right"}:
        raise ComponentSpecError(f"{prefix}.views must define front and right")
    if asset_roles != {"front_art", "right_art"}:
        raise ComponentSpecError(
            f"{prefix}.views must bind front_art and right_art asset roles"
        )

    decorative_idml = instance.get("idml_decorative_leaders")
    if not isinstance(decorative_idml, list):
        raise ComponentSpecError(f"{prefix}.idml_decorative_leaders must be a list")
    decorative_ids: set[str] = set()
    for index, leader in enumerate(decorative_idml):
        leader_prefix = f"{prefix}.idml_decorative_leaders[{index}]"
        if not isinstance(leader, Mapping):
            raise ComponentSpecError(f"{leader_prefix} must be a mapping")
        leader_id = _non_empty(leader.get("id"), field=f"{leader_prefix}.id")
        if leader_id in decorative_ids:
            raise ComponentSpecError(f"{prefix}: duplicate decorative leader {leader_id!r}")
        decorative_ids.add(leader_id)
        _point_list(leader.get("points"), field=f"{leader_prefix}.points")
        stroke = leader.get("stroke_weight")
        if isinstance(stroke, bool) or not isinstance(stroke, (int, float)):
            raise ComponentSpecError(f"{leader_prefix}.stroke_weight must be numeric")
    leader_order = instance.get("idml_leader_order")
    if (
        not isinstance(leader_order, list)
        or not all(isinstance(item, str) and item.strip() for item in leader_order)
        or len(leader_order) != len(set(leader_order))
    ):
        raise ComponentSpecError(f"{prefix}.idml_leader_order must be unique strings")
    expected_leaders = all_callout_ids | {
        f"decorative.{leader_id}" for leader_id in decorative_ids
    }
    if set(leader_order) != expected_leaders:
        raise ComponentSpecError(
            f"{prefix}.idml_leader_order must cover every semantic and decorative leader"
        )
    return instance


def validate_overview_instance_registry(payload: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        issues.append(f"schema_version must be {SCHEMA_VERSION!r}")
    default_id = str(payload.get("default_instance_id") or "")
    instances = payload.get("instances")
    if not isinstance(instances, Mapping) or not instances:
        return issues + ["instances must be a non-empty mapping"]
    if default_id not in instances:
        issues.append("default_instance_id must name a registered instance")
    targets: set[tuple[str, str]] = set()
    for instance_id, raw in instances.items():
        try:
            instance = _validate_instance(str(instance_id), raw)
        except ComponentSpecError as exc:
            issues.append(str(exc))
            continue
        target = instance["target"]
        key = (str(target["model"]).casefold(), str(target["region"]).casefold())
        if key in targets:
            issues.append(f"duplicate target instance for {key[0]}/{key[1]}")
        targets.add(key)
    return issues


@lru_cache(maxsize=4)
def _load_cached(path_text: str) -> dict[str, Any]:
    path = Path(path_text)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ComponentSpecError(f"cannot load overview instances {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ComponentSpecError(f"overview instances must contain a mapping: {path}")
    issues = validate_overview_instance_registry(payload)
    if issues:
        raise ComponentSpecError("invalid overview instances: " + "; ".join(issues))
    return payload


def load_overview_instance_registry(path: Path | None = None) -> dict[str, Any]:
    contract_path = (path or default_overview_instances_path()).resolve()
    return deepcopy(_load_cached(str(contract_path)))


def resolve_overview_instance(
    *,
    model: str | None,
    region: str | None,
    instance_id: str | None = None,
    registry: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    active = dict(registry or load_overview_instance_registry())
    instances = active["instances"]
    if instance_id:
        raw = instances.get(instance_id)
        if raw is None:
            raise ComponentSpecError(f"unknown overview instance {instance_id!r}")
        instance = _validate_instance(instance_id, raw)
    else:
        matches = [
            (key, value)
            for key, value in instances.items()
            if str(value["target"]["model"]).casefold() == str(model or "").casefold()
            and str(value["target"]["region"]).casefold()
            == str(region or "").casefold()
        ]
        if not model and not region:
            default_id = str(active["default_instance_id"])
            matches = [(default_id, instances[default_id])]
        if len(matches) != 1:
            raise ComponentSpecError(
                f"expected one overview instance for {model!r}/{region!r}; "
                f"found {len(matches)}"
            )
        instance_id, raw = matches[0]
        instance = _validate_instance(str(instance_id), raw)
    instance["instance_id"] = str(instance_id)
    return instance


__all__ = [
    "COMPONENT_ID",
    "SCHEMA_VERSION",
    "default_overview_instances_path",
    "load_overview_instance_registry",
    "resolve_overview_instance",
    "validate_overview_instance_registry",
]
