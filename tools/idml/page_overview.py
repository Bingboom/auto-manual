"""Editable product-overview page composed from governed line art and labels.

The approved master uses one body-width artwork slot for each product view.
Localized labels and values sit around that art as native InDesign text, so
the production package never needs the LaTeX-only full-page overview PDF.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any, Mapping

from tools.component_specs.overview import overview_spec_from_blocks
from tools.component_specs.overview_adapters import idml_overview_projection
from tools.component_specs.overview_instance import resolve_overview_instance

from .character_metrics import with_character_metrics
from .page_objects import (
    frame_with_background,
    h1_frame_opts,
    heading_text,
)
from .page_overview_single_art import _graphic_frame, single_image_overview_frames
from .params import IDPKG, param_pt

Block = tuple[str, object]

_LABEL = re.compile(r"^\*\*(.+?)\*\*\s*(.*)$", re.S)
_VEHICLE_LINE_START = re.compile(
    r"\s+(?=(?:Car|Coche|Vehículo|Véhicule|Voiture|Auto|Veículo)\s*:)",
    re.IGNORECASE,
)
_VALUE_VOLTAGE_SPACE = re.compile(r"(?<=\d) (?=V\b)")
_EMPTY_CELL_MARKER_SUFFIX = re.compile(r"\s+-\s*$")


def _rows(value: object) -> list[list[str]]:
    if isinstance(value, list):
        rows = value
    elif isinstance(value, str):
        try:
            rows = ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return []
    else:
        return []
    if not isinstance(rows, list):
        return []
    return [
        [str(cell) for cell in row]
        for row in rows
        if isinstance(row, (list, tuple))
    ]


def _label_value(value: str) -> tuple[str, str]:
    match = _LABEL.match(value.strip())
    if not match:
        return value.strip(), ""
    return match.group(1).strip(), match.group(2).strip()


def _break_vehicle_spec(value: str) -> str:
    """Keep the vehicle-input specification on its own visual line."""
    return _VEHICLE_LINE_START.sub("\n", value)


def _keep_voltage_pair(value: str) -> str:
    """Prevent a voltage number and its ``V`` unit from splitting apart."""
    return _VALUE_VOLTAGE_SPACE.sub("\u00a0", value)


def _strip_empty_cell_marker(value: str) -> str:
    """Drop the RST empty-cell marker leaked by the legacy table parser."""
    return _EMPTY_CELL_MARKER_SUFFIX.sub("", value)


def _typed_paragraph(writer, text: str, *, size: float, leading: float,
                     bold: bool, align: str, terminal: bool) -> str:
    source = f"**{text}**" if bold else text
    xml = writer._psr("HB Body", source, terminal=terminal)
    xml = xml.replace(
        "<ParagraphStyleRange ",
        f'<ParagraphStyleRange Justification="{align}" Hyphenation="false" ',
        1,
    )
    def apply_regular_style(match: re.Match[str]) -> str:
        tag = match.group(0)
        if bold or " FontStyle=" in tag:
            return tag
        return tag[:-1] + ' FontStyle="Regular">'

    xml = re.sub(
        r"<CharacterStyleRange\b[^>]*>",
        apply_regular_style,
        xml,
    )
    return with_character_metrics(xml, point_size=size, leading=leading)


def _label_story(writer, sid: str, label: str, value: str, *,
                 align: str) -> str:
    value = _keep_voltage_pair(value)
    label_size = param_pt(
        writer.params,
        "idml_overview_callout_label_font_size",
        7.0,
    )
    label_leading = param_pt(
        writer.params,
        "idml_overview_callout_label_font_leading",
        7.9,
    )
    label_bold = param_pt(
        writer.params,
        "idml_overview_callout_label_bold",
        1.0,
    ) >= 0.5
    parts = [
        _typed_paragraph(
            writer,
            label,
            size=label_size,
            leading=label_leading,
            bold=label_bold,
            align=align, terminal=not value,
        )
    ]
    if value:
        parts.append(_typed_paragraph(
            writer, value, size=5.0, leading=6.2, bold=False,
            align=align, terminal=True,
        ))
    return writer._add_story_parts(sid, f"Product overview: {label}", parts)


def _leader_path(
    writer,
    rid: str,
    points: tuple[tuple[float, float], ...],
    *,
    color: str,
    weight: float,
) -> str:
    """One native open path in top-left page coordinates."""
    anchors = "".join(
        (
            f'<PathPointType Anchor="{x - writer.page_w / 2:g} '
            f'{y - writer.page_h / 2:g}" '
            f'LeftDirection="{x - writer.page_w / 2:g} '
            f'{y - writer.page_h / 2:g}" '
            f'RightDirection="{x - writer.page_w / 2:g} '
            f'{y - writer.page_h / 2:g}"/>'
        )
        for x, y in points
    )
    return (
        f'  <GraphicLine Self="{rid}" ContentType="Unassigned" '
        'AppliedObjectStyle="ObjectStyle/$ID/[None]" '
        f'FillColor="Swatch/None" StrokeColor="{color}" '
        f'StrokeWeight="{weight:g}" ItemTransform="1 0 0 1 0 0">'
        '<Properties><PathGeometry><GeometryPathType PathOpen="true">'
        f'<PathPointArray>{anchors}</PathPointArray>'
        '</GeometryPathType></PathGeometry></Properties>'
        '</GraphicLine>\n'
    )


def _section_heading(
    writer,
    sid: str,
    text: str,
    *,
    text_y: float,
    bullet_rect: tuple[float, float, float, float],
    text_rect: tuple[float, float, float, float] | None = None,
) -> tuple[str, list[str]]:
    from .page_objects import page_rectangle_xml

    story = writer._add_story_parts(
        f"{sid}_story", text,
        [_typed_paragraph(
            writer, text, size=8.0, leading=9.0, bold=True,
            align="LeftAlign", terminal=True,
        )],
    )
    bullet = page_rectangle_xml(
        writer, f"{sid}_bullet", bullet_rect,
        fill="Color/HB Brand Dark",
        stroke_color="Swatch/None",
        stroke_weight=0,
        corner_radius=bullet_rect[2] / 2.0,
    )
    frame = frame_with_background(
        writer, sid, "heading", story,
        text_rect or (42.0, text_y, writer.page_w - 70.0, 12.0),
        {"inset": (0, 0, 0, 0)},
    )
    return story, [bullet, frame]


def _front_cells(blocks: list[Block]) -> list[tuple[str, str]]:
    tables = [_rows(value) for kind, value in blocks if kind == "table"]
    primary = tables[0] if tables else []
    total = tables[1] if len(tables) > 1 else []
    at = lambda row, col: (  # noqa: E731 - compact structural lookup
        _label_value(_strip_empty_cell_marker(primary[row][col]))
        if row < len(primary) and col < len(primary[row]) and primary[row][col]
        else ("", "")
    )
    # Every locale keeps the six left-side controls in the same source-row
    # order, while the five right-side controls may leave a different blank
    # cell (FR puts AC Output on row 5 instead of row 4).  Select the right
    # side by non-empty source order instead of assuming the EN blank cell.
    left = [at(row, 0) for row in (0, 1, 3, 4, 5, 2)]
    right = [
        at(row, 1)
        for row in range(len(primary))
        if len(primary[row]) > 1 and primary[row][1]
    ]
    right.extend([("", "")] * max(0, 5 - len(right)))
    result: list[tuple[str, str]] = []
    for index in range(5):
        result.extend((left[index], right[index]))
    result.append(left[5])
    if total and total[0]:
        result.append(_label_value(total[0][0]))
    else:
        result.append(("", ""))
    return result


def _right_cells(blocks: list[Block]) -> list[tuple[str, str]]:
    table = next((_rows(value) for kind, value in blocks if kind == "table"), [])
    cells = [
        _label_value(cell)
        for row in table
        for cell in row
        if cell
    ]
    if not cells:
        return [("", ""), ("", ""), ("", "")]
    # EN, FR and ES serialize the right-side rows differently, but their
    # semantic source order is invariant: Handle, AC Input, DC Input.  The
    # visual page places DC on the lower left and AC on the lower right.
    cells.extend([("", "")] * max(0, 3 - len(cells)))
    handle, dc_input, ac_input = cells[0], cells[2], cells[1]
    dc_input = (dc_input[0], _break_vehicle_spec(dc_input[1]))
    return [handle, dc_input, ac_input]


# Compatibility views of the default target instance. Production composition
# resolves the writer's model/region below; these aliases preserve the focused
# geometry-test surface until PR 9 removes the old constants.
_DEFAULT_INSTANCE = resolve_overview_instance(model=None, region=None)
_DEFAULT_VIEWS = {
    str(view["id"]): view for view in _DEFAULT_INSTANCE["views"]
}
_FRONT_ROLES = tuple(
    str(callout["id"]) for callout in _DEFAULT_VIEWS["front"]["callouts"]
)
_RIGHT_ROLES = tuple(
    str(callout["id"]) for callout in _DEFAULT_VIEWS["right"]["callouts"]
)
_FRONT_RECTS = tuple(
    (
        *(float(value) for value in callout["idml"]["rect"]),
        str(callout["idml"]["align"]),
    )
    for callout in _DEFAULT_VIEWS["front"]["callouts"]
)
_RIGHT_RECTS = tuple(
    (
        *(float(value) for value in callout["idml"]["rect"]),
        str(callout["idml"]["align"]),
    )
    for callout in _DEFAULT_VIEWS["right"]["callouts"]
)
_DEFAULT_IDML_PROJECTION = {
    f"{view['id']}.{callout['id']}": callout["idml"]
    for view in _DEFAULT_INSTANCE["views"]
    for callout in view["callouts"]
}
_DEFAULT_DECORATIVE = {
    f"decorative.{leader['id']}": leader
    for leader in _DEFAULT_INSTANCE["idml_decorative_leaders"]
}
_DEFAULT_LEADER_LOOKUP = {**_DEFAULT_IDML_PROJECTION, **_DEFAULT_DECORATIVE}
_LEADER_PATHS = tuple(
    (
        str(_DEFAULT_LEADER_LOOKUP[key].get("id") or key.rsplit(".", 1)[-1]),
        tuple(
            (float(point[0]), float(point[1]))
            for point in (
                _DEFAULT_LEADER_LOOKUP[key].get("leader")
                or _DEFAULT_LEADER_LOOKUP[key]["points"]
            )
        ),
    )
    for key in _DEFAULT_INSTANCE["idml_leader_order"]
)
_LEADER_STROKE_WEIGHTS = {
    str(leader["id"]): float(leader["stroke_weight"])
    for leader in _DEFAULT_INSTANCE["idml_decorative_leaders"]
    if float(leader["stroke_weight"]) != 0.3
}
_LABELS_ABOVE_LEADER = frozenset(
    str(callout["id"])
    for view in _DEFAULT_INSTANCE["views"]
    for callout in view["callouts"]
    if callout["idml"].get("anchor") == "above-leader"
)
_LEADER_Y_BY_ROLE = {
    role: points[0][1]
    for role, points in _LEADER_PATHS
    if role in _LABELS_ABOVE_LEADER
}


def _label_frames(writer, sid: str,
                  cells: list[tuple[str, str]],
                  rects: tuple[tuple[float, float, float, float, str], ...],
                  roles: tuple[str, ...],
                  *,
                  leader_gap: float,
                  leader_y_by_role: Mapping[str, float] | None = None) -> list[str]:
    anchored_leaders = leader_y_by_role or _LEADER_Y_BY_ROLE
    frames: list[str] = []
    for index, ((label, value), (x, y, width, height, align), role) in enumerate(
        zip(cells, rects, roles, strict=True)
    ):
        if not label:
            continue
        opts: dict[str, object] = {"inset": (0, 0, 0, 0)}
        if role in anchored_leaders:
            # Encode the gap in native frame geometry.  InDesign discards the
            # compact InsetSpacing attribute on these absolute text frames,
            # while a frame bottom above the leader survives IDML import.
            y = anchored_leaders[role] - leader_gap - height
            opts = {
                "inset": (0, 0, 0, 0),
                "valign": "BottomAlign",
            }
        story_id = _label_story(
            writer, f"{sid}_label_{index + 1}", label, value, align=align)
        frames.append(frame_with_background(
            writer, sid, f"label_{index + 1}", story_id,
            (x, y, width, height), opts,
        ))
    return frames


def product_overview_frames(
    writer,
    sid: str,
    blocks: list[Block],
    bundle_root: Path,
) -> list[str]:
    """Build the shared Overview component frames without owning a page."""
    h1 = next((str(value) for kind, value in blocks if kind == "h1"), "")
    h2s = [str(value) for kind, value in blocks if kind == "h2"]
    image_refs = [str(value) for kind, value in blocks if kind == "image"]
    if h1 and not h2s and len(image_refs) == 1:
        return single_image_overview_frames(
            writer,
            sid,
            blocks,
            bundle_root,
        )
    if not h1 or len(h2s) != 2 or len(image_refs) != 2:
        raise ValueError("product overview requires one h1, two h2s, and two images")
    assets = [writer._resolve_bundle_image(bundle_root, ref) for ref in image_refs]
    if any(asset is None for asset in assets):
        raise ValueError("product overview contains an unresolved governed image")

    instance = resolve_overview_instance(model=writer.model, region=writer.region)
    try:
        spec = overview_spec_from_blocks(
            blocks,
            instance=instance,
            source_ref=sid,
            language=str(writer.language or "und"),
        )
        projection = idml_overview_projection(spec, instance)
    except Exception as exc:
        raise ValueError(f"invalid product overview semantics: {exc}") from exc
    views = {str(view["id"]): view for view in projection["views"]}
    front_view = views["front"]
    right_view = views["right"]
    h1 = str(projection["accessibility_label"])
    h2s = [str(front_view["title"]), str(right_view["title"])]
    image_refs = [str(front_view["image_ref"]), str(right_view["image_ref"])]

    page_geometry = projection["page"]

    def rect(values: object) -> tuple[float, float, float, float]:
        if not isinstance(values, list) or len(values) != 4:
            raise ValueError("product overview geometry rectangle must have four values")
        return tuple(float(value) for value in values)  # type: ignore[return-value]

    def cells(view: Mapping[str, Any]) -> list[tuple[str, str]]:
        result: list[tuple[str, str]] = []
        for callout in view["callouts"]:
            value = "\n".join(str(item) for item in callout.get("body", []))
            if callout["id"] == "dc_input":
                value = _break_vehicle_spec(value)
            result.append((str(callout["label"]), value))
        return result

    title_sid = writer._add_story_parts(
        f"{sid}_title", h1, [heading_text(writer, h1, level=1)])
    _, front_heading = _section_heading(
        writer,
        f"{sid}_front",
        h2s[0],
        text_y=float(front_view["heading_text_y"]),
        bullet_rect=rect(front_view["heading_bullet_rect"]),
        text_rect=(
            rect(front_view["heading_text_rect"])
            if "heading_text_rect" in front_view
            else None
        ),
    )
    _, right_heading = _section_heading(
        writer,
        f"{sid}_right",
        h2s[1],
        text_y=float(right_view["heading_text_y"]),
        bullet_rect=rect(right_view["heading_bullet_rect"]),
        text_rect=(
            rect(right_view["heading_text_rect"])
            if "heading_text_rect" in right_view
            else None
        ),
    )

    title_rect = rect(page_geometry["title_frame"])
    artwork_and_headings = [
        _graphic_frame(writer, f"art_{sid}_front", assets[0],
                       rect(front_view["art_rect"])),  # type: ignore[arg-type]
        _graphic_frame(writer, f"art_{sid}_right", assets[1],
                       rect(right_view["art_rect"])),  # type: ignore[arg-type]
        frame_with_background(
            writer, sid, "title", title_sid,
            title_rect,
            h1_frame_opts(title_rect, left_inset=6.4, right_inset=6.4),
        ),
        *front_heading,
        *right_heading,
    ]
    white_leaders = [
        _leader_path(
            writer,
            f"leader_knockout_{sid}_{name}",
            points,
            color="Color/Paper",
            weight=1.82,
        )
        for leader in projection["leaders"]
        for name, points in [
            (
                str(leader["id"]),
                tuple(
                    (float(point[0]), float(point[1]))
                    for point in leader["points"]
                ),
            )
        ]
    ]
    dark_leaders = [
        _leader_path(
            writer,
            f"leader_{sid}_{name}",
            points,
            color="Color/HB Brand Dark",
            weight=float(leader["stroke_weight"]),
        )
        for leader in projection["leaders"]
        for name, points in [
            (
                str(leader["id"]),
                tuple(
                    (float(point[0]), float(point[1]))
                    for point in leader["points"]
                ),
            )
        ]
    ]
    leader_gap = param_pt(
        writer.params,
        "idml_overview_label_leader_gap",
        1.2,
    )
    front_rects = tuple(
        (*rect(callout["rect"]), str(callout["align"]))
        for callout in front_view["callouts"]
    )
    right_rects = tuple(
        (*rect(callout["rect"]), str(callout["align"]))
        for callout in right_view["callouts"]
    )
    front_roles = tuple(str(callout["id"]) for callout in front_view["callouts"])
    right_roles = tuple(str(callout["id"]) for callout in right_view["callouts"])
    leader_y_by_role = {
        str(callout["id"]): float(callout["leader"][0][1])
        for view in projection["views"]
        for callout in view["callouts"]
        if callout.get("anchor") == "above-leader"
    }
    label_frames = [
        *_label_frames(
            writer,
            f"{sid}_front",
            cells(front_view),
            front_rects,
            front_roles,
            leader_gap=leader_gap,
            leader_y_by_role=leader_y_by_role,
        ),
        *_label_frames(
            writer,
            f"{sid}_right",
            cells(right_view),
            right_rects,
            right_roles,
            leader_gap=leader_gap,
            leader_y_by_role=leader_y_by_role,
        ),
    ]
    # All editable copy is emitted last and therefore opens above artwork and
    # both leader strokes in InDesign's stacking order.
    return artwork_and_headings + white_leaders + dark_leaders + label_frames


def add_product_overview_page(
    writer,
    sid: str,
    blocks: list[Block],
    bundle_root: Path,
    page_index: int,
) -> str:
    """Compose one localized overview page from source-authored semantics."""
    frames = product_overview_frames(writer, sid, blocks, bundle_root)

    spread_id = f"sp_{page_index}"
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Spread xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'<Spread Self="{spread_id}" PageCount="1" BindingLocation="0" '
        'ShowMasterItems="true">\n'
        f'  <Page Self="{spread_id}_pg" Name="{page_index + 1}" '
        'AppliedMaster="n" OverrideList="" TabOrder="" GridStartingPoint="TopOutside" '
        f'GeometricBounds="0 0 {writer.page_h:g} {writer.page_w:g}" '
        f'ItemTransform="1 0 0 1 {-writer.page_w / 2:g} {-writer.page_h / 2:g}">\n'
        '    <MarginPreference ColumnCount="1" ColumnGutter="12" '
        f'Top="{writer.m_t:g}" Bottom="{writer.m_b:g}" '
        f'Left="{writer.m_l:g}" Right="{writer.m_r:g}"/>\n'
        '  </Page>\n'
        + "".join(frames)
        + '</Spread>\n</idPkg:Spread>\n'
    )
    writer.spreads.append((spread_id, xml))
    return spread_id
