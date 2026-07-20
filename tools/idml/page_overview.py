"""Editable product-overview page composed from governed line art and labels.

The approved master uses one body-width artwork slot for each product view.
Localized labels and values sit around that art as native InDesign text, so
the production package never needs the LaTeX-only full-page overview PDF.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path
from xml.sax.saxutils import escape

from .character_metrics import with_character_metrics
from .page_objects import frame_with_background, heading_bar_opts, heading_text
from .params import IDPKG

_ATTR = {'"': "&quot;"}
Block = tuple[str, object]

_LABEL = re.compile(r"^\*\*(.+?)\*\*\s*(.*)$", re.S)


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
    parts = [
        _typed_paragraph(
            writer, label, size=7.0, leading=7.9, bold=True,
            align=align, terminal=not value,
        )
    ]
    if value:
        parts.append(_typed_paragraph(
            writer, value, size=5.0, leading=6.2, bold=False,
            align=align, terminal=True,
        ))
    return writer._add_story_parts(sid, f"Product overview: {label}", parts)


def _graphic_frame(writer, rect_id: str, asset: Path,
                   rect: tuple[float, float, float, float]) -> str:
    """Absolute linked-art frame; deliberately smaller than a full page."""
    x1, y1, x2, y2 = writer._page_rect(*rect)
    return (
        f'  <Rectangle Self="{rect_id}" ContentType="GraphicType" '
        'AppliedObjectStyle="ObjectStyle/$ID/[None]" '
        'StrokeColor="Swatch/None" StrokeWeight="0" '
        'ItemTransform="1 0 0 1 0 0">\n'
        + writer._path_geometry(x1, y1, x2, y2)
        + f'    <Image Self="{rect_id}_img" ItemTransform="1 0 0 1 {x1:g} {y1:g}">\n'
        f'      <Link Self="{rect_id}_lnk" '
        f'LinkResourceURI="{escape(asset.resolve().as_uri(), _ATTR)}"/>\n'
        '    </Image>\n'
        '    <FrameFittingOption FittingOnEmptyFrame="Proportionally" '
        'FittingAlignment="CenterAnchor" AutoFit="true"/>\n'
        '  </Rectangle>\n'
    )


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
        (42.0, text_y, writer.page_w - 70.0, 12.0),
        {"inset": (0, 0, 0, 0)},
    )
    return story, [bullet, frame]


def _front_cells(blocks: list[Block]) -> list[tuple[str, str]]:
    tables = [_rows(value) for kind, value in blocks if kind == "table"]
    primary = tables[0] if tables else []
    total = tables[1] if len(tables) > 1 else []
    at = lambda row, col: (  # noqa: E731 - compact structural lookup
        _label_value(primary[row][col])
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
    return [cells[0], cells[2], cells[1]]


# label frame positions are keyed by source-table semantics, not localized copy.
_FRONT_RECTS = (
    (31.5, 106.22, 108.0, 14.0, "LeftAlign"),
    (270.0, 106.32, 71.232, 14.0, "RightAlign"),
    (31.5, 129.93, 108.0, 26.0, "LeftAlign"),
    (268.0, 129.38, 73.273, 17.0, "RightAlign"),
    (31.5, 159.27, 108.0, 24.0, "LeftAlign"),
    (276.0, 159.02, 66.786, 14.0, "RightAlign"),
    (31.5, 185.38, 108.0, 39.0, "LeftAlign"),
    (264.0, 180.44, 76.854, 25.0, "RightAlign"),
    (31.5, 227.01, 108.0, 34.0, "LeftAlign"),
    (274.0, 205.26, 66.854, 28.0, "RightAlign"),
    (31.5, 267.93, 108.0, 18.0, "LeftAlign"),
    (262.0, 259.45, 78.854, 29.0, "RightAlign"),
)

_RIGHT_RECTS = (
    (34.5, 340.26, 110.0, 14.0, "LeftAlign"),
    (35.17, 369.61, 90.0, 40.0, "LeftAlign"),
    (274.0, 381.70, 66.099, 28.0, "RightAlign"),
)


_LEADER_PATHS = (
    ("power", ((31.489, 114.185), (158.505, 114.185), (158.505, 161.418))),
    ("lcd", ((341.847, 114.186), (189.796, 114.186), (189.796, 161.661))),
    ("dc12", ((31.489, 146.871), (141.445, 146.871), (141.445, 164.866))),
    ("led_button", ((341.848, 139.520), (215.164, 139.520), (215.164, 160.417))),
    (
        "usb_c_30",
        (
            (31.489, 181.322),
            (121.975, 181.322),
            (121.975, 191.433),
            (137.166, 191.433),
        ),
    ),
    (
        "usb_c_100",
        (
            (32.711, 206.567),
            (133.707, 206.567),
            (133.707, 199.327),
            (136.899, 199.327),
        ),
    ),
    ("usb_a", ((31.564, 247.150), (141.445, 247.150), (141.445, 215.192))),
    ("dc_usb", ((31.887, 279.076), (157.544, 279.076), (157.544, 207.125))),
    ("led", ((343.063, 168.024), (240.218, 168.024))),
    ("ac_power", ((341.333, 189.037), (176.970, 189.037), (176.970, 196.944))),
    ("ac_output", ((341.848, 229.197), (227.181, 229.197), (227.181, 213.113))),
    ("total", ((343.063, 277.164), (246.136, 277.164))),
    ("handle", ((34.461, 350.439), (203.393, 350.439), (203.393, 363.743))),
    ("dc_input", ((34.461, 400.923), (167.819, 400.923))),
    ("ac_input", ((341.261, 398.558), (209.153, 398.558))),
    ("total_connector", ((213.902, 213.103), (213.902, 260.327))),
)


def _label_frames(writer, sid: str,
                  cells: list[tuple[str, str]],
                  rects: tuple[tuple[float, float, float, float, str], ...]) -> list[str]:
    frames: list[str] = []
    for index, ((label, value), (x, y, width, height, align)) in enumerate(
        zip(cells, rects, strict=True)
    ):
        if not label:
            continue
        story_id = _label_story(
            writer, f"{sid}_label_{index + 1}", label, value, align=align)
        frames.append(frame_with_background(
            writer, sid, f"label_{index + 1}", story_id,
            (x, y, width, height), {"inset": (0, 0, 0, 0)},
        ))
    return frames


def add_product_overview_page(
    writer,
    sid: str,
    blocks: list[Block],
    bundle_root: Path,
    page_index: int,
) -> str:
    """Compose one localized overview page from source-authored semantics."""
    h1 = next((str(value) for kind, value in blocks if kind == "h1"), "")
    h2s = [str(value) for kind, value in blocks if kind == "h2"]
    image_refs = [str(value) for kind, value in blocks if kind == "image"]
    if not h1 or len(h2s) != 2 or len(image_refs) != 2:
        raise ValueError("product overview requires one h1, two h2s, and two images")
    assets = [writer._resolve_bundle_image(bundle_root, ref) for ref in image_refs]
    if any(asset is None for asset in assets):
        raise ValueError("product overview contains an unresolved governed image")

    first_h2 = next(i for i, block in enumerate(blocks) if block[0] == "h2")
    second_h2 = next(
        i for i in range(first_h2 + 1, len(blocks)) if blocks[i][0] == "h2"
    )
    front_blocks = blocks[first_h2 + 1:second_h2]
    right_blocks = blocks[second_h2 + 1:]

    title_sid = writer._add_story_parts(
        f"{sid}_title", h1, [heading_text(writer, h1, level=1)])
    _, front_heading = _section_heading(
        writer,
        f"{sid}_front",
        h2s[0],
        text_y=69.832,
        bullet_rect=(30.425, 69.991, 7.067, 7.068),
    )
    _, right_heading = _section_heading(
        writer,
        f"{sid}_right",
        h2s[1],
        text_y=317.009,
        bullet_rect=(30.425, 317.336, 7.067, 7.068),
    )

    artwork_and_headings = [
        _graphic_frame(writer, f"art_{sid}_front", assets[0],
                       (28.0, 98.0, 317.0, 185.0)),  # type: ignore[arg-type]
        _graphic_frame(writer, f"art_{sid}_right", assets[1],
                       (30.0, 335.0, 315.0, 157.0)),  # type: ignore[arg-type]
        frame_with_background(
            writer, sid, "title", title_sid,
            (29.505, 28.035, 311.91, 20.065),
            {**heading_bar_opts(1, (1.5, 5.0, 1.0, 6.0)),
             "text_rect": (35.9, 26.12, 299.0, 20.1)},
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
        for name, points in _LEADER_PATHS
    ]
    dark_leaders = [
        _leader_path(
            writer,
            f"leader_{sid}_{name}",
            points,
            color="Color/HB Brand Dark",
            weight=0.30,
        )
        for name, points in _LEADER_PATHS
    ]
    label_frames = [
        *_label_frames(writer, f"{sid}_front", _front_cells(front_blocks), _FRONT_RECTS),
        *_label_frames(writer, f"{sid}_right", _right_cells(right_blocks), _RIGHT_RECTS),
    ]
    # All editable copy is emitted last and therefore opens above artwork and
    # both leader strokes in InDesign's stacking order.
    frames = artwork_and_headings + white_leaders + dark_leaders + label_frames

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
