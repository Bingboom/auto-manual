"""Production (reference) IDML export: one ordered pass over the projected pages.

``tools/export_idml.py`` prepares the same-source IR and page plan, then hands
them to :class:`ReferenceExport`. The pass keeps its cursor, pending prose and
emitted-page bookkeeping on the instance instead of in nested closures, so each
step is a method with its own complexity budget.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Callable

from tools.idml import design_handoff as _design_handoff
from tools.idml import flow_idml as _flow_idml
from tools.idml import ir_projection as _ir_projection
from tools.idml import ir_sidecar as _ir_sidecar
from tools.idml import package as _package
from tools.idml import page_folio as _folio
from tools.idml import page_identity as _page_identity
from tools.idml import page_overview as _overview
from tools.idml import page_placed as _placed
from tools.idml import page_roles as _page_roles
from tools.idml import page_toc as _toc
from tools.idml import prose_flow as _prose_flow
from tools.idml import reference_story_flow as _reference_story_flow
from tools.idml import symbols_page as _symbols_page
from tools.idml import target_assembly_render as _target_assembly_render
from tools.idml import template_merge as _template_merge
from tools.idml.check import check_idml
from tools.idml.loaders import normalize_lang
from tools.idml.prose_flow import split_safety_first_page
from tools.idml.writer import IdmlWriter


class ReferenceExport:
    """State of one production export, built from the prepared inputs."""

    def __init__(
        self,
        *,
        root: Path,
        args: argparse.Namespace,
        data_root: Any,
        layout_params_csv: Any,
        layout_param_overlays: Any,
        bundle_root: Path,
        params: dict[str, tuple[str, str]],
        manual_ir: Any,
        component_target: Any,
        page_plan: dict | None,
        new_writer: Callable[..., IdmlWriter],
        default_output_path: Callable[[str, str, str, Path], Path],
    ) -> None:
        self.root = root
        self.args = args
        self.data_root = data_root
        self.layout_params_csv = layout_params_csv
        self.layout_param_overlays = layout_param_overlays
        self.bundle_root = bundle_root
        self.params = params
        self.manual_ir = manual_ir
        self.component_target = component_target
        self.page_plan = page_plan
        self._new_writer = new_writer
        self._default_output_path = default_output_path
        self.projected_by_path = {page.path: page for page in _ir_projection.project_pages(self.manual_ir, self.bundle_root)}
        self.sections: list[dict] = []
        self.lcd_rows: list[dict] = []
        self.trouble_rows: list[tuple[str, str]] = []
        self.w = self._new_writer(
            self.params, model=self.args.model, region=self.args.region, language=self.args.lang, page_plan=self.page_plan,
            registered_components=self.component_target is not None and self.component_target.active)
        self.symbol_cache: dict[str, _ir_projection.SymbolPageData | None] = {}
        self.page_cursor = 0
        self.skipped_raw = 0
        self.toc = _toc.TocCollector()
        self.prose_pages = 0

        self.data_roles = {
            _page_roles.PageRole.SPEC: "spec",
            _page_roles.PageRole.LCD: "lcd",
            _page_roles.PageRole.TROUBLESHOOTING_DATA: "trouble",
        }
        self.ordered = list(self.projected_by_path)
        self.role_by_path = {
            page: _page_roles.classify_page_role(page)
            for page in self.ordered
        }
        self.coverage_assignments: list[tuple[Path, _page_roles.PageRole]] = []
        for page in self.ordered:
            try:
                source_ref = page.relative_to(self.bundle_root)
            except ValueError:
                source_ref = Path(page.name)
            self.coverage_assignments.append((source_ref, self.role_by_path[page]))

        self.target_assembly = (self.page_plan or {}).get("plan_source") == "target-assembly"

        self.emitted: set[str] = set()  # legacy: spec:fr/lcd:es/trouble/symbols
        self.pending_prefix_blocks: list[tuple[str, str]] = []
        self.pending_fcc_blocks, self.pending_fcc_title = [], ""
        self.pending_symbol_overflow: _symbols_page.SymbolOverflow | None = None
        self.approved_reference = (
            (self.page_plan or {}).get("plan_source") == "approved-reference"
        )
        self.prose_flow = _prose_flow.ProseFlowBuffer(bundle_root=self.bundle_root)
        self.prose_estimator = _prose_flow.idml_page_estimator(IdmlWriter, self.params, self.bundle_root)
        self.slug_stem = _page_identity.slug
        self.story_emitter = _reference_story_flow.ReferenceStoryEmitter(
            self.w, self.toc, self.bundle_root, self.page_plan, registered_components=self.w.registered_components)

        self.target_renderer = _target_assembly_render.TargetAssemblyRenderer(
            page_plan=self.page_plan, projected_by_path=self.projected_by_path,
            bundle_root=self.bundle_root, writer=self.w, toc=self.toc, manual_ir=self.manual_ir,
            root=self.root, data_root=self.data_root, output_lang=self.args.lang, emitted=self.emitted,
            spec_sections=self.sections,
            lcd_rows=self.lcd_rows, trouble_rows=self.trouble_rows,
            symbol_data_for=self.symbol_data_for, slug_stem=self.slug_stem, component_target=self.component_target,
        )

    def run(self) -> int:
        for page in self.ordered:
            self.render_page(page)
        return self.finish()

    def symbol_data_for(self, lang: str) -> _ir_projection.SymbolPageData | None:
        lang = normalize_lang(lang)
        if lang not in self.symbol_cache:
            self.symbol_cache[lang] = _ir_projection.symbol_page_data(
                self.manual_ir, lang, root=self.root, data_root=self.data_root)
        return self.symbol_cache[lang]

    def chain(self, story_id: str, est_h: float, columns: int = 1, bottom_extra: float = 0.0) -> None:
        # A two-column frame holds twice the height. Do not add an extra
        # safety multiplier here: when the estimate already fits, that creates
        # trailing blank linked frames in InDesign.
        pages = self.w.pages_for_height(est_h / max(1, columns))
        self.w.add_spread_chain(
            story_id, pages, self.page_cursor, columns=columns,
            bottom_extra=bottom_extra, first_top_offset=13.81)
        self.page_cursor += pages

    def page_lang(self, page: Path) -> str: return _page_identity.page_language(page, self.args.lang)

    def emit_prose_story(self, sid: str, title: str, blocks: list[tuple[str, str]], columns: int = 1) -> None:
        self.page_cursor = self.story_emitter.emit(
            sid, title, blocks, self.page_cursor, columns=columns)
        self.prose_pages += 1

    def flush_prose_flow(self) -> None:
        self.prose_flow.flush(
            self.emit_prose_story, self.slug_stem, self.page_plan, self.prose_estimator)

    def flush_pending_prefix(self) -> None:
        if self.pending_prefix_blocks:
            sid = f"st_pending_{self.page_cursor}"
            self.emit_prose_story(sid, sid, self.pending_prefix_blocks)
            self.pending_prefix_blocks = []

    def flush_pending_fcc(self) -> None:
        if self.pending_fcc_blocks:
            sid = "st_" + self.slug_stem(self.pending_fcc_title or f"fcc_{self.page_cursor}")
            self.emit_prose_story(sid, self.pending_fcc_title or sid, self.pending_fcc_blocks)
            self.pending_fcc_blocks = []
            self.pending_fcc_title = ""

    def emit_data_page(self, kind: str, lang: str) -> None:
        lang = normalize_lang(lang)
        self.flush_prose_flow()
        self.flush_pending_fcc()
        self.flush_pending_prefix()
        multilingual_key = kind in {"spec", "lcd"} or (
            self.target_assembly and kind in {"symbols", "trouble"}
        )
        key = f"{kind}:{lang}" if multilingual_key else kind
        if key in self.emitted:
            return
        self.emitted.add(key)
        if kind == "spec":
            data = _ir_projection.spec_page_data(self.manual_ir, lang)
            if data is None:
                return
            secs = list(data.sections)
            notes = list(data.annotations)
            if lang == self.args.lang:
                self.sections[:] = secs
            self.toc.note(data.title, self.page_cursor, lang)
            sid = self.w.add_spec_story(secs, notes, lang=lang, title=data.title,
                                   fit_content=bool(self.page_plan) and not self.approved_reference)
            self.chain(sid, self.w.estimate_spec_height(secs) + 10.0 * len(notes))
        elif kind == "lcd":
            data = _ir_projection.governed_lcd_page_data(
                self.manual_ir, lang, root=self.root, data_root=self.data_root,
                reference_plan=self.page_plan, component_target=self.component_target)
            if data is None:
                return
            rows = list(data.rows)
            if lang == self.args.lang:
                self.lcd_rows[:] = rows
            title = data.title
            self.toc.note(title, self.page_cursor, lang)
            sid = self.w.add_lcd_story(rows, self.data_root, lang=lang, title=title)
            segment_count = self.w.lcd_segment_counts.get(lang, 1)
            _package.add_lcd_story_frames(
                self.w, sid, self.page_cursor, segment_count, lang=lang)
            self.page_cursor += segment_count
        elif kind == "trouble":
            data = _ir_projection.trouble_page_data(self.manual_ir, lang)
            if data is None:
                return
            rows = list(data.rows)
            if lang == self.args.lang:
                self.trouble_rows[:] = rows
            self.toc.note(data.title, self.page_cursor, lang)
            sid = self.w.add_trouble_story(rows, title=data.title)
            self.chain(sid, 16.0 + sum(11.0 * (v.count("\n") + 1) for _, v in rows))
        elif kind == "symbols":
            # Preserve the historical standalone-data-page boundary outside
            # an explicit target assembly. Candidate assemblies carry their
            # own per-language composition identities; legacy/golden bundles
            # emit only the requested output language.
            symbol_lang = normalize_lang(lang if self.target_assembly else self.args.lang)
            data = self.symbol_data_for(symbol_lang)
            if data is None:
                return
            sym_signals = list(data.signals)
            sym_icons = list(data.icons)
            self.toc.note(data.title, self.page_cursor, symbol_lang)
            sid = self.w.add_symbols_story(
                sym_signals,
                sym_icons,
                self.data_root,
                symbol_lang,
                title=data.title,
                signal_headers=data.signal_headers,
                icon_headers=data.icon_headers,
            )
            self.chain(sid, 16.0 + 14.0 * len(sym_signals) + 26.0 * len(sym_icons))

    def render_page(self, page: Path) -> None:
        """Place one projected page, or queue it in the pending prose flow."""
        role = self.role_by_path[page]
        render_delta = self.target_renderer.render(
            page,
            get_page_cursor=lambda: self.page_cursor,
            flush_prose_flow=self.flush_prose_flow,
            flush_pending_fcc=self.flush_pending_fcc,
            flush_pending_prefix=self.flush_pending_prefix,
        )
        if render_delta is not None:
            self.skipped_raw += render_delta.skipped_raw
            self.page_cursor += render_delta.page_count
            self.prose_pages += render_delta.page_count
            return
        symbol_key = (
            f"symbols:{self.page_lang(page)}" if self.target_assembly else "symbols"
        )
        if role is _page_roles.PageRole.SYMBOLS and symbol_key in self.emitted \
                and not self.pending_prefix_blocks and not self.pending_fcc_blocks:
            return
        self.toc.lang = self.page_lang(page)
        placed_asset = _placed.placed_asset_for(
            page.stem, self.toc.lang, self.root / "docs", model=self.w.model,
        )
        if placed_asset is not None:
            self.flush_prose_flow()
            if role is _page_roles.PageRole.PRODUCT_OVERVIEW:
                self.toc.note_h1s(self.projected_by_path[page].blocks, self.page_cursor)
            _placed.add_placed_pdf_page(self.w, "st_placed_" + self.slug_stem(page.stem), placed_asset, self.page_cursor)
            self.page_cursor += 1
            self.prose_pages += 1
            return
        matched = self.data_roles.get(role)
        if matched:
            self._render_data_role_page(page, matched)
            return
        res = self.projected_by_path[page]
        self.skipped_raw += res.skipped_raw
        blocks = _prose_flow.align_operation_tail(list(res.blocks), self.page_plan, page.stem)
        blocks = _prose_flow.align_charging_car_page(blocks, self.page_plan, page.stem)
        blocks = self.target_renderer.prepare_page_blocks(page, blocks)
        self._render_content_page(page, role, res, blocks)

    def _render_data_role_page(self, page: Path, matched: str) -> None:
        if matched == "trouble":
            res = self.projected_by_path[page]
            # A source H1 belongs to the dedicated editable table story;
            # it must not make a semantic troubleshooting page fall back
            # to generic prose.  Conversely, an author-written list-table
            # remains a real flow block and must keep sharing the natural
            # storage/troubleshooting story.  Data components are omitted
            # from ``res.blocks``, so H1-only is the unambiguous semantic
            # data-page shape here.
            if any(kind != "h1" for kind, _ in res.blocks):
                self.skipped_raw += res.skipped_raw
                self.emitted.add(
                    f"trouble:{self.page_lang(page)}"
                    if self.target_assembly else "trouble"
                )
                self.toc.stem_langs[page.stem] = self.page_lang(page)
                self.prose_flow.add(page.stem, _prose_flow.align_trouble_table(
                    _prose_flow.mark_troubleshooting_table(
                        list(res.blocks),
                    ),
                    self.page_plan,
                    page.stem,
                ))
                return
        self.emit_data_page(matched, self.page_lang(page))

    def _add_safety_symbols_page(
        self, page: Path, lang: str, symbol_data: Any, blocks: list[tuple[str, str]],
    ) -> None:
        """Pair the pending safety prefix with the symbol tables on one page."""
        sym_signals = list(symbol_data.signals)
        sym_icons = list(symbol_data.icons)
        sid = "st_safety_symbols_" + self.slug_stem(page.stem)
        self.toc.note(symbol_data.title, self.page_cursor, lang)
        _, self.pending_symbol_overflow = self.w.add_safety_symbols_page(
            sid, self.pending_prefix_blocks, blocks, sym_signals, sym_icons,
            self.bundle_root, self.page_cursor, lang,
            title=symbol_data.title,
            signal_headers=symbol_data.signal_headers,
            icon_headers=symbol_data.icon_headers)
        self.emitted.add(f"symbols:{lang}" if self.target_assembly else "symbols")
        self.pending_prefix_blocks = []
        self.page_cursor += 1
        self.prose_pages += 1

    def _render_content_page(
        self, page: Path, role: Any, res: Any, blocks: list[tuple[str, str]],
    ) -> None:
        if role is _page_roles.PageRole.PRODUCT_OVERVIEW and _ir_projection.uses_native_overview_page(
            self.manual_ir, page, self.bundle_root, approved_reference=self.approved_reference,
            component_target=self.component_target,
        ):
            self.flush_prose_flow()
            self.toc.note_h1s(blocks, self.page_cursor)
            _overview.add_product_overview_page(
                self.w, "st_overview_" + self.slug_stem(page.stem), blocks, self.bundle_root, self.page_cursor)
            self.page_cursor += 1
            self.prose_pages += 1
            return
        if self.pending_prefix_blocks and role is _page_roles.PageRole.MAINTENANCE:
            self.flush_prose_flow()
            lang = self.page_lang(page)
            symbol_data = self.symbol_data_for(lang)
            if symbol_data is None:
                self.flush_pending_fcc()
                blocks = self.pending_prefix_blocks + blocks
                self.pending_prefix_blocks = []
            else:
                self._add_safety_symbols_page(page, lang, symbol_data, blocks)
                return
        if self.pending_fcc_blocks and role is _page_roles.PageRole.INBOX:
            self._add_fcc_inbox_page(page, blocks)
            return
        self.flush_pending_fcc()
        if role is _page_roles.PageRole.FCC:
            self.flush_prose_flow()
            self.flush_pending_prefix()
            if blocks:
                self.pending_fcc_blocks = blocks
                self.pending_fcc_title = page.stem
            return
        if role is _page_roles.PageRole.SYMBOLS:
            self._render_symbols_page(page)
            return
        self._render_flow_page(page, role, res, blocks)

    def _add_fcc_inbox_page(self, page: Path, blocks: list[tuple[str, str]]) -> None:
        self.flush_prose_flow()
        sid = "st_fcc_inbox_" + self.slug_stem(page.stem)
        lang = self.page_lang(page)
        self.toc.note_h1s(blocks, self.page_cursor)
        self.w.add_fcc_inbox_page(
            sid,
            self.pending_fcc_blocks,
            blocks,
            self.bundle_root,
            self.page_cursor,
            symbol_overflow=self.pending_symbol_overflow,
            lang=lang,
            reference_profile=(
                (((self.page_plan or {}).get("idml_contract") or {})
                 .get("editable_components", {}))
                .get("inbox_cards")
            ),
        )
        self.pending_fcc_blocks = []
        self.pending_fcc_title = ""
        self.pending_symbol_overflow = None
        self.page_cursor += 1
        self.prose_pages += 1

    def _render_symbols_page(self, page: Path) -> None:
        self.flush_prose_flow()
        symbol_key = (
            f"symbols:{self.page_lang(page)}" if self.target_assembly else "symbols"
        )
        if symbol_key in self.emitted:
            return
        lang = self.page_lang(page)
        symbol_data = self.symbol_data_for(lang)
        if self.pending_prefix_blocks and symbol_data is not None:
            self._add_safety_symbols_page(page, lang, symbol_data, [])
            return
        self.emit_data_page("symbols", lang)

    def _render_flow_page(
        self, page: Path, role: Any, res: Any, blocks: list[tuple[str, str]],
    ) -> None:
        if self.pending_prefix_blocks:
            blocks = self.pending_prefix_blocks + blocks
            self.pending_prefix_blocks = []
        if not blocks:
            return
        if (
            _prose_flow.warranty_starts_new_flow(self.page_plan)
            and role is _page_roles.PageRole.WARRANTY
        ):
            self.flush_prose_flow()
            self.toc.stem_langs[page.stem] = self.page_lang(page)
            self.emit_prose_story("st_" + self.slug_stem(page.stem), page.stem, blocks)
            return
        if role is _page_roles.PageRole.SAFETY and res.twocol:
            self.flush_prose_flow()
            blocks, self.pending_prefix_blocks = split_safety_first_page(blocks)
            sid = "st_" + re.sub(r"[^a-z0-9]+", "_", page.stem.lower()).strip("_")
            self.toc.lang = self.page_lang(page)
            self.toc.note_h1s(blocks, self.page_cursor)
            self.w.add_safety_page(sid, page.stem, blocks, self.bundle_root, self.page_cursor)
            self.page_cursor += 1
            self.prose_pages += 1
            return
        sid = "st_" + re.sub(r"[^a-z0-9]+", "_", page.stem.lower()).strip("_")
        if res.twocol:
            self.flush_prose_flow()
            self.emit_prose_story(sid, page.stem, blocks, columns=2)
        else:
            self.toc.stem_langs[page.stem] = self.page_lang(page)
            self.prose_flow.add(page.stem, blocks)

    def finish(self) -> int:
        """Emit the remaining data pages, front/back matter and the package."""
        coverage_warning = _page_roles.assembly_coverage_warning(self.coverage_assignments)
        if coverage_warning:
            print(coverage_warning)

        if self.pending_symbol_overflow and self.pending_symbol_overflow.has_rows():
            print(
                "[export-idml] ERROR: symbol continuation was not consumed "
                "by a following FCC page"
            )
            return 1

        # Emit source-declared data pages that were not placed in the ordered walk.
        self.flush_prose_flow()
        for kind in ("spec", "lcd", "trouble", "symbols"):
            self.emit_data_page(kind, self.args.lang)
        back_cover_added = self.target_renderer.back_cover_added
        if _target_assembly_render.needs_legacy_back_cover_fallback(self.target_renderer):
            back_cover_added = _placed.add_preferred_back_cover_page(
                    self.w, self.args.region, self.args.lang, self.root / "docs", self.page_cursor,
                    _ir_projection.back_cover_data(self.manual_ir), reference_plan=self.page_plan)
            if back_cover_added:
                self.page_cursor += 1
        toc_source, self.page_plan = _ir_projection.toc_with_front_matter(self.manual_ir, self.bundle_root, self.page_plan)
        if self.target_renderer.toc_planned:
            _toc.finalize(
                self.w, self.toc, self.w._add_story_parts, self.w._psr,
                source=toc_source,
                has_back_cover=back_cover_added,
                page_plan=self.page_plan,
            )
        _folio.apply(
            self.w,
            self.w._add_story_parts,
            self.w._psr,
            page_plan=self.page_plan,
            has_back_cover=back_cover_added,
        )
        if _ir_projection.report_reference_page_count_issues(self.page_plan, len(self.w.spreads)):
            return 1
        out = Path(self.args.out) if self.args.out else self._default_output_path(self.args.model, self.args.region, self.args.lang, self.bundle_root)
        _ir_projection.emit_reference_page_plan(self.page_plan, out_dir=out.parent)
        _ir_sidecar.write_manual_ir_sidecar(self.manual_ir, out.parent)
        self.w.write(out)
        from tools.idml.font_assets import provision_document_fonts
        provision_document_fonts(out)
        issues = check_idml(out)
        for i in issues:
            print(f"[export-idml] SELF-CHECK FAIL: {i}")
        if self.args.mode == "both":
            flow = _flow_idml.write_flow_outputs(
                root=self.root, model=self.args.model, region=self.args.region, lang=self.args.lang, data_root=self.data_root,
                bundle_root=self.bundle_root, layout_params_csv=self.layout_params_csv,
                layout_param_overlays=self.layout_param_overlays, build_command=sys.argv)
            print(f"[export-idml] FLOW OK: {flow.markdown} | FLOW IDML OK: {flow.idml}")
            handoff = _design_handoff.write_handoff_package(
                root=self.root, model=self.args.model, region=self.args.region, lang=self.args.lang,
                data_root=self.data_root, bundle_root=self.bundle_root,
                production_idml=out, flow=flow, build_command=sys.argv)
            print(f"[export-idml] HANDOFF OK: {handoff.root}")
        if self.args.template:
            _template_merge.bake_beside(out, self.args.template, check_idml)
        n_rows = sum(len(s["rows"]) for s in self.sections)
        print(f"[export-idml] {'OK' if not issues else 'WROTE WITH ISSUES'}: {out}")
        self.story_emitter.report_spans()
        print(f"[export-idml] stories={len(self.w.stories)} spreads={len(self.w.spreads)} "
              f"prose pages={self.prose_pages} skipped raw blocks={self.skipped_raw} | "
              f"spec rows={n_rows} lcd rows={len(self.lcd_rows)} trouble rows={len(self.trouble_rows)}")
        return 1 if issues else 0
