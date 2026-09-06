"""Structure-first HTML source adapter for the three warranty components."""
from __future__ import annotations

from pathlib import Path
import re

from bs4 import BeautifulSoup, Tag

from tools.component_specs.warranty import (
    warranty_lead_component_spec,
    warranty_section_component_spec,
    warranty_years_component_spec,
)


_PERIOD_HEADING = re.compile(r"^(\d+)\s*(\D\S*)(?:\s+(.+))?$")


def _period(cell: Tag, *, source_path: Path) -> dict[str, str]:
    clone = BeautifulSoup(str(cell), "html.parser").find("td")
    if not isinstance(clone, Tag):
        raise ValueError(f"{source_path}: invalid warranty period cell")
    strong = [value for value in clone.find_all("strong") if isinstance(value, Tag)]
    if not strong:
        raise ValueError(f"{source_path}: warranty period has no heading")
    match = _PERIOD_HEADING.fullmatch(strong[0].get_text(" ", strip=True))
    if match is None:
        raise ValueError(f"{source_path}: warranty duration heading changed")
    number, unit, inline_label = match.groups()
    label = str(inline_label or "").strip()
    paragraphs = [strong[0].find_parent("p")]
    if not label:
        if len(strong) < 2:
            raise ValueError(f"{source_path}: warranty duration label is missing")
        label = strong[1].get_text(" ", strip=True)
        paragraphs.append(strong[1].find_parent("p"))
    for paragraph in paragraphs:
        if isinstance(paragraph, Tag):
            paragraph.decompose()
    body_html = clone.decode_contents().strip()
    body_text = clone.get_text(" ", strip=True)
    if not body_html or not body_text:
        raise ValueError(f"{source_path}: warranty period body is empty")
    return {
        "number": number,
        "unit": unit,
        "label": label,
        "body_html": body_html,
        "body_text": body_text,
    }


def _blocks(nodes: list[Tag], *, source_path: Path) -> list[dict[str, object]]:
    blocks: list[dict[str, object]] = []
    for node in nodes:
        if node.name == "p":
            blocks.append(
                {
                    "kind": "paragraph",
                    "html": str(node),
                    "text": node.get_text(" ", strip=True),
                }
            )
            continue
        if node.name in {"ul", "ol"}:
            items = [
                item.get_text(" ", strip=True)
                for item in node.find_all("li", recursive=False)
                if item.get_text(" ", strip=True)
            ]
            blocks.append({"kind": "list", "html": str(node), "items": items})
            continue
        raise ValueError(
            f"{source_path}: unsupported warranty body block <{node.name}>"
        )
    return blocks


def parse_warranty_html(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    expected_sections: int,
    expected_years: list[str],
    language: str,
) -> tuple[tuple[object, tuple[Tag, ...]], ...]:
    heading = soup.find("h1", recursive=False)
    paragraphs = [
        node for node in soup.find_all("p", recursive=False) if isinstance(node, Tag)
    ]
    sections = [
        node for node in soup.find_all("section", recursive=False) if isinstance(node, Tag)
    ]
    if not isinstance(heading, Tag) or len(paragraphs) != 2:
        raise ValueError(f"{source_path}: warranty lead structure changed")
    if len(sections) != expected_sections:
        raise ValueError(
            f"{source_path}: expected {expected_sections} warranty sections; "
            f"found {len(sections)}"
        )
    claims: list[tuple[object, tuple[Tag, ...]]] = [
        (
            warranty_lead_component_spec(
                accessibility_label=heading.get_text(" ", strip=True),
                lead_html=str(paragraphs[0]),
                local_note_html=str(paragraphs[1]),
                source_ref=f"{source_path}#warranty-lead",
                language=language,
            ),
            (paragraphs[0], paragraphs[1]),
        )
    ]
    period_count = 0
    for index, section in enumerate(sections, start=1):
        title = section.find("h2", recursive=False)
        if not isinstance(title, Tag):
            raise ValueError(f"{source_path}: warranty section {index} has no H2")
        table = section.find("table", recursive=False)
        if isinstance(table, Tag):
            rows = table.find_all("tr")
            if len(rows) != 1:
                raise ValueError(f"{source_path}: warranty period needs one row")
            cells = [
                cell for cell in rows[0].find_all(["td", "th"], recursive=False)
                if isinstance(cell, Tag)
            ]
            periods = [_period(cell, source_path=source_path) for cell in cells]
            if [period["number"] for period in periods] != expected_years:
                raise ValueError(f"{source_path}: warranty year order changed")
            claims.append(
                (
                    warranty_years_component_spec(
                        title=title.get_text(" ", strip=True),
                        periods=periods,
                        source_ref=f"{source_path}#warranty-years",
                        language=language,
                    ),
                    (table,),
                )
            )
            period_count += 1
            continue
        content = [
            node for node in section.contents
            if isinstance(node, Tag) and node is not title
        ]
        claims.append(
            (
                warranty_section_component_spec(
                    title=title.get_text(" ", strip=True),
                    section_index=index,
                    blocks=_blocks(content, source_path=source_path),
                    source_ref=f"{source_path}#warranty-section-{index}",
                    language=language,
                ),
                tuple(content),
            )
        )
    if period_count != 1:
        raise ValueError(f"{source_path}: expected one warranty years component")
    return tuple(claims)


__all__ = ["parse_warranty_html"]
