"""IDML exporter — route B of the InDesign handoff plan.

Produces an editable .idml package (styles/geometry mapped 1:1 from
data/layout_params.csv, CMYK swatches, data pages as real tables) so designers
fine-tune pipeline output in InDesign instead of retouching PDFs.

Usage:
  python tools/export_idml.py --model JE-1000F --region US [--lang en] [--flow]
  python tools/export_idml.py --check <file.idml>    # structural validation
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    from tools.idml_rst_extract import bundle_page_order, extract_page
    from tools.script_bootstrap import bootstrap_repo_root
    from tools.idml import check as _check
    from tools.idml import components as _components
    from tools.idml import flow as _flow
    from tools.idml import loaders as _loaders
    from tools.idml import package as _package
    from tools.idml import pages as _pages
    from tools.idml import params as _params
    from tools.idml import primitives as _prim
    from tools.idml import prose_flow as _prose_flow
    from tools.idml import stories as _stories
    from tools.idml import styles as _styles
except ImportError:  # pragma: no cover - direct script execution fallback
    from idml_rst_extract import bundle_page_order, extract_page  # type: ignore
    from script_bootstrap import bootstrap_repo_root
    from idml import check as _check  # type: ignore
    from idml import components as _components  # type: ignore
    from idml import flow as _flow  # type: ignore
    from idml import loaders as _loaders  # type: ignore
    from idml import package as _package  # type: ignore
    from idml import pages as _pages  # type: ignore
    from idml import params as _params  # type: ignore
    from idml import primitives as _prim  # type: ignore
    from idml import prose_flow as _prose_flow  # type: ignore
    from idml import stories as _stories  # type: ignore
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
        return _package.frame_height(self)

    @staticmethod
    def estimate_spec_height(sections: list[dict]) -> float:
        return _package.estimate_spec_height(sections)

    def pages_for_height(self, height_pt: float) -> int:
        return _package.pages_for_height(self, height_pt)

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
        return _stories.add_prose_story(self, sid, title, blocks, bundle_root)

    def add_lcd_story(self, rows: list[dict], data_root: Path) -> str:
        return _stories.add_lcd_story(self, rows, data_root)

    def add_symbols_story(self, signals: list[tuple[str, str]],
                          icons: list[dict], data_root: Path, lang: str = "en") -> str:
        return _stories.add_symbols_story(self, signals, icons, data_root, lang)

    def add_trouble_story(self, rows: list[tuple[str, str]]) -> str:
        return _stories.add_trouble_story(self, rows)

    def add_spec_story(self, sections: list[dict],
                       annotations: list[str] | None = None) -> str:
        return _stories.add_spec_story(self, sections, annotations)

    def add_text_story(self, sid: str, title: str, blocks: list[tuple[str, str]]) -> str:
        return _stories.add_text_story(self, sid, title, blocks)

    def _add_story_parts(self, sid: str, title: str, parts: list[str]) -> str:
        return _stories._add_story_parts(self, sid, title, parts)

    def _frame_xml(self, frame_id: str, story_id: str,
                   x1: float, y1: float, x2: float, y2: float, *,
                   columns: int = 1, fill: str | None = None,
                   rounded: bool = False, balance_columns: bool = False,
                   inset: tuple[float, float, float, float] | None = None) -> str:
        return _pages._frame_xml(self, frame_id, story_id, x1, y1, x2, y2, columns=columns, fill=fill, rounded=rounded, balance_columns=balance_columns, inset=inset)

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

    @staticmethod
    def _path_geometry(x1: float, y1: float, x2: float, y2: float) -> str:
        return _prim.path_geometry(x1, y1, x2, y2)

    def add_spread_chain(self, story_id: str, n_pages: int, start_index: int,
                         columns: int = 1) -> None:
        return _package.add_spread_chain(self, story_id, n_pages, start_index, columns=columns)

    # -- assembly ----------------------------------------------------------
    def designmap_xml(self) -> str:
        return _package.designmap_xml(self)

    def write(self, out_path: Path) -> None:
        return _package.write(self, out_path)


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
    ap.add_argument("--flow", action="store_true",
                    help="single-story book (threaded frames, Word-like reflow)")
    args = ap.parse_args()

    if args.check:
        issues = check_idml(Path(args.check))
        for i in issues:
            print(f"[idml-check] FAIL {i}")
        print(f"[idml-check] {'OK' if not issues else f'{len(issues)} issue(s)'}: {args.check}")
        return 1 if issues else 0

    params = load_layout_params(ROOT / "data" / "layout_params.csv")
    data_root = (ROOT / args.data_root) if not Path(args.data_root).is_absolute() else Path(args.data_root)
    sections = load_spec_sections(data_root, args.model, args.region, args.lang)
    if not sections:
        print(f"[export-idml] ERROR: no specifications rows for {args.model}_{args.region} in {data_root}")
        return 1

    w = IdmlWriter(params)
    lcd_rows = load_lcd_rows(data_root, args.model, args.lang)
    trouble_rows = load_trouble_rows(data_root, args.model, args.region, args.lang)
    spec_annotations = load_spec_annotations(data_root, args.model, args.region, args.lang)
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

    if args.flow:
        return _flow.run_flow(
            w, args, bundle_root=bundle_root, tags=tags,
            bundle_page_order=bundle_page_order, extract_page=extract_page,
            sections=sections, spec_annotations=spec_annotations, lcd_rows=lcd_rows,
            trouble_rows=trouble_rows, symbol_rows_for=symbol_rows_for,
            default_output_path=default_output_path, check_idml=check_idml)

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
    prose_flow = _prose_flow.ProseFlowBuffer()

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

    def emit_prose_story(sid: str, title: str, blocks: list[tuple[str, str]], columns: int = 1) -> None:
        nonlocal prose_pages
        _, est = w.add_prose_story(sid, title, blocks, bundle_root)
        chain(sid, est, columns=columns)
        prose_pages += 1

    def flush_prose_flow() -> None: prose_flow.flush(emit_prose_story, slug_stem)

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

    def emit_data_page(kind: str) -> None:
        flush_prose_flow()
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
            if matched == "trouble":
                res = extract_page(page, tags)
                if res.blocks:
                    skipped_raw += res.skipped_raw
                    emitted["trouble"] = True
                    prose_flow.add(page.stem, res.blocks)
                    continue
            emit_data_page(matched)
            continue
        res = extract_page(page, tags)
        skipped_raw += res.skipped_raw
        blocks = res.blocks
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
                w.add_safety_symbols_page(
                    sid, pending_prefix_blocks, blocks, sym_signals, sym_icons,
                    bundle_root, page_cursor, lang)
                emitted["symbols"] = True
                pending_prefix_blocks = []
                page_cursor += 1
                prose_pages += 1
                continue
        if pending_fcc_blocks and page_stem_has(page, "02_whats_in_the_box"):
            flush_prose_flow()
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
            flush_prose_flow()
            flush_pending_prefix()
            if blocks:
                pending_fcc_blocks = blocks
                pending_fcc_title = page.stem
            continue
        if page.name.startswith("symbols_"):
            flush_prose_flow()
            if emitted["symbols"]:
                continue
            lang = page_lang(page)
            sym_signals, sym_icons = symbol_rows_for(lang)
            if pending_prefix_blocks and (sym_signals or sym_icons):
                sid = "st_safety_symbols_" + slug_stem(page.stem)
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
            flush_prose_flow()
            blocks, pending_prefix_blocks = split_safety_first_page(blocks)
            sid = "st_" + re.sub(r"[^a-z0-9]+", "_", page.stem.lower()).strip("_")
            w.add_safety_page(sid, page.stem, blocks, bundle_root, page_cursor)
            page_cursor += 1
            prose_pages += 1
            continue
        sid = "st_" + re.sub(r"[^a-z0-9]+", "_", page.stem.lower()).strip("_")
        if res.twocol:
            flush_prose_flow()
            emit_prose_story(sid, page.stem, blocks, columns=2)
        else:
            prose_flow.add(page.stem, blocks)

    # data pages always ship, bundle or not
    flush_prose_flow()
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
