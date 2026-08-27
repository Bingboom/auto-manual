"""IDML exporter — route B of the InDesign handoff plan.

Produces an editable .idml package from the same prepared-bundle IR as LaTeX,
so designers can fine-tune pipeline output instead of retouching PDFs.

Usage:
  python tools/export_idml.py --model JE-1000F --region US [--lang en]
      [--data-root data/phase2] [--out docs/_build/.../manual.idml]
  python tools/export_idml.py --check <file.idml>   # structural validation
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
    from tools.idml import check as _check
    from tools.idml import design_handoff as _design_handoff
    from tools.idml import export_cli as _export_cli
    from tools.idml import export_paths as _export_paths
    from tools.idml import flow_idml as _flow_idml
    from tools.idml import loaders as _loaders
    from tools.idml import package as _package
    from tools.idml import page_identity as _page_identity
    from tools.idml import page_roles as _page_roles
    from tools.idml import page_overview as _overview
    from tools.idml import page_placed as _placed
    from tools.idml import page_folio as _folio
    from tools.idml import page_toc as _toc
    from tools.idml import params as _params
    from tools.idml import prose_flow as _prose_flow
    from tools.idml import reference_story_flow as _reference_story_flow
    from tools.idml import symbols_page as _symbols_page
    from tools.idml import target_assembly_render as _target_assembly_render
    from tools.idml import template_merge as _template_merge
    from tools.idml.writer import IdmlWriter
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root
    from idml import check as _check  # type: ignore
    from idml import design_handoff as _design_handoff  # type: ignore
    from idml import export_cli as _export_cli  # type: ignore
    from idml import page_placed as _placed  # type: ignore
    from idml import page_folio as _folio  # type: ignore
    from idml import page_toc as _toc  # type: ignore
    from idml import export_paths as _export_paths  # type: ignore
    from idml import flow_idml as _flow_idml  # type: ignore
    from idml import loaders as _loaders  # type: ignore
    from idml import package as _package  # type: ignore
    from idml import page_identity as _page_identity  # type: ignore
    from idml import page_roles as _page_roles  # type: ignore
    from idml import page_overview as _overview  # type: ignore
    from idml import params as _params  # type: ignore
    from idml import prose_flow as _prose_flow  # type: ignore
    from idml import reference_story_flow as _reference_story_flow  # type: ignore
    from idml import symbols_page as _symbols_page  # type: ignore
    from idml import target_assembly_render as _target_assembly_render  # type: ignore
    from idml import template_merge as _template_merge  # type: ignore
    from idml.writer import IdmlWriter  # type: ignore

ROOT = bootstrap_repo_root(__file__, parent_count=1)
from tools.idml import ir_sidecar as _ir_sidecar
from tools.idml import ir_projection as _ir_projection

MIMETYPE = _params.MIMETYPE
IDPKG = _params.IDPKG
MM_TO_PT = _params.MM_TO_PT
load_layout_params = _params.load_layout_params
param_pt = _params.param_pt
brand_cmyk = _params.brand_cmyk
normalize_lang = _loaders.normalize_lang
load_spec_sections = _loaders.load_spec_sections
load_lcd_rows = _loaders.load_lcd_rows
load_spec_annotations = _loaders.load_spec_annotations
load_symbols_rows = _loaders.load_symbols_rows
load_trouble_rows = _loaders.load_trouble_rows

check_idml = _check.check_idml
split_safety_first_page = _prose_flow.split_safety_first_page


def default_bundle_root(model: str, region: str, lang: str) -> Path:
    return _export_paths.default_bundle_root(ROOT, model, region, lang)


def default_output_path(model: str, region: str, lang: str, bundle_root: Path) -> Path:
    return _export_paths.default_output_path(ROOT, model, region, lang, bundle_root)


def _new_production_writer(
    params: dict[str, tuple[str, str]],
    *,
    model: str,
    region: str,
    language: str,
    page_plan: dict | None,
) -> IdmlWriter:
    """Create the production writer with page-plan asset strictness.

    Approved reference composition is a hard rendering contract: falling back
    from a governed component to a generic table would produce a valid IDML
    package with the wrong design. Other production plans keep the historical
    permissive behavior.
    """
    return IdmlWriter(
        params,
        model=model,
        region=region,
        language=language,
        strict_component_assets=(
            (page_plan or {}).get("plan_source") == "approved-reference"
        ),
        native_structure_markers=(
            (page_plan or {}).get("plan_source") == "target-assembly"
        ),
    )

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = _export_cli.build_parser(__doc__)
    args = ap.parse_args()

    if args.check:
        return _check.run_check_cli(args.check)
    if not args.model:
        ap.error("the following arguments are required: --model")
    data_root, layout_params_csv, layout_param_overlays = (
        _export_cli.resolve_input_paths(ROOT, args)
    )
    bundle_root = Path(args.bundle_root) if args.bundle_root else (
        default_bundle_root(args.model, args.region, args.lang))

    if args.mode == "flow":
        flow = _flow_idml.write_flow_outputs(
            root=ROOT, model=args.model, region=args.region, lang=args.lang, data_root=data_root,
            bundle_root=bundle_root, layout_params_csv=layout_params_csv,
            layout_param_overlays=layout_param_overlays, build_command=sys.argv)
        _ir_sidecar.emit_manual_ir_sidecar(
            root=ROOT, bundle_root=bundle_root, out_dir=flow.idml.parent,
            model=args.model, region=args.region, lang=args.lang, data_root=data_root,
            layout_params_csv=layout_params_csv,
            layout_param_overlays=layout_param_overlays)
        print(f"[export-idml] FLOW OK: {flow.markdown} | FLOW IDML OK: {flow.idml}")
        return 0
    params = load_layout_params(layout_params_csv, layout_param_overlays)
    try:
        manual_ir = _ir_projection.build_same_source_ir(
            root=ROOT, bundle_root=bundle_root, model=args.model, region=args.region,
            lang=args.lang, data_root=data_root,
            layout_params_csv=layout_params_csv,
            layout_param_overlays=layout_param_overlays)
        assembly_plan = Path(args.assembly_plan) if args.assembly_plan else None
        page_plan = _ir_projection.build_reference_page_plan(
            manual_ir,
            root=ROOT,
            bundle_root=bundle_root,
            target_assembly_plan=assembly_plan,
        )
    except ValueError as exc:
        print(f"[export-idml] ERROR: same-source IDML preparation failed: {exc}")
        _export_cli.dump_prepared_bundle_debug(
            ROOT, bundle_root, model=args.model, region=args.region,
        )
        return 1

    projected_by_path = {page.path: page for page in _ir_projection.project_pages(manual_ir, bundle_root)}
    sections: list[dict] = []
    lcd_rows: list[dict] = []
    trouble_rows: list[tuple[str, str]] = []
    w = _new_production_writer(
        params,
        model=args.model,
        region=args.region,
        language=args.lang,
        page_plan=page_plan,
    )
    symbol_cache: dict[str, _ir_projection.SymbolPageData | None] = {}
    def symbol_data_for(lang: str) -> _ir_projection.SymbolPageData | None:
        lang = normalize_lang(lang)
        if lang not in symbol_cache:
            symbol_cache[lang] = _ir_projection.symbol_page_data(
                manual_ir, lang, root=ROOT, data_root=data_root)
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

    data_roles = {
        _page_roles.PageRole.SPEC: "spec",
        _page_roles.PageRole.LCD: "lcd",
        _page_roles.PageRole.TROUBLESHOOTING_DATA: "trouble",
    }
    ordered = list(projected_by_path)
    role_by_path = {
        page: _page_roles.classify_page_role(page)
        for page in ordered
    }
    coverage_assignments: list[tuple[Path, _page_roles.PageRole]] = []
    for page in ordered:
        try:
            source_ref = page.relative_to(bundle_root)
        except ValueError:
            source_ref = Path(page.name)
        coverage_assignments.append((source_ref, role_by_path[page]))

    target_assembly = (page_plan or {}).get("plan_source") == "target-assembly"

    emitted: set[str] = set()  # legacy: spec:fr/lcd:es/trouble/symbols
    pending_prefix_blocks: list[tuple[str, str]] = []
    pending_fcc_blocks, pending_fcc_title = [], ""
    pending_symbol_overflow: _symbols_page.SymbolOverflow | None = None
    approved_reference = (
        (page_plan or {}).get("plan_source") == "approved-reference"
    )
    prose_flow = _prose_flow.ProseFlowBuffer()
    prose_estimator = _prose_flow.idml_page_estimator(IdmlWriter, params, bundle_root)
    def page_lang(page: Path) -> str: return _page_identity.page_language(page, args.lang)
    slug_stem = _page_identity.slug
    story_emitter = _reference_story_flow.ReferenceStoryEmitter(w, toc, bundle_root, page_plan)
    def emit_prose_story(sid: str, title: str, blocks: list[tuple[str, str]], columns: int = 1) -> None:
        nonlocal prose_pages, page_cursor
        page_cursor = story_emitter.emit(
            sid, title, blocks, page_cursor, columns=columns)
        prose_pages += 1

    def flush_prose_flow() -> None:
        prose_flow.flush(
            emit_prose_story, slug_stem, page_plan, prose_estimator)
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
        multilingual_key = kind in {"spec", "lcd"} or (
            target_assembly and kind in {"symbols", "trouble"}
        )
        key = f"{kind}:{lang}" if multilingual_key else kind
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
                manual_ir, lang, root=ROOT, data_root=data_root,
                reference_plan=page_plan)
            if data is None:
                return
            rows = list(data.rows)
            if lang == args.lang:
                lcd_rows[:] = rows
            title = data.title
            toc.note(title, page_cursor, lang)
            sid = w.add_lcd_story(rows, data_root, lang=lang, title=title)
            segment_count = w.lcd_segment_counts.get(lang, 1)
            _package.add_lcd_story_frames(
                w, sid, page_cursor, segment_count, lang=lang)
            page_cursor += segment_count
        elif kind == "trouble":
            data = _ir_projection.trouble_page_data(manual_ir, lang)
            if data is None:
                return
            rows = list(data.rows)
            if lang == args.lang:
                trouble_rows[:] = rows
            toc.note(data.title, page_cursor, lang)
            sid = w.add_trouble_story(rows, title=data.title)
            chain(sid, 16.0 + sum(11.0 * (v.count("\n") + 1) for _, v in rows))
        elif kind == "symbols":
            # Preserve the historical standalone-data-page boundary outside
            # an explicit target assembly. Candidate assemblies carry their
            # own per-language composition identities; legacy/golden bundles
            # emit only the requested output language.
            symbol_lang = normalize_lang(lang if target_assembly else args.lang)
            data = symbol_data_for(symbol_lang)
            if data is None:
                return
            sym_signals = list(data.signals)
            sym_icons = list(data.icons)
            toc.note(data.title, page_cursor, symbol_lang)
            sid = w.add_symbols_story(
                sym_signals,
                sym_icons,
                data_root,
                symbol_lang,
                title=data.title,
                signal_headers=data.signal_headers,
                icon_headers=data.icon_headers,
            )
            chain(sid, 16.0 + 14.0 * len(sym_signals) + 26.0 * len(sym_icons))

    target_renderer = _target_assembly_render.TargetAssemblyRenderer(
        page_plan=page_plan, projected_by_path=projected_by_path,
        bundle_root=bundle_root, writer=w, toc=toc, manual_ir=manual_ir,
        root=ROOT, data_root=data_root, output_lang=args.lang, emitted=emitted,
        spec_sections=sections,
        lcd_rows=lcd_rows, trouble_rows=trouble_rows,
        symbol_data_for=symbol_data_for, slug_stem=slug_stem,
    )
    for page in ordered:
        role = role_by_path[page]
        render_delta = target_renderer.render(
            page,
            get_page_cursor=lambda: page_cursor,
            flush_prose_flow=flush_prose_flow,
            flush_pending_fcc=flush_pending_fcc,
            flush_pending_prefix=flush_pending_prefix,
        )
        if render_delta is not None:
            skipped_raw += render_delta.skipped_raw
            page_cursor += render_delta.page_count
            prose_pages += render_delta.page_count
            continue
        symbol_key = (
            f"symbols:{page_lang(page)}" if target_assembly else "symbols"
        )
        if role is _page_roles.PageRole.SYMBOLS and symbol_key in emitted \
                and not pending_prefix_blocks and not pending_fcc_blocks:
            continue
        toc.lang = page_lang(page)
        placed_asset = _placed.placed_asset_for(
            page.stem, toc.lang, ROOT / "docs", model=w.model,
        )
        if placed_asset is not None:
            flush_prose_flow()
            if role is _page_roles.PageRole.PRODUCT_OVERVIEW:
                toc.note_h1s(projected_by_path[page].blocks, page_cursor)
            _placed.add_placed_pdf_page(w, "st_placed_" + slug_stem(page.stem), placed_asset, page_cursor)
            page_cursor += 1
            prose_pages += 1
            continue
        matched = data_roles.get(role)
        if matched:
            if matched == "trouble":
                res = projected_by_path[page]
                # A source H1 belongs to the dedicated editable table story;
                # it must not make a semantic troubleshooting page fall back
                # to generic prose.  Conversely, an author-written list-table
                # remains a real flow block and must keep sharing the natural
                # storage/troubleshooting story.  Data components are omitted
                # from ``res.blocks``, so H1-only is the unambiguous semantic
                # data-page shape here.
                if any(kind != "h1" for kind, _ in res.blocks):
                    skipped_raw += res.skipped_raw
                    emitted.add(
                        f"trouble:{page_lang(page)}"
                        if target_assembly else "trouble"
                    )
                    toc.stem_langs[page.stem] = page_lang(page)
                    prose_flow.add(page.stem, _prose_flow.align_trouble_table(
                        list(res.blocks), page_plan, page.stem))
                    continue
            emit_data_page(matched, page_lang(page))
            continue
        res = projected_by_path[page]
        skipped_raw += res.skipped_raw
        blocks = _prose_flow.align_operation_tail(list(res.blocks), page_plan, page.stem)
        blocks = _prose_flow.align_charging_car_page(blocks, page_plan, page.stem)
        if approved_reference and role is _page_roles.PageRole.PRODUCT_OVERVIEW:
            flush_prose_flow()
            toc.note_h1s(blocks, page_cursor)
            _overview.add_product_overview_page(
                w,
                "st_overview_" + slug_stem(page.stem),
                blocks,
                bundle_root,
                page_cursor,
            )
            page_cursor += 1
            prose_pages += 1
            continue
        if pending_prefix_blocks and role is _page_roles.PageRole.MAINTENANCE:
            flush_prose_flow()
            lang = page_lang(page)
            symbol_data = symbol_data_for(lang)
            if symbol_data is None:
                flush_pending_fcc()
                blocks = pending_prefix_blocks + blocks
                pending_prefix_blocks = []
            else:
                sym_signals = list(symbol_data.signals)
                sym_icons = list(symbol_data.icons)
                sid = "st_safety_symbols_" + slug_stem(page.stem)
                toc.note(symbol_data.title, page_cursor, lang)
                _, pending_symbol_overflow = w.add_safety_symbols_page(
                    sid, pending_prefix_blocks, blocks, sym_signals, sym_icons,
                    bundle_root, page_cursor, lang,
                    title=symbol_data.title,
                    signal_headers=symbol_data.signal_headers,
                    icon_headers=symbol_data.icon_headers)
                emitted.add(f"symbols:{lang}" if target_assembly else "symbols")
                pending_prefix_blocks = []
                page_cursor += 1
                prose_pages += 1
                continue
        if pending_fcc_blocks and role is _page_roles.PageRole.INBOX:
            flush_prose_flow()
            sid = "st_fcc_inbox_" + slug_stem(page.stem)
            lang = page_lang(page)
            toc.note_h1s(blocks, page_cursor)
            w.add_fcc_inbox_page(
                sid,
                pending_fcc_blocks,
                blocks,
                bundle_root,
                page_cursor,
                symbol_overflow=pending_symbol_overflow,
                lang=lang,
                reference_profile=(
                    (((page_plan or {}).get("idml_contract") or {})
                     .get("editable_components", {}))
                    .get("inbox_cards")
                ),
            )
            pending_fcc_blocks = []
            pending_fcc_title = ""
            pending_symbol_overflow = None
            page_cursor += 1
            prose_pages += 1
            continue
        flush_pending_fcc()
        if role is _page_roles.PageRole.FCC:
            flush_prose_flow()
            flush_pending_prefix()
            if blocks:
                pending_fcc_blocks = blocks
                pending_fcc_title = page.stem
            continue
        if role is _page_roles.PageRole.SYMBOLS:
            flush_prose_flow()
            symbol_key = (
                f"symbols:{page_lang(page)}" if target_assembly else "symbols"
            )
            if symbol_key in emitted:
                continue
            lang = page_lang(page)
            symbol_data = symbol_data_for(lang)
            if pending_prefix_blocks and symbol_data is not None:
                sym_signals = list(symbol_data.signals)
                sym_icons = list(symbol_data.icons)
                sid = "st_safety_symbols_" + slug_stem(page.stem)
                toc.note(symbol_data.title, page_cursor, lang)
                _, pending_symbol_overflow = w.add_safety_symbols_page(
                    sid, pending_prefix_blocks, [], sym_signals, sym_icons,
                    bundle_root, page_cursor, lang,
                    title=symbol_data.title,
                    signal_headers=symbol_data.signal_headers,
                    icon_headers=symbol_data.icon_headers)
                emitted.add(f"symbols:{lang}" if target_assembly else "symbols")
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
        if (
            _prose_flow.warranty_starts_new_flow(page_plan)
            and role is _page_roles.PageRole.WARRANTY
        ):
            flush_prose_flow()
            toc.stem_langs[page.stem] = page_lang(page)
            emit_prose_story("st_" + slug_stem(page.stem), page.stem, blocks)
            continue
        if role is _page_roles.PageRole.SAFETY and res.twocol:
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

    coverage_warning = _page_roles.assembly_coverage_warning(coverage_assignments)
    if coverage_warning:
        print(coverage_warning)

    if pending_symbol_overflow and pending_symbol_overflow.has_rows():
        print(
            "[export-idml] ERROR: symbol continuation was not consumed "
            "by a following FCC page"
        )
        return 1

    # Emit source-declared data pages that were not placed in the ordered walk.
    flush_prose_flow()
    for kind in ("spec", "lcd", "trouble", "symbols"):
        emit_data_page(kind, args.lang)
    back_cover_added = _placed.add_preferred_back_cover_page(
            w, args.region, args.lang, ROOT / "docs", page_cursor,
            _ir_projection.back_cover_data(manual_ir), reference_plan=page_plan)
    if back_cover_added:
        page_cursor += 1
    _toc.finalize(w, toc, w._add_story_parts, w._psr,
                  source=_ir_projection.toc_page_data(manual_ir, bundle_root),
                  page_plan=page_plan)
    _folio.apply(
        w,
        w._add_story_parts,
        w._psr,
        page_plan=page_plan,
        has_back_cover=back_cover_added,
    )
    if _ir_projection.report_reference_page_count_issues(page_plan, len(w.spreads)):
        return 1
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
            bundle_root=bundle_root, layout_params_csv=layout_params_csv,
            layout_param_overlays=layout_param_overlays, build_command=sys.argv)
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
