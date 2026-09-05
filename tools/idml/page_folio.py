"""PagePlan-driven folio frames for the composed IDML manual.

The shared semantic PagePlan owns suppression and numbering.  This post-pass
does not inspect localized titles, story IDs, links, or spread XML.
"""
from __future__ import annotations

from typing import Any

from tools.page_plan import (
    FolioPolicy,
    PagePlan,
    idml_page_binding,
    legacy_folio_page_plan,
)


def folio_frame_bounds(writer, folio: int) -> tuple[float, float, float, float]:
    """Return the approved alternating outer-corner folio frame geometry."""
    y2 = writer.page_h / 2 - 11.0
    if folio % 2:
        x1 = -writer.page_w / 2 + writer.m_l
        x2 = x1 + 24.0
    else:
        x2 = writer.page_w / 2 - writer.m_r
        x1 = x2 - 24.0
    return x1, y2 - 10.0, x2, y2


def _resolve_page_plan(
    raw_plan: dict[str, Any] | None,
    *,
    physical_page_count: int,
    has_back_cover: bool,
) -> PagePlan:
    renderer_plan = (raw_plan or {}).get("renderer_page_plan")
    if isinstance(renderer_plan, dict):
        plan = PagePlan.from_dict(renderer_plan)
        if plan.physical_page_count != physical_page_count:
            raise ValueError(
                "renderer PagePlan physical count does not match IDML spreads "
                f"({plan.physical_page_count} != {physical_page_count})"
            )
        return plan
    return legacy_folio_page_plan(
        physical_page_count,
        has_back_cover=has_back_cover,
        front_matter_roles=tuple((raw_plan or {}).get(
            "front_matter_roles", ("cover", "preface", "toc"))),
    )


def apply(
    writer,
    add_story_parts,
    psr,
    *,
    page_plan: dict[str, Any] | None = None,
    has_back_cover: bool = False,
) -> int:
    """Append folios selected entirely by semantic PagePlan roles."""
    applied = 0
    plan = _resolve_page_plan(
        page_plan,
        physical_page_count=len(writer.spreads),
        has_back_cover=has_back_cover,
    )
    for slot, (sid, xml) in enumerate(writer.spreads):
        physical_page = plan.physical_page(slot + 1)
        if physical_page.folio_policy is FolioPolicy.SUPPRESS:
            continue
        folio = physical_page.folio_number
        if folio is None:
            raise ValueError(f"physical page {slot + 1} has no PagePlan folio")
        binding = idml_page_binding(physical_page)
        if binding.page_number_style is None:
            raise ValueError(f"physical page {slot + 1} has no IDML page-number style")
        story_sid = add_story_parts(
            f"st_folio_{slot}", f"Folio {folio}",
            [psr(binding.page_number_style, f"{folio:02d}", terminal=True)])
        x1, y1, x2, y2 = folio_frame_bounds(writer, folio)
        frame = writer._frame_xml(
            f"tf_folio_{slot}", story_sid,
            x1, y1, x2, y2, inset=(0, 0, 0, 0))
        assert xml.rstrip().endswith("</idPkg:Spread>")
        xml = xml.replace("</Spread>\n</idPkg:Spread>",
                          frame + "</Spread>\n</idPkg:Spread>")
        writer.spreads[slot] = (sid, xml)
        applied += 1
    return applied
