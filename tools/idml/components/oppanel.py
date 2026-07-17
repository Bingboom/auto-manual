"""Operation panel component (template-parity P3).

The V2.0 master's operation sections are bordered panels: illustration
left, bold On/Off rows right, an optional grey "Prerequisite" pill
above. Detected from the prose blocks by tools/idml/oppanel.transform;
this renderer builds the panel as a one-row two-column bordered table
(rounded page-level objects don't exist inside flowed stories).
"""
from __future__ import annotations

from ..primitives import (
    cell,
    component_table,
    image_cell_content,
    psr,
    wrap_table_paragraph,
)
from .base import RenderContext, figure_paragraph


def render_oppanel(spec: dict, ctx: RenderContext, *, tid: str, terminal: bool,
                   span_columns: bool = True,
                   measure_w: float | None = None) -> tuple[str, float]:
    body_w = measure_w or ctx.text_measure
    rows = [tuple(r) for r in spec.get("rows", [])]
    prereq = (spec.get("prereq") or "").strip()

    icon = ""
    img_h = 0.0
    ref = (spec.get("image") or "").strip()
    asset = ctx.resolve_bundle_image(ref) if ref else None
    if asset is not None and asset.exists():
        # The governed operation artwork already contains the product,
        # connector callouts, and reserved label zones.  Preserve that canvas
        # at reference scale; the previous half-column + height cap reduced it
        # to roughly one third of the intended visual area.
        iw, ih = ctx.art_frame_size(asset, max_w=body_w * 0.75)
        icon = figure_paragraph(
            image_cell_content(f"{tid}img", asset, iw, ih),
            tail="<Content></Content>")
        img_h = ih

    right_parts = []
    if prereq:
        right_parts.append(psr("HB Notice Label", prereq))
    for ri, (label, instruction) in enumerate(rows):
        right_parts.append(psr("HB Title L2", label))
        gap = "" if ri == len(rows) - 1 else "\n"
        right_parts.append(psr("HB Body", instruction + gap))
    if right_parts:
        right_parts[-1] = right_parts[-1].replace("<Br/>", "", 1)
    right = "".join(right_parts)

    img_col = body_w * 0.8
    rows_h = (14.0 if prereq else 0.0) + sum(
        9.0 + 7.5 * max(1, len(instr) // 60 + 1) for _, instr in rows)
    est = max(img_h + 12.0, rows_h + 12.0, 40.0)
    if ctx.add_story is not None:
        # master parity: rounded light-grey outline, no inner grid
        from .. import page_objects as _po
        inner_w = body_w - 8.0
        icol = inner_w * 0.8
        cells = [
            cell(f"{tid}c0", "0:0", icon, stroke=False,
                 top=5, bottom=5, left=5, right=4),
            cell(f"{tid}c1", "1:0", right, stroke=False,
                 top=6, bottom=5, left=6, right=5),
        ]
        inner = wrap_table_paragraph(component_table(
            tid, [icol, max(60.0, inner_w - icol)], cells,
            role="warning"), True, False)
        xml = _po.anchored_panel_paragraph(
            ctx.add_story, f"st_anchor_oppanel_{tid}", "operation panel",
            [inner], body_w, est * 1.15 + 8.0, terminal=terminal,
            stroke="Color/HB Border K10", stroke_weight=1.1, radius=10.0,
            inset=(3, 3, 3, 3), valign="TopAlign", auto_height=True)
        return xml, est + 8.0
    cols = [img_col, max(60.0, body_w - img_col)]
    cells = [
        cell(f"{tid}c0", "0:0", icon, top=5, bottom=5, left=5, right=4),
        cell(f"{tid}c1", "1:0", right, top=6, bottom=5, left=6, right=5),
    ]
    table = component_table(tid, cols, cells, role="warning")
    return wrap_table_paragraph(table, terminal, span_columns), est
