"""FCC two-panel component (componentization P2)."""
from __future__ import annotations

from ..primitives import cell, component_table, image_cell_content, psr, wrap_table_paragraph
from ..style_names import table_style_ref
from .base import RenderContext, figure_paragraph


def render_fcc(spec: dict, ctx: RenderContext, *, tid: str, terminal: bool,
               span_columns: bool = True,
               measure_w: float | None = None) -> tuple[str, float]:
    body_w = measure_w or ctx.text_measure
    # Pad to two panels: `\HBFccBlock{}{}` (or args reduced to empty by _detex)
    # used to arrive as texts=[] and crash on texts[0] — an extractor kind must
    # never be able to abort the whole export.
    texts = ((spec.get("texts") or []) + ["", ""])[:2]
    mark = ctx.root / "docs" / "renderers" / "latex" / "assets" / "fcc_mark.pdf"
    icon = ""
    if mark.exists():
        icon = figure_paragraph(image_cell_content(f"{tid}fm", mark, 32.0, 22.0))
    cols = [body_w / 2.0] * 2
    cells = [
        cell(f"{tid}c0", "0:0",
             icon + psr("HB Body", texts[0], terminal=True),
             fill="Color/HB Bg K05", stroke=False),
        cell(f"{tid}c1", "1:0",
             psr("HB Body", texts[1] if len(texts) > 1 else "", terminal=True),
             fill="Color/HB Bg K05", stroke=False),
    ]
    table = component_table(tid, cols, cells, table_style=table_style_ref("layout"))
    per_line = max(20, int(body_w / 2 / (0.52 * 6.2)))
    lines = max((len(t) + per_line - 1) // per_line for t in texts) if texts else 1
    return wrap_table_paragraph(table, terminal, span_columns), 7.5 * lines + 30
