"""Renderer-neutral What's In The Box composition."""
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


COMPONENT_ID = "HB-SPECIAL-INBOX"
VARIANT = "three-card-responsive"
CARD_ASSET_ROLES = ("card_1_art", "card_2_art", "card_3_art")


def _normalize_card(
    card: Mapping[str, Any],
    *,
    number: int,
    asset_role: str,
) -> tuple[dict[str, Any], ComponentAsset]:
    image_ref = str(card.get("image_ref") or card.get("img") or "").strip()
    label = str(card.get("label") or "").strip()
    alt = str(card.get("alt") or label).strip()
    if not image_ref:
        raise ComponentSpecError(f"{COMPONENT_ID}: card {number} image is required")
    if not label:
        raise ComponentSpecError(f"{COMPONENT_ID}: card {number} label is required")
    if not alt:
        raise ComponentSpecError(f"{COMPONENT_ID}: card {number} alt is required")
    return (
        {
            "number": number,
            "image_asset_role": asset_role,
            "alt": alt,
            "label": label,
        },
        ComponentAsset(
            role=asset_role,
            asset_ref=image_ref,
            locale_policy="shared",
        ),
    )


def inbox_component_spec(
    *,
    accessibility_label: str,
    cards: Sequence[Mapping[str, Any]],
    tip_label: str,
    tip_body: str,
    source_ref: str,
    language: str,
    metadata: Mapping[str, Any] | None = None,
    registry: Mapping[str, Any] | None = None,
    theme: Mapping[str, Any] | None = None,
) -> ComponentSpec:
    if len(cards) != 3:
        raise ComponentSpecError(f"{COMPONENT_ID}: exactly three cards are required")
    label = str(accessibility_label).strip()
    normalized_tip_label = str(tip_label).strip()
    normalized_tip_body = str(tip_body).strip()
    if not label:
        raise ComponentSpecError(f"{COMPONENT_ID}: accessibility label is required")
    if not normalized_tip_label or not normalized_tip_body:
        raise ComponentSpecError(f"{COMPONENT_ID}: tip label and body are required")

    normalized_cards: list[dict[str, Any]] = []
    assets: list[ComponentAsset] = []
    for number, (card, asset_role) in enumerate(
        zip(cards, CARD_ASSET_ROLES, strict=True),
        start=1,
    ):
        normalized_card, asset = _normalize_card(
            card,
            number=number,
            asset_role=asset_role,
        )
        normalized_cards.append(normalized_card)
        assets.append(asset)

    active_registry = registry or load_component_registry()
    active_theme = theme or load_manual_theme(component_registry=active_registry)
    spec = ComponentSpec(
        component_id=COMPONENT_ID,
        variant=VARIANT,
        source_ref=str(source_ref),
        language=str(language or "und"),
        slots=(
            ComponentSlot("accessibility_label", "inline_text", label),
            ComponentSlot("cards", "ordered_cards", normalized_cards),
            ComponentSlot("tip_label", "inline_text", normalized_tip_label),
            ComponentSlot("tip_body", "rich_text", normalized_tip_body),
        ),
        assets=tuple(assets),
        token_roles=tuple(active_registry["components"][COMPONENT_ID]["token_roles"]),
        metadata=dict(metadata or {}),
    )
    require_valid_component_spec(spec, active_registry)
    return require_component_theme_roles(spec, active_theme)


def inbox_spec_from_payload(
    payload: Mapping[str, Any],
    *,
    source_ref: str,
    language: str,
    accessibility_label: str,
    tip_label: str,
    tip_body: str,
    registry: Mapping[str, Any] | None = None,
    theme: Mapping[str, Any] | None = None,
) -> ComponentSpec:
    """Combine a typed inbox payload with its source-authored H1 and tip."""
    if str(payload.get("kind") or "") != "inbox":
        raise ComponentSpecError(f"{COMPONENT_ID}: payload kind must be 'inbox'")
    items = payload.get("items")
    if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
        raise ComponentSpecError(f"{COMPONENT_ID}: legacy items must be a list")
    cards: list[dict[str, str]] = []
    for item in items:
        if not isinstance(item, Mapping):
            raise ComponentSpecError(f"{COMPONENT_ID}: legacy item must be a mapping")
        label = str(item.get("label") or "").strip()
        cards.append(
            {
                "image_ref": str(item.get("img") or ""),
                "label": label,
                "alt": str(item.get("alt") or label),
            }
        )
    return inbox_component_spec(
        accessibility_label=accessibility_label,
        cards=cards,
        tip_label=tip_label,
        tip_body=tip_body,
        source_ref=source_ref,
        language=language,
        registry=registry,
        theme=theme,
    )


def inbox_semantic_projection(spec: ComponentSpec) -> dict[str, Any]:
    cards = deepcopy(spec.slot("cards").content)
    assets = {asset.role: asset.asset_ref for asset in spec.assets}
    for card in cards:
        card["image_ref"] = assets[card["image_asset_role"]]
    return {
        "accessibility_label": str(spec.slot("accessibility_label").content),
        "cards": cards,
        "tip_label": str(spec.slot("tip_label").content),
        "tip_body": str(spec.slot("tip_body").content),
    }


__all__ = [
    "CARD_ASSET_ROLES",
    "COMPONENT_ID",
    "VARIANT",
    "inbox_component_spec",
    "inbox_semantic_projection",
    "inbox_spec_from_payload",
]
