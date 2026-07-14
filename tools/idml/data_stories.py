"""LCD, symbols, troubleshooting, and specification story builders."""
from __future__ import annotations

from pathlib import Path

from . import components as _components
from . import lcd_style as _lcd
from . import page_objects as _po
from . import table_borders as _tb
from .loaders import symbol_copy
from .params import IDPKG
from .style_names import paragraph_style_ref

ROOT = Path(__file__).resolve().parents[2]


def add_lcd_story(writer, rows: list[dict], data_root: Path,
                  lang: str = "en", title: str = "LCD DISPLAY") -> str:
    """LCD icon table: circled-no / icon image / name / description."""
    sid = "st_lcd" if lang == "en" else f"st_lcd_{lang}"
    body_w = writer.page_w - writer.m_l - writer.m_r
    table_indent = _lcd.table_left_indent(writer)
    cols, icon_pt, pad = _lcd.layout_tokens(writer, body_w - table_indent)
    if lang == "en":
        icon_pt = min(icon_pt, 23.0)
        cols = (cols[0] + 7.04, cols[1], cols[2], cols[3] - 7.04)
    tid = "tbl_lcd" if lang == "en" else f"tbl_lcd_{lang}"
    cells = []

    for ri, row in enumerate(rows):
        fig = (ROOT / row["figure"]) if row["figure"] else None
        image = (
            writer._image_cell_content(f"{tid}img{ri}", fig, icon_pt, icon_pt)
            if fig and fig.exists() else ""
        )
        image_paragraph = _components.figure_paragraph(
            image, tail="<Content></Content>")
        image_paragraph = image_paragraph.replace(
            'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
            'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
            'BaselineShift="0.6"',
            1,
        )
        cell_defs = (
            (_lcd.typed_paragraph(
                writer, "HB Spec Label", row["no"],
                "type_lcd_no_font_size", "type_lcd_no_font_leading",
                font="Apple SD Gothic Neo"), 0),
            (image_paragraph, 1),
            (_lcd.typed_paragraph(
                writer, "HB Spec Label", row["name"],
                "type_lcd_label_font_size", "type_lcd_label_font_leading",
                bold=True), 2),
            (_lcd.typed_paragraph(
                writer, "HB Spec Value", row["desc"],
                "type_lcd_body_font_size", "type_lcd_body_font_leading"), 3),
        )
        for content, ci in cell_defs:
            cells.append(writer._cell(
                f"{tid}c{ri}_{ci}", f"{ci}:{ri}", content,
                top=pad, bottom=pad, left=pad, right=pad,
                valign="CenterAlign"))
    table = writer._component_table(
        tid, list(cols), cells, n_rows=len(rows), role="data")
    for column in range(3):
        table = _tb.fill_column_xml(table, column, "Color/HB Bg K05")
    table_paragraph = writer._wrap_table_paragraph(
        table, True, span_columns=False)
    table_paragraph = table_paragraph.replace(
        "<ParagraphStyleRange ",
        f'<ParagraphStyleRange LeftIndent="{table_indent:g}" ',
        1,
    )
    parts = [
        _po.h1_pill_paragraph(
            writer, title, writer.page_w - writer.m_l - writer.m_r),
        _po.lcd_hero_paragraph(writer),
        table_paragraph,
    ]
    return writer._add_story_parts(sid, title, parts)


def add_symbols_story(writer, signals: list[tuple[str, str]],
                      icons: list[dict], data_root: Path,
                      lang: str = "en") -> str:
    sid = "st_symbols"
    copy = symbol_copy(lang)
    parts = [_po.h1_pill_paragraph(
        writer, copy["title"], writer.page_w - writer.m_l - writer.m_r)]
    if signals:
        table = writer._table(
            "tbl_sym_sig", signals, label_style="HB Notice Label", role="data")
        parts.append(writer._wrap_table_paragraph(
            table, False, span_columns=False))
    if icons:
        body_w = writer.page_w - writer.m_l - writer.m_r
        cols = (body_w * 0.18, body_w * 0.82)
        tid = "tbl_sym_ico"
        cells = []
        icon_pt = 20.0
        for ri, row in enumerate(icons):
            fig = (ROOT / row["figure"]) if row["figure"] else None
            image = (
                writer._image_cell_content(f"{tid}img{ri}", fig, icon_pt, icon_pt)
                if fig and fig.exists() else ""
            )
            image_cell = _components.figure_paragraph(
                image, tail="<Content></Content>")
            for ci, content in (
                (0, image_cell),
                (1, writer._psr("HB Spec Value", row["text"], terminal=True)),
            ):
                cells.append(writer._cell(
                    f"{tid}c{ri}_{ci}", f"{ci}:{ri}", content,
                    top=2, bottom=2, left=3, right=3))
        table = writer._component_table(
            tid, list(cols), cells, n_rows=len(icons), role="data")
        parts.append(writer._wrap_table_paragraph(
            table, True, span_columns=False))
    return writer._add_story_parts(sid, "MEANING OF SYMBOLS", parts)


def add_trouble_story(writer, rows: list[tuple[str, str]]) -> str:
    sid = "st_trouble"
    parts = [_po.h1_pill_paragraph(
        writer, "TROUBLESHOOTING", writer.page_w - writer.m_l - writer.m_r)]
    table = writer._table("tbl_trouble", rows, role="data")
    body_style_ref = paragraph_style_ref("HB Body")
    parts.append(
        f'  <ParagraphStyleRange AppliedParagraphStyle="{body_style_ref}">\n'
        '    <CharacterStyleRange '
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">\n'
        + table
        + '    <Content></Content></CharacterStyleRange>\n'
        '  </ParagraphStyleRange>\n'
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'<Story Self="{sid}" AppliedTOCStyle="n" TrackChanges="false" '
        'StoryTitle="TROUBLESHOOTING">\n'
        '<StoryPreference OpticalMarginAlignment="false" '
        'FrameType="TextFrameType"/>\n'
        + "".join(parts)
        + '</Story>\n</idPkg:Story>\n'
    )
    writer.stories.append((sid, xml))
    return sid


def add_spec_story(writer, sections: list[dict],
                   annotations: list[str] | None = None,
                   lang: str = "en", title: str = "SPECIFICATIONS") -> str:
    sid = "st_spec" if lang == "en" else f"st_spec_{lang}"
    parts = [_po.h1_pill_paragraph(
        writer, title, writer.page_w - writer.m_l - writer.m_r)]
    english_table_heights = (98.41, 49.06, 94.89, 27.11)
    english_section_before = (7.89, 9.56, 10.54, 14.41)
    english_table_before = (3.79, 2.47, 4.75, 3.30)
    for si, section in enumerate(sections):
        section_title = writer._psr(
            "HB Spec Section", "\u25cf " + section["title"])
        section_before = (
            english_section_before[si]
            if lang == "en" and si < len(english_section_before)
            else 8.87 if si == 0 else 13.47 if si == 3 else 10.07
        )
        section_title = section_title.replace(
            "<ParagraphStyleRange ",
            f'<ParagraphStyleRange SpaceBefore="{section_before:g}" '
            f'LeftIndent="{4.18 if lang == "en" else 0.74:g}" ',
            1,
        )
        if lang == "en":
            section_title = section_title.replace(
                'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
                'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
                'BaselineShift="0.78"',
            )
        parts.append(section_title)
        table = _tb.fill_column_xml(
            _tb.suppress_inner_vertical_edges_xml(
                writer._table(
                    f"tbl_spec_{lang}{si}", section["rows"], role="spec",
                    visual_parity=(lang == "en"),
                ),
                2,
            ),
            0,
            "Color/HB Bg K05",
        )
        last = si == len(sections) - 1 and not annotations
        if lang == "en" and si < len(english_table_heights):
            table = _tb.suppress_outer_edges_xml(table, 2)
            inner = writer._wrap_table_paragraph(
                table, True, span_columns=False)
            panel = _po.anchored_panel_group_paragraph(
                writer._add_story_parts,
                f"st_anchor_spec_{lang}{si}",
                f"{section['title']} specification table",
                [inner],
                writer.page_w - writer.m_l - writer.m_r + 0.35,
                english_table_heights[si],
                terminal=last,
                fill="Color/Paper",
                stroke="Color/HB Brand Dark",
                stroke_weight=0.75,
                radius=6.8,
            )
            panel = panel.replace(
                "<ParagraphStyleRange ",
                f'<ParagraphStyleRange SpaceBefore="{english_table_before[si]:g}" ',
                1,
            )
            parts.append(panel)
            continue
        body_style_ref = paragraph_style_ref("HB Body")
        parts.append(
            f'  <ParagraphStyleRange AppliedParagraphStyle="{body_style_ref}">\n'
            '    <CharacterStyleRange '
            'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">\n'
            + table
            + ('    <Content></Content></CharacterStyleRange>\n' if last else
               '    <Br/></CharacterStyleRange>\n')
            + '  </ParagraphStyleRange>\n'
        )
    for ai, note in enumerate(annotations or []):
        note_xml = writer._psr(
            "HB Spec Note", note,
            terminal=(ai == len(annotations) - 1),
        )
        if lang == "en":
            note_xml = note_xml.replace(
                "<ParagraphStyleRange ",
                '<ParagraphStyleRange LeftIndent="-2.15" '
                'FirstLineIndent="-2.15" '
                f'SpaceBefore="{10.34 if ai == 0 else 4.57:g}" ',
                1,
            )
        parts.append(note_xml)
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'<Story Self="{sid}" AppliedTOCStyle="n" TrackChanges="false" '
        f'StoryTitle="{title}">\n'
        '<StoryPreference OpticalMarginAlignment="false" '
        'FrameType="TextFrameType"/>\n'
        + "".join(parts)
        + '</Story>\n'
        '</idPkg:Story>\n'
    )
    writer.stories.append((sid, xml))
    return sid
