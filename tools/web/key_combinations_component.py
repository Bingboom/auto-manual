"""Render key combinations through the existing English Web table layout."""
from html import escape
from pathlib import Path

from bs4 import BeautifulSoup

from tools.component_specs.key_combinations import key_combinations_projection
from tools.component_specs.model import ComponentSpec
from tools.web.presentation import _transform_key_combination_table


def render_key_combinations_component(spec: ComponentSpec, carrier_html: str = "") -> str:
    data = key_combinations_projection(spec, "web")
    head = "".join(f"<th>{escape(value)}</th>" for value in data["headers"])
    body = "".join("<tr>" + "".join(f"<td>{escape(value)}</td>" for value in row) + "</tr>"
                   for row in data["rows"])
    soup = BeautifulSoup(f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>", "html.parser")
    if carrier_html:
        carrier = BeautifulSoup(carrier_html, "html.parser")
        tables = carrier.select("table.hb-key-combination-table")
        if len(tables) != 1:
            raise ValueError(f"{spec.source_ref}: key-combination carrier requires one table")
        source_cells = tables[0].select("thead > tr > th, tbody > tr > td")
        output_cells = soup.select("thead > tr > th, tbody > tr > td")
        if ([cell.get_text(" ", strip=True) for cell in source_cells]
                != [cell.get_text(" ", strip=True) for cell in output_cells]):
            raise ValueError(f"{spec.source_ref}: key-combination carrier copy disagrees with component")
        # ComponentSpec owns the copy and geometry; the frozen carrier retains
        # source-authored emphasis and line breaks, as for specification tables.
        for source, target in zip(source_cells, output_cells, strict=True):
            target.clear()
            for child in list(source.contents):
                target.append(child.extract())
    _transform_key_combination_table(soup, source_path=Path(spec.source_ref), minimum_body_rows=3)
    figure = soup.select_one("figure.hb-key-combination-composition")
    figure["data-component-id"] = spec.component_id
    return str(soup)
