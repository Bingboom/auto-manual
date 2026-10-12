"""Production IDML story emission with natural prose flow.

Fixed composite pages are flushed and composed by ``export_idml``.  This
module owns the remaining editable prose stories and gives each one a normal
linked spread chain, so ordinary sections can flow across component/page
boundaries without inheriting the LaTeX reference page breaks.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .language_contract import governed_languages
from . import ir_projection
from .asset_contracts import (
    APP_ADD_DEVICE_COMPONENT,
    plan_page_owns_component,
)
from .params import localized_param_pt, param_pt
from .composition_plan import is_explicit_assembly_plan
from .page_roles import classify_page_role
from .prose_flow import (
    DEDICATED_SECTION_ROLES,
    apply_component_composition_data,
    component_kind,
    composition_language,
    composition_type,
    operation_final_frame_x_offset,
    operation_language,
)


def storage_first_top_offset(
    params: dict[str, tuple[str, str]], language: str | None,
) -> float:
    """Return the approved car-notice continuation offset on storage pages.

    Ungoverned languages get no offset at all — not the base value: the base
    row encodes the governed reference flow, which measured fallback pages do
    not follow.
    """
    code = (language or "").split("-", 1)[0].strip().casefold()
    if code not in governed_languages():
        return 0.0
    return localized_param_pt(
        params, "idml_storage_page_top_offset", 0.0, language=code,
    )


@dataclass(frozen=True)
class _StoryTraits:
    """What the page plan and the story's own blocks say about one prose story."""

    plan_source: object
    measured_fallback: bool
    operation_lang: str | None
    composition_lang: str | None
    planned_composition_type: str | None
    effective_warranty_lang: str | None
    is_operation: bool
    is_charging_methods: bool
    is_charging_intro: bool
    is_app: bool
    is_storage_troubleshooting: bool
    is_measured_troubleshooting: bool
    is_measured_overview: bool
    is_warranty: bool


def _warranty_traits(
    registered_components: bool,
    writer: object,
    blocks: list[tuple[str, str]],
    *,
    composition_lang: str | None,
    planned_composition_type: str | None,
    approved_warranty_title: bool,
) -> tuple[str | None, bool]:
    """Return ``(effective warranty language, is a governed warranty story)``."""
    has_warranty_components = registered_components and any(
        kind == "component" and component_kind(payload) in {
            "warrantylead", "warrantysection", "warrantyyears",
        }
        for kind, payload in blocks
    )
    effective_warranty_lang = composition_lang or (
        writer.language if has_warranty_components else None
    )
    is_warranty = (
        (
            planned_composition_type == "warranty"
            or has_warranty_components
            or approved_warranty_title
        )
        and effective_warranty_lang in governed_languages()
    )
    return effective_warranty_lang, is_warranty


def _story_traits(
    page_plan: dict | None,
    registered_components: bool,
    writer: object,
    title: str,
    blocks: list[tuple[str, str]],
) -> _StoryTraits:
    plan_source = (page_plan or {}).get("plan_source")
    approved = plan_source == "approved-reference"
    measured_fallback = page_plan is not None and plan_source != "approved-reference"
    normalized_title = title.casefold()
    operation_lang = operation_language(blocks, page_plan, title)
    composition_lang = composition_language(page_plan, title)
    planned_composition_type = composition_type(page_plan, title)
    effective_warranty_lang, is_warranty = _warranty_traits(
        registered_components,
        writer,
        blocks,
        composition_lang=composition_lang,
        planned_composition_type=planned_composition_type,
        approved_warranty_title=approved and "warranty" in normalized_title,
    )
    is_app = plan_page_owns_component(
        page_plan,
        title,
        component=APP_ADD_DEVICE_COMPONENT,
    )
    return _StoryTraits(
        plan_source=plan_source,
        measured_fallback=measured_fallback,
        operation_lang=operation_lang,
        composition_lang=composition_lang,
        planned_composition_type=planned_composition_type,
        effective_warranty_lang=effective_warranty_lang,
        is_operation=approved and "operation_guide" in title and operation_lang is not None,
        is_charging_methods=approved and "charging_methods" in title,
        is_charging_intro=(
            approved
            and "charging" in normalized_title
            and "charging_methods" not in normalized_title
        ),
        is_app=is_app,
        is_storage_troubleshooting=(
            approved
            and "storage_and_maintenance" in title
            and "troubleshooting" in title
        ),
        is_measured_troubleshooting=(
            measured_fallback
            and "troubleshooting" in normalized_title
            and ("charging" in normalized_title or "storage" in normalized_title)
        ),
        is_measured_overview=measured_fallback and "product_overview" in normalized_title,
        is_warranty=is_warranty,
    )


_MASTER_OFFSETS = {"WARRANTY": 12.30, "APP SETUP": 13.13}


def _final_frame_x_offset(params: dict[str, tuple[str, str]], traits: _StoryTraits) -> float:
    warranty_frame_x_offset = (
        param_pt(
            params,
            f"lang_{traits.effective_warranty_lang}_idml_warranty_frame_x_offset",
            0.0,
        )
        if traits.is_warranty else 0.0
    )
    return (
        operation_final_frame_x_offset(traits.operation_lang)
        if traits.is_operation else warranty_frame_x_offset
    )


def _bottom_extra(params: dict[str, tuple[str, str]], traits: _StoryTraits, title: str) -> float:
    """Invisible frame depth that keeps a page's anchored panel inside its story."""
    if traits.is_operation:
        # The approved EN/FR/ES fourth operation pages deliberately carry
        # the Key panel below the ordinary body-text bottom margin.  The
        # extra frame depth is invisible, but keeps that anchored panel
        # inside the linked story instead of turning the final paragraph
        # into native InDesign overset.
        shared_operation_extra = param_pt(
            params,
            "comp_operation_page_extra_height",
            18.0,
        )
        return param_pt(
            params,
            f"lang_{traits.operation_lang}_comp_operation_page_extra_height",
            shared_operation_extra,
        )
    if traits.is_storage_troubleshooting or traits.is_measured_troubleshooting:
        # The governed troubleshooting panel reaches the reference's
        # lower trim rhythm. Keep its complete editable anchored group in
        # the story with an invisible frame-depth allowance; never shrink
        # localized rows or rely on the finalizer to hide overflow.
        return param_pt(
            params,
            "comp_trouble_page_extra_height",
            32.0,
        )
    if traits.is_measured_overview:
        # Measured-LaTeX fallback may deliberately compose FCC, inbox, and
        # Product Overview on one physical page. Preserve the existing
        # editable components and give only the final carrier frame a small
        # invisible import allowance for anchored-object markers.
        return param_pt(
            params,
            "idml_measured_overview_page_extra_height",
            8.0,
        )
    if traits.is_warranty:
        shared_warranty_extra = param_pt(
            params,
            "comp_warranty_page_extra_height",
            17.0,
        )
        return param_pt(
            params,
            f"lang_{traits.effective_warranty_lang}_comp_warranty_page_extra_height",
            shared_warranty_extra,
        )
    if traits.is_app:
        # Localized App notes remain fully editable at reference sizes.
        # The extra frame depth is outside the visible page and prevents
        # longer French/Spanish copy from becoming native story overset.
        return param_pt(
            params,
            "idml_app_page_extra_height",
            48.0,
        )
    if traits.is_charging_methods or traits.is_charging_intro:
        # The approved charging compositions end on a dense final frame.
        # Reuse the contracted 18 pt deep-frame allowance used by the
        # adjacent editable operation composition so InDesign does not
        # mark the final charging paragraph overset.
        bottom_extra = param_pt(
            params,
            "comp_operation_page_extra_height",
            18.0,
        )
        if title.casefold().startswith("p29_08_"):
            # The approved French charging page carries the longest
            # localized copy in the final frame.
            bottom_extra += 36.0
        return bottom_extra
    return 0.0


def _first_top_offset(
    params: dict[str, tuple[str, str]],
    traits: _StoryTraits,
    *,
    is_ups_charging: bool,
    first_h1: str,
    first_kind: str,
) -> float:
    """Top offset of the story's first frame on its page."""
    if traits.is_charging_methods:
        return param_pt(
            params,
            f"lang_{traits.composition_lang}_idml_charging_methods_page_top_offset",
            param_pt(
                params,
                "idml_charging_methods_page_top_offset",
                23.8,
            ),
        )
    if is_ups_charging:
        return param_pt(
            params,
            f"lang_{traits.composition_lang}_idml_ups_page_top_offset",
            13.81,
        )
    if traits.is_app:
        return 15.06
    if traits.is_storage_troubleshooting:
        return storage_first_top_offset(params, traits.composition_lang)
    if traits.is_warranty:
        return param_pt(
            params,
            f"lang_{traits.effective_warranty_lang}_idml_warranty_page_top_offset",
            _MASTER_OFFSETS.get(first_h1, 13.81),
        )
    return _MASTER_OFFSETS.get(first_h1, 13.81) if first_kind == "h1" else 0.0



@dataclass
class ReferenceStoryEmitter:
    writer: object
    toc: object
    bundle_root: Path
    page_plan: dict | None = None
    # An active component target's warranty story takes the governed warranty
    # frame from its registered components; no other build reads this.
    registered_components: bool = False
    # (title, height-estimate pages, allocated pages).  A story allocated more
    # frames than its content composes into is exactly the trailing-blank-page
    # failure mode; recording both numbers makes the source of each span
    # visible in the exporter report instead of only in a native screenshot.
    spans: list[tuple[str, int, int]] = field(default_factory=list)

    def report_spans(self) -> None:
        """Report each prose story's allocated spread chain and its estimate.

        ``pages_for_height`` rounds up, so a story whose allocated span exceeds
        what InDesign actually composes leaves trailing empty linked frames — the
        "blank body page" screenshots report.  Printing the allocation next to the
        height estimate names the responsible story without opening the package.
        """
        spans = self.spans
        if not spans:
            return
        total = sum(pages for _, _, pages in spans)
        detail = " ".join(
            f"{title}={pages}"
            + ("" if pages == estimated else f"(est{estimated})")
            for title, estimated, pages in spans
        )
        print(f"[export-idml] STORY SPANS: pages={total} | {detail}")

    def _prose_options(
        self, traits: _StoryTraits, final_frame_x_offset: float, columns: int,
    ) -> dict[str, float | str]:
        prose_options: dict[str, float | str] = {
            "inline_origin_shift": final_frame_x_offset,
        }
        if traits.planned_composition_type is not None:
            prose_options["semantic_page_role"] = traits.planned_composition_type
        story_language = (
            traits.operation_lang or traits.composition_lang or traits.effective_warranty_lang
        )
        if story_language is not None:
            prose_options["language"] = story_language
        # A measured plan caps the chain at this estimate, so it counts the
        # frame foot an unbreakable figure leaves; an approved assembly plan
        # fixes the span itself.
        if (
            columns == 1
            and traits.measured_fallback
            and not is_explicit_assembly_plan(self.page_plan)
        ):
            prose_options["figure_frame_height"] = self.writer.frame_height()
        return prose_options

    def _emit_preface(self, sid: str, title: str, page_cursor: int, plan_source: object) -> int:
        writer = self.writer
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
        # A target assembly may explicitly allocate a multilingual
        # preface more than one physical page.  A measured fallback plan,
        # however, may merely leave a physical gap before the next source;
        # that gap is not a request to thread the preface story through
        # blank frames.
        pages = (
            ir_projection.planned_story_pages(
                self.page_plan,
                title,
                1,
            )
            if plan_source == "target-assembly"
            else 1
        )
        self.spans.append((title, 1, pages))
        writer.add_story_frames(
            sid,
            [
                (
                    page_cursor + offset,
                    preface_top,
                    writer.page_h - preface_bottom,
                )
                for offset in range(pages)
            ],
            margin_left=preface_left,
            margin_right=preface_right,
        )
        return page_cursor + pages

    def _planned_pages(
        self, title: str, blocks: list[tuple[str, str]], estimated_pages: int,
    ) -> int:
        pages = ir_projection.planned_story_pages(
            self.page_plan, title, estimated_pages,
        )
        # A dedicated back-matter section no longer shares a linked chain with
        # its neighbour, so it can no longer borrow the following section's
        # frames.  Under a measured fallback plan the LaTeX anchor distance may
        # be shorter than the section's own content; honouring it there is what
        # compresses Warranty past the bottom body margin.  An approved
        # assembly contract stays authoritative.
        if (
            pages < estimated_pages
            and not is_explicit_assembly_plan(self.page_plan)
            and any(
                classify_page_role(Path(stem)) in DEDICATED_SECTION_ROLES
                for stem in title.split(" + ")
            )
        ):
            pages = estimated_pages
        # The same fallback plan measures a *different* composition engine, so
        # LaTeX may spread a section over more physical pages than the IDML
        # writer composes it into, and every surplus frame in the chain is a
        # blank body page.  Cap the span at what this story needs on its own:
        # its height estimate, or one frame per explicitly authored page break,
        # whichever is larger.  Overset is the recoverable failure here and
        # InDesign marks it; a blank page is neither.
        if (
            pages > estimated_pages
            and not is_explicit_assembly_plan(self.page_plan)
        ):
            authored_breaks = sum(
                1 for kind, text in blocks
                if kind == "layout" and text.startswith("page_break")
            )
            pages = max(estimated_pages, authored_breaks + 1)
        return pages

    def emit(self, sid: str, title: str, blocks: list[tuple[str, str]],
             page_cursor: int, columns: int = 1) -> int:
        """Emit one editable prose story and return the next page cursor."""
        writer = self.writer
        self.toc.latch(title)
        traits = _story_traits(
            self.page_plan, self.registered_components, writer, title, blocks,
        )
        final_frame_x_offset = _final_frame_x_offset(writer.params, traits)
        prose_options = self._prose_options(traits, final_frame_x_offset, columns)
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
        if traits.planned_composition_type == "preface" or title == "00_preface":
            return self._emit_preface(sid, title, page_cursor, traits.plan_source)

        estimated_pages = writer.pages_for_height(estimate / max(1, columns))
        pages = self._planned_pages(title, blocks, estimated_pages)
        self.spans.append((title, estimated_pages, pages))
        self.toc.note_h1s(blocks, page_cursor, pages)
        first_h1 = next((text for kind, text in blocks if kind == "h1"), "")
        first_kind = next((kind for kind, _ in blocks if kind != "layout"), "")
        is_ups_charging = (
            traits.plan_source == "approved-reference"
            and "ups_mode" in title.casefold()
            and "charging" in title.casefold()
            and traits.composition_lang in governed_languages()
        )
        bottom_extra = _bottom_extra(writer.params, traits, title)
        writer.add_spread_chain(
            sid, pages, page_cursor, columns=columns,
            bottom_extra=bottom_extra,
            last_frame_x_offset=final_frame_x_offset,
            first_top_offset=_first_top_offset(
                writer.params,
                traits,
                is_ups_charging=is_ups_charging,
                first_h1=first_h1,
                first_kind=first_kind,
            ))
        return page_cursor + pages
