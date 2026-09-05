"""Project approved/reference source-page data into a semantic PagePlan."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .model import (
    PagePlan,
    PagePlanError,
    PageTemplateRole,
    SourcePagePlan,
    policies_for_role,
    validate_page_plan,
)


# A composition owns one physical page policy even when several semantic source
# roles are assembled onto that page. Keep only exceptional policies here;
# ordinary compositions inherit the source role's standard policy.
_COMPOSITION_TEMPLATE_ROLES = {
    "front_cover": PageTemplateRole.FRONT_COVER,
    "preface": PageTemplateRole.NO_FOOTER,
    "preface_safety_maintenance": PageTemplateRole.STANDARD,
    "toc": PageTemplateRole.TOC,
    "back_cover": PageTemplateRole.BACK_COVER,
}


def page_template_role_for_composition_type(
    composition_type: object,
) -> PageTemplateRole | None:
    normalized = str(composition_type or "").strip().casefold().replace("-", "_")
    return _COMPOSITION_TEMPLATE_ROLES.get(normalized)


def page_template_role_for_assembly_role(role: str) -> PageTemplateRole:
    normalized = str(role).strip().casefold().replace("_", "-")
    if normalized == "cover":
        return PageTemplateRole.FRONT_COVER
    if normalized == "back-cover":
        return PageTemplateRole.BACK_COVER
    if normalized == "toc":
        return PageTemplateRole.TOC
    if normalized == "preface":
        return PageTemplateRole.NO_FOOTER
    if normalized.startswith("extension:"):
        return PageTemplateRole.EXTENSION
    return PageTemplateRole.STANDARD


def page_template_role_for_source_ref(source_ref: str | Path) -> PageTemplateRole:
    stem = Path(source_ref).stem.casefold()
    if stem.startswith("cover"):
        return PageTemplateRole.FRONT_COVER
    if stem in {"00_preface", "00_preface_single_language"}:
        return PageTemplateRole.NO_FOOTER
    if stem == "00_toc":
        return PageTemplateRole.TOC
    if stem.endswith("99_back_cover") or stem == "99_back_cover":
        return PageTemplateRole.BACK_COVER
    return PageTemplateRole.STANDARD


def _source_page(
    entry: dict[str, Any],
    *,
    ordinal: int,
) -> SourcePagePlan:
    try:
        source_ref = str(entry["source_ref"])
        physical_start = int(entry["latex_start_page"])
        physical_span = int(entry["planned_page_count"])
        composition_id = str(entry["composition_id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise PagePlanError(
            f"page-plan entry {ordinal} lacks approved physical mapping: {exc}"
        ) from exc
    assembly_role = str(entry.get("page_role") or "")
    role = page_template_role_for_composition_type(entry.get("composition_type"))
    if role is None:
        role = (
            page_template_role_for_assembly_role(assembly_role)
            if assembly_role
            else page_template_role_for_source_ref(source_ref)
        )
    footer_policy, folio_policy = policies_for_role(role)
    extension_id = (
        assembly_role.split(":", 1)[1]
        if role is PageTemplateRole.EXTENSION
        else None
    )
    editability = "finished-art" if role is PageTemplateRole.FRONT_COVER else "source-driven"
    return SourcePagePlan(
        source_ref=source_ref,
        language=str(entry.get("language") or ""),
        ordinal=ordinal,
        physical_start=physical_start,
        physical_span=physical_span,
        composition_id=composition_id,
        assembly_role=assembly_role or role.value,
        role=role,
        footer_policy=footer_policy,
        folio_policy=folio_policy,
        editability=editability,
        extension_id=extension_id,
    )


def build_renderer_page_plan(reference_plan: dict[str, Any]) -> PagePlan:
    pages = reference_plan.get("pages")
    if not isinstance(pages, list):
        raise PagePlanError("reference plan pages must be a list")
    plan = PagePlan(
        source_pages=tuple(
            _source_page(entry, ordinal=ordinal)
            for ordinal, entry in enumerate(pages, start=1)
            if isinstance(entry, dict)
        ),
        physical_page_count=int(reference_plan.get("physical_page_count") or 0),
        constraints=("front-cover-finished-art",),
    )
    if len(plan.source_pages) != len(pages):
        raise PagePlanError("reference plan pages must contain objects only")
    issues = validate_page_plan(plan)
    if issues:
        raise PagePlanError("; ".join(issues))
    return plan


def legacy_folio_page_plan(
    physical_page_count: int,
    *,
    has_back_cover: bool,
    front_matter_roles: tuple[str, ...] = ("cover", "preface", "toc"),
) -> PagePlan:
    """Compatibility plan for non-reference IDML builds, without XML sniffing."""
    if (not front_matter_roles or front_matter_roles[0] != "cover"
            or len(set(front_matter_roles)) != len(front_matter_roles)
            or any(role not in {"cover", "preface", "toc"} for role in front_matter_roles)):
        raise PagePlanError("invalid front-matter roles")
    pages: list[SourcePagePlan] = []
    for ordinal in range(1, physical_page_count + 1):
        if ordinal <= len(front_matter_roles):
            assembly_role = front_matter_roles[ordinal - 1]
            role = page_template_role_for_assembly_role(assembly_role)
        elif has_back_cover and ordinal == physical_page_count:
            role = PageTemplateRole.BACK_COVER
            assembly_role = "back_cover"
        else:
            role = PageTemplateRole.STANDARD
            assembly_role = "legacy-standard"
        footer_policy, folio_policy = policies_for_role(role)
        pages.append(
            SourcePagePlan(
                source_ref=f"legacy/physical-{ordinal}.rst",
                language="",
                ordinal=ordinal,
                physical_start=ordinal,
                physical_span=1,
                composition_id=f"legacy-physical-{ordinal}",
                assembly_role=assembly_role,
                role=role,
                footer_policy=footer_policy,
                folio_policy=folio_policy,
                editability=(
                    "finished-art"
                    if role is PageTemplateRole.FRONT_COVER
                    else "source-driven"
                ),
            )
        )
    plan = PagePlan(
        source_pages=tuple(pages),
        physical_page_count=physical_page_count,
        constraints=("front-cover-finished-art",),
    )
    issues = validate_page_plan(plan)
    if issues:
        raise PagePlanError("; ".join(issues))
    return plan
