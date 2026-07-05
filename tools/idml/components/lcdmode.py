"""LCD screen-mode table component (componentization P2)."""
from __future__ import annotations

from ..primitives import cell, component_table, image_cell_content, psr, wrap_table_paragraph
from .base import RenderContext, figure_paragraph


def render_lcdmode(spec: dict, ctx: RenderContext, *, tid: str, terminal: bool,
                   span_columns: bool = True,
                   measure_w: float | None = None) -> tuple[str, float]:
    # LCD screen mode table (the last annotated-insert holdout):
    # state | action | description rows, LCD art above the table
    body_w = measure_w or ctx.text_measure
    groups = spec.get("groups", [])
    img_ref = spec.get("img", "")
    art = ""
    img = ctx.resolve_bundle_image(img_ref) if img_ref else None
    if img is not None:
        iw, ih = ctx.art_frame_size(img, max_w=110.0)
        art = figure_paragraph(image_cell_content(f"{tid}art", img, iw, ih))
    cols = [body_w * 0.22, body_w * 0.18, body_w * 0.60]
    cells = []
    ri = 0
    for g in groups:
        for ai, (action, desc) in enumerate(g.get("actions", [])):
            state_txt = g.get("state", "") if ai == 0 else ""
            cells.append(cell(f"{tid}c{ri}_0", f"0:{ri}",
                              psr("HB Spec Label", state_txt, terminal=True)))
            cells.append(cell(f"{tid}c{ri}_1", f"1:{ri}",
                              psr("HB Spec Label", action, terminal=True)))
            cells.append(cell(f"{tid}c{ri}_2", f"2:{ri}",
                              psr("HB Spec Value", desc, terminal=True)))
            ri += 1
    table = component_table(tid, cols, cells, n_rows=ri)
    xml = art + wrap_table_paragraph(table, terminal, span_columns)
    return xml, 70.0 + 12.0 * ri
