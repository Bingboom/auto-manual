"""Preface language badge (template-parity P4).

The master's IMPORTANT preface tags each language block with a small
dark pill (EN / FR / ES) beside the bold heading; the extractor emitted
these as a plain "[EN] IMPORTANT" h2 before this component existed.
"""
from __future__ import annotations

from ..params import param_pt
from ..primitives import cell, component_table, psr, wrap_table_paragraph
from .base import RenderContext


def render_langtag(spec: dict, ctx: RenderContext, *, tid: str, terminal: bool,
                   span_columns: bool = True,
                   measure_w: float | None = None) -> tuple[str, float]:
    body_w = measure_w or ctx.text_measure
    lang = (spec.get("lang") or "").strip().upper()
    title = " ".join(spec.get("texts", [])).strip()
    tag_w = param_pt(ctx.params, "idml_preface_tag_width", 4.6 * 72.0 / 25.4)
    cells = [
        cell(f"{tid}c0", "0:0", psr("HB Preface Tag", lang, terminal=True),
             fill="Color/HB Brand Dark", stroke=False,
             top=1.1, bottom=1.1, left=2, right=2,
             valign="CenterAlign"),
        cell(f"{tid}c1", "1:0", psr("HB Preface Title", title, terminal=True),
             stroke=False, top=0, bottom=0, left=1.4 * 72.0 / 25.4,
             right=0, valign="CenterAlign"),
    ]
    table = component_table(
        tid, [tag_w, max(60.0, body_w - tag_w)], cells,
        outer_stroke=False,
    )
    return wrap_table_paragraph(
        table, terminal, span_columns, paragraph_style="HB Preface Body",
    ), param_pt(ctx.params, "idml_preface_tag_height", 2.9 * 72.0 / 25.4)
