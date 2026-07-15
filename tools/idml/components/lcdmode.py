"""LCD screen-mode table component (componentization P2)."""
from __future__ import annotations

from ..params import param_pt
from ..primitives import cell, component_table, image_cell_content, psr, wrap_table_paragraph
from .base import RenderContext, figure_paragraph
from .rounded_table import rounded_table_panel, table_text_indent


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
    inner_w = body_w - 1.5
    state_w = param_pt(ctx.params, "comp_lcd_mode_state_col_width", 59.53)
    action_w = param_pt(ctx.params, "comp_lcd_mode_action_col_width", 42.52)
    cols = [state_w, action_w, inner_w - state_w - action_w]
    rule = max(0.2, param_pt(ctx.params, "comp_table_outer_rule", 0.75) / 2.0)
    text_indent = table_text_indent(ctx.params)
    cells = []
    ri = 0
    for g in groups:
        actions = g.get("actions", [])
        for ai, (action, desc) in enumerate(actions):
            if ai == 0:
                state_cell = cell(
                    f"{tid}c{ri}_0", f"0:{ri}",
                    psr("HB Spec Label", g.get("state", ""), terminal=True),
                    fill="Color/HB Bg K05", top=2, bottom=2,
                    left=text_indent, right=3,
                    edge_weight=rule, edge_color="Color/HB Line K40",
                    valign="CenterAlign",
                ).replace('RowSpan="1"', f'RowSpan="{len(actions)}"', 1)
                cells.append(state_cell)
            cells.append(cell(f"{tid}c{ri}_1", f"1:{ri}",
                              psr("HB Spec Label", action, terminal=True),
                              top=2, bottom=2, left=text_indent, right=3,
                              edge_weight=rule, edge_color="Color/HB Line K40",
                              valign="CenterAlign"))
            cells.append(cell(f"{tid}c{ri}_2", f"2:{ri}",
                              psr("HB Spec Value", desc, terminal=True),
                              top=2, bottom=2, left=text_indent, right=4,
                              edge_weight=rule, edge_color="Color/HB Line K40",
                              valign="CenterAlign"))
            ri += 1
    table = component_table(tid, cols, cells, n_rows=ri, role="data")
    if ctx.add_story is not None:
        # This table has six real action rows.  The former 87.9 pt wrapper
        # was inherited from the image-bearing LaTeX variant and left a
        # 25 pt empty tail after the editable IDML table.  The rows render
        # at about 10.5 pt each at this measure.
        table_text = " ".join(
            str(value)
            for group in groups
            for value in (
                group.get("state", ""),
                *(item for action in group.get("actions", []) for item in action),
            )
        )
        localized = any(ord(char) > 127 for char in table_text)
        if ri >= 6 and localized:
            framed_h = 87.9
        else:
            framed_h = ((13.2 if ri <= 3 else 10.5) * ri + 1.5)
        table_xml = rounded_table_panel(
            ctx.add_story,
            ctx.params,
            sid=f"st_anchor_lcdmode_{tid}",
            title="LCD mode table",
            table_xml=table,
            width=body_w,
            height=framed_h,
            n_cols=3,
            terminal=terminal,
            fill="Color/Paper", stroke="Color/HB Line K40",
            corner_fills={
                "top_left": "Color/HB Bg K05",
                "bottom_left": "Color/HB Bg K05",
                "top_right": "Color/Paper",
                "bottom_right": "Color/Paper",
            },
        )
    else:
        table_xml = wrap_table_paragraph(table, terminal, span_columns)
    xml = art + table_xml
    return xml, 70.0 + 12.0 * ri
