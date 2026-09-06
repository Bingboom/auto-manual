"""Renderer-neutral App download, inline-control, and add-device instances."""
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


APP_COMPONENT_ID = "HB-SPECIAL-APP"
APP_VARIANTS = frozenset({"download", "inline-control", "add-device"})
_DOWNLOAD_ROLES = ("store", "qr")


def _contracts(
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
    _validate_variant_shape(spec)
    return require_component_theme_roles(spec, theme)


def _normalized_rich_items(
    values: Sequence[Mapping[str, Any]],
    *,
    owner: str,
    roles: Sequence[str] | None = None,
) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for index, value in enumerate(values):
        if not isinstance(value, Mapping):
            raise ComponentSpecError(f"{owner}: item {index + 1} must be a mapping")
        role = str(value.get("role") or "").strip()
        html = str(value.get("html") or "").strip()
        text = str(value.get("text") or "").strip()
        if not role or not html or not text:
            raise ComponentSpecError(f"{owner}: item {index + 1} is incomplete")
        normalized.append({"role": role, "html": html, "text": text})
    if roles is not None and [item["role"] for item in normalized] != list(roles):
        raise ComponentSpecError(f"{owner}: roles must be {list(roles)!r}")
    if not normalized:
        raise ComponentSpecError(f"{owner}: at least one item is required")
    return normalized


def _base(
    *,
    variant: str,
    slots: Sequence[ComponentSlot],
    assets: Sequence[ComponentAsset],
    source_ref: str,
    language: str,
    metadata: Mapping[str, Any] | None,
    registry: Mapping[str, Any] | None,
    theme: Mapping[str, Any] | None,
) -> ComponentSpec:
    active_registry, active_theme = _contracts(registry, theme)
    return _finish(
        ComponentSpec(
            component_id=APP_COMPONENT_ID,
            variant=variant,
            source_ref=str(source_ref),
            language=str(language or "und"),
            slots=tuple(slots),
            assets=tuple(assets),
            token_roles=tuple(
                active_registry["components"][APP_COMPONENT_ID]["token_roles"]
            ),
            metadata=dict(metadata or {}),
        ),
        registry=active_registry,
        theme=active_theme,
    )


def app_download_component_spec(
    *,
    accessibility_label: str,
    columns: Sequence[Mapping[str, Any]],
    source_art_ref: str,
    store_art_ref: str,
    qr_art_ref: str,
    source_ref: str,
    language: str,
    metadata: Mapping[str, Any] | None = None,
    registry: Mapping[str, Any] | None = None,
    theme: Mapping[str, Any] | None = None,
) -> ComponentSpec:
    label = str(accessibility_label).strip()
    refs = [str(value).strip() for value in (source_art_ref, store_art_ref, qr_art_ref)]
    if not label or any(not value for value in refs):
        raise ComponentSpecError(
            f"{APP_COMPONENT_ID}: download label and three assets are required"
        )
    return _base(
        variant="download",
        slots=(
            ComponentSlot("accessibility_label", "inline_text", label),
            ComponentSlot(
                "columns",
                "ordered_columns",
                _normalized_rich_items(
                    columns,
                    owner=f"{APP_COMPONENT_ID}.download",
                    roles=_DOWNLOAD_ROLES,
                ),
            ),
        ),
        assets=(
            ComponentAsset("source_art", refs[0], "exact"),
            ComponentAsset("store_art", refs[1], "shared"),
            ComponentAsset("qr_art", refs[2], "shared"),
        ),
        source_ref=source_ref,
        language=language,
        metadata=metadata,
        registry=registry,
        theme=theme,
    )


def app_inline_control_component_spec(
    *,
    accessibility_label: str,
    paragraph_html: str,
    paragraph_text: str,
    source_ref: str,
    language: str,
    metadata: Mapping[str, Any] | None = None,
    registry: Mapping[str, Any] | None = None,
    theme: Mapping[str, Any] | None = None,
) -> ComponentSpec:
    label = str(accessibility_label).strip()
    html = str(paragraph_html).strip()
    text = str(paragraph_text).strip()
    if not label or not html or not text:
        raise ComponentSpecError(
            f"{APP_COMPONENT_ID}: inline control label and paragraph are required"
        )
    return _base(
        variant="inline-control",
        slots=(
            ComponentSlot("accessibility_label", "inline_text", label),
            ComponentSlot(
                "paragraph",
                "rich_text",
                {"html": html, "text": text},
            ),
        ),
        assets=(),
        source_ref=source_ref,
        language=language,
        metadata=metadata,
        registry=registry,
        theme=theme,
    )


def app_add_device_component_spec(
    *,
    accessibility_label: str,
    reference_id: str,
    labels: Sequence[Mapping[str, Any]],
    source_art_ref: str,
    phone_art_ref: str,
    control_art_ref: str,
    source_ref: str,
    language: str,
    metadata: Mapping[str, Any] | None = None,
    registry: Mapping[str, Any] | None = None,
    theme: Mapping[str, Any] | None = None,
) -> ComponentSpec:
    label = str(accessibility_label).strip()
    normalized_id = str(reference_id).strip()
    refs = [str(value).strip() for value in (source_art_ref, phone_art_ref, control_art_ref)]
    if not label or not normalized_id or any(not value for value in refs):
        raise ComponentSpecError(
            f"{APP_COMPONENT_ID}: add-device identity and three assets are required"
        )
    normalized_labels = _normalized_rich_items(
        labels,
        owner=f"{APP_COMPONENT_ID}.add-device",
    )
    if len(normalized_labels) != 3 or len({item["role"] for item in normalized_labels}) != 3:
        raise ComponentSpecError(
            f"{APP_COMPONENT_ID}: add-device requires three unique label roles"
        )
    return _base(
        variant="add-device",
        slots=(
            ComponentSlot("accessibility_label", "inline_text", label),
            ComponentSlot("reference_id", "inline_text", normalized_id),
            ComponentSlot("labels", "ordered_labels", normalized_labels),
        ),
        assets=(
            ComponentAsset("source_art", refs[0], "exact"),
            ComponentAsset("phone_art", refs[1], "shared"),
            ComponentAsset("control_art", refs[2], "shared"),
        ),
        source_ref=source_ref,
        language=language,
        metadata=metadata,
        registry=registry,
        theme=theme,
    )


def _roles(spec: ComponentSpec) -> tuple[set[str], set[str]]:
    return ({slot.role for slot in spec.slots}, {asset.role for asset in spec.assets})


def _validate_variant_shape(spec: ComponentSpec) -> None:
    if spec.component_id != APP_COMPONENT_ID or spec.variant not in APP_VARIANTS:
        raise ComponentSpecError(f"unsupported App component {spec.component_id}/{spec.variant}")
    slots, assets = _roles(spec)
    expected = {
        "download": (
            {"accessibility_label", "columns"},
            {"source_art", "store_art", "qr_art"},
        ),
        "inline-control": (
            {"accessibility_label", "paragraph"},
            set(),
        ),
        "add-device": (
            {"accessibility_label", "reference_id", "labels"},
            {"source_art", "phone_art", "control_art"},
        ),
    }[spec.variant]
    if (slots, assets) != expected:
        raise ComponentSpecError(
            f"{APP_COMPONENT_ID}.{spec.variant}: slots/assets do not match the variant"
        )


def app_semantic_projection(spec: ComponentSpec) -> dict[str, Any]:
    _validate_variant_shape(spec)
    payload: dict[str, Any] = {
        "variant": spec.variant,
        "accessibility_label": str(spec.slot("accessibility_label").content),
    }
    if spec.variant == "download":
        payload["columns"] = deepcopy(spec.slot("columns").content)
        payload["source_art"] = spec.assets[0].asset_ref
        payload["store_art"] = spec.assets[1].asset_ref
        payload["qr_art"] = spec.assets[2].asset_ref
    elif spec.variant == "inline-control":
        payload["paragraph"] = deepcopy(spec.slot("paragraph").content)
    else:
        payload["reference_id"] = str(spec.slot("reference_id").content)
        payload["labels"] = deepcopy(spec.slot("labels").content)
        payload["source_art"] = spec.assets[0].asset_ref
        payload["phone_art"] = spec.assets[1].asset_ref
        payload["control_art"] = spec.assets[2].asset_ref
    return payload


__all__ = [
    "APP_COMPONENT_ID",
    "APP_VARIANTS",
    "app_add_device_component_spec",
    "app_download_component_spec",
    "app_inline_control_component_spec",
    "app_semantic_projection",
]
