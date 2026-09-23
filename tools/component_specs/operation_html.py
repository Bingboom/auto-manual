"""Structure-first HTML source adapter for operation-panel ComponentSpecs."""
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, Mapping

from bs4 import BeautifulSoup, Tag

from tools.component_specs.operation import operation_component_spec

# Source `operation_panel_copy` blocks name the IDML panel layout; this maps a
# Web figure variant to the panel whose copy it may carry.
_PANEL_COPY_LAYOUTS = {"footer-overlay": "energy_saving"}
_BASE_ART_LIVE_COPY = "base-art-live-copy"


def _panel_mode_label(
    panel_copy: Sequence[Mapping[str, Any]],
    *,
    variant: str,
    source_path: Path,
    operation_id: str,
) -> str:
    """Return the source mode label for one base-art figure, if it declares one."""

    panel_layout = _PANEL_COPY_LAYOUTS.get(variant)
    if panel_layout is None:
        return ""
    matches = [
        entry
        for entry in panel_copy
        if str(entry.get("layout") or "").strip() == panel_layout
    ]
    if len(matches) > 1:
        raise ValueError(
            f"{source_path}: operation {operation_id!r} has {len(matches)} "
            f"{panel_layout!r} panel-copy blocks"
        )
    return str(matches[0].get("mode_label") or "").strip() if matches else ""


def _sibling(tag: Tag, *, previous: bool) -> Tag | None:
    candidate = tag.previous_sibling if previous else tag.next_sibling
    while candidate is not None:
        if isinstance(candidate, Tag):
            return candidate
        candidate = candidate.previous_sibling if previous else candidate.next_sibling
    return None


def _matches_image(image: Tag, image_key: str) -> bool:
    normalized = str(image.get("src") or "").replace("\\", "/").casefold()
    normalized_key = image_key.replace("\\", "/").casefold()
    return (
        normalized_key in normalized
        or normalized_key.rsplit("/", 1)[-1] in normalized
    )


def _part(line: Tag, role: str) -> dict[str, str]:
    return {
        "role": role,
        "html": line.decode_contents().strip(),
        "text": line.get_text(" ", strip=True),
    }


def parse_operation_components(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    config: Mapping[str, Any],
    language: str,
    panel_copy: Sequence[Mapping[str, Any]] = (),
) -> tuple[tuple[object, tuple[Tag, ...], Tag, tuple[Tag, ...]], ...]:
    """Return specs, carrier nodes, artwork, and semantic-only source nodes.

    ``panel_copy`` holds the page's ``operation_panel_copy`` source blocks, which
    HTML conversion drops. Only a base-art figure carries their copy, so every
    other figure keeps its frozen spec byte for byte.
    """

    parsed: list[tuple[object, tuple[Tag, ...], Tag, tuple[Tag, ...]]] = []
    for raw_figure in config.get("figures", []):
        if not isinstance(raw_figure, Mapping):
            raise ValueError(f"{source_path}: operation figure contract must be a mapping")
        operation_id = str(raw_figure.get("id") or "").strip()
        image_key = str(raw_figure.get("image_key") or "").strip()
        step_ids = [str(value) for value in raw_figure.get("step_ids", [])]
        images = [
            image for image in soup.find_all("img")
            if isinstance(image, Tag) and _matches_image(image, image_key)
        ]
        if len(images) != 1:
            raise ValueError(
                f"{source_path}: operation {operation_id!r} needs one artwork; "
                f"found {len(images)}"
            )
        image = images[0]
        line_block = _sibling(image, previous=False)
        if not isinstance(line_block, Tag) or "line-block" not in line_block.get("class", []):
            raise ValueError(
                f"{source_path}: operation {operation_id!r} artwork must be followed by a line block"
            )
        lines = [
            line for line in line_block.find_all(class_="line", recursive=False)
            if isinstance(line, Tag) and line.get_text(" ", strip=True)
        ]
        if len(lines) < len(step_ids):
            raise ValueError(
                f"{source_path}: operation {operation_id!r} has too few visible steps"
            )
        pair_mode = len(lines) >= len(step_ids) * 2 and all(
            isinstance(lines[index * 2].find("strong"), Tag)
            and lines[index * 2].get_text(" ", strip=True)
            == lines[index * 2].find("strong").get_text(" ", strip=True)
            for index in range(len(step_ids))
        )
        lines_per_step = 2 if pair_mode else 1
        steps = []
        for index, step_id in enumerate(step_ids):
            start = index * lines_per_step
            selected = lines[start : start + lines_per_step]
            roles = ("label", "instruction") if pair_mode else ("summary",)
            steps.append(
                {"id": step_id, "parts": [_part(line, role) for line, role in zip(selected, roles, strict=True)]}
            )
        supporting_count = int(raw_figure.get("capture_following_lines", 0))
        supporting_lines = lines[len(step_ids) * lines_per_step :]
        if supporting_count and not supporting_lines:
            supporting_block = _sibling(line_block, previous=False)
            if not isinstance(supporting_block, Tag) or "line-block" not in supporting_block.get(
                "class", []
            ):
                raise ValueError(
                    f"{source_path}: operation {operation_id!r} is missing supporting copy"
                )
            supporting_lines = [
                line
                for line in supporting_block.find_all(class_="line", recursive=False)
                if isinstance(line, Tag) and line.get_text(" ", strip=True)
            ]
        if len(supporting_lines) < supporting_count:
            raise ValueError(
                f"{source_path}: operation {operation_id!r} has too few supporting lines"
            )
        supporting = [
            line.decode_contents().strip()
            for line in supporting_lines[:supporting_count]
        ]
        prerequisite = ""
        owned: list[Tag] = []
        if raw_figure.get("capture_prerequisite"):
            candidate = _sibling(image, previous=True)
            if not isinstance(candidate, Tag) or candidate.name != "p":
                raise ValueError(
                    f"{source_path}: operation {operation_id!r} needs a prerequisite paragraph"
                )
            prerequisite = str(candidate)
            owned.append(candidate)
        owned.extend((image, line_block))
        variant = str(raw_figure.get("layout") or "")
        presentation_mode = str(raw_figure.get("presentation_mode") or "").strip()
        mode_label = (
            _panel_mode_label(
                panel_copy,
                variant=variant,
                source_path=source_path,
                operation_id=operation_id,
            )
            if presentation_mode == _BASE_ART_LIVE_COPY
            else ""
        )
        spec = operation_component_spec(
            operation_id=operation_id,
            accessibility_label=str(image.get("alt") or operation_id),
            layout=variant,
            steps=steps,
            prerequisite_html=prerequisite,
            supporting_copy=supporting,
            artwork_ref=str(image.get("src") or ""),
            source_ref=f"{source_path}#operation-{operation_id}",
            language=language,
            mode_label=mode_label,
            metadata={"presentation_mode": presentation_mode}
            if presentation_mode
            else None,
        )
        parsed.append(
            (spec, tuple(owned), image, tuple(supporting_lines[:supporting_count]))
        )
    return tuple(parsed)


__all__ = ["parse_operation_components"]
