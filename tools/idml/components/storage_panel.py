"""Complete editable Storage panel for compact shared pages."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..page_objects import (
    frame_with_background,
    h1_bar_h_pt,
    heading_bar_opts,
    heading_text,
)
from ..params import param_pt
from ..source_copy import source_text
from .fixed_panel_contract import FrameRect, normalize_language


@dataclass(frozen=True)
class StoragePanelData:
    title: str
    body_blocks: tuple[tuple[str, str], ...]

    @classmethod
    def from_blocks(
        cls,
        blocks: list[tuple[str, str]],
    ) -> "StoragePanelData":
        title = source_text(
            next((text for kind, text in blocks if kind == "h1"), ""),
            owner="Storage page title",
        )
        if not title:
            raise ValueError("storage_specifications requires a Storage H1")
        return cls(
            title=title,
            body_blocks=tuple(
                block for block in blocks if block[0] != "h1"
            ),
        )


@dataclass(frozen=True)
class StoragePanelContract:
    language: str
    frame_rects: tuple[FrameRect, ...]


@dataclass(frozen=True)
class StoragePanelRender:
    title_story_id: str
    body_story_id: str
    frames: tuple[str, ...]
    contract: StoragePanelContract


class StoragePanel:
    """Own the Storage title, body card, fill, radius, and inset."""

    def __init__(
        self,
        writer,
        *,
        sid: str,
        data: StoragePanelData,
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
    ) -> StoragePanelRender:
        writer = self.writer
        title_sid = f"{self.sid}_storage_title"
        body_sid = f"{self.sid}_storage_body"
        writer._add_story_parts(
            title_sid,
            f"{self.data.title} title",
            [heading_text(writer, self.data.title, level=1)],
        )
        writer.add_prose_story(
            body_sid,
            f"{self.data.title} body",
            list(self.data.body_blocks),
            self.bundle_root,
            language=self.language,
            disable_hyphenation=True,
        )

        baseline_y = param_pt(
            writer.params,
            "idml_shared_page_top",
            27.7,
        )
        title_height = h1_bar_h_pt(writer)
        body_top = y + param_pt(
            writer.params,
            "idml_compact_storage_spec_body_top",
            59.0,
        ) - baseline_y
        body_bottom = y + param_pt(
            writer.params,
            "idml_compact_storage_spec_body_bottom",
            131.5,
        ) - baseline_y
        if not y + title_height < body_top < body_bottom < y + available_height:
            raise ValueError("StoragePanel frame tokens are not ordered")
        body_inset = param_pt(
            writer.params,
            "idml_compact_storage_spec_body_inset",
            6.0,
        )
        title_rect = (x, y, width, title_height)
        body_rect = (x, body_top, width, body_bottom - body_top)
        frames = (
            frame_with_background(
                writer,
                self.sid,
                "storage_title",
                title_sid,
                title_rect,
                {
                    **heading_bar_opts(1, (1.5, 5, 1, 6)),
                    "text_rect": (
                        x + 6.0,
                        y,
                        width - 12.0,
                        title_height,
                    ),
                },
            ),
            frame_with_background(
                writer,
                self.sid,
                "storage_body",
                body_sid,
                body_rect,
                {
                    "fill": "Color/HB Bg K05",
                    "rounded": True,
                    "inset": (
                        body_inset,
                        body_inset,
                        body_inset,
                        body_inset,
                    ),
                },
            ),
        )
        return StoragePanelRender(
            title_story_id=title_sid,
            body_story_id=body_sid,
            frames=frames,
            contract=StoragePanelContract(
                language=self.language,
                frame_rects=(("title", title_rect), ("body", body_rect)),
            ),
        )


__all__ = [
    "StoragePanel",
    "StoragePanelContract",
    "StoragePanelData",
    "StoragePanelRender",
]
