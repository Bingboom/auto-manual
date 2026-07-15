"""Explicit linked-story frame placement for shared physical pages."""
from __future__ import annotations

from .params import IDPKG


def add_story_frames(
    writer,
    story_id: str,
    frames: list[tuple[int, float, float]],
    *,
    margin_left: float | None = None,
    margin_right: float | None = None,
) -> None:
    """Place one linked story in explicit page-top/page-bottom regions."""
    x1 = -writer.page_w / 2 + (writer.m_l if margin_left is None else margin_left)
    x2 = writer.page_w / 2 - (writer.m_r if margin_right is None else margin_right)
    for i, (page_index, top, bottom) in enumerate(frames):
        spread_id = f"sp_{page_index}"
        frame_id = f"tf_{story_id}_{i}"
        prev = (
            f'PreviousTextFrame="tf_{story_id}_{i - 1}"'
            if i else 'PreviousTextFrame="n"'
        )
        nxt = (
            f'NextTextFrame="tf_{story_id}_{i + 1}"'
            if i < len(frames) - 1 else 'NextTextFrame="n"'
        )
        frame_xml = (
            f'  <TextFrame Self="{frame_id}" ParentStory="{story_id}" {prev} {nxt} '
            'ContentType="TextType" '
            'AppliedObjectStyle="ObjectStyle/$ID/[Normal Text Frame]" '
            'ItemTransform="1 0 0 1 0 0">\n'
            + writer._path_geometry(
                x1,
                -writer.page_h / 2 + top,
                x2,
                -writer.page_h / 2 + bottom,
            )
            + '    <TextFramePreference TextColumnCount="1" TextColumnGutter="11" '
            'AutoSizingType="Off"/>\n'
            '  </TextFrame>\n'
        )
        existing = next(
            (index for index, (sid, _xml) in enumerate(writer.spreads)
             if sid == spread_id),
            None,
        )
        if existing is not None:
            sid, xml = writer.spreads[existing]
            writer.spreads[existing] = (
                sid,
                xml.replace('</Spread>\n', frame_xml + '</Spread>\n', 1),
            )
            continue
        xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<idPkg:Spread xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
            f'<Spread Self="{spread_id}" PageCount="1" BindingLocation="0" '
            'ShowMasterItems="true">\n'
            f'  <Page Self="{spread_id}_pg" Name="{page_index + 1}" '
            'AppliedMaster="n" OverrideList="" TabOrder="" '
            'GridStartingPoint="TopOutside" '
            f'GeometricBounds="0 0 {writer.page_h:g} {writer.page_w:g}" '
            f'ItemTransform="1 0 0 1 {-writer.page_w / 2:g} '
            f'{-writer.page_h / 2:g}">\n'
            '    <MarginPreference ColumnCount="1" ColumnGutter="12" '
            f'Top="{writer.m_t:g}" Bottom="{writer.m_b:g}" '
            f'Left="{writer.m_l:g}" Right="{writer.m_r:g}"/>\n'
            '  </Page>\n'
            + frame_xml
            + '</Spread>\n'
            '</idPkg:Spread>\n'
        )
        writer.spreads.append((spread_id, xml))


def add_lcd_story_frames(
    writer,
    story_id: str,
    start_page: int,
    segment_count: int,
) -> None:
    """Place one complete rounded LCD table segment on each page."""
    bottom = writer.page_h - writer.m_b + 18.0
    add_story_frames(writer, story_id, [
        (start_page + offset, 27.33 if offset == 0 else writer.m_t, bottom)
        for offset in range(segment_count)
    ])
