"""Render target-assembly composition instances through shared IDML components."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from . import composition_plan, ir_projection, shared_page
from .loaders import normalize_lang

SPECIAL_COMPOSITION_TYPES = frozenset({
    "preface_safety_maintenance",
    "symbols",
    "safety_symbols",
    "inbox_overview",
    "fcc_inbox_overview",
    "lcd_operations",
    "connections",
    "troubleshooting",
    "charging",
    "charging_storage",
    "operation_ups",
    "charging_charging_methods",
    "app",
    "storage_troubleshooting",
    "specifications",
    "storage_specifications",
})


@dataclass(frozen=True)
class RenderDelta:
    page_count: int
    skipped_raw: int


class TargetAssemblyRenderer:
    """Stateful ordered dispatcher for target composition instances."""

    def __init__(
        self,
        *,
        page_plan: dict[str, Any] | None,
        projected_by_path: dict[Path, ir_projection.ProjectedPage],
        bundle_root: Path,
        writer,
        toc,
        manual_ir,
        root: Path,
        data_root: Path,
        output_lang: str,
        emitted: set[str],
        spec_sections: list[dict],
        lcd_rows: list[dict],
        trouble_rows: list[tuple[str, str]],
        symbol_data_for: Callable[[str], ir_projection.SymbolPageData | None],
        slug_stem: Callable[[str], str],
    ) -> None:
        self.enabled = (page_plan or {}).get("plan_source") == "target-assembly"
        plan = (
            composition_plan.build_composition_plan(page_plan)
            if self.enabled and page_plan is not None
            else None
        )
        self.composition_by_ref = plan.by_source_ref() if plan is not None else {}
        self.plan_entry_by_ref = {
            str(entry.get("source_ref") or ""): entry
            for entry in (page_plan or {}).get("pages", [])
        }
        self.page_plan = page_plan
        self.projected_by_path = projected_by_path
        self.bundle_root = bundle_root
        self.writer = writer
        self.toc = toc
        self.manual_ir = manual_ir
        self.root = root
        self.data_root = data_root
        self.output_lang = output_lang
        self.emitted = emitted
        self.spec_sections = spec_sections
        self.lcd_rows = lcd_rows
        self.trouble_rows = trouble_rows
        self.symbol_data_for = symbol_data_for
        self.slug_stem = slug_stem
        self.handled_compositions: set[str] = set()
        self.routed_tail_blocks: dict[str, list[tuple[str, str]]] = {}

    def _source_ref_for(self, page: Path) -> str:
        try:
            return page.relative_to(self.bundle_root).as_posix()
        except ValueError:
            return page.name

    def _projected_for(self, source_ref: str) -> ir_projection.ProjectedPage:
        entry = self.plan_entry_by_ref[source_ref]
        source_path = str(entry.get("source_path") or source_ref)
        return self.projected_by_path[self.bundle_root / source_path]

    def render(
        self,
        page: Path,
        *,
        get_page_cursor: Callable[[], int],
        flush_prose_flow: Callable[[], None],
        flush_pending_fcc: Callable[[], None],
        flush_pending_prefix: Callable[[], None],
    ) -> RenderDelta | None:
        composition = self.composition_by_ref.get(self._source_ref_for(page))
        if (
            not self.enabled
            or composition is None
            or composition.composition_type not in SPECIAL_COMPOSITION_TYPES
        ):
            return None
        if composition.composition_id in self.handled_compositions:
            return RenderDelta(page_count=0, skipped_raw=0)
        self.handled_compositions.add(composition.composition_id)
        flush_prose_flow()
        flush_pending_fcc()
        flush_pending_prefix()
        page_cursor = get_page_cursor()
        composition_pages = [
            self._projected_for(ref) for ref in composition.source_refs
        ]
        skipped_raw = sum(item.skipped_raw for item in composition_pages)
        lang = normalize_lang(composition.language)
        if composition.composition_type == "preface_safety_maintenance":
            for projected in composition_pages:
                self.toc.note_h1s(list(projected.blocks), page_cursor)
            shared_page.add_flow_composition(
                self.writer,
                sid="st_" + self.slug_stem(composition.composition_id),
                title=composition.composition_id,
                source_blocks=[list(item.blocks) for item in composition_pages],
                bundle_root=self.bundle_root,
                page_index=page_cursor,
                page_count=composition.page_count,
                language=lang,
            )
        elif composition.composition_type == "symbols":
            symbol_data = self.symbol_data_for(lang)
            if symbol_data is None:
                raise ValueError(f"{composition.composition_id}: missing Symbols data")
            self.toc.note(symbol_data.title, page_cursor, lang)
            shared_page.add_symbols_page(
                self.writer,
                sid="st_" + self.slug_stem(composition.composition_id),
                symbol_data=symbol_data,
                bundle_root=self.bundle_root,
                page_index=page_cursor,
                language=lang,
            )
            self.emitted.add(f"symbols:{lang}")
        elif composition.composition_type == "safety_symbols":
            safety, _symbols = composition_pages
            symbol_data = self.symbol_data_for(lang)
            if symbol_data is None:
                raise ValueError(f"{composition.composition_id}: missing Symbols data")
            self.toc.note_h1s(list(safety.blocks), page_cursor)
            self.toc.note(symbol_data.title, page_cursor, lang)
            shared_page.add_safety_symbols_page(
                self.writer,
                safety_sid="st_" + self.slug_stem(Path(safety.path).stem),
                safety_title=Path(safety.path).stem,
                safety_blocks=list(safety.blocks),
                symbol_data=symbol_data,
                bundle_root=self.bundle_root,
                data_root=self.data_root,
                page_index=page_cursor,
                language=lang,
            )
            self.emitted.add(f"symbols:{lang}")
        elif composition.composition_type == "inbox_overview":
            inbox, overview = composition_pages
            for projected in composition_pages:
                self.toc.note_h1s(list(projected.blocks), page_cursor)
            inbox_data = self.plan_entry_by_ref[
                composition.source_refs[0]
            ].get("composition_data")
            overview_data = self.plan_entry_by_ref[
                composition.source_refs[1]
            ].get("composition_data")
            shared_page.add_inbox_overview_page(
                self.writer,
                sid="st_" + self.slug_stem(composition.composition_id),
                inbox_blocks=list(inbox.blocks),
                overview_blocks=list(overview.blocks),
                bundle_root=self.bundle_root,
                page_index=page_cursor,
                language=lang,
                composition_data={
                    **(inbox_data if isinstance(inbox_data, dict) else {}),
                    **(overview_data if isinstance(overview_data, dict) else {}),
                },
            )
        elif composition.composition_type == "fcc_inbox_overview":
            fcc, inbox, overview = composition_pages
            for projected in composition_pages:
                self.toc.note_h1s(list(projected.blocks), page_cursor)
            shared_page.add_fcc_inbox_overview_page(
                self.writer,
                sid="st_" + self.slug_stem(composition.composition_id),
                fcc_blocks=list(fcc.blocks),
                inbox_blocks=list(inbox.blocks),
                overview_blocks=list(overview.blocks),
                bundle_root=self.bundle_root,
                page_index=page_cursor,
                language=lang,
            )
        elif composition.composition_type == "lcd_operations":
            _lcd, operation = composition_pages
            lcd_data = ir_projection.lcd_page_data(
                self.manual_ir,
                lang,
                root=self.root,
                data_root=self.data_root,
                reference_plan=self.page_plan,
            )
            if lcd_data is None:
                raise ValueError(f"{composition.composition_id}: missing LCD data")
            operation_blocks = list(operation.blocks)
            if lang == self.output_lang:
                self.lcd_rows[:] = list(lcd_data.rows)
            self.toc.note(lcd_data.title, page_cursor, lang)
            self.toc.note_h1s(operation_blocks, page_cursor)
            hero_path = (
                self.writer._resolve_bundle_image(
                    self.bundle_root, lcd_data.hero_reference,
                )
                if lcd_data.hero_reference
                else None
            )
            shared_page.add_lcd_operations_page(
                self.writer,
                lcd_data=lcd_data,
                operation_sid="st_" + self.slug_stem(Path(operation.path).stem),
                operation_title=Path(operation.path).stem,
                operation_blocks=operation_blocks,
                bundle_root=self.bundle_root,
                data_root=self.data_root,
                page_index=page_cursor,
                language=lang,
                hero_path=hero_path,
                composition_data=self.plan_entry_by_ref[
                    composition.source_refs[0]
                ].get("composition_data"),
            )
            self.emitted.add(f"lcd:{lang}")
        elif composition.composition_type == "connections":
            connection = composition_pages[0]
            entry = self.plan_entry_by_ref[composition.source_refs[0]]
            split = entry.get("flow_split")
            if not isinstance(split, dict):
                raise ValueError(
                    f"{composition.composition_id}: connections requires flow_split"
                )
            occurrence = int(split["occurrence"])
            seen = 0
            split_at = None
            connection_blocks = list(connection.blocks)
            for block_index, (kind, _value) in enumerate(connection_blocks):
                if kind == split["at_kind"]:
                    seen += 1
                    if seen == occurrence:
                        split_at = block_index
                        break
            if split_at is None:
                raise ValueError(
                    f"{composition.composition_id}: flow_split cannot be applied"
                )
            tail_id = str(split["tail_composition_id"])
            self.routed_tail_blocks[tail_id] = connection_blocks[split_at:]
            head = connection_blocks[:split_at]
            self.toc.note_h1s(head, page_cursor)
            shared_page.add_connections_page(
                self.writer,
                sid="st_" + self.slug_stem(Path(connection.path).stem),
                title=Path(connection.path).stem,
                blocks=head,
                bundle_root=self.bundle_root,
                page_index=page_cursor,
                language=lang,
                composition_data=entry.get("composition_data"),
            )
        elif composition.composition_type == "troubleshooting":
            trouble = composition_pages[0]
            trouble_data = ir_projection.trouble_page_data(self.manual_ir, lang)
            tail = self.routed_tail_blocks.pop(composition.composition_id, None)
            if trouble_data is None or tail is None:
                raise ValueError(
                    f"{composition.composition_id}: missing routed connection tail "
                    "or Troubleshooting data"
                )
            if lang == self.output_lang:
                self.trouble_rows[:] = list(trouble_data.rows)
            self.toc.note(trouble_data.title, page_cursor, lang)
            shared_page.add_connection_tail_troubleshooting_page(
                self.writer,
                connection_sid=(
                    "st_" + self.slug_stem(composition.composition_id) + "_tail"
                ),
                connection_title=composition.composition_id,
                connection_blocks=tail,
                trouble_sid="st_" + self.slug_stem(Path(trouble.path).stem),
                trouble_title=Path(trouble.path).stem,
                trouble_blocks=list(trouble.blocks),
                bundle_root=self.bundle_root,
                page_index=page_cursor,
                language=lang,
                composition_data=self.plan_entry_by_ref[
                    composition.source_refs[0]
                ].get("composition_data"),
            )
            self.emitted.add(f"trouble:{lang}")
        elif composition.composition_type == "charging":
            charging = composition_pages[0]
            charging_blocks = list(charging.blocks)
            self.toc.note_h1s(charging_blocks, page_cursor)
            shared_page.add_charging_page(
                self.writer,
                sid="st_" + self.slug_stem(composition.composition_id),
                title=composition.composition_id,
                charging_blocks=charging_blocks,
                bundle_root=self.bundle_root,
                page_index=page_cursor,
                language=lang,
                composition_data=self.plan_entry_by_ref[
                    composition.source_refs[0]
                ].get("composition_data"),
            )
        elif composition.composition_type == "charging_storage":
            charging, storage = composition_pages
            charging_blocks = list(charging.blocks)
            storage_blocks = list(storage.blocks)
            self.toc.note_h1s(charging_blocks, page_cursor)
            self.toc.note_h1s(storage_blocks, page_cursor)
            shared_page.add_charging_storage_page(
                self.writer,
                sid="st_" + self.slug_stem(composition.composition_id),
                title=composition.composition_id,
                charging_blocks=charging_blocks,
                storage_blocks=storage_blocks,
                bundle_root=self.bundle_root,
                page_index=page_cursor,
                language=lang,
            )
        elif composition.composition_type == "app":
            app_page = composition_pages[0]
            app_blocks = list(app_page.blocks)
            self.toc.note_h1s(app_blocks, page_cursor)
            shared_page.add_app_composition(
                self.writer,
                sid="st_" + self.slug_stem(composition.composition_id),
                title=composition.composition_id,
                blocks=app_blocks,
                bundle_root=self.bundle_root,
                page_index=page_cursor,
                page_count=composition.page_count,
                language=lang,
                page_plan=self.page_plan,
                source_stem=Path(app_page.path).stem,
            )
        elif composition.composition_type in {
            "operation_ups",
            "charging_charging_methods",
        }:
            for projected in composition_pages:
                self.toc.note_h1s(list(projected.blocks), page_cursor)
            flow_options = dict(
                (
                    self.plan_entry_by_ref[composition.source_refs[0]].get(
                        "composition_data"
                    )
                    or {}
                ).get("flow")
                or {}
            )
            default_image_role = {
                "operation_ups": "compact_diagram",
                "charging_charging_methods": "charging_diagram",
            }[composition.composition_type]
            shared_page.add_flow_composition(
                self.writer,
                sid="st_" + self.slug_stem(composition.composition_id),
                title=composition.composition_id,
                source_blocks=[list(item.blocks) for item in composition_pages],
                bundle_root=self.bundle_root,
                page_index=page_cursor,
                page_count=composition.page_count,
                language=lang,
                operation_first=(
                    composition.composition_type == "operation_ups"
                ),
                image_role=str(
                    flow_options.get("image_role") or default_image_role
                ),
                asset_refs=flow_options.get("asset_refs"),
            )
        elif composition.composition_type == "storage_troubleshooting":
            storage, trouble = composition_pages
            trouble_data = ir_projection.trouble_page_data(self.manual_ir, lang)
            if trouble_data is None:
                raise ValueError(
                    f"{composition.composition_id}: missing Troubleshooting data"
                )
            if lang == self.output_lang:
                self.trouble_rows[:] = list(trouble_data.rows)
            self.toc.note_h1s(list(storage.blocks), page_cursor)
            self.toc.note(trouble_data.title, page_cursor, lang)
            shared_page.add_storage_troubleshooting_page(
                self.writer,
                sid="st_" + self.slug_stem(composition.composition_id),
                storage_blocks=list(storage.blocks),
                trouble_sid="st_" + self.slug_stem(Path(trouble.path).stem),
                trouble_title=Path(trouble.path).stem,
                trouble_blocks=list(trouble.blocks),
                bundle_root=self.bundle_root,
                page_index=page_cursor,
                language=lang,
            )
            self.emitted.add(f"trouble:{lang}")
        elif composition.composition_type == "specifications":
            spec_data = ir_projection.spec_page_data(self.manual_ir, lang)
            if spec_data is None:
                raise ValueError(
                    f"{composition.composition_id}: missing Specifications data"
                )
            self.toc.note(spec_data.title, page_cursor, lang)
            _spec_sid, rendered_sections = shared_page.add_specifications_page(
                self.writer,
                spec_data=spec_data,
                page_index=page_cursor,
                language=lang,
                composition_data=self.plan_entry_by_ref[
                    composition.source_refs[0]
                ].get("composition_data"),
            )
            if lang == self.output_lang:
                self.spec_sections[:] = rendered_sections
            self.emitted.add(f"spec:{lang}")
        elif composition.composition_type == "storage_specifications":
            storage, _spec = composition_pages
            storage_blocks = list(storage.blocks)
            spec_data = ir_projection.spec_page_data(self.manual_ir, lang)
            if spec_data is None:
                raise ValueError(
                    f"{composition.composition_id}: missing Specifications data"
                )
            self.toc.note_h1s(storage_blocks, page_cursor)
            self.toc.note(spec_data.title, page_cursor, lang)
            composition_data = self.plan_entry_by_ref[
                composition.source_refs[1]
            ].get("composition_data")
            _storage_sid, _spec_sid, grouped_sections = (
                shared_page.add_storage_specifications_page(
                    self.writer,
                    sid="st_" + self.slug_stem(composition.composition_id),
                    storage_blocks=storage_blocks,
                    spec_data=spec_data,
                    bundle_root=self.bundle_root,
                    page_index=page_cursor,
                    language=lang,
                    composition_data=composition_data,
                )
            )
            if lang == self.output_lang:
                self.spec_sections[:] = grouped_sections
            self.emitted.add(f"spec:{lang}")
        return RenderDelta(
            page_count=composition.page_count,
            skipped_raw=skipped_raw,
        )
