"""Renderer-neutral LCD, troubleshooting, and symbol table instances."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from tools.component_specs.model import (
    ComponentAsset,
    ComponentSlot,
    ComponentSpec,
    ComponentSpecError,
)
from tools.component_specs.registry import load_component_registry, require_valid_component_spec
from tools.component_specs.theme import load_manual_theme, require_component_theme_roles


LCD_ICON_COMPONENT_ID = "HB-TABLE-LCD-ICON"
TROUBLESHOOTING_COMPONENT_ID = "HB-TABLE-TROUBLESHOOTING"
SYMBOL_SIGNAL_COMPONENT_ID = "HB-TABLE-SYMBOL-SIGNAL"
SYMBOL_ICON_COMPONENT_ID = "HB-TABLE-SYMBOL-ICON"


def _contracts(
    registry: Mapping[str, Any] | None,
    theme: Mapping[str, Any] | None,
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    active_registry = registry or load_component_registry()
    return active_registry, theme or load_manual_theme(component_registry=active_registry)


def _finish(
    component_id: str,
    variant: str,
    slots: tuple[ComponentSlot, ...],
    assets: tuple[ComponentAsset, ...],
    *,
    source_ref: str,
    language: str,
    metadata: Mapping[str, Any] | None,
    registry: Mapping[str, Any] | None,
    theme: Mapping[str, Any] | None,
) -> ComponentSpec:
    active_registry, active_theme = _contracts(registry, theme)
    spec = ComponentSpec(
        component_id=component_id,
        variant=variant,
        source_ref=str(source_ref),
        language=str(language or "und"),
        slots=slots,
        assets=assets,
        token_roles=tuple(active_registry["components"][component_id]["token_roles"]),
        metadata=dict(metadata or {}),
    )
    require_valid_component_spec(spec, active_registry)
    return require_component_theme_roles(spec, active_theme)


def _text_pair(raw: Mapping[str, Any], key: str, component_id: str) -> dict[str, str]:
    html = str(raw.get(f"{key}_html") or "").strip()
    text = str(raw.get(f"{key}_text") or "").strip()
    if not html or not text:
        raise ComponentSpecError(f"{component_id}: {key} HTML and text are required")
    return {f"{key}_html": html, f"{key}_text": text}


def _headers(values: Sequence[Mapping[str, Any]], *, count: int, component_id: str) -> list[dict[str, str]]:
    if len(values) != count:
        raise ComponentSpecError(f"{component_id}: exactly {count} headers are required")
    return [_text_pair(value, "content", component_id) for value in values]


def lcd_icon_component_spec(
    *,
    accessibility_label: str,
    rows: Sequence[Mapping[str, Any]],
    icon_refs: Sequence[str],
    source_ref: str,
    language: str,
    icon_locale_policy: str = "shared",
    metadata: Mapping[str, Any] | None = None,
    registry: Mapping[str, Any] | None = None,
    theme: Mapping[str, Any] | None = None,
) -> ComponentSpec:
    label = str(accessibility_label).strip()
    if not label or not rows or len(rows) != len(icon_refs):
        raise ComponentSpecError(
            f"{LCD_ICON_COMPONENT_ID}: label and one icon per row are required"
        )
    normalized = []
    for index, raw in enumerate(rows):
        if not isinstance(raw, Mapping) or int(raw.get("asset_index", -1)) != index:
            raise ComponentSpecError(
                f"{LCD_ICON_COMPONENT_ID}: row {index + 1} asset order is invalid"
            )
        icon_alt = str(raw.get("icon_alt") or "").strip()
        if not icon_alt:
            raise ComponentSpecError(
                f"{LCD_ICON_COMPONENT_ID}: row {index + 1} icon alt is required"
            )
        normalized.append(
            {
                **_text_pair(raw, "number", LCD_ICON_COMPONENT_ID),
                **_text_pair(raw, "name", LCD_ICON_COMPONENT_ID),
                **_text_pair(raw, "description", LCD_ICON_COMPONENT_ID),
                "icon_alt": icon_alt,
                "asset_index": index,
            }
        )
    assets = tuple(
        ComponentAsset("icons", str(ref).strip(), icon_locale_policy)
        for ref in icon_refs
    )
    if any(not asset.asset_ref for asset in assets):
        raise ComponentSpecError(f"{LCD_ICON_COMPONENT_ID}: icon refs must be non-empty")
    return _finish(
        LCD_ICON_COMPONENT_ID,
        "icon-catalog",
        (
            ComponentSlot("accessibility_label", "inline_text", label),
            ComponentSlot("rows", "ordered_rows", normalized),
        ),
        assets,
        source_ref=source_ref,
        language=language,
        metadata=metadata,
        registry=registry,
        theme=theme,
    )


def troubleshooting_component_spec(
    *,
    headers: Sequence[Mapping[str, Any]],
    rows: Sequence[Mapping[str, Any]],
    source_ref: str,
    language: str,
    metadata: Mapping[str, Any] | None = None,
    registry: Mapping[str, Any] | None = None,
    theme: Mapping[str, Any] | None = None,
) -> ComponentSpec:
    normalized_rows = []
    for raw in rows:
        normalized_rows.append(
            {
                **_text_pair(raw, "code", TROUBLESHOOTING_COMPONENT_ID),
                **_text_pair(raw, "measures", TROUBLESHOOTING_COMPONENT_ID),
            }
        )
    if not normalized_rows:
        raise ComponentSpecError(f"{TROUBLESHOOTING_COMPONENT_ID}: rows are required")
    return _finish(
        TROUBLESHOOTING_COMPONENT_ID,
        "two-column",
        (
            ComponentSlot(
                "headers",
                "ordered_headers",
                _headers(headers, count=2, component_id=TROUBLESHOOTING_COMPONENT_ID),
            ),
            ComponentSlot("rows", "ordered_rows", normalized_rows),
        ),
        (),
        source_ref=source_ref,
        language=language,
        metadata=metadata,
        registry=registry,
        theme=theme,
    )


def symbol_signal_component_spec(
    *,
    accessibility_label: str,
    headers: Sequence[Mapping[str, Any]],
    rows: Sequence[Mapping[str, Any]],
    source_ref: str,
    language: str,
    metadata: Mapping[str, Any] | None = None,
    registry: Mapping[str, Any] | None = None,
    theme: Mapping[str, Any] | None = None,
) -> ComponentSpec:
    normalized_rows = []
    for raw in rows:
        label = str(raw.get("label") or "").strip()
        if not label:
            raise ComponentSpecError(f"{SYMBOL_SIGNAL_COMPONENT_ID}: label is required")
        normalized_rows.append(
            {"label": label, **_text_pair(raw, "meaning", SYMBOL_SIGNAL_COMPONENT_ID)}
        )
    if not normalized_rows:
        raise ComponentSpecError(f"{SYMBOL_SIGNAL_COMPONENT_ID}: rows are required")
    return _finish(
        SYMBOL_SIGNAL_COMPONENT_ID,
        "localized-badges",
        (
            ComponentSlot("accessibility_label", "inline_text", str(accessibility_label).strip()),
            ComponentSlot(
                "headers",
                "ordered_headers",
                _headers(headers, count=2, component_id=SYMBOL_SIGNAL_COMPONENT_ID),
            ),
            ComponentSlot("rows", "ordered_rows", normalized_rows),
        ),
        (),
        source_ref=source_ref,
        language=language,
        metadata=metadata,
        registry=registry,
        theme=theme,
    )


def symbol_icon_component_spec(
    *,
    accessibility_label: str,
    headers: Sequence[Mapping[str, Any]],
    panels: Sequence[Sequence[Mapping[str, Any]]],
    icon_refs: Sequence[str],
    source_ref: str,
    language: str,
    icon_locale_policy: str = "shared",
    metadata: Mapping[str, Any] | None = None,
    registry: Mapping[str, Any] | None = None,
    theme: Mapping[str, Any] | None = None,
) -> ComponentSpec:
    if len(panels) != 2 or any(not panel for panel in panels):
        raise ComponentSpecError(f"{SYMBOL_ICON_COMPONENT_ID}: two non-empty panels are required")
    normalized_panels = []
    seen_indices: set[int] = set()
    for panel in panels:
        normalized_panel = []
        for raw in panel:
            index = int(raw.get("asset_index", -1))
            alt = str(raw.get("icon_alt") or "").strip()
            if index < 0 or index >= len(icon_refs) or index in seen_indices or not alt:
                raise ComponentSpecError(f"{SYMBOL_ICON_COMPONENT_ID}: icon binding is invalid")
            seen_indices.add(index)
            normalized_panel.append(
                {
                    "asset_index": index,
                    "icon_alt": alt,
                    **_text_pair(raw, "meaning", SYMBOL_ICON_COMPONENT_ID),
                }
            )
        normalized_panels.append(normalized_panel)
    if seen_indices != set(range(len(icon_refs))):
        raise ComponentSpecError(f"{SYMBOL_ICON_COMPONENT_ID}: icon bindings must be complete")
    assets = tuple(
        ComponentAsset("icons", str(ref).strip(), icon_locale_policy)
        for ref in icon_refs
    )
    return _finish(
        SYMBOL_ICON_COMPONENT_ID,
        "two-panel-responsive",
        (
            ComponentSlot("accessibility_label", "inline_text", str(accessibility_label).strip()),
            ComponentSlot(
                "headers",
                "ordered_headers",
                _headers(headers, count=4, component_id=SYMBOL_ICON_COMPONENT_ID),
            ),
            ComponentSlot("panels", "ordered_panels", normalized_panels),
        ),
        assets,
        source_ref=source_ref,
        language=language,
        metadata=metadata,
        registry=registry,
        theme=theme,
    )


def manual_table_semantic_projection(spec: ComponentSpec) -> dict[str, Any]:
    values = {slot.role: deepcopy(slot.content) for slot in spec.slots}
    values["assets"] = [asset.asset_ref for asset in spec.assets]
    return values


__all__ = [
    "LCD_ICON_COMPONENT_ID",
    "SYMBOL_ICON_COMPONENT_ID",
    "SYMBOL_SIGNAL_COMPONENT_ID",
    "TROUBLESHOOTING_COMPONENT_ID",
    "lcd_icon_component_spec",
    "manual_table_semantic_projection",
    "symbol_icon_component_spec",
    "symbol_signal_component_spec",
    "troubleshooting_component_spec",
]
