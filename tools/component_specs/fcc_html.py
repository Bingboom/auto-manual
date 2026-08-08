"""Parse governed FCC HTML into one renderer-neutral ComponentSpec."""
from __future__ import annotations

from dataclasses import dataclass
import fnmatch
from pathlib import Path
from typing import Any, Mapping

from bs4 import BeautifulSoup, Tag

from tools.component_specs.fcc import fcc_blocks_from_text, fcc_component_spec
from tools.component_specs.model import ComponentSpec


@dataclass(frozen=True)
class FccHtmlSource:
    spec: ComponentSpec
    heading: Tag
    consumed_nodes: tuple[Tag, ...]


def _next_tag_sibling(tag: Tag) -> Tag | None:
    sibling = tag.next_sibling
    while sibling is not None:
        if isinstance(sibling, Tag):
            return sibling
        sibling = sibling.next_sibling
    return None


def _matches_source(source_path: Path, patterns: list[str]) -> bool:
    stem = source_path.stem.lower()
    return any(fnmatch.fnmatch(stem, pattern.lower()) for pattern in patterns)


def _right_column_rule(
    config: Mapping[str, Any], source_path: Path
) -> tuple[str | None, str]:
    for override in config["right_column_markers"]:
        if _matches_source(
            source_path,
            [str(pattern) for pattern in override["source_patterns"]],
        ):
            return str(override["marker"]), str(override.get("language") or "und")
    return None, "und"


def _opening_lines(opening: Tag) -> list[str]:
    lines = [
        line.get_text(" ", strip=True)
        for line in opening.find_all(class_="line", recursive=False)
        if isinstance(line, Tag) and line.get_text(" ", strip=True)
    ]
    return lines or [opening.get_text(" ", strip=True)]


def _copy_parts(block: Tag) -> list[str]:
    if "line-block" in block.get("class", []):
        return [
            line.get_text(" ", strip=True)
            for line in block.find_all(class_="line", recursive=False)
            if isinstance(line, Tag) and line.get_text(" ", strip=True)
        ]
    # Historical FR source contains literal RST line-block markers inside one
    # paragraph. Treat them as semantic paragraph boundaries instead of copy.
    return [part.strip() for part in block.get_text(" ", strip=True).split("|") if part.strip()]


def _split_at_marker(
    parts: list[str], marker: str | None
) -> tuple[list[str], list[str]]:
    if not marker:
        return parts, []
    left: list[str] = []
    right: list[str] = []
    in_right = False
    for part in parts:
        marker_index = part.find(marker)
        if marker_index >= 0 and not in_right:
            prefix = part[:marker_index].strip()
            suffix = part[marker_index:].strip()
            if prefix:
                left.append(prefix)
            if suffix:
                right.append(suffix)
            in_right = True
        elif in_right:
            right.append(part)
        else:
            left.append(part)
    return left, right


def _blocks(parts: list[str]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for part in parts:
        blocks.extend(fcc_blocks_from_text(part))
    return blocks


def parse_fcc_html(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    config: Mapping[str, Any],
    error_type: type[Exception],
) -> FccHtmlSource:
    heading = soup.find("h1")
    if not isinstance(heading, Tag) or heading.get_text(" ", strip=True).casefold() != "fcc":
        raise error_type(f"{source_path}: FCC page is missing its H1")

    opening = _next_tag_sibling(heading)
    if not isinstance(opening, Tag) or "line-block" not in opening.get("class", []):
        raise error_type(f"{source_path}: FCC page is missing its opening line block")

    copy_nodes: list[Tag] = []
    sibling = _next_tag_sibling(opening)
    while isinstance(sibling, Tag) and sibling.name != "ul":
        if sibling.name not in {"p", "div"}:
            raise error_type(
                f"{source_path}: FCC pre-list copy must remain paragraph-based"
            )
        copy_nodes.append(sibling)
        sibling = _next_tag_sibling(sibling)
    if not copy_nodes or not isinstance(sibling, Tag) or sibling.name != "ul":
        raise error_type(f"{source_path}: FCC page is missing its body or measure list")
    bullet_node = sibling

    trailing: list[Tag] = []
    sibling = _next_tag_sibling(bullet_node)
    while isinstance(sibling, Tag):
        if sibling.name != "p":
            raise error_type(
                f"{source_path}: FCC trailing content must remain paragraph-based"
            )
        trailing.append(sibling)
        sibling = _next_tag_sibling(sibling)
    if not trailing:
        raise error_type(f"{source_path}: FCC page is missing modification copy")

    marker, language = _right_column_rule(config, source_path)
    copy_parts = [part for node in copy_nodes for part in _copy_parts(node)]
    left_parts, right_parts = _split_at_marker(copy_parts, marker)
    if not left_parts or not right_parts:
        raise error_type(
            f"{source_path}: FCC body is missing its governed right-column marker"
        )
    list_items = [
        item.get_text(" ", strip=True)
        for item in bullet_node.find_all("li", recursive=False)
        if item.get_text(" ", strip=True)
    ]
    if not list_items:
        raise error_type(f"{source_path}: FCC corrective-measure list is empty")
    right_blocks = _blocks(right_parts)
    right_blocks.append({"kind": "list", "items": list_items})
    right_blocks.extend(
        fcc_blocks_from_text(
            " ".join(node.get_text(" ", strip=True) for node in trailing)
        )
    )
    try:
        spec = fcc_component_spec(
            accessibility_label=heading.get_text(" ", strip=True),
            opening_copy=_opening_lines(opening),
            left_blocks=_blocks(left_parts),
            right_blocks=right_blocks,
            source_ref=source_path.as_posix(),
            language=language,
            mark_asset_ref=str(config["mark_asset_ref"]),
        )
    except Exception as exc:
        raise error_type(f"{source_path}: {exc}") from exc
    return FccHtmlSource(
        spec=spec,
        heading=heading,
        consumed_nodes=(opening, *copy_nodes, bullet_node, *trailing),
    )


__all__ = ["FccHtmlSource", "parse_fcc_html"]
