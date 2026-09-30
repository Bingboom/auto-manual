"""Shared Web table presentation for authored LCD and symbol references."""
from bs4 import BeautifulSoup

from tools.component_specs.reference_table import reference_table_projection


def _row(soup, values, *, header=False):
    row = soup.new_tag("tr")
    for value in values:
        cell = soup.new_tag("th" if header else "td")
        if header:
            cell["scope"] = "col"
        fragment = BeautifulSoup(value["html"], "html.parser")
        if fragment.get_text("\n", strip=True) != value["text"]:
            raise ValueError("reference table HTML and text differ")
        if fragment.find(["img", "table", "script", "style"]):
            raise ValueError("text reference cell contains unsupported markup")
        for node in list(fragment.contents):
            cell.append(node.extract())
        row.append(cell)
    return row


def render_reference_table_component(spec):
    projection = reference_table_projection(spec)
    soup = BeautifulSoup("", "html.parser")
    figure = soup.new_tag("figure", attrs={
        "class": ["hb-reference-composition", f"hb-reference-{spec.variant}"],
        "data-component-id": spec.component_id, "data-component-variant": spec.variant,
        "aria-label": projection["label"], "tabindex": "0",
    })
    table = soup.new_tag("table", attrs={"class": "hb-reference-table"})
    if projection["headers"]:
        head = soup.new_tag("thead")
        head.append(_row(soup, projection["headers"], header=True))
        table.append(head)
    body = soup.new_tag("tbody")
    for row in projection["rows"]:
        body.append(_row(soup, row))
    table.append(body)
    figure.append(table)
    return str(figure)
