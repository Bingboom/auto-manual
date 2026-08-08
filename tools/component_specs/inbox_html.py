"""Parse governed Inbox HTML into one renderer-neutral ComponentSpec."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from tools.component_specs.inbox import inbox_component_spec
from tools.component_specs.model import ComponentSpec


@dataclass(frozen=True)
class InboxHtmlSource:
    spec: ComponentSpec
    heading: Tag
    inbox_table: Tag
    tip_table: Tag


def _next_tag_sibling(tag: Tag) -> Tag | None:
    sibling = tag.next_sibling
    while sibling is not None:
        if isinstance(sibling, Tag):
            return sibling
        sibling = sibling.next_sibling
    return None


def _table_rows(table: Tag) -> list[list[Tag]]:
    rows: list[list[Tag]] = []
    for row in table.select("tr"):
        cells = [
            cell
            for cell in row.find_all(["th", "td"], recursive=False)
            if isinstance(cell, Tag)
        ]
        if cells:
            rows.append(cells)
    return rows


def parse_inbox_html(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    language: str,
    error_type: type[Exception],
) -> InboxHtmlSource:
    heading = soup.find("h1")
    if not isinstance(heading, Tag):
        raise error_type(f"{source_path}: in-the-box page is missing its H1")
    inbox_table = _next_tag_sibling(heading)
    if not isinstance(inbox_table, Tag) or inbox_table.name != "table":
        raise error_type(f"{source_path}: in-the-box H1 must be followed by a table")
    rows = _table_rows(inbox_table)
    if len(rows) != 1 or len(rows[0]) != 3:
        raise error_type(
            f"{source_path}: in-the-box table must contain one row with three items"
        )

    tip_table = _next_tag_sibling(inbox_table)
    if not isinstance(tip_table, Tag) or tip_table.name != "table":
        raise error_type(f"{source_path}: in-the-box grid is missing its tip table")
    tip_rows = _table_rows(tip_table)
    if len(tip_rows) != 1 or len(tip_rows[0]) != 2:
        raise error_type(
            f"{source_path}: in-the-box tip must contain one label cell and one body cell"
        )

    cards: list[dict[str, str]] = []
    for index, cell in enumerate(rows[0], start=1):
        image = cell.find("img")
        if not isinstance(image, Tag):
            raise error_type(f"{source_path}: in-the-box item {index} is missing its image")
        label = cell.get_text(" ", strip=True)
        if not label:
            raise error_type(f"{source_path}: in-the-box item {index} is missing its label")
        cards.append(
            {
                "image_ref": str(image.get("src") or ""),
                "alt": str(image.get("alt") or label),
                "label": label,
            }
        )

    tip_label_cell, tip_body_cell = tip_rows[0]
    tip_label = tip_label_cell.get_text(" ", strip=True)
    tip_body = tip_body_cell.get_text(" ", strip=True)
    try:
        spec = inbox_component_spec(
            accessibility_label=heading.get_text(" ", strip=True),
            cards=cards,
            tip_label=tip_label,
            tip_body=tip_body,
            source_ref=source_path.as_posix(),
            language=language,
        )
    except Exception as exc:
        raise error_type(f"{source_path}: {exc}") from exc
    return InboxHtmlSource(
        spec=spec,
        heading=heading,
        inbox_table=inbox_table,
        tip_table=tip_table,
    )


__all__ = ["InboxHtmlSource", "parse_inbox_html"]
