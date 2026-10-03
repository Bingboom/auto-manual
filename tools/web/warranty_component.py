"""Direct Web renderers for embedded warranty ComponentSpecs."""
from __future__ import annotations

from bs4 import BeautifulSoup, Tag

from tools.component_specs.model import ComponentSpec
from tools.component_specs.warranty import (
    WARRANTY_LEAD_COMPONENT_ID,
    WARRANTY_SECTION_COMPONENT_ID,
    WARRANTY_YEARS_COMPONENT_ID,
)
from tools.component_specs.warranty_adapters import web_warranty_projection


def _append_fragment(soup: BeautifulSoup, parent: Tag, html: str) -> None:
    fragment = BeautifulSoup(html, "html.parser")
    for node in list(fragment.contents):
        parent.append(node.extract())


def _render_lead(spec: ComponentSpec, projection: dict) -> str:
    soup = BeautifulSoup("", "html.parser")
    figure = soup.new_tag(
        "figure",
        attrs={
            "class": projection["component_class"],
            "aria-label": projection["accessibility_label"],
            "data-component-id": spec.component_id,
        },
    )
    lead = soup.new_tag("div", attrs={"class": "hb-warranty-intro-panel"})
    note = soup.new_tag("div", attrs={"class": "hb-warranty-local-note"})
    _append_fragment(soup, lead, projection["lead_html"])
    _append_fragment(soup, note, projection["local_note_html"])
    figure.extend((lead, note))
    soup.append(figure)
    return str(soup)


def _render_section(spec: ComponentSpec, projection: dict) -> str:
    soup = BeautifulSoup("", "html.parser")
    figure = soup.new_tag(
        "figure",
        attrs={
            "class": projection["component_class"],
            "aria-label": projection["title"],
            "data-warranty-card-index": str(projection["section_index"]),
            "data-component-id": spec.component_id,
        },
    )
    for block in projection["blocks"]:
        _append_fragment(soup, figure, block["html"])
    soup.append(figure)
    return str(soup)


def _render_years(spec: ComponentSpec, projection: dict) -> str:
    soup = BeautifulSoup("", "html.parser")
    figure = soup.new_tag(
        "figure",
        attrs={
            "class": projection["component_class"],
            "aria-label": projection["title"],
            "data-component-id": spec.component_id,
        },
    )
    grid = soup.new_tag("div", attrs={"class": "hb-warranty-period-grid"})
    for period in projection["periods"]:
        item = soup.new_tag(
            "div",
            attrs={
                "class": "hb-warranty-period-item",
                "aria-label": f"{period['number']} {period['unit']} {period['label']}",
            },
        )
        heading = soup.new_tag("div", attrs={"class": "hb-warranty-period-heading"})
        badge = soup.new_tag("span", attrs={"class": "hb-warranty-year-badge"})
        badge.string = period["number"]
        title = soup.new_tag("div", attrs={"class": "hb-warranty-period-title"})
        unit = soup.new_tag("strong", attrs={"class": "hb-warranty-years-unit"})
        unit.string = period["unit"]
        label = soup.new_tag("strong", attrs={"class": "hb-warranty-period-label"})
        label.string = period["label"]
        title.extend((unit, label))
        heading.extend((badge, title))
        copy = soup.new_tag("div", attrs={"class": "hb-warranty-period-copy"})
        _append_fragment(soup, copy, period["body_html"])
        item.extend((heading, copy))
        grid.append(item)
    figure.append(grid)
    soup.append(figure)
    return str(soup)


def render_warranty_component(spec: ComponentSpec) -> str:
    projection = web_warranty_projection(spec)
    if spec.component_id == WARRANTY_LEAD_COMPONENT_ID:
        return _render_lead(spec, projection)
    if spec.component_id == WARRANTY_SECTION_COMPONENT_ID:
        return _render_section(spec, projection)
    if spec.component_id == WARRANTY_YEARS_COMPONENT_ID:
        return _render_years(spec, projection)
    raise ValueError(f"unsupported warranty component {spec.component_id!r}")


__all__ = ["render_warranty_component"]
