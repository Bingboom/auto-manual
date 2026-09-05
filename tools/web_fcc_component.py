"""Responsive Web adapter for the renderer-neutral FCC ComponentSpec."""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, NavigableString, Tag

from tools.component_specs.fcc import COMPONENT_ID
from tools.component_specs.fcc_adapters import web_fcc_projection
from tools.manual_ir import ManualIR, build_manual_ir_from_source
from tools.manual_ir.web_fcc import decode_fcc_ir, load_web_fcc_source


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


def render_fcc_ir(ir: ManualIR) -> str:
    spec, mark_path = decode_fcc_ir(ir)
    projection = web_fcc_projection(spec)
    soup = BeautifulSoup("", "html.parser")
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
            "src": mark_path,
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

    return str(composition)


def transform_fcc(
    soup: BeautifulSoup, *, source_path: Path, config: Mapping[str, Any],
    error_type: type[Exception], language: str | None = None,
    model: str | None = None, region: str | None = None,
) -> None:
    try:
        source = load_web_fcc_source(
            str(soup), source_path=source_path, config=config,
            language=language, model=model, region=region,
        )
        rendered = render_fcc_ir(build_manual_ir_from_source(source))
    except ValueError as exc:
        raise error_type(str(exc)) from exc
    # The parser owns all following FCC siblings; mutate only after replay.
    heading = soup.find("h1")
    for node in list(heading.find_next_siblings()):
        node.decompose()
    heading.insert_after(BeautifulSoup(rendered, "html.parser").figure)


__all__ = ["transform_fcc", "render_fcc_ir"]
