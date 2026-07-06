"""Story builders for the IDML exporter (componentization P3).

Each function takes the writer (geometry/params/primitives via its thin
delegates + the stories/spreads sinks) and appends the built story. Moved
verbatim from IdmlWriter — the golden byte-comparison pins equivalence.
"""
from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from . import components as _components
from .loaders import symbol_copy
from .params import IDPKG
from .primitives import _ATTR_ENTITIES

ROOT = Path(__file__).resolve().parents[2]


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
        span_columns = has_twocol_layout and not in_twocol and kind in {"h1", "h2"}
        parts.append(writer._psr(
            style, text, terminal=terminal, span_columns=span_columns))
        # width-aware: chars/line ~ frame_width / (0.52 * font size)
        size = {"h1": 9.0, "h2": 8.6, "h3": 7.0, "label": 6.8}.get(kind, 6.2)
        leading = {"h1": 16.0, "h2": 12.0, "h3": 9.0, "label": 12.0}.get(kind, 7.5)
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
            ('  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Figure">'
             '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
             + img + '<Content></Content></CharacterStyleRange></ParagraphStyleRange>\n', 1),
            (writer._psr("HB Spec Label", row["name"], terminal=True), 2),
            (writer._psr("HB Spec Value", row["desc"], terminal=True), 3),
        )
        for content, ci in cell_defs:
            cells.append(
                f'    <Cell Self="{tid}c{ri}_{ci}" Name="{ci}:{ri}" RowSpan="1" ColumnSpan="1" '
                'AppliedCellStyle="CellStyle/$ID/[None]" '
                'TopInset="2" BottomInset="2" LeftInset="3" RightInset="3">\n'
                + content + '    </Cell>'
            )
    row_els = "\n".join(
        f'    <Row Self="{tid}r{ri}" Name="{ri}"/>' for ri in range(len(rows))
    )
    col_els = "\n".join(
        f'    <Column Self="{tid}col{ci}" Name="{ci}" SingleColumnWidth="{wd:g}"/>'
        for ci, wd in enumerate(cols)
    )
    table = (
        f'  <Table Self="{tid}" AppliedTableStyle="TableStyle/$ID/[Basic Table]" '
        f'BodyRowCount="{len(rows)}" ColumnCount="{len(cols)}" HeaderRowCount="0" FooterRowCount="0">\n'
        f'{row_els}\n{col_els}\n' + "\n".join(cells) + "\n  </Table>\n"
    )
    parts = [
        writer._psr("HB H1", "LCD DISPLAY"),
        '  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Body">\n'
        '    <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">\n'
        + table +
        '    <Content></Content></CharacterStyleRange>\n'
        '  </ParagraphStyleRange>\n',
    ]
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'<Story Self="{sid}" AppliedTOCStyle="n" TrackChanges="false" StoryTitle="LCD DISPLAY">\n'
        '<StoryPreference OpticalMarginAlignment="false" FrameType="TextFrameType"/>\n'
        + "".join(parts) + '</Story>\n</idPkg:Story>\n'
    )
    writer.stories.append((sid, xml))
    return sid

def add_symbols_story(writer, signals: list[tuple[str, str]],
                      icons: list[dict], data_root: Path, lang: str = "en") -> str:
    sid = "st_symbols"
    copy = symbol_copy(lang)
    parts = [writer._psr("HB H1", copy["title"])]
    if signals:
        table = writer._table("tbl_sym_sig", signals, label_style="HB Notice Label")
        parts.append(
            '  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Body">\n'
            '    <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">\n'
            + table + '    <Br/></CharacterStyleRange>\n  </ParagraphStyleRange>\n')
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
            img_cell = (
                '  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Figure">'
                '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
                + img + '<Content></Content></CharacterStyleRange></ParagraphStyleRange>\n')
            for ci, content in ((0, img_cell),
                                (1, writer._psr("HB Spec Value", row["text"], terminal=True))):
                cells.append(
                    f'    <Cell Self="{tid}c{ri}_{ci}" Name="{ci}:{ri}" RowSpan="1" ColumnSpan="1" '
                    'AppliedCellStyle="CellStyle/$ID/[None]" '
                    'TopInset="2" BottomInset="2" LeftInset="3" RightInset="3">\n'
                    + content + '    </Cell>')
        row_els = "\n".join(f'    <Row Self="{tid}r{ri}" Name="{ri}"/>' for ri in range(len(icons)))
        col_els = "\n".join(
            f'    <Column Self="{tid}col{ci}" Name="{ci}" SingleColumnWidth="{wd:g}"/>'
            for ci, wd in enumerate(cols))
        table2 = (
            f'  <Table Self="{tid}" AppliedTableStyle="TableStyle/$ID/[Basic Table]" '
            f'BodyRowCount="{len(icons)}" ColumnCount="2" HeaderRowCount="0" FooterRowCount="0">\n'
            f'{row_els}\n{col_els}\n' + "\n".join(cells) + "\n  </Table>\n")
        parts.append(
            '  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Body">\n'
            '    <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">\n'
            + table2 + '    <Content></Content></CharacterStyleRange>\n  </ParagraphStyleRange>\n')
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'<Story Self="{sid}" AppliedTOCStyle="n" TrackChanges="false" StoryTitle="MEANING OF SYMBOLS">\n'
        '<StoryPreference OpticalMarginAlignment="false" FrameType="TextFrameType"/>\n'
        + "".join(parts) + '</Story>\n</idPkg:Story>\n'
    )
    writer.stories.append((sid, xml))
    return sid

def add_trouble_story(writer, rows: list[tuple[str, str]]) -> str:
    sid = "st_trouble"
    parts = [writer._psr("HB H1", "TROUBLESHOOTING")]
    table = writer._table("tbl_trouble", rows)
    parts.append(
        '  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Body">\n'
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
        table = writer._table(f"tbl_spec{si}", sec["rows"])
        last = si == len(sections) - 1 and not annotations
        parts.append(
            '  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Body">\n'
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
