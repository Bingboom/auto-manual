"""Production IDML story emission with natural prose flow.

Fixed composite pages are flushed and composed by ``export_idml``.  This
module owns the remaining editable prose stories and gives each one a normal
linked spread chain, so ordinary sections can flow across component/page
boundaries without inheriting the LaTeX reference page breaks.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .params import param_pt


@dataclass
class ReferenceStoryEmitter:
    writer: object
    toc: object
    bundle_root: Path

    def emit(self, sid: str, title: str, blocks: list[tuple[str, str]],
             page_cursor: int, columns: int = 1) -> int:
        """Emit one editable prose story and return the next page cursor."""
        writer = self.writer
        self.toc.latch(title)
        _, estimate = writer.add_prose_story(
            sid, title, blocks, self.bundle_root)
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
        self.toc.note_h1s(blocks, page_cursor, pages)
        first_h1 = next((text for kind, text in blocks if kind == "h1"), "")
        first_kind = next((kind for kind, _ in blocks if kind != "layout"), "")
        master_offsets = {"WARRANTY": 12.30, "APP SETUP": 13.13}
        writer.add_spread_chain(
            sid, pages, page_cursor, columns=columns,
            bottom_extra=(
                param_pt(
                    writer.params, "comp_warranty_page_extra_height", 17.0,
                ) if first_h1 == "WARRANTY" else 0.0
            ),
            first_top_offset=(
                master_offsets.get(first_h1, 13.81)
                if first_kind == "h1" else 0.0
            ))
        return page_cursor + pages
