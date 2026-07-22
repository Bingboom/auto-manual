"""Operation panel component (template-parity P3).

The V2.0 master's operation sections are bordered panels with one full-width
illustration and editable copy positioned over the artwork's reserved zones.
Every copy block is emitted as its own top-layer text frame so an InDesign
operator can select, move, and edit it during final-mile layout work.
"""
from __future__ import annotations

from pathlib import Path

from ..character_metrics import with_character_metrics
from ..primitives import (
    cell,
    component_table,
    image_cell_content,
    path_geometry,
    psr,
    wrap_table_paragraph,
)
from ..page_objects import rounded_path_geometry
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
    if len(text) > 44:
        estimated_w = len(text) * 6.2 * 0.52 + 10.0
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
            image_w * 0.775,
            -image_h + image_h * 0.02,
            image_w * 0.225,
            26.1 * scale,
            22.0 * scale,
        )
    if "dc_usb" in stem or "dc-usb" in stem:
        return (
            image_w * 0.815,
            -image_h + image_h * 0.165,
            image_w * 0.185,
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
) -> str:
    """Create one independently movable top-layer frame per operation row."""
    if not rows or ctx.add_story is None:
        return ""
    left, first_top, width, gap, frame_h = _row_layout(ref, image_w, image_h)
    if max(len(label) for label, _instruction in rows) >= 8:
        width = max(width, image_w * 0.16)
        left = image_w - width
    frames = []
    for index, (label, instruction) in enumerate(rows):
        top = first_top + index * gap
        frames.append(_editable_text_frame(
            ctx,
            story_id=f"st_anchor_oppanel_row_{index}_{tid}",
            frame_id=f"tf_oppanel_row_{index}_{tid}",
            title=f"{tid} operation row {index + 1}",
            parts=[
                psr("HB Title L2", label),
                psr("HB Body", instruction, terminal=True),
            ],
            left=left,
            top=top,
            right=left + width,
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
    chars_per_line = max(18, int(width / (size * 0.52)))
    return sum(
        max(1, (len(line.strip()) + chars_per_line - 1) // chars_per_line)
        for line in text.splitlines() or [""]
    )


def _positioned_image(
    rect_id: str,
    asset: Path,
    width: float,
    height: float,
    *,
    left: float,
    bottom: float,
) -> str:
    """Place one linked image inside a composed operation-panel group."""
    xml = image_cell_content(rect_id, asset, width, height)
    return xml.replace(
        'ItemTransform="1 0 0 1 0 0"',
        f'ItemTransform="1 0 0 1 {left:g} {bottom:g}"',
        1,
    )


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
    )
    if space_after:
        xml = xml.replace(
            "<ParagraphStyleRange ",
            f'<ParagraphStyleRange SpaceAfter="{space_after:g}" ',
            1,
        )
    return xml, height + space_after


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
    mode_label = str(spec.get("mode_label") or "On/Off").strip()
    duration = str(spec.get("duration") or "3s").strip()

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

    copy_width = width - 28.0
    leading = 7.5
    guidance_heights = [
        _estimated_lines(text, copy_width) * leading + 0.8
        for text in guidance[:2]
    ]
    while len(guidance_heights) < 2:
        guidance_heights.append(leading + 0.8)
    grey_height = max(49.0, 9.0 + sum(guidance_heights))
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
        left=7.5,
        top=grey_top,
        right=width - 7.5,
        bottom=grey_bottom,
        radius=7.0,
        fill="Color/HB Bg K05",
    ))

    clock = ctx.resolve_bundle_image("icon_clock_3s.png")
    if clock is not None and clock.exists():
        shapes.append(_positioned_image(
            f"oppanel_energy_clock_{tid}", clock, 10.5, 10.5,
            left=width * 0.601,
            bottom=-12.0,
        ))

    text_layers: list[str] = []
    text_top = grey_top + 4.8
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
            left=14.0,
            top=text_top,
            right=width - 14.0,
            bottom=text_top + frame_height,
            auto_height=True,
        ))
        text_top += frame_height

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
            left=width * 0.68,
            top=-29.5 - action_delta,
            right=width * 0.86,
            bottom=-16.0 - action_delta,
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
            left=width * 0.642,
            top=-21.5,
            right=width * 0.69,
            bottom=-9.0,
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
            left=width * 0.682,
            top=-6.0 - action_height,
            right=width - 10.0,
            bottom=-6.0,
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
    if len(steps) >= 2:
        center = row_centers[1]
        text_layers.append(_editable_text_frame(
            ctx,
            story_id=f"st_anchor_oppanel_led_sos_{tid}",
            frame_id=f"tf_oppanel_led_sos_{tid}",
            title=f"{tid} LED SOS label",
            parts=[_sized_psr(
                "HB Body", "SOS", size=6.0, leading=6.8,
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
        row_text = _row_text_layers(
            ctx, tid=tid, ref=ref, rows=rows, image_w=iw, image_h=ih,
        )
        overlay = prereq_underlay + tail_underlay + prereq_text + tail_text + row_text
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
