"""Production-master page regions for English prose stories."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import ir_projection
from .params import param_pt


@dataclass
class ReferenceStoryEmitter:
    writer: object
    toc: object
    bundle_root: Path
    page_plan: object
    charging_method_prefix: list[tuple[str, str]] = field(default_factory=list)

    def emit(self, sid: str, title: str, blocks: list[tuple[str, str]],
             page_cursor: int, columns: int = 1) -> int:
        """Emit one story and return the next/shareable page cursor."""
        writer = self.writer
        self.toc.latch(title)
        if title == "08_charging_methods" and self.charging_method_prefix:
            blocks = self.charging_method_prefix + blocks
            self.charging_method_prefix = []
        first_h1 = next((text for kind, text in blocks if kind == "h1"), "")
        if first_h1 == "UNINTERRUPTIBLE POWER SUPPLY (UPS)":
            return self._emit_ups_and_charging(sid, title, blocks, page_cursor)

        _, estimate = writer.add_prose_story(
            sid, title, blocks, self.bundle_root)
        shared_regions = {
            "05_operation_guide_placeholder": (
                [(page_cursor, 26.67, writer.page_h - writer.m_b)]
                + [(page_cursor + offset, writer.m_t, writer.page_h - writer.m_b)
                   for offset in range(1, 4)],
                4,
            ),
            "09_storage_and_maintenance": ([(page_cursor, 103.50, 202.0)], 0),
            "troubleshooting_en": ([(page_cursor, 204.43, 504.0)], 1),
        }
        if title in shared_regions:
            frames, consumed_pages = shared_regions[title]
            self.toc.note_h1s(blocks, page_cursor, len(frames))
            writer.add_story_frames(sid, frames)
            return page_cursor + consumed_pages
        if title == "08_charging_methods":
            writer.add_story_frames(sid, [
                (page_cursor, writer.m_t, writer.page_h - writer.m_b),
                (page_cursor + 1, writer.m_t, writer.page_h - writer.m_b),
                (page_cursor + 2, writer.m_t, 103.50),
            ])
            return page_cursor + 2

        pages = writer.pages_for_height(estimate / max(1, columns))
        pages = ir_projection.planned_story_pages(
            self.page_plan, title, pages)
        self.toc.note_h1s(blocks, page_cursor, pages)
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

    def _emit_ups_and_charging(
        self,
        sid: str,
        title: str,
        blocks: list[tuple[str, str]],
        page_cursor: int,
    ) -> int:
        writer = self.writer
        split_at = next(
            index for index, block in enumerate(blocks)
            if block == ("h1", "CHARGING")
        )
        ups_blocks = blocks[:split_at]
        charging_blocks = blocks[split_at:]
        method_at = next(
            index for index, block in enumerate(charging_blocks)
            if block == ("h2", "CHARGING VIA AC WALL OUTLET")
        )
        charging_intro = charging_blocks[:method_at]
        self.charging_method_prefix = charging_blocks[method_at:]
        ups_sid = sid + "_ups"
        charging_sid = sid + "_charging"
        writer.add_prose_story(
            ups_sid, title + " UPS", ups_blocks, self.bundle_root)
        writer.add_prose_story(
            charging_sid, title + " CHARGING", charging_intro,
            self.bundle_root)
        writer.add_story_frames(ups_sid, [(page_cursor, 33.04, 365.0)])
        writer.add_story_frames(
            charging_sid,
            [(
                page_cursor,
                367.42,
                # The LaTeX-parity NOTE is taller than the legacy strip. The
                # production page still has an 18 pt footer-safe region below
                # the normal body margin, also used by the LCD continuation.
                writer.page_h - 4.0,
            )],
        )
        self.toc.note_h1s(ups_blocks, page_cursor, 1)
        self.toc.note_h1s(charging_intro, page_cursor, 1)
        return page_cursor + 1
