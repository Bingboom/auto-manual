"""Responsive Web adapter for the renderer-neutral FCC ComponentSpec."""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, NavigableString, Tag

from tools.component_specs.fcc import COMPONENT_ID
from tools.component_specs.fcc_adapters import web_fcc_projection
from tools.component_specs.fcc_html import parse_fcc_html


def _append_paragraph_content(
    soup: BeautifulSoup,
    paragraph: Tag,
    block: Mapping[str, Any],
    *,
    continuation: bool,
) -> None:
    if continuation:
        paragraph.append(NavigableString(" "))
    label_text = str(block.get("label") or "").strip()
    if label_text:
        label = soup.new_tag("strong")
        label.string = label_text
        paragraph.append(label)
    body = str(block.get("text") or "").strip()
    if body:
        paragraph.append(NavigableString(f" {body}" if label_text else body))


def _append_blocks(
    soup: BeautifulSoup,
    parent: Tag,
    blocks: list[Mapping[str, Any]],
) -> None:
    paragraph: Tag | None = None
    for block in blocks:
        if block["kind"] != "list":
            if paragraph is None:
                paragraph = soup.new_tag("p")
                parent.append(paragraph)
            _append_paragraph_content(
                soup,
                paragraph,
                block,
                continuation=bool(paragraph.contents),
            )
            continue

        paragraph = None
        list_node = soup.new_tag("ul", attrs={"class": "simple"})
        for text in block["items"]:
            item = soup.new_tag("li")
            item_paragraph = soup.new_tag("p")
            item_paragraph.string = str(text)
            item.append(item_paragraph)
            list_node.append(item)
        parent.append(list_node)


def _opening_copy(soup: BeautifulSoup, lines: list[str]) -> Tag:
    line_block = soup.new_tag("div", attrs={"class": "line-block"})
    for text in lines:
        line = soup.new_tag("div", attrs={"class": "line"})
        line.string = text
        line_block.append(line)
    return line_block


def transform_fcc(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    config: Mapping[str, Any],
    error_type: type[Exception],
) -> None:
    source = parse_fcc_html(
        soup,
        source_path=source_path,
        config=config,
        error_type=error_type,
    )
    projection = web_fcc_projection(source.spec)
    composition = soup.new_tag(
        "figure",
        attrs={
            "class": projection["composition_class"],
            "aria-label": projection["accessibility_label"],
            "data-component-id": COMPONENT_ID,
        },
    )
    grid = soup.new_tag("div", attrs={"class": projection["grid_class"]})
    left = soup.new_tag(
        "div",
        attrs={
            "class": [projection["column_class"], "hb-fcc-column-left"],
        },
    )
    right = soup.new_tag(
        "div",
        attrs={
            "class": [projection["column_class"], "hb-fcc-column-right"],
        },
    )
    opening_row = soup.new_tag("div", attrs={"class": "hb-fcc-opening"})
    logo = soup.new_tag(
        "img",
        attrs={
            "class": projection["mark_class"],
            "src": str(config["mark_path"]),
            "alt": projection["accessibility_label"],
            "loading": "lazy",
        },
    )
    opening_copy = soup.new_tag("div", attrs={"class": "hb-fcc-opening-copy"})
    opening_copy.append(_opening_copy(soup, projection["opening_copy"]))
    opening_row.append(logo)
    opening_row.append(opening_copy)
    left.append(opening_row)
    _append_blocks(soup, left, projection["left_blocks"])
    _append_blocks(soup, right, projection["right_blocks"])
    grid.append(left)
    grid.append(right)
    composition.append(grid)

    for node in source.consumed_nodes:
        node.decompose()
    source.heading.insert_after(composition)


__all__ = ["transform_fcc"]
