"""Editable warranty-page components shared with the LaTeX token layer."""
from __future__ import annotations

import re

from .. import page_objects as _po
from ..line_metrics import estimated_line_count, estimated_text_width
from ..params import param_pt
from ..primitives import (
    cell,
    component_table,
    path_geometry,
    psr,
    wrap_table_paragraph,
)
from .base import RenderContext, figure_paragraph

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
    return estimated_line_count(
        plain,
        width,
        point_size=size,
        narrow_width_ratio=0.50,
        minimum_narrow_chars=8,
    )


def _panel_width(ctx: RenderContext, width: float) -> float:
    """Return the approved locale-width correction for warranty shells."""
    return width + _language_param(
        ctx,
        "idml_warranty_panel_width_adjust",
        0.0,
    )


def _variant_adjust(
    spec: dict,
    ctx: RenderContext,
    key: str,
) -> float:
    """Per-variant additive correction, with the same language cascade as the base.

    The values this offsets are themselves per-language (`_language_param` over
    `lang_<code>_idml_warranty_*`), so a language-blind variant token could not
    express a correction that differs between en and es on the same key — the
    tuning would have to go back onto the shared base tokens, which the approved
    JE-1000F/US reference layout also reads.
    """

    variant = str(spec.get("layout_variant") or "").strip().lower()
    if not variant or re.fullmatch(r"[a-z][a-z0-9_]*", variant) is None:
        return 0.0
    return _language_param(
        ctx,
        f"idml_warranty_variant_{variant}_{key}",
        0.0,
    )


def _variant_value(
    spec: dict,
    ctx: RenderContext,
    key: str,
    default: float,
) -> float:
    variant = str(spec.get("layout_variant") or "").strip().lower()
    if not variant or re.fullmatch(r"[a-z][a-z0-9_]*", variant) is None:
        return default
    return _language_param(
        ctx,
        f"idml_warranty_variant_{variant}_{key}",
        default,
    )


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


def _variant_body_format(
    xml: str,
    spec: dict,
    ctx: RenderContext,
    *,
    horizontal_scale: float,
    leading: float | None,
) -> str:
    attrs: list[str] = []
    if leading is not None:
        attrs.append(f'Leading="{leading:g}"')
    if _variant_value(spec, ctx, "disable_hyphenation", 0.0) >= 0.5:
        attrs.extend(('Hyphenation="false"', 'Composer="HL Single"'))
    if attrs:
        xml = xml.replace(
            "<ParagraphStyleRange ",
            f'<ParagraphStyleRange {" ".join(attrs)} ',
            1,
        )
    return xml.replace(
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
        f'HorizontalScale="{horizontal_scale:g}"',
    )


def _year_heading(
    item: dict,
    ctx: RenderContext,
    *,
    marker_id: str,
    unit_indent: float,
) -> str:
    """Render the shared, font-portable warranty year badge.

    The approved composition uses a dark circular badge with a white live-text
    numeral.  A Unicode circled digit is not portable across InDesign hosts,
    while reducing the heading to a bare ``3``/``2`` loses the component's
    visual contract.  Keep the circle as native IDML geometry and put the
    ordinary numeral in its own editable story; ordinary ASCII digits are
    covered by the packaged production face on every target.
    """
    number = str(item.get("number", "")).strip()
    unit = str(item.get("unit", "")).strip()
    badge_size = param_pt(ctx.params, "type_warranty_year_number_font_size", 21.0)
    diameter = param_pt(ctx.params, "comp_warranty_year_badge_size", 23.81)
    badge = ""
    if ctx.add_story is not None:
        safe_id = re.sub(r"[^A-Za-z0-9_]+", "_", marker_id).strip("_")
        safe_id = safe_id or "warranty_year"
        numeral_xml = psr("HB Warranty Year Heading", number, terminal=True)
        numeral_xml = numeral_xml.replace(
            "<ParagraphStyleRange ",
            '<ParagraphStyleRange Justification="CenterAlign" ',
            1,
        )
        numeral_xml = numeral_xml.replace(
            'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
            'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
            f'FillColor="Color/Paper" PointSize="{badge_size:g}" '
            'FontStyle="Bold"',
            1,
        )
        numeral_sid = ctx.add_story(
            f"st_anchor_{safe_id}",
            f"Warranty year {number} badge",
            [numeral_xml],
        )
        background = (
            f'<Polygon Self="bg_{safe_id}" ContentType="Unassigned" '
            'AppliedObjectStyle="ObjectStyle/$ID/[None]" '
            'FillColor="Color/HB Brand Dark" StrokeColor="Swatch/None" '
            'StrokeWeight="0" ItemTransform="1 0 0 1 0 0">\n'
            + _po.rounded_path_geometry(
                0.0,
                -diameter,
                diameter,
                0.0,
                diameter / 2.0,
            )
            + _anchor()
            + '</Polygon>\n'
        )
        numeral_frame = _text_frame(
            numeral_sid,
            f"tf_{safe_id}",
            0.0,
            -diameter,
            diameter,
            0.0,
            valign="CenterAlign",
        )
        badge = (
            f'<Group Self="grp_{safe_id}" '
            'AppliedObjectStyle="ObjectStyle/$ID/[None]" '
            'ItemTransform="1 0 0 1 0 0">\n'
            + background
            + numeral_frame
            + '</Group>'
        )

    if badge:
        # Pin the unit to the same component-owned x coordinate used by the
        # subtitle below.  Letting a literal space follow the inline badge
        # made the unit advance font-dependent and allowed the two baselines
        # to drift apart when the Unicode circled digit became native IDML.
        xml = psr("HB Warranty Year Heading", f"\t{unit}")
        tab_properties = (
            '<Properties><TabList type="list"><ListItem type="record">'
            '<Alignment type="enumeration">LeftAlign</Alignment>'
            '<AlignmentCharacter type="string"></AlignmentCharacter>'
            '<Leader type="string"></Leader>'
            f'<Position type="unit">{unit_indent:g}</Position>'
            '</ListItem></TabList></Properties>'
        )
        xml = xml.replace(
            "\n    <CharacterStyleRange",
            f"\n    {tab_properties}\n    <CharacterStyleRange",
            1,
        )
        marker = (
            'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
        )
        xml = xml.replace(marker, marker + badge, 1)
    else:
        # Pure component callers do not own a story registry.  Preserve a
        # readable fallback there; production IDML writers always provide
        # ``add_story`` and therefore take the native circular path above.
        xml = psr("HB Warranty Year Heading", f"**{number}** {unit}")
        xml = xml.replace(
            'FontStyle="Bold"',
            f'PointSize="{badge_size:g}" FontStyle="Bold"',
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
    section_index: int | None = None,
) -> tuple[str, float]:
    items = list(spec.get("items", []))
    if not items:
        return "", 0.0
    gap = param_pt(ctx.params, "comp_warranty_year_column_gap", 2.27)
    left_ratio = _variant_value(
        spec,
        ctx,
        "year_left_ratio",
        _language_param(
            ctx,
            "idml_warranty_year_left_ratio",
            float(ctx.params.get(
                "comp_warranty_year_left_ratio", ("0.59", "ratio"),
            )[0]),
        ),
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
    rendered_body_leading = _variant_value(
        spec, ctx, "body_font_leading", body_leading,
    )
    section_horizontal_scale = _variant_value(
        spec,
        ctx,
        "body_horizontal_scale",
        _language_param(ctx, "idml_warranty_body_horizontal_scale", 100.0),
    )
    horizontal_scale = _variant_value(
        spec,
        ctx,
        "year_body_horizontal_scale",
        section_horizontal_scale,
    )
    estimate_horizontal_scale = _variant_value(
        spec,
        ctx,
        "body_estimate_horizontal_scale",
        horizontal_scale,
    )
    if section_index is not None:
        estimate_horizontal_scale = _variant_value(
            spec,
            ctx,
            f"body_estimate_horizontal_scale_{section_index}",
            estimate_horizontal_scale,
        )
    badge_size = param_pt(ctx.params, "type_warranty_year_number_font_size", 21.0)
    subtitle_size = param_pt(ctx.params, "type_warranty_year_subtitle_font_size", 7.2)
    unit_indent = param_pt(
        ctx.params, "idml_warranty_year_subtitle_left_indent", 21.31,
    )
    if ctx.add_story is not None:
        # The approved 21.31 pt token was measured against the former Unicode
        # circled-digit advance.  Native badge geometry is 4.90 pt wider at
        # the unit baseline.  Keep the frozen approved token intact and own
        # that renderer migration delta inside the shared native component.
        unit_indent += _language_param(
            ctx,
            "idml_warranty_native_badge_indent_adjust",
            4.90,
        )
    for index, (item, col_w) in enumerate(zip(items, cols)):
        subtitle = str(item.get("label", "")).strip()
        body = str(item.get("text", "")).strip()
        content = _year_heading(
            item,
            ctx,
            marker_id=f"warranty_year_{tid}_{index}",
            unit_indent=unit_indent,
        )
        if _variant_value(
            spec, ctx, "strip_year_subtitle_leading_dash", 0.0,
        ) >= 0.5:
            subtitle = re.sub(r"^[\s—–-]+", "", subtitle)
        subtitle_xml = psr("HB Warranty Year Subtitle", subtitle)
        # The subtitle's first letter sits on the same vertical as the unit
        # text (the ``Y`` in ``YEARS``), not after an additional optical gap.
        subtitle_xml = subtitle_xml.replace(
            "<ParagraphStyleRange ",
            f'<ParagraphStyleRange LeftIndent="{unit_indent:g}" ',
            1,
        )
        content += subtitle_xml
        # The reference returns the explanatory copy to the left edge of each
        # column; only the subtitle carries the optical badge offset.
        content += _variant_body_format(
            psr("HB Warranty Body", body, terminal=True),
            spec,
            ctx,
            horizontal_scale=horizontal_scale,
            leading=(
                rendered_body_leading
                if rendered_body_leading != body_leading else None
            ),
        )
        cells.append(cell(
            f"{tid}c{index}", f"{index}:0", content,
            stroke=False, top=0, bottom=0,
            left=0, right=(gap if index < len(items) - 1 else 0),
            valign="TopAlign",
        ))
        lines = _wrapped_lines(
            body,
            col_w - 2.0,
            body_size * estimate_horizontal_scale / 100.0,
        )
        max_height = max(
            max_height,
            badge_size
            + 1.0
            + subtitle_size
            + 2.0
            + lines * rendered_body_leading,
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
    width = _panel_width(ctx, measure_w or ctx.text_measure)
    lead_lines = [
        _plain_strong(str(value)) for value in spec.get("texts", []) if value
    ]
    text = "\n".join(lead_lines)
    size = param_pt(ctx.params, "type_warranty_lead_font_size", 7.0)
    leading = param_pt(ctx.params, "type_warranty_lead_font_leading", 8.2)
    pad_lr = param_pt(ctx.params, "comp_warranty_lead_pad_lr", 10.2)
    pad_tb = _language_param(
        ctx,
        "idml_warranty_lead_pad_tb",
        param_pt(ctx.params, "comp_warranty_lead_pad_tb", 7.65),
    )
    horizontal_scale = _variant_value(
        spec,
        ctx,
        "lead_horizontal_scale",
        _language_param(ctx, "idml_warranty_lead_horizontal_scale", 100.0),
    )
    lines = (
        len(lead_lines)
        if len(lead_lines) > 1
        else _wrapped_lines(text, width - 2 * pad_lr, size)
    ) or 1
    natural_height = lines * leading + 2 * pad_tb
    governed_height = _language_param(
        ctx, "idml_warranty_lead_height", natural_height,
    )
    height = (
        max(natural_height, governed_height)
        if len(lead_lines) > 1 else governed_height
    )
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
    before = _language_param(ctx, "idml_warranty_lead_before", 1.98)
    after = param_pt(ctx.params, "comp_warranty_lead_after", 2.83)
    xml = xml.replace(
        "<ParagraphStyleRange ",
        '<ParagraphStyleRange '
        f'LeftIndent="{_language_param(ctx, "idml_warranty_lead_left_indent", 0.0):g}" '
        f'SpaceBefore="{before:g}" SpaceAfter="{after:g}" ',
        1,
    )
    return xml, before + height + after


def _section_body(
    blocks: list[dict],
    ctx: RenderContext,
    *,
    tid: str,
    width: float,
    layout_spec: dict,
    section_index: int,
) -> tuple[list[str], float]:
    body_size = param_pt(ctx.params, "type_warranty_body_font_size", 6.0)
    body_leading = param_pt(ctx.params, "idml_warranty_body_font_leading", 6.0)
    list_leading = param_pt(ctx.params, "type_warranty_body_font_leading", 7.2)
    body_after = param_pt(ctx.params, "idml_warranty_paragraph_after", 2.83)
    list_after = param_pt(ctx.params, "idml_warranty_list_after", 1.0)
    horizontal_scale = _variant_value(
        layout_spec,
        ctx,
        "body_horizontal_scale",
        _language_param(
            ctx, "idml_warranty_body_horizontal_scale", 100.0,
        ),
    )
    estimate_horizontal_scale = _variant_value(
        layout_spec,
        ctx,
        "body_estimate_horizontal_scale",
        horizontal_scale,
    )
    estimate_horizontal_scale = _variant_value(
        layout_spec,
        ctx,
        f"body_estimate_horizontal_scale_{section_index}",
        estimate_horizontal_scale,
    )
    rendered_body_leading = _variant_value(
        layout_spec, ctx, "body_font_leading", body_leading,
    )
    list_indent = param_pt(
        ctx.params, "idml_warranty_list_left_indent", 5.67,
    )
    parts: list[str] = []
    height = 0.0
    for block_index, block in enumerate(blocks):
        kind = str(block.get("kind", "body"))
        terminal = block_index == len(blocks) - 1
        if kind == "component" and block.get("spec", {}).get("kind") == "warrantyyears":
            years_spec = dict(block["spec"])
            if layout_spec.get("layout_variant"):
                years_spec["layout_variant"] = layout_spec["layout_variant"]
            table, table_height = _years_table(
                years_spec,
                ctx,
                tid=f"{tid}_years",
                width=width,
                section_index=section_index,
            )
            # The native circle reaches above the ordinary text ascender.  A
            # composition-level clearance keeps it below the section-title
            # plate without baking a page-specific offset into JE/JBP/KR.
            badge_clearance = param_pt(
                ctx.params,
                "comp_warranty_section_pad_top",
                9.07,
            )
            parts.append(wrap_table_paragraph(
                table,
                True,
                span_columns=False,
            ))
            height += badge_clearance + table_height
            continue
        text = str(block.get("text", ""))
        is_list = kind in {"list", "sublist"}
        style = "HB Warranty List" if is_list else "HB Warranty Body"
        leading = list_leading if is_list else body_leading
        paragraph_after = list_after if is_list else body_after
        list_marker = ""
        list_text = text
        if is_list:
            marker_match = re.match(r"^\s*([•◦])(?:\s+|$)", text)
            if marker_match:
                list_marker = marker_match.group(1)
                list_text = text[marker_match.end():]
            else:
                list_marker = "◦" if kind == "sublist" else "•"
                list_text = text.lstrip()
        paragraph = psr(
            style,
            list_text if is_list else text,
            terminal=terminal,
        )
        if is_list:
            first_line_indent = param_pt(
                ctx.params, "idml_warranty_list_first_line_indent", -list_indent,
            )
            paragraph = paragraph.replace(
                "<ParagraphStyleRange ",
                f'<ParagraphStyleRange LeftIndent="{list_indent:g}" '
                f'FirstLineIndent="{first_line_indent:g}" RightIndent="0" ',
                1,
            )
            # Keep the bullet out of the prose run.  A literal ``• `` makes
            # the continuation line depend on the font's bullet glyph width;
            # the approved reference uses a fixed tab stop after the marker.
            tab_properties = (
                '<Properties><TabList type="list"><ListItem type="record">'
                '<Alignment type="enumeration">LeftAlign</Alignment>'
                '<AlignmentCharacter type="string"></AlignmentCharacter>'
                '<Leader type="string"></Leader>'
                f'<Position type="unit">{list_indent:g}</Position>'
                '</ListItem></TabList></Properties>'
            )
            bullet_xml = (
                '<CharacterStyleRange '
                'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
                'PointSize="4.8">'
                f'<Content>{list_marker}</Content>'
                '</CharacterStyleRange>'
            )
            tab_xml = (
                '<CharacterStyleRange '
                'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
                '<Content>\t</Content>'
                '</CharacterStyleRange>'
            )
            paragraph = paragraph.replace(
                "\n    <CharacterStyleRange",
                f"\n    {tab_properties}\n    {bullet_xml}\n    {tab_xml}\n    <CharacterStyleRange",
                1,
            )
        paragraph = _variant_body_format(
            paragraph,
            layout_spec,
            ctx,
            horizontal_scale=horizontal_scale,
            leading=(
                rendered_body_leading
                if not is_list and rendered_body_leading != body_leading else None
            ),
        )
        if not terminal:
            paragraph = paragraph.replace(
                "<ParagraphStyleRange ",
                f'<ParagraphStyleRange SpaceAfter="{paragraph_after:g}" ',
                1,
            )
        parts.append(paragraph)
        available = width - (
            list_indent if kind in {"list", "sublist"} else 0.0
        )
        height += _wrapped_lines(
            list_text if is_list else text,
            available,
            body_size * estimate_horizontal_scale / 100.0,
        ) * leading
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
    width = _panel_width(ctx, measure_w or ctx.text_measure)
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
        blocks,
        ctx,
        tid=tid,
        width=inner_w,
        layout_spec=spec,
        section_index=index,
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
    panel_adjust = _language_param(
        ctx,
        f"idml_warranty_panel_height_adjust_{index}",
        0.0,
    ) + _variant_adjust(
        spec,
        ctx,
        f"panel_height_adjust_{index}",
    )
    panel_h = max(
        22.0,
        pad_top + body_height + pad_bottom - trim + panel_adjust,
    )
    title_horizontal_scale = _language_param(
        ctx,
        "idml_warranty_title_horizontal_scale",
        100.0,
    )
    title_estimate_scale = _language_param(
        ctx,
        "idml_warranty_title_estimate_horizontal_scale",
        title_horizontal_scale,
    )
    title_estimate_size = (
        param_pt(ctx.params, "idml_warranty_title_font_size", 8.0)
        * title_estimate_scale
        / 100.0
    )
    title_leading = param_pt(ctx.params, "type_warranty_title_font_leading", 8.8)
    title_pad_lr = param_pt(ctx.params, "comp_warranty_title_pad_lr", 5.1)
    title_pad_tb = param_pt(ctx.params, "comp_warranty_title_pad_tb", 1.98)
    title_h = title_leading + 2 * title_pad_tb
    title_w = min(
        width - 2 * pad_lr,
        max(
            55.0,
            estimated_text_width(
                title,
                point_size=title_estimate_size,
                narrow_width_ratio=0.53,
            ) + 2 * title_pad_lr,
        ),
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

    title_xml = psr("HB Warranty Title", title, terminal=True).replace(
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
        f'HorizontalScale="{title_horizontal_scale:g}"',
        1,
    )
    title_sid = ctx.add_story(
        f"st_anchor_warranty_title_{tid}",
        f"{title} warranty panel title",
        [title_xml],
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
    body_top_adjust = _variant_value(
        spec,
        ctx,
        f"body_top_adjust_{index}",
        _variant_value(spec, ctx, "body_top_adjust", 0.0),
    )
    if any(
        str(block.get("kind") or "") == "component"
        and str(block.get("spec", {}).get("kind") or "") == "warrantyyears"
        for block in blocks
    ):
        # SpaceBefore on the first paragraph of an InDesign text frame is
        # ignored.  Allocate the extra height above and move the body frame's
        # top edge instead, keeping the native circles clear of the title.
        body_top_adjust += param_pt(
            ctx.params,
            "comp_warranty_section_pad_top",
            9.07,
        )
    body_frame = _text_frame(
        body_sid,
        f"tf_warranty_body_{tid}",
        pad_lr,
        -panel_h + pad_top + body_top_adjust,
        width - pad_lr,
        -(
            _language_param(
                ctx, "idml_warranty_exclusions_body_bottom_inset", 0.0,
            )
            if index == 5 else max(0.0, pad_bottom - trim)
        ),
        valign=(
            "CenterAlign"
            if index == 6
            and _variant_value(spec, ctx, "final_body_center", 0.0) >= 0.5
            else "TopAlign"
        ),
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
    before_default_key = (
        "comp_warranty_first_section_before" if index == 1
        else "idml_warranty_period_section_before" if index == 2
        else "idml_warranty_final_section_before" if index == 6
        else "idml_warranty_section_before"
    )
    before = _language_param(
        ctx,
        f"idml_warranty_section_{index}_before",
        param_pt(ctx.params, before_default_key, 4.25),
    )
    before = max(
        0.0,
        before + _variant_adjust(
            spec,
            ctx,
            f"section_{index}_before_adjust",
        ),
    )
    after = param_pt(ctx.params, "comp_warranty_section_after", 1.13)
    host = host.replace(
        "<ParagraphStyleRange ",
        f'<ParagraphStyleRange SpaceBefore="{before:g}" SpaceAfter="{after:g}" ',
        1,
    )
    return host, before + panel_h + after
