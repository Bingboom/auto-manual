"""Preface language badge (template-parity P4).

The master's IMPORTANT preface tags each language block with a small
dark pill (EN / FR / ES) beside the bold heading; the extractor emitted
these as a plain "[EN] IMPORTANT" h2 before this component existed.
"""
from __future__ import annotations

from ..primitives import cell, component_table, psr, wrap_table_paragraph
from .base import RenderContext


def render_langtag(spec: dict, ctx: RenderContext, *, tid: str, terminal: bool,
                   span_columns: bool = True,
                   measure_w: float | None = None) -> tuple[str, float]:
    body_w = measure_w or ctx.text_measure
    lang = (spec.get("lang") or "").strip().upper()
    title = " ".join(spec.get("texts", [])).strip()
    cells = [
        cell(f"{tid}c0", "0:0", psr("HB Notice Side Label", lang, terminal=True),
             top=2, bottom=2, left=2, right=2),
        cell(f"{tid}c1", "1:0", psr("HB Title L2", title, terminal=True),
             top=3, bottom=2, left=5, right=3),
    ]
    table = component_table(tid, [22.0, max(60.0, body_w - 22.0)], cells)
    return wrap_table_paragraph(table, terminal, span_columns), 16.0
