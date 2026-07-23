"""Story builders whose golden byte-comparison pins IDML equivalence."""
from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from . import components as _components, page_objects as _po, prose_flow as _flow
from .data_stories import add_lcd_story, add_spec_story, add_symbols_story, add_trouble_story
from .params import IDPKG, param_pt
from .primitives import _ATTR_ENTITIES
from .character_metrics import with_character_baseline_shift
from .story_rhythm import (
    operation_key_visual_raise,
    operation_story_rhythm_for_next_block,
)

# Coarse story-chain estimates include paragraph gaps; they are deliberately
# independent from visible paragraph styles and their golden output.
_EST_SIZE = {"h1": 9.0, "h2": 8.6, "h3": 7.0, "label": 6.8}
_EST_LEADING = {"h1": 16.0, "h2": 12.0, "h3": 9.0, "label": 12.0}

def add_prose_story(writer, sid: str, title: str, blocks: list[tuple[str, str]],
                    bundle_root: Path, *,
                    inline_origin_shift: float = 0.0,
                    language: str | None = None) -> tuple[str, float]:
    """Story from extracted prose blocks; returns (sid, est_height_pt)."""
    parts: list[str] = []
    est = 0.0
    img_n = 0
    is_preface = title == "00_preface"
    content_indices = [i for i, (kind, _) in enumerate(blocks) if kind != "layout"]
    last_idx = content_indices[-1] if content_indices else -1
    in_twocol = False
    next_h1_page_top: float | None = None
    next_trouble_h1_language: str | None = None
    operation_intro_lines: int | None = None
    operation_energy_panel_height: float | None = None
    operation_h2_seen = False
    has_twocol_layout = any(kind == "layout" for kind, _ in blocks)
    first_h1 = next((text for kind, text in blocks if kind == "h1"), "")
    page_language = language or {
        "WARRANTY": "en",
        "GARANTIE": "fr",
        "GARANTÍA": "es",
    }.get(first_h1) or _flow.operation_language(blocks)
    text_measure = writer.page_w - writer.m_l - writer.m_r
    if is_preface:
        text_measure = writer.page_w - param_pt(
            writer.params, "idml_preface_margin_left", writer.m_l,
        ) - param_pt(writer.params, "idml_preface_margin_right", writer.m_r)
    column_measure = (text_measure - 11.0) / 2.0

    for bi, (kind, text) in enumerate(blocks):
        if kind == "layout":
            if text == "twocol_start":
                in_twocol = True
            elif text == "twocol_end":
                in_twocol = False
            elif text == "page_break" or text.startswith("page_break:"):
                page_break = writer._psr("HB Body", "")
                if ":" in text:
                    space_after = float(text.split(":", 1)[1])
                    page_break = page_break.replace(
                        "<ParagraphStyleRange ",
                        f'<ParagraphStyleRange SpaceAfter="{space_after:g}" ',
                        1,
                    )
                parts.append(_flow.start_next_page(page_break))
            elif text.startswith("next_h1_page_top:"):
                next_h1_page_top = float(text.split(":", 1)[1])
            elif text.startswith("trouble_h1_before:"):
                next_trouble_h1_language = text.split(":", 1)[1]
            continue
        terminal = bi == last_idx
        if kind == "component":
            import json as _json
            spec = _json.loads(text)
            span_columns = not in_twocol
            measure_w = column_measure if in_twocol else (text_measure if is_preface else None)
            xml_part, h = writer._render_component(
                sid, bi, spec, bundle_root, terminal,
                span_columns=span_columns, measure_w=measure_w,
                language=page_language,
                inline_origin_shift=inline_origin_shift)
            if xml_part:
                parts.append(xml_part)
                est += h
                if str(spec.get("layout") or "").strip().lower() == "energy_saving":
                    operation_energy_panel_height = h
            continue
        if kind == "table":
            import json as _json
            raw_rows = _json.loads(text)
            img_n += 1
            xml_part, h = _components.render_table_block(
                raw_rows,
                writer._render_context(
                    bundle_root,
                    language=page_language,
                    inline_origin_shift=inline_origin_shift,
                ),
                tid=f"{sid}_t{img_n}", terminal=terminal,
                span_columns=not in_twocol)
            xml_part = _flow.align_table_xml(xml_part, blocks, bi)
            parts.append(xml_part)
            est += h
            continue
        if kind == "image":
            xml_part, h = _components.render_image_block(
                text, writer._render_context(bundle_root),
                rect_id=f"{sid}_im{img_n + 1}", terminal=terminal)
            if xml_part is None:
                continue
            img_n += 1
            parts.append(xml_part)
            est += h
            continue
        if kind == "h1":
            h1_xml = _po.h1_pill_paragraph(writer, text, text_measure)
            if next_trouble_h1_language is not None:
                h1_xml = _flow.apply_troubleshooting_h1_rhythm(
                    h1_xml, writer.params, next_trouble_h1_language,
                )
                next_trouble_h1_language = None
            if next_h1_page_top is not None:
                offset = max(0.0, next_h1_page_top - writer.m_t)
                h1_xml = h1_xml.replace(
                    "<ParagraphStyleRange ",
                    f'<ParagraphStyleRange StartParagraph="NextPage" '
                    f'SpaceBefore="{offset:g}" ',
                    1,
                )
                next_h1_page_top = None
            parts.append(h1_xml)
            est += 24.0
            continue
        next_block = blocks[bi + 1] if bi + 1 < len(blocks) else ("", "")
        operation_h2 = kind in {"h2_operation_energy", "h2_operation_led"}
        overview_h2 = kind in {"h2_overview_front", "h2_overview_right"}
        semantic_kind = "h2" if overview_h2 or operation_h2 else kind
        if kind == "body_operation_energy_intro":
            semantic_kind = "body"
        style = writer._PROSE_STYLE.get(semantic_kind, "HB Body")
        if is_preface and kind == "body":
            style = "HB Preface Body"
        text = "\u25cf " + text if semantic_kind == "h2" else text
        span_columns = has_twocol_layout and not in_twocol and semantic_kind in {"h1", "h2"}
        paragraph = writer._psr(
            style, text, terminal=terminal, span_columns=span_columns)
        operation_attrs, operation_spacing = operation_story_rhythm_for_next_block(
            kind, next_block, page_language,
            title=title,
            intro_lines=operation_intro_lines,
            energy_panel_height=operation_energy_panel_height,
            baseline_panel_height=text_measure * 0.545 + 2.0,
            params=writer.params,
            first_operation_h2=(semantic_kind == "h2" and not operation_h2_seen),
        )
        if semantic_kind == "h2":
            operation_h2_seen = True
        if kind == "warrantynote":
            note_scale = param_pt(
                writer.params,
                f"lang_{page_language}_idml_warranty_note_horizontal_scale",
                param_pt(
                    writer.params,
                    "idml_warranty_note_horizontal_scale",
                    100.0,
                ),
            )
            paragraph = paragraph.replace(
                'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
                'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
                f'HorizontalScale="{note_scale:g}"',
                1,
            )
        if kind == "h2_overview_front":
            paragraph = paragraph.replace(
                "<ParagraphStyleRange ",
                '<ParagraphStyleRange SpaceBefore="5.19" SpaceAfter="10.66" '
                'LeftIndent="0.91" ',
                1,
            )
        elif kind == "h2_overview_right":
            paragraph = paragraph.replace(
                "<ParagraphStyleRange ",
                '<ParagraphStyleRange LeftIndent="0.91" ',
                1,
            )
            paragraph = paragraph.replace(
                'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
                'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
                'BaselineShift="-0.32"',
                1,
            )
            paragraph = _po.vertical_spacer_paragraph(
                f"spacer_{sid}_overview_right", 0.0) + paragraph
        if operation_attrs is not None:
            paragraph = paragraph.replace(
                "<ParagraphStyleRange ",
                f"<ParagraphStyleRange {operation_attrs} ",
                1,
            )
        key_visual_raise = operation_key_visual_raise(
            kind,
            next_block,
            page_language,
            writer.params,
        )
        if key_visual_raise:
            paragraph = with_character_baseline_shift(
                paragraph,
                shift=key_visual_raise,
            )
        parts.append(paragraph)
        # width-aware: chars/line ~ frame_width / (0.52 * font size)
        size = _EST_SIZE.get(semantic_kind, 6.2)
        leading = _EST_LEADING.get(semantic_kind, 7.5)
        if is_preface and kind == "body":
            size = param_pt(writer.params, "idml_preface_body_font_size", 7.2)
            leading = param_pt(writer.params, "idml_preface_body_font_leading", 8.6)
        elif kind == "body_operation_energy_intro":
            leading = 8.1
        measure = column_measure if in_twocol else text_measure
        per_line = max(20, int(measure / (0.52 * size)))
        lines = sum(max(1, (len(seg) + per_line - 1) // per_line)
                    for seg in text.split("\n"))
        paragraph_spacing = 0.0
        if is_preface and kind == "body":
            paragraph_spacing = param_pt(
                writer.params, "idml_preface_paragraph_space_after", 2.0,
            ) * len(text.split("\n"))
        if operation_spacing is not None:
            paragraph_spacing = operation_spacing
        if kind == "body_operation_energy_intro":
            operation_intro_lines = lines
        est += leading * lines + paragraph_spacing
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'<Story Self="{sid}" AppliedTOCStyle="n" TrackChanges="false" StoryTitle="{escape(title, _ATTR_ENTITIES)}">\n'
        '<StoryPreference OpticalMarginAlignment="false" FrameType="TextFrameType"/>\n'
        + "".join(parts) + '</Story>\n</idPkg:Story>\n'
    )
    writer.stories.append((sid, xml))
    return sid, est

def add_text_story(writer, sid: str, title: str, blocks: list[tuple[str, str]]) -> str:
    parts = [
        writer._psr(style, text, terminal=(i == len(blocks) - 1))
        for i, (style, text) in enumerate(blocks)
    ]
    return writer._add_story_parts(sid, title, parts)

def _add_story_parts(writer, sid: str, title: str, parts: list[str]) -> str:
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'<Story Self="{sid}" AppliedTOCStyle="n" TrackChanges="false" StoryTitle="{escape(title, _ATTR_ENTITIES)}">\n'
        '<StoryPreference OpticalMarginAlignment="false" FrameType="TextFrameType"/>\n'
        + "".join(parts) +
        '</Story>\n'
        '</idPkg:Story>\n'
    )
    writer.stories.append((sid, xml))
    return sid
