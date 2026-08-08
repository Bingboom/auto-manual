"""Immutable renderer-neutral PagePlan model and validation."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


SCHEMA_VERSION = "renderer-page-plan/v1"


class PagePlanError(ValueError):
    """A semantic page plan is incomplete or contradictory."""


class PageTemplateRole(str, Enum):
    STANDARD = "standard"
    NO_FOOTER = "no-footer"
    FRONT_COVER = "front-cover"
    BACK_COVER = "back-cover"
    TOC = "toc"
    EXTENSION = "extension"


class FooterPolicy(str, Enum):
    SHOW = "show"
    SUPPRESS = "suppress"


class FolioPolicy(str, Enum):
    SHOW = "show"
    SUPPRESS = "suppress"


class RendererCapability(str, Enum):
    RENDERED = "rendered"
    PROJECTION_ONLY = "projection-only"
    NOT_APPLICABLE = "not-applicable"


DEFAULT_RENDERER_CAPABILITIES = (
    ("latex", RendererCapability.RENDERED),
    ("idml", RendererCapability.RENDERED),
    ("word", RendererCapability.PROJECTION_ONLY),
    ("web", RendererCapability.NOT_APPLICABLE),
)


def policies_for_role(
    role: PageTemplateRole,
) -> tuple[FooterPolicy, FolioPolicy]:
    if role is PageTemplateRole.STANDARD:
        return FooterPolicy.SHOW, FolioPolicy.SHOW
    return FooterPolicy.SUPPRESS, FolioPolicy.SUPPRESS


@dataclass(frozen=True)
class SourcePagePlan:
    source_ref: str
    language: str
    ordinal: int
    physical_start: int
    physical_span: int
    composition_id: str
    assembly_role: str
    role: PageTemplateRole
    footer_policy: FooterPolicy
    folio_policy: FolioPolicy
    editability: str = "source-driven"
    extension_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "source_ref": self.source_ref,
            "language": self.language,
            "ordinal": self.ordinal,
            "physical_start": self.physical_start,
            "physical_span": self.physical_span,
            "composition_id": self.composition_id,
            "assembly_role": self.assembly_role,
            "role": self.role.value,
            "footer_policy": self.footer_policy.value,
            "folio_policy": self.folio_policy.value,
            "editability": self.editability,
        }
        if self.extension_id is not None:
            payload["extension_id"] = self.extension_id
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> SourcePagePlan:
        try:
            return cls(
                source_ref=str(payload["source_ref"]),
                language=str(payload["language"]),
                ordinal=int(payload["ordinal"]),
                physical_start=int(payload["physical_start"]),
                physical_span=int(payload["physical_span"]),
                composition_id=str(payload["composition_id"]),
                assembly_role=str(payload["assembly_role"]),
                role=PageTemplateRole(payload["role"]),
                footer_policy=FooterPolicy(payload["footer_policy"]),
                folio_policy=FolioPolicy(payload["folio_policy"]),
                editability=str(payload.get("editability", "source-driven")),
                extension_id=(
                    str(payload["extension_id"])
                    if payload.get("extension_id") is not None
                    else None
                ),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise PagePlanError(f"invalid source page plan: {exc}") from exc


@dataclass(frozen=True)
class PhysicalPagePlan:
    ordinal: int
    role: PageTemplateRole
    footer_policy: FooterPolicy
    folio_policy: FolioPolicy
    folio_number: int | None
    source_refs: tuple[str, ...]
    composition_ids: tuple[str, ...]


@dataclass(frozen=True)
class PagePlan:
    source_pages: tuple[SourcePagePlan, ...]
    physical_page_count: int
    renderer_capabilities: tuple[
        tuple[str, RendererCapability], ...
    ] = DEFAULT_RENDERER_CAPABILITIES
    constraints: tuple[str, ...] = ()
    schema_version: str = SCHEMA_VERSION

    def capability(self, renderer: str) -> RendererCapability:
        capabilities = dict(self.renderer_capabilities)
        try:
            return capabilities[renderer]
        except KeyError as exc:
            raise PagePlanError(f"unknown PagePlan renderer: {renderer}") from exc

    def physical_pages(self) -> tuple[PhysicalPagePlan, ...]:
        coverage: list[list[SourcePagePlan]] = [
            [] for _ in range(self.physical_page_count)
        ]
        for page in self.source_pages:
            for physical in range(
                page.physical_start,
                page.physical_start + page.physical_span,
            ):
                if 1 <= physical <= self.physical_page_count:
                    coverage[physical - 1].append(page)

        first_folio = next(
            (
                ordinal
                for ordinal, pages in enumerate(coverage, start=1)
                if pages and pages[0].folio_policy is FolioPolicy.SHOW
            ),
            None,
        )
        physical_pages: list[PhysicalPagePlan] = []
        for ordinal, pages in enumerate(coverage, start=1):
            if not pages:
                raise PagePlanError(f"physical page {ordinal} has no source coverage")
            roles = {page.role for page in pages}
            footer_policies = {page.footer_policy for page in pages}
            folio_policies = {page.folio_policy for page in pages}
            if len(roles) != 1 or len(footer_policies) != 1 or len(folio_policies) != 1:
                refs = ", ".join(page.source_ref for page in pages)
                raise PagePlanError(
                    f"physical page {ordinal} has conflicting page policies: {refs}"
                )
            role = next(iter(roles))
            footer_policy = next(iter(footer_policies))
            folio_policy = next(iter(folio_policies))
            folio_number = (
                ordinal - first_folio + 1
                if folio_policy is FolioPolicy.SHOW and first_folio is not None
                else None
            )
            physical_pages.append(
                PhysicalPagePlan(
                    ordinal=ordinal,
                    role=role,
                    footer_policy=footer_policy,
                    folio_policy=folio_policy,
                    folio_number=folio_number,
                    source_refs=tuple(page.source_ref for page in pages),
                    composition_ids=tuple(
                        dict.fromkeys(page.composition_id for page in pages)
                    ),
                )
            )
        return tuple(physical_pages)

    def physical_page(self, ordinal: int) -> PhysicalPagePlan:
        if ordinal <= 0 or ordinal > self.physical_page_count:
            raise PagePlanError(f"physical page ordinal is out of range: {ordinal}")
        return self.physical_pages()[ordinal - 1]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "physical_page_count": self.physical_page_count,
            "renderer_capabilities": {
                name: capability.value
                for name, capability in self.renderer_capabilities
            },
            "constraints": list(self.constraints),
            "source_pages": [page.to_dict() for page in self.source_pages],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> PagePlan:
        try:
            raw_capabilities = payload["renderer_capabilities"]
            if not isinstance(raw_capabilities, dict):
                raise TypeError("renderer_capabilities must be an object")
            plan = cls(
                schema_version=str(payload["schema_version"]),
                physical_page_count=int(payload["physical_page_count"]),
                renderer_capabilities=tuple(
                    (str(name), RendererCapability(value))
                    for name, value in raw_capabilities.items()
                ),
                constraints=tuple(str(item) for item in payload.get("constraints", [])),
                source_pages=tuple(
                    SourcePagePlan.from_dict(item)
                    for item in payload["source_pages"]
                ),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise PagePlanError(f"invalid PagePlan payload: {exc}") from exc
        issues = validate_page_plan(plan)
        if issues:
            raise PagePlanError("; ".join(issues))
        return plan


def validate_page_plan(plan: PagePlan) -> list[str]:
    issues: list[str] = []
    if plan.schema_version != SCHEMA_VERSION:
        issues.append(f"schema_version must be {SCHEMA_VERSION}")
    if plan.physical_page_count <= 0:
        issues.append("physical_page_count must be positive")
    capabilities = dict(plan.renderer_capabilities)
    if set(capabilities) != {"latex", "idml", "word", "web"}:
        issues.append("renderer capabilities must declare latex, idml, word, and web")
    elif capabilities != dict(DEFAULT_RENDERER_CAPABILITIES):
        issues.append("renderer capabilities do not match the PagePlan v1 contract")

    refs: set[str] = set()
    for expected_ordinal, page in enumerate(plan.source_pages, start=1):
        if page.ordinal != expected_ordinal:
            issues.append(f"{page.source_ref}: ordinal must be {expected_ordinal}")
        if not page.source_ref or page.source_ref in refs:
            issues.append(f"source_ref must be non-empty and unique: {page.source_ref!r}")
        refs.add(page.source_ref)
        if page.physical_start <= 0 or page.physical_span <= 0:
            issues.append(f"{page.source_ref}: physical start/span must be positive")
        elif page.physical_start + page.physical_span - 1 > plan.physical_page_count:
            issues.append(f"{page.source_ref}: physical span exceeds the plan")
        expected_footer, expected_folio = policies_for_role(page.role)
        if (page.footer_policy, page.folio_policy) != (
            expected_footer,
            expected_folio,
        ):
            issues.append(f"{page.source_ref}: policies do not match role {page.role.value}")
        if page.role is PageTemplateRole.EXTENSION and not page.extension_id:
            issues.append(f"{page.source_ref}: extension role requires extension_id")
        if page.role is not PageTemplateRole.EXTENSION and page.extension_id:
            issues.append(f"{page.source_ref}: extension_id is only valid for extension role")
        if page.role is PageTemplateRole.FRONT_COVER and page.editability != "finished-art":
            issues.append(f"{page.source_ref}: front cover must declare finished-art")
        if page.role is PageTemplateRole.BACK_COVER and page.editability != "source-driven":
            issues.append(f"{page.source_ref}: back cover must remain source-driven")

    try:
        plan.physical_pages()
    except PagePlanError as exc:
        issues.append(str(exc))
    if any(page.role is PageTemplateRole.FRONT_COVER for page in plan.source_pages):
        if "front-cover-finished-art" not in plan.constraints:
            issues.append("front-cover-finished-art constraint is required")
    return issues
