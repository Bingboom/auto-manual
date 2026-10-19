"""Small HTML construction helpers for the FCC Web adapter."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from bs4 import BeautifulSoup, NavigableString, Tag


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


def append_fcc_blocks(
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


def fcc_opening_copy(soup: BeautifulSoup, lines: list[str]) -> Tag:
    line_block = soup.new_tag("div", attrs={"class": "line-block"})
    for text in lines:
        line = soup.new_tag("div", attrs={"class": "line"})
        line.string = text
        line_block.append(line)
    return line_block


__all__ = ["append_fcc_blocks", "fcc_opening_copy"]
