"""Small XML helpers shared by the fixed FCC/Inbox panel family."""
from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from ..style_names import paragraph_style_ref


def add_story(writer, sid: str, title: str, parts: list[str]) -> str:
    return writer._add_story_parts(sid, title, parts)


def image_paragraph(
    writer,
    tid: str,
    image: Path,
    max_width: float,
    *,
    center: bool = True,
    space_after: float = 0.0,
) -> str:
    width, height = writer._art_frame_size(image, max_w=max_width)
    figure_style = paragraph_style_ref("HB Figure")
    justification = ' Justification="CenterAlign"' if center else ""
    spacing = f' SpaceAfter="{space_after:g}"' if space_after else ""
    return (
        f'  <ParagraphStyleRange AppliedParagraphStyle="{figure_style}"'
        f'{justification}{spacing}>\n'
        '    <CharacterStyleRange '
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
        + writer._image_cell_content(tid, image, width, height)
        + '<Content></Content><Br/></CharacterStyleRange>\n'
        '  </ParagraphStyleRange>\n'
    )


def centered_psr(
    style: str,
    text: str,
    *,
    character_attrs: str = "",
) -> str:
    style_ref = paragraph_style_ref(style)
    attrs = f" {character_attrs}" if character_attrs else ""
    return (
        f'  <ParagraphStyleRange AppliedParagraphStyle="{style_ref}" '
        'Justification="CenterAlign">\n'
        '    <CharacterStyleRange '
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"'
        f'{attrs}>'
        f'<Content>{escape(text)}</Content></CharacterStyleRange>\n'
        '  </ParagraphStyleRange>\n'
    )


__all__ = ["add_story", "centered_psr", "image_paragraph"]
