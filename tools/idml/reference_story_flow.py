"""Production IDML story emission with natural prose flow.

Fixed composite pages are flushed and composed by ``export_idml``.  This
module owns the remaining editable prose stories and gives each one a normal
linked spread chain, so ordinary sections can flow across component/page
boundaries without inheriting the LaTeX reference page breaks.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import ir_projection
from .asset_contracts import is_je1000f_us_app_reference_plan_page
from .params import param_pt
from .prose_flow import operation_final_frame_x_offset, operation_language


@dataclass
class ReferenceStoryEmitter:
    writer: object
    toc: object
    bundle_root: Path
    page_plan: dict | None = None

    def emit(self, sid: str, title: str, blocks: list[tuple[str, str]],
             page_cursor: int, columns: int = 1) -> int:
        """Emit one editable prose story and return the next page cursor."""
        writer = self.writer
        self.toc.latch(title)
        operation_lang = operation_language(blocks, self.page_plan, title)
        is_operation = (
            (self.page_plan or {}).get("plan_source") == "approved-reference"
            and "operation_guide" in title
            and operation_lang is not None
        )
        is_charging_methods = (
            (self.page_plan or {}).get("plan_source") == "approved-reference"
            and "charging_methods" in title
        )
        is_charging_intro = (
            (self.page_plan or {}).get("plan_source") == "approved-reference"
            and "charging" in title.casefold()
            and "charging_methods" not in title.casefold()
        )
        is_app = is_je1000f_us_app_reference_plan_page(
            self.page_plan,
            title,
        )
        final_frame_x_offset = (
            operation_final_frame_x_offset(operation_lang)
            if is_operation else 0.0
        )
        prose_options: dict[str, float | str] = {
            "inline_origin_shift": final_frame_x_offset,
        }
        if operation_lang is not None:
            prose_options["language"] = operation_lang
        _, estimate = writer.add_prose_story(
            sid,
            title,
            blocks,
            self.bundle_root,
            **prose_options,
        )
        if title == "00_preface":
            preface_left = param_pt(
                writer.params, "idml_preface_margin_left", writer.m_l,
            )
            preface_right = param_pt(
                writer.params, "idml_preface_margin_right", writer.m_r,
            )
            preface_top = param_pt(
                writer.params, "idml_preface_margin_top", writer.m_t,
            )
            preface_bottom = param_pt(
                writer.params, "idml_preface_margin_bottom", writer.m_b,
            )
            writer.add_story_frames(
                sid,
                [(page_cursor, preface_top, writer.page_h - preface_bottom)],
                margin_left=preface_left,
                margin_right=preface_right,
            )
            return page_cursor + 1

        pages = writer.pages_for_height(estimate / max(1, columns))
        pages = ir_projection.planned_story_pages(
            self.page_plan, title, pages,
        )
        self.toc.note_h1s(blocks, page_cursor, pages)
        first_h1 = next((text for kind, text in blocks if kind == "h1"), "")
        first_kind = next((kind for kind, _ in blocks if kind != "layout"), "")
        master_offsets = {"WARRANTY": 12.30, "APP SETUP": 13.13}
        if is_operation:
            # The approved EN/FR/ES fourth operation pages deliberately carry
            # the Key panel below the ordinary body-text bottom margin.  The
            # extra frame depth is invisible, but keeps that anchored panel
            # inside the linked story instead of turning the final paragraph
            # into native InDesign overset.
            bottom_extra = param_pt(
                writer.params,
                "comp_operation_page_extra_height",
                18.0,
            )
        elif first_h1 == "WARRANTY":
            bottom_extra = param_pt(
                writer.params,
                "comp_warranty_page_extra_height",
                17.0,
            )
        elif is_charging_methods or is_charging_intro:
            # The approved charging compositions end on a dense final frame.
            # Reuse the contracted 18 pt deep-frame allowance used by the
            # adjacent editable operation composition so InDesign does not
            # mark the final charging paragraph overset.
            bottom_extra = param_pt(
                writer.params,
                "comp_operation_page_extra_height",
                18.0,
            )
            if title.casefold().startswith("p29_08_"):
                # The approved French charging page carries the longest
                # localized copy in the final frame.
                bottom_extra += 36.0
        else:
            bottom_extra = 0.0
        writer.add_spread_chain(
            sid, pages, page_cursor, columns=columns,
            bottom_extra=bottom_extra,
            last_frame_x_offset=final_frame_x_offset,
            first_top_offset=(
                23.8
                if is_charging_methods
                else 15.06
                if is_app
                else (
                    master_offsets.get(first_h1, 13.81)
                    if first_kind == "h1" else 0.0
                )
            ))
        return page_cursor + pages
