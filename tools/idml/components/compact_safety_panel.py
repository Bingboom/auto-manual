"""Editable compact Safety block used above SymbolsPanel."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..page_objects import (
    frame_with_background,
    h1_bar_h_pt,
    h1_frame_opts,
    heading_text,
)
from ..params import param_pt
from ..source_copy import source_text
from .fixed_panel_contract import FrameRect, normalize_language


@dataclass(frozen=True)
class CompactSafetyPanelData:
    story_title: str
    title: str
    body_blocks: tuple[tuple[str, str], ...]

    @classmethod
    def from_blocks(
        cls,
        blocks: list[tuple[str, str]],
        *,
        story_title: str,
    ) -> "CompactSafetyPanelData":
        return cls(
            story_title=story_title,
            title=source_text(
                next((text for kind, text in blocks if kind == "h1"), ""),
                owner="compact Safety page title",
            ),
            body_blocks=tuple(
                block for block in blocks if block[0] != "h1"
            ),
        )


@dataclass(frozen=True)
class CompactSafetyPanelRender:
    story_ids: tuple[str, str]
    frames: tuple[str, str]
    frame_rects: tuple[FrameRect, FrameRect]


class CompactSafetyPanel:
    """Own the compact Safety title, body frame, inset, and typography."""

    def __init__(
        self,
        writer,
        *,
        sid: str,
        data: CompactSafetyPanelData,
        bundle_root: Path,
        language: str,
    ) -> None:
        self.writer = writer
        self.sid = sid
        self.data = data
        self.bundle_root = bundle_root
        self.language = normalize_language(language)

    def render(
        self,
        *,
        x: float,
        y: float,
        width: float,
        available_height: float,
    ) -> CompactSafetyPanelRender:
        writer = self.writer
        title_sid = f"{self.sid}_title"
        writer._add_story_parts(
            title_sid,
            self.data.title,
            [heading_text(writer, self.data.title, level=1)],
        )
        writer._safety_section_story(
            self.sid,
            self.data.story_title,
            list(self.data.body_blocks),
            self.bundle_root,
            compact=True,
        )
        title_height = h1_bar_h_pt(writer)
        title_body_gap = param_pt(
            writer.params,
            "idml_compact_safety_title_body_gap",
            3.5,
        )
        body_top = y + title_height + title_body_gap
        title_rect = (x, y, width, title_height)
        body_rect = (
            x,
            body_top,
            width,
            available_height - title_height - title_body_gap,
        )
        return CompactSafetyPanelRender(
            story_ids=(title_sid, self.sid),
            frames=(
                frame_with_background(
                    writer,
                    self.sid,
                    "safety_title",
                    title_sid,
                    title_rect,
                    h1_frame_opts(title_rect),
                ),
                frame_with_background(
                    writer,
                    self.sid,
                    "safety_body",
                    self.sid,
                    body_rect,
                    {"inset": (0, 0, 0, 0)},
                ),
            ),
            frame_rects=(("title", title_rect), ("body", body_rect)),
        )


__all__ = [
    "CompactSafetyPanel",
    "CompactSafetyPanelData",
    "CompactSafetyPanelRender",
]
