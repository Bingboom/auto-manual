"""Single-page registered compositions for an active component target.

Each composition is a one-page plan (``plan_source`` ``registered-component``)
for exactly the sources the approved plan grouped together.  It routes that
page through the shared component renderer; it never places other pages.
"""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from .component_targets import ComponentTarget
from .prose_flow import move_car_notice_to_storage_blocks
from .reference_layout_plan import ReferenceLayoutPlanError


_CHARGING_METHODS = "page/08_charging_methods.rst"
_STORAGE = "page/09_storage_and_maintenance.rst"
_WARRANTY = "page/11_warranty.rst"


def resolve_registered_component_plans(
    target: ComponentTarget,
    *,
    bundle_root: Path,
    projected_by_path: dict[Path, Any],
) -> tuple[
    dict[str, Any] | None,
    dict[str, Any] | None,
    dict[str, Any] | None,
]:
    """Resolve the Storage/Troubleshooting, Warranty and Charging compositions.

    When both the shared page and Charging are registered, the approved car
    notice moves from the end of Charging to the head of Storage.
    """
    shared = target.composition(
        "storage_troubleshooting",
        (_STORAGE, f"page/troubleshooting_{target.language}.rst"),
    )
    warranty = target.composition("warranty", (_WARRANTY,))
    charging = target.composition("charging_methods", (_CHARGING_METHODS,))
    if shared is not None and charging is not None:
        methods_path = bundle_root / _CHARGING_METHODS
        storage_path = bundle_root / _STORAGE
        moved = move_car_notice_to_storage_blocks(
            list(projected_by_path[methods_path].blocks),
            list(projected_by_path[storage_path].blocks),
        )
        if moved is not None:
            methods_blocks, storage_blocks = moved
            projected_by_path[methods_path] = replace(
                projected_by_path[methods_path], blocks=tuple(methods_blocks),
            )
            projected_by_path[storage_path] = replace(
                projected_by_path[storage_path], blocks=tuple(storage_blocks),
            )
    return shared, warranty, charging


def apply_registered_warranty_footer_clearance(
    blocks: list[tuple[str, str]],
    page_plan: dict[str, Any] | None,
) -> list[tuple[str, str]]:
    """Reclaim only the final panel's spare bottom area for footer clearance."""
    if page_plan is None:
        return blocks
    if (
        page_plan.get("plan_source") != "registered-component"
        or {
            page.get("composition_type")
            for page in page_plan.get("pages", [])
            if isinstance(page, dict)
        } != {"warranty"}
    ):
        raise ReferenceLayoutPlanError(
            "warranty footer clearance requires a registered warranty component"
        )
    projected: list[tuple[str, str]] = []
    adjusted = False
    for kind, payload in blocks:
        if kind != "component":
            projected.append((kind, payload))
            continue
        try:
            spec = json.loads(payload)
        except (TypeError, json.JSONDecodeError):
            projected.append((kind, payload))
            continue
        if (
            isinstance(spec, dict)
            and spec.get("kind") == "warrantysection"
            and spec.get("index") == 6
        ):
            spec["panel_height_adjust"] = -6.0
            payload = json.dumps(spec, ensure_ascii=False)
            adjusted = True
        projected.append((kind, payload))
    if not adjusted:
        raise ReferenceLayoutPlanError(
            "registered warranty composition has no final section"
        )
    return projected


def registered_warranty_blocks(
    stem: str,
    blocks: list[tuple[str, str]],
    page_plan: dict[str, Any] | None,
    warranty_plan: dict[str, Any] | None,
) -> list[tuple[str, str]]:
    """Transform one isolated warranty source and apply its registered fit."""
    from .prose_flow import ProseFlowBuffer

    prepared, _columns = ProseFlowBuffer._batch_content(
        [(stem, blocks, 1)], page_plan,
    )
    return apply_registered_warranty_footer_clearance(prepared, warranty_plan)


__all__ = [
    "apply_registered_warranty_footer_clearance",
    "registered_warranty_blocks",
    "resolve_registered_component_plans",
]
