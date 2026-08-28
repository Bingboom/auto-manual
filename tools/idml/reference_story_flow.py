"""Production IDML story emission with natural prose flow.

Fixed composite pages are flushed and composed by ``export_idml``.  This
module owns the remaining editable prose stories and gives each one a normal
linked spread chain, so ordinary sections can flow across component/page
boundaries without inheriting the LaTeX reference page breaks.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .language_contract import governed_languages
from . import ir_projection
from .asset_contracts import (
    APP_ADD_DEVICE_COMPONENT,
    plan_page_owns_component,
)
from .params import param_pt
from .prose_flow import (
    apply_component_composition_data,
    composition_language,
    composition_type,
    operation_final_frame_x_offset,
    operation_language,
)


def storage_first_top_offset(
    params: dict[str, tuple[str, str]], language: str | None,
) -> float:
    """Return the approved car-notice continuation offset on storage pages."""
    if language not in governed_languages():
        return 0.0
    return param_pt(
        params,
        f"lang_{language}_idml_storage_page_top_offset",
        param_pt(params, "idml_storage_page_top_offset", 0.0),
    )


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
        plan_source = (self.page_plan or {}).get("plan_source")
        measured_fallback = self.page_plan is not None and plan_source != "approved-reference"
        normalized_title = title.casefold()
        operation_lang = operation_language(blocks, self.page_plan, title)
        composition_lang = composition_language(self.page_plan, title)
        planned_composition_type = composition_type(self.page_plan, title)
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
        is_app = plan_page_owns_component(
            self.page_plan,
            title,
            component=APP_ADD_DEVICE_COMPONENT,
        )
        is_storage_troubleshooting = (
            plan_source == "approved-reference"
            and "storage_and_maintenance" in title
            and "troubleshooting" in title
        )
        is_measured_troubleshooting = (
            measured_fallback
            and "troubleshooting" in normalized_title
            and (
                "charging" in normalized_title
                or "storage" in normalized_title
            )
        )
        is_measured_overview = (
            measured_fallback
            and "product_overview" in normalized_title
        )
        is_warranty = (
            (
                planned_composition_type == "warranty"
                or (
                    (self.page_plan or {}).get("plan_source")
                    == "approved-reference"
                    and "warranty" in title.casefold()
                )
            )
            and composition_lang in governed_languages()
        )
        warranty_frame_x_offset = (
            param_pt(
                writer.params,
                f"lang_{composition_lang}_idml_warranty_frame_x_offset",
                0.0,
            )
            if is_warranty else 0.0
        )
        final_frame_x_offset = (
            operation_final_frame_x_offset(operation_lang)
            if is_operation else warranty_frame_x_offset
        )
        prose_options: dict[str, float | str] = {
            "inline_origin_shift": final_frame_x_offset,
        }
        if planned_composition_type is not None:
            prose_options["semantic_page_role"] = planned_composition_type
        story_language = operation_lang or composition_lang
        if story_language is not None:
            prose_options["language"] = story_language
        blocks = apply_component_composition_data(
            blocks,
            self.page_plan,
            title,
        )
        _, estimate = writer.add_prose_story(
            sid,
            title,
            blocks,
            self.bundle_root,
            **prose_options,
        )
        if planned_composition_type == "preface" or title == "00_preface":
            preface_left = param_pt(
                writer.params, "idml_preface_margin_left", writer.m_l,
            )
            preface_right = param_pt(
                writer.params, "idml_preface_margin_right", writer.m_r,
            )
            preface_top = param_pt(
                writer.params,
                "idml_compact_preface_margin_top",
                param_pt(
                    writer.params, "idml_preface_margin_top", writer.m_t,
                ),
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
        is_ups_charging = (
            (self.page_plan or {}).get("plan_source") == "approved-reference"
            and "ups_mode" in title.casefold()
            and "charging" in title.casefold()
            and composition_lang in governed_languages()
        )
        master_offsets = {"WARRANTY": 12.30, "APP SETUP": 13.13}
        if is_operation:
            # The approved EN/FR/ES fourth operation pages deliberately carry
            # the Key panel below the ordinary body-text bottom margin.  The
            # extra frame depth is invisible, but keeps that anchored panel
            # inside the linked story instead of turning the final paragraph
            # into native InDesign overset.
            shared_operation_extra = param_pt(
                writer.params,
                "comp_operation_page_extra_height",
                18.0,
            )
            bottom_extra = param_pt(
                writer.params,
                f"lang_{operation_lang}_comp_operation_page_extra_height",
                shared_operation_extra,
            )
        elif is_storage_troubleshooting or is_measured_troubleshooting:
            # The governed troubleshooting panel reaches the reference's
            # lower trim rhythm. Keep its complete editable anchored group in
            # the story with an invisible frame-depth allowance; never shrink
            # localized rows or rely on the finalizer to hide overflow.
            bottom_extra = param_pt(
                writer.params,
                "comp_trouble_page_extra_height",
                32.0,
            )
        elif is_measured_overview:
            # Measured-LaTeX fallback may deliberately compose FCC, inbox, and
            # Product Overview on one physical page. Preserve the existing
            # editable components and give only the final carrier frame a small
            # invisible import allowance for anchored-object markers.
            bottom_extra = param_pt(
                writer.params,
                "idml_measured_overview_page_extra_height",
                8.0,
            )
        elif is_warranty:
            shared_warranty_extra = param_pt(
                writer.params,
                "comp_warranty_page_extra_height",
                17.0,
            )
            bottom_extra = param_pt(
                writer.params,
                f"lang_{composition_lang}_comp_warranty_page_extra_height",
                shared_warranty_extra,
            )
        elif is_app:
            # Localized App notes remain fully editable at reference sizes.
            # The extra frame depth is outside the visible page and prevents
            # longer French/Spanish copy from becoming native story overset.
            bottom_extra = param_pt(
                writer.params,
                "idml_app_page_extra_height",
                48.0,
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
                param_pt(
                    writer.params,
                    f"lang_{composition_lang}_idml_charging_methods_page_top_offset",
                    param_pt(
                        writer.params,
                        "idml_charging_methods_page_top_offset",
                        23.8,
                    ),
                )
                if is_charging_methods
                else param_pt(
                    writer.params,
                    f"lang_{composition_lang}_idml_ups_page_top_offset",
                    13.81,
                )
                if is_ups_charging
                else 15.06
                if is_app
                else storage_first_top_offset(writer.params, composition_lang)
                if is_storage_troubleshooting
                else param_pt(
                    writer.params,
                    f"lang_{composition_lang}_idml_warranty_page_top_offset",
                    master_offsets.get(first_h1, 13.81),
                )
                if is_warranty
                else (
                    master_offsets.get(first_h1, 13.81)
                    if first_kind == "h1" else 0.0
                )
            ))
        return page_cursor + pages
