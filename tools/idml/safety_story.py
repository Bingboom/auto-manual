"""Safety-section story serialization shared by page compositions."""
from __future__ import annotations

import re
from pathlib import Path

from .character_metrics import with_character_metrics
from .language_contract import layout_override_languages
from .params import param_pt


def _safety_section_story(writer, sid: str, title: str,
                          blocks: list[tuple[str, str]],
                          bundle_root: Path, *,
                          compact: bool = False,
                          language: str | None = None) -> str:
    parts: list[str] = []
    text_measure = writer.page_w - writer.m_l - writer.m_r
    column_gap = param_pt(writer.params, "comp_twocol_sep", 6.24)
    column_measure = (text_measure - column_gap) / 2.0
    content_indices = [i for i, (kind, _) in enumerate(blocks) if kind != "layout"]
    last_idx = content_indices[-1] if content_indices else -1
    previous_kind = ""
    dense_language = any(marker in sid.casefold() for marker in ("_fr_", "_es_"))
    language = (
        str(language).strip().casefold().replace("_", "-").split("-", 1)[0]
        if language else _safety_language(sid)
    )
    right_section = sid.endswith("_right")
    scale_key = (
        "idml_compact_safety_list_horizontal_scale"
        if compact
        else "idml_safety_list_horizontal_scale_dense"
        if dense_language
        else "idml_safety_list_horizontal_scale"
    )
    localized_scale_key = f"lang_{language}_{scale_key}"
    horizontal_scale = 100.0 * float(
        writer.params.get(
            localized_scale_key,
            writer.params.get(
                scale_key,
                (
                    "0.96"
                    if compact
                    else "0.90"
                    if dense_language
                    else "0.98",
                    "ratio",
                ),
            ),
        )[0]
    )
    compact_size = param_pt(
        writer.params,
        f"lang_{language}_idml_compact_safety_list_font_size",
        param_pt(writer.params, "idml_compact_safety_list_font_size", 5.0),
    )
    compact_leading = param_pt(
        writer.params,
        f"lang_{language}_idml_compact_safety_list_leading",
        param_pt(writer.params, "idml_compact_safety_list_leading", 5.8),
    )
    for bi, (kind, text) in enumerate(blocks):
        terminal = bi == last_idx
        if kind == "component":
            import json as _json
            xml_part, _ = writer._render_component(
                sid, bi, _json.loads(text), bundle_root, terminal,
                span_columns=False, measure_w=column_measure)
            parts.append(xml_part)
        elif kind == "body":
            # \HBTypeBody territory: lead-ins are body Medium, not L2 Bold
            body_xml = writer._psr(
                "HB Body",
                f"**{text}**" if compact else text,
                terminal=terminal,
            )
            if compact:
                body_xml = with_character_metrics(
                    body_xml,
                    point_size=param_pt(
                        writer.params,
                        f"lang_{language}_idml_compact_safety_body_font_size",
                        param_pt(
                            writer.params,
                            "idml_compact_safety_body_font_size",
                            5.4,
                        ),
                    ),
                    leading=param_pt(
                        writer.params,
                        f"lang_{language}_idml_compact_safety_body_leading",
                        param_pt(
                            writer.params,
                            "idml_compact_safety_body_leading",
                            6.1,
                        ),
                    ),
                )
            parts.append(body_xml)
        elif kind == "safetylead":
            parts.append(writer._psr("HB Safety Lead", text, terminal=terminal))
        elif kind == "list":
            list_style = (
                f"HB Safety List {language.upper()}"
                if language in {"fr", "es"}
                else "HB Safety List"
            )
            list_left_indent = param_pt(
                writer.params,
                (
                    f"lang_{language}_idml_safety_right_list_left_indent"
                    if right_section
                    else f"lang_{language}_idml_safety_list_left_indent"
                ),
                param_pt(writer.params, "idml_list_left_indent", 3.7),
            )
            list_first_line_indent = param_pt(
                writer.params,
                (
                    f"lang_{language}_idml_safety_right_list_first_line_indent"
                    if right_section
                    else f"lang_{language}_idml_safety_list_first_line_indent"
                ),
                param_pt(writer.params, "idml_list_first_line_indent", -6.25),
            )
            list_space_after = param_pt(
                writer.params,
                (
                    f"lang_{language}_idml_compact_safety_list_space_after"
                    if compact
                    else f"lang_{language}_idml_safety_list_space_after"
                ),
                param_pt(
                    writer.params,
                    "idml_compact_safety_list_space_after"
                    if compact else "comp_list_itemsep",
                    0.35 if compact else 2.07,
                ),
            )
            list_xml = _safety_list_xml(
                writer,
                style=list_style,
                text=text,
                terminal=terminal,
                left_indent=list_left_indent,
                first_line_indent=list_first_line_indent,
                space_after=list_space_after,
                horizontal_scale=horizontal_scale,
                default_marker="•",
            )
            if compact:
                list_xml = with_character_metrics(
                    list_xml,
                    point_size=compact_size,
                    leading=compact_leading,
                    horizontal_scale=horizontal_scale,
                )
            parts.append(list_xml)
        elif kind == "sublist":
            sublist_style = (
                f"HB Safety Sublist {language.upper()}"
                if language in {"fr", "es"}
                else "HB Safety Sublist"
            )
            sublist_space_after = param_pt(
                writer.params,
                (
                    f"lang_{language}_idml_compact_safety_list_space_after"
                    if compact
                    else f"lang_{language}_idml_safety_list_space_after"
                ),
                param_pt(
                    writer.params,
                    "idml_compact_safety_list_space_after"
                    if compact else "comp_sublist_itemsep",
                    0.35 if compact else 2.0,
                ),
            )
            sublist_left_indent = param_pt(
                writer.params, "idml_sublist_left_indent", 9.58,
            )
            sublist_xml = _safety_list_xml(
                writer,
                style=sublist_style,
                text=text,
                terminal=terminal,
                left_indent=sublist_left_indent,
                first_line_indent=param_pt(
                    writer.params, "idml_sublist_first_line_indent", -6.04,
                ),
                space_after=sublist_space_after,
                horizontal_scale=horizontal_scale,
                default_marker="–",
            )
            if compact:
                sublist_xml = with_character_metrics(
                    sublist_xml,
                    point_size=compact_size,
                    leading=compact_leading,
                    horizontal_scale=horizontal_scale,
                )
            if previous_kind != "sublist":
                first_gap = param_pt(
                    writer.params, "idml_sublist_first_space_before", 0.45,
                )
                sublist_xml = sublist_xml.replace(
                    "<ParagraphStyleRange ",
                    f'<ParagraphStyleRange SpaceBefore="{first_gap:g}" ',
                    1,
                )
            parts.append(sublist_xml)
        elif kind in {"h1", "h2", "h3"}:
            parts.append(writer._psr(writer._PROSE_STYLE[kind], text, terminal=terminal))
        if kind != "layout":
            previous_kind = kind
    return writer._add_story_parts(sid, title, parts)


def _safety_list_xml(
    writer,
    *,
    style: str,
    text: str,
    terminal: bool,
    left_indent: float,
    first_line_indent: float,
    space_after: float,
    horizontal_scale: float,
    default_marker: str,
) -> str:
    """Render a safety-list marker separately from its tab-aligned prose."""
    marker_match = re.match(r"^\s*([•◦–-])(?:\s+|$)", text)
    marker = marker_match.group(1) if marker_match else default_marker
    list_text = text[marker_match.end():] if marker_match else text.lstrip()
    paragraph = writer._psr(style, list_text, terminal=terminal)
    paragraph = paragraph.replace(
        "<ParagraphStyleRange ",
        (
            '<ParagraphStyleRange '
            f'LeftIndent="{left_indent:g}" '
            f'FirstLineIndent="{first_line_indent:g}" '
            f'SpaceAfter="{space_after:g}" '
            'RightIndent="0" Hyphenation="false" '
        ),
        1,
    )
    paragraph = paragraph.replace(
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
        f'HorizontalScale="{horizontal_scale:g}"',
    )
    tab_properties = (
        '<Properties><TabList type="list"><ListItem type="record">'
        '<Alignment type="enumeration">LeftAlign</Alignment>'
        '<AlignmentCharacter type="string"></AlignmentCharacter>'
        '<Leader type="string"></Leader>'
        f'<Position type="unit">{left_indent:g}</Position>'
        '</ListItem></TabList></Properties>'
    )
    marker_xml = (
        '<CharacterStyleRange '
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
        f'HorizontalScale="{horizontal_scale:g}">'
        f'<Content>{marker}</Content>'
        '</CharacterStyleRange>'
    )
    tab_xml = (
        '<CharacterStyleRange '
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
        '<Content>\t</Content>'
        '</CharacterStyleRange>'
    )
    return paragraph.replace(
        "\n    <CharacterStyleRange",
        f"\n    {tab_properties}\n    {marker_xml}\n    {tab_xml}\n    <CharacterStyleRange",
        1,
    )


def _safety_language(sid: str) -> str:
    """Resolve the safety story's locale row-set from its story id.

    Scans every honored layout language, so a line in layout tuning reads its
    own ``lang_<code>_`` safety rows (or the base defaults) instead of
    silently borrowing the approved EN row-set through the "en" fallback.
    """
    folded = sid.casefold()
    return next(
        (lang for lang in layout_override_languages() if f"_{lang}" in folded),
        "en",
    )
