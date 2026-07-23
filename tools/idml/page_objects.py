"""Spread-level object helpers for composed IDML pages."""
from __future__ import annotations

from .params import param_pt

CAPSULE_OBJECT_STYLE = "ObjectStyle/HB Capsule Heading"
ROUNDED_TABLE_OBJECT_STYLE = "ObjectStyle/HB Rounded Table Outer"
PANEL_OBJECT_STYLE = "ObjectStyle/HB Rounded Panel"
CARD_OBJECT_STYLE = "ObjectStyle/HB Inbox Card"
BADGE_OBJECT_STYLE = "ObjectStyle/HB Badge"


def capsule_opts(inset: tuple[float, float, float, float]) -> dict:
    return heading_bar_opts(2, inset)


def h1_bar_opts(inset: tuple[float, float, float, float]) -> dict:
    return heading_bar_opts(1, inset)


def heading_bar_opts(level: int,
                     inset: tuple[float, float, float, float]) -> dict:
    if level == 1:
        return {
            "h1_bar_bg": True,
            "inset": inset,
            "valign": "CenterAlign",
        }
    if level == 2:
        return {
            "capsule_bg": True,
            "inset": inset,
            "valign": "CenterAlign",
        }
    return {"inset": inset}


def with_rounded_outer(opts: dict) -> dict:
    return {**opts, "rounded_outer": True}


def capsule_text(writer, text: str, *, point_size: float | None = None) -> str:
    return heading_text(writer, text, level=2, point_size=point_size)


def heading_text(writer, text: str, *, level: int,
                 point_size: float | None = None) -> str:
    # level 1 rides the HB Capsule Text baseline (the type_h1_* keys);
    # level 2 takes the subbar type size, both shared with params.tex.
    font_style = None
    if point_size is None and level == 2:
        from .params import param_pt
        point_size = param_pt(writer.params, "type_subbar_font_size", 6.6)
        # \HBTypeSubbar renders Gilroy-Medium in the publish line
        font_style = "Medium"
    xml = writer._psr("HB Capsule Text", text, terminal=True)
    if level == 1:
        # CenterAlign centres the font's line box, not Gilroy's visible caps.
        # Fixed/composed title frames need a slight downward optical shift;
        # flowed H1 hosts override it below because their inline line box has
        # different metrics.
        xml = xml.replace(
            'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
            'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
            'BaselineShift="-1.5"',
            1,
        )
    if point_size is None:
        return xml
    override = f'PointSize="{point_size:g}"'
    if font_style:
        override += f' FontStyle="{font_style}"'
    return xml.replace(
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
        + override,
        1,
    )


def rectangle_xml(rect_id: str, x1: float, y1: float, x2: float, y2: float, *,
                  fill: str = "Color/Paper",
                  stroke_color: str = "Color/HB Line K40",
                  stroke_weight: float = 0.75,
                  rounded: bool = True,
                  corner_radius: float = 5.5,
                  object_style: str = ROUNDED_TABLE_OBJECT_STYLE) -> str:
    from .primitives import path_geometry

    geometry = (
        rounded_path_geometry(x1, y1, x2, y2, corner_radius)
        if rounded else path_geometry(x1, y1, x2, y2)
    )
    return (
        f'  <Rectangle Self="{rect_id}" ContentType="Unassigned" '
        f'AppliedObjectStyle="{object_style}" FillColor="{fill}" '
        f'StrokeColor="{stroke_color}" StrokeWeight="{stroke_weight:g}" '
        'ItemTransform="1 0 0 1 0 0">\n'
        + geometry +
        '  </Rectangle>\n'
    )


def rounded_path_geometry(x1: float, y1: float, x2: float, y2: float,
                          radius: float) -> str:
    """Closed rounded rectangle path with real Bezier arcs.

    InDesign does not reliably turn CornerOption attributes on generated
    spline items into a visible shape. Emitting the path itself keeps the
    rounded outline visible after opening the IDML.
    """
    r = max(0.0, min(radius, abs(x2 - x1) / 2.0, abs(y2 - y1) / 2.0))
    if r <= 0:
        from .primitives import path_geometry
        return path_geometry(x1, y1, x2, y2)
    k = r * 0.5522847498
    points = (
        ((x1, y1 + r), (x1, y1 + r - k), (x1, y1 + r)),
        ((x1, y2 - r), (x1, y2 - r), (x1, y2 - r + k)),
        ((x1 + r, y2), (x1 + r - k, y2), (x1 + r, y2)),
        ((x2 - r, y2), (x2 - r, y2), (x2 - r + k, y2)),
        ((x2, y2 - r), (x2, y2 - r + k), (x2, y2 - r)),
        ((x2, y1 + r), (x2, y1 + r), (x2, y1 + r - k)),
        ((x2 - r, y1), (x2 - r + k, y1), (x2 - r, y1)),
        ((x1 + r, y1), (x1 + r, y1), (x1 + r - k, y1)),
    )
    anchors = "\n".join(
        f'            <PathPointType Anchor="{anchor[0]:g} {anchor[1]:g}" '
        f'LeftDirection="{left[0]:g} {left[1]:g}" '
        f'RightDirection="{right[0]:g} {right[1]:g}"/>'
        for anchor, left, right in points
    )
    return (
        '    <Properties>\n'
        '      <PathGeometry>\n'
        '        <GeometryPathType PathOpen="false">\n'
        '          <PathPointArray>\n'
        f'{anchors}\n'
        '          </PathPointArray>\n'
        '        </GeometryPathType>\n'
        '      </PathGeometry>\n'
        '    </Properties>\n'
    )


def rounded_corner_mask_geometry(x1: float, y1: float,
                                 x2: float, y2: float,
                                 radius: float, corner: str) -> str:
    """Return the square-corner area outside one rounded-rectangle arc.

    Editable InDesign tables remain rectangular even when their separate
    outer frame is rounded.  These three-point paths cover only the area
    outside the matching Bezier arc, preventing cell fills from protruding
    through the four corners without rasterizing or clipping the table.
    """
    r = max(0.0, min(radius, abs(x2 - x1) / 2.0, abs(y2 - y1) / 2.0))
    if r <= 0:
        return ""
    k = r * 0.5522847498
    if corner == "top_left":
        points = (
            ((x1, y1), (x1, y1), (x1, y1)),
            ((x1 + r, y1), (x1 + r, y1), (x1 + r - k, y1)),
            ((x1, y1 + r), (x1, y1 + r - k), (x1, y1 + r)),
        )
    elif corner == "top_right":
        points = (
            ((x2, y1), (x2, y1), (x2, y1)),
            ((x2, y1 + r), (x2, y1 + r), (x2, y1 + r - k)),
            ((x2 - r, y1), (x2 - r + k, y1), (x2 - r, y1)),
        )
    elif corner == "bottom_left":
        points = (
            ((x1, y2), (x1, y2), (x1, y2)),
            ((x1, y2 - r), (x1, y2 - r), (x1, y2 - r + k)),
            ((x1 + r, y2), (x1 + r - k, y2), (x1 + r, y2)),
        )
    elif corner == "bottom_right":
        points = (
            ((x2, y2), (x2, y2), (x2, y2)),
            ((x2 - r, y2), (x2 - r, y2), (x2 - r + k, y2)),
            ((x2, y2 - r), (x2, y2 - r + k), (x2, y2 - r)),
        )
    else:
        raise ValueError(f"unsupported rounded corner: {corner}")
    anchors = "\n".join(
        f'            <PathPointType Anchor="{anchor[0]:g} {anchor[1]:g}" '
        f'LeftDirection="{left[0]:g} {left[1]:g}" '
        f'RightDirection="{right[0]:g} {right[1]:g}"/>'
        for anchor, left, right in points
    )
    return (
        '    <Properties>\n'
        '      <PathGeometry>\n'
        '        <GeometryPathType PathOpen="false">\n'
        '          <PathPointArray>\n'
        f'{anchors}\n'
        '          </PathPointArray>\n'
        '        </GeometryPathType>\n'
        '      </PathGeometry>\n'
        '    </Properties>\n'
    )


def bottom_rounded_path_geometry(x1: float, y1: float, x2: float, y2: float,
                                 radius: float) -> str:
    """Closed rectangle with square top corners and rounded bottom corners."""
    r = max(0.0, min(radius, abs(x2 - x1) / 2.0, abs(y2 - y1)))
    if r <= 0:
        from .primitives import path_geometry
        return path_geometry(x1, y1, x2, y2)
    k = r * 0.5522847498
    points = (
        ((x1, y1), (x1, y1), (x1, y1)),
        ((x1, y2 - r), (x1, y2 - r), (x1, y2 - r + k)),
        ((x1 + r, y2), (x1 + r - k, y2), (x1 + r, y2)),
        ((x2 - r, y2), (x2 - r, y2), (x2 - r + k, y2)),
        ((x2, y2 - r), (x2, y2 - r + k), (x2, y2 - r)),
        ((x2, y1), (x2, y1), (x2, y1)),
    )
    anchors = "\n".join(
        f'            <PathPointType Anchor="{anchor[0]:g} {anchor[1]:g}" '
        f'LeftDirection="{left[0]:g} {left[1]:g}" '
        f'RightDirection="{right[0]:g} {right[1]:g}"/>'
        for anchor, left, right in points
    )
    return (
        '    <Properties>\n'
        '      <PathGeometry>\n'
        '        <GeometryPathType PathOpen="false">\n'
        '          <PathPointArray>\n'
        f'{anchors}\n'
        '          </PathPointArray>\n'
        '        </GeometryPathType>\n'
        '      </PathGeometry>\n'
        '    </Properties>\n'
    )


def left_rounded_path_geometry(x1: float, y1: float, x2: float, y2: float,
                               radius: float) -> str:
    """Closed rectangle with rounded left corners and square right corners."""
    r = max(0.0, min(radius, abs(x2 - x1) / 2.0, abs(y2 - y1) / 2.0))
    if r <= 0:
        from .primitives import path_geometry
        return path_geometry(x1, y1, x2, y2)
    k = r * 0.5522847498
    points = (
        ((x2, y1), (x2, y1), (x2, y1)),
        ((x2, y2), (x2, y2), (x2, y2)),
        ((x1 + r, y2), (x1 + r, y2), (x1 + r - k, y2)),
        ((x1, y2 - r), (x1, y2 - r + k), (x1, y2 - r)),
        ((x1, y1 + r), (x1, y1 + r), (x1, y1 + r - k)),
        ((x1 + r, y1), (x1 + r - k, y1), (x1 + r, y1)),
    )
    anchors = "\n".join(
        f'            <PathPointType Anchor="{anchor[0]:g} {anchor[1]:g}" '
        f'LeftDirection="{left[0]:g} {left[1]:g}" '
        f'RightDirection="{right[0]:g} {right[1]:g}"/>'
        for anchor, left, right in points
    )
    return (
        '    <Properties>\n'
        '      <PathGeometry>\n'
        '        <GeometryPathType PathOpen="false">\n'
        '          <PathPointArray>\n'
        f'{anchors}\n'
        '          </PathPointArray>\n'
        '        </GeometryPathType>\n'
        '      </PathGeometry>\n'
        '    </Properties>\n'
    )


def page_rectangle_xml(writer, rect_id: str,
                       rect: tuple[float, float, float, float], *,
                       fill: str = "Color/Paper",
                       stroke_color: str = "Color/HB Line K40",
                       stroke_weight: float = 0.75,
                       corner_radius: float = 5.5,
                       object_style: str = ROUNDED_TABLE_OBJECT_STYLE,
                       rounded: bool = True) -> str:
    x1, y1, x2, y2 = writer._page_rect(*rect)
    return rectangle_xml(
        rect_id, x1, y1, x2, y2,
        fill=fill,
        stroke_color=stroke_color,
        stroke_weight=stroke_weight,
        rounded=rounded,
        corner_radius=corner_radius,
        object_style=object_style,
    )


def left_rounded_xml(writer, rect_id: str,
                     rect: tuple[float, float, float, float], *,
                     fill: str = "Color/Paper",
                     corner_radius: float = 5.5,
                     object_style: str = PANEL_OBJECT_STYLE) -> str:
    x1, y1, x2, y2 = writer._page_rect(*rect)
    return (
        f'  <Rectangle Self="{rect_id}" ContentType="Unassigned" '
        f'AppliedObjectStyle="{object_style}" FillColor="{fill}" '
        'StrokeColor="Swatch/None" StrokeWeight="0" '
        'ItemTransform="1 0 0 1 0 0">\n'
        + left_rounded_path_geometry(x1, y1, x2, y2, corner_radius) +
        '  </Rectangle>\n'
    )


def h1_arc_pt(writer) -> float:
    """H1 bottom-corner radius from the shared layout param, the same
    key params.tex feeds \\HBTitleLevelOne (STYLE_MAP.md)."""
    from .params import param_pt
    return param_pt(writer.params, "comp_h1_pill_arc", 5.67)


def h1_bar_h_pt(writer) -> float:
    """H1 bar height from the same explicit token used by LaTeX."""
    from .params import param_pt
    return param_pt(writer.params, "comp_h1_pill_height", 20.126)


def capsule_xml(writer, rect_id: str,
                rect: tuple[float, float, float, float], *,
                bottom_only: bool = False,
                corner_radius: float | None = None) -> str:
    x1, y1, x2, y2 = writer._page_rect(*rect)
    # capsules are stadiums (radius = half height); H1 bars take the
    # shared CSV radius.  Composed pages may pass a measured master radius
    # when the source object is a rounded rectangle rather than a stadium.
    geometry = (
        bottom_rounded_path_geometry(x1, y1, x2, y2, h1_arc_pt(writer))
        if bottom_only
        else rounded_path_geometry(
            x1, y1, x2, y2,
            abs(y2 - y1) / 2.0 if corner_radius is None else corner_radius,
        )
    )
    return (
        f'  <Rectangle Self="{rect_id}" ContentType="Unassigned" '
        f'AppliedObjectStyle="{CAPSULE_OBJECT_STYLE}" '
        'FillColor="Color/HB Brand Dark" StrokeColor="Swatch/None" '
        'StrokeWeight="0" ItemTransform="1 0 0 1 0 0">\n'
        + geometry +
        '  </Rectangle>\n'
    )


def rounded_outer_xml(writer, rect_id: str,
                      rect: tuple[float, float, float, float]) -> str:
    x1, y1, x2, y2 = writer._page_rect(*rect)
    return rectangle_xml(rect_id, x1, y1, x2, y2)


def frame_with_background(writer, sid: str, frame_id: str, story_id: str,
                          rect: tuple[float, float, float, float],
                          opts: dict) -> str:
    opts = dict(opts)
    capsule_bg = bool(opts.pop("capsule_bg", False))
    h1_bar_bg = bool(opts.pop("h1_bar_bg", False))
    rounded_outer = bool(opts.pop("rounded_outer", False))
    text_rect = opts.pop("text_rect", rect)
    x1, y1, x2, y2 = writer._page_rect(*rect)
    tx1, ty1, tx2, ty2 = writer._page_rect(*text_rect)
    parts: list[str] = []
    if capsule_bg:
        parts.append(capsule_xml(writer, f"bg_{sid}_{frame_id}", rect))
    if h1_bar_bg:
        parts.append(capsule_xml(
            writer, f"bg_{sid}_{frame_id}", rect, bottom_only=True))
    if rounded_outer:
        parts.append(rounded_outer_xml(writer, f"bg_{sid}_{frame_id}", rect))
    parts.append(writer._frame_xml(
        f"tf_{sid}_{frame_id}", story_id, tx1, ty1, tx2, ty2, **opts))
    return "".join(parts)


def lcd_hero_paragraph(writer, lang: str = "en") -> str:
    """The master's annotated LCD line-art above the icon table
    (finished art cropped from the V2.0 PDF; numbers only, so one asset
    serves every language). Empty string when the asset is absent."""
    from pathlib import Path as _P

    from .style_names import paragraph_style_ref
    root = _P(__file__).resolve().parents[2]
    hero = (
        root / "docs" / "templates" / "word_template" / "common_assets"
        / "lcd" / "lcd_map.png"
    )
    if not hero.is_file():
        return ""
    width, height = writer._art_frame_size(
        hero, max_w=writer.page_w - writer.m_l - writer.m_r)
    # The template reserves ~159pt for the hero slot; a taller-aspect asset
    # (the vector v2 is 1.69:1 vs the old crop's 1.97:1) must shrink-to-fit
    # or it pushes the downstream prose chain into overset.
    language = (lang or "en").strip().casefold().replace("_", "-").split("-", 1)[0]
    hero_max_h = param_pt(
        writer.params,
        f"lang_{language}_idml_lcd_hero_max_height",
        param_pt(writer.params, "idml_lcd_hero_max_height", 159.0),
    )
    if height > hero_max_h:
        width, height = width * hero_max_h / height, hero_max_h
    horizontal_scale = float(writer.params.get(
        f"lang_{language}_idml_lcd_hero_horizontal_scale",
        writer.params.get("idml_lcd_hero_horizontal_scale", ("1", "ratio")),
    )[0])
    width *= horizontal_scale
    space_before = param_pt(
        writer.params,
        f"lang_{language}_idml_lcd_hero_space_before",
        param_pt(writer.params, "idml_lcd_hero_space_before", 5.72),
    )
    image_xml = writer._image_cell_content("lcd_hero", hero, width, height)
    if horizontal_scale != 1.0:
        image_xml = image_xml.replace(
            '<Image Self="lcd_hero_img" ItemTransform="1 0 0 1 0 0">',
            f'<Image Self="lcd_hero_img" ItemTransform="{horizontal_scale:g} 0 0 1 0 0">',
            1,
        )
    style = paragraph_style_ref("HB Figure")
    return (
        f'  <ParagraphStyleRange AppliedParagraphStyle="{style}" '
        f'Justification="CenterAlign" SpaceBefore="{space_before:g}" '
        'SpaceAfter="3.37">'
        '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
        + image_xml
        + "<Content></Content><Br/></CharacterStyleRange></ParagraphStyleRange>\n"
    )


def anchored_rounded_frame_xml(sid: str, width: float, height: float, *,
                               fill: str = "Swatch/None",
                               stroke: str | None = None,
                               stroke_weight: float = 1.0,
                               radius: float = 7.0,
                               inset: tuple[float, float, float, float] = (1, 7, 1, 7),
                               valign: str = "CenterAlign",
                               auto_height: bool = False,
                               bottom_only: bool = False,
                               anchor_x_offset: float = 0.0) -> str:
    """An inline anchored text frame with a rounded filled path.

    Paragraph shading and table cells cannot round their corners; every
    rounded in-flow object (H1 capsule, notice panel, label chip) is this
    frame anchored in a host paragraph. InlinePosition must be the child
    AnchoredObjectSetting element — as a TextFrame attribute InDesign
    silently drops it, and with it the ParentStory binding.
    """
    geometry = (bottom_rounded_path_geometry(0.0, -height, width, 0.0, radius)
                if bottom_only
                else rounded_path_geometry(0.0, -height, width, 0.0, radius))
    insets = "".join(f'<ListItem type="unit">{v:g}</ListItem>' for v in inset)
    stroke_attr = (f'StrokeColor="{stroke}" StrokeWeight="{stroke_weight:g}"'
                   if stroke else 'StrokeColor="Swatch/None" StrokeWeight="0"')
    # AutoSizingType is honored on IDML import (verified live): the frame
    # hugs its content, so `height` is only the flow estimate. Keep the
    # TOP reference point — BottomCenterPoint invalidates the anchored
    # frame on import (Object-is-invalid). Estimate generously: an
    # under-estimate grows the frame down over the following lines.
    auto_attr = (' AutoSizingType="HeightOnly" '
                 'AutoSizingReferencePoint="TopCenterPoint"'
                 if auto_height else '')
    return (
        f'<TextFrame Self="tfp_{sid}" ParentStory="{sid}" '
        'PreviousTextFrame="n" NextTextFrame="n" ContentType="TextType" '
        'AppliedObjectStyle="ObjectStyle/HB Capsule Heading" '
        f'FillColor="{fill}" {stroke_attr} '
        'ItemTransform="1 0 0 1 0 0">\n'
        + geometry +
        '    <TextFramePreference TextColumnCount="1" '
        f'VerticalJustification="{valign}"{auto_attr}>'
        f'<Properties><InsetSpacing type="list">{insets}'
        '</InsetSpacing></Properties></TextFramePreference>\n'
        '    <AnchoredObjectSetting AnchoredPosition="InlinePosition" '
        'SpineRelative="false" LockPosition="false" PinPosition="true" '
        'AnchorPoint="BottomRightAnchor" HorizontalAlignment="LeftAlign" '
        'HorizontalReferencePoint="TextFrame" VerticalAlignment="TopAlign" '
        'VerticalReferencePoint="LineBaseline" '
        f'AnchorXoffset="{anchor_x_offset:g}" '
        'AnchorYoffset="0" AnchorSpaceAbove="0"/>\n'
        '  </TextFrame>'
    )


def h1_pill_paragraph(writer, text: str, width: float,
                      height: float | None = None) -> str:
    """The master's H1 bar inside a flowed story: sharp top corners,
    rounded bottom corners (\\HBTitleLevelOne / capsule_xml bottom_only —
    see STYLE_MAP.md). One definition serving every flowed page, like
    the LaTeX H1 macro.
    """
    # st_anchor_ prefix: package.designmap_xml declares these after their
    # host stories, which is what makes InDesign bind ParentStory at all.
    if height is None:
        height = h1_bar_h_pt(writer)
    # fit-to-width: long localized titles (FR/ES) must not overset the
    # single-line bar — shrink the point size until the estimated run
    # fits the measure, floor 7pt (the LaTeX box wraps instead; a capped
    # shrink keeps the IDML bar single-line like the master).
    from .params import param_pt
    size = param_pt(writer.params, "type_h1_font_size", 9.0)
    avail = width - 11.0  # left/right insets
    est_w = len(text) * size * 0.62
    point_size = None
    if est_w > avail and len(text) > 0:
        point_size = max(7.0, avail / (len(text) * 0.62))
    sid = f"st_anchor_h1pill_{len(writer.stories)}"
    title_xml = heading_text(writer, text, level=1, point_size=point_size)
    title_xml = title_xml.replace(
        'BaselineShift="-1.5"',
        'BaselineShift="0.5"',
        1,
    )
    title_xml = title_xml.replace(
        "<ParagraphStyleRange ",
        '<ParagraphStyleRange LeftIndent="4.74" ',
        1,
    )
    writer._add_story_parts(
        sid, text, [title_xml])
    from .style_names import paragraph_style_ref as _psr_ref
    figure_style = _psr_ref("HB Figure")
    return (
        f'  <ParagraphStyleRange AppliedParagraphStyle="{figure_style}">'
        '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
        + anchored_rounded_frame_xml(sid, width, height,
                                     fill="Color/HB Brand Dark",
                                     bottom_only=True, radius=h1_arc_pt(writer),
                                     inset=(1.5, 1.0, 1, 1.0))
        + '<Content></Content><Br/></CharacterStyleRange>'
        '</ParagraphStyleRange>\n'
    )


def anchored_panel_paragraph(add_story, sid: str, title: str,
                             parts: list[str], width: float, height: float, *,
                             terminal: bool = False, **frame_kwargs) -> str:
    """A host paragraph carrying one rounded panel (sub-story + frame).

    The shared shape behind notice bars, operation panels and data-table
    outlines: content goes into an anchored sub-story, the rounded frame
    is inlined in an HB Figure paragraph.
    """
    story_sid = add_story(sid, title, parts)
    frame = anchored_rounded_frame_xml(story_sid, width, height, **frame_kwargs)
    from .style_names import paragraph_style_ref as _psr_ref
    style_ref = _psr_ref("HB Figure")
    return (
        f'  <ParagraphStyleRange AppliedParagraphStyle="{style_ref}">'
        '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
        + frame + '<Content></Content>'
        + ('' if terminal else '<Br/>')
        + '</CharacterStyleRange></ParagraphStyleRange>\n'
    )


def anchored_panel_group_paragraph(add_story, sid: str, title: str,
                                    parts: list[str], width: float, height: float, *,
                                    terminal: bool = False,
                                    fill: str = "Color/Paper",
                                    stroke: str = "Color/HB Line K40",
                                    stroke_weight: float = 0.75,
                                    radius: float = 6.8,
                                    content_inset: float = 0.0,
                                    corner_fills: dict[str, str] | None = None,
                                    group_underlay: str = "",
                                    group_overlay: str = "",
                                    group_x_offset: float = 0.0,
                                    content_bottom_bleed: float = 0.0) -> str:
    """Rounded background plus square content frame in one anchored group.

    A table directly inside a rounded text-frame is inset by InDesign at
    the curved top corners.  Separating the rounded rectangle from the
    square text-frame preserves the exact table measure while keeping the
    whole object editable and movable as one inline group.  Composite panels
    may additionally place native shapes or linked art below the content frame
    and independent editable text frames above the rounded outline.
    """
    from .primitives import path_geometry
    from .style_names import paragraph_style_ref as _psr_ref

    story_sid = add_story(sid, title, parts)
    anchor = (
        '    <AnchoredObjectSetting AnchoredPosition="InlinePosition" '
        'SpineRelative="false" LockPosition="false" PinPosition="true" '
        'AnchorPoint="BottomRightAnchor" HorizontalAlignment="LeftAlign" '
        'HorizontalReferencePoint="TextFrame" VerticalAlignment="TopAlign" '
        'VerticalReferencePoint="LineBaseline" AnchorXoffset="0" '
        'AnchorYoffset="0" AnchorSpaceAbove="0"/>\n'
    )
    path_x1 = -0.37
    path_x2 = width - 0.37
    path_y1 = -height
    path_y2 = 0.0
    background = (
        f'  <Rectangle Self="bg_group_{sid}" ContentType="Unassigned" '
        f'AppliedObjectStyle="{ROUNDED_TABLE_OBJECT_STYLE}" FillColor="{fill}" '
        'StrokeColor="Swatch/None" StrokeWeight="0" '
        'ItemTransform="1 0 0 1 0 0">\n'
        + rounded_path_geometry(path_x1, path_y1, path_x2, path_y2, radius)
        + anchor
        + '  </Rectangle>\n'
    )
    frame = (
        f'  <TextFrame Self="tf_group_{sid}" ParentStory="{story_sid}" '
        'PreviousTextFrame="n" NextTextFrame="n" ContentType="TextType" '
        'AppliedObjectStyle="ObjectStyle/$ID/[Normal Text Frame]" '
        'FillColor="Swatch/None" StrokeColor="Swatch/None" StrokeWeight="0" '
        'ItemTransform="1 0 0 1 0 0">\n'
        + path_geometry(
            content_inset, -height + content_inset,
            width - content_inset,
            -content_inset + max(0.0, content_bottom_bleed),
        )
        + '    <TextFramePreference TextColumnCount="1" '
        'VerticalJustification="TopAlign" AutoSizingType="Off">'
        '<Properties><InsetSpacing type="list">'
        + ''.join('<ListItem type="unit">0</ListItem>' for _ in range(4))
        + '</InsetSpacing></Properties></TextFramePreference>\n'
        + anchor
        + '  </TextFrame>\n'
    )
    corner_fills = corner_fills or {}
    masks = "".join(
        (
            f'  <Rectangle Self="mask_{corner}_group_{sid}" '
            'ContentType="Unassigned" '
            'AppliedObjectStyle="ObjectStyle/$ID/[None]" '
            f'FillColor="{corner_fills.get(corner, fill)}" '
            'StrokeColor="Swatch/None" StrokeWeight="0" '
            'ItemTransform="1 0 0 1 0 0">\n'
            + rounded_corner_mask_geometry(
                path_x1, path_y1, path_x2, path_y2, radius, corner)
            + anchor
            + '  </Rectangle>\n'
        )
        for corner in (
            "top_left", "top_right", "bottom_left", "bottom_right")
    )
    outline = (
        f'  <Rectangle Self="outline_group_{sid}" ContentType="Unassigned" '
        f'AppliedObjectStyle="{ROUNDED_TABLE_OBJECT_STYLE}" '
        f'FillColor="Swatch/None" StrokeColor="{stroke}" '
        f'StrokeWeight="{stroke_weight:g}" ItemTransform="1 0 0 1 0 0">\n'
        + rounded_path_geometry(path_x1, path_y1, path_x2, path_y2, radius)
        + anchor
        + '  </Rectangle>\n'
    )
    group = (
        f'<Group Self="grp_{sid}" AppliedObjectStyle="ObjectStyle/$ID/[None]" '
        f'ItemTransform="1 0 0 1 {-0.37 + group_x_offset:g} 0">\n'
        + background + group_underlay + frame + masks + outline
        + group_overlay + '</Group>'
    )
    style_ref = _psr_ref("HB Figure")
    return (
        f'  <ParagraphStyleRange AppliedParagraphStyle="{style_ref}">'
        '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
        + group + '<Content></Content>'
        + ('' if terminal else '<Br/>')
        + '</CharacterStyleRange></ParagraphStyleRange>\n'
    )


def vertical_spacer_paragraph(rect_id: str, height: float) -> str:
    """Invisible inline rectangle that contributes an exact flow height."""
    from .primitives import path_geometry
    from .style_names import paragraph_style_ref as _psr_ref

    style_ref = _psr_ref("HB Figure")
    rectangle = (
        f'<Rectangle Self="{rect_id}" ContentType="Unassigned" '
        'AppliedObjectStyle="ObjectStyle/$ID/[None]" '
        'FillColor="Swatch/None" StrokeColor="Swatch/None" StrokeWeight="0" '
        'ItemTransform="1 0 0 1 0 0">\n'
        + path_geometry(0.0, -height, 1.0, 0.0)
        + '    <AnchoredObjectSetting AnchoredPosition="InlinePosition" '
        'SpineRelative="false" LockPosition="false" PinPosition="true" '
        'AnchorPoint="BottomRightAnchor" HorizontalAlignment="LeftAlign" '
        'HorizontalReferencePoint="TextFrame" VerticalAlignment="TopAlign" '
        'VerticalReferencePoint="LineBaseline" AnchorXoffset="0" '
        'AnchorYoffset="0" AnchorSpaceAbove="0"/>\n'
        '  </Rectangle>'
    )
    return (
        f'  <ParagraphStyleRange AppliedParagraphStyle="{style_ref}">'
        '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
        + rectangle
        + '<Content></Content><Br/></CharacterStyleRange>'
        '</ParagraphStyleRange>\n'
    )


def anchored_spacer_paragraph(add_story, sid: str, height: float) -> str:
    """Invisible anchored text-frame used when a real flow gap is required."""
    from .style_names import paragraph_style_ref as _psr_ref

    empty_style = _psr_ref("HB Body")
    empty = (
        f'  <ParagraphStyleRange AppliedParagraphStyle="{empty_style}">'
        '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
        '<Content></Content></CharacterStyleRange></ParagraphStyleRange>\n'
    )
    return anchored_panel_paragraph(
        add_story,
        sid,
        "vertical spacer",
        [empty],
        1.0,
        height,
        fill="Swatch/None",
        stroke="Swatch/None",
        stroke_weight=0,
        radius=0,
        inset=(0, 0, 0, 0),
        valign="TopAlign",
        auto_height=False,
    )
