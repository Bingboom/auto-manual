"""Shared rounded data-table shell and cell inset tokens.

The editable table remains a square text frame.  The visible rounded border,
corner clipping and continuation-page shell are owned here so individual
renderers cannot silently fall back to square table outlines.
"""
from __future__ import annotations

from collections.abc import Callable

from .. import page_objects
from ..params import param_pt
from ..primitives import wrap_table_paragraph
from ..table_borders import suppress_outer_edges_xml


def table_text_indent(params: dict[str, tuple[str, str]]) -> float:
    """One body-character leading inset shared by rounded data tables."""
    return param_pt(params, "comp_table_text_indent", 5.2)


def rounded_table_panel(
    add_story: Callable[[str, str, list[str]], str],
    params: dict[str, tuple[str, str]],
    *,
    sid: str,
    title: str,
    table_xml: str,
    width: float,
    height: float,
    n_cols: int,
    terminal: bool,
    fill: str = "Color/Paper",
    stroke: str = "Color/HB Line K40",
    stroke_weight: float | None = None,
    radius: float | None = None,
    corner_fills: dict[str, str] | None = None,
    left_indent: float = 0.0,
    space_before: float = 0.0,
    space_after: float = 0.0,
    start_next_page: bool = False,
    content_bottom_bleed: float = 0.0,
) -> str:
    """Wrap one table segment in the canonical editable rounded shell."""
    table_xml = suppress_outer_edges_xml(table_xml, n_cols)
    inner = wrap_table_paragraph(table_xml, True, span_columns=False)
    xml = page_objects.anchored_panel_group_paragraph(
        add_story,
        sid,
        title,
        [inner],
        width,
        height,
        terminal=terminal,
        fill=fill,
        stroke=stroke,
        stroke_weight=(
            stroke_weight
            if stroke_weight is not None
            else param_pt(params, "comp_table_outer_rule", 0.75)
        ),
        radius=(
            radius
            if radius is not None
            else param_pt(params, "comp_table_outer_arc", 6.8)
        ),
        content_inset=0.0,
        corner_fills=corner_fills,
        # Inline groups use their own text-frame reference point; paragraph
        # LeftIndent is preserved in IDML but ignored by InDesign for these
        # objects. Apply the measured optical offset to the group transform.
        group_x_offset=left_indent,
        content_bottom_bleed=content_bottom_bleed,
    )
    attrs: list[str] = []
    if start_next_page:
        attrs.append('StartParagraph="NextPage"')
    if space_before:
        attrs.append(f'SpaceBefore="{space_before:g}"')
    if space_after:
        attrs.append(f'SpaceAfter="{space_after:g}"')
    if attrs:
        xml = xml.replace(
            "<ParagraphStyleRange ",
            "<ParagraphStyleRange " + " ".join(attrs) + " ",
            1,
        )
    return xml
