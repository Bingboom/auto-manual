"""IDML exporter — route B of the InDesign handoff plan.

Produces an editable .idml (InDesign Markup Language) package so designers
can fine-tune pipeline output in InDesign instead of retouching PDFs:

- page geometry and paragraph styles are mapped 1:1 from data/layout_params.csv
- brand colors are emitted as CMYK swatches (from the brand_color_* keys)
- the SPECIFICATIONS page is exported as real IDML tables fed straight from
  the phase2 Spec_Master snapshot (section titles + label/value rows)
- body sections flow through linked text frames so InDesign reflows freely

MVP scope (M1-M3): valid package + style system + spec tables/story.
Not yet covered: image frames, two-column safety layout, full page set.

Usage:
  python tools/export_idml.py --model JE-1000F --region US [--lang en]
      [--data-root data/phase2] [--out docs/_build/.../manual.idml]
  python tools/export_idml.py --check <file.idml>   # structural validation
"""
from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

try:
    from tools.idml_rst_extract import bundle_page_order, extract_page
    from tools.script_bootstrap import bootstrap_repo_root
    from tools.idml import check as _check
    from tools.idml import components as _components
    from tools.idml import loaders as _loaders
    from tools.idml import params as _params
    from tools.idml import primitives as _prim
    from tools.idml import styles as _styles
except ImportError:  # pragma: no cover - direct script execution fallback
    from idml_rst_extract import bundle_page_order, extract_page  # type: ignore
    from script_bootstrap import bootstrap_repo_root
    from idml import check as _check  # type: ignore
    from idml import components as _components  # type: ignore
    from idml import loaders as _loaders  # type: ignore
    from idml import params as _params  # type: ignore
    from idml import primitives as _prim  # type: ignore
    from idml import styles as _styles  # type: ignore

ROOT = bootstrap_repo_root(__file__, parent_count=1)

MIMETYPE = _params.MIMETYPE
IDPKG = _params.IDPKG
MM_TO_PT = _params.MM_TO_PT
load_layout_params = _params.load_layout_params
param_pt = _params.param_pt
brand_cmyk = _params.brand_cmyk

SYMBOL_COPY = _loaders.SYMBOL_COPY
normalize_lang = _loaders.normalize_lang
symbol_copy = _loaders.symbol_copy
load_spec_sections = _loaders.load_spec_sections
load_lcd_rows = _loaders.load_lcd_rows
load_spec_annotations = _loaders.load_spec_annotations
load_symbols_rows = _loaders.load_symbols_rows
load_trouble_rows = _loaders.load_trouble_rows

check_idml = _check.check_idml


# ---------------------------------------------------------------------------
# IDML package writer
# ---------------------------------------------------------------------------

class IdmlWriter:
    def __init__(self, params: dict[str, tuple[str, str]]):
        self.params = params
        self.page_w = param_pt(params, "page_paperwidth", 368.79)
        self.page_h = param_pt(params, "page_paperheight", 524.69)
        self.m_l = param_pt(params, "page_margin_left", 28.35)
        self.m_r = param_pt(params, "page_margin_right", 28.35)
        self.m_t = param_pt(params, "page_margin_top", 14.17)
        self.m_b = param_pt(params, "page_margin_bottom", 36.85)
        self.stories: list[tuple[str, str]] = []   # (id, xml)
        self.spreads: list[tuple[str, str]] = []

    # -- styles ------------------------------------------------------------
    def para_styles(self) -> list[tuple[str, float, float, str, str]]:
        return _styles.para_styles(self.params)

    def styles_xml(self) -> str:
        return _styles.styles_xml(self.params)

    def graphic_xml(self) -> str:
        return _styles.graphic_xml(self.params)

    def fonts_xml(self) -> str:
        return _styles.fonts_xml()

    def preferences_xml(self) -> str:
        return _styles.preferences_xml(page_w=self.page_w, page_h=self.page_h,
                                       m_t=self.m_t, m_b=self.m_b,
                                       m_l=self.m_l, m_r=self.m_r)

    # -- content -----------------------------------------------------------

    GLYPH_FALLBACKS = _prim.GLYPH_FALLBACKS

    @classmethod
    def _clean_text(cls, text: str) -> str:
        return _prim.clean_text(text)

    @classmethod
    def _psr(cls, style: str, text: str, *, terminal: bool = False,
             span_columns: bool = False) -> str:
        return _prim.psr(style, text, terminal=terminal, span_columns=span_columns)

    @staticmethod
    def _bold_runs(line: str) -> list[tuple[str, bool]]:
        return _prim.bold_runs(line)

    def _table(self, tid: str, rows: list[tuple[str, str]],
               label_style: str = "HB Spec Label") -> str:
        return _prim.spec_table(tid, rows, label_style, params=self.params,
                                page_w=self.page_w, m_l=self.m_l, m_r=self.m_r)

    def frame_height(self) -> float:
        return self.page_h - self.m_t - self.m_b

    @staticmethod
    def estimate_spec_height(sections: list[dict]) -> float:
        """Rough content height in pt for page-count estimation.

        Deliberately coarse: if it underestimates, InDesign shows the
        standard overset indicator and the designer drags the chain one
        frame longer — a trailing blank page is worse than that.
        """
        h = 16.0  # H1
        for sec in sections:
            h += 14.0  # section title
            for _, value in sec["rows"]:
                h += 11.0 * max(1, value.count("\n") + 1)
        return h

    def pages_for_height(self, height_pt: float) -> int:
        import math
        return max(1, math.ceil(height_pt / self.frame_height()))

    def _image_cell_content(self, rect_id: str, image_path: Path, w_pt: float, h_pt: float) -> str:
        return _prim.image_cell_content(rect_id, image_path, w_pt, h_pt)

    _PROSE_STYLE = _prim.PROSE_STYLE

    def _resolve_bundle_image(self, bundle_root: Path, ref: str) -> Path | None:
        return _prim.resolve_bundle_image(bundle_root, ref)

    def _art_frame_size(self, img: Path, max_w: float = 120.0) -> tuple[float, float]:
        return _prim.art_frame_size(img, max_w, page_w=self.page_w, m_l=self.m_l, m_r=self.m_r)

    def _cell(self, cid: str, name: str, content: str, *, fill: str | None = None,
              stroke: bool = True, top: float = 3, bottom: float = 3,
              left: float = 4, right: float = 4) -> str:
        return _prim.cell(cid, name, content, fill=fill, stroke=stroke,
                          top=top, bottom=bottom, left=left, right=right)

    def _component_table(self, tid: str, cols: list[float], cells: list[str],
                         n_rows: int = 1) -> str:
        return _prim.component_table(tid, cols, cells, n_rows)

    def _wrap_table_paragraph(self, table: str, terminal: bool,
                              span_columns: bool = True) -> str:
        return _prim.wrap_table_paragraph(table, terminal, span_columns)

    def _render_component(self, sid: str, n: int, spec: dict,
                          bundle_root: Path, terminal: bool,
                          span_columns: bool = True,
                          measure_w: float | None = None) -> tuple[str, float]:
        """Component spec -> (xml, est_height) via the component registry."""
        return _components.render(
            spec, self._render_context(bundle_root), tid=f"{sid}_cmp{n}",
            terminal=terminal, span_columns=span_columns, measure_w=measure_w)

    def _render_context(self, bundle_root: Path) -> "_components.RenderContext":
        return _components.RenderContext(
            params=self.params, page_w=self.page_w, m_l=self.m_l, m_r=self.m_r,
            root=ROOT, bundle_root=bundle_root)

    def add_prose_story(self, sid: str, title: str, blocks: list[tuple[str, str]],
                        bundle_root: Path) -> tuple[str, float]:
        """Story from extracted prose blocks; returns (sid, est_height_pt)."""
        parts: list[str] = []
        est = 0.0
        img_n = 0
        content_indices = [i for i, (kind, _) in enumerate(blocks) if kind != "layout"]
        last_idx = content_indices[-1] if content_indices else -1
        in_twocol = False
        has_twocol_layout = any(kind == "layout" for kind, _ in blocks)
        text_measure = self.page_w - self.m_l - self.m_r
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
                xml_part, h = self._render_component(
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
                    raw_rows, self._render_context(bundle_root),
                    tid=f"{sid}_t{img_n}", terminal=terminal,
                    span_columns=not in_twocol)
                parts.append(xml_part)
                est += h
                continue
            if kind == "image":
                xml_part, h = _components.render_image_block(
                    text, self._render_context(bundle_root),
                    rect_id=f"{sid}_im{img_n + 1}", terminal=terminal)
                if xml_part is None:
                    continue
                img_n += 1
                parts.append(xml_part)
                est += h
                continue
            style = self._PROSE_STYLE.get(kind, "HB Body")
            span_columns = has_twocol_layout and not in_twocol and kind in {"h1", "h2"}
            parts.append(self._psr(
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
            f'<Story Self="{sid}" AppliedTOCStyle="n" TrackChanges="false" StoryTitle="{escape(title)}">\n'
            '<StoryPreference OpticalMarginAlignment="false" FrameType="TextFrameType"/>\n'
            + "".join(parts) + '</Story>\n</idPkg:Story>\n'
        )
        self.stories.append((sid, xml))
        return sid, est

    def add_lcd_story(self, rows: list[dict], data_root: Path) -> str:
        """LCD icon table: circled-no / icon image / name / description."""
        sid = "st_lcd"
        body_w = self.page_w - self.m_l - self.m_r
        cols = (body_w * 0.08, body_w * 0.12, body_w * 0.28, body_w * 0.52)
        tid = "tbl_lcd"
        cells = []
        icon_pt = 24.0
        for ri, row in enumerate(rows):
            # figure paths are repo-relative in both live and fixture snapshots
            fig = (ROOT / row["figure"]) if row["figure"] else None
            img = (self._image_cell_content(f"{tid}img{ri}", fig, icon_pt, icon_pt)
                   if fig and fig.exists() else "")
            cell_defs = (
                (self._psr("HB Spec Label", row["no"], terminal=True), 0),
                ('  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Figure">'
                 '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
                 + img + '<Content></Content></CharacterStyleRange></ParagraphStyleRange>\n', 1),
                (self._psr("HB Spec Label", row["name"], terminal=True), 2),
                (self._psr("HB Spec Value", row["desc"], terminal=True), 3),
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
            self._psr("HB H1", "LCD DISPLAY"),
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
        self.stories.append((sid, xml))
        return sid

    def add_symbols_story(self, signals: list[tuple[str, str]],
                          icons: list[dict], data_root: Path, lang: str = "en") -> str:
        sid = "st_symbols"
        copy = symbol_copy(lang)
        parts = [self._psr("HB H1", copy["title"])]
        if signals:
            table = self._table("tbl_sym_sig", signals, label_style="HB Notice Label")
            parts.append(
                '  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Body">\n'
                '    <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">\n'
                + table + '    <Br/></CharacterStyleRange>\n  </ParagraphStyleRange>\n')
        if icons:
            body_w = self.page_w - self.m_l - self.m_r
            cols = (body_w * 0.18, body_w * 0.82)
            tid = "tbl_sym_ico"
            cells = []
            icon_pt = 20.0
            for ri, row in enumerate(icons):
                fig = (ROOT / row["figure"]) if row["figure"] else None
                img = (self._image_cell_content(f"{tid}img{ri}", fig, icon_pt, icon_pt)
                       if fig and fig.exists() else "")
                img_cell = (
                    '  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Figure">'
                    '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
                    + img + '<Content></Content></CharacterStyleRange></ParagraphStyleRange>\n')
                for ci, content in ((0, img_cell),
                                    (1, self._psr("HB Spec Value", row["text"], terminal=True))):
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
        self.stories.append((sid, xml))
        return sid

    def add_trouble_story(self, rows: list[tuple[str, str]]) -> str:
        sid = "st_trouble"
        parts = [self._psr("HB H1", "TROUBLESHOOTING")]
        table = self._table("tbl_trouble", rows)
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
        self.stories.append((sid, xml))
        return sid

    def add_spec_story(self, sections: list[dict],
                       annotations: list[str] | None = None) -> str:
        sid = "st_spec"
        parts = [self._psr("HB H1", "SPECIFICATIONS")]
        for si, sec in enumerate(sections):
            parts.append(self._psr("HB Spec Section", sec["title"]))
            # table anchored in its own paragraph; the paragraph still needs
            # its own <Br/> so the next section title starts a new paragraph
            table = self._table(f"tbl_spec{si}", sec["rows"])
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
            parts.append(self._psr("HB Spec Note", note,
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
        self.stories.append((sid, xml))
        return sid

    def add_text_story(self, sid: str, title: str, blocks: list[tuple[str, str]]) -> str:
        parts = [
            self._psr(style, text, terminal=(i == len(blocks) - 1))
            for i, (style, text) in enumerate(blocks)
        ]
        return self._add_story_parts(sid, title, parts)

    def _add_story_parts(self, sid: str, title: str, parts: list[str]) -> str:
        xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
            f'<Story Self="{sid}" AppliedTOCStyle="n" TrackChanges="false" StoryTitle="{escape(title)}">\n'
            '<StoryPreference OpticalMarginAlignment="false" FrameType="TextFrameType"/>\n'
            + "".join(parts) +
            '</Story>\n'
            '</idPkg:Story>\n'
        )
        self.stories.append((sid, xml))
        return sid

    def _frame_xml(self, frame_id: str, story_id: str,
                   x1: float, y1: float, x2: float, y2: float, *,
                   columns: int = 1, fill: str | None = None,
                   rounded: bool = False, balance_columns: bool = False,
                   inset: tuple[float, float, float, float] | None = None) -> str:
        fill_attr = f'FillColor="{fill}" ' if fill else ""
        stroke_attr = (
            'StrokeColor="Swatch/None" StrokeWeight="0" '
            if fill else ""
        )
        corner_attr = 'CornerOption="RoundedCorner" CornerRadius="7" ' if rounded else ""
        balance_attr = ' VerticalBalanceColumns="true"' if balance_columns else ""
        inset_attr = ""
        if inset is not None:
            inset_attr = ' InsetSpacing="' + " ".join(f"{v:g}" for v in inset) + '"'
        return (
            f'  <TextFrame Self="{frame_id}" ParentStory="{story_id}" '
            'PreviousTextFrame="n" NextTextFrame="n" ContentType="TextType" '
            'AppliedObjectStyle="ObjectStyle/$ID/[Normal Text Frame]" '
            f'{fill_attr}{stroke_attr}{corner_attr}'
            'ItemTransform="1 0 0 1 0 0">\n'
            + self._path_geometry(x1, y1, x2, y2) +
            f'    <TextFramePreference TextColumnCount="{columns}" '
            f'TextColumnGutter="11" AutoSizingType="Off"{balance_attr}{inset_attr}/>\n'
            '  </TextFrame>\n'
        )

    def _page_rect(self, x: float, y: float, w: float, h: float) -> tuple[float, float, float, float]:
        return (
            -self.page_w / 2 + x,
            -self.page_h / 2 + y,
            -self.page_w / 2 + x + w,
            -self.page_h / 2 + y + h,
        )

    def _safety_section_story(self, sid: str, title: str,
                              blocks: list[tuple[str, str]],
                              bundle_root: Path) -> str:
        parts: list[str] = []
        text_measure = self.page_w - self.m_l - self.m_r
        column_measure = (text_measure - 11.0) / 2.0
        content_indices = [i for i, (kind, _) in enumerate(blocks) if kind != "layout"]
        last_idx = content_indices[-1] if content_indices else -1
        for bi, (kind, text) in enumerate(blocks):
            terminal = bi == last_idx
            if kind == "component":
                import json as _json
                xml_part, _ = self._render_component(
                    sid, bi, _json.loads(text), bundle_root, terminal,
                    span_columns=False, measure_w=column_measure)
                parts.append(xml_part)
            elif kind == "body":
                parts.append(self._psr("HB Title L2", text, terminal=terminal))
            elif kind == "list":
                parts.append(self._psr("HB List", text, terminal=terminal))
            elif kind in {"h1", "h2", "h3"}:
                parts.append(self._psr(self._PROSE_STYLE[kind], text, terminal=terminal))
        return self._add_story_parts(sid, title, parts)

    def add_safety_page(self, sid: str, title: str, blocks: list[tuple[str, str]],
                        bundle_root: Path, page_index: int) -> str:
        """V2.0 US safety page 01: fixed component regions, not one flow."""
        h1 = next((t for k, t in blocks if k == "h1"), title)
        top_warning = next((t for k, t in blocks
                            if k == "component" and '"kind": "safetywarning"' in t), None)
        subbar = next((t for k, t in blocks if k == "h2"), "OPERATING INSTRUCTIONS")

        sections: list[list[tuple[str, str]]] = []
        cur: list[tuple[str, str]] | None = None
        for kind, text in blocks:
            if kind == "layout" and text == "twocol_start":
                cur = []
            elif kind == "layout" and text == "twocol_end":
                if cur is not None:
                    sections.append(cur)
                cur = None
            elif cur is not None:
                cur.append((kind, text))

        title_sid = f"{sid}_title"
        self._add_story_parts(
            title_sid, f"{title} title",
            [self._psr("HB Capsule Text", h1, terminal=True)])
        warning_sid = f"{sid}_top_warning"
        if top_warning:
            import json as _json
            xml_part, _ = self._render_component(
                warning_sid, 0, _json.loads(top_warning), bundle_root,
                terminal=True, span_columns=False)
            self._add_story_parts(warning_sid, f"{title} warning", [xml_part])
        bar_sid = f"{sid}_subbar"
        self._add_story_parts(
            bar_sid, f"{title} subbar",
            [self._psr("HB Capsule Text", subbar, terminal=True)])
        section_sids = []
        for idx, section in enumerate(sections[:2]):
            sec_sid = f"{sid}_section{idx + 1}"
            self._safety_section_story(sec_sid, f"{title} section {idx + 1}",
                                       section, bundle_root)
            section_sids.append(sec_sid)

        spread_id = f"sp_{page_index}"
        page_no = page_index + 1
        body_x = 27.4
        body_w = self.page_w - body_x * 2
        frames = []
        for frame_id, story_id, rect, opts in (
            ("title", title_sid, (body_x, 27.5, body_w, 18.8),
             {"fill": "Color/HB Brand Dark", "rounded": True, "inset": (1, 5, 1, 6)}),
            ("warning", warning_sid, (body_x, 55.5, body_w, 31.5),
             {"inset": (0, 0, 0, 0)}),
            ("section1", section_sids[0] if section_sids else "", (body_x, 93.5, body_w, 162.0),
             {"columns": 2, "balance_columns": True, "inset": (0, 0, 0, 0)}),
            ("subbar", bar_sid, (body_x, 263.5, body_w, 17.2),
             {"fill": "Color/HB Brand Dark", "rounded": True, "inset": (0.5, 5, 0.5, 6)}),
            ("section2", section_sids[1] if len(section_sids) > 1 else "",
             (body_x, 286.0, body_w, 205.0),
             {"columns": 2, "balance_columns": True, "inset": (0, 0, 0, 0)}),
        ):
            if not story_id:
                continue
            x1, y1, x2, y2 = self._page_rect(*rect)
            frames.append(self._frame_xml(
                f"tf_{sid}_{frame_id}", story_id, x1, y1, x2, y2, **opts))

        xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<idPkg:Spread xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
            f'<Spread Self="{spread_id}" PageCount="1" BindingLocation="0" ShowMasterItems="true">\n'
            f'  <Page Self="{spread_id}_pg" Name="{page_no}" '
            'AppliedMaster="n" OverrideList="" TabOrder="" GridStartingPoint="TopOutside" '
            f'GeometricBounds="0 0 {self.page_h:g} {self.page_w:g}" '
            f'ItemTransform="1 0 0 1 {-self.page_w / 2:g} {-self.page_h / 2:g}">\n'
            '    <MarginPreference ColumnCount="1" ColumnGutter="12" '
            f'Top="{self.m_t:g}" Bottom="{self.m_b:g}" '
            f'Left="{self.m_l:g}" Right="{self.m_r:g}"/>\n'
            '  </Page>\n'
            + "".join(frames) +
            '</Spread>\n'
            '</idPkg:Spread>\n'
        )
        self.spreads.append((spread_id, xml))
        return spread_id

    def _single_component_story(self, sid: str, title: str, spec: dict,
                                bundle_root: Path, measure_w: float) -> str:
        xml_part, _ = self._render_component(
            sid, 0, spec, bundle_root,
            terminal=True, span_columns=False, measure_w=measure_w)
        return self._add_story_parts(sid, title, [xml_part])

    def add_fcc_inbox_page(
        self,
        sid: str,
        fcc_blocks: list[tuple[str, str]],
        inbox_blocks: list[tuple[str, str]],
        bundle_root: Path,
        page_index: int,
    ) -> str:
        """V2.0 page 03: FCC notice and inbox cards share one page."""
        import json as _json

        body_x = 27.4
        body_w = self.page_w - body_x * 2
        fcc_spec = next(
            (
                _json.loads(text) for kind, text in fcc_blocks
                if kind == "component" and _json.loads(text).get("kind") == "fcc"
            ),
            {"kind": "fcc", "texts": ["", ""]},
        )
        inbox_title = next((text for kind, text in inbox_blocks if kind == "h1"),
                           "WHAT'S IN THE BOX")
        inbox_spec = next(
            (
                _json.loads(text) for kind, text in inbox_blocks
                if kind == "component" and _json.loads(text).get("kind") == "inbox"
            ),
            None,
        )
        tip_spec = next(
            (
                _json.loads(text) for kind, text in inbox_blocks
                if kind == "component" and _json.loads(text).get("kind") == "notice"
            ),
            None,
        )

        fcc_sid = f"{sid}_fcc"
        self._single_component_story(
            fcc_sid, "FCC notice", fcc_spec, bundle_root, body_w)
        title_sid = f"{sid}_title"
        self._add_story_parts(
            title_sid, "Inbox title",
            [self._psr("HB Capsule Text", inbox_title, terminal=True)])
        frame_specs: list[tuple[str, str, tuple[float, float, float, float], dict]] = [
            ("fcc", fcc_sid, (body_x, 34.0, body_w, 184.0),
             {"fill": "Color/HB Bg K05", "rounded": True, "inset": (0, 0, 0, 0)}),
            ("title", title_sid, (body_x, 250.0, body_w, 21.5),
             {"fill": "Color/HB Brand Dark", "rounded": True, "inset": (1, 5, 1, 6)}),
        ]
        if inbox_spec:
            inbox_sid = f"{sid}_inbox"
            self._single_component_story(
                inbox_sid, "Inbox cards", inbox_spec, bundle_root, body_w)
            frame_specs.append(
                ("inbox", inbox_sid, (body_x, 278.0, body_w, 160.0),
                 {"inset": (0, 0, 0, 0)})
            )
        if tip_spec:
            tip_sid = f"{sid}_tip"
            self._single_component_story(
                tip_sid, "Inbox tip", tip_spec, bundle_root, body_w)
            frame_specs.append(
                ("tip", tip_sid, (body_x, 456.0, body_w, 42.0),
                 {"inset": (0, 0, 0, 0)})
            )

        spread_id = f"sp_{page_index}"
        page_no = page_index + 1
        frames = []
        for frame_id, story_id, rect, opts in frame_specs:
            x1, y1, x2, y2 = self._page_rect(*rect)
            frames.append(self._frame_xml(
                f"tf_{sid}_{frame_id}", story_id, x1, y1, x2, y2, **opts))

        xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<idPkg:Spread xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
            f'<Spread Self="{spread_id}" PageCount="1" BindingLocation="0" ShowMasterItems="true">\n'
            f'  <Page Self="{spread_id}_pg" Name="{page_no}" '
            'AppliedMaster="n" OverrideList="" TabOrder="" GridStartingPoint="TopOutside" '
            f'GeometricBounds="0 0 {self.page_h:g} {self.page_w:g}" '
            f'ItemTransform="1 0 0 1 {-self.page_w / 2:g} {-self.page_h / 2:g}">\n'
            '    <MarginPreference ColumnCount="1" ColumnGutter="12" '
            f'Top="{self.m_t:g}" Bottom="{self.m_b:g}" '
            f'Left="{self.m_l:g}" Right="{self.m_r:g}"/>\n'
            '  </Page>\n'
            + "".join(frames) +
            '</Spread>\n'
            '</idPkg:Spread>\n'
        )
        self.spreads.append((spread_id, xml))
        return spread_id

    def _symbol_signal_bar(self, tid: str, label: str, bundle_root: Path) -> str:
        asset_name = f"{label.lower()}_bar.png"
        asset = (
            ROOT / "docs" / "templates" / "word_template" / "common_assets"
            / "symbols" / asset_name
        )
        if asset.exists():
            return ('  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Figure">'
                    '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
                    + self._image_cell_content(tid, asset, 61.2, 16.2)
                    + '<Content></Content></CharacterStyleRange></ParagraphStyleRange>\n')
        return self._psr("HB Capsule Text", label, terminal=True)

    def _symbols_signal_table(self, tid: str, signals: list[tuple[str, str]],
                              width: float, bundle_root: Path,
                              lang: str = "en") -> str:
        copy = symbol_copy(lang)
        rows = [(copy["symbol"], copy["meaning"], True)] + [
            (label, text, False) for label, text in signals
        ]
        cols = [width * 0.24, width * 0.76]
        cells = []
        for ri, (left, right, header) in enumerate(rows):
            if header:
                left_xml = self._psr("HB Spec Label", left, terminal=True)
                right_xml = self._psr("HB Spec Label", right, terminal=True)
            else:
                left_xml = self._symbol_signal_bar(f"{tid}sig{ri}", left, bundle_root)
                right_xml = self._psr("HB Spec Value", right, terminal=True)
            cells.append(self._cell(f"{tid}c{ri}_0", f"0:{ri}", left_xml,
                                    top=3, bottom=3, left=6, right=4))
            cells.append(self._cell(f"{tid}c{ri}_1", f"1:{ri}", right_xml,
                                    top=3, bottom=3, left=7, right=5))
        return self._component_table(tid, cols, cells, n_rows=len(rows))

    def _symbols_icon_table(self, tid: str, icons: list[dict], width: float,
                            lang: str = "en") -> str:
        copy = symbol_copy(lang)
        rows = [{"figure": "", "text": copy["meaning"], "header": True}] + [
            {**row, "header": False} for row in icons
        ]
        cols = [width * 0.27, width * 0.73]
        cells = []
        for ri, row in enumerate(rows):
            if row.get("header"):
                left_xml = self._psr("HB Spec Label", copy["symbol"], terminal=True)
                right_xml = self._psr("HB Spec Label", row["text"], terminal=True)
            else:
                fig = (ROOT / row["figure"]) if row.get("figure") else None
                icon = ""
                if fig and fig.exists():
                    icon = self._image_cell_content(f"{tid}img{ri}", fig, 28.0, 28.0)
                left_xml = (
                    '  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Figure">'
                    '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
                    + icon + '<Content></Content></CharacterStyleRange></ParagraphStyleRange>\n')
                right_xml = self._psr("HB Spec Value", row["text"], terminal=True)
            cells.append(self._cell(f"{tid}c{ri}_0", f"0:{ri}", left_xml,
                                    top=3, bottom=3, left=4, right=4))
            cells.append(self._cell(f"{tid}c{ri}_1", f"1:{ri}", right_xml,
                                    top=3, bottom=3, left=5, right=4))
        return self._component_table(tid, cols, cells, n_rows=len(rows))

    def _table_story(self, sid: str, title: str, table: str) -> str:
        return self._add_story_parts(
            sid, title,
            ['  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Body">\n'
             '    <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">\n'
             + table +
             '    <Content></Content></CharacterStyleRange>\n'
             '  </ParagraphStyleRange>\n'])

    def add_safety_symbols_page(
        self,
        sid: str,
        tail_blocks: list[tuple[str, str]],
        maintenance_blocks: list[tuple[str, str]],
        signals: list[tuple[str, str]],
        icons: list[dict],
        bundle_root: Path,
        page_index: int,
        lang: str = "en",
    ) -> str:
        """V2.0 page 02: safety tail + maintenance + symbols on one page."""
        import json as _json
        copy = symbol_copy(lang)

        tail_sids: list[str] = []
        for bi, (kind, text) in enumerate(tail_blocks):
            if kind != "component":
                continue
            spec = _json.loads(text)
            if spec.get("kind") == "safetywarning":
                spec = {
                    "kind": "tailwarnbox",
                    "label": copy["warning"],
                    "texts": spec.get("texts", []),
                }
            elif spec.get("kind") == "warnbox":
                spec = {
                    **spec,
                    "kind": "tailwarnbox",
                }
            tail_sid = f"{sid}_tail_{spec.get('label', bi).lower()}"
            xml_part, _ = self._render_component(
                tail_sid, bi, spec, bundle_root,
                terminal=True, span_columns=False)
            self._add_story_parts(tail_sid, f"Safety tail {bi}", [xml_part])
            tail_sids.append(tail_sid)

        maint_title = next((t for k, t in maintenance_blocks if k == "h1"),
                           "USER MAINTENANCE INSTRUCTIONS")
        maint_text = "\n".join(t for k, t in maintenance_blocks if k == "body")
        maint_title_sid = f"{sid}_maintenance_title"
        self._add_story_parts(
            maint_title_sid, "Maintenance title",
            [self._psr("HB Capsule Text", maint_title, terminal=True)])
        maint_body_sid = f"{sid}_maintenance_body"
        self._add_story_parts(
            maint_body_sid, "Maintenance body",
            [self._psr("HB Body", maint_text, terminal=True)])

        symbols_title_sid = f"{sid}_symbols_title"
        self._add_story_parts(
            symbols_title_sid, "Symbols title",
            [self._psr("HB Capsule Text", copy["title"], terminal=True)])

        body_x = 27.4
        body_w = self.page_w - body_x * 2
        icon_gap = 6.0
        icon_table_w = (body_w - icon_gap) / 2.0
        left_icons = icons[:6]
        right_icons = icons[6:]
        signal_sid = f"{sid}_signals"
        self._table_story(
            signal_sid, "Signal words",
            self._symbols_signal_table(
                f"{sid}_sig_tbl", signals, body_w, bundle_root, lang))
        left_sid = f"{sid}_icons_left"
        self._table_story(
            left_sid, "Symbol icons left",
            self._symbols_icon_table(f"{sid}_icons_l_tbl", left_icons, icon_table_w, lang))
        right_sid = f"{sid}_icons_right"
        self._table_story(
            right_sid, "Symbol icons right",
            self._symbols_icon_table(
                f"{sid}_icons_r_tbl", right_icons, icon_table_w, lang))

        frame_specs = (
            ("tail_warning", tail_sids[0] if tail_sids else "", (body_x, 18.0, body_w, 46.0),
             {"inset": (0, 0, 0, 0)}),
            ("tail_danger", tail_sids[1] if len(tail_sids) > 1 else "", (body_x, 68.0, body_w, 38.0),
             {"inset": (0, 0, 0, 0)}),
            ("maint_title", maint_title_sid, (body_x, 113.0, body_w, 16.5),
             {"fill": "Color/HB Brand Dark", "rounded": True, "inset": (0.5, 5, 0.5, 6)}),
            ("maint_body", maint_body_sid, (body_x, 132.5, body_w, 34.0),
             {"inset": (0, 0, 0, 0)}),
            ("symbols_title", symbols_title_sid, (body_x, 173.5, body_w, 27.0),
             {"fill": "Color/HB Brand Dark", "rounded": True, "inset": (2, 5, 1, 6)}),
            ("signals", signal_sid, (body_x, 211.5, body_w, 111.0),
             {"inset": (0, 0, 0, 0)}),
            ("icons_left", left_sid, (body_x, 329.0, icon_table_w, 179.0),
             {"inset": (0, 0, 0, 0)}),
            ("icons_right", right_sid, (body_x + icon_table_w + icon_gap, 329.0, icon_table_w, 179.0),
             {"inset": (0, 0, 0, 0)}),
        )

        spread_id = f"sp_{page_index}"
        page_no = page_index + 1
        frames = []
        for frame_id, story_id, rect, opts in frame_specs:
            if not story_id:
                continue
            x1, y1, x2, y2 = self._page_rect(*rect)
            frames.append(self._frame_xml(
                f"tf_{sid}_{frame_id}", story_id, x1, y1, x2, y2, **opts))
        xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<idPkg:Spread xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
            f'<Spread Self="{spread_id}" PageCount="1" BindingLocation="0" ShowMasterItems="true">\n'
            f'  <Page Self="{spread_id}_pg" Name="{page_no}" '
            'AppliedMaster="n" OverrideList="" TabOrder="" GridStartingPoint="TopOutside" '
            f'GeometricBounds="0 0 {self.page_h:g} {self.page_w:g}" '
            f'ItemTransform="1 0 0 1 {-self.page_w / 2:g} {-self.page_h / 2:g}">\n'
            '    <MarginPreference ColumnCount="1" ColumnGutter="12" '
            f'Top="{self.m_t:g}" Bottom="{self.m_b:g}" '
            f'Left="{self.m_l:g}" Right="{self.m_r:g}"/>\n'
            '  </Page>\n'
            + "".join(frames) +
            '</Spread>\n'
            '</idPkg:Spread>\n'
        )
        self.spreads.append((spread_id, xml))
        return spread_id

    @staticmethod
    def _path_geometry(x1: float, y1: float, x2: float, y2: float) -> str:
        return _prim.path_geometry(x1, y1, x2, y2)

    def add_spread_chain(self, story_id: str, n_pages: int, start_index: int,
                         columns: int = 1) -> None:
        """One spread per page, each holding one frame of a linked chain.

        Spread coordinates: origin at the spread center; the page's
        top-left corner sits at (-w/2, -h/2), so the type area is that
        corner offset by the page margins.
        """
        x1 = -self.page_w / 2 + self.m_l
        x2 = self.page_w / 2 - self.m_r
        y1 = -self.page_h / 2 + self.m_t
        y2 = self.page_h / 2 - self.m_b
        for i in range(n_pages):
            spread_id = f"sp_{start_index + i}"
            frame_id = f"tf_{story_id}_{i}"
            prev = f'PreviousTextFrame="tf_{story_id}_{i-1}"' if i > 0 else 'PreviousTextFrame="n"'
            nxt = f'NextTextFrame="tf_{story_id}_{i+1}"' if i < n_pages - 1 else 'NextTextFrame="n"'
            xml = (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                f'<idPkg:Spread xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
                f'<Spread Self="{spread_id}" PageCount="1" BindingLocation="0" ShowMasterItems="true">\n'
                f'  <Page Self="{spread_id}_pg" Name="{start_index + i + 1}" '
                'AppliedMaster="n" OverrideList="" TabOrder="" GridStartingPoint="TopOutside" '
                f'GeometricBounds="0 0 {self.page_h:g} {self.page_w:g}" '
                f'ItemTransform="1 0 0 1 {-self.page_w / 2:g} {-self.page_h / 2:g}">\n'
                '    <MarginPreference ColumnCount="1" ColumnGutter="12" '
                f'Top="{self.m_t:g}" Bottom="{self.m_b:g}" Left="{self.m_l:g}" Right="{self.m_r:g}"/>\n'
                '  </Page>\n'
                f'  <TextFrame Self="{frame_id}" ParentStory="{story_id}" {prev} {nxt} '
                'ContentType="TextType" AppliedObjectStyle="ObjectStyle/$ID/[Normal Text Frame]" '
                'ItemTransform="1 0 0 1 0 0">\n'
                + self._path_geometry(x1, y1, x2, y2) +
                f'    <TextFramePreference TextColumnCount="{columns}" TextColumnGutter="11" AutoSizingType="Off"/>\n'
                '  </TextFrame>\n'
                '</Spread>\n'
                '</idPkg:Spread>\n'
            )
            self.spreads.append((spread_id, xml))

    # -- assembly ----------------------------------------------------------
    def designmap_xml(self) -> str:
        spread_refs = "\n".join(
            f'  <idPkg:Spread src="Spreads/Spread_{sid}.xml"/>' for sid, _ in self.spreads
        )
        story_refs = "\n".join(
            f'  <idPkg:Story src="Stories/Story_{sid}.xml"/>' for sid, _ in self.stories
        )
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<?aid style="50" type="document" readerVersion="15.0" featureSet="257" product="15.0(100)"?>\n'
            f'<Document xmlns:idPkg="{IDPKG}" DOMVersion="15.0" Self="doc" '
            'StoryList="' + " ".join(sid for sid, _ in self.stories) + '" Name="manual">\n'
            '  <Language Self="Language/$ID/English%3a USA" Name="$ID/English: USA" '
            'SingleQuotes="&#8216;&#8217;" DoubleQuotes="&#8220;&#8221;"/>\n'
            f'  <idPkg:Graphic src="Resources/Graphic.xml"/>\n'
            f'  <idPkg:Fonts src="Resources/Fonts.xml"/>\n'
            f'  <idPkg:Styles src="Resources/Styles.xml"/>\n'
            f'  <idPkg:Preferences src="Resources/Preferences.xml"/>\n'
            f'{spread_refs}\n'
            f'{story_refs}\n'
            '</Document>\n'
        )

    def write(self, out_path: Path) -> None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(out_path, "w") as zf:
            # mimetype must be first and stored uncompressed
            zf.writestr(zipfile.ZipInfo("mimetype"), MIMETYPE, compress_type=zipfile.ZIP_STORED)
            def add(name: str, data: str) -> None:
                zf.writestr(name, data, compress_type=zipfile.ZIP_DEFLATED)
            add("designmap.xml", self.designmap_xml())
            add("META-INF/container.xml",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">\n'
                '  <rootfiles><rootfile full-path="designmap.xml" media-type="text/xml"/></rootfiles>\n'
                '</container>\n')
            add("Resources/Graphic.xml", self.graphic_xml())
            add("Resources/Fonts.xml", self.fonts_xml())
            add("Resources/Styles.xml", self.styles_xml())
            add("Resources/Preferences.xml", self.preferences_xml())
            for sid, xml in self.spreads:
                add(f"Spreads/Spread_{sid}.xml", xml)
            for sid, xml in self.stories:
                add(f"Stories/Story_{sid}.xml", xml)


def split_safety_first_page(
    blocks: list[tuple[str, str]],
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Keep the V2.0 safety page-01 composition aligned with the master.

    The source template places the two main ``safetytwocol`` sections on page
    01. The trailing WARNING/DANGER boxes continue at the top of page 02 before
    the next prose section. Split at the second ``twocol_end`` marker rather
    than keying off copy text, so localized safety pages keep the same layout
    contract.
    """
    ends = 0
    for idx, (kind, text) in enumerate(blocks):
        if kind == "layout" and text == "twocol_end":
            ends += 1
            if ends == 2:
                return blocks[:idx + 1], blocks[idx + 1:]
    return blocks, []


def default_bundle_root(model: str, region: str, lang: str) -> Path:
    """Pick the prepared RST bundle path used by the current target layout."""
    lang_bundle = ROOT / "docs" / "_build" / model / region / lang / "rst"
    region_bundle = ROOT / "docs" / "_build" / model / region / "rst"
    return lang_bundle if lang_bundle.is_dir() else region_bundle


def default_output_path(model: str, region: str, lang: str, bundle_root: Path) -> Path:
    """Match the IDML output location to the prepared bundle layout."""
    region_bundle = ROOT / "docs" / "_build" / model / region / "rst"
    model_slug = model.replace("-", "").lower()
    region_slug = region.lower()
    try:
        is_region_bundle = bundle_root.resolve() == region_bundle.resolve()
    except FileNotFoundError:
        is_region_bundle = bundle_root == region_bundle
    if is_region_bundle:
        return (
            ROOT / "docs" / "_build" / model / region / "idml"
            / f"manual_{model_slug}_{region_slug}.idml"
        )
    return (
        ROOT / "docs" / "_build" / model / region / lang / "idml"
        / f"manual_{model_slug}_{region_slug}_{lang}.idml"
    )


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="JE-1000F")
    ap.add_argument("--region", default="US")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--data-root", default="data/phase2")
    ap.add_argument("--out", default=None)
    ap.add_argument("--bundle-root", default=None,
                    help="Prepared rst bundle dir (default: docs/_build/<model>/<region>/<lang>/rst); prose pages are skipped if absent")
    ap.add_argument("--check", default=None, help="validate an existing .idml and exit")
    args = ap.parse_args()

    if args.check:
        issues = check_idml(Path(args.check))
        for i in issues:
            print(f"[idml-check] FAIL {i}")
        print(f"[idml-check] {'OK' if not issues else f'{len(issues)} issue(s)'}: {args.check}")
        return 1 if issues else 0

    params = load_layout_params(ROOT / "data" / "layout_params.csv")
    data_root = (ROOT / args.data_root) if not Path(args.data_root).is_absolute() else Path(args.data_root)
    sections = load_spec_sections(data_root, args.model, args.region)
    if not sections:
        print(f"[export-idml] ERROR: no specifications rows for {args.model}_{args.region} in {data_root}")
        return 1

    w = IdmlWriter(params)
    lcd_rows = load_lcd_rows(data_root, args.model)
    trouble_rows = load_trouble_rows(data_root, args.model, args.region)
    spec_annotations = load_spec_annotations(data_root, args.model, args.region)
    symbol_cache: dict[str, tuple[list[tuple[str, str]], list[dict]]] = {}

    def symbol_rows_for(lang: str) -> tuple[list[tuple[str, str]], list[dict]]:
        lang = normalize_lang(lang)
        if lang not in symbol_cache:
            symbol_cache[lang] = load_symbols_rows(data_root, lang)
        return symbol_cache[lang]

    bundle_root = Path(args.bundle_root) if args.bundle_root else (
        default_bundle_root(args.model, args.region, args.lang))
    tags = {
        "latex",
        f"region_{args.region.lower()}",
        f"lang_{args.lang.lower()}",
        "model_" + args.model.lower().replace("-", "_"),
    }
    page_cursor = 0
    skipped_raw = 0
    prose_pages = 0

    def chain(story_id: str, est_h: float, columns: int = 1) -> None:
        nonlocal page_cursor
        # A two-column frame holds twice the height. Do not add an extra
        # safety multiplier here: when the estimate already fits, that creates
        # trailing blank linked frames in InDesign.
        pages = w.pages_for_height(est_h / max(1, columns))
        w.add_spread_chain(story_id, pages, page_cursor, columns=columns)
        page_cursor += pages

    DATA_PAGES = {"spec": "spec_", "lcd": "lcd_icons_", "trouble": "troubleshooting_"}
    ordered = bundle_page_order(bundle_root) if bundle_root.is_dir() else []
    if not ordered:
        print(f"[export-idml] NOTE: no prepared bundle at {bundle_root}; "
              "exporting data pages only (run `build.py rst` first for full prose)")

    emitted = {"spec": False, "lcd": False, "trouble": False, "symbols": False}
    pending_prefix_blocks: list[tuple[str, str]] = []
    pending_fcc_blocks: list[tuple[str, str]] = []
    pending_fcc_title = ""

    def page_lang(page: Path) -> str:
        try:
            text = page.read_text(encoding="utf-8")
        except OSError:
            text = ""
        match = re.search(r"\\HBApplyLang\{([^}]+)\}", text)
        if match:
            return normalize_lang(match.group(1))
        suffix = page.stem.rsplit("_", 1)[-1]
        return normalize_lang(suffix if len(suffix) <= 5 else args.lang)

    def page_stem_has(page: Path, suffix: str) -> bool:
        return page.stem == suffix or page.stem.endswith("_" + suffix)

    def slug_stem(stem: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", stem.lower()).strip("_")

    def flush_pending_prefix() -> None:
        nonlocal pending_prefix_blocks, prose_pages
        if not pending_prefix_blocks:
            return
        sid = f"st_pending_{page_cursor}"
        _, est = w.add_prose_story(sid, sid, pending_prefix_blocks, bundle_root)
        chain(sid, est)
        prose_pages += 1
        pending_prefix_blocks = []

    def flush_pending_fcc() -> None:
        nonlocal pending_fcc_blocks, pending_fcc_title, prose_pages
        if not pending_fcc_blocks:
            return
        sid = "st_" + slug_stem(pending_fcc_title or f"fcc_{page_cursor}")
        _, est = w.add_prose_story(
            sid, pending_fcc_title or sid, pending_fcc_blocks, bundle_root)
        chain(sid, est)
        prose_pages += 1
        pending_fcc_blocks = []
        pending_fcc_title = ""

    def emit_data_page(kind: str) -> None:
        flush_pending_fcc()
        flush_pending_prefix()
        if emitted[kind]:
            return
        emitted[kind] = True
        if kind == "spec":
            sid = w.add_spec_story(sections, spec_annotations)
            chain(sid, w.estimate_spec_height(sections) + 10.0 * len(spec_annotations))
        elif kind == "lcd" and lcd_rows:
            sid = w.add_lcd_story(lcd_rows, data_root)
            chain(sid, 16.0 + sum(max(28.0, 11.0 * (r["desc"].count("\n") + 1)) for r in lcd_rows))
        elif kind == "trouble" and trouble_rows:
            sid = w.add_trouble_story(trouble_rows)
            chain(sid, 16.0 + sum(11.0 * (v.count("\n") + 1) for _, v in trouble_rows))
        elif kind == "symbols":
            sym_signals, sym_icons = symbol_rows_for(args.lang)
            if not (sym_signals or sym_icons):
                return
            sid = w.add_symbols_story(sym_signals, sym_icons, data_root, args.lang)
            chain(sid, 16.0 + 14.0 * len(sym_signals) + 26.0 * len(sym_icons))

    for page in ordered:
        if page.name.startswith("symbols_") and emitted["symbols"] \
                and not pending_prefix_blocks and not pending_fcc_blocks:
            continue
        matched = next((k for k, prefix in DATA_PAGES.items()
                        if page.name.startswith(prefix)), None)
        if matched:
            emit_data_page(matched)
            continue
        res = extract_page(page, tags)
        skipped_raw += res.skipped_raw
        blocks = res.blocks
        if pending_prefix_blocks and "user_maintenance" in page.stem:
            lang = page_lang(page)
            sym_signals, sym_icons = symbol_rows_for(lang)
            if not (sym_signals or sym_icons):
                flush_pending_fcc()
                blocks = pending_prefix_blocks + blocks
                pending_prefix_blocks = []
            else:
                sid = "st_safety_symbols_" + re.sub(
                    r"[^a-z0-9]+", "_", page.stem.lower()).strip("_")
                w.add_safety_symbols_page(
                    sid, pending_prefix_blocks, blocks, sym_signals, sym_icons,
                    bundle_root, page_cursor, lang)
                emitted["symbols"] = True
                pending_prefix_blocks = []
                page_cursor += 1
                prose_pages += 1
                continue
        if pending_fcc_blocks and page_stem_has(page, "02_whats_in_the_box"):
            sid = "st_fcc_inbox_" + slug_stem(page.stem)
            w.add_fcc_inbox_page(
                sid, pending_fcc_blocks, blocks, bundle_root, page_cursor)
            pending_fcc_blocks = []
            pending_fcc_title = ""
            page_cursor += 1
            prose_pages += 1
            continue
        flush_pending_fcc()
        if page_stem_has(page, "01_fcc"):
            flush_pending_prefix()
            if blocks:
                pending_fcc_blocks = blocks
                pending_fcc_title = page.stem
            continue
        if page.name.startswith("symbols_"):
            if emitted["symbols"]:
                continue
            lang = page_lang(page)
            sym_signals, sym_icons = symbol_rows_for(lang)
            if pending_prefix_blocks and (sym_signals or sym_icons):
                sid = "st_safety_symbols_" + re.sub(
                    r"[^a-z0-9]+", "_", page.stem.lower()).strip("_")
                w.add_safety_symbols_page(
                    sid, pending_prefix_blocks, [], sym_signals, sym_icons,
                    bundle_root, page_cursor, lang)
                emitted["symbols"] = True
                pending_prefix_blocks = []
                page_cursor += 1
                prose_pages += 1
                continue
            emit_data_page("symbols")
            continue
        if pending_prefix_blocks:
            blocks = pending_prefix_blocks + blocks
            pending_prefix_blocks = []
        if not blocks:
            continue
        if page.name.startswith("safety_") and res.twocol:
            blocks, pending_prefix_blocks = split_safety_first_page(blocks)
            sid = "st_" + re.sub(r"[^a-z0-9]+", "_", page.stem.lower()).strip("_")
            w.add_safety_page(sid, page.stem, blocks, bundle_root, page_cursor)
            page_cursor += 1
            prose_pages += 1
            continue
        sid = "st_" + re.sub(r"[^a-z0-9]+", "_", page.stem.lower()).strip("_")
        _, est = w.add_prose_story(sid, page.stem, blocks, bundle_root)
        chain(sid, est, columns=2 if res.twocol else 1)
        prose_pages += 1

    # data pages always ship, bundle or not
    for kind in ("spec", "lcd", "trouble", "symbols"):
        emit_data_page(kind)

    out = Path(args.out) if args.out else (
        default_output_path(args.model, args.region, args.lang, bundle_root))
    w.write(out)
    issues = check_idml(out)
    for i in issues:
        print(f"[export-idml] SELF-CHECK FAIL: {i}")
    n_rows = sum(len(s["rows"]) for s in sections)
    print(f"[export-idml] {'OK' if not issues else 'WROTE WITH ISSUES'}: {out}")
    print(f"[export-idml] stories={len(w.stories)} spreads={len(w.spreads)} "
          f"prose pages={prose_pages} skipped raw blocks={skipped_raw} | "
          f"spec rows={n_rows} lcd rows={len(lcd_rows)} trouble rows={len(trouble_rows)}")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
