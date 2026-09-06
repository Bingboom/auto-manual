"""Validate rich carriers retained beside embedded Web ComponentSpecs."""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, Tag

from tools.component_specs.fcc import fcc_semantic_projection
from tools.component_specs.inbox_adapters import web_inbox_projection
from tools.component_specs.model import ComponentSpec
from tools.component_specs.overview_adapters import web_overview_projection


def validate_fcc_carrier(spec: ComponentSpec, carrier_html: str) -> str:
    """Return unowned whitespace after proving FCC copy/semantic agreement."""

    carrier = BeautifulSoup(carrier_html, "html.parser")
    source_copy = carrier.get_text(" ", strip=True)
    semantics = fcc_semantic_projection(spec)
    expected_copy = [*semantics["opening_copy"]]
    for block in semantics["left_blocks"] + semantics["right_blocks"]:
        expected_copy.extend(
            [
                str(block.get("label") or ""),
                str(block.get("text") or ""),
                *[str(item) for item in block.get("items", [])],
            ]
        )
    if any(value and value not in source_copy for value in expected_copy):
        raise ValueError(f"{spec.source_ref}: FCC carrier does not match semantics")
    return "".join(str(node) for node in carrier.contents if not isinstance(node, Tag))


def validate_inbox_carrier(
    spec: ComponentSpec,
    carrier_html: str,
    *,
    source_ref: str,
) -> tuple[BeautifulSoup, Mapping[str, Any], list[Tag], list[Tag]]:
    """Parse one Inbox carrier and prove its cards/TIP match the spec."""

    carrier = BeautifulSoup(carrier_html, "html.parser")
    tables = carrier.find_all("table", recursive=False)
    if len(tables) != 2:
        raise ValueError(f"{source_ref}: Inbox carrier requires card and tip tables")
    inbox_rows, tip_rows = (table.find_all("tr") for table in tables)
    source_cells = (
        inbox_rows[0].find_all(["th", "td"], recursive=False)
        if len(inbox_rows) == 1
        else []
    )
    tip_cells = (
        tip_rows[0].find_all(["th", "td"], recursive=False)
        if len(tip_rows) == 1
        else []
    )
    projection = web_inbox_projection(spec)
    if len(source_cells) != 3 or len(tip_cells) != 2:
        raise ValueError(f"{source_ref}: Inbox carrier geometry changed")
    for card_data, cell in zip(projection["cards"], source_cells, strict=True):
        image = cell.find("img")
        if (
            not isinstance(image, Tag)
            or str(image.get("src") or "") != card_data["image_ref"]
            or cell.get_text(" ", strip=True) != card_data["label"]
        ):
            raise ValueError(
                f"{source_ref}: Inbox carrier does not match component semantics"
            )
    if (
        tip_cells[0].get_text(" ", strip=True) != projection["tip_label"]
        or tip_cells[1].get_text(" ", strip=True) != projection["tip_body"]
    ):
        raise ValueError(
            f"{source_ref}: Inbox tip carrier does not match component semantics"
        )
    return carrier, projection, source_cells, tip_cells


def validate_overview_carrier(
    spec: ComponentSpec,
    carrier_html: str,
    *,
    instance: Mapping[str, Any],
    source_path: Path,
) -> tuple[BeautifulSoup, list[tuple[Mapping[str, Any], Tag, Tag]]]:
    """Return ordered Overview view/image/section triples after agreement checks."""

    projection = web_overview_projection(spec, instance)
    soup = BeautifulSoup(carrier_html, "html.parser")
    resolved: list[tuple[Mapping[str, Any], Tag, Tag]] = []
    used_sections: set[int] = set()
    for view in projection["views"]:
        image = next(
            (
                candidate
                for candidate in soup.find_all("img")
                if str(candidate.get("src") or "") == str(view["image_ref"])
            ),
            None,
        )
        if not isinstance(image, Tag):
            raise ValueError(
                f"{source_path}: overview carrier is missing {view['image_ref']!r}"
            )
        section = image.find_parent("section")
        heading = section.find("h2") if isinstance(section, Tag) else None
        if (
            not isinstance(section, Tag)
            or id(section) in used_sections
            or not isinstance(heading, Tag)
            or heading.get_text(" ", strip=True) != str(view["title"])
        ):
            raise ValueError(
                f"{source_path}: overview carrier view {view['id']!r} changed"
            )
        source_copy = section.get_text(" ", strip=True)
        for callout in view["callouts"]:
            expected = [str(callout["label"]), *map(str, callout.get("body", []))]
            if any(value and value not in source_copy for value in expected):
                raise ValueError(
                    f"{source_path}: overview carrier callout {callout['id']!r} changed"
                )
        used_sections.add(id(section))
        resolved.append((view, image, section))
    return soup, resolved


__all__ = [
    "validate_fcc_carrier",
    "validate_inbox_carrier",
    "validate_overview_carrier",
]
