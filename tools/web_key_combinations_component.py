"""Render key combinations through the existing English Web table layout."""
from html import escape
from pathlib import Path

from bs4 import BeautifulSoup

from tools.component_specs.key_combinations import key_combinations_projection
from tools.component_specs.model import ComponentSpec
from tools.web_presentation import _transform_key_combination_table


def render_key_combinations_component(spec: ComponentSpec) -> str:
    data = key_combinations_projection(spec, "web")
    head = "".join(f"<th>{escape(value)}</th>" for value in data["headers"])
    body = "".join("<tr>" + "".join(f"<td>{escape(value)}</td>" for value in row) + "</tr>"
                   for row in data["rows"])
    soup = BeautifulSoup(f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>", "html.parser")
    _transform_key_combination_table(soup, source_path=Path(spec.source_ref), minimum_body_rows=3)
    figure = soup.select_one("figure.hb-key-combination-composition")
    figure["data-component-id"] = spec.component_id
    return str(soup)
