"""Complete editable Symbols panel shared by standard and compact pages.

Page assemblers own only the rectangle assigned to this component.  This
module owns the title, table stories, row fitting, fills, rounded shells,
carrier allowance, and the minimum gap between the signal and icon tables.
"""
from __future__ import annotations

from pathlib import Path

from ..language_contract import governed_languages
from ..layout_est import est_table_height, template_symbol_split
from ..page_objects import (
    frame_with_background,
    heading_bar_opts,
    heading_text,
    with_rounded_outer,
)
from ..params import component_param_pt
from ..source_copy import source_text
from .symbols_panel_contract import (
    SymbolsPanelContract,
    SymbolsPanelData,
    SymbolsPanelRender,
)
from .symbols_panel_metrics import (
    SymbolsPanelDensity,
    fit_visible_rows,
    icon_heights,
    normalized_language,
    panel_metrics,
)


class SymbolsPanel:
    """Measure and render one complete editable Symbols panel."""

    def __init__(
        self,
        writer,
        *,
        sid: str,
        data: SymbolsPanelData,
        bundle_root: Path,
        language: str,
        density: SymbolsPanelDensity,
    ) -> None:
        if density not in {"standard", "compact"}:
            raise ValueError(f"unsupported SymbolsPanel density: {density}")
        self.writer = writer
        self.sid = sid
        self.data = data
        self.bundle_root = bundle_root
        self.language = normalized_language(language)
        self.density = density

    def _story_ids(self) -> tuple[str, str, str, str]:
        title = (
            f"{self.sid}_symbols_title"
            if self.density == "standard"
            else f"{self.sid}_title"
        )
        return (
            title,
            f"{self.sid}_signals",
            f"{self.sid}_icons_left",
            f"{self.sid}_icons_right",
        )

    def render(
        self,
        *,
        x: float,
        y: float,
        width: float,
        available_height: float,
    ) -> SymbolsPanelRender:
        from ..symbols_page import SymbolOverflow

        writer = self.writer
        language = self.language
        metrics = panel_metrics(
            writer, language, self.density, len(self.data.signals),
        )
        title = source_text(self.data.title, owner="SymbolsPanel title")
        signal_headers = tuple(
            source_text(value, owner=f"SymbolsPanel signal header {index + 1}")
            for index, value in enumerate(self.data.signal_headers)
        )
        icon_headers = tuple(
            source_text(value, owner=f"SymbolsPanel icon header {index + 1}")
            for index, value in enumerate(self.data.icon_headers)
        )

        icon_gap = component_param_pt(
            writer.params,
            "idml_symbols_column_gap",
            component_param_pt(
                writer.params,
                "comp_symbol_column_gap",
                6.0,
                strict=False,
                owner="SymbolsPanel column-gap fallback",
            ),
            strict=writer.strict_component_assets,
            owner="SymbolsPanel",
        )
        icon_table_trim = component_param_pt(
            writer.params,
            "idml_symbols_icon_table_width_trim",
            0.0,
            strict=writer.strict_component_assets,
            owner="SymbolsPanel",
        )
        icon_table_width = (width - icon_gap) / 2.0 - icon_table_trim
        left_icon_col = component_param_pt(
            writer.params,
            (
                "idml_compact_symbols_icon_left_col_width"
                if self.density == "compact"
                else "idml_symbols_icon_left_col_width"
            ),
            component_param_pt(
                writer.params,
                "idml_symbols_icon_col_width",
                39.685,
                strict=False,
                owner="SymbolsPanel left-column fallback",
            ),
            strict=writer.strict_component_assets,
            owner="SymbolsPanel left icon column",
        )
        right_icon_col = component_param_pt(
            writer.params,
            (
                "idml_compact_symbols_icon_right_col_width"
                if self.density == "compact"
                else "idml_symbols_icon_right_col_width"
            ),
            left_icon_col,
            strict=writer.strict_component_assets,
            owner="SymbolsPanel right icon column",
        )

        left_icons, right_icons, overflow_left, overflow_right = (
            template_symbol_split(list(self.data.icons), dense=False)
        )
        signal_frame_height = (
            sum(metrics.signal_row_heights)
            + metrics.signal_frame_allowance
        )
        icon_content_budget = (
            available_height
            - metrics.title_height
            - metrics.title_gap
            - signal_frame_height
            - metrics.signal_gap
            - metrics.icon_frame_allowance
        )
        if icon_content_budget < metrics.icon_header_height:
            raise ValueError(
                "SymbolsPanel rectangle is too short for its table header"
            )

        if self.density == "standard":
            right_last = (
                metrics.icon_long_last_row_height
                if language == "en"
                else metrics.icon_last_row_height
            )
            left_count = fit_visible_rows(
                left_icons,
                budget=icon_content_budget,
                header=metrics.icon_header_height,
                ordinary=metrics.icon_left_row_height,
                last=metrics.icon_last_row_height,
            )
            right_count = fit_visible_rows(
                right_icons,
                budget=icon_content_budget,
                header=metrics.icon_header_height,
                ordinary=metrics.icon_right_row_height,
                last=right_last,
            )
            overflow_left = left_icons[left_count:] + overflow_left
            overflow_right = right_icons[right_count:] + overflow_right
            left_icons = left_icons[:left_count]
            right_icons = right_icons[:right_count]

        left_heights = icon_heights(
            left_icons,
            header=metrics.icon_header_height,
            ordinary=metrics.icon_left_row_height,
            last=metrics.icon_last_row_height,
        )
        right_last = (
            metrics.icon_long_last_row_height
            if self.density == "compact" or language == "en"
            else metrics.icon_last_row_height
        )
        right_heights = icon_heights(
            right_icons,
            header=metrics.icon_header_height,
            ordinary=metrics.icon_right_row_height,
            last=right_last,
        )
        shell_height = max(sum(left_heights), sum(right_heights))
        if left_heights and sum(left_heights) < shell_height:
            left_heights[-1] += shell_height - sum(left_heights)
        if right_heights and sum(right_heights) < shell_height:
            right_heights[-1] += shell_height - sum(right_heights)
        icon_frame_height = shell_height + metrics.icon_frame_allowance
        if self.density == "standard" and language not in governed_languages():
            from ..symbols_page import SafetySymbolsPageStyle

            style = SafetySymbolsPageStyle.from_writer(writer, language)
            icon_space = (
                available_height
                - metrics.title_height
                - metrics.title_gap
                - signal_frame_height
                - metrics.signal_gap
            )
            estimated = max(
                est_table_height(
                    [row.get("text", "") for row in left_icons],
                    icon_table_width * style.fallback_text_width_ratio,
                    style.fallback_row_height,
                ),
                est_table_height(
                    [row.get("text", "") for row in right_icons],
                    icon_table_width * style.fallback_text_width_ratio,
                    style.fallback_row_height,
                ),
            )
            icon_frame_height = style.fallback_import_allowance + max(
                style.fallback_min_height,
                min(estimated, icon_space),
            )

        title_sid, signal_sid, left_sid, right_sid = self._story_ids()
        writer._add_story_parts(
            title_sid,
            "Symbols title" if self.density == "standard" else title,
            [heading_text(writer, title, level=1)],
        )
        writer._table_story(
            signal_sid,
            "Signal words",
            writer._symbols_signal_table(
                f"{self.sid}_sig_tbl",
                list(self.data.signals),
                width,
                self.bundle_root,
                language,
                headers=signal_headers,
                row_heights=list(metrics.signal_row_heights),
                fit_body_to_row=metrics.fit_body_to_row,
                cell_vertical_inset=metrics.signal_cell_inset,
                fill_all_cells=metrics.fill_all_cells,
                disable_hyphenation=metrics.disable_hyphenation,
                auto_grow_rows=metrics.auto_grow_rows,
            ),
        )

        icon_width = None
        icon_height = None
        if self.density == "compact":
            icon_width = component_param_pt(
                writer.params,
                "idml_compact_symbols_icon_width",
                component_param_pt(
                    writer.params,
                    "idml_symbols_icon_width",
                    26.0,
                    strict=False,
                    owner="SymbolsPanel compact icon-width fallback",
                ),
                strict=writer.strict_component_assets,
                owner="SymbolsPanel compact icon width",
            )
            icon_height = component_param_pt(
                writer.params,
                "idml_compact_symbols_icon_height",
                component_param_pt(
                    writer.params,
                    "idml_symbols_icon_height",
                    26.0,
                    strict=False,
                    owner="SymbolsPanel compact icon-height fallback",
                ),
                strict=writer.strict_component_assets,
                owner="SymbolsPanel compact icon height",
            )

        writer._table_story(
            left_sid,
            "Symbol icons left",
            writer._symbols_icon_table(
                f"{self.sid}_icons_l_tbl",
                left_icons,
                icon_table_width,
                language,
                headers=icon_headers,
                row_heights=left_heights,
                icon_col_width=left_icon_col,
                icon_width=icon_width,
                icon_height=icon_height,
                fit_body_to_row=metrics.fit_body_to_row,
                fill_all_cells=metrics.fill_all_cells,
                disable_hyphenation=metrics.disable_hyphenation,
                auto_grow_rows=metrics.auto_grow_rows,
            ),
        )
        writer._table_story(
            right_sid,
            "Symbol icons right",
            writer._symbols_icon_table(
                f"{self.sid}_icons_r_tbl",
                right_icons,
                icon_table_width,
                language,
                headers=icon_headers,
                row_heights=right_heights,
                icon_col_width=right_icon_col,
                icon_width=icon_width,
                icon_height=icon_height,
                fit_body_to_row=metrics.fit_body_to_row,
                fill_all_cells=metrics.fill_all_cells,
                disable_hyphenation=metrics.disable_hyphenation,
                auto_grow_rows=metrics.auto_grow_rows,
            ),
        )

        title_rect = (x, y, width, metrics.title_height)
        title_background_rect = title_rect
        title_opts = {
            **heading_bar_opts(1, (1.5, 5, 1, 6)),
            "text_rect": (x + 6.0, y, width - 12.0, metrics.title_height),
        }
        if metrics.title_optical_offset:
            title_background_rect = (
                x,
                y + metrics.title_optical_offset,
                width,
                metrics.title_height,
            )
        signal_top = y + metrics.title_height + metrics.title_gap
        signal_rect = (x, signal_top, width, signal_frame_height)
        icons_top = signal_top + signal_frame_height + metrics.signal_gap
        left_rect = (x, icons_top, icon_table_width, icon_frame_height)
        right_rect = (
            x + icon_table_width + icon_gap,
            icons_top,
            icon_table_width,
            icon_frame_height,
        )
        total_height = icons_top + icon_frame_height - y
        if total_height > available_height + 0.001:
            raise ValueError(
                "SymbolsPanel content exceeds its assigned rectangle: "
                f"needed={total_height:.3f} available={available_height:.3f}"
            )

        shell_opts = with_rounded_outer({
            "inset": (0, 0, 0, 0),
            "rounded_outer_masks": True,
        })
        frames = (
            frame_with_background(
                writer,
                self.sid,
                "symbols_title",
                title_sid,
                title_background_rect,
                title_opts,
            ),
            frame_with_background(
                writer, self.sid, "signals", signal_sid, signal_rect,
                shell_opts,
            ),
            frame_with_background(
                writer, self.sid, "icons_left", left_sid, left_rect,
                shell_opts,
            ),
            frame_with_background(
                writer, self.sid, "icons_right", right_sid, right_rect,
                shell_opts,
            ),
        )
        contract = SymbolsPanelContract(
            density=self.density,
            language=language,
            title_height=metrics.title_height,
            title_gap=metrics.title_gap,
            signal_row_heights=metrics.signal_row_heights,
            signal_frame_height=signal_frame_height,
            signal_gap=metrics.signal_gap,
            left_icon_row_heights=tuple(left_heights),
            right_icon_row_heights=tuple(right_heights),
            icon_frame_height=icon_frame_height,
            column_gap=icon_gap,
            table_width=icon_table_width,
            fill_all_cells=metrics.fill_all_cells,
            auto_grow_rows=metrics.auto_grow_rows,
            disable_hyphenation=metrics.disable_hyphenation,
            frame_rects=(
                ("title", title_background_rect),
                ("signals", signal_rect),
                ("icons_left", left_rect),
                ("icons_right", right_rect),
            ),
        )
        return SymbolsPanelRender(
            story_ids=(title_sid, signal_sid, left_sid, right_sid),
            frames=frames,
            height=total_height,
            overflow=SymbolOverflow(
                tuple(overflow_left), tuple(overflow_right), icon_headers,
            ),
            contract=contract,
        )

    @staticmethod
    def render_continuation(
        writer,
        *,
        sid: str,
        overflow: object,
        language: str,
        density: SymbolsPanelDensity,
        x: float,
        y: float,
        width: float,
        available_height: float,
    ) -> tuple[list[str], list[str]]:
        """Render overflow rows without leaking table geometry to a page."""

        if density not in {"standard", "compact"}:
            raise ValueError(f"unsupported SymbolsPanel density: {density}")
        if not getattr(overflow, "has_rows")():
            return [], []
        language = normalized_language(language)
        column_gap = component_param_pt(
            writer.params,
            "idml_symbols_continuation_column_gap",
            7.0,
            strict=False,
            owner="SymbolsPanel continuation",
        )
        table_width = (width - column_gap) / 2.0
        story_ids: list[str] = []
        frames: list[str] = []
        for side, rows, table_x in (
            ("left", list(getattr(overflow, "left")), x),
            (
                "right",
                list(getattr(overflow, "right")),
                x + table_width + column_gap,
            ),
        ):
            if not rows:
                continue
            story_id = f"{sid}_symbols_{side}"
            table = writer._symbols_icon_table(
                f"{sid}_symbols_{side}_tbl",
                rows,
                table_width,
                language,
                headers=tuple(getattr(overflow, "headers")),
                include_header=False,
                row_heights=[available_height / len(rows)] * len(rows),
                fit_body_to_row=True,
            )
            writer._table_story(
                story_id,
                f"Symbol icons continuation {side}",
                table,
            )
            story_ids.append(story_id)
            frames.append(frame_with_background(
                writer,
                sid,
                f"symbols_{side}",
                story_id,
                (table_x, y, table_width, available_height),
                with_rounded_outer({
                    "inset": (0, 0, 0, 0),
                    "rounded_outer_masks": True,
                }),
            ))
        return story_ids, frames


__all__ = [
    "SymbolsPanel",
    "SymbolsPanelContract",
    "SymbolsPanelData",
    "SymbolsPanelDensity",
    "SymbolsPanelRender",
]
