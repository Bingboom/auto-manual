"""Renderer-neutral semantic page planning.

The package shares page roles and policies.  Renderer-specific geometry stays
in the LaTeX, IDML, Word, and Web adapters.
"""
from .adapters import (
    PageAdapterBinding,
    idml_page_binding,
    latex_page_binding,
    web_pagination_binding,
    word_page_binding,
)
from .model import (
    FolioPolicy,
    FooterPolicy,
    PagePlan,
    PagePlanError,
    PageTemplateRole,
    PhysicalPagePlan,
    RendererCapability,
    SourcePagePlan,
    validate_page_plan,
)
from .projection import (
    build_renderer_page_plan,
    legacy_folio_page_plan,
    page_template_role_for_assembly_role,
    page_template_role_for_source_ref,
)

__all__ = (
    "FolioPolicy",
    "FooterPolicy",
    "PageAdapterBinding",
    "PagePlan",
    "PagePlanError",
    "PageTemplateRole",
    "PhysicalPagePlan",
    "RendererCapability",
    "SourcePagePlan",
    "build_renderer_page_plan",
    "idml_page_binding",
    "latex_page_binding",
    "legacy_folio_page_plan",
    "page_template_role_for_assembly_role",
    "page_template_role_for_source_ref",
    "validate_page_plan",
    "web_pagination_binding",
    "word_page_binding",
)
