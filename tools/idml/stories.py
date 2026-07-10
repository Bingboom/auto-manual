"""Story builders for the IDML exporter (componentization P3).

Each function takes the writer (geometry/params/primitives via its thin
delegates + the stories/spreads sinks) and appends the built story. Moved
verbatim from IdmlWriter — the golden byte-comparison pins equivalence.
"""
from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from . import components as _components, page_objects as _po
from . import table_borders as _tb
from .loaders import symbol_copy
from .params import IDPKG
from .primitives import _ATTR_ENTITIES
from .style_names import paragraph_style_ref

ROOT = Path(__file__).resolve().parents[2]

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
    content_indices = [i for i, (kind, _) in enumerate(blocks) if kind != "layout"]
    last_idx = content_indices[-1] if content_indices else -1
    in_twocol = False
    has_twocol_layout = any(kind == "layout" for kind, _ in blocks)
    text_measure = writer.page_w - writer.m_l - writer.m_r
    column_measure = (text_measure - 11.0) / 2.0
    for bi, (kind, text) in enumerate(blocks):
        if kind == "layout":
            if text == "twocol_start":
                in_twocol = True
            elif text == "twocol_end":
                in_twocol = False
            continue
        terminal = bi == last_idx
        if kind == "component":
            import json as _json
            spec = _json.loads(text)
            span_columns = not in_twocol
            measure_w = column_measure if in_twocol else None
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
        style = writer._PROSE_STYLE.get(kind, "HB Body")
        text = "\u25cf " + text if kind == "h2" else text
        span_columns = has_twocol_layout and not in_twocol and kind in {"h1", "h2"}
        parts.append(writer._psr(
            style, text, terminal=terminal, span_columns=span_columns))
        # width-aware: chars/line ~ frame_width / (0.52 * font size)
        size = _EST_SIZE.get(kind, 6.2)
        leading = _EST_LEADING.get(kind, 7.5)
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

def add_lcd_story(writer, rows: list[dict], data_root: Path) -> str:
    """LCD icon table: circled-no / icon image / name / description."""
    sid = "st_lcd"
    body_w = writer.page_w - writer.m_l - writer.m_r
    cols = (body_w * 0.08, body_w * 0.12, body_w * 0.28, body_w * 0.52)
    tid = "tbl_lcd"
    cells = []
    icon_pt = 24.0
    for ri, row in enumerate(rows):
        # figure paths are repo-relative in both live and fixture snapshots
        fig = (ROOT / row["figure"]) if row["figure"] else None
        img = (writer._image_cell_content(f"{tid}img{ri}", fig, icon_pt, icon_pt)
               if fig and fig.exists() else "")
        cell_defs = (
            (writer._psr("HB Spec Label", row["no"], terminal=True), 0),
            (_components.figure_paragraph(img, tail="<Content></Content>"), 1),
            (writer._psr("HB Spec Label", row["name"], terminal=True), 2),
            (writer._psr("HB Spec Value", row["desc"], terminal=True), 3),
        )
        for content, ci in cell_defs:
            cells.append(writer._cell(f"{tid}c{ri}_{ci}", f"{ci}:{ri}", content,
                                      top=2, bottom=2, left=3, right=3))
    table = _tb.fill_column_xml(writer._component_table(tid, list(cols), cells, n_rows=len(rows), role="data"), 1, "Color/HB Bg K05")
    parts = [
        writer._psr("HB H1", "LCD DISPLAY"),
        _po.lcd_hero_paragraph(writer),
        writer._wrap_table_paragraph(table, True, span_columns=False),
    ]
    return writer._add_story_parts(sid, "LCD DISPLAY", parts)

def add_symbols_story(writer, signals: list[tuple[str, str]],
                      icons: list[dict], data_root: Path, lang: str = "en") -> str:
    sid = "st_symbols"
    copy = symbol_copy(lang)
    parts = [writer._psr("HB H1", copy["title"])]
    if signals:
        table = writer._table("tbl_sym_sig", signals, label_style="HB Notice Label", role="data")
        parts.append(writer._wrap_table_paragraph(table, False, span_columns=False))
    if icons:
        body_w = writer.page_w - writer.m_l - writer.m_r
        cols = (body_w * 0.18, body_w * 0.82)
        tid = "tbl_sym_ico"
        cells = []
        icon_pt = 20.0
        for ri, row in enumerate(icons):
            fig = (ROOT / row["figure"]) if row["figure"] else None
            img = (writer._image_cell_content(f"{tid}img{ri}", fig, icon_pt, icon_pt)
                   if fig and fig.exists() else "")
            img_cell = _components.figure_paragraph(img, tail="<Content></Content>")
            for ci, content in ((0, img_cell),
                                (1, writer._psr("HB Spec Value", row["text"], terminal=True))):
                cells.append(writer._cell(f"{tid}c{ri}_{ci}", f"{ci}:{ri}", content,
                                          top=2, bottom=2, left=3, right=3))
        table2 = writer._component_table(tid, list(cols), cells, n_rows=len(icons), role="data")
        parts.append(writer._wrap_table_paragraph(table2, True, span_columns=False))
    return writer._add_story_parts(sid, "MEANING OF SYMBOLS", parts)

def add_trouble_story(writer, rows: list[tuple[str, str]]) -> str:
    sid = "st_trouble"
    parts = [writer._psr("HB H1", "TROUBLESHOOTING")]
    table = writer._table("tbl_trouble", rows, role="data")
    body_style_ref = paragraph_style_ref("HB Body")
    parts.append(
        f'  <ParagraphStyleRange AppliedParagraphStyle="{body_style_ref}">\n'
        '    <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">\n'
        + table +
        '    <Content></Content></CharacterStyleRange>\n'
        '  </ParagraphStyleRange>\n'
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'<Story Self="{sid}" AppliedTOCStyle="n" TrackChanges="false" StoryTitle="TROUBLESHOOTING">\n'
        '<StoryPreference OpticalMarginAlignment="false" FrameType="TextFrameType"/>\n'
        + "".join(parts) + '</Story>\n</idPkg:Story>\n'
    )
    writer.stories.append((sid, xml))
    return sid

def add_spec_story(writer, sections: list[dict],
                   annotations: list[str] | None = None) -> str:
    sid = "st_spec"
    parts = [writer._psr("HB H1", "SPECIFICATIONS")]
    for si, sec in enumerate(sections):
        parts.append(writer._psr("HB Spec Section", sec["title"]))
        # table anchored in its own paragraph; the paragraph still needs
        # its own <Br/> so the next section title starts a new paragraph
        table = _tb.suppress_inner_vertical_edges_xml(
            writer._table(f"tbl_spec{si}", sec["rows"], role="spec"), 2)
        last = si == len(sections) - 1 and not annotations
        body_style_ref = paragraph_style_ref("HB Body")
        parts.append(
            f'  <ParagraphStyleRange AppliedParagraphStyle="{body_style_ref}">\n'
            '    <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">\n'
            + table +
            ('    <Content></Content></CharacterStyleRange>\n' if last else
             '    <Br/></CharacterStyleRange>\n')
            + '  </ParagraphStyleRange>\n'
        )
    # footnotes + notes under the tables (master parity)
    for ai, note in enumerate(annotations or []):
        parts.append(writer._psr("HB Spec Note", note,
                               terminal=(ai == len(annotations) - 1)))
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'<Story Self="{sid}" AppliedTOCStyle="n" TrackChanges="false" StoryTitle="SPECIFICATIONS">\n'
        '<StoryPreference OpticalMarginAlignment="false" FrameType="TextFrameType"/>\n'
        + "".join(parts) +
        '</Story>\n'
        '</idPkg:Story>\n'
    )
    writer.stories.append((sid, xml))
    return sid

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
