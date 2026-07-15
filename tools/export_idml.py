"""IDML exporter — route B of the InDesign handoff plan.

Produces an editable .idml package from the same prepared-bundle IR as LaTeX,
so designers can fine-tune pipeline output instead of retouching PDFs.

Usage:
  python tools/export_idml.py --model JE-1000F --region US [--lang en]
      [--data-root data/phase2] [--out docs/_build/.../manual.idml]
  python tools/export_idml.py --check <file.idml>   # structural validation
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
    from tools.idml import check as _check
    from tools.idml import components as _components
    from tools.idml import design_handoff as _design_handoff
    from tools.idml import export_paths as _export_paths
    from tools.idml import flow_idml as _flow_idml
    from tools.idml import loaders as _loaders
    from tools.idml import package as _package
    from tools.idml import page_identity as _page_identity
    from tools.idml import page_placed as _placed
    from tools.idml import page_folio as _folio
    from tools.idml import page_toc as _toc
    from tools.idml import pages as _pages
    from tools.idml import params as _params
    from tools.idml import primitives as _prim
    from tools.idml import prose_flow as _prose_flow
    from tools.idml import reference_story_flow as _reference_story_flow
    from tools.idml import stories as _stories
    from tools.idml import styles as _styles
    from tools.idml import template_merge as _template_merge
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root
    from idml import check as _check  # type: ignore
    from idml import components as _components  # type: ignore
    from idml import design_handoff as _design_handoff  # type: ignore
    from idml import page_placed as _placed  # type: ignore
    from idml import page_folio as _folio  # type: ignore
    from idml import page_toc as _toc  # type: ignore
    from idml import export_paths as _export_paths  # type: ignore
    from idml import flow_idml as _flow_idml  # type: ignore
    from idml import loaders as _loaders  # type: ignore
    from idml import package as _package  # type: ignore
    from idml import page_identity as _page_identity  # type: ignore
    from idml import pages as _pages  # type: ignore
    from idml import params as _params  # type: ignore
    from idml import primitives as _prim  # type: ignore
    from idml import prose_flow as _prose_flow  # type: ignore
    from idml import reference_story_flow as _reference_story_flow  # type: ignore
    from idml import stories as _stories  # type: ignore
    from idml import styles as _styles  # type: ignore
    from idml import template_merge as _template_merge  # type: ignore

ROOT = bootstrap_repo_root(__file__, parent_count=1)
from tools.idml import ir_sidecar as _ir_sidecar
from tools.idml import ir_projection as _ir_projection

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
load_page_title = _loaders.load_page_title

check_idml = _check.check_idml
split_safety_first_page = _prose_flow.split_safety_first_page


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
               visual_parity: bool = False) -> str:
        return _prim.spec_table(tid, rows, label_style, params=self.params,
                                page_w=self.page_w, m_l=self.m_l, m_r=self.m_r,
                                role=role, visual_parity=visual_parity)

    frame_height = _package.frame_height
    estimate_spec_height = staticmethod(_package.estimate_spec_height)
    pages_for_height = _package.pages_for_height

    def _image_cell_content(self, rect_id: str, image_path: Path, w_pt: float, h_pt: float) -> str:
        return _prim.image_cell_content(rect_id, image_path, w_pt, h_pt)

    _PROSE_STYLE = _prim.PROSE_STYLE

    def _resolve_bundle_image(self, bundle_root: Path, ref: str) -> Path | None:
        return _prim.resolve_bundle_image(bundle_root, ref)

    def _art_frame_size(self, img: Path, max_w: float = 120.0) -> tuple[float, float]:
        return _prim.art_frame_size(img, max_w, page_w=self.page_w, m_l=self.m_l, m_r=self.m_r)

    def _cell(self, cid: str, name: str, content: str, *, fill: str | None = None,
              stroke: bool = True, top: float = 3, bottom: float = 3,
              left: float = 4, right: float = 4, valign: str | None = None) -> str:
        return _prim.cell(cid, name, content, fill=fill, stroke=stroke,
                          top=top, bottom=bottom, left=left, right=right, valign=valign)

    def _component_table(self, tid: str, cols: list[float], cells: list[str], n_rows: int = 1, **kwargs) -> str:
        return _prim.component_table(tid, cols, cells, n_rows, **kwargs)

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
            root=ROOT, bundle_root=bundle_root, add_story=self._add_story_parts)

    def add_prose_story(self, sid: str, title: str, blocks: list[tuple[str, str]],
                        bundle_root: Path) -> tuple[str, float]:
        return _stories.add_prose_story(self, sid, title, blocks, bundle_root)

    def add_lcd_story(self, rows: list[dict], data_root: Path, **kw) -> str:
        return _stories.add_lcd_story(self, rows, data_root, **kw)

    def add_symbols_story(self, signals: list[tuple[str, str]],
                          icons: list[dict], data_root: Path, lang: str = "en") -> str:
        return _stories.add_symbols_story(self, signals, icons, data_root, lang)

    def add_trouble_story(self, rows: list[tuple[str, str]]) -> str:
        return _stories.add_trouble_story(self, rows)

    def add_spec_story(self, sections: list[dict],
                       annotations: list[str] | None = None, **kw) -> str:
        return _stories.add_spec_story(self, sections, annotations, **kw)

    def add_text_story(self, sid: str, title: str, blocks: list[tuple[str, str]]) -> str:
        return _stories.add_text_story(self, sid, title, blocks)

    def _add_story_parts(self, sid: str, title: str, parts: list[str]) -> str:
        return _stories._add_story_parts(self, sid, title, parts)

    def _frame_xml(self, frame_id: str, story_id: str,
                   x1: float, y1: float, x2: float, y2: float, *,
                   columns: int = 1, fill: str | None = None,
                   rounded: bool = False, balance_columns: bool = False,
                   inset: tuple[float, float, float, float] | None = None,
                   **kwargs) -> str:
        return _pages._frame_xml(self, frame_id, story_id, x1, y1, x2, y2, columns=columns, fill=fill, rounded=rounded, balance_columns=balance_columns, inset=inset, **kwargs)

    def _page_rect(self, x: float, y: float, w: float, h: float) -> tuple[float, float, float, float]:
        return _pages._page_rect(self, x, y, w, h)

    def _safety_section_story(self, sid: str, title: str,
                              blocks: list[tuple[str, str]],
                              bundle_root: Path) -> str:
        return _pages._safety_section_story(self, sid, title, blocks, bundle_root)

    def add_safety_page(self, sid: str, title: str, blocks: list[tuple[str, str]],
                        bundle_root: Path, page_index: int) -> str:
        return _pages.add_safety_page(self, sid, title, blocks, bundle_root, page_index)

    def _single_component_story(self, sid: str, title: str, spec: dict,
                                bundle_root: Path, measure_w: float) -> str:
        return _pages._single_component_story(self, sid, title, spec, bundle_root, measure_w)

    def add_fcc_inbox_page(
        self,
        sid: str,
        fcc_blocks: list[tuple[str, str]],
        inbox_blocks: list[tuple[str, str]],
        bundle_root: Path,
        page_index: int,
    ) -> str:
        return _pages.add_fcc_inbox_page(self, sid, fcc_blocks, inbox_blocks, bundle_root, page_index)

    def _symbol_signal_bar(self, tid: str, label: str, bundle_root: Path) -> str:
        return _pages._symbol_signal_bar(self, tid, label, bundle_root)

    def _symbols_signal_table(self, tid: str, signals: list[tuple[str, str]],
                              width: float, bundle_root: Path,
                              lang: str = "en") -> str:
        return _pages._symbols_signal_table(self, tid, signals, width, bundle_root, lang)

    def _symbols_icon_table(self, tid: str, icons: list[dict], width: float,
                            lang: str = "en") -> str:
        return _pages._symbols_icon_table(self, tid, icons, width, lang)

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
    ) -> str:
        return _pages.add_safety_symbols_page(self, sid, tail_blocks, maintenance_blocks, signals, icons, bundle_root, page_index, lang)

    _path_geometry = staticmethod(_prim.path_geometry)
    add_spread_chain = _package.add_spread_chain
    add_story_frames = _package.add_story_frames

    # -- assembly ----------------------------------------------------------
    designmap_xml = _package.designmap_xml
    write = _package.write


def default_bundle_root(model: str, region: str, lang: str) -> Path:
    return _export_paths.default_bundle_root(ROOT, model, region, lang)


def default_output_path(model: str, region: str, lang: str, bundle_root: Path) -> Path:
    return _export_paths.default_output_path(ROOT, model, region, lang, bundle_root)

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
    ap.add_argument("--mode", "--idml-mode", dest="mode", choices=("production", "flow", "both"), default="production",
                    help="IDML export mode; production preserves historical behavior.")
    ap.add_argument("--check", default=None, help="validate an existing .idml and exit")
    ap.add_argument("--template", default=None, help="bake production idml into this template .idml (pre-styled)")
    args = ap.parse_args()

    if args.check:
        return _check.run_check_cli(args.check)
    data_root = (ROOT / args.data_root) if not Path(args.data_root).is_absolute() else Path(args.data_root)
    bundle_root = Path(args.bundle_root) if args.bundle_root else (
        default_bundle_root(args.model, args.region, args.lang))

    if args.mode == "flow":
        flow = _flow_idml.write_flow_outputs(
            root=ROOT, model=args.model, region=args.region, lang=args.lang, data_root=data_root,
            bundle_root=bundle_root, build_command=sys.argv)
        _ir_sidecar.emit_manual_ir_sidecar(
            root=ROOT, bundle_root=bundle_root, out_dir=flow.idml.parent,
            model=args.model, region=args.region, lang=args.lang, data_root=data_root)
        print(f"[export-idml] FLOW OK: {flow.markdown} | FLOW IDML OK: {flow.idml}")
        return 0
    params = load_layout_params(ROOT / "data" / "layout_params.csv")
    try:
        manual_ir = _ir_projection.build_same_source_ir(
            root=ROOT, bundle_root=bundle_root, model=args.model, region=args.region,
            lang=args.lang, data_root=data_root)
    except ValueError as exc:
        print(f"[export-idml] ERROR: prepared bundle is required for same-source IDML: {exc}")
        return 1

    projected_by_path = {page.path: page for page in _ir_projection.project_pages(manual_ir, bundle_root)}
    page_plan = _ir_projection.build_reference_page_plan(manual_ir, bundle_root=bundle_root)
    sections: list[dict] = []
    lcd_rows: list[dict] = []
    trouble_rows: list[tuple[str, str]] = []
    w = IdmlWriter(params)
    symbol_cache: dict[str, tuple[list[tuple[str, str]], list[dict]]] = {}
    def symbol_rows_for(lang: str) -> tuple[list[tuple[str, str]], list[dict]]:
        lang = normalize_lang(lang)
        if lang not in symbol_cache:
            data = _ir_projection.symbol_page_data(
                manual_ir, lang, root=ROOT, data_root=data_root)
            symbol_cache[lang] = (
                list(data.signals) if data else [], list(data.icons) if data else [])
        return symbol_cache[lang]
    page_cursor = 0
    skipped_raw = 0
    toc = _toc.TocCollector()
    prose_pages = 0

    def chain(story_id: str, est_h: float, columns: int = 1, bottom_extra: float = 0.0) -> None:
        nonlocal page_cursor
        # A two-column frame holds twice the height. Do not add an extra
        # safety multiplier here: when the estimate already fits, that creates
        # trailing blank linked frames in InDesign.
        pages = w.pages_for_height(est_h / max(1, columns))
        w.add_spread_chain(
            story_id, pages, page_cursor, columns=columns,
            bottom_extra=bottom_extra, first_top_offset=13.81)
        page_cursor += pages

    DATA_PAGES = {"spec": "spec_", "lcd": "lcd_icons_", "trouble": "troubleshooting_"}
    ordered = list(projected_by_path)

    emitted: set[str] = set()  # "spec:fr", "lcd:es", "trouble", "symbols"
    pending_prefix_blocks: list[tuple[str, str]] = []
    pending_fcc_blocks, pending_fcc_title = [], ""
    prose_flow = _prose_flow.ProseFlowBuffer()
    prose_estimator = _prose_flow.idml_page_estimator(IdmlWriter, params, bundle_root)
    def page_lang(page: Path) -> str: return _page_identity.page_language(page, args.lang)
    page_stem_has = _page_identity.stem_has
    slug_stem = _page_identity.slug

    story_emitter = _reference_story_flow.ReferenceStoryEmitter(w, toc, bundle_root)

    def emit_prose_story(sid: str, title: str, blocks: list[tuple[str, str]],
                         columns: int = 1) -> None:
        nonlocal prose_pages, page_cursor
        page_cursor = story_emitter.emit(
            sid, title, blocks, page_cursor, columns=columns)
        prose_pages += 1

    def flush_prose_flow() -> None:
        prose_flow.flush(
            emit_prose_story, slug_stem, None, prose_estimator)
    def flush_pending_prefix() -> None:
        nonlocal pending_prefix_blocks
        if pending_prefix_blocks:
            sid = f"st_pending_{page_cursor}"
            emit_prose_story(sid, sid, pending_prefix_blocks)
            pending_prefix_blocks = []

    def flush_pending_fcc() -> None:
        nonlocal pending_fcc_blocks, pending_fcc_title
        if pending_fcc_blocks:
            sid = "st_" + slug_stem(pending_fcc_title or f"fcc_{page_cursor}")
            emit_prose_story(sid, pending_fcc_title or sid, pending_fcc_blocks)
            pending_fcc_blocks = []
            pending_fcc_title = ""

    def emit_data_page(kind: str, lang: str) -> None:
        nonlocal page_cursor
        flush_prose_flow()
        flush_pending_fcc()
        flush_pending_prefix()
        key = f"{kind}:{lang}" if kind in {"spec", "lcd"} else kind
        if key in emitted:
            return
        emitted.add(key)
        if kind == "spec":
            data = _ir_projection.spec_page_data(manual_ir, lang)
            if data is None:
                return
            secs = list(data.sections)
            notes = list(data.annotations)
            if lang == args.lang:
                sections[:] = secs
            title = data.title
            toc.note(title, page_cursor, lang)
            sid = w.add_spec_story(secs, notes, lang=lang, title=title)
            chain(sid, w.estimate_spec_height(secs) + 10.0 * len(notes))
        elif kind == "lcd":
            data = _ir_projection.lcd_page_data(
                manual_ir, lang, root=ROOT, data_root=data_root)
            if data is None:
                return
            rows = list(data.rows)
            if lang == args.lang:
                lcd_rows[:] = rows
            title = data.title
            toc.note(title, page_cursor, lang)
            sid = w.add_lcd_story(rows, data_root, lang=lang, title=title)
            segment_count = w.lcd_segment_counts.get(lang, 1)
            _package.add_lcd_story_frames(w, sid, page_cursor, segment_count)
            page_cursor += segment_count
        elif kind == "trouble":
            rows = list(_ir_projection.trouble_rows(manual_ir, lang))
            if not rows:
                return
            if lang == args.lang:
                trouble_rows[:] = rows
            toc.note(_toc.DATA_TITLES.get(kind, ""), page_cursor)
            sid = w.add_trouble_story(rows)
            chain(sid, 16.0 + sum(11.0 * (v.count("\n") + 1) for _, v in rows))
        elif kind == "symbols":
            sym_signals, sym_icons = symbol_rows_for(args.lang)
            if not (sym_signals or sym_icons):
                return
            toc.note(_toc.DATA_TITLES.get(kind, ""), page_cursor)
            sid = w.add_symbols_story(sym_signals, sym_icons, data_root, args.lang)
            chain(sid, 16.0 + 14.0 * len(sym_signals) + 26.0 * len(sym_icons))

    for page in ordered:
        if page.name.startswith("symbols_") and "symbols" in emitted \
                and not pending_prefix_blocks and not pending_fcc_blocks:
            continue
        toc.lang = page_lang(page)
        placed_asset = _placed.placed_asset_for(page.stem, toc.lang, ROOT / "docs")
        if placed_asset is not None:
            flush_prose_flow()
            if "overview" in page.stem:
                toc.note(_toc.OVERVIEW_TITLES.get(toc.lang, _toc.OVERVIEW_TITLES["en"]), page_cursor, toc.lang)
            _placed.add_placed_pdf_page(w, "st_placed_" + slug_stem(page.stem), placed_asset, page_cursor)
            page_cursor += 1
            prose_pages += 1
            continue
        matched = next((k for k, prefix in DATA_PAGES.items()
                        if page.name.startswith(prefix)), None)
        if matched:
            if matched == "trouble":
                res = projected_by_path[page]
                if res.blocks:
                    skipped_raw += res.skipped_raw
                    emitted.add("trouble")
                    toc.stem_langs[page.stem] = page_lang(page)
                    prose_flow.add(page.stem, list(res.blocks))
                    continue
            emit_data_page(matched, page_lang(page))
            continue
        res = projected_by_path[page]
        skipped_raw += res.skipped_raw
        blocks = list(res.blocks)
        if pending_prefix_blocks and "user_maintenance" in page.stem:
            flush_prose_flow()
            lang = page_lang(page)
            sym_signals, sym_icons = symbol_rows_for(lang)
            if not (sym_signals or sym_icons):
                flush_pending_fcc()
                blocks = pending_prefix_blocks + blocks
                pending_prefix_blocks = []
            else:
                sid = "st_safety_symbols_" + slug_stem(page.stem)
                toc.note(_toc.SYMBOL_TITLES.get(lang, _toc.SYMBOL_TITLES["en"]), page_cursor, lang)
                w.add_safety_symbols_page(
                    sid, pending_prefix_blocks, blocks, sym_signals, sym_icons,
                    bundle_root, page_cursor, lang)
                emitted.add("symbols")
                pending_prefix_blocks = []
                page_cursor += 1
                prose_pages += 1
                continue
        if pending_fcc_blocks and page_stem_has(page, "02_whats_in_the_box"):
            flush_prose_flow()
            sid = "st_fcc_inbox_" + slug_stem(page.stem)
            toc.note_h1s(blocks, page_cursor)
            w.add_fcc_inbox_page(
                sid, pending_fcc_blocks, blocks, bundle_root, page_cursor)
            pending_fcc_blocks = []
            pending_fcc_title = ""
            page_cursor += 1
            prose_pages += 1
            continue
        flush_pending_fcc()
        if page_stem_has(page, "01_fcc"):
            flush_prose_flow()
            flush_pending_prefix()
            if blocks:
                pending_fcc_blocks = blocks
                pending_fcc_title = page.stem
            continue
        if page.name.startswith("symbols_"):
            flush_prose_flow()
            if "symbols" in emitted:
                continue
            lang = page_lang(page)
            sym_signals, sym_icons = symbol_rows_for(lang)
            if pending_prefix_blocks and (sym_signals or sym_icons):
                sid = "st_safety_symbols_" + slug_stem(page.stem)
                toc.note(_toc.SYMBOL_TITLES.get(lang, _toc.SYMBOL_TITLES["en"]), page_cursor, lang)
                w.add_safety_symbols_page(
                    sid, pending_prefix_blocks, [], sym_signals, sym_icons,
                    bundle_root, page_cursor, lang)
                emitted.add("symbols")
                pending_prefix_blocks = []
                page_cursor += 1
                prose_pages += 1
                continue
            emit_data_page("symbols", lang)
            continue
        if pending_prefix_blocks:
            blocks = pending_prefix_blocks + blocks
            pending_prefix_blocks = []
        if not blocks:
            continue
        if page_stem_has(page, "11_warranty"):
            flush_prose_flow()
            toc.stem_langs[page.stem] = page_lang(page)
            emit_prose_story("st_" + slug_stem(page.stem), page.stem, blocks)
            continue
        if page.name.startswith("safety_") and res.twocol:
            flush_prose_flow()
            blocks, pending_prefix_blocks = split_safety_first_page(blocks)
            sid = "st_" + re.sub(r"[^a-z0-9]+", "_", page.stem.lower()).strip("_")
            toc.lang = page_lang(page)
            toc.note_h1s(blocks, page_cursor)
            w.add_safety_page(sid, page.stem, blocks, bundle_root, page_cursor)
            page_cursor += 1
            prose_pages += 1
            continue
        sid = "st_" + re.sub(r"[^a-z0-9]+", "_", page.stem.lower()).strip("_")
        if res.twocol:
            flush_prose_flow()
            emit_prose_story(sid, page.stem, blocks, columns=2)
        else:
            toc.stem_langs[page.stem] = page_lang(page)
            prose_flow.add(page.stem, blocks)

    # Emit source-declared data pages that were not placed in the ordered walk.
    flush_prose_flow()
    for kind in ("spec", "lcd", "trouble", "symbols"):
        emit_data_page(kind, args.lang)
    back_asset = _placed.placed_asset_for("back_cover", args.lang, ROOT / "docs")
    back_copy = _ir_projection.back_cover_data(manual_ir)
    if back_asset is not None:
        # Finished back-cover art from the master source wins over the
        # temporary composed page (the pending-asset note in page_placed).
        _placed.add_placed_pdf_page(w, "st_placed_back_cover", back_asset, page_cursor)
        page_cursor += 1
    elif _placed.add_back_cover_page(w, args.region, page_cursor, back_copy):
        page_cursor += 1
    _toc.finalize(w, toc, w._add_story_parts, w._psr,
                  source=_ir_projection.toc_page_data(manual_ir, bundle_root))
    _folio.apply(w, w._add_story_parts, w._psr)
    out = Path(args.out) if args.out else default_output_path(args.model, args.region, args.lang, bundle_root)
    _ir_projection.emit_reference_page_plan(page_plan, out_dir=out.parent)
    _ir_sidecar.write_manual_ir_sidecar(manual_ir, out.parent)
    w.write(out)
    issues = check_idml(out)
    for i in issues:
        print(f"[export-idml] SELF-CHECK FAIL: {i}")
    if args.mode == "both":
        flow = _flow_idml.write_flow_outputs(
            root=ROOT, model=args.model, region=args.region, lang=args.lang, data_root=data_root,
            bundle_root=bundle_root, build_command=sys.argv)
        print(f"[export-idml] FLOW OK: {flow.markdown} | FLOW IDML OK: {flow.idml}")
        handoff = _design_handoff.write_handoff_package(
            root=ROOT, model=args.model, region=args.region, lang=args.lang,
            data_root=data_root, bundle_root=bundle_root,
            production_idml=out, flow=flow, build_command=sys.argv)
        print(f"[export-idml] HANDOFF OK: {handoff.root}")
    if args.template:
        _template_merge.bake_beside(out, args.template, check_idml)
    n_rows = sum(len(s["rows"]) for s in sections)
    print(f"[export-idml] {'OK' if not issues else 'WROTE WITH ISSUES'}: {out}")
    print(f"[export-idml] stories={len(w.stories)} spreads={len(w.spreads)} "
          f"prose pages={prose_pages} skipped raw blocks={skipped_raw} | "
          f"spec rows={n_rows} lcd rows={len(lcd_rows)} trouble rows={len(trouble_rows)}")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
