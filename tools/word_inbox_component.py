"""Editable Word/HTML adapter for the renderer-neutral Inbox ComponentSpec."""
from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any, Mapping

from bs4 import BeautifulSoup, Tag

from tools.component_specs.inbox import COMPONENT_ID
from tools.component_specs.inbox_adapters import word_inbox_projection
from tools.component_specs.inbox_html import parse_inbox_html


def _is_plain_inventory(soup: BeautifulSoup) -> bool:
    """A text-only inventory has no illustrated-card or adjacent tip semantics."""
    heading = soup.find("h1")
    table = heading.find_next_sibling() if isinstance(heading, Tag) else None
    if not isinstance(table, Tag) or table.name != "table" or table.find("img"):
        return False
    rows = table.find_all("tr")
    cells = rows[0].find_all(["td", "th"], recursive=False) if len(rows) == 1 else []
    following = table.find_next_sibling()
    return (
        len(cells) == 3
        and all(cell.get_text(" ", strip=True) for cell in cells)
        and (following is None or following.name != "table")
    )


def transform_word_inbox_html(
    html_fragment: str,
    *,
    source_path: Path,
    config: Mapping[str, Any],
    language: str,
) -> str:
    """Project Inbox ComponentSpec as editable Word-friendly HTML tables."""
    patterns = [str(pattern).lower() for pattern in config["source_patterns"]]
    if not any(fnmatch.fnmatch(source_path.stem.lower(), pattern) for pattern in patterns):
        return html_fragment
    soup = BeautifulSoup(html_fragment, "html.parser")
    if _is_plain_inventory(soup):
        return html_fragment
    source = parse_inbox_html(
        soup,
        source_path=source_path,
        language=language,
        error_type=RuntimeError,
    )
    projection = word_inbox_projection(source.spec)

    table = soup.new_tag(
        "table",
        attrs={
            "class": ["manual-table", projection["table_class"]],
            "aria-label": projection["accessibility_label"],
            "data-component-id": COMPONENT_ID,
            "style": "width:100%;border-collapse:separate;border-spacing:8px 0;",
        },
    )
    body = soup.new_tag("tbody")
    row = soup.new_tag("tr")
    for card in projection["cards"]:
        cell = soup.new_tag(
            "td",
            attrs={
                "class": projection["card_class"],
                "style": (
                    "width:33.333%;padding:10px;vertical-align:top;"
                    "text-align:center;border:1px solid #888;"
                ),
            },
        )
        number = soup.new_tag("p", attrs={"class": "hb-inbox-word-number"})
        strong = soup.new_tag("strong")
        strong.string = str(card["number"])
        number.append(strong)
        image = soup.new_tag(
            "img",
            attrs={
                "src": str(card["image_ref"]),
                "alt": str(card["alt"]),
                "style": "width:120px;height:auto;",
            },
        )
        label = soup.new_tag("p", attrs={"class": "hb-inbox-word-label"})
        label.string = str(card["label"])
        cell.append(number)
        cell.append(image)
        cell.append(label)
        row.append(cell)
    body.append(row)
    table.append(body)

    tip_table = soup.new_tag(
        "table",
        attrs={
            "class": ["manual-callout-table", projection["tip_class"]],
            "role": "note",
            "data-component-id": COMPONENT_ID,
            "style": "width:100%;border-collapse:collapse;margin:8px 0 16px 0;",
        },
    )
    tip_body = soup.new_tag("tbody")
    tip_row = soup.new_tag("tr")
    tip_label = soup.new_tag(
        "td",
        attrs={
            "class": "hb-inbox-word-tip-label",
            "style": "width:16%;padding:8px;border:1px solid #888;font-weight:700;",
        },
    )
    tip_label.string = projection["tip_label"]
    tip_copy = soup.new_tag(
        "td",
        attrs={
            "class": "hb-inbox-word-tip-body",
            "style": "width:84%;padding:8px;border:1px solid #888;",
        },
    )
    tip_copy.string = projection["tip_body"]
    tip_row.append(tip_label)
    tip_row.append(tip_copy)
    tip_body.append(tip_row)
    tip_table.append(tip_body)

    source.inbox_table.replace_with(table)
    source.tip_table.replace_with(tip_table)
    return str(soup)


__all__ = ["transform_word_inbox_html"]
