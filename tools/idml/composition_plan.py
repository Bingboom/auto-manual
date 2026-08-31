"""Renderer-neutral composition types and physical assembly instances.

The target plan chooses *which* reusable composition type owns a group of
source pages and where that group sits physically.  It never selects a model-
specific renderer branch.  Approved reference plans that predate the explicit
``composition_type`` field are projected by their ordered semantic PageRole
signature; new target assembly plans declare the type directly and are checked
against the same registry.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .page_roles import PageRole, classify_page_role


EXPLICIT_PLAN_SOURCES = frozenset({"approved-reference", "target-assembly"})


class CompositionPlanError(ValueError):
    """A target assembly cannot be projected onto shared compositions."""


@dataclass(frozen=True)
class CompositionTypeSpec:
    type_id: str
    source_roles: tuple[PageRole, ...]


@dataclass(frozen=True)
class CompositionInstance:
    composition_id: str
    composition_type: str
    start_page: int
    page_count: int
    language: str
    source_refs: tuple[str, ...]
    source_roles: tuple[PageRole, ...]

    @property
    def end_page(self) -> int:
        return self.start_page + self.page_count - 1


@dataclass(frozen=True)
class CompositionPlan:
    physical_page_count: int
    compositions: tuple[CompositionInstance, ...]

    def by_source_ref(self) -> dict[str, CompositionInstance]:
        return {
            source_ref: composition
            for composition in self.compositions
            for source_ref in composition.source_refs
        }


def _spec(type_id: str, *roles: PageRole) -> CompositionTypeSpec:
    return CompositionTypeSpec(type_id=type_id, source_roles=tuple(roles))


# Shared semantic composition vocabulary. Geometry and rendering live in the
# matching compositor modules and layout tokens; target plans contain no model
# identifiers or frame coordinates.
REGISTRY: dict[str, CompositionTypeSpec] = {
    spec.type_id: spec
    for spec in (
        _spec("front_cover", PageRole.COVER),
        _spec("preface", PageRole.PREFACE),
        _spec(
            "preface_safety_maintenance",
            PageRole.PREFACE,
            PageRole.SAFETY,
            PageRole.MAINTENANCE,
        ),
        _spec("toc", PageRole.TOC),
        _spec("safety", PageRole.SAFETY),
        _spec("symbols", PageRole.SYMBOLS),
        _spec("maintenance_symbols", PageRole.MAINTENANCE, PageRole.SYMBOLS),
        _spec("safety_symbols", PageRole.SAFETY, PageRole.SYMBOLS),
        _spec("fcc_inbox", PageRole.FCC, PageRole.INBOX),
        _spec(
            "fcc_inbox_overview",
            PageRole.FCC,
            PageRole.INBOX,
            PageRole.PRODUCT_OVERVIEW,
        ),
        _spec("inbox_overview", PageRole.INBOX, PageRole.PRODUCT_OVERVIEW),
        _spec("product_overview", PageRole.PRODUCT_OVERVIEW),
        _spec("lcd", PageRole.LCD),
        _spec("lcd_operations", PageRole.LCD, PageRole.OPERATION_GUIDE),
        _spec("operation", PageRole.OPERATION_GUIDE),
        _spec("ups_charging", PageRole.UPS_MODE, PageRole.CHARGING),
        _spec("charging_methods", PageRole.CHARGING_METHODS),
        _spec("connections", PageRole.CONNECTIONS),
        _spec("troubleshooting", PageRole.TROUBLESHOOTING_DATA),
        _spec("charging", PageRole.CHARGING),
        _spec(
            "charging_storage",
            PageRole.CHARGING,
            PageRole.STORAGE_MAINTENANCE,
        ),
        _spec(
            "storage_troubleshooting",
            PageRole.STORAGE_MAINTENANCE,
            PageRole.TROUBLESHOOTING_DATA,
        ),
        _spec(
            "storage_specifications",
            PageRole.STORAGE_MAINTENANCE,
            PageRole.SPEC,
        ),
        _spec("specifications", PageRole.SPEC),
        _spec("warranty", PageRole.WARRANTY),
        _spec("app", PageRole.APP_SETUP),
        _spec("regulatory_compliance", PageRole.REGULATORY_COMPLIANCE),
        _spec("back_cover", PageRole.BACK_COVER),
    )
}

_TYPE_BY_SIGNATURE = {
    spec.source_roles: spec.type_id
    for spec in REGISTRY.values()
}


def is_explicit_assembly_plan(plan: dict[str, Any] | None) -> bool:
    return (plan or {}).get("plan_source") in EXPLICIT_PLAN_SOURCES


def _positive_int(value: object, *, label: str) -> int:
    if isinstance(value, bool):
        raise CompositionPlanError(f"{label} must be a positive integer")
    try:
        result = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise CompositionPlanError(f"{label} must be a positive integer") from exc
    if result <= 0:
        raise CompositionPlanError(f"{label} must be a positive integer")
    return result


def _page_role(entry: dict[str, Any]) -> PageRole:
    raw = entry.get("page_role")
    if isinstance(raw, str) and raw:
        try:
            return PageRole(raw)
        except ValueError as exc:
            raise CompositionPlanError(f"unknown page_role: {raw}") from exc
    source_ref = str(entry.get("source_ref") or "")
    return classify_page_role(Path(source_ref))


def _composition_type(
    entries: list[dict[str, Any]],
    roles: tuple[PageRole, ...],
) -> str:
    explicit = {
        str(entry["composition_type"])
        for entry in entries
        if entry.get("composition_type") is not None
    }
    if len(explicit) > 1:
        raise CompositionPlanError("one composition_id has multiple composition types")
    if explicit:
        type_id = next(iter(explicit))
        spec = REGISTRY.get(type_id)
        if spec is None:
            raise CompositionPlanError(f"unregistered composition_type: {type_id}")
        if spec.source_roles != roles:
            wanted = tuple(role.value for role in spec.source_roles)
            actual = tuple(role.value for role in roles)
            raise CompositionPlanError(
                f"composition_type {type_id} requires roles {wanted}, got {actual}"
            )
        return type_id
    try:
        return _TYPE_BY_SIGNATURE[roles]
    except KeyError as exc:
        signature = tuple(role.value for role in roles)
        raise CompositionPlanError(
            f"no shared composition type for source roles {signature}"
        ) from exc


def build_composition_plan(plan: dict[str, Any]) -> CompositionPlan:
    """Group a normalized page plan into validated composition instances."""
    physical_page_count = _positive_int(
        plan.get("physical_page_count"),
        label="physical_page_count",
    )
    raw_pages = plan.get("pages")
    if not isinstance(raw_pages, list) or not raw_pages:
        raise CompositionPlanError("page plan must contain pages")

    grouped: dict[str, list[dict[str, Any]]] = {}
    order: list[str] = []
    seen_refs: set[str] = set()
    for index, raw in enumerate(raw_pages):
        if not isinstance(raw, dict):
            raise CompositionPlanError(f"pages[{index}] must be an object")
        source_ref = str(raw.get("source_ref") or "")
        if not source_ref or source_ref in seen_refs:
            raise CompositionPlanError(
                f"source_ref must be non-empty and unique: {source_ref!r}"
            )
        seen_refs.add(source_ref)
        composition_id = str(raw.get("composition_id") or "")
        if not composition_id:
            raise CompositionPlanError(f"{source_ref}: composition_id is required")
        if composition_id not in grouped:
            grouped[composition_id] = []
            order.append(composition_id)
        grouped[composition_id].append(raw)

    compositions: list[CompositionInstance] = []
    for composition_id in order:
        entries = grouped[composition_id]
        first = entries[0]
        start_page = _positive_int(
            first.get("latex_start_page", first.get("start_page")),
            label=f"{composition_id}.start_page",
        )
        page_count = _positive_int(
            first.get("planned_page_count", first.get("page_count")),
            label=f"{composition_id}.page_count",
        )
        ranges = {
            (
                _positive_int(
                    entry.get("latex_start_page", entry.get("start_page")),
                    label=f"{composition_id}.start_page",
                ),
                _positive_int(
                    entry.get("planned_page_count", entry.get("page_count")),
                    label=f"{composition_id}.page_count",
                ),
            )
            for entry in entries
        }
        if ranges != {(start_page, page_count)}:
            raise CompositionPlanError(
                f"composition {composition_id} has inconsistent physical ranges"
            )
        languages = {str(entry.get("language") or "") for entry in entries}
        if len(languages) != 1:
            raise CompositionPlanError(
                f"composition {composition_id} spans multiple languages"
            )
        roles = tuple(_page_role(entry) for entry in entries)
        type_id = _composition_type(entries, roles)
        compositions.append(
            CompositionInstance(
                composition_id=composition_id,
                composition_type=type_id,
                start_page=start_page,
                page_count=page_count,
                language=next(iter(languages)),
                source_refs=tuple(str(entry["source_ref"]) for entry in entries),
                source_roles=roles,
            )
        )

    cursor = 1
    for composition in sorted(
        compositions,
        key=lambda item: (item.start_page, item.composition_id),
    ):
        if composition.start_page != cursor:
            relation = "overlaps" if composition.start_page < cursor else "leaves a gap"
            raise CompositionPlanError(
                f"composition {composition.composition_id} {relation} at page "
                f"{composition.start_page}; expected {cursor}"
            )
        cursor = composition.end_page + 1
    if cursor != physical_page_count + 1:
        raise CompositionPlanError(
            f"composition coverage ends at page {cursor - 1}, expected "
            f"{physical_page_count}"
        )
    return CompositionPlan(
        physical_page_count=physical_page_count,
        compositions=tuple(compositions),
    )


__all__ = (
    "EXPLICIT_PLAN_SOURCES",
    "REGISTRY",
    "CompositionInstance",
    "CompositionPlan",
    "CompositionPlanError",
    "CompositionTypeSpec",
    "build_composition_plan",
    "is_explicit_assembly_plan",
)
