"""Source-driven standalone emphasis pill used in prose introductions."""
from __future__ import annotations

from .. import page_objects as _po
from ..params import param_pt
from ..primitives import cell, component_table, psr, wrap_table_paragraph
from .base import RenderContext


def render_emphasispill(
    spec: dict,
    ctx: RenderContext,
    *,
    tid: str,
    terminal: bool,
    span_columns: bool = True,
    measure_w: float | None = None,
) -> tuple[str, float]:
    text = " ".join(str(value).strip() for value in spec.get("texts", []) if value)
    if not text:
        return "", 0.0
    body_w = measure_w or ctx.text_measure
    size = param_pt(ctx.params, "type_warranty_lead_font_size", 7.0)
    height = max(14.2, param_pt(ctx.params, "comp_subbar_height", 13.89))
    width_factor = 0.50 if len(text) > 55 else 0.44
    width = min(body_w, max(96.0, len(text) * size * width_factor + 16.0))
    content = psr("HB Emphasis Pill", text, terminal=True)
    if ctx.add_story is None:
        table = component_table(
            tid,
            [width],
            [cell(f"{tid}c0", "0:0", content, fill="Color/HB Brand Dark",
                  stroke=False, top=2, bottom=2, left=7, right=7,
                  valign="CenterAlign")],
            role="warning",
        )
        return wrap_table_paragraph(table, terminal, span_columns), height + 2.0

    xml = _po.anchored_panel_paragraph(
        ctx.add_story,
        f"st_anchor_emphasis_{tid}",
        "source emphasis pill",
        [content],
        width,
        height,
        terminal=terminal,
        fill="Color/HB Brand Dark",
        stroke="Swatch/None",
        stroke_weight=0,
        radius=height / 2.0,
        inset=(1.0, 7.0, 1.0, 7.0),
        valign="CenterAlign",
        auto_height=False,
    )
    xml = xml.replace(
        "<ParagraphStyleRange ",
        '<ParagraphStyleRange SpaceBefore="1" SpaceAfter="1.5" ',
        1,
    )
    return xml, height + 2.5
