"""Character-run serialization for editable IDML prose."""
from __future__ import annotations

from xml.sax.saxutils import escape

from .font_family import CJK_FONT_FAMILY_TOKEN

DIRECT_CURRENT_SYMBOL_FONT = "Apple Symbols"
GENERAL_SYMBOL_FONT = CJK_FONT_FAMILY_TOKEN.name
SYMBOL_FONT_FALLBACK_STYLE = "Regular"
SYMBOL_FONT_FALLBACKS = {
    "⎓": DIRECT_CURRENT_SYMBOL_FONT,
    "※": GENERAL_SYMBOL_FONT,
    # Gilroy's installed production face has no masculine ordinal indicator.
    # Keep the source Spanish ``Nº`` intact and route only that glyph through
    # the governed Unicode fallback so PDF/X export does not emit .notdef.
    "º": GENERAL_SYMBOL_FONT,
    **{
        ch: GENERAL_SYMBOL_FONT
        for ch in "₀₁₂₃₄₅₆₇₈₉①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳❶❷❸❹❺❻❼❽❾●"
    },
    **{ch: "Apple SD Gothic Neo" for ch in "㉑㉒㉓㉔㉕㉖㉗"},
}
SPEC_SUPERSCRIPT_MARKERS = frozenset(
    "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
)

# Script/presentation blocks that require the governed CJK family instead of
# inheriting the Latin primary paragraph font.  Keep this explicit rather
# than using East Asian Width: emoji are often Wide too, but must not be
# silently routed to a CJK text font.  Width-aware line estimation is a
# separate Stage 5 contract.
_CJK_CODEPOINT_RANGES = (
    (0x1100, 0x11FF),   # Hangul Jamo
    (0x2E80, 0x2FFF),   # CJK radicals + ideographic description characters
    (0x3000, 0x303F),   # CJK symbols and punctuation
    (0x3040, 0x30FF),   # Hiragana + Katakana
    (0x3100, 0x312F),   # Bopomofo
    (0x3130, 0x318F),   # Hangul compatibility Jamo
    (0x31A0, 0x31BF),   # Bopomofo extended
    (0x31C0, 0x31EF),   # CJK strokes
    (0x31F0, 0x31FF),   # Katakana phonetic extensions
    (0x3200, 0x33FF),   # Enclosed CJK letters/months and compatibility units
    (0x3400, 0x4DBF),   # CJK unified ideographs extension A
    (0x4E00, 0x9FFF),   # CJK unified ideographs
    (0xA960, 0xA97F),   # Hangul Jamo extended A
    (0xAC00, 0xD7AF),   # Hangul syllables
    (0xD7B0, 0xD7FF),   # Hangul Jamo extended B
    (0xF900, 0xFAFF),   # CJK compatibility ideographs
    (0xFE10, 0xFE1F),   # Vertical punctuation forms
    (0xFE30, 0xFE4F),   # CJK compatibility forms
    (0xFF01, 0xFFEF),   # Fullwidth forms, halfwidth Katakana/Hangul
    (0x1B000, 0x1B16F), # Kana supplements and small Kana extension
    (0x20000, 0x2FA1F), # CJK extensions B-F + compatibility supplement
    (0x30000, 0x323AF), # CJK extensions G-H
)


def _is_cjk_character(character: str) -> bool:
    codepoint = ord(character)
    return any(start <= codepoint <= end for start, end in _CJK_CODEPOINT_RANGES)


def _fallback_font(character: str) -> str | None:
    symbol_font = SYMBOL_FONT_FALLBACKS.get(character)
    if symbol_font is not None:
        return symbol_font
    if _is_cjk_character(character):
        return CJK_FONT_FAMILY_TOKEN.name
    return None


def _font_runs(segment: str) -> list[tuple[str, str | None]]:
    """Split a text segment by the explicit fallback font it needs."""
    runs: list[tuple[str, str | None]] = []
    buffer: list[str] = []
    current_font = _fallback_font(segment[0]) if segment else None
    for character in segment:
        font = _fallback_font(character)
        if font != current_font:
            runs.append(("".join(buffer), current_font))
            buffer = []
            current_font = font
        buffer.append(character)
    if buffer:
        runs.append(("".join(buffer), current_font))
    return runs


def _style_range(
    segment: str,
    *,
    bold: bool,
    fallback_font: str | None,
    superscript_marker: bool = False,
    inner_xml: str | None = None,
    position: str | None = None,
) -> str:
    attrs = 'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"'
    properties = ""
    if fallback_font:
        attrs += f' FontStyle="{SYMBOL_FONT_FALLBACK_STYLE}"'
        properties = (
            "<Properties>"
            f'<AppliedFont type="string">{escape(fallback_font)}</AppliedFont>'
            "</Properties>"
        )
    elif bold:
        attrs += ' FontStyle="Bold"'
    if position:
        attrs += f' Position="{position}"'
    if superscript_marker and segment and all(
        character in SPEC_SUPERSCRIPT_MARKERS for character in segment
    ):
        attrs += ' PointSize="5.2" BaselineShift="2.4"'
    content = inner_xml if inner_xml is not None else f"<Content>{escape(segment)}</Content>"
    return f'<CharacterStyleRange {attrs}>{properties}{content}</CharacterStyleRange>'


def inline_role_range(segment: str, *, role: str, bold: bool = False) -> str:
    """Serialize an RST sub/sup role as an editable InDesign text position."""
    position = "Subscript" if role == "sub" else "Superscript"
    return "".join(
        _style_range(
            piece,
            bold=bold,
            fallback_font=fallback_font,
            position=position,
        )
        for piece, fallback_font in _font_runs(segment)
    )


def _ranges_with_replacements(
    segment: str,
    *,
    bold: bool,
    superscript_marker: bool,
    replacements: dict[str, str],
) -> list[str]:
    """Split one character run around governed anchored inline objects."""
    output: list[str] = []
    cursor = 0
    while cursor < len(segment):
        matches = [
            (position, marker, replacement)
            for marker, replacement in replacements.items()
            if (position := segment.find(marker, cursor)) >= 0
        ]
        if not matches:
            output.append(_style_range(
                segment[cursor:],
                bold=bold,
                fallback_font=None,
                superscript_marker=superscript_marker,
            ))
            break
        start, marker, replacement = min(matches, key=lambda item: item[0])
        if start > cursor:
            output.append(_style_range(
                segment[cursor:start],
                bold=bold,
                fallback_font=None,
                superscript_marker=superscript_marker,
            ))
        output.append(_style_range(
            "", bold=False, fallback_font=None, inner_xml=replacement,
        ))
        cursor = start + len(marker)
    return output


def character_ranges(
    segment: str,
    *,
    bold: bool,
    superscript_markers: bool,
    replacements: dict[str, str],
) -> list[str]:
    """Serialize one bold/plain segment, preserving fallback-font boundaries."""
    output: list[str] = []
    for piece, fallback_font in _font_runs(segment):
        if replacements and fallback_font is None:
            output.extend(_ranges_with_replacements(
                piece,
                bold=bold,
                superscript_marker=superscript_markers,
                replacements=replacements,
            ))
        else:
            output.append(_style_range(
                piece,
                bold=bold,
                fallback_font=fallback_font,
                superscript_marker=superscript_markers,
            ))
    return output
