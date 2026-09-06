"""Direct Web renderer for the embedded hybrid LCD Mode component."""
from __future__ import annotations

from bs4 import BeautifulSoup, Tag

from tools.component_specs.lcd_mode_adapters import web_lcd_mode_projection
from tools.component_specs.model import ComponentSpec


def _append_html(soup: BeautifulSoup, cell: Tag, value: str) -> None:
    fragment = BeautifulSoup(value, "html.parser")
    for node in list(fragment.contents):
        cell.append(node.extract())


def render_lcd_mode_component(spec: ComponentSpec) -> str:
    projection = web_lcd_mode_projection(spec)
    soup = BeautifulSoup("", "html.parser")
    figure = soup.new_tag(
        "figure",
        attrs={
            "class": projection["composition_class"],
            "aria-label": projection["accessibility_label"],
            "data-component-id": spec.component_id,
        },
    )
    art_panel = soup.new_tag("div", attrs={"class": projection["art_panel_class"]})
    art_panel.append(
        soup.new_tag(
            "img",
            attrs={
                "class": "hb-lcd-mode-art",
                "src": projection["artwork_ref"],
                "alt": projection["accessibility_label"],
            },
        )
    )
    table_panel = soup.new_tag(
        "div", attrs={"class": projection["table_panel_class"]}
    )
    table = soup.new_tag("table", attrs={"class": projection["table_class"]})
    colgroup = soup.new_tag("colgroup")
    for css_class in (
        "hb-lcd-mode-col-state",
        "hb-lcd-mode-col-action",
        "hb-lcd-mode-col-copy",
    ):
        colgroup.append(soup.new_tag("col", attrs={"class": css_class}))
    table.append(colgroup)
    body = soup.new_tag("tbody")
    for group in projection["groups"]:
        for index, action in enumerate(group["actions"]):
            row = soup.new_tag("tr")
            if index == 0:
                state = soup.new_tag(
                    "td", attrs={"class": "hb-lcd-mode-state", "rowspan": "3"}
                )
                _append_html(soup, state, group["state_html"])
                row.append(state)
            action_cell = soup.new_tag("td", attrs={"class": "hb-lcd-mode-action"})
            copy_cell = soup.new_tag("td", attrs={"class": "hb-lcd-mode-copy"})
            _append_html(soup, action_cell, action["action_html"])
            _append_html(soup, copy_cell, action["description_html"])
            row.extend((action_cell, copy_cell))
            body.append(row)
    table.append(body)
    table_panel.append(table)
    figure.extend((art_panel, table_panel))
    soup.append(figure)
    return str(soup)


__all__ = ["render_lcd_mode_component"]
