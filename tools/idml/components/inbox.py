"""WHAT'S IN THE BOX three-card component (componentization P2)."""
from __future__ import annotations

from ..primitives import cell, component_table, image_cell_content, psr, wrap_table_paragraph
from .base import RenderContext, figure_paragraph


def render_inbox(spec: dict, ctx: RenderContext, *, tid: str, terminal: bool,
                 span_columns: bool = True,
                 measure_w: float | None = None) -> tuple[str, float]:
    body_w = measure_w or ctx.text_measure
    items = spec.get("items", [])[:3]
    cols = [body_w / 3.0] * 3
    cells = []
    for ci, item in enumerate(items):
        img = ctx.resolve_bundle_image(item.get("img", ""))
        icon_w = body_w / 3.0 - 14
        icon = ""
        if img is not None:
            iw, ih = ctx.art_frame_size(img, max_w=min(icon_w, 60.0))
            icon = image_cell_content(f"{tid}i{ci}", img, iw, ih)
        content = (
            psr("HB Card Number", str(ci + 1)) +
            figure_paragraph(icon)
            + psr("HB InBox Label", item.get("label", ""), terminal=True))
        cells.append(cell(
            f"{tid}c0_{ci}", f"{ci}:0", content,
            top=9, bottom=10, left=6, right=6,
        ))
    table = component_table(tid, cols, cells, role="layout")
    return wrap_table_paragraph(table, terminal, span_columns), 110.0
