"""Spread-level object helpers for composed IDML pages."""
from __future__ import annotations

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
        return {"h1_bar_bg": True, "inset": inset}
    if level == 2:
        return {"capsule_bg": True, "inset": inset}
    return {"inset": inset}


def with_rounded_outer(opts: dict) -> dict:
    return {**opts, "rounded_outer": True}


def capsule_text(writer, text: str, *, point_size: float | None = None) -> str:
    return heading_text(writer, text, level=2, point_size=point_size)


def heading_text(writer, text: str, *, level: int,
                 point_size: float | None = None) -> str:
    if point_size is None and level == 1:
        point_size = 12.4
    xml = writer._psr("HB Capsule Text", text, terminal=True)
    if point_size is None:
        return xml
    return xml.replace(
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
        f'PointSize="{point_size:g}"',
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
        ((x1, y1 + r), (x1, y1 + r), (x1, y1 + r)),
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


def capsule_xml(writer, rect_id: str,
                rect: tuple[float, float, float, float], *,
                bottom_only: bool = False) -> str:
    x1, y1, x2, y2 = writer._page_rect(*rect)
    geometry = (
        bottom_rounded_path_geometry(x1, y1, x2, y2, 7.0)
        if bottom_only else rounded_path_geometry(x1, y1, x2, y2, 7.0)
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
    x1, y1, x2, y2 = writer._page_rect(*rect)
    parts: list[str] = []
    if capsule_bg:
        parts.append(capsule_xml(writer, f"bg_{sid}_{frame_id}", rect))
    if h1_bar_bg:
        parts.append(capsule_xml(
            writer, f"bg_{sid}_{frame_id}", rect, bottom_only=True))
    if rounded_outer:
        parts.append(rounded_outer_xml(writer, f"bg_{sid}_{frame_id}", rect))
    parts.append(writer._frame_xml(
        f"tf_{sid}_{frame_id}", story_id, x1, y1, x2, y2, **opts))
    return "".join(parts)
