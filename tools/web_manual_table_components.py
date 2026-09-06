"""Native Web rendering for embedded LCD, troubleshooting, and symbol tables."""
from __future__ import annotations

from bs4 import BeautifulSoup, Tag

from tools.component_specs.manual_table_adapters import web_manual_table_projection
from tools.component_specs.manual_tables import (
    LCD_ICON_COMPONENT_ID,
    SYMBOL_ICON_COMPONENT_ID,
    SYMBOL_SIGNAL_COMPONENT_ID,
    TROUBLESHOOTING_COMPONENT_ID,
)
from tools.component_specs.model import ComponentSpec


def _append_html(cell: Tag, value: str) -> None:
    fragment = BeautifulSoup(value, "html.parser")
    for node in list(fragment.contents):
        cell.append(node.extract())


def _colgroup(soup: BeautifulSoup, classes: tuple[str, ...]) -> Tag:
    group = soup.new_tag("colgroup")
    for css_class in classes:
        group.append(soup.new_tag("col", attrs={"class": css_class}))
    return group


def _render_lcd(spec: ComponentSpec, projection: dict) -> str:
    soup = BeautifulSoup("", "html.parser")
    figure = soup.new_tag(
        "figure",
        attrs={
            "class": projection["component_class"],
            "aria-label": projection["accessibility_label"],
            "tabindex": "0",
            "data-component-id": spec.component_id,
        },
    )
    table = soup.new_tag("table", attrs={"class": "hb-lcd-icon-table"})
    table.append(
        _colgroup(
            soup,
            tuple(
                f"hb-lcd-col-{role}"
                for role in ("number", "icon", "name", "description")
            ),
        )
    )
    body = soup.new_tag("tbody")
    for row in projection["rows"]:
        tr = soup.new_tag("tr")
        number = soup.new_tag("td", attrs={"class": "hb-lcd-number"})
        icon = soup.new_tag("td", attrs={"class": "hb-lcd-icon"})
        name = soup.new_tag("td", attrs={"class": "hb-lcd-name"})
        description = soup.new_tag("td", attrs={"class": "hb-lcd-description"})
        _append_html(number, row["number_html"])
        icon.append(
            soup.new_tag(
                "img",
                attrs={
                    "class": "hb-lcd-icon-art",
                    "src": projection["assets"][row["asset_index"]],
                    "alt": row["icon_alt"],
                },
            )
        )
        _append_html(name, row["name_html"])
        _append_html(description, row["description_html"])
        tr.extend((number, icon, name, description))
        body.append(tr)
    table.append(body)
    figure.append(table)
    soup.append(figure)
    return str(soup)


def _render_troubleshooting(spec: ComponentSpec, projection: dict) -> str:
    soup = BeautifulSoup("", "html.parser")
    figure = soup.new_tag(
        "figure",
        attrs={
            "class": projection["component_class"],
            "aria-label": " / ".join(
                header["content_text"] for header in projection["headers"]
            ),
            "tabindex": "0",
            "data-component-id": spec.component_id,
        },
    )
    table = soup.new_tag("table", attrs={"class": "hb-troubleshooting-table"})
    table.append(
        _colgroup(
            soup,
            ("hb-troubleshooting-col-code", "hb-troubleshooting-col-measures"),
        )
    )
    head = soup.new_tag("thead")
    header_row = soup.new_tag("tr")
    for role, header in zip(
        ("code", "measures"), projection["headers"], strict=True
    ):
        cell = soup.new_tag(
            "th", attrs={"class": f"hb-troubleshooting-{role}", "scope": "col"}
        )
        _append_html(cell, header["content_html"])
        header_row.append(cell)
    head.append(header_row)
    table.append(head)
    body = soup.new_tag("tbody")
    for row in projection["rows"]:
        tr = soup.new_tag("tr")
        for role in ("code", "measures"):
            cell = soup.new_tag("td", attrs={"class": f"hb-troubleshooting-{role}"})
            _append_html(cell, row[f"{role}_html"])
            tr.append(cell)
        body.append(tr)
    table.append(body)
    figure.append(table)
    soup.append(figure)
    return str(soup)


def _render_signal(spec: ComponentSpec, projection: dict) -> str:
    soup = BeautifulSoup("", "html.parser")
    figure = soup.new_tag(
        "figure",
        attrs={
            "class": projection["component_class"],
            "aria-label": projection["accessibility_label"],
            "data-component-id": spec.component_id,
        },
    )
    table = soup.new_tag("table", attrs={"class": "hb-symbol-signal-table"})
    table.append(
        _colgroup(
            soup,
            ("hb-symbol-signal-col-label", "hb-symbol-signal-col-meaning"),
        )
    )
    head = soup.new_tag("thead")
    header_row = soup.new_tag("tr")
    for index, header in enumerate(projection["headers"]):
        cell = soup.new_tag(
            "th",
            attrs={
                "scope": "col",
                "class": (
                    "hb-symbol-signal-label-heading"
                    if index == 0
                    else "hb-symbol-signal-meaning-heading"
                ),
            },
        )
        _append_html(cell, header["content_html"])
        header_row.append(cell)
    head.append(header_row)
    table.append(head)
    body = soup.new_tag("tbody")
    for row in projection["rows"]:
        tr = soup.new_tag("tr")
        label_cell = soup.new_tag("td", attrs={"class": "hb-symbol-signal-label-cell"})
        badge = soup.new_tag(
            "span", attrs={"class": "hb-signal-badge", "aria-label": row["label"]}
        )
        icon = soup.new_tag("span", attrs={"class": "hb-signal-icon", "aria-hidden": "true"})
        icon.string = "⚠"
        label = soup.new_tag("span", attrs={"class": "hb-signal-label"})
        label.string = row["label"]
        badge.extend((icon, label))
        label_cell.append(badge)
        meaning = soup.new_tag("td", attrs={"class": "hb-symbol-signal-meaning-cell"})
        _append_html(meaning, row["meaning_html"])
        tr.extend((label_cell, meaning))
        body.append(tr)
    table.append(body)
    figure.append(table)
    soup.append(figure)
    return str(soup)


def _render_icons(spec: ComponentSpec, projection: dict) -> str:
    soup = BeautifulSoup("", "html.parser")
    figure = soup.new_tag(
        "figure",
        attrs={
            "class": projection["component_class"],
            "aria-label": projection["accessibility_label"],
            "data-component-id": spec.component_id,
        },
    )
    grid = soup.new_tag("div", attrs={"class": "hb-symbol-pair-grid"})
    for panel_index, panel in enumerate(projection["panels"]):
        panel_node = soup.new_tag(
            "div",
            attrs={"class": ["hb-symbol-panel", f"hb-symbol-panel-{panel_index + 1}"]},
        )
        table = soup.new_tag("table", attrs={"class": "hb-symbol-panel-table"})
        table.append(_colgroup(soup, ("hb-symbol-col-icon", "hb-symbol-col-meaning")))
        head = soup.new_tag("thead")
        header_row = soup.new_tag("tr")
        for index, header in enumerate(projection["headers"][panel_index * 2 : panel_index * 2 + 2]):
            cell = soup.new_tag(
                "th",
                attrs={
                    "scope": "col",
                    "class": "hb-symbol-icon-heading" if index == 0 else "hb-symbol-meaning-heading",
                },
            )
            _append_html(cell, header["content_html"])
            header_row.append(cell)
        head.append(header_row)
        table.append(head)
        body = soup.new_tag("tbody")
        for row in panel:
            tr = soup.new_tag("tr")
            icon_cell = soup.new_tag("td", attrs={"class": "hb-symbol-icon"})
            icon_cell.append(
                soup.new_tag(
                    "img",
                    attrs={
                        "class": "hb-symbol-art",
                        "src": projection["assets"][row["asset_index"]],
                        "alt": row["icon_alt"],
                    },
                )
            )
            meaning = soup.new_tag("td", attrs={"class": "hb-symbol-meaning"})
            _append_html(meaning, row["meaning_html"])
            tr.extend((icon_cell, meaning))
            body.append(tr)
        table.append(body)
        panel_node.append(table)
        grid.append(panel_node)
    figure.append(grid)
    soup.append(figure)
    return str(soup)


def render_manual_table_component(spec: ComponentSpec) -> str:
    projection = web_manual_table_projection(spec)
    if spec.component_id == LCD_ICON_COMPONENT_ID:
        return _render_lcd(spec, projection)
    if spec.component_id == TROUBLESHOOTING_COMPONENT_ID:
        return _render_troubleshooting(spec, projection)
    if spec.component_id == SYMBOL_SIGNAL_COMPONENT_ID:
        return _render_signal(spec, projection)
    if spec.component_id == SYMBOL_ICON_COMPONENT_ID:
        return _render_icons(spec, projection)
    raise ValueError(f"unsupported manual table component: {spec.component_id}")


__all__ = ["render_manual_table_component"]
