"""Character-run serialization for editable IDML prose."""
from __future__ import annotations

import re
from xml.sax.saxutils import escape

from .font_family import (
    BULLET_FONT_FAMILY_TOKEN,
    CIRCLED_NUMBER_FONT_FAMILY_TOKEN,
    CJK_FONT_FAMILY_TOKEN,
    family_declares_style,
    cjk_font_family_for_language,
    KOREAN_FONT_FAMILY_TOKEN,
    SYMBOL_FONT_FAMILY_TOKEN,
    TEXT_SYMBOL_FONT_FAMILY_TOKEN,
)

GENERAL_SYMBOL_FONT = SYMBOL_FONT_FAMILY_TOKEN.name
CIRCLED_NUMBER_FONT = CIRCLED_NUMBER_FONT_FAMILY_TOKEN.name
TEXT_SYMBOL_FONT = TEXT_SYMBOL_FONT_FAMILY_TOKEN.name
BULLET_FONT = BULLET_FONT_FAMILY_TOKEN.name
SYMBOL_FONT_FALLBACK_STYLE = "Regular"
SYMBOL_FONT_FALLBACKS = {
    "⎓": GENERAL_SYMBOL_FONT,
    # U+203B is a native vector component.  Unlike a font fallback, it remains
    # stable after saving to INDD and reopening on another host.
    # Gilroy's installed production face has no masculine ordinal indicator.
    # Keep the source Spanish ``Nº`` intact and route only that glyph through
    # the governed Unicode fallback so PDF/X export does not emit .notdef.
    "º": TEXT_SYMBOL_FONT,
    # JP temperature values use the single U+2103 character. Gilroy lacks it;
    # preserve the source unit and use the already bundled text-symbol face.
    "℃": TEXT_SYMBOL_FONT,
    **{ch: TEXT_SYMBOL_FONT for ch in "₀₁₂₃₄₅₆₇₈₉"},
    # The shared regulatory contact row uses these three editable Unicode
    # icons.  Gilroy and the first Noto Symbols face do not cover U+260E;
    # Noto Sans Symbols2 covers the complete set and is already carried in
    # every designer-facing IDML package.  Keep the source codepoints intact
    # and split only the icon run from the adjacent contact copy.
    **{ch: BULLET_FONT for ch in "☎✉◉"},
    **{ch: BULLET_FONT for ch in "●■"},
    # Gilroy does not cover the open-circle marker used by nested warranty
    # lists.  Keep the authored marker editable, but route it through the
    # same portable bullet face already shipped in every IDML package.
    "◦": BULLET_FONT,
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


_CHARACTER_STYLE_RANGE_OPEN = re.compile(r"<CharacterStyleRange\s[^>]*>")
_FONT_STYLE_ATTR = re.compile(r'\sFontStyle="[^"]*"')


def drop_duplicate_font_style(xml: str) -> str:
    """Collapse a doubled ``FontStyle`` on one character range.

    A component may set a semantic style (``Bold`` on a table header) on a
    range whose text also needs an explicit fallback font, and the fallback
    adds its own ``Regular``. XML rejects two attributes with the same name,
    so InDesign refuses the whole story — it surfaced the first time a
    Hangul troubleshooting header met the bold header style.

    The fallback face supplies the style that actually applies, so its
    attribute (the last one) is the one kept. Ranges carrying a single
    ``FontStyle`` are returned untouched, which makes this a no-op on every
    story that is already valid.
    """

    def collapse(match: re.Match[str]) -> str:
        tag = match.group(0)
        styles = _FONT_STYLE_ATTR.findall(tag)
        if len(styles) < 2:
            return tag
        return _FONT_STYLE_ATTR.sub("", tag[:-1]) + styles[-1] + ">"

    return _CHARACTER_STYLE_RANGE_OPEN.sub(collapse, xml)


# Weight the shipped Japanese book gives each component, measured by matching
# every Japanese run against the same page of the printed reference and grouping
# the answers by the paragraph style that produced it. Only non-Regular entries
# appear: Regular is the inherited default, so listing it would be a no-op.
#
# Recorded in code-as-doc/reviews/bp_jp_reference_vs_built_2026-09.md together
# with the proportion behind each choice. Where the reference is not unanimous
# the dominant weight is used, by operator ruling, rather than leaving the
# component at body weight.
_JAPANESE_PARAGRAPH_WEIGHTS = {
    # running text
    "HB Symbol Body": "DemiLight",      # 94% of 238 chars
    "HB Warranty Body": "DemiLight",    # 76% of 401 chars
    "HB Warranty List": "DemiLight",    # 100% of 124 chars
    "HB Warranty Lead": "DemiLight",    # 100%, small sample
    # secondary structure
    "HB TOC Entry": "Medium",           # 100% of 51 chars
    "HB TOC Bar": "Medium",             # 100%, small sample
    "\u6bb5\u843d\u6837\u5f0f-\u52a0\u7c97": "Medium",  # 87% of 38 chars
    # headings and labels
    "HB TOC Title": "Bold",             # 100%, small sample
    "HB Warranty Title": "Bold",        # 100% of 36 chars
    "\u5e26\u5e95Heading2": "Bold",    # 100% of 66 chars
    "Heading2": "Bold",                 # 68% of 22 chars
    "HB Callout Label": "Bold",         # 80%, small sample
    "HB Operation Row Label": "Bold",   # 100%, small sample
}

_PARAGRAPH_RANGE = re.compile(
    r'(<ParagraphStyleRange\b[^>]*AppliedParagraphStyle="([^"]+)"[^>]*>)(.*?)'
    r"(</ParagraphStyleRange>)",
    re.S,
)


def _apply_paragraph_weight(body: str, family: str, weight: str) -> str:
    """Set ``weight`` on this paragraph's runs in ``family``.

    Only runs sitting at the inherited Regular are moved. A run that already
    carries Bold got it from inline emphasis in the source, and emphasis is a
    stronger signal than the component's resting weight, so it is left alone.
    """
    applied = f'<AppliedFont type="string">{family}</AppliedFont>'

    def retag(match: re.Match[str]) -> str:
        attrs, inner = match.group(1), match.group(2)
        if applied not in inner or 'FontStyle="Regular"' not in attrs:
            return match.group(0)
        return attrs.replace('FontStyle="Regular"', f'FontStyle="{weight}"') + inner + "</CharacterStyleRange>"

    return re.sub(
        r"(<CharacterStyleRange\b[^>]*>)((?:(?!</CharacterStyleRange>).)*?)</CharacterStyleRange>",
        retag,
        body,
        flags=re.S,
    )


def apply_cjk_paragraph_weights(xml: str, language: str | None) -> str:
    """Give each component the resting weight the shipped book uses.

    Language-scoped on purpose: the paragraph styles are shared across every
    language, and the Latin family has no DemiLight at all, so writing these
    weights into the style definitions would change books that were never
    measured. Applying them here, beside the family binding that is already
    language-scoped, leaves every other language byte-identical.
    """
    from .font_family import (
        JAPANESE_FONT_FAMILY_TOKEN,
        cjk_font_family_for_language,
        family_declares_style,
    )

    # Resolve through the family rather than testing the language spelling: the
    # registry already owns which codes mean Japanese, and the guardrails keep
    # language literals out of this layer.
    family = cjk_font_family_for_language(language)
    if family != JAPANESE_FONT_FAMILY_TOKEN.name:
        return xml

    def handle(match: re.Match[str]) -> str:
        open_tag, style_ref, body, close_tag = match.groups()
        weight = _JAPANESE_PARAGRAPH_WEIGHTS.get(style_ref.split("/")[-1])
        if weight is None or not family_declares_style(family, weight):
            return match.group(0)
        return open_tag + _apply_paragraph_weight(body, family, weight) + close_tag

    return _PARAGRAPH_RANGE.sub(handle, xml)


_GENERIC_CJK_APPLIED_FONT = (
    f'<AppliedFont type="string">{CJK_FONT_FAMILY_TOKEN.name}</AppliedFont>'
)


def localize_cjk_fallback_font(xml: str, language: str | None) -> str:
    """Bind generic CJK runs to the portable face for this document language.

    This is also where deferred emphasis is settled. ``_style_range`` writes
    ``Bold`` on a generic CJK run without knowing the document language, since
    the family that finally applies is chosen here. A family that ships only a
    Regular face cannot honour it, so the emphasis is withdrawn rather than
    left to become a missing-face substitution covering the whole run.
    """
    family = cjk_font_family_for_language(language)
    if not family_declares_style(family, "Bold"):
        xml = _withdraw_unsupported_cjk_bold(xml)
    if family == CJK_FONT_FAMILY_TOKEN.name:
        return xml
    bound = xml.replace(
        _GENERIC_CJK_APPLIED_FONT,
        f'<AppliedFont type="string">{family}</AppliedFont>',
    )
    return apply_cjk_paragraph_weights(bound, language)


_CJK_BOLD_RANGE = re.compile(
    r'(<CharacterStyleRange\b[^>]*?)FontStyle="Bold"([^>]*>(?:(?!</CharacterStyleRange>).)*?'
    + re.escape(_GENERIC_CJK_APPLIED_FONT) + r")",
    re.S,
)


def _withdraw_unsupported_cjk_bold(xml: str) -> str:
    """Return ``xml`` with bold removed from generic-CJK runs only."""
    return _CJK_BOLD_RANGE.sub(
        lambda m: f'{m.group(1)}FontStyle="{SYMBOL_FONT_FALLBACK_STYLE}"{m.group(2)}',
        xml,
    )


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
        # A fallback run still carries its emphasis, but only where the family
        # that finally applies ships a Bold face. Asking for a face the package
        # lacks makes InDesign substitute the whole run, and bold used to be
        # dropped here unconditionally, which flattened every emphasized CJK
        # label to body weight.
        #
        # The generic CJK token is a placeholder: the document language decides
        # the real family later, at localize_cjk_fallback_font. Emit the
        # emphasis here and let that sink downgrade it if the resolved family
        # cannot render it, because this function has no language to resolve.
        deferred = fallback_font == CJK_FONT_FAMILY_TOKEN.name
        style = (
            "Bold"
            if bold and (deferred or family_declares_style(fallback_font, "Bold"))
            else SYMBOL_FONT_FALLBACK_STYLE
        )
        attrs += f' FontStyle="{style}"'
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
    # Import lazily: components import the primitives module during registry
    # initialization, so a module-level import would create a package cycle.
    if "※" in segment:
        from .components.native_marker import reference_mark_xml

        replacements = {"※": reference_mark_xml(), **replacements}
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
