"""Renderer-neutral warranty lead, section, and year-card instances."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from tools.component_specs.model import ComponentSlot, ComponentSpec, ComponentSpecError
from tools.component_specs.registry import load_component_registry, require_valid_component_spec
from tools.component_specs.theme import load_manual_theme, require_component_theme_roles


WARRANTY_LEAD_COMPONENT_ID = "HB-WARRANTY-LEAD"
WARRANTY_SECTION_COMPONENT_ID = "HB-WARRANTY-SECTION"
WARRANTY_YEARS_COMPONENT_ID = "HB-WARRANTY-YEARS"


def _active_contracts(
    registry: Mapping[str, Any] | None,
    theme: Mapping[str, Any] | None,
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    active_registry = registry or load_component_registry()
    return active_registry, theme or load_manual_theme(component_registry=active_registry)


def _finish(
    spec: ComponentSpec,
    *,
    registry: Mapping[str, Any],
    theme: Mapping[str, Any],
) -> ComponentSpec:
    require_valid_component_spec(spec, registry)
    return require_component_theme_roles(spec, theme)


def warranty_lead_component_spec(
    *,
    accessibility_label: str,
    lead_html: str,
    local_note_html: str,
    source_ref: str,
    language: str,
    metadata: Mapping[str, Any] | None = None,
    registry: Mapping[str, Any] | None = None,
    theme: Mapping[str, Any] | None = None,
) -> ComponentSpec:
    label = str(accessibility_label).strip()
    lead = str(lead_html).strip()
    note = str(local_note_html).strip()
    if not label or not lead or not note:
        raise ComponentSpecError(
            f"{WARRANTY_LEAD_COMPONENT_ID}: label, lead, and local note are required"
        )
    active_registry, active_theme = _active_contracts(registry, theme)
    return _finish(
        ComponentSpec(
            component_id=WARRANTY_LEAD_COMPONENT_ID,
            variant="intro-panel",
            source_ref=str(source_ref),
            language=str(language or "und"),
            slots=(
                ComponentSlot("accessibility_label", "inline_text", label),
                ComponentSlot("lead", "rich_text", lead),
                ComponentSlot("local_note", "rich_text", note),
            ),
            assets=(),
            token_roles=tuple(
                active_registry["components"][WARRANTY_LEAD_COMPONENT_ID]["token_roles"]
            ),
            metadata=dict(metadata or {}),
        ),
        registry=active_registry,
        theme=active_theme,
    )


def _normalize_blocks(blocks: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, block in enumerate(blocks, start=1):
        kind = str(block.get("kind") or "").strip()
        html = str(block.get("html") or "").strip()
        if kind == "paragraph":
            text = str(block.get("text") or "").strip()
            if not html or not text:
                raise ComponentSpecError(
                    f"{WARRANTY_SECTION_COMPONENT_ID}: paragraph {index} is empty"
                )
            normalized.append({"kind": kind, "html": html, "text": text})
            continue
        if kind == "list":
            items = block.get("items")
            if (
                not html
                or not isinstance(items, Sequence)
                or isinstance(items, (str, bytes))
                or not items
                or any(not str(item).strip() for item in items)
            ):
                raise ComponentSpecError(
                    f"{WARRANTY_SECTION_COMPONENT_ID}: list {index} is invalid"
                )
            normalized.append(
                {"kind": kind, "html": html, "items": [str(item).strip() for item in items]}
            )
            continue
        raise ComponentSpecError(
            f"{WARRANTY_SECTION_COMPONENT_ID}: unsupported block kind {kind!r}"
        )
    if not normalized:
        raise ComponentSpecError(f"{WARRANTY_SECTION_COMPONENT_ID}: body is required")
    return normalized


def warranty_section_component_spec(
    *,
    title: str,
    section_index: int,
    blocks: Sequence[Mapping[str, Any]],
    source_ref: str,
    language: str,
    metadata: Mapping[str, Any] | None = None,
    registry: Mapping[str, Any] | None = None,
    theme: Mapping[str, Any] | None = None,
) -> ComponentSpec:
    normalized_title = str(title).strip()
    if not normalized_title or section_index < 1:
        raise ComponentSpecError(
            f"{WARRANTY_SECTION_COMPONENT_ID}: title and positive section index are required"
        )
    active_registry, active_theme = _active_contracts(registry, theme)
    return _finish(
        ComponentSpec(
            component_id=WARRANTY_SECTION_COMPONENT_ID,
            variant="rounded-card",
            source_ref=str(source_ref),
            language=str(language or "und"),
            slots=(
                ComponentSlot("title", "inline_text", normalized_title),
                ComponentSlot("section_index", "block_index", section_index),
                ComponentSlot("blocks", "ordered_blocks", _normalize_blocks(blocks)),
            ),
            assets=(),
            token_roles=tuple(
                active_registry["components"][WARRANTY_SECTION_COMPONENT_ID]["token_roles"]
            ),
            metadata=dict(metadata or {}),
        ),
        registry=active_registry,
        theme=active_theme,
    )


def _normalize_periods(periods: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    if len(periods) < 1:
        raise ComponentSpecError(f"{WARRANTY_YEARS_COMPONENT_ID}: periods are required")
    normalized: list[dict[str, str]] = []
    for index, period in enumerate(periods, start=1):
        item = {
            key: str(period.get(key) or "").strip()
            for key in ("number", "unit", "label", "body_html", "body_text")
        }
        if any(not value for value in item.values()) or not item["number"].isdigit():
            raise ComponentSpecError(
                f"{WARRANTY_YEARS_COMPONENT_ID}: period {index} is invalid"
            )
        normalized.append(item)
    return normalized


def warranty_years_component_spec(
    *,
    title: str,
    periods: Sequence[Mapping[str, Any]],
    source_ref: str,
    language: str,
    metadata: Mapping[str, Any] | None = None,
    registry: Mapping[str, Any] | None = None,
    theme: Mapping[str, Any] | None = None,
) -> ComponentSpec:
    normalized_title = str(title).strip()
    if not normalized_title:
        raise ComponentSpecError(f"{WARRANTY_YEARS_COMPONENT_ID}: title is required")
    active_registry, active_theme = _active_contracts(registry, theme)
    return _finish(
        ComponentSpec(
            component_id=WARRANTY_YEARS_COMPONENT_ID,
            variant="numeric-badges",
            source_ref=str(source_ref),
            language=str(language or "und"),
            slots=(
                ComponentSlot("title", "inline_text", normalized_title),
                ComponentSlot("periods", "ordered_periods", _normalize_periods(periods)),
            ),
            assets=(),
            token_roles=tuple(
                active_registry["components"][WARRANTY_YEARS_COMPONENT_ID]["token_roles"]
            ),
            metadata=dict(metadata or {}),
        ),
        registry=active_registry,
        theme=active_theme,
    )


def warranty_semantic_projection(spec: ComponentSpec) -> dict[str, Any]:
    if spec.component_id == WARRANTY_LEAD_COMPONENT_ID:
        return {
            "accessibility_label": str(spec.slot("accessibility_label").content),
            "lead_html": str(spec.slot("lead").content),
            "local_note_html": str(spec.slot("local_note").content),
        }
    if spec.component_id == WARRANTY_SECTION_COMPONENT_ID:
        return {
            "title": str(spec.slot("title").content),
            "section_index": int(spec.slot("section_index").content),
            "blocks": deepcopy(spec.slot("blocks").content),
        }
    if spec.component_id == WARRANTY_YEARS_COMPONENT_ID:
        return {
            "title": str(spec.slot("title").content),
            "periods": deepcopy(spec.slot("periods").content),
        }
    raise ComponentSpecError(f"unsupported warranty component {spec.component_id!r}")


__all__ = [
    "WARRANTY_LEAD_COMPONENT_ID",
    "WARRANTY_SECTION_COMPONENT_ID",
    "WARRANTY_YEARS_COMPONENT_ID",
    "warranty_lead_component_spec",
    "warranty_section_component_spec",
    "warranty_semantic_projection",
    "warranty_years_component_spec",
]
