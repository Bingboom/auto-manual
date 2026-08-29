"""Character-run serialization for editable IDML prose."""
from __future__ import annotations

from xml.sax.saxutils import escape

from .font_family import (
    BULLET_FONT_FAMILY_TOKEN,
    CIRCLED_NUMBER_FONT_FAMILY_TOKEN,
    CJK_FONT_FAMILY_TOKEN,
    KOREAN_FONT_FAMILY_TOKEN,
    SYMBOL_FONT_FAMILY_TOKEN,
    TEXT_SYMBOL_FONT_FAMILY_TOKEN,
)

GENERAL_SYMBOL_FONT = SYMBOL_FONT_FAMILY_TOKEN.name
CIRCLED_NUMBER_FONT = CIRCLED_NUMBER_FONT_FAMILY_TOKEN.name
TEXT_SYMBOL_FONT = TEXT_SYMBOL_FONT_FAMILY_TOKEN.name
BULLET_FONT = BULLET_FONT_FAMILY_TOKEN.name
SYMBOL_FONT_FALLBACK_STYLE = "Regular"
# Noto Sans carries U+203B, but its glyph is 0.837 em wide.  Preserve the
# 0.593-em reference-mark advance used by the approved fixed frames so the
# portable face does not introduce a line-wrap/overset regression.
_REFERENCE_MARK_HORIZONTAL_SCALE = 70.8
SYMBOL_FONT_FALLBACKS = {
    "⎓": GENERAL_SYMBOL_FONT,
    "※": TEXT_SYMBOL_FONT,
    # Gilroy's installed production face has no masculine ordinal indicator.
    # Keep the source Spanish ``Nº`` intact and route only that glyph through
    # the governed Unicode fallback so PDF/X export does not emit .notdef.
    "º": TEXT_SYMBOL_FONT,
    **{ch: TEXT_SYMBOL_FONT for ch in "₀₁₂₃₄₅₆₇₈₉"},
    "●": BULLET_FONT,
    **{
        ch: CIRCLED_NUMBER_FONT
        for ch in "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳❶❷❸❹❺❻❼❽❾"
    },
}
SPEC_SUPERSCRIPT_MARKERS = frozenset(
    "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
)
_HIGH_CIRCLED_NUMBER_REPLACEMENTS = {
    chr(0x3251 + offset): f"({21 + offset})"
    for offset in range(7)
}


def _portable_text(segment: str) -> str:
    """Replace Unicode labels whose only common faces are host-specific."""
    return "".join(
        _HIGH_CIRCLED_NUMBER_REPLACEMENTS.get(character, character)
        for character in segment
    )

# Script/presentation blocks that require the governed CJK family instead of
# inheriting the Latin primary paragraph font.  Keep this explicit rather
# than using East Asian Width: emoji are often Wide too, but must not be
# silently routed to a CJK text font.  Width-aware line estimation is a
# separate Stage 5 contract.
_CJK_CODEPOINT_RANGES = (
    (0x2E80, 0x2FFF),   # CJK radicals + ideographic description characters
    (0x3000, 0x303F),   # CJK symbols and punctuation
    (0x3040, 0x30FF),   # Hiragana + Katakana
    (0x3100, 0x312F),   # Bopomofo
    (0x31A0, 0x31BF),   # Bopomofo extended
    (0x31C0, 0x31EF),   # CJK strokes
    (0x31F0, 0x31FF),   # Katakana phonetic extensions
    (0x3200, 0x33FF),   # Enclosed CJK letters/months and compatibility units
    (0x3400, 0x4DBF),   # CJK unified ideographs extension A
    (0x4E00, 0x9FFF),   # CJK unified ideographs
    (0xF900, 0xFAFF),   # CJK compatibility ideographs
    (0xFE10, 0xFE1F),   # Vertical punctuation forms
    (0xFE30, 0xFE4F),   # CJK compatibility forms
    (0xFF01, 0xFF9F),   # Fullwidth forms + halfwidth Katakana
    (0xFFE0, 0xFFEF),   # Fullwidth signs
    (0x1B000, 0x1B16F), # Kana supplements and small Kana extension
    (0x20000, 0x2FA1F), # CJK extensions B-F + compatibility supplement
    (0x30000, 0x323AF), # CJK extensions G-H
)

# Hangul routes to the governed Korean text face, not the CJK symbol
# fallback: Korean body type is a typographic choice (font_family.py), and
# Korean prose otherwise uses Western punctuation, so splitting by script
# block keeps ja/zh output byte-identical.
_HANGUL_CODEPOINT_RANGES = (
    (0x1100, 0x11FF),   # Hangul Jamo
    (0x3130, 0x318F),   # Hangul compatibility Jamo
    (0xA960, 0xA97F),   # Hangul Jamo extended A
    (0xAC00, 0xD7AF),   # Hangul syllables
    (0xD7B0, 0xD7FF),   # Hangul Jamo extended B
    (0xFFA0, 0xFFDC),   # Halfwidth Hangul variants
)


def _is_cjk_character(character: str) -> bool:
    codepoint = ord(character)
    return any(start <= codepoint <= end for start, end in _CJK_CODEPOINT_RANGES)


def _is_hangul_character(character: str) -> bool:
    codepoint = ord(character)
    return any(
        start <= codepoint <= end for start, end in _HANGUL_CODEPOINT_RANGES
    )


def fallback_font_for_character(character: str) -> str | None:
    """Return the governed IDML font required for one source character."""
    symbol_font = SYMBOL_FONT_FALLBACKS.get(character)
    if symbol_font is not None:
        return symbol_font
    if _is_hangul_character(character):
        return KOREAN_FONT_FAMILY_TOKEN.name
    if _is_cjk_character(character):
        return CJK_FONT_FAMILY_TOKEN.name
    return None


def _fallback_font(character: str) -> str | None:
    """Backward-compatible private entrypoint retained by latest-main tests."""
    return fallback_font_for_character(character)


def _font_runs(segment: str) -> list[tuple[str, str | None]]:
    """Split a text segment by the explicit fallback font it needs."""
    runs: list[tuple[str, str | None]] = []
    buffer: list[str] = []
    current_font = fallback_font_for_character(segment[0]) if segment else None
    for character in segment:
        font = fallback_font_for_character(character)
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
        if fallback_font == TEXT_SYMBOL_FONT and segment and set(segment) == {"※"}:
            attrs += f' HorizontalScale="{_REFERENCE_MARK_HORIZONTAL_SCALE:g}"'
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
    segment = _portable_text(segment)
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
    segment = _portable_text(segment)
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
