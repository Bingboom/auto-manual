"""Render embedded auto-resume copy through the existing shared Web layout."""
from html import escape
from pathlib import Path

from bs4 import BeautifulSoup

from tools.component_specs.auto_resume import auto_resume_projection
from tools.component_specs.model import ComponentSpec
from tools.web.presentation import _transform_auto_resume_table


def render_auto_resume_component(spec: ComponentSpec) -> str:
    data = auto_resume_projection(spec, "web")
    left, right = data["conditions"]
    rows = [(left[0], right[0]), (left[1], right[1]), ("", right[2]), (left[2], right[3])]
    head = "".join(f"<th>{escape(value)}</th>" for value in data["headers"])
    body = "".join("<tr>" + "".join(f"<td>{escape(value)}</td>" for value in row) + "</tr>" for row in rows)
    soup = BeautifulSoup(f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>", "html.parser")
    _transform_auto_resume_table(soup, source_path=Path(spec.source_ref), expected_body_rows=4)
    figure = soup.select_one("figure.hb-auto-resume-composition")
    figure["data-component-id"] = spec.component_id
    figure["tabindex"] = "0"
    return str(soup)
