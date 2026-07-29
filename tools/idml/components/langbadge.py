"""Preface language badge (template-parity P4).

The master's IMPORTANT preface tags each language block with a small
dark pill (EN / FR / ES) beside the bold heading; the extractor emitted
these as a plain "[EN] IMPORTANT" h2 before this component existed.
"""
from __future__ import annotations

from ..page_objects import anchored_panel_paragraph
from ..params import param_pt
from ..primitives import cell, component_table, psr, wrap_table_paragraph
from .base import RenderContext


def _with_baseline_shift(paragraph: str, shift: float) -> str:
    """Apply an optical shift without changing the one-row table height."""
    return paragraph.replace(
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
        f'BaselineShift="{shift:g}"',
        1,
    )


def render_langtag(spec: dict, ctx: RenderContext, *, tid: str, terminal: bool,
                   span_columns: bool = True,
                   measure_w: float | None = None) -> tuple[str, float]:
    body_w = measure_w or ctx.text_measure
    lang = (spec.get("lang") or "").strip().upper()
    title = " ".join(spec.get("texts", [])).strip()
    tag_w = param_pt(ctx.params, "idml_preface_tag_width", 4.6 * 72.0 / 25.4)
    # Optical defaults are the phase2e PDF-bbox deltas against the hash-bound
    # V2 reference.  Keep them token-overridable: they describe this layout,
    # not language content, and must not migrate into the source copy.
    tag_left = param_pt(ctx.params, "idml_preface_tag_left_inset", 2.244)
    title_left = param_pt(ctx.params, "idml_preface_title_left_inset", 8.947)
    tag_shift = param_pt(ctx.params, "idml_preface_tag_baseline_shift", 0.5672)
    title_shift = param_pt(ctx.params, "idml_preface_title_baseline_shift", -1.2665)
    default_after = param_pt(ctx.params, "idml_preface_header_space_after", 8.3191)
    language_key = lang.lower()
    header_before = param_pt(
        ctx.params,
        f"lang_{language_key}_idml_preface_header_space_before",
        0.0,
    )
    body_gap = param_pt(
        ctx.params,
        f"lang_{language_key}_idml_preface_header_space_after",
        default_after,
    )
    tag_vertical_inset = param_pt(
        ctx.params, "idml_preface_tag_vertical_inset", 1.1,
    )
    tag_height = param_pt(
        ctx.params, "idml_preface_tag_height", 2.9 * 72.0 / 25.4,
    )
    tag_radius = param_pt(
        ctx.params, "idml_preface_tag_corner_radius", 1.25,
    )
    tag = _with_baseline_shift(
        psr("HB Preface Tag", lang, terminal=True), tag_shift,
    )
    heading = _with_baseline_shift(
        psr("HB Preface Title", title, terminal=True), title_shift,
    )
    if ctx.add_story is not None:
        tag = anchored_panel_paragraph(
            ctx.add_story,
            f"st_anchor_langbadge_{tid}",
            f"{lang} preface language tag",
            [tag],
            tag_w,
            tag_height,
            terminal=True,
            fill="Color/HB Brand Dark",
            stroke=None,
            radius=tag_radius,
            inset=(tag_vertical_inset, tag_left, tag_vertical_inset, tag_left),
            valign="CenterAlign",
        )
        tag_cell = cell(
            f"{tid}c0", "0:0", tag,
            stroke=False, top=0, bottom=0, left=0, right=0,
            valign="CenterAlign",
        )
    else:
        tag_cell = cell(
            f"{tid}c0", "0:0", tag,
            fill="Color/HB Brand Dark", stroke=False,
            top=tag_vertical_inset, bottom=tag_vertical_inset,
            left=tag_left, right=tag_left,
            valign="CenterAlign",
        )
    cells = [
        tag_cell,
        cell(f"{tid}c1", "1:0", heading,
             stroke=False, top=0, bottom=0, left=title_left,
             right=0, valign="CenterAlign"),
    ]
    table = component_table(
        tid, [tag_w, max(60.0, body_w - tag_w)], cells,
        outer_stroke=False,
    )
    paragraph = wrap_table_paragraph(
        table, terminal, span_columns, paragraph_style="HB Preface Body",
    ).replace(
        "<ParagraphStyleRange ",
        f'<ParagraphStyleRange SpaceBefore="{header_before:g}" '
        f'SpaceAfter="{body_gap:g}" ',
        1,
    )
    return paragraph, header_before + tag_height + body_gap
