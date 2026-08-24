"""Font-independent native vector markers for editable IDML prose."""
from __future__ import annotations

from ..page_objects import rounded_path_geometry
from ..params import param_pt
from ..primitives import path_geometry

MARKER_TOKEN = "\ue100"
MARKER_GAP_TOKEN = "\ue101"
DIRECT_CURRENT_TOKEN = "\ue102"
_SUBSCRIPT_DIGITS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")


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


def _direct_current_symbol(marker_id: str) -> str:
    width = 7.0
    paths = [
        _line_path(((0.0, -3.8), (width, -3.8))),
        _line_path(((0.0, -1.0), (2.0, -1.0))),
        _line_path(((3.0, -1.0), (5.0, -1.0))),
        _line_path(((6.0, -1.0), (width, -1.0))),
    ]
    return (
        f'<GraphicLine Self="{marker_id}" ContentType="Unassigned" '
        'AppliedObjectStyle="ObjectStyle/$ID/[None]" '
        'FillColor="Swatch/None" StrokeColor="Color/HB Brand Dark" '
        'StrokeWeight="0.65" EndCap="ButtEndCap" '
        'ItemTransform="1 0 0 1 0 0">'
        '<Properties><PathGeometry>'
        + "".join(paths)
        + '</PathGeometry></Properties>'
        + _anchor()
        + '</GraphicLine>'
    )


def portable_symbol_text(
    text: str,
    *,
    marker_id: str,
) -> tuple[str, dict[str, str]]:
    """Replace Windows-only symbol glyphs with native/typographic equivalents."""
    output: list[str] = []
    for character in text:
        if character == "⎓":
            output.append(DIRECT_CURRENT_TOKEN)
        elif character in "₀₁₂₃₄₅₆₇₈₉":
            output.append(f":sub:`{character.translate(_SUBSCRIPT_DIGITS)}`")
        else:
            output.append(character)
    replacements = (
        {
            DIRECT_CURRENT_TOKEN: _direct_current_symbol(
                f"{marker_id}_direct_current"
            )
        }
        if DIRECT_CURRENT_TOKEN in output
        else {}
    )
    return "".join(output), replacements


__all__ = (
    "MARKER_GAP_TOKEN",
    "MARKER_TOKEN",
    "DIRECT_CURRENT_TOKEN",
    "marked_text",
    "marker_replacements",
    "portable_symbol_text",
)
