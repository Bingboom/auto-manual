"""Operation panel component (template-parity P3).

The V2.0 master's operation sections are bordered panels with one full-width
illustration and editable copy positioned over the artwork's reserved zones.
Every copy block is emitted as its own top-layer text frame so an InDesign
operator can select, move, and edit it during final-mile layout work.
"""
from __future__ import annotations

import re
from pathlib import Path

from ..language_contract import governed_languages
from ..character_metrics import with_character_metrics
from ..line_metrics import estimated_line_count, estimated_text_width
from ..primitives import (
    cell,
    component_table,
    image_cell_content,
    path_geometry,
    psr,
    wrap_table_paragraph,
)
from ..page_objects import rounded_path_geometry
from ..params import component_param_pt, param_pt
from ..source_copy import source_text
from .base import RenderContext, figure_paragraph


def _inline_anchor(*, pin: bool = True) -> str:
    """Return the anchor contract shared by operation overlay objects."""
    return (
        '    <AnchoredObjectSetting AnchoredPosition="InlinePosition" '
        f'SpineRelative="false" LockPosition="false" PinPosition="{str(pin).lower()}" '
        'AnchorPoint="BottomRightAnchor" HorizontalAlignment="LeftAlign" '
        'HorizontalReferencePoint="TextFrame" VerticalAlignment="TopAlign" '
        'VerticalReferencePoint="LineBaseline" AnchorXoffset="0" '
        'AnchorYoffset="0" AnchorSpaceAbove="0"/>\n'
    )


def _editable_text_frame(
    ctx: RenderContext,
    *,
    story_id: str,
    frame_id: str,
    title: str,
    parts: list[str],
    left: float,
    top: float,
    right: float,
    bottom: float,
    inset: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
    valign: str = "TopAlign",
    auto_height: bool = False,
) -> str:
    """Return an independently editable, manually positionable text frame."""
    if ctx.add_story is None:
        return ""
    sid = ctx.add_story(story_id, title, parts)
    inset_xml = "".join(
        f'<ListItem type="unit">{value:g}</ListItem>' for value in inset
    )
    auto_xml = (
        ' AutoSizingType="HeightOnly" AutoSizingReferencePoint="TopCenterPoint"'
        if auto_height else ' AutoSizingType="Off"'
    )
    return (
        f'<TextFrame Self="{frame_id}" '
        f'ParentStory="{sid}" PreviousTextFrame="n" NextTextFrame="n" '
        'ContentType="TextType" '
        'AppliedObjectStyle="ObjectStyle/$ID/[Normal Text Frame]" '
        'FillColor="Swatch/None" StrokeColor="Swatch/None" StrokeWeight="0" '
        'ItemTransform="1 0 0 1 0 0">\n'
        + path_geometry(left, top, right, bottom)
        + '    <TextFramePreference TextColumnCount="1" '
        f'VerticalJustification="{valign}"{auto_xml}>'
        f'<Properties><InsetSpacing type="list">{inset_xml}'
        '</InsetSpacing></Properties></TextFramePreference>\n'
        + _inline_anchor(pin=False)
        + '  </TextFrame>\n'
    )


def _prereq_overlay_parts(
    ctx: RenderContext, *, tid: str, text: str, image_w: float, image_h: float,
) -> tuple[str, str]:
    """Return prerequisite underlay and top-layer editable text separately."""
    if not text or ctx.add_story is None:
        return "", ""

    # Measured from reference pages 07/08: the pill starts 3pt inside the art,
    # spans about 45.5% of the art width, and is 13.7pt tall.
    label_w = image_w * 0.455
    # The approved EN/FR prerequisite fits the measured one-line pill.  The
    # longer Spanish copy needs more of the otherwise empty top strip; widen
    # by glyph estimate instead of letting the fixed-height text frame overset.
    estimated_w = estimated_text_width(text, point_size=6.2) + 10.0
    if estimated_w > label_w:
        label_w = min(image_w * 0.62, max(label_w, estimated_w))
    label_h = 13.7
    left = 3.0
    top = -image_h + 3.0
    right = left + label_w
    bottom = top + label_h
    # The source artwork still contains a light-grey placeholder pill.  Cover
    # that baked-in paint first so the replacement remains genuinely editable
    # (and does not show a darker halo at the rounded edges).  Keep the mask a
    # little larger than the replacement, but constrained to the same reserved
    # area so it cannot cover neighbouring artwork.
    mask = (
        f'<Rectangle Self="oppanel_prereq_mask_{tid}" '
        'ContentType="Unassigned" '
        'AppliedObjectStyle="ObjectStyle/$ID/[None]" '
        'FillColor="Color/Paper" StrokeColor="Swatch/None" '
        'StrokeWeight="0" ItemTransform="1 0 0 1 0 0">\n'
        + rounded_path_geometry(left - 1.0, top - 1.0, right + 1.0, bottom + 1.0, 7.5)
        + _inline_anchor()
        + '  </Rectangle>\n'
    )
    background = (
        f'<Rectangle Self="oppanel_prereq_bg_{tid}" '
        'ContentType="Unassigned" '
        'AppliedObjectStyle="ObjectStyle/HB Rounded Panel" '
        'FillColor="Color/HB Bg K05" StrokeColor="Swatch/None" '
        'StrokeWeight="0" ItemTransform="1 0 0 1 0 0">\n'
        + rounded_path_geometry(left, top, right, bottom, 6.5)
        + _inline_anchor()
        + '  </Rectangle>\n'
    )
    text_frame = _editable_text_frame(
        ctx,
        story_id=f"st_anchor_oppanel_prereq_{tid}",
        frame_id=f"tf_oppanel_prereq_{tid}",
        title=f"{tid} prerequisite label",
        parts=[psr("HB Body", f"**{text}**", terminal=True)],
        left=left,
        top=top,
        right=right,
        bottom=bottom,
        # InDesign stores insets as top, left, bottom, right.
        inset=(1.5, 5.0, 1.5, 5.0),
        valign="CenterAlign",
    )
    return mask + background, text_frame


def _prereq_overlay(ctx: RenderContext, *, tid: str, text: str,
                    image_w: float, image_h: float) -> str:
    """Compatibility wrapper returning the complete prerequisite stack."""
    underlay, text_frame = _prereq_overlay_parts(
        ctx, tid=tid, text=text, image_w=image_w, image_h=image_h,
    )
    return underlay + text_frame


def _row_layout(ref: str, image_w: float, image_h: float) -> tuple[float, ...]:
    """Return measured row geometry for POWER, AC, and DC/USB artwork."""
    stem = Path(ref).stem.lower()
    scale = image_w / 294.9
    if "main_power" in stem:
        return (
            image_w * 0.765,
            -image_h + image_h * 0.035,
            image_w * 0.235,
            26.1 * scale,
            22.0 * scale,
        )
    if "dc_usb" in stem or "dc-usb" in stem:
        return (
            image_w * 0.845,
            -image_h + image_h * 0.165,
            image_w * 0.155,
            20.6 * scale,
            19.5 * scale,
        )
    # AC artwork and the generic prerequisite layout share the same reserved
    # upper-right bracket zone.
    return (
        image_w * 0.845,
        -image_h + image_h * 0.23,
        image_w * 0.155,
        23.1 * scale,
        20.5 * scale,
    )


def _row_text_layers(
    ctx: RenderContext,
    *,
    tid: str,
    ref: str,
    rows: list[tuple[str, str]],
    image_w: float,
    image_h: float,
    panel_w: float | None = None,
) -> str:
    """Create one independently movable top-layer frame per operation row."""
    if not rows or ctx.add_story is None:
        return ""
    left, first_top, width, gap, frame_h = _row_layout(ref, image_w, image_h)
    panel_right = panel_w if panel_w is not None else image_w / 0.945
    right_edge_offset = component_param_pt(
        ctx.params,
        "idml_operation_row_right_edge_offset",
        6.5,
        strict=ctx.strict_component_assets,
        owner="operation-row right edge",
    )
    if max(len(label) for label, _instruction in rows) >= 8:
        width = max(width, image_w * 0.16)
        left = image_w - width
    frames = []
    language = (ctx.language or "en").strip().lower().replace("_", "-").split("-", 1)[0]
    base_label_size = component_param_pt(
        ctx.params,
        "idml_operation_row_label_font_size",
        10.0,
        strict=ctx.strict_component_assets,
        owner="operation row label",
    )
    base_label_leading = component_param_pt(
        ctx.params,
        "idml_operation_row_label_font_leading",
        11.0,
        strict=ctx.strict_component_assets,
        owner="operation row label",
    )
    label_size = component_param_pt(
        ctx.params,
        f"lang_{language}_idml_operation_row_label_font_size",
        base_label_size,
        strict=ctx.strict_component_assets and language in governed_languages(),
        owner="localized operation row label",
    )
    label_leading = component_param_pt(
        ctx.params,
        f"lang_{language}_idml_operation_row_label_font_leading",
        base_label_leading,
        strict=ctx.strict_component_assets and language in governed_languages(),
        owner="localized operation row label",
    )
    stem = Path(ref).stem.lower()
    row_x_offset = 0.0
    row_y_offsets = [0.0, 0.0]
    if "main_power" in stem:
        row_y_offsets = [
            component_param_pt(
                ctx.params,
                "idml_operation_main_power_on_y_offset",
                0.0,
                strict=ctx.strict_component_assets,
                owner="main-power On row position",
            ),
            component_param_pt(
                ctx.params,
                "idml_operation_main_power_off_y_offset",
                0.0,
                strict=ctx.strict_component_assets,
                owner="main-power Off row position",
            ),
        ]
    elif "dc_usb" in stem or "dc-usb" in stem:
        row_x_offset = component_param_pt(
            ctx.params,
            "idml_operation_dc_usb_x_offset",
            0.0,
            strict=ctx.strict_component_assets,
            owner="DC/USB operation-row position",
        )
    else:
        row_y_offsets[1] = component_param_pt(
            ctx.params,
            "idml_operation_ac_output_off_y_offset",
            0.0,
            strict=ctx.strict_component_assets,
            owner="AC-output Off row position",
        )
    for index, (label, instruction) in enumerate(rows):
        top = first_top + index * gap + row_y_offsets[min(index, 1)]
        frames.append(_editable_text_frame(
            ctx,
            story_id=f"st_anchor_oppanel_row_{index}_{tid}",
            frame_id=f"tf_oppanel_row_{index}_{tid}",
            title=f"{tid} operation row {index + 1}",
            parts=[
                _sized_psr(
                    "HB Operation Row Label",
                    label,
                    size=label_size,
                    leading=label_leading,
                    terminal=False,
                ),
                psr("HB Body", instruction, terminal=True),
            ],
            left=left + row_x_offset,
            top=top,
            right=max(
                left + row_x_offset + width,
                panel_right + right_edge_offset,
            ),
            bottom=top + frame_h,
            auto_height=True,
        ))
    return "".join(frames)


def _tail_overlay_parts(
    ctx: RenderContext, *, tid: str, text: str, image_w: float, image_h: float,
) -> tuple[str, str]:
    """Return the POWER standby grey box and its editable top-layer copy."""
    if not text or ctx.add_story is None:
        return "", ""
    left = image_w * 0.407
    right = image_w
    bottom = -image_h + image_h * 0.955
    lines = [line for line in text.splitlines() if line.strip()]
    line_count = sum(max(1, (len(line) + 54) // 55) for line in lines)
    scale = image_w / 294.9
    box_height = max(42.7 * scale, (8.0 + line_count * 7.5) * scale)
    top = bottom - box_height
    background = (
        f'<Rectangle Self="oppanel_tail_bg_{tid}" ContentType="Unassigned" '
        'AppliedObjectStyle="ObjectStyle/HB Rounded Panel" '
        'FillColor="Color/HB Bg K05" StrokeColor="Swatch/None" '
        'StrokeWeight="0" ItemTransform="1 0 0 1 0 0">\n'
        + rounded_path_geometry(left, top, right, bottom, 6.5)
        + _inline_anchor()
        + '  </Rectangle>\n'
    )
    text_frame = _editable_text_frame(
        ctx,
        story_id=f"st_anchor_oppanel_tail_{tid}",
        frame_id=f"tf_oppanel_tail_{tid}",
        title=f"{tid} standby note",
        parts=[psr("HB Body", text, terminal=True)],
        left=left,
        top=top,
        right=right,
        bottom=bottom,
        inset=(4.0, 5.0, 4.0, 5.0),
    )
    return background, text_frame


def _sized_psr(
    style: str,
    text: str,
    *,
    size: float,
    leading: float,
    terminal: bool = True,
    justification: str | None = None,
) -> str:
    """Return a paragraph with compact reference-art type overrides."""
    xml = psr(style, text, terminal=terminal)
    paragraph_attrs = ""
    if justification:
        paragraph_attrs = f'Justification="{justification}" '
    if paragraph_attrs:
        xml = xml.replace(
            "<ParagraphStyleRange ",
            f"<ParagraphStyleRange {paragraph_attrs}",
            1,
        )
    return with_character_metrics(
        xml,
        point_size=size,
        leading=leading,
    )


def _estimated_lines(text: str, width: float, *, size: float = 6.2) -> int:
    """Conservative localized-copy wrap estimate for fixed overlay slots."""
    return estimated_line_count(
        text,
        width,
        point_size=size,
        minimum_narrow_chars=18,
    )


def _positioned_image(
    rect_id: str,
    asset: Path,
    width: float,
    height: float,
    *,
    left: float,
    bottom: float,
    pin: bool = True,
) -> str:
    """Place one linked image inside a composed operation-panel group."""
    xml = image_cell_content(rect_id, asset, width, height)
    xml = xml.replace(
        'ItemTransform="1 0 0 1 0 0"',
        f'ItemTransform="1 0 0 1 {left:g} {bottom:g}"',
        1,
    )
    if not pin:
        xml = xml.replace('PinPosition="true"', 'PinPosition="false"', 1)
    return xml


def _operation_duration(rows: list[tuple[str, str]]) -> str:
    """Return the compact duration token embedded in localized row copy."""
    for _label, instruction in rows:
        match = re.search(
            r"\b(\d+)\s*(?:seconds?|secondes?|segundos?|s)\b",
            instruction,
            re.I,
        )
        if match is not None:
            return f"{match.group(1)}s"
    return ""


def _main_power_clock_overlay(
    ctx: RenderContext,
    *,
    tid: str,
    ref: str,
    rows: list[tuple[str, str]],
    image_w: float,
    image_h: float,
) -> str:
    """Replace the baked POWER clock and restore its editable duration."""
    if "main_power" not in Path(ref).stem.lower():
        return ""
    clock = ctx.resolve_bundle_image("icon_clock_3s.png")
    if clock is None or not clock.exists():
        return ""

    size = component_param_pt(
        ctx.params,
        "idml_operation_main_power_clock_size",
        10.5,
        strict=ctx.strict_component_assets,
        owner="main-power movable clock",
    )
    x_offset = component_param_pt(
        ctx.params,
        "idml_operation_main_power_clock_x_offset",
        0.0,
        strict=ctx.strict_component_assets,
        owner="main-power movable clock",
    )
    y_offset = component_param_pt(
        ctx.params,
        "idml_operation_main_power_clock_y_offset",
        0.0,
        strict=ctx.strict_component_assets,
        owner="main-power movable clock",
    )
    duration = _operation_duration(rows)
    duration_gap = component_param_pt(
        ctx.params,
        "idml_operation_main_power_duration_gap",
        1.3,
        strict=ctx.strict_component_assets,
        owner="main-power editable duration",
    )
    duration_x_offset = component_param_pt(
        ctx.params,
        "idml_operation_main_power_duration_x_offset",
        0.0,
        strict=ctx.strict_component_assets,
        owner="main-power editable duration",
    )
    duration_y_offset = component_param_pt(
        ctx.params,
        "idml_operation_main_power_duration_y_offset",
        0.0,
        strict=ctx.strict_component_assets,
        owner="main-power editable duration",
    )
    duration_size = component_param_pt(
        ctx.params,
        "idml_operation_main_power_duration_font_size",
        7.2,
        strict=ctx.strict_component_assets,
        owner="main-power editable duration",
    )
    duration_leading = component_param_pt(
        ctx.params,
        "idml_operation_main_power_duration_font_leading",
        8.0,
        strict=ctx.strict_component_assets,
        owner="main-power editable duration",
    )
    clock_left = image_w * 0.714 + x_offset
    clock_bottom = -image_h * 0.46 + y_offset
    mask = _shape(
        shape_id=f"oppanel_main_power_clock_mask_{tid}",
        left=image_w * 0.762,
        top=-image_h * 0.58,
        right=image_w * 0.810,
        bottom=-image_h * 0.45,
        fill="Color/Paper",
    )
    clock_xml = _positioned_image(
        f"oppanel_main_power_clock_{tid}",
        clock,
        size,
        size,
        left=clock_left,
        bottom=clock_bottom,
        pin=False,
    )
    if not duration:
        return mask + clock_xml
    duration_left = clock_left + size + duration_gap + duration_x_offset
    duration_top = clock_bottom - size + duration_y_offset
    duration_xml = _editable_text_frame(
        ctx,
        story_id=f"st_anchor_oppanel_main_power_duration_{tid}",
        frame_id=f"tf_oppanel_main_power_duration_{tid}",
        title=f"{tid} main-power duration",
        parts=[_sized_psr(
            "HB Body",
            duration,
            size=duration_size,
            leading=duration_leading,
            terminal=True,
        )],
        left=duration_left,
        top=duration_top,
        right=duration_left + max(13.0, duration_size * 2.2),
        bottom=clock_bottom + duration_y_offset,
        valign="CenterAlign",
    )
    return mask + clock_xml + duration_xml


def _shape(
    *,
    shape_id: str,
    left: float,
    top: float,
    right: float,
    bottom: float,
    radius: float = 0.0,
    fill: str = "Swatch/None",
    stroke: str = "Swatch/None",
    stroke_weight: float = 0.0,
) -> str:
    geometry = (
        rounded_path_geometry(left, top, right, bottom, radius)
        if radius else path_geometry(left, top, right, bottom)
    )
    return (
        f'<Rectangle Self="{shape_id}" ContentType="Unassigned" '
        'AppliedObjectStyle="ObjectStyle/$ID/[None]" '
        f'FillColor="{fill}" StrokeColor="{stroke}" '
        f'StrokeWeight="{stroke_weight:g}" '
        'ItemTransform="1 0 0 1 0 0">\n'
        + geometry
        + _inline_anchor()
        + '  </Rectangle>\n'
    )


def _panel_bounds(tid: str, width: float, height: float) -> str:
    """Interior bounds leave room for the group's host-story line box.

    A nested inline group exactly as tall as its containing text frame imports
    as an overset object character and the whole panel renders blank.  The
    special panels already reserve 8pt above and at least 6pt below their art;
    expose those margins as flow slack while keeping the full outer frame at
    the approved reference dimensions.
    """
    return _shape(
        shape_id=f"oppanel_bounds_{tid}",
        left=0.0,
        top=-height + 8.0,
        right=width,
        bottom=-6.0,
    )


def _bold_colon_lead(text: str) -> str:
    """Bold the first reference lead through its first colon, language-free."""
    indexes = [position for mark in (":", "：")
               if (position := text.find(mark)) >= 0]
    if not indexes:
        return text
    split_at = min(indexes) + 1
    return f"**{text[:split_at]}**{text[split_at:]}"


def _bulb_underlay(tid: str, index: int, *, left: float, center: float) -> str:
    """Small native bulb outline used by LED steps one and three."""
    dark = "Color/HB Brand Dark"
    prefix = f"oppanel_led_bulb_{index}_{tid}"
    pieces = [
        _shape(
            shape_id=f"{prefix}_glass",
            left=left + 3.0,
            top=center - 5.5,
            right=left + 11.0,
            bottom=center + 2.5,
            radius=4.0,
            fill="Color/Paper",
            stroke=dark,
            stroke_weight=0.75,
        ),
        _shape(
            shape_id=f"{prefix}_base",
            left=left + 5.0,
            top=center + 3.2,
            right=left + 9.0,
            bottom=center + 4.1,
            fill=dark,
        ),
        _shape(
            shape_id=f"{prefix}_ray_top",
            left=left + 6.7,
            top=center - 9.0,
            right=left + 7.3,
            bottom=center - 6.7,
            fill=dark,
        ),
        _shape(
            shape_id=f"{prefix}_ray_left",
            left=left,
            top=center - 2.0,
            right=left + 2.2,
            bottom=center - 1.4,
            fill=dark,
        ),
        _shape(
            shape_id=f"{prefix}_ray_right",
            left=left + 11.8,
            top=center - 2.0,
            right=left + 14.0,
            bottom=center - 1.4,
            fill=dark,
        ),
    ]
    return "".join(pieces)


def _special_panel_paragraph(
    ctx: RenderContext,
    *,
    tid: str,
    title: str,
    group_content: str,
    width: float,
    height: float,
    terminal: bool,
    space_after: float = 0.0,
    anchor_x_offset: float = 0.0,
    anchor_y_offset: float = 0.0,
) -> tuple[str, float]:
    """Wrap a measured editable group in the operation-panel outline."""
    from .. import page_objects as _po

    group = (
        f'<Group Self="grp_oppanel_{tid}" '
        'AppliedObjectStyle="ObjectStyle/$ID/[None]" '
        'ItemTransform="1 0 0 1 -10.2 8">'
        + group_content
        + "</Group>"
    )
    inner = figure_paragraph(group, tail="<Content></Content>")
    xml = _po.anchored_panel_paragraph(
        ctx.add_story,
        f"st_anchor_oppanel_{tid}",
        title,
        [inner],
        width,
        height,
        terminal=terminal,
        fill="Color/Paper",
        stroke="Color/HB Border K10",
        stroke_weight=1.1,
        radius=10.0,
        # The interior bounds already expose the visual top/bottom margins.
        # Keep the carrier inset-free so its paragraph line box has the full
        # outer height available during IDML import.
        inset=(0, 0, 0, 0),
        valign="TopAlign",
        auto_height=False,
        anchor_x_offset=anchor_x_offset,
        anchor_y_offset=anchor_y_offset,
    )
    if space_after:
        xml = xml.replace(
            "<ParagraphStyleRange ",
            f'<ParagraphStyleRange SpaceAfter="{space_after:g}" ',
            1,
        )
    return xml, height + space_after


def _render_image_caption_panel(
    spec: dict,
    ctx: RenderContext,
    *,
    tid: str,
    terminal: bool,
    measure_w: float | None,
) -> tuple[str, float]:
    """Render linked operation art and editable caption in one rounded card."""

    width = measure_w or ctx.text_measure
    caption = source_text(
        spec.get("caption"),
        owner="operation image-caption panel",
        strict=ctx.strict_component_assets,
    )
    ref = str(spec.get("image") or "").strip()
    asset = ctx.resolve_bundle_image(ref) if ref else None
    if asset is None or not asset.exists():
        if ctx.strict_component_assets:
            raise FileNotFoundError(
                f"operation image-caption asset missing: {ref}"
            )
        return psr("HB Body", caption, terminal=terminal), 16.0

    art_w, art_h = ctx.art_frame_size(asset, max_w=width - 30.0)
    caption_width = width - 30.0
    caption_size = 5.4
    caption_leading = 6.2
    caption_lines = _estimated_lines(
        caption, caption_width, size=caption_size,
    )
    caption_height = max(20.0, caption_lines * caption_leading + 7.0)
    height = art_h + caption_height + 8.0
    art_top = -height + 4.0
    caption_bottom = -4.0
    caption_top = caption_bottom - caption_height

    shapes = [
        _panel_bounds(tid, width, height),
        _positioned_image(
            f"oppanel_image_caption_art_{tid}",
            asset,
            art_w,
            art_h,
            left=(width - art_w) / 2.0,
            bottom=art_top + art_h,
        ),
        _shape(
            shape_id=f"oppanel_image_caption_bg_{tid}",
            left=7.0,
            top=caption_top,
            right=width - 7.0,
            bottom=caption_bottom,
            radius=7.0,
            fill="Color/HB Bg K05",
        ),
    ]
    caption_frame = _editable_text_frame(
        ctx,
        story_id=f"st_anchor_oppanel_image_caption_{tid}",
        frame_id=f"tf_oppanel_image_caption_{tid}",
        title=f"{tid} image caption",
        parts=[_sized_psr(
            "HB Body",
            caption,
            size=caption_size,
            leading=caption_leading,
            terminal=True,
        )],
        left=14.0,
        top=caption_top,
        right=width - 14.0,
        bottom=caption_bottom,
        inset=(3.0, 0.0, 3.0, 0.0),
        valign="CenterAlign",
    )
    return _special_panel_paragraph(
        ctx,
        tid=tid,
        title="image caption operation panel",
        group_content="".join(shapes) + caption_frame,
        width=width,
        height=height,
        terminal=terminal,
    )


def _render_image_notice_panel(
    spec: dict,
    ctx: RenderContext,
    *,
    tid: str,
    terminal: bool,
    measure_w: float | None,
) -> tuple[str, float]:
    """Render operation artwork and its following notice in one outer card."""

    from .notice import render_notice

    width = measure_w or ctx.text_measure
    ref = str(spec.get("image") or "").strip()
    asset = ctx.resolve_bundle_image(ref) if ref else None
    if asset is None or not asset.exists():
        if ctx.strict_component_assets:
            raise FileNotFoundError(f"operation image-notice asset missing: {ref}")
        notice = dict(spec.get("notice") or {})
        return render_notice(
            notice,
            ctx,
            tid=f"{tid}_notice",
            terminal=terminal,
            measure_w=width,
        )

    notice_spec = dict(spec.get("notice") or {})
    notice_spec["space_before"] = 0.0
    notice_spec["space_after"] = 0.0
    notice_w = width - 14.0
    notice_xml, notice_estimate = render_notice(
        notice_spec,
        ctx,
        tid=f"{tid}_notice",
        terminal=True,
        measure_w=notice_w,
    )
    group_start = notice_xml.index('<Group Self="grp_notice_')
    group_end = notice_xml.index("</Group>", group_start) + len("</Group>")
    notice_group = notice_xml[group_start:group_end].replace(
        'ItemTransform="1 0 0 1 0 0"',
        'ItemTransform="1 0 0 1 7 -7"',
        1,
    )
    notice_gap = param_pt(ctx.params, "comp_data_table_before", 3.4)
    notice_h = max(1.0, notice_estimate - 2.0 * notice_gap)

    rows = [tuple(row) for row in spec.get("rows", [])]
    prereq = str(spec.get("prereq") or "").strip()
    tail = str(spec.get("tail") or "").strip()
    art_w, art_h = ctx.art_frame_size(asset, max_w=width - 18.0)
    art_left = (width - art_w) / 2.0
    height = art_h + notice_h + 19.0
    art_bottom = -notice_h - 12.0
    prereq_underlay, prereq_text = _prereq_overlay_parts(
        ctx, tid=tid, text=prereq, image_w=art_w, image_h=art_h,
    )
    tail_underlay, tail_text = _tail_overlay_parts(
        ctx, tid=tid, text=tail, image_w=art_w, image_h=art_h,
    )
    art_group = (
        f'<Group Self="grp_oppanel_image_notice_art_{tid}" '
        'AppliedObjectStyle="ObjectStyle/$ID/[None]" '
        f'ItemTransform="1 0 0 1 {art_left:g} {art_bottom:g}">'
        + image_cell_content(f"oppanel_image_notice_art_{tid}", asset, art_w, art_h)
        + prereq_underlay
        + tail_underlay
        + _main_power_clock_overlay(
            ctx, tid=tid, ref=ref, rows=rows, image_w=art_w, image_h=art_h,
        )
        + prereq_text
        + tail_text
        + _row_text_layers(
            ctx,
            tid=tid,
            ref=ref,
            rows=rows,
            image_w=art_w,
            image_h=art_h,
            panel_w=art_w,
        )
        + "</Group>"
    )
    return _special_panel_paragraph(
        ctx,
        tid=tid,
        title="image notice operation panel",
        group_content=_panel_bounds(tid, width, height) + art_group + notice_group,
        width=width,
        height=height,
        terminal=terminal,
    )


def _render_energy_saving_panel(
    spec: dict,
    ctx: RenderContext,
    *,
    tid: str,
    terminal: bool,
    measure_w: float | None,
) -> tuple[str, float]:
    """Render the reference Energy Saving card with editable top copy."""
    width = measure_w or ctx.text_measure
    guidance = [str(item).strip() for item in spec.get("guidance", [])
                if str(item).strip()]
    action = str(spec.get("action") or "").strip()
    mode_label = source_text(
        spec.get("mode_label"),
        owner="Energy Saving mode label",
        strict=ctx.strict_component_assets,
    )
    duration = source_text(
        spec.get("duration"),
        owner="Energy Saving duration",
        strict=ctx.strict_component_assets,
    )

    mode_x_offset = component_param_pt(
        ctx.params,
        "idml_operation_energy_mode_x_offset",
        0.0,
        strict=ctx.strict_component_assets,
        owner="Energy Saving On/Off position",
    )
    mode_y_offset = component_param_pt(
        ctx.params,
        "idml_operation_energy_mode_y_offset",
        0.0,
        strict=ctx.strict_component_assets,
        owner="Energy Saving On/Off position",
    )
    duration_x_offset = component_param_pt(
        ctx.params,
        "idml_operation_energy_duration_x_offset",
        0.0,
        strict=ctx.strict_component_assets,
        owner="Energy Saving duration position",
    )
    duration_y_offset = component_param_pt(
        ctx.params,
        "idml_operation_energy_duration_y_offset",
        0.0,
        strict=ctx.strict_component_assets,
        owner="Energy Saving duration position",
    )
    clock_x_offset = component_param_pt(
        ctx.params,
        "idml_operation_energy_clock_x_offset",
        0.0,
        strict=ctx.strict_component_assets,
        owner="Energy Saving clock position",
    )
    clock_y_offset = component_param_pt(
        ctx.params,
        "idml_operation_energy_clock_y_offset",
        0.0,
        strict=ctx.strict_component_assets,
        owner="Energy Saving clock position",
    )
    guidance_x_offset = component_param_pt(
        ctx.params,
        "idml_operation_energy_guidance_x_offset",
        0.0,
        strict=ctx.strict_component_assets,
        owner="Energy Saving guidance-panel position",
    )
    guidance_y_offset = component_param_pt(
        ctx.params,
        "idml_operation_energy_guidance_y_offset",
        0.0,
        strict=ctx.strict_component_assets,
        owner="Energy Saving guidance-panel position",
    )
    action_x_offset = component_param_pt(
        ctx.params,
        "idml_operation_energy_action_x_offset",
        0.0,
        strict=ctx.strict_component_assets,
        owner="Energy Saving action-copy position",
    )
    action_y_offset = component_param_pt(
        ctx.params,
        "idml_operation_energy_action_y_offset",
        0.0,
        strict=ctx.strict_component_assets,
        owner="Energy Saving action-copy position",
    )
    panel_y_offset = component_param_pt(
        ctx.params,
        "idml_operation_energy_panel_y_offset",
        0.0,
        strict=ctx.strict_component_assets,
        owner="Energy Saving whole-panel position",
    )

    action_width = (width - 10.0) - width * 0.682
    action_leading = 6.0
    action_lines = _estimated_lines(action, action_width, size=6.0)
    action_height = (
        14.0 if action_lines <= 2 else action_lines * action_leading + 3.0
    )
    # Moving the panel's last visible copy 2pt above the flow bound creates
    # the same 6pt outer margin as the reference and keeps localized growth
    # inside the card.  Shift On/Off by the same delta so it remains above the
    # action when French wraps to three lines.
    action_delta = action_height - 14.0 + 2.0
    mode_vertical_shift = 3.0

    copy_width = width - 28.0
    leading = 7.5
    guidance_gap = component_param_pt(
        ctx.params,
        "idml_operation_energy_guidance_gap",
        -2.0,
        strict=ctx.strict_component_assets,
        owner="Energy Saving guidance paragraph rhythm",
    )
    guidance_heights = [
        _estimated_lines(text, copy_width) * leading + 0.8
        for text in guidance[:2]
    ]
    while len(guidance_heights) < 2:
        guidance_heights.append(leading + 0.8)
    visible_guidance_count = min(2, len(guidance))
    grey_height = max(
        49.0,
        9.0 + sum(guidance_heights[:visible_guidance_count])
        + guidance_gap * max(0, visible_guidance_count - 1),
    )
    height = max(width * 0.545, grey_height + 110.0)
    grey_top = -height + 8.0
    grey_bottom = grey_top + grey_height

    shapes = [_panel_bounds(tid, width, height)]
    ref = str(spec.get("image") or "").strip()
    asset = ctx.resolve_bundle_image(ref) if ref else None
    if asset is not None and asset.exists():
        art_w, art_h = ctx.art_frame_size(asset, max_w=width * 0.873)
        art_top = grey_bottom + 4.5
        shapes.append(_positioned_image(
            f"{tid}img", asset, art_w, art_h,
            left=width * 0.060,
            bottom=art_top + art_h,
        ))
    shapes.append(_shape(
        shape_id=f"oppanel_energy_guidance_bg_{tid}",
        left=7.5 + guidance_x_offset,
        top=grey_top + guidance_y_offset,
        right=width - 7.5 + guidance_x_offset,
        bottom=grey_bottom + guidance_y_offset,
        radius=7.0,
        fill="Color/HB Bg K05",
    ))

    clock = ctx.resolve_bundle_image("icon_clock_3s.png")
    if clock is not None and clock.exists():
        shapes.append(_positioned_image(
            f"oppanel_energy_clock_{tid}", clock, 10.5, 10.5,
            left=width * 0.601 + clock_x_offset,
            bottom=-12.0 + clock_y_offset,
        ))

    text_layers: list[str] = []
    text_top = grey_top + 4.8 + guidance_y_offset
    for index, text in enumerate(guidance[:2]):
        frame_height = guidance_heights[index]
        text_layers.append(_editable_text_frame(
            ctx,
            story_id=f"st_anchor_oppanel_energy_guidance_{index}_{tid}",
            frame_id=f"tf_oppanel_energy_guidance_{index}_{tid}",
            title=f"{tid} energy guidance {index + 1}",
            parts=[_sized_psr(
                "HB Body", text, size=6.2, leading=leading, terminal=True,
            )],
            left=14.0 + guidance_x_offset,
            top=text_top,
            right=width - 14.0 + guidance_x_offset,
            bottom=text_top + frame_height,
            auto_height=True,
        ))
        text_top += frame_height
        if index + 1 < min(2, len(guidance)):
            text_top += guidance_gap

    text_layers.extend([
        _editable_text_frame(
            ctx,
            story_id=f"st_anchor_oppanel_energy_mode_{tid}",
            frame_id=f"tf_oppanel_energy_mode_{tid}",
            title=f"{tid} energy mode label",
            parts=[_sized_psr(
                "HB Title L2", mode_label, size=10.2, leading=11.2,
                terminal=True,
            )],
            left=width * 0.68 + mode_x_offset,
            top=-29.5 - action_delta + mode_vertical_shift + mode_y_offset,
            right=width * 0.86 + mode_x_offset,
            bottom=-16.0 - action_delta + mode_vertical_shift + mode_y_offset,
            auto_height=True,
        ),
        _editable_text_frame(
            ctx,
            story_id=f"st_anchor_oppanel_energy_duration_{tid}",
            frame_id=f"tf_oppanel_energy_duration_{tid}",
            title=f"{tid} energy duration",
            parts=[_sized_psr(
                "HB Body", duration, size=7.2, leading=8.0, terminal=True,
            )],
            left=width * 0.642 + duration_x_offset,
            top=-21.5 + duration_y_offset,
            right=width * 0.69 + duration_x_offset,
            bottom=-9.0 + duration_y_offset,
            valign="CenterAlign",
        ),
        _editable_text_frame(
            ctx,
            story_id=f"st_anchor_oppanel_energy_action_{tid}",
            frame_id=f"tf_oppanel_energy_action_{tid}",
            title=f"{tid} energy action",
            parts=[_sized_psr(
                "HB Body", action, size=6.0, leading=action_leading,
                terminal=True,
            )],
            left=width * 0.682 + action_x_offset,
            top=-6.0 - action_height + action_y_offset,
            right=width - 10.0 + action_x_offset,
            bottom=-6.0 + action_y_offset,
        ),
    ])
    return _special_panel_paragraph(
        ctx,
        tid=tid,
        title="energy saving operation panel",
        group_content="".join(shapes) + "".join(text_layers),
        width=width,
        height=height,
        terminal=terminal,
        space_after=2.0,
        anchor_y_offset=panel_y_offset,
    )


def _render_led_light_panel(
    spec: dict,
    ctx: RenderContext,
    *,
    tid: str,
    terminal: bool,
    measure_w: float | None,
) -> tuple[str, float]:
    """Render the reference LED card with movable step copy and labels."""
    width = measure_w or ctx.text_measure
    lead = str(spec.get("lead") or "").strip()
    steps = [str(item).strip() for item in spec.get("steps", [])
             if str(item).strip()][:3]
    height = max(145.0, width * 0.465)
    lead_width = width - 32.0
    lead_height = max(16.0, _estimated_lines(lead, lead_width) * 7.5 + 3.0)
    grey_top = -height + 9.0
    grey_bottom = grey_top + max(25.0, lead_height + 7.0)

    shapes = [_panel_bounds(tid, width, height)]
    ref = str(spec.get("image") or "").strip()
    # The reference LED art includes the complete product/LIGHT-button
    # illustration. Keep the source copy and all step labels as editable
    # top-layer frames, but use the complete governed illustration as the
    # background when the staged bundle contains it.
    asset = (
        ctx.resolve_bundle_image("operation/led_light_complete.png")
        if ref and "led_light" in Path(ref).stem.lower()
        else ctx.resolve_bundle_image(ref)
    ) if ref else None
    if asset is not None and asset.exists():
        art_w, art_h = ctx.art_frame_size(asset, max_w=width * 0.568)
        shapes.append(_positioned_image(
            f"{tid}img", asset, art_w, art_h,
            left=width * 0.054,
            bottom=-6.0,
        ))
    shapes.append(_shape(
        shape_id=f"oppanel_led_lead_bg_{tid}",
        left=10.0,
        top=grey_top,
        right=width - 20.0,
        bottom=grey_bottom,
        radius=7.0,
        fill="Color/HB Bg K05",
    ))

    circle_left = width * 0.59
    icon_left = width * 0.65
    row_centers = [-height + 74.0, -height + 98.0, -height + 123.0]
    for index, center in enumerate(row_centers):
        shapes.append(_shape(
            shape_id=f"oppanel_led_number_bg_{index}_{tid}",
            left=circle_left,
            top=center - 7.5,
            right=circle_left + 15.0,
            bottom=center + 7.5,
            radius=7.5,
            fill="Color/Paper",
            stroke="Color/HB Brand Dark",
            stroke_weight=0.8,
        ))
        if index == 1:
            shapes.append(_shape(
                shape_id=f"oppanel_led_sos_bg_{tid}",
                left=icon_left,
                top=center - 5.0,
                right=icon_left + 20.0,
                bottom=center + 5.0,
                radius=5.0,
                fill="Color/Paper",
                stroke="Color/HB Brand Dark",
                stroke_weight=0.7,
            ))
        else:
            shapes.append(_bulb_underlay(
                tid, index, left=icon_left + 3.0, center=center,
            ))

    text_layers = [_editable_text_frame(
        ctx,
        story_id=f"st_anchor_oppanel_led_lead_{tid}",
        frame_id=f"tf_oppanel_led_lead_{tid}",
        title=f"{tid} LED lead",
        parts=[_sized_psr(
            "HB Body", _bold_colon_lead(lead), size=6.2, leading=7.5,
            terminal=True,
        )],
        left=16.0,
        top=grey_top + 4.0,
        right=width - 26.0,
        bottom=grey_bottom - 3.0,
        auto_height=True,
    )]
    for index, (center, step) in enumerate(zip(row_centers, steps)):
        text_layers.append(_editable_text_frame(
            ctx,
            story_id=f"st_anchor_oppanel_led_number_{index}_{tid}",
            frame_id=f"tf_oppanel_led_number_{index}_{tid}",
            title=f"{tid} LED step number {index + 1}",
            parts=[_sized_psr(
                "HB Title L2", str(index + 1), size=8.6, leading=9.4,
                terminal=True, justification="CenterAlign",
            )],
            left=circle_left,
            top=center - 7.5,
            right=circle_left + 15.0,
            bottom=center + 7.5,
            valign="CenterAlign",
        ))
        text_layers.append(_editable_text_frame(
            ctx,
            story_id=f"st_anchor_oppanel_led_step_{index}_{tid}",
            frame_id=f"tf_oppanel_led_step_{index}_{tid}",
            title=f"{tid} LED step {index + 1}",
            parts=[_sized_psr(
                "HB Body", step, size=6.2, leading=7.5, terminal=True,
            )],
            left=width * 0.72,
            top=center - 9.0,
            right=width - 8.0,
            bottom=center + 9.0,
            auto_height=True,
        ))
    sos_label = source_text(
        spec.get("sos_label"),
        owner="LED operation SOS label",
        strict=ctx.strict_component_assets,
    )
    if len(steps) >= 2 and sos_label:
        center = row_centers[1]
        text_layers.append(_editable_text_frame(
            ctx,
            story_id=f"st_anchor_oppanel_led_sos_{tid}",
            frame_id=f"tf_oppanel_led_sos_{tid}",
            title=f"{tid} LED SOS label",
            parts=[_sized_psr(
                "HB Body", sos_label, size=6.0, leading=6.8,
                terminal=True, justification="CenterAlign",
            )],
            left=icon_left,
            top=center - 5.0,
            right=icon_left + 20.0,
            bottom=center + 5.0,
            valign="CenterAlign",
        ))

    return _special_panel_paragraph(
        ctx,
        tid=tid,
        title="LED light operation panel",
        group_content="".join(shapes) + "".join(text_layers),
        width=width,
        height=height,
        terminal=terminal,
    )


def render_oppanel(spec: dict, ctx: RenderContext, *, tid: str, terminal: bool,
                   span_columns: bool = True,
                   measure_w: float | None = None) -> tuple[str, float]:
    layout = str(spec.get("layout") or "").strip().lower()
    if ctx.add_story is not None and layout == "energy_saving":
        return _render_energy_saving_panel(
            spec, ctx, tid=tid, terminal=terminal, measure_w=measure_w,
        )
    if ctx.add_story is not None and layout == "led_light":
        return _render_led_light_panel(
            spec, ctx, tid=tid, terminal=terminal, measure_w=measure_w,
        )
    if ctx.add_story is not None and layout == "image_caption":
        return _render_image_caption_panel(
            spec, ctx, tid=tid, terminal=terminal, measure_w=measure_w,
        )
    if ctx.add_story is not None and layout == "image_notice":
        return _render_image_notice_panel(
            spec, ctx, tid=tid, terminal=terminal, measure_w=measure_w,
        )

    body_w = measure_w or ctx.text_measure
    rows = [tuple(r) for r in spec.get("rows", [])]
    prereq = (spec.get("prereq") or "").strip()

    icon = ""
    img_h = 0.0
    ref = (spec.get("image") or "").strip()
    asset = ctx.resolve_bundle_image(ref) if ref else None
    if asset is not None and asset.exists():
        # The governed operation artwork already contains the product,
        # connector callouts, and reserved label zones.  Preserve that canvas
        # at reference scale; the previous half-column + height cap reduced it
        # to roughly one third of the intended visual area.
        iw, ih = ctx.art_frame_size(asset, max_w=body_w * 0.945)
        prereq_underlay, prereq_text = _prereq_overlay_parts(
            ctx, tid=tid, text=prereq, image_w=iw, image_h=ih,
        )
        tail = (spec.get("tail") or "").strip()
        tail_underlay, tail_text = _tail_overlay_parts(
            ctx, tid=tid, text=tail, image_w=iw, image_h=ih,
        )
        main_power_clock = _main_power_clock_overlay(
            ctx, tid=tid, ref=ref, rows=rows, image_w=iw, image_h=ih,
        )
        row_text = _row_text_layers(
            ctx, tid=tid, ref=ref, rows=rows, image_w=iw, image_h=ih,
            panel_w=body_w,
        )
        overlay = (
            prereq_underlay + tail_underlay + main_power_clock
            + prereq_text + tail_text + row_text
        )
        fallback = psr("HB Body", f"**{prereq}**") if prereq and not overlay else ""
        image_xml = image_cell_content(f"{tid}img", asset, iw, ih)
        if overlay:
            image_xml = (
                f'<Group Self="grp_oppanel_{tid}" '
                'AppliedObjectStyle="ObjectStyle/$ID/[None]" '
                'ItemTransform="1 0 0 1 -6.5 0">'
                # Artwork and shapes are emitted first; every text frame is
                # appended last so it opens at the top of the group z-order.
                + image_xml + overlay + '</Group>'
            )
        icon = fallback + figure_paragraph(
            image_xml, tail="<Content></Content>")
        img_h = ih

    if ctx.add_story is not None and icon:
        # Reference pages 07/08 use a full-width artwork canvas.  The panel is
        # only about 10-14pt taller than that canvas; a fixed frame prevents
        # localized row stories from inflating the outer panel unexpectedly.
        from .. import page_objects as _po
        panel_h = img_h + 12.0
        xml = _po.anchored_panel_paragraph(
            ctx.add_story,
            f"st_anchor_oppanel_{tid}",
            "operation panel",
            [icon],
            body_w,
            panel_h,
            terminal=terminal,
            stroke="Color/HB Border K10",
            stroke_weight=1.1,
            radius=10.0,
            inset=(3, 3, 3, 3),
            valign="TopAlign",
            auto_height=False,
        )
        return xml, panel_h

    # Table fallback for pure/table-only render contexts without sub-stories.
    img_col = body_w * 0.74
    right_width = max(60.0, body_w - 8.0 - img_col - 11.0)

    right_parts = []
    if prereq and ctx.add_story is None and not icon:
        right_parts.append(psr("HB Body", f"**{prereq}**"))
    for ri, (label, instruction) in enumerate(rows):
        right_parts.append(psr("HB Title L2", label))
        gap = "" if ri == len(rows) - 1 else "\n"
        right_parts.append(psr("HB Body", instruction + gap))
    tail = (spec.get("tail") or "").strip()
    tail_xml = ""
    if tail and ctx.add_story is not None:
        from .. import page_objects as _po
        tail_lines = max(1, len(tail) // 55 + 1)
        tail_height = 8.0 + 7.5 * tail_lines
        tail_xml = _po.anchored_panel_paragraph(
            ctx.add_story,
            f"st_anchor_oppanel_tail_{tid}",
            "operation tail",
            [psr("HB Body", tail, terminal=True)],
            right_width,
            tail_height,
            terminal=False,
            fill="Color/HB Bg K05",
            stroke=None,
            radius=6.5,
            inset=(3, 3, 3, 3),
            valign="TopAlign",
            auto_height=True,
        )
        right_parts.append(tail_xml)
    elif tail:
        right_parts.append(psr("HB Body", tail))
    if right_parts:
        right_parts[-1] = right_parts[-1].replace("<Br/>", "", 1)
    right = "".join(right_parts)

    tail_height = (8.0 + 7.5 * max(1, len(tail) // 55 + 1)) if tail else 0.0
    rows_h = sum(
        9.0 + 7.5 * max(1, len(instr) // 60 + 1) for _, instr in rows)
    rows_h += tail_height
    est = max(img_h + 12.0, rows_h + 12.0, 40.0)
    cols = [img_col, max(60.0, body_w - img_col)]
    cells = [
        cell(f"{tid}c0", "0:0", icon, top=5, bottom=5, left=5, right=4),
        cell(f"{tid}c1", "1:0", right, top=6, bottom=5, left=6, right=5),
    ]
    table = component_table(tid, cols, cells, role="warning")
    return wrap_table_paragraph(table, terminal, span_columns), est
