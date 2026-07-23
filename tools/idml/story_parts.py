"""Small standalone story builders re-exported by the stories facade."""
from __future__ import annotations

from xml.sax.saxutils import escape

from .params import IDPKG
from .primitives import _ATTR_ENTITIES


def add_text_story(writer, sid: str, title: str, blocks: list[tuple[str, str]]) -> str:
    parts = [
        writer._psr(style, text, terminal=(index == len(blocks) - 1))
        for index, (style, text) in enumerate(blocks)
    ]
    return add_story_parts(writer, sid, title, parts)


def add_story_parts(writer, sid: str, title: str, parts: list[str]) -> str:
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'<Story Self="{sid}" AppliedTOCStyle="n" TrackChanges="false" StoryTitle="{escape(title, _ATTR_ENTITIES)}">\n'
        '<StoryPreference OpticalMarginAlignment="false" FrameType="TextFrameType"/>\n'
        + "".join(parts)
        + '</Story>\n</idPkg:Story>\n'
    )
    writer.stories.append((sid, xml))
    return sid
