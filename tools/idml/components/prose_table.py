"""Prose-page data tables — the extractor's ``("table", json rows)`` block
(componentization P2). Two-column tables render in the spec-table shape;
wider ones (e.g. KEY COMBINATIONS) get a narrow first column and an even
split for the rest.
"""
from __future__ import annotations

from ..primitives import cell, component_table, psr, spec_table, wrap_table_paragraph
from .base import RenderContext


def render_table_block(raw_rows: list[list], ctx: RenderContext, *, tid: str,
                       terminal: bool, span_columns: bool = True) -> tuple[str, float]:
    n_cols = max(len(r) for r in raw_rows)
    if n_cols <= 2:
        rows2 = [(r[0], r[1] if len(r) > 1 else "") for r in raw_rows]
        table = spec_table(tid, [(str(a), str(b)) for a, b in rows2],
                           params=ctx.params, page_w=ctx.page_w,
                           m_l=ctx.m_l, m_r=ctx.m_r)
    else:
        # N-column prose tables (e.g. KEY COMBINATIONS): first
        # column narrow-ish, rest evenly split
        body_w2 = ctx.page_w - ctx.m_l - ctx.m_r
        cols = [body_w2 * 0.3] + [body_w2 * 0.7 / (n_cols - 1)] * (n_cols - 1)
        cells = []
        for ri, r in enumerate(raw_rows):
            for ci in range(n_cols):
                txt = str(r[ci]) if ci < len(r) else ""
                style = "HB Spec Label" if ri == 0 else "HB Spec Value"
                cells.append(cell(
                    f"{tid}c{ri}_{ci}", f"{ci}:{ri}",
                    psr(style, txt, terminal=True)))
        table = component_table(tid, cols, cells, n_rows=len(raw_rows))
    xml = wrap_table_paragraph(table, terminal, span_columns=span_columns)
    return xml, 11.0 * (len(raw_rows) + 1)
