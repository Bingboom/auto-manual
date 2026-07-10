"""Warranty-period cards (template-parity P4).

The master renders the warranty period as two side-by-side cards with a
huge numeral ("3" / "2"), the YEARS unit + card title beside it, and the
explanatory copy below. The source carries them as one table row whose
cells read "**3 YEARS** **Standard Warranty** <copy>".
"""
from __future__ import annotations

from ..primitives import cell, component_table, psr, wrap_table_paragraph
from .base import RenderContext


def render_warrantyyears(spec: dict, ctx: RenderContext, *, tid: str, terminal: bool,
                         span_columns: bool = True,
                         measure_w: float | None = None) -> tuple[str, float]:
    body_w = measure_w or ctx.text_measure
    items = spec.get("items", [])
    if not items:
        return "", 0.0
    col_w = max(60.0, (body_w - 6.0 * (len(items) - 1)) / len(items))
    cells = []
    max_lines = 1
    for ci, item in enumerate(items):
        number = str(item.get("number", "")).strip()
        unit = str(item.get("unit", "")).strip()
        label = str(item.get("label", "")).strip()
        text = str(item.get("text", "")).strip()
        parts = [
            psr("HB Big Numeral", f"{number} {unit}"),
            psr("HB Title L3", label),
            psr("HB Body", text, terminal=True),
        ]
        cells.append(cell(f"{tid}c{ci}", f"{ci}:0", "".join(parts),
                          top=5, bottom=5, left=5, right=5))
        max_lines = max(max_lines, len(text) // 52 + 1)
    table = component_table(tid, [col_w] * len(items), cells, role="warning")
    est = 30.0 + 8.0 + 7.5 * max_lines + 10.0
    return wrap_table_paragraph(table, terminal, span_columns), est
