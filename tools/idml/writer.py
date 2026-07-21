"""Stateful IDML package writer façade over focused rendering modules.

The exporter owns page-composition policy.  This class owns only shared page
geometry plus the story/spread sinks and preserves the historical delegate
surface used by tests and the focused IDML renderers.
"""
from __future__ import annotations

from pathlib import Path

from . import components as _components
from . import package as _package
from . import pages as _pages
from . import primitives as _prim
from . import stories as _stories
from . import styles as _styles
from .params import param_pt


ROOT = Path(__file__).resolve().parents[2]


class IdmlWriter:
    def __init__(
        self,
        params: dict[str, tuple[str, str]],
        *,
        model: str | None = None,
        region: str | None = None,
        language: str | None = None,
    ):
        self.params = params
        self.model = model
        self.region = region
        self.language = language
        self.page_w = param_pt(params, "page_paperwidth", 368.79)
        self.page_h = param_pt(params, "page_paperheight", 524.69)
        self.m_l = param_pt(params, "page_margin_left", 28.35)
        self.m_r = param_pt(params, "page_margin_right", 28.35)
        self.m_t = param_pt(params, "page_margin_top", 14.17)
        self.m_b = param_pt(params, "page_margin_bottom", 36.85)
        self.stories: list[tuple[str, str]] = []   # (id, xml)
        self.spreads: list[tuple[str, str]] = []
        self.lcd_segment_counts: dict[str, int] = {}

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
               label_style: str = "HB Spec Label", *, role: str | None = None,
               visual_parity: bool = False,
               section_index: int | None = None) -> str:
        return _prim.spec_table(tid, rows, label_style, params=self.params,
                                page_w=self.page_w, m_l=self.m_l, m_r=self.m_r,
                                role=role, visual_parity=visual_parity,
                                section_index=section_index)

    frame_height = _package.frame_height
    estimate_spec_height = staticmethod(_package.estimate_spec_height)
    pages_for_height = _package.pages_for_height

    def _image_cell_content(self, rect_id: str, image_path: Path,
                            w_pt: float, h_pt: float) -> str:
        return _prim.image_cell_content(rect_id, image_path, w_pt, h_pt)

    _PROSE_STYLE = _prim.PROSE_STYLE

    def _resolve_bundle_image(self, bundle_root: Path, ref: str) -> Path | None:
        return _prim.resolve_bundle_image(bundle_root, ref)

    def _art_frame_size(self, img: Path,
                        max_w: float = 120.0) -> tuple[float, float]:
        return _prim.art_frame_size(
            img,
            max_w,
            page_w=self.page_w,
            m_l=self.m_l,
            m_r=self.m_r,
        )

    def _cell(self, cid: str, name: str, content: str, *,
              fill: str | None = None, stroke: bool = True,
              top: float = 3, bottom: float = 3,
              left: float = 4, right: float = 4,
              valign: str | None = None) -> str:
        return _prim.cell(cid, name, content, fill=fill, stroke=stroke,
                          top=top, bottom=bottom, left=left, right=right,
                          valign=valign)

    def _component_table(self, tid: str, cols: list[float], cells: list[str],
                         n_rows: int = 1, **kwargs) -> str:
        return _prim.component_table(tid, cols, cells, n_rows, **kwargs)

    def _wrap_table_paragraph(self, table: str, terminal: bool,
                              span_columns: bool = True) -> str:
        return _prim.wrap_table_paragraph(table, terminal, span_columns)

    def _render_component(self, sid: str, n: int, spec: dict,
                          bundle_root: Path, terminal: bool,
                          span_columns: bool = True,
                          measure_w: float | None = None,
                          language: str | None = None,
                          inline_origin_shift: float = 0.0) -> tuple[str, float]:
        """Component spec -> (xml, est_height) via the component registry."""
        return _components.render(
            spec, self._render_context(
                bundle_root,
                language=language,
                inline_origin_shift=inline_origin_shift,
            ),
            tid=f"{sid}_cmp{n}",
            terminal=terminal, span_columns=span_columns, measure_w=measure_w)

    def _render_context(
        self,
        bundle_root: Path,
        *,
        language: str | None = None,
        inline_origin_shift: float = 0.0,
    ) -> "_components.RenderContext":
        return _components.RenderContext(
            params=self.params, page_w=self.page_w, m_l=self.m_l, m_r=self.m_r,
            root=ROOT, bundle_root=bundle_root, model=self.model, region=self.region,
            language=language or self.language,
            inline_origin_shift=inline_origin_shift,
            add_story=self._add_story_parts)

    def add_prose_story(self, sid: str, title: str,
                        blocks: list[tuple[str, str]],
                        bundle_root: Path, *,
                        inline_origin_shift: float = 0.0) -> tuple[str, float]:
        return _stories.add_prose_story(
            self,
            sid,
            title,
            blocks,
            bundle_root,
            inline_origin_shift=inline_origin_shift,
        )

    def add_lcd_story(self, rows: list[dict], data_root: Path, **kw) -> str:
        return _stories.add_lcd_story(self, rows, data_root, **kw)

    def add_symbols_story(self, signals: list[tuple[str, str]],
                          icons: list[dict], data_root: Path,
                          lang: str = "en") -> str:
        return _stories.add_symbols_story(self, signals, icons, data_root, lang)

    def add_trouble_story(self, rows: list[tuple[str, str]]) -> str:
        return _stories.add_trouble_story(self, rows)

    def add_spec_story(self, sections: list[dict],
                       annotations: list[str] | None = None, **kw) -> str:
        return _stories.add_spec_story(self, sections, annotations, **kw)

    def add_text_story(self, sid: str, title: str,
                       blocks: list[tuple[str, str]]) -> str:
        return _stories.add_text_story(self, sid, title, blocks)

    def _add_story_parts(self, sid: str, title: str, parts: list[str]) -> str:
        return _stories._add_story_parts(self, sid, title, parts)

    def _frame_xml(self, frame_id: str, story_id: str,
                   x1: float, y1: float, x2: float, y2: float, *,
                   columns: int = 1, fill: str | None = None,
                   rounded: bool = False, balance_columns: bool = False,
                   inset: tuple[float, float, float, float] | None = None,
                   **kwargs) -> str:
        return _pages._frame_xml(
            self,
            frame_id,
            story_id,
            x1,
            y1,
            x2,
            y2,
            columns=columns,
            fill=fill,
            rounded=rounded,
            balance_columns=balance_columns,
            inset=inset,
            **kwargs,
        )

    def _page_rect(self, x: float, y: float, w: float,
                   h: float) -> tuple[float, float, float, float]:
        return _pages._page_rect(self, x, y, w, h)

    def _safety_section_story(self, sid: str, title: str,
                              blocks: list[tuple[str, str]],
                              bundle_root: Path) -> str:
        return _pages._safety_section_story(
            self, sid, title, blocks, bundle_root)

    def add_safety_page(self, sid: str, title: str,
                        blocks: list[tuple[str, str]], bundle_root: Path,
                        page_index: int) -> str:
        return _pages.add_safety_page(
            self, sid, title, blocks, bundle_root, page_index)

    def _single_component_story(self, sid: str, title: str, spec: dict,
                                bundle_root: Path, measure_w: float) -> str:
        return _pages._single_component_story(
            self, sid, title, spec, bundle_root, measure_w)

    def add_fcc_inbox_page(
        self,
        sid: str,
        fcc_blocks: list[tuple[str, str]],
        inbox_blocks: list[tuple[str, str]],
        bundle_root: Path,
        page_index: int,
        *,
        symbol_overflow: tuple[list[dict], list[dict]] | None = None,
        lang: str = "en",
    ) -> str:
        return _pages.add_fcc_inbox_page(
            self,
            sid,
            fcc_blocks,
            inbox_blocks,
            bundle_root,
            page_index,
            symbol_overflow=symbol_overflow,
            lang=lang,
        )

    def _symbol_signal_bar(self, tid: str, label: str,
                           bundle_root: Path) -> str:
        return _pages._symbol_signal_bar(self, tid, label, bundle_root)

    def _symbols_signal_table(self, tid: str,
                              signals: list[tuple[str, str]], width: float,
                              bundle_root: Path, lang: str = "en") -> str:
        return _pages._symbols_signal_table(
            self, tid, signals, width, bundle_root, lang)

    def _symbols_icon_table(
        self,
        tid: str,
        icons: list[dict],
        width: float,
        lang: str = "en",
        *,
        include_header: bool = True,
        row_heights: list[float] | None = None,
    ) -> str:
        return _pages._symbols_icon_table(
            self,
            tid,
            icons,
            width,
            lang,
            include_header=include_header,
            row_heights=row_heights,
        )

    def _table_story(self, sid: str, title: str, table: str) -> str:
        return _pages._table_story(self, sid, title, table)

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
        *,
        dense: bool = False,
    ) -> tuple[str, tuple[list[dict], list[dict]]]:
        return _pages.add_safety_symbols_page(
            self,
            sid,
            tail_blocks,
            maintenance_blocks,
            signals,
            icons,
            bundle_root,
            page_index,
            lang,
            dense=dense,
        )

    _path_geometry = staticmethod(_prim.path_geometry)
    add_spread_chain = _package.add_spread_chain
    add_story_frames = _package.add_story_frames

    # -- assembly ----------------------------------------------------------
    designmap_xml = _package.designmap_xml
    write = _package.write


__all__ = ["IdmlWriter"]
