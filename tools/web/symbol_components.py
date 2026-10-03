"""Semantic Web projections for localized manual symbol components."""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup, Tag

from tools.manual_ir import ManualIR, build_manual_ir_from_source
from tools.manual_ir.web_symbols import decode_signal_ir, load_web_signal_source


def render_signal_ir(ir: ManualIR) -> str:
    soup, table, headers, body_rows, labels = decode_signal_ir(ir)
    for colgroup in table.find_all("colgroup", recursive=False):
        colgroup.decompose()
    table.attrs.pop("style", None)
    table["class"] = ["hb-symbol-signal-table"]

    colgroup = soup.new_tag("colgroup")
    colgroup.append(
        soup.new_tag("col", attrs={"class": "hb-symbol-signal-col-label"})
    )
    colgroup.append(
        soup.new_tag("col", attrs={"class": "hb-symbol-signal-col-meaning"})
    )
    table.insert(0, colgroup)

    for index, header in enumerate(headers):
        header.attrs.pop("style", None)
        header["scope"] = "col"
        header["class"] = [
            "hb-symbol-signal-label-heading"
            if index == 0
            else "hb-symbol-signal-meaning-heading"
        ]

    for row, localized_label in zip(body_rows, labels, strict=True):
        label_cell, meaning_cell = [
            cell
            for cell in row.find_all("td", recursive=False)
            if isinstance(cell, Tag)
        ]
        label_cell.clear()
        label_cell.attrs.pop("style", None)
        label_cell["class"] = ["hb-symbol-signal-label-cell"]
        meaning_cell.attrs.pop("style", None)
        meaning_cell["class"] = ["hb-symbol-signal-meaning-cell"]

        badge = soup.new_tag(
            "span",
            attrs={
                "class": "hb-signal-badge",
                "aria-label": localized_label,
            },
        )
        icon = soup.new_tag(
            "span",
            attrs={"class": "hb-signal-icon", "aria-hidden": "true"},
        )
        icon.string = "⚠"
        label = soup.new_tag("span", attrs={"class": "hb-signal-label"})
        label.string = localized_label
        badge.append(icon)
        badge.append(label)
        label_cell.append(badge)

    composition = soup.new_tag(
        "figure",
        attrs={
            "class": "hb-symbol-signal-composition",
            "aria-label": " / ".join(
                header.get_text(" ", strip=True) for header in headers
            ),
        },
    )
    table.replace_with(composition)
    composition.append(table)
    return str(composition)


def transform_symbol_signal_table(
    soup: BeautifulSoup, *, source_path: Path, expected_body_rows: int,
    error_type: type[RuntimeError], language: str | None = None,
    model: str | None = None, region: str | None = None,
) -> None:
    try:
        source = load_web_signal_source(
            str(soup), source_path=source_path, expected_body_rows=expected_body_rows,
            language=language, model=model, region=region,
        )
        rendered = render_signal_ir(build_manual_ir_from_source(source))
    except ValueError as exc:
        raise error_type(str(exc)) from exc
    # Locate the already validated boundary by exact markup, without decoding again.
    original = source.pages[0].blocks[0][1]["table_html"]
    table = next(table for table in soup.find_all("table") if str(table) == original)
    # Preserve adjacent whitespace left by removal of the print colgroup.
    table.replace_with(BeautifulSoup(
        rendered, "html.parser", preserve_whitespace_tags={"table"},
    ).figure)


__all__ = ["transform_symbol_signal_table", "render_signal_ir"]
