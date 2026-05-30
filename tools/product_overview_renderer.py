#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
import re

from tools.csv_pages.renderers_common import latex_arg_escape, rst_escape, spec_latex_cell, split_spec_lines
from tools.language_aliases import normalize_language


PRODUCT_OVERVIEW_TOKEN = "{{ product_overview }}"
PRODUCT_OVERVIEW_FIELD_PLACEHOLDERS = (
    "MAIN_POWER_BUTTON_LABEL",
    "FRONT_DC12_PORT_LABEL",
    "FRONT_DC12_PORT_SPEC",
    "DC_USB_POWER_BUTTON_LABEL",
    "FRONT_USB_C_LOW_LABEL",
    "FRONT_USB_C_LOW_SPEC",
    "FRONT_USB_C_HIGH_LABEL",
    "FRONT_USB_C_HIGH_SPEC",
    "AC_POWER_BUTTON_LABEL",
    "FRONT_USB_A_LABEL",
    "FRONT_USB_A_SPEC",
    "FRONT_AC_OUTPUT_LABEL",
    "FRONT_AC_OUTPUT_SPEC",
    "FRONT_TOTAL_OUTPUT_LABEL",
    "FRONT_TOTAL_OUTPUT_SPEC",
    "SIDE_AC_INPUT_LABEL",
    "SIDE_AC_INPUT_SPEC",
    "SIDE_DC_INPUT_LABEL",
    "SIDE_DC_INPUT_PV_SPEC",
    "SIDE_DC_INPUT_CAR_SPEC",
)

_FIELD_MARKER_RE = re.compile(r"(?m)^\.\. product-overview-fields:.*(?:\n[ \t]+.*)*\n?")
_OVERVIEW_IMAGE_ROOT = "templates/word_template/common_assets/overview"


@dataclass(frozen=True)
class OverviewCell:
    label: str = ""
    specs: tuple[str, ...] = ()


@dataclass(frozen=True)
class OverviewRow:
    cells: tuple[OverviewCell, ...]


@dataclass(frozen=True)
class OverviewPanel:
    title: str
    image: str
    alt: str
    rows: tuple[OverviewRow, ...]


@dataclass(frozen=True)
class OverviewLayout:
    title: str
    panels: tuple[OverviewPanel, ...]


def _cell(label: str = "", *specs: str) -> OverviewCell:
    return OverviewCell(label=label, specs=tuple(specs))


def _pair(left: OverviewCell, right: OverviewCell) -> OverviewRow:
    return OverviewRow(cells=(left, right))


def _full(cell: OverviewCell) -> OverviewRow:
    return OverviewRow(cells=(cell,))


_LAYOUTS: dict[str, OverviewLayout] = {
    "en": OverviewLayout(
        title="PRODUCT OVERVIEW",
        panels=(
            OverviewPanel(
                title="FRONT VIEW",
                image="front_product.jpg",
                alt="Front view diagram placeholder.",
                rows=(
                    _pair(_cell("MAIN_POWER_BUTTON_LABEL"), _cell("Handle")),
                    _pair(_cell("FRONT_DC12_PORT_LABEL", "FRONT_DC12_PORT_SPEC"), _cell("LCD")),
                    _pair(_cell("DC_USB_POWER_BUTTON_LABEL"), _cell("LED Light Button")),
                    _pair(_cell("FRONT_USB_C_LOW_LABEL", "FRONT_USB_C_LOW_SPEC"), _cell("LED Light")),
                    _pair(_cell("FRONT_USB_C_HIGH_LABEL", "FRONT_USB_C_HIGH_SPEC"), _cell("AC_POWER_BUTTON_LABEL")),
                    _pair(
                        _cell("FRONT_USB_A_LABEL", "FRONT_USB_A_SPEC"),
                        _cell("FRONT_AC_OUTPUT_LABEL", "FRONT_AC_OUTPUT_SPEC"),
                    ),
                    _full(_cell("FRONT_TOTAL_OUTPUT_LABEL", "FRONT_TOTAL_OUTPUT_SPEC")),
                ),
            ),
            OverviewPanel(
                title="RIGHT SIDE VIEW",
                image="right_side_ports.png",
                alt="Right side view diagram placeholder.",
                rows=(
                    _pair(_cell("Handle"), _cell("SIDE_AC_INPUT_LABEL", "SIDE_AC_INPUT_SPEC")),
                    _pair(_cell(), _cell("SIDE_DC_INPUT_LABEL", "SIDE_DC_INPUT_PV_SPEC", "SIDE_DC_INPUT_CAR_SPEC")),
                ),
            ),
        ),
    ),
    "es": OverviewLayout(
        title="DESCRIPCIÓN GENERAL DEL PRODUCTO",
        panels=(
            OverviewPanel(
                title="VISTA FRONTAL",
                image="front_product.jpg",
                alt="Diagrama de vista frontal.",
                rows=(
                    _pair(_cell("MAIN_POWER_BUTTON_LABEL"), _cell("Asa")),
                    _pair(_cell("FRONT_DC12_PORT_LABEL", "FRONT_DC12_PORT_SPEC"), _cell("LCD")),
                    _pair(_cell("DC_USB_POWER_BUTTON_LABEL"), _cell("Botón de luz LED")),
                    _pair(_cell("FRONT_USB_C_LOW_LABEL", "FRONT_USB_C_LOW_SPEC"), _cell("Luz LED")),
                    _pair(_cell("FRONT_USB_C_HIGH_LABEL", "FRONT_USB_C_HIGH_SPEC"), _cell("AC_POWER_BUTTON_LABEL")),
                    _pair(
                        _cell("FRONT_USB_A_LABEL", "FRONT_USB_A_SPEC"),
                        _cell("FRONT_AC_OUTPUT_LABEL", "FRONT_AC_OUTPUT_SPEC"),
                    ),
                    _full(_cell("FRONT_TOTAL_OUTPUT_LABEL", "FRONT_TOTAL_OUTPUT_SPEC")),
                ),
            ),
            OverviewPanel(
                title="VISTA LATERAL DERECHA",
                image="right_side_ports.png",
                alt="Diagrama de vista lateral derecha.",
                rows=(
                    _full(_cell("SIDE_AC_INPUT_LABEL", "SIDE_AC_INPUT_SPEC")),
                    _full(_cell("SIDE_DC_INPUT_LABEL", "SIDE_DC_INPUT_CAR_SPEC", "SIDE_DC_INPUT_PV_SPEC")),
                ),
            ),
        ),
    ),
    "fr": OverviewLayout(
        title="APERÇU DU PRODUIT",
        panels=(
            OverviewPanel(
                title="VUE DE FACE",
                image="front_product.jpg",
                alt="Schéma de la vue de face.",
                rows=(
                    _pair(_cell("MAIN_POWER_BUTTON_LABEL"), _cell("LCD")),
                    _pair(_cell("FRONT_DC12_PORT_LABEL", "FRONT_DC12_PORT_SPEC"), _cell("Bouton lumière LED")),
                    _pair(_cell("DC_USB_POWER_BUTTON_LABEL"), _cell("Lumière LED")),
                    _pair(_cell("FRONT_USB_C_LOW_LABEL", "FRONT_USB_C_LOW_SPEC"), _cell("AC_POWER_BUTTON_LABEL")),
                    _pair(_cell("FRONT_USB_C_HIGH_LABEL", "FRONT_USB_C_HIGH_SPEC"), _cell()),
                    _pair(
                        _cell("FRONT_USB_A_LABEL", "FRONT_USB_A_SPEC"),
                        _cell("FRONT_AC_OUTPUT_LABEL", "FRONT_AC_OUTPUT_SPEC"),
                    ),
                    _full(_cell("FRONT_TOTAL_OUTPUT_LABEL", "FRONT_TOTAL_OUTPUT_SPEC")),
                ),
            ),
            OverviewPanel(
                title="VUE LATÉRALE DROITE",
                image="right_side_ports.png",
                alt="Schéma de la vue latérale droite.",
                rows=(
                    _pair(_cell("Poignée"), _cell()),
                    _pair(
                        _cell("SIDE_AC_INPUT_LABEL", "SIDE_AC_INPUT_SPEC"),
                        _cell("SIDE_DC_INPUT_LABEL", "SIDE_DC_INPUT_PV_SPEC", "SIDE_DC_INPUT_CAR_SPEC"),
                    ),
                ),
            ),
        ),
    ),
    "pt-BR": OverviewLayout(
        title="VISÃO GERAL DO PRODUTO",
        panels=(
            OverviewPanel(
                title="VISTA FRONTAL",
                image="front_product.jpg",
                alt="Diagrama da vista frontal.",
                rows=(
                    _pair(_cell("MAIN_POWER_BUTTON_LABEL"), _cell("LCD")),
                    _pair(_cell("FRONT_DC12_PORT_LABEL", "FRONT_DC12_PORT_SPEC"), _cell("Botão da luz LED")),
                    _pair(_cell("DC_USB_POWER_BUTTON_LABEL"), _cell("Luz LED")),
                    _pair(_cell("FRONT_USB_C_LOW_LABEL", "FRONT_USB_C_LOW_SPEC"), _cell("AC_POWER_BUTTON_LABEL")),
                    _pair(_cell("FRONT_USB_C_HIGH_LABEL", "FRONT_USB_C_HIGH_SPEC"), _cell()),
                    _pair(
                        _cell("FRONT_USB_A_LABEL", "FRONT_USB_A_SPEC"),
                        _cell("FRONT_AC_OUTPUT_LABEL", "FRONT_AC_OUTPUT_SPEC"),
                    ),
                    _full(_cell("FRONT_TOTAL_OUTPUT_LABEL", "FRONT_TOTAL_OUTPUT_SPEC")),
                ),
            ),
            OverviewPanel(
                title="VISTA LATERAL DIREITA",
                image="right_side_ports.png",
                alt="Diagrama da vista lateral direita.",
                rows=(
                    _pair(_cell("Alça"), _cell()),
                    _pair(
                        _cell("SIDE_AC_INPUT_LABEL", "SIDE_AC_INPUT_SPEC"),
                        _cell("SIDE_DC_INPUT_LABEL", "SIDE_DC_INPUT_PV_SPEC", "SIDE_DC_INPUT_CAR_SPEC"),
                    ),
                ),
            ),
        ),
    ),
    "ja": OverviewLayout(
        title="各部の名称",
        panels=(
            OverviewPanel(
                title="正面",
                image="front_product.jpg",
                alt="Front product image.",
                rows=(
                    _pair(_cell("MAIN_POWER_BUTTON_LABEL"), _cell("ハンドル")),
                    _pair(_cell("FRONT_DC12_PORT_LABEL", "FRONT_DC12_PORT_SPEC"), _cell("LCDディスプレイ")),
                    _pair(_cell("DC_USB_POWER_BUTTON_LABEL"), _cell("LEDライトボタン")),
                    _pair(_cell("FRONT_USB_C_LOW_LABEL", "FRONT_USB_C_LOW_SPEC"), _cell("LEDライト")),
                    _pair(_cell("FRONT_USB_C_HIGH_LABEL", "FRONT_USB_C_HIGH_SPEC"), _cell("AC_POWER_BUTTON_LABEL")),
                    _pair(
                        _cell("FRONT_USB_A_LABEL", "FRONT_USB_A_SPEC"),
                        _cell("FRONT_AC_OUTPUT_LABEL", "FRONT_AC_OUTPUT_SPEC"),
                    ),
                ),
            ),
            OverviewPanel(
                title="右側面",
                image="right_side_ports.png",
                alt="Right side port overview.",
                rows=(
                    _full(_cell("SIDE_DC_INPUT_LABEL", "SIDE_DC_INPUT_PV_SPEC", "SIDE_DC_INPUT_CAR_SPEC")),
                    _full(_cell("SIDE_AC_INPUT_LABEL", "SIDE_AC_INPUT_SPEC")),
                ),
            ),
        ),
    ),
}


def _layout_for_lang(lang: str) -> OverviewLayout:
    return _LAYOUTS.get(normalize_language(lang), _LAYOUTS["en"])


def _resolve_text(token: str, substitutions: dict[str, str]) -> str:
    if not token:
        return ""
    if token in PRODUCT_OVERVIEW_FIELD_PLACEHOLDERS:
        return rst_escape(substitutions.get(token, f"|{token}|"))
    return rst_escape(token)


def _cell_label(cell: OverviewCell, substitutions: dict[str, str]) -> str:
    return _resolve_text(cell.label, substitutions)


def _cell_specs(cell: OverviewCell, substitutions: dict[str, str]) -> list[str]:
    values: list[str] = []
    for spec in cell.specs:
        value = _resolve_text(spec, substitutions)
        if value:
            values.extend(line for line in split_spec_lines(value) if line)
    return values


def _cell_latex_args(cell: OverviewCell, substitutions: dict[str, str]) -> tuple[str, str]:
    label = spec_latex_cell(_cell_label(cell, substitutions))
    specs = [spec_latex_cell(value) for value in _cell_specs(cell, substitutions)]
    return label, r" \newline ".join(value for value in specs if value)


def _render_latex(layout: OverviewLayout, substitutions: dict[str, str]) -> str:
    raw_lines: list[str] = [rf"\section{{{latex_arg_escape(layout.title)}}}"]
    for panel in layout.panels:
        raw_lines.append(
            rf"\HBOverviewPanel{{{latex_arg_escape(panel.title)}}}{{{panel.image}}}{{%"
        )
        for row in panel.rows:
            if len(row.cells) == 1:
                label, specs = _cell_latex_args(row.cells[0], substitutions)
                raw_lines.append(rf"\HBOverviewFull{{{label}}}{{{specs}}}")
                continue
            if len(row.cells) == 2:
                left_label, left_specs = _cell_latex_args(row.cells[0], substitutions)
                right_label, right_specs = _cell_latex_args(row.cells[1], substitutions)
                raw_lines.append(
                    rf"\HBOverviewPair{{{left_label}}}{{{left_specs}}}{{{right_label}}}{{{right_specs}}}"
                )
                continue
            raise ValueError(f"Product overview row must have one or two cells, got {len(row.cells)}")
        raw_lines.append("}")

    lines = [".. only:: latex", "", "   .. raw:: latex", ""]
    lines.extend(f"      {line}" for line in raw_lines)
    return "\n".join(lines)


def _render_heading(lines: list[str], title: str, marker: str) -> None:
    lines.append(f"   {title}")
    lines.append(f"   {marker * len(title)}")


def _rst_cell_lines(cell: OverviewCell, substitutions: dict[str, str]) -> list[str]:
    label = _cell_label(cell, substitutions)
    specs = _cell_specs(cell, substitutions)
    lines: list[str] = []
    if label:
        lines.append(f"**{label}**")
    if specs:
        if lines:
            lines.append("")
        for idx, spec in enumerate(specs):
            if idx:
                lines.append("")
            lines.append(spec)
    return lines or [""]


def _render_table(lines: list[str], rows: list[OverviewRow], substitutions: dict[str, str]) -> None:
    if not rows:
        return

    column_count = len(rows[0].cells)
    widths = "100" if column_count == 1 else "50 50"
    lines.extend(
        [
            "   .. list-table::",
            "      :header-rows: 0",
            f"      :widths: {widths}",
            "",
        ]
    )
    for row in rows:
        if len(row.cells) != column_count:
            raise ValueError("Product overview table groups must not mix one-cell and two-cell rows")
        first_cell, *remaining_cells = row.cells
        first_lines = _rst_cell_lines(first_cell, substitutions)
        lines.append("      * -" if not first_lines[0] else f"      * - {first_lines[0]}")
        for line in first_lines[1:]:
            lines.append(f"          {line}" if line else "")
        for cell in remaining_cells:
            cell_lines = _rst_cell_lines(cell, substitutions)
            lines.append("        -" if not cell_lines[0] else f"        - {cell_lines[0]}")
            for line in cell_lines[1:]:
                lines.append(f"          {line}" if line else "")
    lines.append("")


def _render_panel_rst(lines: list[str], panel: OverviewPanel, substitutions: dict[str, str]) -> None:
    _render_heading(lines, panel.title, "-")
    lines.extend(
        [
            "",
            f"   .. image:: {_OVERVIEW_IMAGE_ROOT}/{panel.image}",
            f"      :alt: {panel.alt}",
            "      :width: 420px",
            "",
        ]
    )

    grouped_rows: list[OverviewRow] = []
    current_column_count: int | None = None
    for row in panel.rows:
        column_count = len(row.cells)
        if current_column_count is not None and column_count != current_column_count:
            _render_table(lines, grouped_rows, substitutions)
            grouped_rows = []
        grouped_rows.append(row)
        current_column_count = column_count
    _render_table(lines, grouped_rows, substitutions)


def _render_rst(layout: OverviewLayout, substitutions: dict[str, str]) -> str:
    lines = [".. only:: not latex", ""]
    _render_heading(lines, layout.title, "=")
    lines.append("")
    for panel in layout.panels:
        _render_panel_rst(lines, panel, substitutions)
    return "\n".join(lines).rstrip()


def render_product_overview(substitutions: dict[str, str], *, lang: str) -> str:
    layout = _layout_for_lang(lang)
    return "\n\n".join(
        [
            _render_latex(layout, substitutions),
            _render_rst(layout, substitutions),
        ]
    ).rstrip() + "\n"


def render_product_overview_page(template_text: str, substitutions: dict[str, str], *, lang: str) -> str:
    if PRODUCT_OVERVIEW_TOKEN not in template_text:
        return template_text
    cleaned = _FIELD_MARKER_RE.sub("", template_text)
    rendered = render_product_overview(substitutions, lang=lang).rstrip()
    return cleaned.replace(PRODUCT_OVERVIEW_TOKEN, rendered)
