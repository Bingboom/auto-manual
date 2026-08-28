"""Complete Safety-tail, Maintenance, and Symbols page component."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..page_objects import (
    frame_with_background,
    heading_bar_opts,
    heading_text,
    with_rounded_outer,
)
from ..source_copy import source_text
from .fixed_panel_contract import FrameRect, normalize_language
from .symbols_panel import SymbolsPanel, SymbolsPanelData


@dataclass(frozen=True)
class SafetySymbolsPanelData:
    tail_blocks: tuple[tuple[str, str], ...]
    maintenance_blocks: tuple[tuple[str, str], ...]
    symbols: SymbolsPanelData

    @classmethod
    def from_source(
        cls,
        *,
        tail_blocks: list[tuple[str, str]],
        maintenance_blocks: list[tuple[str, str]],
        title: str,
        signal_headers: tuple[str, str],
        icon_headers: tuple[str, str],
        signals: list[object],
        icons: list[dict],
    ) -> "SafetySymbolsPanelData":
        return cls(
            tail_blocks=tuple(tail_blocks),
            maintenance_blocks=tuple(maintenance_blocks),
            symbols=SymbolsPanelData(
                title=source_text(title, owner="Symbols page title"),
                signal_headers=(
                    source_text(
                        signal_headers[0],
                        owner="Symbols signal column 1 header",
                    ),
                    source_text(
                        signal_headers[1],
                        owner="Symbols signal column 2 header",
                    ),
                ),
                icon_headers=(
                    source_text(
                        icon_headers[0],
                        owner="Symbols icon column 1 header",
                    ),
                    source_text(
                        icon_headers[1],
                        owner="Symbols icon column 2 header",
                    ),
                ),
                signals=tuple(signals),
                icons=tuple(icons),
            ),
        )


@dataclass(frozen=True)
class SafetySymbolsPanelContract:
    language: str
    frame_rects: tuple[FrameRect, ...]


@dataclass(frozen=True)
class SafetySymbolsPanelRender:
    story_ids: tuple[str, ...]
    frames: tuple[str, ...]
    overflow: object
    contract: SafetySymbolsPanelContract


class SafetySymbolsPanel:
    """Own all fixed geometry on the Safety maintenance/Symbols page."""

    def __init__(
        self,
        writer,
        *,
        sid: str,
        data: SafetySymbolsPanelData,
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
    ) -> SafetySymbolsPanelRender:
        from ..symbols_page import SafetySymbolsPageStyle

        writer = self.writer
        style = SafetySymbolsPageStyle.from_writer(writer, self.language)
        tail_stories: list[tuple[str, float]] = []
        for block_index, (kind, text) in enumerate(self.data.tail_blocks):
            if kind != "component":
                continue
            spec = json.loads(text)
            if spec.get("kind") in {"safetywarning", "warnbox", "notice"}:
                label = source_text(
                    spec.get("label"),
                    owner="Safety tail warning label",
                    strict=writer.strict_component_assets,
                )
                spec = {
                    "kind": "tailwarnbox",
                    "label": label,
                    "texts": spec.get("texts", []),
                    "language": self.language,
                }
            tail_sid = (
                f"{self.sid}_tail_{spec.get('label', block_index).lower()}"
            )
            xml_part, tail_height = writer._render_component(
                tail_sid,
                block_index,
                spec,
                self.bundle_root,
                terminal=True,
                span_columns=False,
            )
            writer._add_story_parts(
                tail_sid,
                f"Safety tail {block_index}",
                [xml_part],
            )
            tail_stories.append((tail_sid, tail_height))

        maintenance_title = source_text(
            next((
                text
                for kind, text in self.data.maintenance_blocks
                if kind in ("h1", "h2")
            ), ""),
            owner="User maintenance title",
        )
        maintenance_text = "\n".join(
            text
            for kind, text in self.data.maintenance_blocks
            if kind == "body"
        )
        maintenance_title_sid = f"{self.sid}_maintenance_title"
        writer._add_story_parts(
            maintenance_title_sid,
            "Maintenance title",
            [heading_text(writer, maintenance_title, level=2)],
        )
        maintenance_body_sid = f"{self.sid}_maintenance_body"
        writer._add_story_parts(
            maintenance_body_sid,
            "Maintenance body",
            [writer._psr(
                "HB Maintenance Body",
                maintenance_text,
                terminal=True,
            )],
        )

        cursor = y + style.page_top
        frame_specs: list[
            tuple[str, str, tuple[float, float, float, float], dict]
        ] = []

        def place(
            frame_id: str,
            story_id: str,
            height: float,
            options: dict,
            gap: float = 6.0,
        ) -> None:
            nonlocal cursor
            frame_specs.append((
                frame_id,
                story_id,
                (x, cursor, width, height),
                options,
            ))
            cursor += height + gap

        tail_geometry = (
            (style.first_tail_height, style.first_tail_gap),
            (style.second_tail_height, style.second_tail_gap),
        )
        for index, ((tail_sid, _), (height, gap)) in enumerate(
            zip(tail_stories, tail_geometry, strict=False)
        ):
            place(
                f"tail_{index}",
                tail_sid,
                height,
                with_rounded_outer({
                    "inset": (0, 0, 0, 0),
                    "valign": "CenterAlign",
                }),
                gap=gap,
            )
        place(
            "maint_title",
            maintenance_title_sid,
            style.subbar_height,
            heading_bar_opts(2, (0.5, 5, 0.5, 6)),
            gap=style.maintenance_title_gap,
        )
        place(
            "maint_body",
            maintenance_body_sid,
            style.maintenance_body_height,
            {"inset": (0, 0, 0, 0)},
            gap=style.maintenance_body_gap,
        )
        symbols = SymbolsPanel(
            writer,
            sid=self.sid,
            data=self.data.symbols,
            bundle_root=self.bundle_root,
            language=self.language,
            density="standard",
        ).render(
            x=x,
            y=cursor,
            width=width,
            available_height=(
                y + available_height - style.page_bottom_allowance - cursor
            ),
        )

        frames: list[str] = []
        frame_rects: list[FrameRect] = []
        for frame_id, story_id, rect, options in frame_specs:
            if frame_id == "maint_title":
                options = {
                    **options,
                    "text_rect": (
                        rect[0] + 6.0,
                        rect[1],
                        rect[2] - 12.0,
                        rect[3],
                    ),
                }
            frames.append(frame_with_background(
                writer,
                self.sid,
                frame_id,
                story_id,
                rect,
                options,
            ))
            frame_rects.append((frame_id, rect))
        frames.extend(symbols.frames)
        story_ids = [tail_sid for tail_sid, _ in tail_stories]
        story_ids.extend((maintenance_title_sid, maintenance_body_sid))
        story_ids.extend(symbols.story_ids)
        return SafetySymbolsPanelRender(
            story_ids=tuple(story_ids),
            frames=tuple(frames),
            overflow=symbols.overflow,
            contract=SafetySymbolsPanelContract(
                language=self.language,
                frame_rects=tuple(frame_rects),
            ),
        )


__all__ = [
    "SafetySymbolsPanel",
    "SafetySymbolsPanelContract",
    "SafetySymbolsPanelData",
    "SafetySymbolsPanelRender",
]
