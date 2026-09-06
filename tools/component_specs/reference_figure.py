"""Renderer-neutral governed reference figures and approved asset bindings."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import re
from typing import Any

from tools.component_specs.model import (
    ComponentAsset,
    ComponentSlot,
    ComponentSpec,
    ComponentSpecError,
)
from tools.component_specs.registry import load_component_registry, require_valid_component_spec
from tools.component_specs.theme import load_manual_theme, require_component_theme_roles


REFERENCE_FIGURE_COMPONENT_ID = "HB-SPECIAL-REFERENCE-FIGURE"
REFERENCE_FIGURE_VARIANTS = frozenset({"semantic-fallback", "approved-composite"})
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_CAPTION_MODES = frozenset({"none", "live", "embedded"})


def _normalize_captions(values: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for index, value in enumerate(values, start=1):
        if not isinstance(value, Mapping):
            raise ComponentSpecError(
                f"{REFERENCE_FIGURE_COMPONENT_ID}: caption {index} must be a mapping"
            )
        html = str(value.get("html") or "").strip()
        text = str(value.get("text") or "").strip()
        if not html or not text:
            raise ComponentSpecError(
                f"{REFERENCE_FIGURE_COMPONENT_ID}: caption {index} is incomplete"
            )
        result.append({"html": html, "text": text})
    return result


def _normalize_adjacent(value: Mapping[str, Any] | None) -> dict[str, str] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ComponentSpecError(
            f"{REFERENCE_FIGURE_COMPONENT_ID}: adjacent copy must be a mapping"
        )
    position = str(value.get("position") or "").strip()
    html = str(value.get("html") or "").strip()
    text = str(value.get("text") or "").strip()
    if position not in {"before", "after"} or not html or not text:
        raise ComponentSpecError(
            f"{REFERENCE_FIGURE_COMPONENT_ID}: adjacent copy is incomplete"
        )
    return {"position": position, "html": html, "text": text}


def _normalize_approved(value: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    required = {
        "asset_key",
        "asset_ref",
        "locale",
        "content_sha256",
        "source_fragment_sha256",
    }
    if set(value) != required:
        raise ComponentSpecError(
            f"{REFERENCE_FIGURE_COMPONENT_ID}: approved composite has invalid fields"
        )
    result = {key: str(value.get(key) or "").strip() for key in required}
    if any(not result[key] for key in required):
        raise ComponentSpecError(
            f"{REFERENCE_FIGURE_COMPONENT_ID}: approved composite is incomplete"
        )
    for key in ("content_sha256", "source_fragment_sha256"):
        result[key] = result[key].casefold()
        if not _SHA256.fullmatch(result[key]):
            raise ComponentSpecError(
                f"{REFERENCE_FIGURE_COMPONENT_ID}: approved {key} is invalid"
            )
    return result


def reference_figure_component_spec(
    *,
    reference_id: str,
    accessibility_label: str,
    caption_mode: str,
    captions: Sequence[Mapping[str, Any]],
    adjacent_copy: Mapping[str, Any] | None,
    source_art_ref: str,
    source_art_locale_policy: str,
    source_fragment_sha256: str,
    source_ref: str,
    language: str,
    image_key: str,
    web_replace_key: str = "",
    caption_layout: str = "equal",
    approved_composite: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
    registry: Mapping[str, Any] | None = None,
    theme: Mapping[str, Any] | None = None,
) -> ComponentSpec:
    normalized_id = str(reference_id).strip()
    label = str(accessibility_label).strip()
    mode = str(caption_mode).strip()
    source_art = str(source_art_ref).strip()
    image_identity = str(image_key).strip()
    source_hash = str(source_fragment_sha256).strip().casefold()
    layout = str(caption_layout).strip()
    if (
        not normalized_id
        or not label
        or mode not in _CAPTION_MODES
        or not source_art
        or not image_identity
        or not _SHA256.fullmatch(source_hash)
        or not layout
    ):
        raise ComponentSpecError(
            f"{REFERENCE_FIGURE_COMPONENT_ID}: identity, art, caption mode, and hash are required"
        )
    normalized_captions = _normalize_captions(captions)
    if mode == "live" and not normalized_captions:
        raise ComponentSpecError(
            f"{REFERENCE_FIGURE_COMPONENT_ID}: live captions cannot be empty"
        )
    if mode != "live" and normalized_captions:
        raise ComponentSpecError(
            f"{REFERENCE_FIGURE_COMPONENT_ID}: only live caption mode accepts captions"
        )
    adjacent = _normalize_adjacent(adjacent_copy)
    approved = _normalize_approved(approved_composite)
    if approved is not None and approved["source_fragment_sha256"] != source_hash:
        raise ComponentSpecError(
            f"{REFERENCE_FIGURE_COMPONENT_ID}: approved source-fragment hash disagrees"
        )
    active_registry = registry or load_component_registry()
    active_theme = theme or load_manual_theme(component_registry=active_registry)
    slots = [
        ComponentSlot("reference_id", "inline_text", normalized_id),
        ComponentSlot("accessibility_label", "inline_text", label),
        ComponentSlot("caption_mode", "inline_text", mode),
        ComponentSlot("caption_layout", "inline_text", layout),
    ]
    if normalized_captions:
        slots.append(ComponentSlot("captions", "ordered_labels", normalized_captions))
    if adjacent is not None:
        slots.append(ComponentSlot("adjacent_copy", "rich_text", adjacent))
    assets = [ComponentAsset("source_art", source_art, source_art_locale_policy)]
    merged_metadata = dict(metadata or {})
    merged_metadata.update(
        {
            "image_key": image_identity,
            "web_replace_key": str(web_replace_key).strip(),
            "source_fragment_sha256": source_hash,
        }
    )
    if approved is not None:
        assets.append(
            ComponentAsset(
                "approved_composite",
                approved.pop("asset_ref"),
                "shared" if approved["locale"].casefold() == "shared" else "exact",
            )
        )
        merged_metadata["approved_composite"] = approved
    spec = ComponentSpec(
        component_id=REFERENCE_FIGURE_COMPONENT_ID,
        variant="approved-composite" if approved is not None else "semantic-fallback",
        source_ref=str(source_ref),
        language=str(language or "und"),
        slots=tuple(slots),
        assets=tuple(assets),
        token_roles=tuple(
            active_registry["components"][REFERENCE_FIGURE_COMPONENT_ID]["token_roles"]
        ),
        metadata=merged_metadata,
    )
    require_valid_component_spec(spec, active_registry)
    _validate_variant_shape(spec)
    return require_component_theme_roles(spec, active_theme)


def _validate_variant_shape(spec: ComponentSpec) -> None:
    if (
        spec.component_id != REFERENCE_FIGURE_COMPONENT_ID
        or spec.variant not in REFERENCE_FIGURE_VARIANTS
    ):
        raise ComponentSpecError(
            f"unsupported reference figure {spec.component_id}/{spec.variant}"
        )
    roles = {asset.role for asset in spec.assets}
    expected = (
        {"source_art", "approved_composite"}
        if spec.variant == "approved-composite"
        else {"source_art"}
    )
    approved = spec.metadata.get("approved_composite")
    if roles != expected or (spec.variant == "approved-composite") != isinstance(
        approved, Mapping
    ):
        raise ComponentSpecError(
            f"{REFERENCE_FIGURE_COMPONENT_ID}: approved binding does not match variant"
        )
    source_hash = str(spec.metadata.get("source_fragment_sha256") or "").casefold()
    if not _SHA256.fullmatch(source_hash):
        raise ComponentSpecError(
            f"{REFERENCE_FIGURE_COMPONENT_ID}: source_fragment_sha256 is invalid"
        )
    if isinstance(approved, Mapping):
        if str(approved.get("source_fragment_sha256") or "").casefold() != source_hash:
            raise ComponentSpecError(
                f"{REFERENCE_FIGURE_COMPONENT_ID}: approved source hash disagrees"
            )


def reference_figure_semantic_projection(spec: ComponentSpec) -> dict[str, Any]:
    _validate_variant_shape(spec)
    captions = next(
        (slot.content for slot in spec.slots if slot.role == "captions"),
        [],
    )
    adjacent = next(
        (slot.content for slot in spec.slots if slot.role == "adjacent_copy"),
        None,
    )
    payload: dict[str, Any] = {
        "reference_id": str(spec.slot("reference_id").content),
        "accessibility_label": str(spec.slot("accessibility_label").content),
        "caption_mode": str(spec.slot("caption_mode").content),
        "caption_layout": str(spec.slot("caption_layout").content),
        "captions": deepcopy(list(captions)),
        "adjacent_copy": deepcopy(adjacent),
        "source_art": spec.assets[0].asset_ref,
        "source_art_locale_policy": spec.assets[0].locale_policy,
        "image_key": str(spec.metadata["image_key"]),
        "web_replace_key": str(spec.metadata.get("web_replace_key") or ""),
        "source_fragment_sha256": str(spec.metadata["source_fragment_sha256"]),
        "approved_composite": deepcopy(spec.metadata.get("approved_composite")),
    }
    if spec.variant == "approved-composite":
        payload["approved_composite"]["asset_ref"] = spec.assets[1].asset_ref
        payload["approved_composite"]["locale_policy"] = spec.assets[1].locale_policy
    return payload


__all__ = [
    "REFERENCE_FIGURE_COMPONENT_ID",
    "REFERENCE_FIGURE_VARIANTS",
    "reference_figure_component_spec",
    "reference_figure_semantic_projection",
]
