"""Editable warranty-page components shared with the LaTeX token layer."""
from __future__ import annotations

import math
import re

from .. import page_objects as _po
from ..params import param_pt
from ..primitives import (
    cell,
    component_table,
    path_geometry,
    psr,
    wrap_table_paragraph,
)
from .base import RenderContext, figure_paragraph

_CIRCLED = {str(index): glyph for index, glyph in enumerate("❶❷❸❹❺❻❼❽❾", 1)}


def _plain_strong(text: str) -> str:
    match = re.fullmatch(r"\s*\*\*(.*?)\*\*\s*", text, re.S)
    return match.group(1) if match else text


def _language_param(ctx: RenderContext, key: str, default: float) -> float:
    base = param_pt(ctx.params, key, default)
    language = (ctx.language or "").strip().lower()
    if language:
        return param_pt(ctx.params, f"lang_{language}_{key}", base)
    return base


def _wrapped_lines(text: str, width: float, size: float) -> int:
    plain = text.replace("**", "").strip()
    if not plain:
        return 1
    chars = max(8, int(width / max(1.0, size * 0.50)))
    return max(1, math.ceil(len(plain) / chars))


def _anchor() -> str:
    return (
        '    <AnchoredObjectSetting AnchoredPosition="InlinePosition" '
        'SpineRelative="false" LockPosition="false" PinPosition="true" '
        'AnchorPoint="BottomRightAnchor" HorizontalAlignment="LeftAlign" '
        'HorizontalReferencePoint="TextFrame" VerticalAlignment="TopAlign" '
        'VerticalReferencePoint="LineBaseline" AnchorXoffset="0" '
        'AnchorYoffset="0" AnchorSpaceAbove="0"/>\n'
    )


def _text_frame(
    sid: str,
    self_id: str,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    valign: str = "TopAlign",
) -> str:
    insets = "".join('<ListItem type="unit">0</ListItem>' for _ in range(4))
    return (
        f'<TextFrame Self="{self_id}" ParentStory="{sid}" '
        'PreviousTextFrame="n" NextTextFrame="n" ContentType="TextType" '
        'AppliedObjectStyle="ObjectStyle/$ID/[Normal Text Frame]" '
        'FillColor="Swatch/None" StrokeColor="Swatch/None" StrokeWeight="0" '
        'ItemTransform="1 0 0 1 0 0">\n'
        + path_geometry(x1, y1, x2, y2)
        + '    <TextFramePreference TextColumnCount="1" '
        f'VerticalJustification="{valign}" AutoSizingType="Off">'
        f'<Properties><InsetSpacing type="list">{insets}'
        '</InsetSpacing></Properties></TextFramePreference>\n'
        + _anchor()
        + '</TextFrame>\n'
    )


def _year_heading(item: dict, ctx: RenderContext) -> str:
    number = str(item.get("number", "")).strip()
    unit = str(item.get("unit", "")).strip()
    glyph = _CIRCLED.get(number, number)
    xml = psr("HB Warranty Year Heading", f"{glyph} {unit}")
    badge_size = param_pt(ctx.params, "type_warranty_year_number_font_size", 21.0)
    glyph_size = param_pt(ctx.params, "idml_warranty_year_glyph_size", 30.0)
    xml = xml.replace(
        'FontStyle="Regular"',
        f'PointSize="{glyph_size:g}" FontStyle="Regular"',
        1,
    )
    xml = xml.replace(
        "<ParagraphStyleRange ",
        f'<ParagraphStyleRange Leading="{badge_size + 1:g}" SpaceAfter="1.2" ',
        1,
    )
    return xml


def _years_table(
    spec: dict,
    ctx: RenderContext,
    *,
    tid: str,
    width: float,
) -> tuple[str, float]:
    items = list(spec.get("items", []))
    if not items:
        return "", 0.0
    gap = param_pt(ctx.params, "comp_warranty_year_column_gap", 2.27)
    left_ratio = _language_param(
        ctx,
        "idml_warranty_year_left_ratio",
        float(ctx.params.get(
            "comp_warranty_year_left_ratio", ("0.59", "ratio"),
        )[0]),
    )
    if len(items) == 2:
        left_w = (width - gap) * left_ratio
        cols = [left_w, width - gap - left_w]
    else:
        cols = [(width - gap * (len(items) - 1)) / len(items)] * len(items)
    cells: list[str] = []
    max_height = 0.0
    body_size = param_pt(ctx.params, "type_warranty_body_font_size", 6.0)
    body_leading = param_pt(ctx.params, "idml_warranty_body_font_leading", 6.0)
    badge_size = param_pt(ctx.params, "type_warranty_year_number_font_size", 21.0)
    subtitle_size = param_pt(ctx.params, "type_warranty_year_subtitle_font_size", 7.2)
    for index, (item, col_w) in enumerate(zip(items, cols)):
        subtitle = str(item.get("label", "")).strip()
        body = str(item.get("text", "")).strip()
        content = _year_heading(item, ctx)
        subtitle_xml = psr("HB Warranty Year Subtitle", subtitle)
        subtitle_indent = (
            param_pt(ctx.params, "comp_warranty_year_badge_size", 23.81) + 3.97
        )
        subtitle_xml = subtitle_xml.replace(
            "<ParagraphStyleRange ",
            f'<ParagraphStyleRange LeftIndent="{subtitle_indent:g}" ',
            1,
        )
        content += subtitle_xml
        content += psr("HB Warranty Body", body, terminal=True)
        cells.append(cell(
            f"{tid}c{index}", f"{index}:0", content,
            stroke=False, top=0, bottom=0,
            left=0, right=(gap if index < len(items) - 1 else 0),
            valign="TopAlign",
        ))
        lines = _wrapped_lines(body, col_w - 2.0, body_size)
        max_height = max(
            max_height,
            badge_size + 1.0 + subtitle_size + 2.0 + lines * body_leading,
        )
    return component_table(
        tid, cols, cells, n_rows=1, outer_stroke=False,
    ), max_height


def render_warrantyyears(
    spec: dict,
    ctx: RenderContext,
    *,
    tid: str,
    terminal: bool,
    span_columns: bool = True,
    measure_w: float | None = None,
) -> tuple[str, float]:
    width = measure_w or ctx.text_measure
    table, height = _years_table(spec, ctx, tid=tid, width=width)
    if not table:
        return "", 0.0
    return wrap_table_paragraph(table, terminal, span_columns), height


def render_warrantylead(
    spec: dict,
    ctx: RenderContext,
    *,
    tid: str,
    terminal: bool,
    span_columns: bool = True,
    measure_w: float | None = None,
) -> tuple[str, float]:
    width = measure_w or ctx.text_measure
    text = " ".join(
        _plain_strong(str(value)) for value in spec.get("texts", []) if value
    )
    size = param_pt(ctx.params, "type_warranty_lead_font_size", 7.0)
    leading = param_pt(ctx.params, "type_warranty_lead_font_leading", 8.2)
    pad_lr = param_pt(ctx.params, "comp_warranty_lead_pad_lr", 10.2)
    pad_tb = _language_param(
        ctx,
        "idml_warranty_lead_pad_tb",
        param_pt(ctx.params, "comp_warranty_lead_pad_tb", 7.65),
    )
    horizontal_scale = _language_param(
        ctx, "idml_warranty_lead_horizontal_scale", 100.0,
    )
    lines = _wrapped_lines(text, width - 2 * pad_lr, size)
    height = lines * leading + 2 * pad_tb
    content = psr("HB Warranty Lead", text, terminal=True).replace(
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
        f'HorizontalScale="{horizontal_scale:g}"',
        1,
    )
    if ctx.add_story is None:
        table = component_table(
            tid,
            [width],
            [cell(f"{tid}c0", "0:0", content, fill="Color/HB Bg K05",
                  stroke=False, top=pad_tb, bottom=pad_tb,
                  left=pad_lr, right=pad_lr)],
            role="warning",
        )
        return wrap_table_paragraph(table, terminal, span_columns), height
    xml = _po.anchored_panel_paragraph(
        ctx.add_story,
        f"st_anchor_warranty_lead_{tid}",
        "warranty purchase-channel lead",
        [content],
        width,
        height,
        terminal=terminal,
        fill="Color/HB Bg K05",
        stroke="Swatch/None",
        stroke_weight=0,
        radius=param_pt(ctx.params, "comp_warranty_lead_arc", 9.07),
        inset=(pad_tb, pad_lr, pad_tb, pad_lr),
        valign="CenterAlign",
        auto_height=False,
    )
    before = param_pt(ctx.params, "idml_warranty_lead_before", 1.98)
    after = param_pt(ctx.params, "comp_warranty_lead_after", 2.83)
    xml = xml.replace(
        "<ParagraphStyleRange ",
        f'<ParagraphStyleRange SpaceBefore="{before:g}" SpaceAfter="{after:g}" ',
        1,
    )
    return xml, before + height + after


def _section_body(
    blocks: list[dict],
    ctx: RenderContext,
    *,
    tid: str,
    width: float,
) -> tuple[list[str], float]:
    body_size = param_pt(ctx.params, "type_warranty_body_font_size", 6.0)
    body_leading = param_pt(ctx.params, "idml_warranty_body_font_leading", 6.0)
    list_leading = param_pt(ctx.params, "type_warranty_body_font_leading", 7.2)
    body_after = param_pt(ctx.params, "idml_warranty_paragraph_after", 2.83)
    list_after = param_pt(ctx.params, "idml_warranty_list_after", 1.0)
    parts: list[str] = []
    height = 0.0
    for block_index, block in enumerate(blocks):
        kind = str(block.get("kind", "body"))
        terminal = block_index == len(blocks) - 1
        if kind == "component" and block.get("spec", {}).get("kind") == "warrantyyears":
            table, table_height = _years_table(
                block["spec"], ctx, tid=f"{tid}_years", width=width,
            )
            parts.append(wrap_table_paragraph(table, True, span_columns=False))
            height += table_height
            continue
        text = str(block.get("text", ""))
        is_list = kind in {"list", "sublist"}
        style = "HB Warranty List" if is_list else "HB Warranty Body"
        leading = list_leading if is_list else body_leading
        paragraph_after = list_after if is_list else body_after
        paragraph = psr(style, text, terminal=terminal)
        if not terminal:
            paragraph = paragraph.replace(
                "<ParagraphStyleRange ",
                f'<ParagraphStyleRange SpaceAfter="{paragraph_after:g}" ',
                1,
            )
        parts.append(paragraph)
        available = width - (9.0 if kind in {"list", "sublist"} else 0.0)
        height += _wrapped_lines(text, available, body_size) * leading
        if not terminal:
            height += paragraph_after
    return parts, height


def render_warrantysection(
    spec: dict,
    ctx: RenderContext,
    *,
    tid: str,
    terminal: bool,
    span_columns: bool = True,
    measure_w: float | None = None,
) -> tuple[str, float]:
    width = measure_w or ctx.text_measure
    title = str(spec.get("title", "")).strip()
    index = int(spec.get("index", 0) or 0)
    blocks = list(spec.get("blocks", []))
    pad_lr = param_pt(ctx.params, "comp_warranty_section_pad_lr", 9.07)
    pad_top = param_pt(ctx.params, "comp_warranty_section_pad_top", 9.07)
    pad_bottom_key = (
        "comp_warranty_exclusions_pad_bottom"
        if index == 5 else "comp_warranty_section_pad_bottom"
    )
    pad_bottom = param_pt(
        ctx.params, pad_bottom_key, 16.44 if index == 5 else 5.10,
    )
    inner_w = width - 2 * pad_lr
    body_parts, body_height = _section_body(
        blocks, ctx, tid=tid, width=inner_w,
    )
    trim_key = (
        "idml_warranty_panel_trim_first" if index == 1
        else "idml_warranty_panel_trim_period" if index == 2
        else "idml_warranty_panel_trim_exclusions" if index == 5
        else ""
    )
    trim = (
        _language_param(ctx, trim_key, param_pt(ctx.params, trim_key, 0.0))
        if trim_key else 0.0
    )
    panel_h = max(22.0, pad_top + body_height + pad_bottom - trim)
    title_size = param_pt(ctx.params, "idml_warranty_title_font_size", 8.0)
    title_leading = param_pt(ctx.params, "type_warranty_title_font_leading", 8.8)
    title_pad_lr = param_pt(ctx.params, "comp_warranty_title_pad_lr", 5.1)
    title_pad_tb = param_pt(ctx.params, "comp_warranty_title_pad_tb", 1.98)
    title_h = title_leading + 2 * title_pad_tb
    title_w = min(
        width - 2 * pad_lr,
        max(55.0, len(title) * title_size * 0.53 + 2 * title_pad_lr),
    )
    if ctx.add_story is None:
        fallback = psr("HB Warranty Title", title) + "".join(body_parts)
        table = component_table(
            tid,
            [width],
            [cell(f"{tid}c0", "0:0", fallback, stroke=True,
                  top=pad_top, bottom=pad_bottom, left=pad_lr, right=pad_lr)],
            role="warning",
        )
        return wrap_table_paragraph(table, terminal, span_columns), panel_h

    title_sid = ctx.add_story(
        f"st_anchor_warranty_title_{tid}",
        f"{title} warranty panel title",
        [psr("HB Warranty Title", title, terminal=True)],
    )
    body_sid = ctx.add_story(
        f"st_anchor_warranty_body_{tid}",
        f"{title} warranty panel body",
        body_parts,
    )
    rule = param_pt(ctx.params, "comp_warranty_section_rule", 0.9)
    arc = param_pt(ctx.params, "comp_warranty_section_arc", 6.8)
    title_arc = param_pt(ctx.params, "comp_warranty_title_arc", 4.82)
    title_x = param_pt(ctx.params, "comp_warranty_title_inset", 8.50)
    outer = (
        f'<Rectangle Self="bg_warranty_{tid}" ContentType="Unassigned" '
        'AppliedObjectStyle="ObjectStyle/HB Rounded Panel" '
        'FillColor="Color/Paper" StrokeColor="Color/HB Border K10" '
        f'StrokeWeight="{rule:g}" ItemTransform="1 0 0 1 0 0">\n'
        + _po.rounded_path_geometry(0.0, -panel_h, width, 0.0, arc)
        + _anchor()
        + '</Rectangle>\n'
    )
    plate = (
        f'<Rectangle Self="plate_warranty_{tid}" ContentType="Unassigned" '
        'AppliedObjectStyle="ObjectStyle/HB Rounded Panel" '
        'FillColor="Color/HB Brand Dark" StrokeColor="Swatch/None" '
        'StrokeWeight="0" ItemTransform="1 0 0 1 0 0">\n'
        + _po.rounded_path_geometry(
            title_x,
            -panel_h - title_h / 2.0,
            title_x + title_w,
            -panel_h + title_h / 2.0,
            title_arc,
        )
        + _anchor()
        + '</Rectangle>\n'
    )
    title_frame = _text_frame(
        title_sid,
        f"tf_warranty_title_{tid}",
        title_x + title_pad_lr,
        -panel_h - title_h / 2.0,
        title_x + title_w - title_pad_lr,
        -panel_h + title_h / 2.0,
        valign="CenterAlign",
    )
    body_frame = _text_frame(
        body_sid,
        f"tf_warranty_body_{tid}",
        pad_lr,
        -panel_h + pad_top,
        width - pad_lr,
        -max(0.0, pad_bottom - trim),
    )
    group = (
        f'<Group Self="grp_warranty_{tid}" '
        'AppliedObjectStyle="ObjectStyle/$ID/[None]" '
        'ItemTransform="1 0 0 1 0 0">\n'
        + outer + plate + title_frame + body_frame + '</Group>'
    )
    host = figure_paragraph(
        group,
        tail='<Content></Content>' + ('' if terminal else '<Br/>'),
    )
    before_key = (
        "comp_warranty_first_section_before" if index == 1
        else "idml_warranty_period_section_before" if index == 2
        else "idml_warranty_final_section_before" if index == 6
        else "idml_warranty_section_before"
    )
    before = param_pt(ctx.params, before_key, 4.25)
    after = param_pt(ctx.params, "comp_warranty_section_after", 1.13)
    host = host.replace(
        "<ParagraphStyleRange ",
        f'<ParagraphStyleRange SpaceBefore="{before:g}" SpaceAfter="{after:g}" ',
        1,
    )
    return host, before + panel_h + after
