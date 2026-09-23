"""Resolve exact registered compositions without activating a whole-book plan."""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from tools.manual_ir import ManualIR
from tools.utils.path_utils import PathSegments, Paths

from .reference_layout_plan import (
    REGISTRY_SCHEMA_VERSION,
    SUPPORTED_SCHEMA_VERSIONS,
    ReferenceLayoutPlanError,
)
from .prose_flow import move_car_notice_to_storage_blocks


def _object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReferenceLayoutPlanError(f"cannot read registered component plan {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReferenceLayoutPlanError(f"registered component plan must be an object: {path}")
    return value


def _registered_plan(root: Path, raw_path: Any) -> dict[str, Any]:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ReferenceLayoutPlanError(
            "registered component plan path must be non-empty"
        )
    relative = Path(raw_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ReferenceLayoutPlanError(
            "registered component plan path must stay repo-relative"
        )
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(root):
        raise ReferenceLayoutPlanError(
            "registered component plan path escapes the repository"
        )
    return _object(resolved)


def find_registered_component_plan(
    ir: ManualIR,
    *,
    root: Path,
    language: str,
    composition_type: str,
    source_refs: tuple[str, ...],
) -> dict[str, Any] | None:
    """Return one hash-pinned composition-only plan for the requested sources."""
    root = root.resolve()
    registry_path = Paths(root=root).renderer_contracts_dir / PathSegments.REFERENCE_LAYOUT_REGISTRY_JSON
    if not registry_path.is_file():
        return None
    registry = _object(registry_path)
    if registry.get("schema_version") != REGISTRY_SCHEMA_VERSION:
        raise ReferenceLayoutPlanError(f"registry schema_version must be {REGISTRY_SCHEMA_VERSION}")
    language = language.strip().casefold().replace("_", "-").split("-", 1)[0]
    actual = {page.source_ref: page for page in ir.pages}
    matches: list[dict[str, Any]] = []
    entries = registry.get("plans")
    if not isinstance(entries, list):
        raise ReferenceLayoutPlanError("registry plans must be a list")
    for registered in entries:
        target = registered.get("target") if isinstance(registered, dict) else None
        if not isinstance(target, dict) or target.get("model") != ir.model or target.get("region") != ir.region:
            continue
        if language not in target.get("languages", []):
            continue
        payload = _registered_plan(root, registered.get("path"))
        if payload.get("schema_version") not in SUPPORTED_SCHEMA_VERSIONS:
            raise ReferenceLayoutPlanError(
                "registered component plan schema is unsupported"
            )
        if payload.get("target") != target:
            raise ReferenceLayoutPlanError(
                "registered component plan target does not match its registry entry"
            )
        approval = payload.get("approval")
        if not isinstance(approval, dict) or approval.get("status") != "approved":
            raise ReferenceLayoutPlanError("registered component plan is not approved")
        pages_value = payload.get("pages")
        if not isinstance(pages_value, list):
            raise ReferenceLayoutPlanError(
                "registered component plan pages must be a list"
            )
        pages = [page for page in pages_value if isinstance(page, dict)]
        selected = [next((page for page in pages if page.get("source_ref") == ref), None) for ref in source_refs]
        if any(page is None for page in selected):
            continue
        if any(page.get("language") != language for page in selected):
            continue
        if len({str(page.get("composition_id")) for page in selected}) != 1:
            continue
        if any(
            ref not in actual
            or actual[ref].language != language
            or actual[ref].source_sha256 != page.get("source_sha256")
            for ref, page in zip(source_refs, selected, strict=True)
        ):
            continue
        component_id = str(selected[0]["composition_id"])
        component_pages = [
            {
                **page,
                "source_path": page.get("source_path") or page["source_ref"],
                "composition_id": component_id,
                "composition_type": composition_type,
                "start_page": 1,
                "page_count": 1,
            }
            for page in selected
        ]
        matches.append({
            "plan_source": "registered-component",
            "physical_page_count": 1,
            "pages": component_pages,
        })
    if len(matches) > 1:
        raise ReferenceLayoutPlanError(
            f"registry has {len(matches)} owners for {composition_type} "
            f"{ir.model}/{ir.region}/{language}"
        )
    return matches[0] if matches else None


def apply_registered_storage_trouble_flow(
    ir: ManualIR,
    *,
    root: Path,
    bundle_root: Path,
    language: str,
    projected_by_path: dict[Path, Any],
) -> dict[str, Any] | None:
    """Bind the registered shared page and move its approved car-notice tail."""
    shared = find_registered_component_plan(
        ir, root=root, language=language,
        composition_type="storage_troubleshooting",
        source_refs=(
            "page/09_storage_and_maintenance.rst",
            f"page/troubleshooting_{language}.rst",
        ),
    )
    charging = find_registered_component_plan(
        ir, root=root, language=language,
        composition_type="charging_methods",
        source_refs=("page/08_charging_methods.rst",),
    )
    if shared is None or charging is None:
        return shared
    methods_path = bundle_root / "page" / "08_charging_methods.rst"
    storage_path = bundle_root / "page" / "09_storage_and_maintenance.rst"
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
    return shared


def resolve_registered_component_plans(
    ir: ManualIR,
    *,
    root: Path,
    bundle_root: Path,
    language: str,
    projected_by_path: dict[Path, Any],
) -> tuple[
    dict[str, Any] | None,
    dict[str, Any] | None,
    dict[str, Any] | None,
]:
    """Resolve no-plan shared-page, warranty, and charging ownership."""
    shared = apply_registered_storage_trouble_flow(
        ir,
        root=root,
        bundle_root=bundle_root,
        language=language,
        projected_by_path=projected_by_path,
    )
    warranty = find_registered_component_plan(
        ir,
        root=root,
        language=language,
        composition_type="warranty",
        source_refs=("page/11_warranty.rst",),
    )
    charging = find_registered_component_plan(
        ir,
        root=root,
        language=language,
        composition_type="charging_methods",
        source_refs=("page/08_charging_methods.rst",),
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
    "apply_registered_storage_trouble_flow",
    "apply_registered_warranty_footer_clearance",
    "find_registered_component_plan",
    "registered_warranty_blocks",
    "resolve_registered_component_plans",
]
