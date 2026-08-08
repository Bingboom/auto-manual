"""Renderer-neutral product-overview semantics."""
from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
from copy import deepcopy
import re
from typing import Any

from tools.component_specs.model import (
    ComponentAsset,
    ComponentSlot,
    ComponentSpec,
    ComponentSpecError,
)
from tools.component_specs.registry import load_component_registry, require_valid_component_spec
from tools.component_specs.theme import load_manual_theme, require_component_theme_roles


COMPONENT_ID = "HB-SPECIAL-OVERVIEW"
LIVE_VARIANT = "annotated-live"
COMPOSITE_VARIANT = "approved-composite"
VARIANTS = frozenset({LIVE_VARIANT, COMPOSITE_VARIANT})
VIEW_IDS = ("front", "right")
ASSET_ROLES = {"front": "front_art", "right": "right_art"}

_LABEL = re.compile(r"^\*\*(.+?)\*\*\s*(.*)$", re.S)
_EMPTY_CELL_MARKER_SUFFIX = re.compile(r"\s+-\s*$")


def _normalize_callout(
    callout: Mapping[str, Any],
    *,
    view_id: str,
    index: int,
) -> dict[str, Any]:
    callout_id = str(callout.get("id") or "").strip()
    label = str(callout.get("label") or "").strip()
    raw_body = callout.get("body") or []
    if not isinstance(raw_body, Sequence) or isinstance(raw_body, (str, bytes)):
        raise ComponentSpecError(
            f"{COMPONENT_ID}: {view_id} callout {index} body must be a list"
        )
    body = [str(value).strip() for value in raw_body if str(value).strip()]
    if not callout_id or not label:
        raise ComponentSpecError(
            f"{COMPONENT_ID}: {view_id} callout {index} requires id and label"
        )
    return {"id": callout_id, "label": label, "body": body}


def _normalize_stored_view(
    view: Mapping[str, Any],
    *,
    index: int,
) -> dict[str, Any]:
    view_id = str(view.get("id") or "").strip()
    title = str(view.get("title") or "").strip()
    image_asset_role = str(view.get("image_asset_role") or "").strip()
    alt = str(view.get("alt") or title).strip()
    raw_callouts = view.get("callouts")
    if view_id not in VIEW_IDS:
        raise ComponentSpecError(
            f"{COMPONENT_ID}: view {index} has unsupported id {view_id!r}"
        )
    if not title or not image_asset_role or not alt:
        raise ComponentSpecError(
            f"{COMPONENT_ID}: view {view_id} requires title, image role, and alt"
        )
    if image_asset_role != ASSET_ROLES[view_id]:
        raise ComponentSpecError(
            f"{COMPONENT_ID}: view {view_id} must use asset role "
            f"{ASSET_ROLES[view_id]!r}"
        )
    if not isinstance(raw_callouts, Sequence) or isinstance(
        raw_callouts, (str, bytes)
    ):
        raise ComponentSpecError(f"{COMPONENT_ID}: view {view_id} callouts must be a list")
    callouts = [
        _normalize_callout(callout, view_id=view_id, index=callout_index)
        for callout_index, callout in enumerate(raw_callouts, start=1)
        if isinstance(callout, Mapping)
    ]
    if len(callouts) != len(raw_callouts) or not callouts:
        raise ComponentSpecError(
            f"{COMPONENT_ID}: view {view_id} callouts must be non-empty mappings"
        )
    callout_ids = [callout["id"] for callout in callouts]
    if len(callout_ids) != len(set(callout_ids)):
        raise ComponentSpecError(f"{COMPONENT_ID}: view {view_id} callout ids repeat")
    return {
        "id": view_id,
        "title": title,
        "image_asset_role": image_asset_role,
        "alt": alt,
        "callouts": callouts,
    }


def _normalize_source_view(view: Mapping[str, Any], *, index: int) -> dict[str, Any]:
    view_id = str(view.get("id") or "").strip()
    image_ref = str(view.get("image_ref") or "").strip()
    if view_id not in VIEW_IDS:
        raise ComponentSpecError(
            f"{COMPONENT_ID}: view {index} has unsupported id {view_id!r}"
        )
    if not image_ref:
        raise ComponentSpecError(
            f"{COMPONENT_ID}: view {view_id} requires an image reference"
        )
    return _normalize_stored_view(
        {**view, "image_asset_role": ASSET_ROLES[view_id]},
        index=index,
    )


def overview_component_spec(
    *,
    accessibility_label: str,
    views: Sequence[Mapping[str, Any]],
    geometry_ref: str,
    source_ref: str,
    language: str,
    variant: str = LIVE_VARIANT,
    metadata: Mapping[str, Any] | None = None,
    registry: Mapping[str, Any] | None = None,
    theme: Mapping[str, Any] | None = None,
) -> ComponentSpec:
    if variant not in VARIANTS:
        raise ComponentSpecError(f"{COMPONENT_ID}: unsupported variant {variant!r}")
    label = str(accessibility_label).strip()
    geometry = str(geometry_ref).strip()
    if not label or not geometry:
        raise ComponentSpecError(
            f"{COMPONENT_ID}: accessibility label and geometry_ref are required"
        )
    if len(views) != 2:
        raise ComponentSpecError(f"{COMPONENT_ID}: exactly two views are required")
    normalized_views = [
        _normalize_source_view(view, index=index)
        for index, view in enumerate(views, start=1)
    ]
    if tuple(view["id"] for view in normalized_views) != VIEW_IDS:
        raise ComponentSpecError(
            f"{COMPONENT_ID}: views must remain ordered as {VIEW_IDS!r}"
        )

    assets = tuple(
        ComponentAsset(
            role=ASSET_ROLES[view["id"]],
            asset_ref=str(source_view.get("image_ref") or ""),
            locale_policy="shared",
        )
        for view, source_view in zip(normalized_views, views, strict=True)
    )
    active_registry = registry or load_component_registry()
    active_theme = theme or load_manual_theme(component_registry=active_registry)
    spec = ComponentSpec(
        component_id=COMPONENT_ID,
        variant=variant,
        source_ref=str(source_ref),
        language=str(language or "und"),
        slots=(
            ComponentSlot("accessibility_label", "inline_text", label),
            ComponentSlot("views", "ordered_views", normalized_views),
            ComponentSlot("geometry_ref", "instance_ref", geometry),
        ),
        assets=assets,
        token_roles=tuple(active_registry["components"][COMPONENT_ID]["token_roles"]),
        metadata=dict(metadata or {}),
    )
    require_valid_component_spec(spec, active_registry)
    return require_component_theme_roles(spec, active_theme)


def overview_semantic_projection(spec: ComponentSpec) -> dict[str, Any]:
    raw_views = spec.slot("views").content
    if not isinstance(raw_views, list):
        raise ComponentSpecError(f"{COMPONENT_ID}: views must be a list")
    asset_refs = {asset.role: asset.asset_ref for asset in spec.assets}
    views: list[dict[str, Any]] = []
    for index, raw_view in enumerate(raw_views, start=1):
        if not isinstance(raw_view, Mapping):
            raise ComponentSpecError(f"{COMPONENT_ID}: view {index} must be a mapping")
        normalized = _normalize_stored_view(raw_view, index=index)
        role = normalized["image_asset_role"]
        if role not in asset_refs:
            raise ComponentSpecError(f"{COMPONENT_ID}: missing asset role {role!r}")
        normalized["image_ref"] = asset_refs[role]
        views.append(normalized)
    return {
        "accessibility_label": str(spec.slot("accessibility_label").content),
        "views": deepcopy(views),
        "geometry_ref": str(spec.slot("geometry_ref").content),
        "variant": spec.variant,
    }


def _rows(value: object) -> list[list[str]]:
    if isinstance(value, list):
        rows = value
    elif isinstance(value, str):
        try:
            rows = ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return []
    else:
        return []
    if not isinstance(rows, list):
        return []
    return [
        [str(cell) for cell in row]
        for row in rows
        if isinstance(row, (list, tuple))
    ]


def _semantic_cell(
    value: str,
    *,
    strip_empty_marker: bool,
) -> dict[str, Any] | None:
    candidate = str(value).strip()
    if strip_empty_marker:
        candidate = _EMPTY_CELL_MARKER_SUFFIX.sub("", candidate)
    if not candidate:
        return None
    match = _LABEL.match(candidate)
    if match is None:
        return {"label": candidate, "body": []}
    body = match.group(2).strip()
    return {
        "label": match.group(1).strip(),
        "body": [body] if body else [],
    }


def _source_slots_from_blocks(blocks: Sequence[tuple[str, object]]) -> dict[str, dict[str, Any]]:
    first_h2 = next((index for index, block in enumerate(blocks) if block[0] == "h2"), -1)
    second_h2 = next(
        (
            index
            for index in range(first_h2 + 1, len(blocks))
            if blocks[index][0] == "h2"
        ),
        -1,
    )
    if first_h2 < 0 or second_h2 < 0:
        return {}
    front_tables = [_rows(value) for kind, value in blocks[first_h2 + 1 : second_h2] if kind == "table"]
    right_tables = [_rows(value) for kind, value in blocks[second_h2 + 1 :] if kind == "table"]
    primary = front_tables[0] if front_tables else []
    total = front_tables[1] if len(front_tables) > 1 else []

    def at(row: int, column: int) -> dict[str, Any] | None:
        if row >= len(primary) or column >= len(primary[row]):
            return None
        return _semantic_cell(primary[row][column], strip_empty_marker=True)

    slots: dict[str, dict[str, Any]] = {}
    left = [at(row, 0) for row in (0, 1, 3, 4, 5, 2)]
    right = [
        at(row, 1)
        for row in range(len(primary))
        if len(primary[row]) > 1
        and _semantic_cell(primary[row][1], strip_empty_marker=True) is not None
    ]
    for index, value in enumerate(left):
        if value is not None:
            slots[f"front.left.{index}"] = value
    for index, value in enumerate(right):
        if value is not None:
            slots[f"front.right.{index}"] = value
    if total and total[0]:
        value = _semantic_cell(total[0][0], strip_empty_marker=False)
        if value is not None:
            slots["front.total.0"] = value

    right_table = right_tables[0] if right_tables else []
    sequence = [
        value
        for row in right_table
        for cell in row
        # The legacy IDML renderer preserved the RST list-table's ``-`` body
        # marker on right-view labels (notably French ``Poignée``). Keep that
        # source-adapter behavior during the PR 8 compatibility window so the
        # renderer-neutral refactor remains byte-stable.
        if (value := _semantic_cell(cell, strip_empty_marker=False)) is not None
    ]
    for index, value in enumerate(sequence):
        slots[f"right.sequence.{index}"] = value
    return slots


def overview_spec_from_blocks(
    blocks: Sequence[tuple[str, object]],
    *,
    instance: Mapping[str, Any],
    source_ref: str,
    language: str,
) -> ComponentSpec:
    h1 = next((str(value) for kind, value in blocks if kind == "h1"), "")
    h2s = [str(value) for kind, value in blocks if kind == "h2"]
    image_refs = [str(value) for kind, value in blocks if kind == "image"]
    if not h1 or len(h2s) != 2 or len(image_refs) != 2:
        raise ComponentSpecError(
            f"{COMPONENT_ID}: blocks require one h1, two h2s, and two images"
        )
    slots = _source_slots_from_blocks(blocks)
    views: list[dict[str, Any]] = []
    for index, instance_view in enumerate(instance["views"]):
        callouts: list[dict[str, Any]] = []
        for binding in instance_view["callouts"]:
            source_slot = str(binding["source_slot"])
            semantic = slots.get(source_slot)
            if semantic is None:
                raise ComponentSpecError(
                    f"{COMPONENT_ID}: missing source slot {source_slot!r}"
                )
            callouts.append({"id": str(binding["id"]), **semantic})
        views.append(
            {
                "id": str(instance_view["id"]),
                "title": h2s[index],
                "image_ref": image_refs[index],
                "alt": h2s[index],
                "callouts": callouts,
            }
        )
    return overview_component_spec(
        accessibility_label=h1,
        views=views,
        geometry_ref=str(instance["instance_id"]),
        source_ref=source_ref,
        language=language,
        metadata={"source_kind": "idml_blocks"},
    )


__all__ = [
    "ASSET_ROLES",
    "COMPONENT_ID",
    "COMPOSITE_VARIANT",
    "LIVE_VARIANT",
    "VARIANTS",
    "VIEW_IDS",
    "overview_component_spec",
    "overview_semantic_projection",
    "overview_spec_from_blocks",
]
