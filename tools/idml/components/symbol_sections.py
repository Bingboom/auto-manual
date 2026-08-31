"""Reusable partial Symbols components for split safety/icon compositions.

Some approved manuals place signal-word explanations below Safety and move the
icon meanings to their own following page.  These components reuse the same
table builders, signal badges, icon fitting, shells, and layout tokens as the
complete :class:`SymbolsPanel`; page assemblers only assign rectangles.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..page_objects import (
    frame_with_background,
    h1_bar_h_pt,
    h1_frame_opts,
    heading_text,
    with_rounded_outer,
)
from ..params import component_param_pt
from ..source_copy import source_text
from ..symbols_page import SafetySymbolsPageStyle
from .symbols_panel_contract import SymbolsPanelData
from .symbols_panel_metrics import normalized_language


@dataclass(frozen=True)
class SymbolSectionRender:
    """Rendered story/frame identifiers for one partial Symbols component."""

    story_ids: tuple[str, ...]
    frames: tuple[str, ...]
    height: float


def _shell_options(
    writer,
    *,
    left_plate_width: float,
    rect: tuple[float, float, float, float],
) -> dict:
    carrier = component_param_pt(
        writer.params,
        "idml_symbols_native_carrier_allowance",
        11.3386,
        strict=writer.strict_component_assets,
        owner="partial Symbols component native table carrier",
    )
    return with_rounded_outer({
        "inset": (0, 0, 0, 0),
        "rounded_outer_masks": True,
        "left_plate_width": left_plate_width,
        "text_rect": (rect[0], rect[1], rect[2], rect[3] + carrier),
    })


class SignalWordsPanel:
    """Editable signal-word table, optionally without a source header row."""

    def __init__(
        self,
        writer,
        *,
        sid: str,
        data: SymbolsPanelData,
        bundle_root: Path,
        language: str,
        include_header: bool,
    ) -> None:
        self.writer = writer
        self.sid = sid
        self.data = data
        self.bundle_root = bundle_root
        self.language = normalized_language(language)
        self.include_header = include_header

    def render(
        self,
        *,
        x: float,
        y: float,
        width: float,
        available_height: float,
    ) -> SymbolSectionRender:
        writer = self.writer
        style = SafetySymbolsPageStyle.from_writer(writer, self.language)
        headers = tuple(
            source_text(value, owner=f"SignalWordsPanel header {index + 1}")
            for index, value in enumerate(self.data.signal_headers)
        )
        row_heights = [style.signal_row_height] * len(self.data.signals)
        if self.include_header:
            row_heights.insert(0, style.signal_header_height)
        frame_height = sum(row_heights) + style.table_frame_allowance
        if frame_height > available_height + 0.001:
            raise ValueError(
                "SignalWordsPanel content exceeds its assigned rectangle: "
                f"needed={frame_height:.3f} available={available_height:.3f}"
            )
        signal_col = component_param_pt(
            writer.params,
            "comp_symbol_signal_col_width",
            width * 0.24,
            strict=writer.strict_component_assets,
            owner="SignalWordsPanel signal column",
        )
        story_id = f"{self.sid}_signals"
        writer._table_story(
            story_id,
            "Signal words",
            writer._symbols_signal_table(
                f"{self.sid}_sig_tbl",
                list(self.data.signals),
                width,
                self.bundle_root,
                self.language,
                headers=headers,
                include_header=self.include_header,
                row_heights=row_heights,
                left_col_width=signal_col,
                fit_body_to_row=True,
                disable_hyphenation=True,
                auto_grow_rows=False,
            ),
        )
        rect = (x, y, width, frame_height)
        frame = frame_with_background(
            writer,
            self.sid,
            "signals",
            story_id,
            rect,
            _shell_options(
                writer,
                left_plate_width=signal_col,
                rect=rect,
            ),
        )
        return SymbolSectionRender(
            story_ids=(story_id,),
            frames=(frame,),
            height=frame_height,
        )


class SymbolIconsPanel:
    """Editable single-column symbol meanings for a dedicated icon page."""

    def __init__(
        self,
        writer,
        *,
        sid: str,
        data: SymbolsPanelData,
        language: str,
        include_header: bool,
    ) -> None:
        self.writer = writer
        self.sid = sid
        self.data = data
        self.language = normalized_language(language)
        self.include_header = include_header

    def render(
        self,
        *,
        x: float,
        y: float,
        width: float,
        available_height: float,
    ) -> SymbolSectionRender:
        writer = self.writer
        style = SafetySymbolsPageStyle.from_writer(writer, self.language)
        title = source_text(self.data.title, owner="SymbolIconsPanel title")
        headers = tuple(
            source_text(value, owner=f"SymbolIconsPanel header {index + 1}")
            for index, value in enumerate(self.data.icon_headers)
        )
        title_height = h1_bar_h_pt(writer)
        title_gap = style.symbols_title_gap
        rows = len(self.data.icons) + (1 if self.include_header else 0)
        if rows <= 0:
            raise ValueError("SymbolIconsPanel requires at least one icon row")
        table_height = available_height - title_height - title_gap
        if table_height <= 0:
            raise ValueError("SymbolIconsPanel rectangle is too short")
        row_heights = [table_height / rows] * rows
        icon_col = component_param_pt(
            writer.params,
            "idml_symbols_icons_single_col_width",
            component_param_pt(
                writer.params,
                "idml_symbols_icon_col_width",
                39.685,
                strict=False,
                owner="SymbolIconsPanel icon-column fallback",
            ),
            strict=writer.strict_component_assets,
            owner="SymbolIconsPanel icon column",
        )
        title_sid = f"{self.sid}_title"
        table_sid = f"{self.sid}_icons"
        writer._add_story_parts(
            title_sid,
            title,
            [heading_text(writer, title, level=1)],
        )
        writer._table_story(
            table_sid,
            "Symbol icons",
            writer._symbols_icon_table(
                f"{self.sid}_icons_tbl",
                list(self.data.icons),
                width,
                self.language,
                headers=headers,
                include_header=self.include_header,
                row_heights=row_heights,
                icon_col_width=icon_col,
                fit_body_to_row=True,
                disable_hyphenation=True,
                auto_grow_rows=False,
            ),
        )
        title_rect = (x, y, width, title_height)
        table_rect = (x, y + title_height + title_gap, width, table_height)
        return SymbolSectionRender(
            story_ids=(title_sid, table_sid),
            frames=(
                frame_with_background(
                    writer,
                    self.sid,
                    "title",
                    title_sid,
                    title_rect,
                    h1_frame_opts(title_rect),
                ),
                frame_with_background(
                    writer,
                    self.sid,
                    "icons",
                    table_sid,
                    table_rect,
                    _shell_options(
                        writer,
                        left_plate_width=icon_col,
                        rect=table_rect,
                    ),
                ),
            ),
            height=available_height,
        )


__all__ = [
    "SignalWordsPanel",
    "SymbolIconsPanel",
    "SymbolSectionRender",
]
