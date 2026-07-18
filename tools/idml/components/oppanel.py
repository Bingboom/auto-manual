"""Operation panel component (template-parity P3).

The V2.0 master's operation sections are bordered panels: illustration
left, bold On/Off rows right, an optional grey "Prerequisite" pill
above. Detected from the prose blocks by tools/idml/oppanel.transform;
this renderer builds the panel as a one-row two-column bordered table
(rounded page-level objects don't exist inside flowed stories).
"""
from __future__ import annotations

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


def _inline_anchor() -> str:
    """Return the anchor contract shared by operation overlay objects."""
    return (
        '    <AnchoredObjectSetting AnchoredPosition="InlinePosition" '
        'SpineRelative="false" LockPosition="false" PinPosition="true" '
        'AnchorPoint="BottomRightAnchor" HorizontalAlignment="LeftAlign" '
        'HorizontalReferencePoint="TextFrame" VerticalAlignment="TopAlign" '
        'VerticalReferencePoint="LineBaseline" AnchorXoffset="0" '
        'AnchorYoffset="0" AnchorSpaceAbove="0"/>\n'
    )


def _prereq_overlay(ctx: RenderContext, *, tid: str, text: str,
                    image_w: float, image_h: float) -> str:
    """Place editable prerequisite text over the artwork's blank pill."""
    if not text or ctx.add_story is None:
        return ""

    # The governed operation artwork reserves roughly the first 46% of its
    # width and 13pt of height for this light-grey pill.  Keep the overlay
    # proportional as the art is scaled for different page measures.
    label_w = image_w * 0.46
    label_h = 13.0
    left = 5.0
    top = -image_h + 5.0
    right = left + label_w
    bottom = top + label_h
    label_sid = ctx.add_story(
        f"st_anchor_oppanel_prereq_{tid}",
        f"{tid} prerequisite label",
        [psr("HB Body", f"**{text}**", terminal=True)],
    )
    inset_xml = "".join(
        f'<ListItem type="unit">{value:g}</ListItem>'
        for value in (4.0, 1.5, 4.0, 1.5)
    )
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
    text_frame = (
        f'<TextFrame Self="tf_oppanel_prereq_{tid}" '
        f'ParentStory="{label_sid}" PreviousTextFrame="n" NextTextFrame="n" '
        'ContentType="TextType" '
        'AppliedObjectStyle="ObjectStyle/$ID/[Normal Text Frame]" '
        'FillColor="Swatch/None" StrokeColor="Swatch/None" StrokeWeight="0" '
        'ItemTransform="1 0 0 1 0 0">\n'
        + path_geometry(left, top, right, bottom)
        + '    <TextFramePreference TextColumnCount="1" '
        'VerticalJustification="CenterAlign" AutoSizingType="Off">'
        f'<Properties><InsetSpacing type="list">{inset_xml}'
        '</InsetSpacing></Properties></TextFramePreference>\n'
        + _inline_anchor()
        + '  </TextFrame>\n'
    )
    return mask + background + text_frame


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
        iw, ih = ctx.art_frame_size(asset, max_w=body_w * 0.88)
        overlay = _prereq_overlay(
            ctx, tid=tid, text=prereq, image_w=iw, image_h=ih,
        )
        fallback = psr("HB Body", f"**{prereq}**") if prereq and not overlay else ""
        image_xml = image_cell_content(f"{tid}img", asset, iw, ih)
        if overlay:
            image_xml = (
                f'<Group Self="grp_oppanel_{tid}" '
                'AppliedObjectStyle="ObjectStyle/$ID/[None]" '
                'ItemTransform="1 0 0 1 0 0">'
                + image_xml + overlay + '</Group>'
            )
        icon = fallback + figure_paragraph(
            image_xml, tail="<Content></Content>")
        img_h = ih

    # The artwork intentionally reaches into the visual space beside the
    # illustration (its callout rules terminate near the On/Off column).  A
    # 74/26 split matches the master better than the old 80/20 split while
    # leaving enough width for the editable labels and tail pill.
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
    if ctx.add_story is not None:
        # master parity: rounded light-grey outline, no inner grid
        from .. import page_objects as _po
        inner_w = body_w - 8.0
        icol = inner_w * 0.74
        cells = [
            cell(f"{tid}c0", "0:0", icon, stroke=False,
                 top=5, bottom=5, left=5, right=4),
            cell(f"{tid}c1", "1:0", right, stroke=False,
                 top=6, bottom=5, left=6, right=5),
        ]
        inner = wrap_table_paragraph(component_table(
            tid, [icol, max(60.0, inner_w - icol)], cells,
            role="warning"), True, False)
        xml = _po.anchored_panel_paragraph(
            ctx.add_story, f"st_anchor_oppanel_{tid}", "operation panel",
            [inner], body_w, est * 1.15 + 8.0, terminal=terminal,
            stroke="Color/HB Border K10", stroke_weight=1.1, radius=10.0,
            inset=(3, 3, 3, 3), valign="TopAlign", auto_height=True)
        return xml, est + 8.0
    cols = [img_col, max(60.0, body_w - img_col)]
    cells = [
        cell(f"{tid}c0", "0:0", icon, top=5, bottom=5, left=5, right=4),
        cell(f"{tid}c1", "1:0", right, top=6, bottom=5, left=6, right=5),
    ]
    table = component_table(tid, cols, cells, role="warning")
    return wrap_table_paragraph(table, terminal, span_columns), est
