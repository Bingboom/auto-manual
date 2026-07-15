"""Story builders whose golden byte-comparison pins IDML equivalence."""
from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from . import components as _components, page_objects as _po, prose_flow as _flow
from .data_stories import (
    add_lcd_story,
    add_spec_story,
    add_symbols_story,
    add_trouble_story,
)
from .params import IDPKG
from .params import param_pt
from .primitives import _ATTR_ENTITIES

# Height-ESTIMATION constants for sizing the linked spread chain. These are
# deliberately NOT the paragraph-style sizes/leadings from styles.para_styles
# (the leadings here include inter-paragraph spacing, and estimation is
# intentionally coarse: an underestimate surfaces as InDesign overset — one
# drag — while an overestimate leaves trailing blank pages). Do not "unify"
# them with the style table without regenerating the golden deliberately.
_EST_SIZE = {"h1": 9.0, "h2": 8.6, "h3": 7.0, "label": 6.8}
_EST_LEADING = {"h1": 16.0, "h2": 12.0, "h3": 9.0, "label": 12.0}

def add_prose_story(writer, sid: str, title: str, blocks: list[tuple[str, str]],
                    bundle_root: Path) -> tuple[str, float]:
    """Story from extracted prose blocks; returns (sid, est_height_pt)."""
    parts: list[str] = []
    est = 0.0
    img_n = 0
    is_preface = title == "00_preface"
    content_indices = [i for i, (kind, _) in enumerate(blocks) if kind != "layout"]
    last_idx = content_indices[-1] if content_indices else -1
    in_twocol = False
    next_h1_page_top: float | None = None
    has_twocol_layout = any(kind == "layout" for kind, _ in blocks)
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
            elif text == "page_break": parts.append(_flow.start_next_page(writer._psr("HB Body", "")))
            elif text.startswith("next_h1_page_top:"):
                next_h1_page_top = float(text.split(":", 1)[1])
            continue
        terminal = bi == last_idx
        if kind == "component":
            import json as _json
            spec = _json.loads(text)
            span_columns = not in_twocol
            measure_w = column_measure if in_twocol else (text_measure if is_preface else None)
            xml_part, h = writer._render_component(
                sid, bi, spec, bundle_root, terminal,
                span_columns=span_columns, measure_w=measure_w)
            if xml_part:
                parts.append(xml_part)
                est += h
            continue
        if kind == "table":
            import json as _json
            raw_rows = _json.loads(text)
            img_n += 1
            xml_part, h = _components.render_table_block(
                raw_rows, writer._render_context(bundle_root),
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
        overview_h2 = kind in {"h2_overview_front", "h2_overview_right"}
        semantic_kind = "h2" if overview_h2 else kind
        style = writer._PROSE_STYLE.get(semantic_kind, "HB Body")
        if is_preface and kind == "body":
            style = "HB Preface Body"
        text = "\u25cf " + text if semantic_kind == "h2" else text
        span_columns = has_twocol_layout and not in_twocol and kind in {"h1", "h2"}
        paragraph = writer._psr(
            style, text, terminal=terminal, span_columns=span_columns)
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
        parts.append(paragraph)
        # width-aware: chars/line ~ frame_width / (0.52 * font size)
        size = _EST_SIZE.get(semantic_kind, 6.2)
        leading = _EST_LEADING.get(semantic_kind, 7.5)
        if is_preface and kind == "body":
            size = param_pt(writer.params, "idml_preface_body_font_size", 7.2)
            leading = param_pt(writer.params, "idml_preface_body_font_leading", 8.6)
        measure = column_measure if in_twocol else text_measure
        per_line = max(20, int(measure / (0.52 * size)))
        lines = sum(max(1, (len(seg) + per_line - 1) // per_line)
                    for seg in text.split("\n"))
        est += leading * lines
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
