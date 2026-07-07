"""Section part-builders for the IDML exporter.

Each builder returns the ParagraphStyleRange XML fragments (``parts``) for one
section, WITHOUT wrapping them in a Story envelope. Two consumers:

- ``idml.stories`` wraps a single builder's parts into a standalone per-page
  story (composed mode).
- ``idml.flow`` concatenates every builder's parts into one book-length story
  (single-flow mode).

``terminal_last`` controls whether the final paragraph omits its trailing
<Br/>: True for a standalone story, False when the parts feed a larger flow so
the next section cannot fuse onto this one.

Split out of ``idml.stories`` so that story-flow growth lands here (an
unpinned module) rather than pushing the guardrailed façade files up.
"""
from __future__ import annotations

from pathlib import Path

from . import components as _components
from .loaders import symbol_copy
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


def prose_blocks_to_parts(writer, sid: str, blocks: list[tuple[str, str]],
                          bundle_root: Path, *,
                          terminal_last: bool = True) -> tuple[list[str], float]:
    """Extracted prose blocks -> (parts, est_height_pt)."""
    parts: list[str] = []
    est = 0.0
    img_n = 0
    content_indices = [i for i, (kind, _) in enumerate(blocks) if kind != "layout"]
    last_idx = content_indices[-1] if (content_indices and terminal_last) else -1
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
        size = _EST_SIZE.get(kind, 6.2)
        leading = _EST_LEADING.get(kind, 7.5)
        measure = column_measure if in_twocol else text_measure
        per_line = max(20, int(measure / (0.52 * size)))
        lines = sum(max(1, (len(seg) + per_line - 1) // per_line)
                    for seg in text.split("\n"))
        est += leading * lines
    return parts, est


def lcd_parts(writer, rows: list[dict], *, tid: str = "tbl_lcd",
              terminal_last: bool = True) -> list[str]:
    body_w = writer.page_w - writer.m_l - writer.m_r
    cols = (body_w * 0.08, body_w * 0.12, body_w * 0.28, body_w * 0.52)
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
    table = writer._component_table(tid, list(cols), cells, n_rows=len(rows))
    return [
        writer._psr("HB H1", "LCD DISPLAY"),
        writer._wrap_table_paragraph(table, terminal_last, span_columns=False),
    ]


def symbols_parts(writer, signals: list[tuple[str, str]], icons: list[dict],
                  lang: str = "en", *, sig_tid: str = "tbl_sym_sig",
                  ico_tid: str = "tbl_sym_ico", terminal_last: bool = True,
                  icon_chunk_size: int | None = None,
                  flow_friendly: bool = False) -> list[str]:
    copy = symbol_copy(lang)
    parts = [writer._psr("HB H1", copy["title"])]
    if flow_friendly:
        for label, meaning in signals:
            parts.append(writer._psr("HB Notice Label", label))
            parts.append(writer._psr("HB Spec Value", meaning))
        for ri, row in enumerate(icons):
            fig = (ROOT / row["figure"]) if row["figure"] else None
            if fig and fig.exists():
                img = writer._image_cell_content(f"{ico_tid}img{ri}", fig, 20.0, 20.0)
                parts.append(_components.figure_paragraph(img))
            parts.append(writer._psr(
                "HB Spec Value", row["text"],
                terminal=terminal_last and ri == len(icons) - 1))
        return parts
    if signals:
        table = writer._table(sig_tid, signals, label_style="HB Notice Label")
        # signals table is never the terminal element (a trailing <Br/> keeps
        # the icon table or the flow's next section on its own paragraph)
        parts.append(writer._wrap_table_paragraph(table, False, span_columns=False))
    if icons:
        body_w = writer.page_w - writer.m_l - writer.m_r
        cols = (body_w * 0.18, body_w * 0.82)
        icon_pt = 20.0
        chunk_size = icon_chunk_size or len(icons)
        for chunk_start in range(0, len(icons), chunk_size):
            chunk = icons[chunk_start:chunk_start + chunk_size]
            chunk_tid = ico_tid if len(icons) == len(chunk) else f"{ico_tid}_{chunk_start}"
            cells = []
            for ri, row in enumerate(chunk):
                src_ri = chunk_start + ri
                fig = (ROOT / row["figure"]) if row["figure"] else None
                img = (writer._image_cell_content(f"{chunk_tid}img{src_ri}", fig, icon_pt, icon_pt)
                       if fig and fig.exists() else "")
                img_cell = _components.figure_paragraph(img, tail="<Content></Content>")
                for ci, content in (
                    (0, img_cell),
                    (1, writer._psr("HB Spec Value", row["text"], terminal=True)),
                ):
                    cells.append(writer._cell(
                        f"{chunk_tid}c{ri}_{ci}", f"{ci}:{ri}", content,
                        top=2, bottom=2, left=3, right=3))
            table2 = writer._component_table(chunk_tid, list(cols), cells, n_rows=len(chunk))
            is_last_chunk = chunk_start + chunk_size >= len(icons)
            parts.append(writer._wrap_table_paragraph(
                table2, terminal_last and is_last_chunk, span_columns=False))
    return parts


def trouble_parts(writer, rows: list[tuple[str, str]], *, tid: str = "tbl_trouble",
                  terminal_last: bool = True) -> list[str]:
    parts = [writer._psr("HB H1", "TROUBLESHOOTING")]
    table = writer._table(tid, rows)
    body_style_ref = paragraph_style_ref("HB Body")
    tail = ('    <Content></Content></CharacterStyleRange>\n' if terminal_last
            else '    <Br/></CharacterStyleRange>\n')
    parts.append(
        f'  <ParagraphStyleRange AppliedParagraphStyle="{body_style_ref}">\n'
        '    <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">\n'
        + table + tail
        + '  </ParagraphStyleRange>\n'
    )
    return parts


def spec_parts(writer, sections: list[dict], annotations: list[str] | None = None,
               *, tid_prefix: str = "tbl_spec", terminal_last: bool = True) -> list[str]:
    parts = [writer._psr("HB H1", "SPECIFICATIONS")]
    for si, sec in enumerate(sections):
        parts.append(writer._psr("HB Spec Section", sec["title"]))
        # table anchored in its own paragraph; the paragraph still needs
        # its own <Br/> so the next section title starts a new paragraph
        table = writer._table(f"{tid_prefix}{si}", sec["rows"])
        last = terminal_last and si == len(sections) - 1 and not annotations
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
                               terminal=(terminal_last and ai == len(annotations) - 1)))
    return parts
