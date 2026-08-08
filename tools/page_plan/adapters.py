"""Renderer bindings for the shared semantic PagePlan."""
from __future__ import annotations

from dataclasses import dataclass

from .model import (
    FolioPolicy,
    PagePlan,
    PageTemplateRole,
    PhysicalPagePlan,
    RendererCapability,
)


@dataclass(frozen=True)
class PageAdapterBinding:
    renderer: str
    capability: RendererCapability
    page_template: str | None
    footer_style: str | None
    page_number_style: str | None
    pagination: str


def _fixed_template(role: PageTemplateRole, bindings: dict[str, str]) -> str:
    if role is PageTemplateRole.STANDARD:
        return bindings["standard"]
    if role in {PageTemplateRole.NO_FOOTER, PageTemplateRole.TOC}:
        return bindings["no-footer"]
    if role in {PageTemplateRole.FRONT_COVER, PageTemplateRole.BACK_COVER}:
        return bindings["cover"]
    return bindings["extension"]


def latex_page_binding(page: PhysicalPagePlan) -> PageAdapterBinding:
    return PageAdapterBinding(
        renderer="latex",
        capability=RendererCapability.RENDERED,
        page_template=_fixed_template(
            page.role,
            {
                "standard": "HBPageTemplateStandard",
                "no-footer": "HBPageTemplateNoFooter",
                "cover": "HBPageTemplateCover",
                "extension": "HBPageTemplateStandard",
            },
        ),
        footer_style=(
            "HBTypeFooter" if page.folio_policy is FolioPolicy.SHOW else None
        ),
        page_number_style=(
            "HBTypePageNumber" if page.folio_policy is FolioPolicy.SHOW else None
        ),
        pagination="fixed",
    )


def idml_page_binding(page: PhysicalPagePlan) -> PageAdapterBinding:
    return PageAdapterBinding(
        renderer="idml",
        capability=RendererCapability.RENDERED,
        page_template=_fixed_template(
            page.role,
            {
                "standard": "HB Standard Page",
                "no-footer": "HB No Footer Page",
                "cover": "HB Cover Page",
                "extension": "HB Standard Page",
            },
        ),
        footer_style=("HB Footer" if page.folio_policy is FolioPolicy.SHOW else None),
        page_number_style=(
            "HB Page Number" if page.folio_policy is FolioPolicy.SHOW else None
        ),
        pagination="fixed",
    )


def word_page_binding(role: PageTemplateRole) -> PageAdapterBinding:
    footer = role is PageTemplateRole.STANDARD
    return PageAdapterBinding(
        renderer="word",
        capability=RendererCapability.PROJECTION_ONLY,
        page_template=role.value,
        footer_style="section-footer" if footer else None,
        page_number_style="section-page-number" if footer else None,
        pagination="word-section-projection",
    )


def web_pagination_binding(plan: PagePlan) -> PageAdapterBinding:
    return PageAdapterBinding(
        renderer="web",
        capability=plan.capability("web"),
        page_template=None,
        footer_style=None,
        page_number_style=None,
        pagination="not-applicable",
    )
