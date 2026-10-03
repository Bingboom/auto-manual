"""Public IR consumer for the two independent icon/meaning panels."""
from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup, Tag

from tools.manual_ir import ManualIR, build_manual_ir_from_source
from tools.manual_ir.web_symbols import decode_pair_ir, load_web_pair_source


def render_pair_ir(ir: ManualIR) -> str:
    soup, source_table, header, body_rows = decode_pair_ir(ir)
    source_path = Path(ir.pages[0].source_ref)
    composition = soup.new_tag(
        "figure",
        attrs={
            "class": "hb-symbol-pair-composition",
            "aria-label": " / ".join(
                cell.get_text(" ", strip=True) for cell in header[:2]
            ),
        },
    )
    grid = soup.new_tag("div", attrs={"class": "hb-symbol-pair-grid"})
    composition.append(grid)

    for panel_index, column_offset in enumerate((0, 2)):
        panel = soup.new_tag(
            "div",
            attrs={
                "class": ["hb-symbol-panel", f"hb-symbol-panel-{panel_index + 1}"],
            },
        )
        table = soup.new_tag("table", attrs={"class": "hb-symbol-panel-table"})
        colgroup = soup.new_tag("colgroup")
        colgroup.append(soup.new_tag("col", attrs={"class": "hb-symbol-col-icon"}))
        colgroup.append(soup.new_tag("col", attrs={"class": "hb-symbol-col-meaning"}))
        table.append(colgroup)

        thead = soup.new_tag("thead")
        header_row = soup.new_tag("tr")
        for cell_index, source_cell in enumerate(
            header[column_offset : column_offset + 2]
        ):
            source_cell.extract()
            source_cell.name = "th"
            source_cell["scope"] = "col"
            source_cell["class"] = [
                "hb-symbol-icon-heading"
                if cell_index == 0
                else "hb-symbol-meaning-heading"
            ]
            header_row.append(source_cell)
        thead.append(header_row)
        table.append(thead)

        tbody = soup.new_tag("tbody")
        for source_row in body_rows:
            pair = source_row[column_offset : column_offset + 2]
            if not pair[0].find("img"):
                if pair[1].get_text(" ", strip=True):
                    raise ValueError(
                        f"{source_path}: symbol row has meaning copy without artwork"
                    )
                continue
            row = soup.new_tag("tr")
            icon_cell, meaning_cell = pair
            icon_cell.extract()
            meaning_cell.extract()
            icon_cell["class"] = ["hb-symbol-icon"]
            meaning_cell["class"] = ["hb-symbol-meaning"]
            image = icon_cell.find("img")
            if not isinstance(image, Tag):
                raise ValueError(
                    f"{source_path}: symbol row is missing its governed artwork"
                )
            for attribute in ("style", "width", "height"):
                image.attrs.pop(attribute, None)
            image["class"] = [*image.get("class", []), "hb-symbol-art"]
            row.append(icon_cell)
            row.append(meaning_cell)
            tbody.append(row)
        table.append(tbody)
        panel.append(table)
        grid.append(panel)

    source_table.replace_with(composition)
    return str(composition)


def transform_symbol_pairs(
    soup: BeautifulSoup, *, source_path: Path, error_type: type[Exception],
    language: str | None = None, model: str | None = None, region: str | None = None,
) -> None:
    try:
        source = load_web_pair_source(
            str(soup), source_path=source_path, language=language, model=model, region=region,
        )
        rendered = render_pair_ir(build_manual_ir_from_source(source))
    except ValueError as exc:
        raise error_type(str(exc)) from exc
    original = source.pages[0].blocks[0][1]["table_html"]
    table = next(table for table in soup.find_all("table") if str(table) == original)
    table.replace_with(BeautifulSoup(rendered, "html.parser", preserve_whitespace_tags={"table"}).figure)
