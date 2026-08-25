"""Public data and geometry contract for the editable Symbols panel."""
from __future__ import annotations

from dataclasses import dataclass

from .symbols_panel_metrics import SymbolsPanelDensity


@dataclass(frozen=True)
class SymbolsPanelData:
    """Localized semantic input consumed by ``SymbolsPanel``."""

    title: str
    signal_headers: tuple[str, str]
    icon_headers: tuple[str, str]
    signals: tuple[object, ...]
    icons: tuple[dict, ...]

    @classmethod
    def from_source(cls, source: object) -> "SymbolsPanelData":
        return cls(
            title=str(getattr(source, "title")),
            signal_headers=tuple(getattr(source, "signal_headers")),
            icon_headers=tuple(getattr(source, "icon_headers")),
            signals=tuple(getattr(source, "signals")),
            icons=tuple(getattr(source, "icons")),
        )


@dataclass(frozen=True)
class SymbolsPanelContract:
    """Stable, reviewable geometry behind the editable panel."""

    density: SymbolsPanelDensity
    language: str
    title_height: float
    title_gap: float
    signal_row_heights: tuple[float, ...]
    signal_frame_height: float
    signal_gap: float
    left_icon_row_heights: tuple[float, ...]
    right_icon_row_heights: tuple[float, ...]
    icon_frame_height: float
    column_gap: float
    table_width: float
    fill_all_cells: bool
    shell_fill: str
    auto_grow_rows: bool
    disable_hyphenation: bool
    frame_rects: tuple[tuple[str, tuple[float, float, float, float]], ...]


@dataclass(frozen=True)
class SymbolsPanelRender:
    """Rendered stories/frames plus overflow owned by one panel instance."""

    story_ids: tuple[str, str, str, str]
    frames: tuple[str, str, str, str]
    height: float
    overflow: object
    contract: SymbolsPanelContract


__all__ = [
    "SymbolsPanelContract",
    "SymbolsPanelData",
    "SymbolsPanelRender",
]
