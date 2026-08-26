"""Internal density and row-fitting rules for :mod:`symbols_panel`.

Keeping measurement policy separate leaves ``SymbolsPanel`` as the public
component boundary while preventing its renderer from becoming another
monolithic page module.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..page_objects import h1_bar_h_pt
from ..params import param_pt


SymbolsPanelDensity = Literal["standard", "compact"]


@dataclass(frozen=True)
class PanelMetrics:
    title_height: float
    title_gap: float
    signal_row_heights: tuple[float, ...]
    signal_frame_allowance: float
    signal_gap: float
    icon_header_height: float
    icon_left_row_height: float
    icon_right_row_height: float
    icon_last_row_height: float
    icon_long_last_row_height: float
    icon_frame_allowance: float
    signal_cell_inset: float
    auto_grow_rows: bool
    disable_hyphenation: bool
    fit_body_to_row: bool
    title_optical_offset: float


def normalized_language(language: str) -> str:
    return language.strip().casefold().replace("_", "-").split("-", 1)[0]


def _compact_metric(writer, language: str, key: str, fallback: float) -> float:
    return param_pt(
        writer.params,
        f"lang_{language}_{key}",
        param_pt(writer.params, key, fallback),
    )


def panel_metrics(
    writer,
    language: str,
    density: SymbolsPanelDensity,
    signal_count: int,
) -> PanelMetrics:
    # Imported lazily so the historical symbols-page facade can import the
    # public component without a module cycle.
    from ..symbols_page import SafetySymbolsPageStyle

    style = SafetySymbolsPageStyle.from_writer(writer, language)
    title_height = h1_bar_h_pt(writer)
    if density == "standard":
        return PanelMetrics(
            title_height=title_height,
            title_gap=style.symbols_title_gap,
            signal_row_heights=(style.signal_header_height,) + (
                style.signal_row_height,
            ) * signal_count,
            signal_frame_allowance=0.0,
            signal_gap=style.signal_gap_after,
            icon_header_height=style.icon_header_height,
            icon_left_row_height=style.icon_row_height,
            icon_right_row_height=style.icon_row_height,
            icon_last_row_height=style.icon_last_row_height,
            icon_long_last_row_height=style.icon_long_last_row_height,
            icon_frame_allowance=style.table_frame_allowance,
            signal_cell_inset=3.0,
            auto_grow_rows=True,
            disable_hyphenation=False,
            fit_body_to_row=False,
            title_optical_offset=style.h1_optical_offset,
        )

    signal_header = _compact_metric(
        writer,
        language,
        "idml_compact_symbols_signal_header_height",
        style.signal_header_height,
    )
    signal_row = _compact_metric(
        writer,
        language,
        "idml_compact_symbols_signal_row_height",
        style.signal_row_height,
    )
    signal_last = _compact_metric(
        writer,
        language,
        "idml_compact_symbols_signal_last_row_height",
        signal_row,
    )
    signal_heights = [signal_header] + [signal_row] * signal_count
    if signal_count:
        signal_heights[-1] = signal_last
    return PanelMetrics(
        title_height=title_height,
        title_gap=param_pt(
            writer.params,
            "idml_compact_symbols_title_gap",
            style.symbols_title_gap,
        ),
        signal_row_heights=tuple(signal_heights),
        signal_frame_allowance=param_pt(
            writer.params,
            "idml_compact_symbols_signal_frame_allowance",
            0.0,
        ),
        signal_gap=_compact_metric(
            writer,
            language,
            "idml_compact_symbols_signal_gap_after",
            style.signal_gap_after,
        ),
        icon_header_height=_compact_metric(
            writer,
            language,
            "idml_compact_symbols_icon_header_height",
            style.icon_header_height,
        ),
        icon_left_row_height=_compact_metric(
            writer,
            language,
            "idml_compact_symbols_icon_row_height",
            style.icon_row_height,
        ),
        icon_right_row_height=_compact_metric(
            writer,
            language,
            "idml_compact_symbols_icon_right_row_height",
            _compact_metric(
                writer,
                language,
                "idml_compact_symbols_icon_row_height",
                style.icon_row_height,
            ),
        ),
        icon_last_row_height=_compact_metric(
            writer,
            language,
            "idml_compact_symbols_icon_last_row_height",
            style.icon_last_row_height,
        ),
        icon_long_last_row_height=_compact_metric(
            writer,
            language,
            "idml_compact_symbols_icon_long_last_row_height",
            style.icon_long_last_row_height,
        ),
        icon_frame_allowance=param_pt(
            writer.params,
            "idml_compact_symbols_table_frame_allowance",
            style.table_frame_allowance,
        ),
        signal_cell_inset=_compact_metric(
            writer,
            language,
            "idml_compact_symbols_signal_cell_vertical_inset",
            3.0,
        ),
        auto_grow_rows=False,
        disable_hyphenation=True,
        fit_body_to_row=True,
        title_optical_offset=0.0,
    )


def icon_heights(
    rows: list[dict],
    *,
    header: float,
    ordinary: float,
    last: float,
) -> list[float]:
    return (
        [header]
        + [ordinary] * max(0, len(rows) - 1)
        + ([last] if rows else [])
    )


def fit_visible_rows(
    rows: list[dict],
    *,
    budget: float,
    header: float,
    ordinary: float,
    last: float,
) -> int:
    for visible in range(len(rows), -1, -1):
        heights = icon_heights(
            rows[:visible],
            header=header,
            ordinary=ordinary,
            last=last,
        )
        if sum(heights) <= budget + 0.001:
            return visible
    return 0


__all__ = [
    "PanelMetrics",
    "SymbolsPanelDensity",
    "fit_visible_rows",
    "icon_heights",
    "normalized_language",
    "panel_metrics",
]
