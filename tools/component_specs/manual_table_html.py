"""HTML source adapters for shared LCD, troubleshooting, and symbol tables."""
from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup, Tag

from tools.component_specs.model import ComponentSpec
from tools.component_specs.manual_tables import (
    lcd_icon_component_spec,
    symbol_icon_component_spec,
    symbol_signal_component_spec,
    troubleshooting_component_spec,
)
from tools.manual_ir.web_symbols import decode_pair_table, decode_signal_table
from tools.manual_ir.web_tables import decode_table, declared_tables, table_boundary


def _content(cell: Tag, key: str) -> dict[str, str]:
    return {
        f"{key}_html": cell.decode_contents().strip(),
        f"{key}_text": cell.get_text("\n", strip=True),
    }


def _header(cell: Tag) -> dict[str, str]:
    return _content(cell, "content")


def parse_lcd_icon_html(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    declared_page: bool,
    language: str,
    table: Tag | None = None,
) -> tuple[ComponentSpec, Tag, tuple[Tag, ...]]:
    tables = [table] if table is not None else declared_tables(soup, "lcd", declared_page)
    if len(tables) != 1:
        raise ValueError(f"{source_path}: LCD component requires exactly one table")
    table = tables[0]
    _, _, rows = decode_table(table, "lcd", f"{source_path}#lcd-icons")
    numbered = "lcd-unnumbered" not in table.get("class", [])
    values = []
    images = []
    for index, row in enumerate(rows):
        cells = row.find_all(["th", "td"], recursive=False)
        icon, name, description = cells[-3:]
        image = icon.find("img")
        if not isinstance(image, Tag):
            raise ValueError(f"{source_path}: LCD row {index + 1} has no icon")
        images.append(image)
        values.append(
            {
                **(_content(cells[0], "number") if numbered else {}),
                **_content(name, "name"),
                **_content(description, "description"),
                "icon_alt": str(image.get("alt") or name.get_text(" ", strip=True)),
                "asset_index": index,
            }
        )
    boundary = table_boundary(table, "lcd")
    spec = lcd_icon_component_spec(
        accessibility_label=str(boundary.get("aria-label") or "LCD icon meanings"),
        rows=values,
        numbered=numbered,
        icon_refs=[str(image.get("src") or "") for image in images],
        source_ref=f"{source_path}#lcd-icons",
        language=language,
    )
    return spec, boundary, tuple(images)


def parse_troubleshooting_html(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    declared_page: bool,
    language: str,
) -> tuple[ComponentSpec, Tag, tuple[Tag, ...]]:
    tables = declared_tables(soup, "troubleshooting", declared_page)
    if len(tables) != 1:
        raise ValueError(
            f"{source_path}: troubleshooting component requires exactly one table"
        )
    table = tables[0]
    _, header_rows, data_rows = decode_table(
        table, "troubleshooting", f"{source_path}#troubleshooting"
    )
    header_cells = header_rows[0].find_all(["th", "td"], recursive=False)
    values = []
    for row in data_rows:
        code, measures = row.find_all(["th", "td"], recursive=False)
        values.append(
            {**_content(code, "code"), **_content(measures, "measures")}
        )
    spec = troubleshooting_component_spec(
        headers=[_header(cell) for cell in header_cells],
        rows=values,
        source_ref=f"{source_path}#troubleshooting",
        language=language,
    )
    return spec, table_boundary(table, "troubleshooting"), ()


def parse_symbol_tables_html(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    expected_signal_rows: int,
    language: str,
) -> tuple[
    tuple[ComponentSpec, Tag, tuple[Tag, ...]],
    tuple[ComponentSpec, Tag, tuple[Tag, ...]],
]:
    signal_payload, signal_table, signal_headers, signal_rows = decode_signal_table(
        soup,
        source_path=source_path,
        expected_body_rows=expected_signal_rows,
    )
    signal_spec = symbol_signal_component_spec(
        accessibility_label=" / ".join(signal_payload["headers"]),
        headers=[_header(cell) for cell in signal_headers],
        rows=[
            {
                "label": label,
                **_content(row.find_all("td", recursive=False)[1], "meaning"),
            }
            for label, row in zip(signal_payload["labels"], signal_rows, strict=True)
        ],
        source_ref=f"{source_path}#symbol-signals",
        language=language,
    )

    return (
        (signal_spec, signal_table, ()),
        parse_symbol_icon_html(soup, source_path=source_path, language=language),
    )


def parse_symbol_icon_html(
    soup: BeautifulSoup, *, source_path: Path, language: str,
) -> tuple[ComponentSpec, Tag, tuple[Tag, ...]]:
    _, icon_table, icon_headers, icon_rows = decode_pair_table(
        soup, source_path=source_path
    )
    images: list[Tag] = []
    panels = []
    for offset in (0, 2):
        panel = []
        for cells in icon_rows:
            icon_cell, meaning_cell = cells[offset : offset + 2]
            image = icon_cell.find("img")
            if not isinstance(image, Tag):
                continue
            asset_index = len(images)
            images.append(image)
            panel.append(
                {
                    "asset_index": asset_index,
                    "icon_alt": str(image.get("alt") or "symbol"),
                    **_content(meaning_cell, "meaning"),
                }
            )
        panels.append(panel)
    icon_spec = symbol_icon_component_spec(
        accessibility_label=" / ".join(
            cell.get_text(" ", strip=True) for cell in icon_headers[:2]
        ),
        headers=[_header(cell) for cell in icon_headers],
        panels=panels,
        icon_refs=[str(image.get("src") or "") for image in images],
        source_ref=f"{source_path}#symbol-icons",
        language=language,
    )
    return icon_spec, icon_table, tuple(images)



__all__ = [
    "parse_lcd_icon_html",
    "parse_symbol_tables_html",
    "parse_troubleshooting_html",
]
