"""Storage section adapter that reuses the approved JE prose renderer."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ..page_objects import (
    frame_with_background,
    h1_bar_h_pt,
    h1_frame_opts,
    heading_text,
)
from ..params import param_pt
from ..source_copy import source_text
from .fixed_panel_contract import FrameRect, normalize_language


StoragePanelVariant = Literal["shared_prose", "rounded_panel"]


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
    renderer: StoragePanelVariant = "shared_prose"


@dataclass(frozen=True)
class StoragePanelRender:
    story_id: str
    contract: StoragePanelContract
    frames: tuple[str, ...] = ()
    frame_rects: tuple[FrameRect, ...] = ()


class StoragePanel:
    """Render Storage through the exact prose/H1 path used by JE-1000F.

    The compact page composer owns only the outer story rectangle.  This
    adapter deliberately defines no fill, corner radius, inset, title-frame
    geometry, or model-specific paragraph treatment.
    """

    def __init__(
        self,
        writer,
        *,
        sid: str,
        data: StoragePanelData,
        bundle_root: Path,
        language: str,
        layout_variant: StoragePanelVariant = "shared_prose",
    ) -> None:
        if layout_variant not in {"shared_prose", "rounded_panel"}:
            raise ValueError(
                f"unsupported Storage panel variant: {layout_variant}"
            )
        self.writer = writer
        self.sid = sid
        self.data = data
        self.bundle_root = bundle_root
        self.language = normalize_language(language)
        self.layout_variant = layout_variant

    def render(
        self,
        *,
        x: float | None = None,
        y: float | None = None,
        width: float | None = None,
        available_height: float | None = None,
    ) -> StoragePanelRender:
        if self.layout_variant == "shared_prose":
            self.writer.add_prose_story(
                self.sid,
                self.data.title,
                [("h1", self.data.title), *self.data.body_blocks],
                self.bundle_root,
                language=self.language,
                disable_hyphenation=True,
            )
            return StoragePanelRender(
                story_id=self.sid,
                contract=StoragePanelContract(
                    language=self.language,
                    renderer=self.layout_variant,
                ),
            )

        if None in {x, y, width, available_height}:
            raise ValueError(
                "rounded Storage panel requires a complete page rectangle"
            )
        assert x is not None
        assert y is not None
        assert width is not None
        assert available_height is not None

        title_sid = f"{self.sid}_title"
        self.writer._add_story_parts(
            title_sid,
            self.data.title,
            [heading_text(self.writer, self.data.title, level=1)],
        )
        self.writer.add_prose_story(
            self.sid,
            self.data.title,
            list(self.data.body_blocks),
            self.bundle_root,
            language=self.language,
            disable_hyphenation=True,
        )
        title_height = h1_bar_h_pt(self.writer)
        title_body_gap = param_pt(
            self.writer.params,
            "idml_compact_storage_panel_title_body_gap",
            12.0,
        )
        body_bottom_gap = param_pt(
            self.writer.params,
            "idml_compact_storage_panel_body_bottom_gap",
            10.0,
        )
        body_top = y + title_height + title_body_gap
        body_height = (
            available_height
            - title_height
            - title_body_gap
            - body_bottom_gap
        )
        if body_height <= 0:
            raise ValueError("rounded Storage panel has no body height")
        title_rect = (x, y, width, title_height)
        body_rect = (x, body_top, width, body_height)
        body_inset = param_pt(
            self.writer.params,
            "idml_compact_storage_panel_body_inset",
            8.0,
        )
        return StoragePanelRender(
            story_id=self.sid,
            contract=StoragePanelContract(
                language=self.language,
                renderer=self.layout_variant,
            ),
            frames=(
                frame_with_background(
                    self.writer,
                    self.sid,
                    "storage_title",
                    title_sid,
                    title_rect,
                    h1_frame_opts(title_rect),
                ),
                frame_with_background(
                    self.writer,
                    self.sid,
                    "storage_body",
                    self.sid,
                    body_rect,
                    {
                        "rounded": True,
                        "fill": "Color/HB Bg K05",
                        "inset": (
                            body_inset,
                            body_inset,
                            body_inset,
                            body_inset,
                        ),
                    },
                ),
            ),
            frame_rects=(
                ("title", title_rect),
                ("body", body_rect),
            ),
        )


__all__ = [
    "StoragePanel",
    "StoragePanelContract",
    "StoragePanelData",
    "StoragePanelRender",
    "StoragePanelVariant",
]
