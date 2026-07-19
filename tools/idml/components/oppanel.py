"""Operation panel component (template-parity P3).

The V2.0 master's operation sections are bordered panels with one full-width
illustration and editable copy positioned over the artwork's reserved zones.
Every copy block is emitted as its own top-layer text frame so an InDesign
operator can select, move, and edit it during final-mile layout work.
"""
from __future__ import annotations

from pathlib import Path

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
            image_w * 0.797,
            -image_h + image_h * 0.02,
            image_w * 0.203,
            26.1 * scale,
            22.0 * scale,
        )
    if "dc_usb" in stem or "dc-usb" in stem:
        return (
            image_w * 0.895,
            -image_h + image_h * 0.165,
            image_w * 0.105,
            20.6 * scale,
            19.5 * scale,
        )
    # AC artwork and the generic prerequisite layout share the same reserved
    # upper-right bracket zone.
    return (
        image_w * 0.875,
        -image_h + image_h * 0.23,
        image_w * 0.125,
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


def render_oppanel(spec: dict, ctx: RenderContext, *, tid: str, terminal: bool,
                   span_columns: bool = True,
                   measure_w: float | None = None) -> tuple[str, float]:
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
