"""Editable LCD callouts placed over a target-assembly hero figure."""
from __future__ import annotations

from collections.abc import Sequence

from .. import lcd_style as _lcd


def _page_point(writer, point: Sequence[float]) -> tuple[float, float]:
    """Convert top-left page coordinates into the spread coordinate system."""
    return (
        float(point[0]) - writer.page_w / 2.0,
        float(point[1]) - writer.page_h / 2.0,
    )


def _leader_xml(
    writer,
    *,
    leader_id: str,
    points: Sequence[Sequence[float]],
) -> str:
    anchors = "".join(
        (
            f'<PathPointType Anchor="{x:g} {y:g}" '
            f'LeftDirection="{x:g} {y:g}" '
            f'RightDirection="{x:g} {y:g}"/>'
        )
        for x, y in (_page_point(writer, point) for point in points)
    )
    return (
        f'  <GraphicLine Self="{leader_id}" ContentType="Unassigned" '
        'AppliedObjectStyle="ObjectStyle/$ID/[None]" '
        'FillColor="Swatch/None" StrokeColor="Color/HB Brand Dark" '
        'StrokeWeight="0.5" EndCap="ButtEndCap" '
        'ItemTransform="1 0 0 1 0 0">'
        '<Properties><PathGeometry><GeometryPathType PathOpen="true">'
        f'<PathPointArray>{anchors}</PathPointArray>'
        '</GeometryPathType></PathGeometry></Properties>'
        '</GraphicLine>\n'
    )


def _callout_story(
    writer,
    *,
    story_id: str,
    text: str,
    align: str,
) -> str:
    paragraph = _lcd.typed_paragraph(
        writer,
        "HB Spec Label",
        text,
        point_size=6.2,
        leading=7.0,
        bold=True,
    ).replace(
        "<ParagraphStyleRange ",
        f'<ParagraphStyleRange Justification="{align}" ',
        1,
    )
    return writer._add_story_parts(story_id, f"LCD callout {text}", [paragraph])


def add_lcd_callouts(
    writer,
    *,
    page_index: int,
    language: str,
    rows: Sequence[dict],
    callouts: Sequence[dict],
) -> None:
    """Add live label stories and native leader lines to one existing spread."""
    if not callouts:
        return
    spread_id = f"sp_{page_index}"
    spread_index = next(
        (
            index
            for index, (candidate, _xml) in enumerate(writer.spreads)
            if candidate == spread_id
        ),
        None,
    )
    if spread_index is None:
        raise ValueError(f"LCD callouts require existing spread {spread_id}")

    overlay: list[str] = []
    normalized_language = (
        language.strip().casefold().replace("_", "-").split("-", 1)[0]
    )
    for callout in callouts:
        row_index = int(callout["row_index"])
        if row_index > len(rows):
            raise ValueError(
                f"LCD callout row_index {row_index} exceeds {len(rows)} rows"
            )
        row = rows[row_index - 1]
        text = str(row.get("name") or "").strip()
        if not text:
            raise ValueError(f"LCD callout row {row_index} has no name")
        story_id = f"st_lcd_callout_{normalized_language}_{row_index}"
        _callout_story(
            writer,
            story_id=story_id,
            text=text,
            align=str(callout["align"]),
        )
        rect = tuple(float(value) for value in callout["text_rect"])
        x1, y1, x2, y2 = writer._page_rect(*rect)
        overlay.append(writer._frame_xml(
            f"tf_{story_id}",
            story_id,
            x1,
            y1,
            x2,
            y2,
            inset=(0.0, 0.0, 0.0, 0.0),
            valign="CenterAlign",
        ))
        overlay.append(_leader_xml(
            writer,
            leader_id=f"gl_lcd_callout_{normalized_language}_{row_index}",
            points=callout["leader_points"],
        ))

    sid, spread_xml = writer.spreads[spread_index]
    writer.spreads[spread_index] = (
        sid,
        spread_xml.replace("</Spread>\n", "".join(overlay) + "</Spread>\n", 1),
    )


__all__ = ("add_lcd_callouts",)
