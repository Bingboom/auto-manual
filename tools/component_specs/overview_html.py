"""Parse governed product-overview HTML into one ComponentSpec."""
from __future__ import annotations

from dataclasses import dataclass
import fnmatch
from pathlib import Path
from typing import Any, Mapping

from bs4 import BeautifulSoup, Tag

from tools.component_specs.model import ComponentSpec
from tools.component_specs.overview import overview_component_spec


@dataclass(frozen=True)
class OverviewHtmlView:
    view_id: str
    section: Tag
    image: Tag


@dataclass(frozen=True)
class OverviewHtmlSource:
    spec: ComponentSpec
    heading: Tag
    views: tuple[OverviewHtmlView, ...]


def _src_matches_key(src: str, image_key: str) -> bool:
    normalized_src = src.replace("\\", "/").lower()
    normalized_key = image_key.replace("\\", "/").lower()
    return (
        normalized_key in normalized_src
        or normalized_key.rsplit("/", 1)[-1] in normalized_src
    )


def _table_rows(table: Tag) -> list[list[Tag]]:
    rows: list[list[Tag]] = []
    for row in table.find_all("tr"):
        cells = [
            cell
            for cell in row.find_all("td", recursive=False)
            if isinstance(cell, Tag)
        ]
        if cells:
            rows.append(cells)
    return rows


def _cell_semantic(cell: Tag | None) -> dict[str, Any] | None:
    if cell is None or not cell.get_text(" ", strip=True):
        return None
    strong = cell.find("strong")
    if not isinstance(strong, Tag):
        return None
    label = strong.get_text(" ", strip=True)
    body: list[str] = []
    for paragraph in cell.find_all("p", recursive=False):
        if paragraph.find("strong") is strong:
            residual = paragraph.get_text(" ", strip=True)
            if residual != label:
                residual = residual.removeprefix(label).strip()
                if residual:
                    body.append(residual)
            continue
        text = paragraph.get_text(" ", strip=True)
        if text:
            body.append(text)
    return {"label": label, "body": body}


def _source_slots(view_id: str, section: Tag) -> dict[str, dict[str, Any]]:
    tables = section.find_all("table", recursive=False)
    if view_id == "front":
        if len(tables) < 2:
            return {}
        primary = _table_rows(tables[0])
        total_rows = _table_rows(tables[1])

        def at(row: int, column: int) -> dict[str, Any] | None:
            if row >= len(primary) or column >= len(primary[row]):
                return None
            return _cell_semantic(primary[row][column])

        left = [at(row, 0) for row in (0, 1, 3, 4, 5, 2)]
        right = [
            at(row, 1)
            for row in range(len(primary))
            if at(row, 1) is not None
        ]
        slots: dict[str, dict[str, Any]] = {}
        for index, value in enumerate(left):
            if value is not None:
                slots[f"front.left.{index}"] = value
        for index, value in enumerate(right):
            if value is not None:
                slots[f"front.right.{index}"] = value
        if total_rows and total_rows[0]:
            total = _cell_semantic(total_rows[0][0])
            if total is not None:
                slots["front.total.0"] = total
        return slots

    if view_id == "right":
        if not tables:
            return {}
        sequence = [
            value
            for row in _table_rows(tables[0])
            for cell in row
            if (value := _cell_semantic(cell)) is not None
        ]
        return {
            f"right.sequence.{index}": value
            for index, value in enumerate(sequence)
        }
    return {}


def _language_for_source(instance: Mapping[str, Any], source_path: Path) -> str:
    stem = source_path.stem.casefold()
    locales: set[str] = set()
    for view in instance["views"]:
        for mapping in view["composite_locales"]:
            if any(
                fnmatch.fnmatch(stem, str(pattern).casefold())
                for pattern in mapping["source_patterns"]
            ):
                locales.add(str(mapping["locale"]))
    if len(locales) != 1:
        raise ValueError(
            f"{source_path}: overview locale mapping must resolve once; got {sorted(locales)!r}"
        )
    return next(iter(locales))


def parse_overview_html(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    instance: Mapping[str, Any],
    error_type: type[Exception],
) -> OverviewHtmlSource:
    heading = soup.find("h1")
    if not isinstance(heading, Tag):
        raise error_type(f"{source_path}: product overview is missing its H1")
    html_views: list[OverviewHtmlView] = []
    semantic_views: list[dict[str, Any]] = []
    for instance_view in instance["views"]:
        view_id = str(instance_view["id"])
        image = next(
            (
                candidate
                for candidate in soup.find_all("img")
                if _src_matches_key(
                    str(candidate.get("src", "")), str(instance_view["image_key"])
                )
            ),
            None,
        )
        if not isinstance(image, Tag):
            raise error_type(
                f"{source_path}: product overview is missing governed image "
                f"{instance_view['image_key']}"
            )
        section = image.find_parent("section")
        if not isinstance(section, Tag):
            raise error_type(
                f"{source_path}: overview image is not contained by a section"
            )
        h2 = section.find("h2")
        if not isinstance(h2, Tag):
            raise error_type(f"{source_path}: {view_id} overview view is missing its H2")
        slots = _source_slots(view_id, section)
        callouts: list[dict[str, Any]] = []
        for binding in instance_view["callouts"]:
            source_slot = str(binding["source_slot"])
            semantic = slots.get(source_slot)
            if semantic is None:
                raise error_type(
                    f"{source_path}: product overview {view_id} is missing source slot "
                    f"{source_slot!r}"
                )
            callouts.append({"id": str(binding["id"]), **semantic})
        semantic_views.append(
            {
                "id": view_id,
                "title": h2.get_text(" ", strip=True),
                "image_ref": str(image.get("src") or ""),
                "alt": str(image.get("alt") or h2.get_text(" ", strip=True)),
                "callouts": callouts,
            }
        )
        html_views.append(OverviewHtmlView(view_id, section, image))
    try:
        spec = overview_component_spec(
            accessibility_label=heading.get_text(" ", strip=True),
            views=semantic_views,
            geometry_ref=str(instance["instance_id"]),
            source_ref=source_path.as_posix(),
            language=_language_for_source(instance, source_path),
        )
    except Exception as exc:
        raise error_type(f"{source_path}: {exc}") from exc
    return OverviewHtmlSource(spec=spec, heading=heading, views=tuple(html_views))


__all__ = ["OverviewHtmlSource", "OverviewHtmlView", "parse_overview_html"]
