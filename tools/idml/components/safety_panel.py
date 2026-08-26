"""Complete editable standard Safety panel."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..page_objects import (
    frame_with_background,
    h1_bar_h_pt,
    h1_frame_opts,
    heading_bar_opts,
    heading_text,
    with_rounded_outer,
)
from ..params import component_param_pt, param_pt
from ..safety_story import _safety_language
from ..source_copy import source_block_text
from .fixed_panel_contract import FrameRect


def _split_section_at_list(
    blocks: list[tuple[str, str]],
    left_list_items: int,
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    seen = 0
    for index, (kind, _text) in enumerate(blocks):
        if kind != "list":
            continue
        if seen == left_list_items:
            return blocks[:index], blocks[index:]
        seen += 1
    raise ValueError(
        "approved safety-page split exceeds the available first-section "
        "list items"
    )


def _approved_param(writer, key: str, default: float) -> float:
    return component_param_pt(
        writer.params,
        key,
        default,
        strict=writer.strict_component_assets,
        owner="safety-page",
    )


@dataclass(frozen=True)
class SafetyPanelData:
    story_title: str
    h1: str
    top_warning: str | None
    subbar: str
    sections: tuple[tuple[tuple[str, str], ...], ...]

    @classmethod
    def from_blocks(
        cls,
        blocks: list[tuple[str, str]],
        *,
        story_title: str,
    ) -> "SafetyPanelData":
        sections: list[tuple[tuple[str, str], ...]] = []
        current: list[tuple[str, str]] | None = None
        for kind, text in blocks:
            if kind == "layout" and text == "twocol_start":
                current = []
            elif kind == "layout" and text == "twocol_end":
                if current is not None:
                    sections.append(tuple(current))
                current = None
            elif current is not None:
                current.append((kind, text))
        return cls(
            story_title=story_title,
            h1=source_block_text(
                blocks,
                "h1",
                owner="Safety page title",
            ),
            top_warning=next((
                text
                for kind, text in blocks
                if kind == "component" and any(
                    f'"kind": "{name}"' in text
                    for name in ("safetywarning", "safetyinstruction")
                )
            ), None),
            subbar=source_block_text(
                blocks,
                "h2",
                owner="Safety operating-instructions title",
            ),
            sections=tuple(sections),
        )


@dataclass(frozen=True)
class SafetyPanelContract:
    language: str
    frame_rects: tuple[FrameRect, ...]


@dataclass(frozen=True)
class SafetyPanelRender:
    story_ids: tuple[str, ...]
    frames: tuple[str, ...]
    contract: SafetyPanelContract


class SafetyPanel:
    """Own every story and internal frame of the standard Safety block."""

    def __init__(
        self,
        writer,
        *,
        sid: str,
        data: SafetyPanelData,
        bundle_root: Path,
    ) -> None:
        self.writer = writer
        self.sid = sid
        self.data = data
        self.bundle_root = bundle_root

    def _add_stories(
        self,
    ) -> tuple[str, str, str, list[tuple[str, str | None]]]:
        writer = self.writer
        sid = self.sid
        title = self.data.story_title
        title_sid = f"{sid}_title"
        writer._add_story_parts(
            title_sid,
            f"{title} title",
            [heading_text(writer, self.data.h1, level=1)],
        )
        warning_sid = f"{sid}_top_warning"
        if self.data.top_warning:
            xml_part, _ = writer._render_component(
                warning_sid,
                0,
                json.loads(self.data.top_warning),
                self.bundle_root,
                terminal=True,
                span_columns=False,
            )
            writer._add_story_parts(
                warning_sid,
                f"{title} warning",
                [xml_part],
            )
        bar_sid = f"{sid}_subbar"
        writer._add_story_parts(
            bar_sid,
            f"{title} subbar",
            [heading_text(writer, self.data.subbar, level=2)],
        )

        language = _safety_language(sid)
        dense = writer.strict_component_assets and language in {"fr", "es"}
        section_sids: list[tuple[str, str | None]] = []
        for index, frozen_section in enumerate(self.data.sections[:2]):
            section = list(frozen_section)
            section_sid = f"{sid}_section{index + 1}"
            if index == 0 and dense:
                base_left_count = _approved_param(
                    writer,
                    "idml_safety_first_section_left_list_items",
                    5.0,
                )
                left_count = round(_approved_param(
                    writer,
                    f"lang_{language}_idml_safety_first_section_left_list_items",
                    base_left_count,
                ))
                left_blocks, right_blocks = _split_section_at_list(
                    section,
                    left_count,
                )
                left_sid = f"{section_sid}_left"
                right_sid = f"{section_sid}_right"
                writer._safety_section_story(
                    left_sid,
                    f"{title} section {index + 1} left",
                    left_blocks,
                    self.bundle_root,
                )
                writer._safety_section_story(
                    right_sid,
                    f"{title} section {index + 1} right",
                    right_blocks,
                    self.bundle_root,
                )
                section_sids.append((left_sid, right_sid))
            else:
                writer._safety_section_story(
                    section_sid,
                    f"{title} section {index + 1}",
                    section,
                    self.bundle_root,
                )
                section_sids.append((section_sid, None))
        return title_sid, warning_sid, bar_sid, section_sids

    def render(
        self,
        *,
        x: float,
        y: float,
        width: float,
        available_height: float,
    ) -> SafetyPanelRender:
        del available_height
        writer = self.writer
        title_sid, warning_sid, bar_sid, sections = self._add_stories()
        language = _safety_language(self.sid)
        dense = writer.strict_component_assets and language in {"fr", "es"}
        column_gap = param_pt(writer.params, "comp_twocol_sep", 6.24)
        warning_top = _approved_param(
            writer,
            "idml_safety_warning_top",
            55.5,
        )
        warning_height = _approved_param(
            writer,
            "idml_safety_warning_height",
            31.5,
        )
        second_top = _approved_param(
            writer,
            "idml_safety_second_section_top",
            281.88,
        )
        second_height = _approved_param(
            writer,
            "idml_safety_second_section_height",
            209.12,
        )
        subbar_height = param_pt(writer.params, "comp_subbar_height", 13.9)
        subbar_top = 263.0
        if dense:
            warning_top = _approved_param(
                writer,
                f"lang_{language}_idml_safety_warning_top",
                warning_top,
            )
            warning_height = _approved_param(
                writer,
                f"lang_{language}_idml_safety_warning_height",
                warning_height,
            )
            second_height = _approved_param(
                writer,
                f"lang_{language}_idml_safety_second_section_height",
                second_height,
            )

        title_height = h1_bar_h_pt(writer)
        title_rect = (x, y + 27.92, width, title_height)
        definitions = (
            (
                "title",
                title_sid,
                title_rect,
                h1_frame_opts(title_rect),
            ),
            (
                "warning",
                warning_sid,
                (x, y + warning_top, width, warning_height),
                with_rounded_outer({
                    "inset": (0, 0, 0, 0),
                    "valign": "CenterAlign",
                }),
            ),
            (
                "section1",
                sections[0][0] if sections else "",
                (x, y + 95.77, width, 162.0),
                {
                    "columns": 2,
                    "gutter": column_gap,
                    "balance_columns": True,
                    "inset": (0, 0, 0, 0),
                },
            ),
            (
                "subbar",
                bar_sid,
                (x, y + subbar_top, width, subbar_height),
                {
                    **heading_bar_opts(2, (0.5, 0, 0.5, 0)),
                    "text_rect": (
                        x + 6.0,
                        y + subbar_top,
                        width - 12.0,
                        subbar_height,
                    ),
                },
            ),
            (
                "section2",
                sections[1][0] if len(sections) > 1 else "",
                (x, y + second_top, width, second_height),
                {
                    "columns": 2,
                    "gutter": column_gap,
                    "balance_columns": True,
                    "inset": (0, 0, 0, 0),
                },
            ),
        )
        frames: list[str] = []
        frame_rects: list[FrameRect] = []
        for frame_id, story_id, rect, options in definitions:
            if not story_id:
                continue
            if frame_id == "section1" and dense:
                base_gap = _approved_param(
                    writer,
                    "idml_safety_first_section_column_gap",
                    13.4,
                )
                gap = _approved_param(
                    writer,
                    f"lang_{language}_idml_safety_first_section_column_gap",
                    base_gap,
                )
                base_left_top = _approved_param(
                    writer,
                    "idml_safety_first_section_left_top",
                    95.77,
                )
                left_top = _approved_param(
                    writer,
                    f"lang_{language}_idml_safety_first_section_left_top",
                    base_left_top,
                )
                base_right_top = _approved_param(
                    writer,
                    "idml_safety_first_section_right_top",
                    base_left_top,
                )
                right_top = _approved_param(
                    writer,
                    f"lang_{language}_idml_safety_first_section_right_top",
                    base_right_top,
                )
                bottom = _approved_param(
                    writer,
                    "idml_safety_first_section_bottom",
                    257.77,
                )
                bottom = _approved_param(
                    writer,
                    f"lang_{language}_idml_safety_first_section_bottom",
                    bottom,
                )
                minimum_gap = _approved_param(
                    writer,
                    "idml_safety_first_section_to_subbar_gap",
                    4.0,
                )
                bottom = min(bottom, subbar_top - minimum_gap)
                column_width = (width - gap) / 2.0
                left_rect = (
                    x,
                    y + left_top,
                    column_width,
                    bottom - left_top,
                )
                right_rect = (
                    x + column_width + gap,
                    y + right_top,
                    column_width,
                    bottom - right_top,
                )
                frames.extend((
                    frame_with_background(
                        writer,
                        self.sid,
                        "section1_left",
                        story_id,
                        left_rect,
                        {"inset": (0, 0, 0, 0)},
                    ),
                    frame_with_background(
                        writer,
                        self.sid,
                        "section1_right",
                        sections[0][1] or "",
                        right_rect,
                        {"inset": (0, 0, 0, 0)},
                    ),
                ))
                frame_rects.extend((
                    ("section1_left", left_rect),
                    ("section1_right", right_rect),
                ))
                continue
            frames.append(frame_with_background(
                writer,
                self.sid,
                frame_id,
                story_id,
                rect,
                options,
            ))
            frame_rects.append((frame_id, rect))

        story_ids = [title_sid]
        if self.data.top_warning:
            story_ids.append(warning_sid)
        story_ids.append(bar_sid)
        story_ids.extend(
            story_id
            for pair in sections
            for story_id in pair
            if story_id
        )
        return SafetyPanelRender(
            story_ids=tuple(story_ids),
            frames=tuple(frames),
            contract=SafetyPanelContract(
                language=language,
                frame_rects=tuple(frame_rects),
            ),
        )


__all__ = [
    "SafetyPanel",
    "SafetyPanelContract",
    "SafetyPanelData",
    "SafetyPanelRender",
]
