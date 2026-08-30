"""Font-independent inline markers for portable IDML stories.

The reference mark (U+203B) must survive an IDML -> INDD save/reopen cycle on
both Windows and macOS.  InDesign can report a document font as installed
during the initial IDML import and still reopen the saved INDD with a missing
glyph.  Keep the approved 5.6 pt Noto outline as editable native IDML paths so
the marker has no host-font dependency at all.
"""
from __future__ import annotations

import re

from ..page_objects import rounded_path_geometry
from ..params import param_pt
from ..primitives import path_geometry


MARKER_TOKEN = "\ue100"
MARKER_GAP_TOKEN = "\ue101"
DIRECT_CURRENT_TOKEN = "\ue102"
_SUBSCRIPT_DIGITS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")


_MARKER_START = "<!--HB_NATIVE_REFERENCE_MARK-->"
_MARKER_END = "<!--/HB_NATIVE_REFERENCE_MARK-->"
_LEFT_ID = "__HB_NATIVE_REFERENCE_MARK_LEFT__"
_GLYPH_ID = "__HB_NATIVE_REFERENCE_MARK_GLYPH__"
_RIGHT_ID = "__HB_NATIVE_REFERENCE_MARK_RIGHT__"

# Noto Sans U+203B at 5.6 pt with the approved 70.8% horizontal scale.  The
# outline is committed as geometry rather than generated at build time so the
# renderer does not gain a fontTools dependency and builds remain byte-stable.
_REFERENCE_MARK_GEOMETRY = (
    '<GeometryPathType PathOpen="false"><PathPointArray>'
    '<PathPointType Anchor="1.44319 -3.3936" LeftDirection="1.51984 -3.3936" RightDirection="1.36918 -3.3936"/>'
    '<PathPointType Anchor="1.28261 -3.4832" LeftDirection="1.31565 -3.42347" RightDirection="1.24957 -3.54293"/>'
    '<PathPointType Anchor="1.23305 -3.7296" LeftDirection="1.23305 -3.62507" RightDirection="1.23305 -3.8304"/>'
    '<PathPointType Anchor="1.28261 -3.9704" LeftDirection="1.24957 -3.91067" RightDirection="1.31565 -4.03013"/>'
    '<PathPointType Anchor="1.44319 -4.06" LeftDirection="1.36918 -4.06" RightDirection="1.51984 -4.06"/>'
    '<PathPointType Anchor="1.60971 -3.9704" LeftDirection="1.57535 -4.03013" RightDirection="1.64407 -3.91067"/>'
    '<PathPointType Anchor="1.66125 -3.7296" LeftDirection="1.66125 -3.8304" RightDirection="1.66125 -3.62507"/>'
    '<PathPointType Anchor="1.60971 -3.4832" LeftDirection="1.64407 -3.54293" RightDirection="1.57535 -3.42347"/>'
    '</PathPointArray></GeometryPathType>'
    '<GeometryPathType PathOpen="false"><PathPointArray>'
    '<PathPointType Anchor="0.241853 0" LeftDirection="0.241853 0" RightDirection="0.241853 0"/>'
    '<PathPointType Anchor="0.059472 -0.2576" LeftDirection="0.059472 -0.2576" RightDirection="0.059472 -0.2576"/>'
    '<PathPointType Anchor="1.2727 -1.9936" LeftDirection="1.2727 -1.9936" RightDirection="1.2727 -1.9936"/>'
    '<PathPointType Anchor="0.0555072 -3.724" LeftDirection="0.0555072 -3.724" RightDirection="0.0555072 -3.724"/>'
    '<PathPointType Anchor="0.237888 -3.9872" LeftDirection="0.237888 -3.9872" RightDirection="0.237888 -3.9872"/>'
    '<PathPointType Anchor="1.45905 -2.2568" LeftDirection="1.45905 -2.2568" RightDirection="1.45905 -2.2568"/>'
    '<PathPointType Anchor="2.68417 -3.9816" LeftDirection="2.68417 -3.9816" RightDirection="2.68417 -3.9816"/>'
    '<PathPointType Anchor="2.86655 -3.724" LeftDirection="2.86655 -3.724" RightDirection="2.86655 -3.724"/>'
    '<PathPointType Anchor="1.64539 -1.9936" LeftDirection="1.64539 -1.9936" RightDirection="1.64539 -1.9936"/>'
    '<PathPointType Anchor="2.85862 -0.252" LeftDirection="2.85862 -0.252" RightDirection="2.85862 -0.252"/>'
    '<PathPointType Anchor="2.67624 0.0056" LeftDirection="2.67624 0.0056" RightDirection="2.67624 0.0056"/>'
    '<PathPointType Anchor="1.45905 -1.7304" LeftDirection="1.45905 -1.7304" RightDirection="1.45905 -1.7304"/>'
    '</PathPointArray></GeometryPathType>'
    '<GeometryPathType PathOpen="false"><PathPointArray>'
    '<PathPointType Anchor="0.214099 -1.652" LeftDirection="0.280179 -1.652" RightDirection="0.150662 -1.652"/>'
    '<PathPointType Anchor="0.059472 -1.7276" LeftDirection="0.09912 -1.6772" RightDirection="0.019824 -1.778"/>'
    '<PathPointType Anchor="0 -1.9768" LeftDirection="0 -1.86107" RightDirection="0 -2.09253"/>'
    '<PathPointType Anchor="0.059472 -2.2288" LeftDirection="0.019824 -2.17653" RightDirection="0.09912 -2.28107"/>'
    '<PathPointType Anchor="0.214099 -2.3072" LeftDirection="0.150662 -2.3072" RightDirection="0.280179 -2.3072"/>'
    '<PathPointType Anchor="0.372691 -2.2288" LeftDirection="0.333043 -2.28107" RightDirection="0.412339 -2.17653"/>'
    '<PathPointType Anchor="0.432163 -1.9768" LeftDirection="0.432163 -2.09253" RightDirection="0.432163 -1.86107"/>'
    '<PathPointType Anchor="0.372691 -1.7276" LeftDirection="0.412339 -1.778" RightDirection="0.333043 -1.6772"/>'
    '</PathPointArray></GeometryPathType>'
    '<GeometryPathType PathOpen="false"><PathPointArray>'
    '<PathPointType Anchor="2.70399 -1.652" LeftDirection="2.77007 -1.652" RightDirection="2.64056 -1.652"/>'
    '<PathPointType Anchor="2.54937 -1.7276" LeftDirection="2.58901 -1.6772" RightDirection="2.50972 -1.778"/>'
    '<PathPointType Anchor="2.48989 -1.9768" LeftDirection="2.48989 -1.86107" RightDirection="2.48989 -2.09253"/>'
    '<PathPointType Anchor="2.54937 -2.2288" LeftDirection="2.50972 -2.17653" RightDirection="2.58901 -2.28107"/>'
    '<PathPointType Anchor="2.70399 -2.3072" LeftDirection="2.64056 -2.3072" RightDirection="2.77007 -2.3072"/>'
    '<PathPointType Anchor="2.86259 -2.2288" LeftDirection="2.82294 -2.28107" RightDirection="2.90223 -2.17653"/>'
    '<PathPointType Anchor="2.92206 -1.9768" LeftDirection="2.92206 -2.09253" RightDirection="2.92206 -1.86107"/>'
    '<PathPointType Anchor="2.86259 -1.7276" LeftDirection="2.90223 -1.778" RightDirection="2.82294 -1.6772"/>'
    '</PathPointArray></GeometryPathType>'
    '<GeometryPathType PathOpen="false"><PathPointArray>'
    '<PathPointType Anchor="1.44319 0.084" LeftDirection="1.51984 0.084" RightDirection="1.36918 0.084"/>'
    '<PathPointType Anchor="1.28261 -0.0056" LeftDirection="1.31565 0.0541333" RightDirection="1.24957 -0.0653333"/>'
    '<PathPointType Anchor="1.23305 -0.252" LeftDirection="1.23305 -0.147467" RightDirection="1.23305 -0.3528"/>'
    '<PathPointType Anchor="1.28261 -0.4928" LeftDirection="1.24957 -0.433067" RightDirection="1.31565 -0.552533"/>'
    '<PathPointType Anchor="1.44319 -0.5824" LeftDirection="1.36918 -0.5824" RightDirection="1.51984 -0.5824"/>'
    '<PathPointType Anchor="1.60971 -0.4928" LeftDirection="1.57535 -0.552533" RightDirection="1.64407 -0.433067"/>'
    '<PathPointType Anchor="1.66125 -0.252" LeftDirection="1.66125 -0.3528" RightDirection="1.66125 -0.147467"/>'
    '<PathPointType Anchor="1.60971 -0.0056" LeftDirection="1.64407 -0.0653333" RightDirection="1.57535 0.0541333"/>'
    '</PathPointArray></GeometryPathType>'
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


def _circle(marker_id: str, diameter: float) -> str:
    return (
        f'<Rectangle Self="{marker_id}" ContentType="Unassigned" '
        'AppliedObjectStyle="ObjectStyle/$ID/[None]" '
        'FillColor="Color/HB Brand Dark" StrokeColor="Swatch/None" '
        'StrokeWeight="0" ItemTransform="1 0 0 1 0 0">\n'
        + rounded_path_geometry(0.0, -diameter, diameter, 0.0, diameter / 2.0)
        + _anchor()
        + '</Rectangle>'
    )


def _gap(marker_id: str, width: float) -> str:
    return (
        f'<Rectangle Self="{marker_id}" ContentType="Unassigned" '
        'AppliedObjectStyle="ObjectStyle/$ID/[None]" '
        'FillColor="Swatch/None" StrokeColor="Swatch/None" '
        'StrokeWeight="0" ItemTransform="1 0 0 1 0 0">\n'
        + path_geometry(0.0, -0.1, width, 0.0)
        + _anchor()
        + '</Rectangle>'
    )


def marker_replacements(writer, *, marker_id: str) -> dict[str, str]:
    """Return inline replacements matching the shared LaTeX H2 geometry."""
    radius = param_pt(writer.params, "comp_title_l2_bullet_radius", 2.126)
    gap = param_pt(writer.params, "comp_title_l2_gap", 3.969)
    return {
        MARKER_TOKEN: _circle(f"{marker_id}_circle", radius * 2.0),
        MARKER_GAP_TOKEN: _gap(f"{marker_id}_gap", gap),
    }


def marked_text(text: str) -> str:
    return f"{MARKER_TOKEN}{MARKER_GAP_TOKEN}{text}"


def _line_path(points: tuple[tuple[float, float], ...]) -> str:
    anchors = "".join(
        (
            f'<PathPointType Anchor="{x:g} {y:g}" '
            f'LeftDirection="{x:g} {y:g}" '
            f'RightDirection="{x:g} {y:g}"/>'
        )
        for x, y in points
    )
    return (
        '<GeometryPathType PathOpen="true"><PathPointArray>'
        f'{anchors}</PathPointArray></GeometryPathType>'
    )


def _direct_current_symbol(marker_id: str, point_size: float) -> str:
    """Reproduce the approved Apple Symbols U+2393 metrics as native paths."""

    if point_size <= 0:
        raise ValueError("direct-current symbol point size must be positive")
    scale = point_size / 2048.0
    advance = 1514.0 * scale
    left_bearing = 128.0 * scale
    drawn_width = 1258.0 * scale
    right_bearing = advance - left_bearing - drawn_width
    top_y = -645.0 * scale
    bottom_y = -354.5 * scale
    stroke_weight = 139.5 * scale
    paths = [
        _line_path(((0.0, top_y), (drawn_width, top_y))),
        _line_path(((0.0, bottom_y), (265.0 * scale, bottom_y))),
        _line_path(((494.0 * scale, bottom_y), (758.0 * scale, bottom_y))),
        _line_path(((990.0 * scale, bottom_y), (1252.0 * scale, bottom_y))),
    ]
    symbol = (
        f'<GraphicLine Self="{marker_id}" ContentType="Unassigned" '
        'AppliedObjectStyle="ObjectStyle/$ID/[None]" '
        'FillColor="Swatch/None" StrokeColor="Color/HB Brand Dark" '
        f'StrokeWeight="{stroke_weight:g}" EndCap="ButtEndCap" '
        'ItemTransform="1 0 0 1 0 0">'
        '<Properties><PathGeometry>'
        + "".join(paths)
        + '</PathGeometry></Properties>'
        + _anchor()
        + '</GraphicLine>'
    )
    return (
        _gap(f"{marker_id}_left_bearing", left_bearing)
        + symbol
        + _gap(f"{marker_id}_right_bearing", right_bearing)
    )


def portable_symbol_text(
    text: str,
    *,
    marker_id: str,
    point_size: float = 6.0,
) -> tuple[str, dict[str, str]]:
    """Replace host-only glyphs with portable typographic equivalents."""
    output: list[str] = []
    for character in text:
        if character == "⎓":
            output.append(character)
        elif character in "₀₁₂₃₄₅₆₇₈₉":
            output.append(f":sub:`{character.translate(_SUBSCRIPT_DIGITS)}`")
        else:
            output.append(character)
    replacements = (
        {
            DIRECT_CURRENT_TOKEN: _direct_current_symbol(
                f"{marker_id}_direct_current",
                point_size,
            )
        }
        if DIRECT_CURRENT_TOKEN in output
        else {}
    )
    return "".join(output), replacements


def _anchored_object_setting() -> str:
    return (
        '<AnchoredObjectSetting AnchoredPosition="InlinePosition" '
        'SpineRelative="false" LockPosition="false" PinPosition="true" '
        'AnchorPoint="BottomRightAnchor" HorizontalAlignment="LeftAlign" '
        'HorizontalReferencePoint="TextFrame" VerticalAlignment="TopAlign" '
        'VerticalReferencePoint="LineBaseline" AnchorXoffset="0" '
        'AnchorYoffset="0" AnchorSpaceAbove="0"/>'
    )


def _bearing_rectangle(item_id: str) -> str:
    width = 0.19824
    points = (
        '<PathPointType Anchor="0 -0.1" LeftDirection="0 -0.1" RightDirection="0 -0.1"/>'
        '<PathPointType Anchor="0 0" LeftDirection="0 0" RightDirection="0 0"/>'
        f'<PathPointType Anchor="{width:g} 0" LeftDirection="{width:g} 0" RightDirection="{width:g} 0"/>'
        f'<PathPointType Anchor="{width:g} -0.1" LeftDirection="{width:g} -0.1" RightDirection="{width:g} -0.1"/>'
    )
    return (
        f'<Rectangle Self="{item_id}" ContentType="Unassigned" '
        'AppliedObjectStyle="ObjectStyle/$ID/[None]" FillColor="Swatch/None" '
        'StrokeColor="Swatch/None" StrokeWeight="0" '
        'ItemTransform="1 0 0 1 0 0"><Properties><PathGeometry>'
        '<GeometryPathType PathOpen="false"><PathPointArray>'
        + points
        + '</PathPointArray></GeometryPathType></PathGeometry></Properties>'
        + _anchored_object_setting()
        + '</Rectangle>'
    )


def reference_mark_xml() -> str:
    """Return one unresolved native U+203B inline component.

    Story identity is not known at paragraph-render time.  Package assembly
    binds the three placeholder ``Self`` values to deterministic story-local
    IDs before the XML is written into the IDML archive.
    """
    glyph = (
        f'<Polygon Self="{_GLYPH_ID}" ContentType="Unassigned" '
        'AppliedObjectStyle="ObjectStyle/$ID/[None]" '
        'FillColor="Color/HB Brand Dark" StrokeColor="Swatch/None" '
        'StrokeWeight="0" ItemTransform="1 0 0 1 0 0">'
        '<Properties><PathGeometry>'
        + _REFERENCE_MARK_GEOMETRY
        + '</PathGeometry></Properties>'
        + _anchored_object_setting()
        + '</Polygon>'
    )
    return (
        _MARKER_START
        + _bearing_rectangle(_LEFT_ID)
        + glyph
        + _bearing_rectangle(_RIGHT_ID)
        + _MARKER_END
    )


_MARKER_PATTERN = re.compile(
    re.escape(_MARKER_START) + r"(.*?)" + re.escape(_MARKER_END),
    re.DOTALL,
)


def bind_reference_mark_ids(story_id: str, story_xml: str) -> str:
    """Bind every native marker to deterministic, document-unique IDs."""
    safe_story_id = re.sub(r"[^A-Za-z0-9_]+", "_", story_id).strip("_") or "story"
    count = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal count
        prefix = f"hb_refmark_{safe_story_id}_{count}"
        count += 1
        marker = match.group(1)
        marker = marker.replace(_LEFT_ID, prefix + "_left")
        marker = marker.replace(_GLYPH_ID, prefix + "_glyph")
        marker = marker.replace(_RIGHT_ID, prefix + "_right")
        return marker

    bound = _MARKER_PATTERN.sub(replace, story_xml)
    unresolved = (_LEFT_ID, _GLYPH_ID, _RIGHT_ID, _MARKER_START, _MARKER_END)
    if any(token in bound for token in unresolved):
        raise ValueError(f"unresolved native reference marker in story {story_id}")
    return bound


__all__ = (
    "MARKER_GAP_TOKEN",
    "MARKER_TOKEN",
    "DIRECT_CURRENT_TOKEN",
    "bind_reference_mark_ids",
    "marked_text",
    "marker_replacements",
    "portable_symbol_text",
    "reference_mark_xml",
)
