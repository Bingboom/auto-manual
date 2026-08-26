"""Source-driven standalone emphasis pill used in prose introductions."""
from __future__ import annotations

from .. import page_objects as _po
from ..line_metrics import estimated_text_width
from ..params import param_pt
from ..primitives import cell, component_table, psr, wrap_table_paragraph
from .base import RenderContext
from .native_marker import marked_text, marker_replacements


def render_emphasispill(
    spec: dict,
    ctx: RenderContext,
    *,
    tid: str,
    terminal: bool,
    span_columns: bool = True,
    measure_w: float | None = None,
) -> tuple[str, float]:
    text = " ".join(str(value).strip() for value in spec.get("texts", []) if value)
    if not text:
        return "", 0.0
    body_w = measure_w or ctx.text_measure
    size = param_pt(ctx.params, "idml_charging_emphasis_font_size", 6.6)
    space_before = param_pt(
        ctx.params,
        "idml_charging_emphasis_space_before",
        5.0,
    )
    horizontal_padding = param_pt(
        ctx.params,
        "idml_charging_emphasis_horizontal_padding",
        7.0,
    )
    space_after = 1.5
    height = max(14.2, param_pt(ctx.params, "comp_subbar_height", 13.89))
    width_factor = 0.50 if len(text) > 55 else 0.44
    width = min(
        body_w,
        max(
            96.0,
            estimated_text_width(
                text,
                point_size=size,
                narrow_width_ratio=width_factor,
            ) + 2.0 * horizontal_padding + 2.0,
        ),
    )
    content = psr("HB Emphasis Pill", text, terminal=True)
    if ctx.add_story is None:
        # The rectangular table fallback has no rounded endcaps to provide
        # optical inset, so carry the padding on its editable paragraph.
        content = content.replace(
            "<ParagraphStyleRange ",
            f'<ParagraphStyleRange LeftIndent="{horizontal_padding:g}" '
            f'RightIndent="{horizontal_padding:g}" ',
            1,
        )
        table = component_table(
            tid,
            [width],
            [cell(f"{tid}c0", "0:0", content, fill="Color/HB Brand Dark",
                  stroke=False, top=2, bottom=2, left=0, right=0,
                  valign="CenterAlign")],
            role="warning",
        )
        return wrap_table_paragraph(table, terminal, span_columns), height + 2.0

    # InDesign does not preserve a one-sided InsetSpacing reliably on this
    # inline rounded text frame.  Put the optical left edge on the editable
    # paragraph instead; keep the right side unindented so the final words
    # retain the width allowance reserved above.
    content = content.replace(
        "<ParagraphStyleRange ",
        f'<ParagraphStyleRange LeftIndent="{horizontal_padding:g}" ',
        1,
    )
    xml = _po.anchored_panel_group_paragraph(
        ctx.add_story,
        f"st_anchor_emphasis_{tid}",
        "source emphasis pill",
        [content],
        width,
        height,
        terminal=terminal,
        fill="Color/HB Brand Dark",
        stroke="Swatch/None",
        stroke_weight=0,
        radius=height / 2.0,
        valign="CenterAlign",
        mask_content_corners=False,
    )
    xml = xml.replace(
        "<ParagraphStyleRange ",
        f'<ParagraphStyleRange SpaceBefore="{space_before:g}" '
        f'SpaceAfter="{space_after:g}" ',
        1,
    )
    return xml, height + space_before + space_after


def render_headingpill(
    spec: dict,
    ctx: RenderContext,
    *,
    tid: str,
    terminal: bool,
    span_columns: bool = True,
    measure_w: float | None = None,
) -> tuple[str, float]:
    """Render the standard H2 marker and an emphasis pill on one row."""

    heading = str(spec.get("heading") or "").strip()
    pill = str(spec.get("pill") or "").strip()
    if not heading or not pill:
        return "", 0.0

    body_w = measure_w or ctx.text_measure
    size = param_pt(ctx.params, "idml_charging_emphasis_font_size", 6.6)
    horizontal_padding = param_pt(
        ctx.params,
        "idml_charging_emphasis_horizontal_padding",
        7.0,
    )
    height = max(14.2, param_pt(ctx.params, "comp_subbar_height", 13.89))
    width_factor = 0.50 if len(pill) > 55 else 0.44
    pill_width = min(
        body_w * 0.48,
        max(
            96.0,
            estimated_text_width(
                pill,
                point_size=size,
                narrow_width_ratio=width_factor,
            ) + 2.0 * horizontal_padding + 2.0,
        ),
    )
    gap = param_pt(ctx.params, "comp_title_l2_gap", 3.969)
    heading_width = body_w - pill_width - gap
    if heading_width <= 0:
        raise ValueError("heading pill exceeds the available text measure")

    heading_text = marked_text(heading) if ctx.native_structure_markers else "● " + heading
    heading_xml = psr(
        "HB Title L2",
        heading_text,
        terminal=True,
        inline_replacements=(
            marker_replacements(
                ctx,
                marker_id=f"{tid}_h2_marker",
            )
            if ctx.native_structure_markers
            else None
        ),
    )
    pill_xml = psr("HB Emphasis Pill", pill, terminal=True)
    if ctx.add_story is None:
        pill_xml = pill_xml.replace(
            "<ParagraphStyleRange ",
            f'<ParagraphStyleRange LeftIndent="{horizontal_padding:g}" '
            f'RightIndent="{horizontal_padding:g}" ',
            1,
        )
        pill_cell = cell(
            f"{tid}c1",
            "1:0",
            pill_xml,
            fill="Color/HB Brand Dark",
            stroke=False,
            top=2,
            bottom=2,
            left=gap,
            right=0,
            valign="CenterAlign",
        )
    else:
        pill_xml = pill_xml.replace(
            "<ParagraphStyleRange ",
            f'<ParagraphStyleRange LeftIndent="{horizontal_padding:g}" ',
            1,
        )
        pill_xml = _po.anchored_panel_group_paragraph(
            ctx.add_story,
            f"st_anchor_headingpill_{tid}",
            "heading suffix emphasis pill",
            [pill_xml],
            pill_width,
            height,
            terminal=True,
            fill="Color/HB Brand Dark",
            stroke="Swatch/None",
            stroke_weight=0,
            radius=height / 2.0,
            valign="CenterAlign",
            mask_content_corners=False,
        )
        pill_cell = cell(
            f"{tid}c1",
            "1:0",
            pill_xml,
            stroke=False,
            top=0,
            bottom=0,
            left=gap,
            right=0,
            valign="CenterAlign",
        )

    table = component_table(
        tid,
        [heading_width, pill_width + gap],
        [
            cell(
                f"{tid}c0",
                "0:0",
                heading_xml,
                stroke=False,
                top=0,
                bottom=0,
                left=0,
                right=0,
                valign="CenterAlign",
            ),
            pill_cell,
        ],
        outer_stroke=False,
    )
    variant = str(spec.get("variant") or "").strip().casefold()
    default_space_before = param_pt(
        ctx.params,
        "idml_title_l2_space_before",
        5.67,
    )
    space_before = (
        param_pt(
            ctx.params,
            "idml_charging_headingpill_space_before",
            0.0,
        )
        if variant == "charging"
        else default_space_before
    )
    space_after = param_pt(ctx.params, "idml_title_l2_space_after", 5.67)
    paragraph = wrap_table_paragraph(
        table,
        terminal,
        span_columns,
        paragraph_style="HB Body",
    ).replace(
        "<ParagraphStyleRange ",
        f'<ParagraphStyleRange SpaceBefore="{space_before:g}" '
        f'SpaceAfter="{space_after:g}" ',
        1,
    )
    return paragraph, height + space_before + space_after
