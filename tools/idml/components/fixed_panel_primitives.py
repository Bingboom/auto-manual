"""Small XML helpers shared by the fixed FCC/Inbox panel family."""
from __future__ import annotations

import re
from pathlib import Path

from ..inline_text import character_ranges
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
    content = "".join(
        character_ranges(
            text,
            # Preserve the caller's exact FontStyle/attribute order for
            # ordinary text.  Governed fallback runs already declare their
            # own Regular face and ``apply_character_attrs`` will not
            # overwrite it with a primary-font style.
            bold=False,
            superscript_markers=False,
            replacements={},
        )
    )
    xml = (
        f'  <ParagraphStyleRange AppliedParagraphStyle="{style_ref}" '
        'Justification="CenterAlign">\n'
        f'    {content}\n'
        '  </ParagraphStyleRange>\n'
    )
    return apply_character_attrs(xml, character_attrs)


_ATTRIBUTE_NAME = re.compile(r"([A-Za-z_:][A-Za-z0-9_.:-]*)\s*=")
_CHARACTER_RANGE_OPEN = re.compile(r"<CharacterStyleRange\b([^>]*)>")


def apply_character_attrs(paragraph_xml: str, character_attrs: str) -> str:
    """Add character attributes to every range without duplicating overrides.

    ``writer._psr`` splits CJK and governed-symbol fallback runs so each can
    carry its own font/style attributes.  Fixed-panel typography still needs
    to apply to every one of those ranges, but it must preserve an explicit
    fallback ``FontStyle=Regular`` (and bold/inline-role overrides) instead of
    serializing the same XML attribute twice.
    """
    additions = [
        match.group(0).strip()
        for match in re.finditer(
            r"[A-Za-z_:][A-Za-z0-9_.:-]*\s*=\s*\"[^\"]*\"",
            character_attrs,
        )
    ]
    if not additions:
        return paragraph_xml

    def merge(match: re.Match[str]) -> str:
        existing = match.group(1)
        existing_names = set(_ATTRIBUTE_NAME.findall(existing))
        missing = [
            attribute
            for attribute in additions
            if _ATTRIBUTE_NAME.match(attribute).group(1) not in existing_names
        ]
        suffix = (" " + " ".join(missing)) if missing else ""
        return f"<CharacterStyleRange{existing}{suffix}>"

    return _CHARACTER_RANGE_OPEN.sub(merge, paragraph_xml)


__all__ = [
    "add_story",
    "apply_character_attrs",
    "centered_psr",
    "image_paragraph",
]
