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
    marker = 'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"'
    return xml.replace(
        marker,
        marker + f' PointSize="{size:g}" Leading="{leading:g}"',
    )


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


def _rule(writer, rid: str, x: float, y: float, w: float,
          h: float = 0.35) -> str:
    from .page_objects import page_rectangle_xml

    return page_rectangle_xml(
        writer, rid, (x, y, w, h),
        fill="Color/HB Brand Dark",
        stroke_color="Swatch/None",
        stroke_weight=0,
        corner_radius=0,
        rounded=False,
    )


def _section_heading(writer, sid: str, text: str,
                     y: float) -> tuple[str, list[str]]:
    from .page_objects import page_rectangle_xml

    story = writer._add_story_parts(
        f"{sid}_story", text,
        [_typed_paragraph(
            writer, text, size=8.0, leading=9.0, bold=True,
            align="LeftAlign", terminal=True,
        )],
    )
    bullet = page_rectangle_xml(
        writer, f"{sid}_bullet", (33.0, y + 2.0, 6.0, 6.0),
        fill="Color/HB Brand Dark",
        stroke_color="Swatch/None",
        stroke_weight=0,
        corner_radius=3.0,
    )
    frame = frame_with_background(
        writer, sid, "heading", story,
        (42.0, y, writer.page_w - 70.0, 12.0),
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
    (31.5, 103.8, 108.0, 14.0, "LeftAlign"),
    (270.0, 103.8, 71.5, 14.0, "RightAlign"),
    (31.5, 127.5, 108.0, 26.0, "LeftAlign"),
    (268.0, 127.0, 73.5, 17.0, "RightAlign"),
    (31.5, 157.0, 108.0, 24.0, "LeftAlign"),
    (276.0, 157.0, 65.5, 14.0, "RightAlign"),
    (31.5, 183.0, 108.0, 39.0, "LeftAlign"),
    (264.0, 178.0, 77.5, 25.0, "RightAlign"),
    (31.5, 224.5, 108.0, 34.0, "LeftAlign"),
    (274.0, 203.0, 67.5, 28.0, "RightAlign"),
    (31.5, 265.5, 108.0, 18.0, "LeftAlign"),
    (262.0, 257.0, 79.5, 29.0, "RightAlign"),
)

_RIGHT_RECTS = (
    (34.5, 337.5, 110.0, 14.0, "LeftAlign"),
    (35.0, 367.0, 100.0, 40.0, "LeftAlign"),
    (274.0, 379.0, 67.0, 28.0, "RightAlign"),
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
    _, front_heading = _section_heading(writer, f"{sid}_front", h2s[0], 66.5)
    _, right_heading = _section_heading(writer, f"{sid}_right", h2s[1], 313.5)

    frames = [
        _graphic_frame(writer, f"art_{sid}_front", assets[0],
                       (28.0, 98.4, 316.8, 158.2)),  # type: ignore[arg-type]
        _graphic_frame(writer, f"art_{sid}_right", assets[1],
                       (28.0, 336.0, 316.8, 158.2)),  # type: ignore[arg-type]
        frame_with_background(
            writer, sid, "title", title_sid,
            (28.5, 29.6, 311.9, 20.1),
            {**heading_bar_opts(1, (1.5, 5.0, 1.0, 6.0)),
             "text_rect": (34.0, 29.2, 301.0, 20.1)},
        ),
        *front_heading,
        *right_heading,
        *_label_frames(writer, f"{sid}_front", _front_cells(front_blocks), _FRONT_RECTS),
        *_label_frames(writer, f"{sid}_right", _right_cells(right_blocks), _RIGHT_RECTS),
        # Long horizontal leaders; the linked artwork retains the short device-side stubs.
        _rule(writer, f"rule_{sid}_front_l1", 31.5, 114.2, 127.0),
        _rule(writer, f"rule_{sid}_front_r1", 189.8, 114.2, 152.0),
        _rule(writer, f"rule_{sid}_front_l2", 31.5, 137.9, 129.0),
        _rule(writer, f"rule_{sid}_front_r2", 189.8, 137.9, 152.0),
        _rule(writer, f"rule_{sid}_right_l", 34.5, 350.4, 169.0),
        _rule(writer, f"rule_{sid}_right_r", 227.0, 391.5, 114.0),
    ]

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
