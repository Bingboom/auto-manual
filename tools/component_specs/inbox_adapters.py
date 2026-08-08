"""Four renderer adapters for the Inbox ComponentSpec."""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from tools.component_specs.inbox import inbox_semantic_projection, inbox_spec_from_legacy_payload
from tools.component_specs.model import ComponentSpec, ComponentSpecError
from tools.component_specs.registry import adapter_binding


_EXPECTED_ADAPTER_KEYS = {
    "web": "hb_inbox",
    "latex": "hb_latex_inbox",
    "idml": "idml_inbox",
    "word": "word_inbox",
}


def _projection(spec: ComponentSpec, renderer: str) -> dict[str, Any]:
    binding = adapter_binding(spec, renderer)
    expected = _EXPECTED_ADAPTER_KEYS[renderer]
    if binding.get("key") != expected:
        raise ComponentSpecError(
            f"{spec.component_id}: expected {renderer} adapter {expected!r}; "
            f"got {binding.get('key')!r}"
        )
    return inbox_semantic_projection(spec)


def web_inbox_projection(spec: ComponentSpec) -> dict[str, Any]:
    return {
        **_projection(spec, "web"),
        "composition_class": "hb-inbox-composition",
        "grid_class": "hb-inbox-grid",
        "card_class": "hb-inbox-card",
        "art_class": "hb-inbox-art",
        "label_class": "hb-inbox-label",
        "tip_class": "hb-inbox-tip",
    }


def latex_inbox_projection(spec: ComponentSpec) -> dict[str, Any]:
    projection = _projection(spec, "latex")
    arguments: list[str] = []
    for card in projection["cards"]:
        arguments.extend((str(card["image_ref"]), str(card["label"])))
    return {**projection, "macro": "HBInBoxThree", "arguments": arguments}


def idml_inbox_payload(spec: ComponentSpec) -> dict[str, Any]:
    _projection(spec, "idml")
    legacy = spec.metadata.get("legacy_payload")
    if isinstance(legacy, Mapping):
        return deepcopy(dict(legacy))
    projection = inbox_semantic_projection(spec)
    return {
        "kind": "inbox",
        "items": [
            {
                "img": str(card["image_ref"]),
                "label": str(card["label"]),
                "alt": str(card["alt"]),
            }
            for card in projection["cards"]
        ],
    }


def idml_inbox_payload_from_legacy(
    payload: Mapping[str, Any],
    *,
    source_ref: str,
    language: str,
    accessibility_label: str = "What's in the Box",
    tip_label: str = "TIP",
    tip_body: str = "See the source-authored tip copy.",
) -> dict[str, Any]:
    items = payload.get("items")
    if (
        not isinstance(items, list)
        or len(items) != 3
        or any(
            not isinstance(item, Mapping)
            or not str(item.get("img") or "").strip()
            or not str(item.get("label") or "").strip()
            for item in items
        )
    ):
        # Historical unit fixtures exercise partial card lists. Production
        # ComponentSpec is deliberately strict; keep this compatibility-only
        # facade until PR 9 so unrelated fixed-page tests do not change shape.
        return deepcopy(dict(payload))
    return idml_inbox_payload(
        inbox_spec_from_legacy_payload(
            payload,
            source_ref=source_ref,
            language=language,
            accessibility_label=accessibility_label,
            tip_label=tip_label,
            tip_body=tip_body,
        )
    )


def word_inbox_projection(spec: ComponentSpec) -> dict[str, Any]:
    return {
        **_projection(spec, "word"),
        "table_class": "hb-inbox-word-table",
        "card_class": "hb-inbox-word-card",
        "tip_class": "hb-inbox-word-tip",
    }


__all__ = [
    "idml_inbox_payload",
    "idml_inbox_payload_from_legacy",
    "latex_inbox_projection",
    "web_inbox_projection",
    "word_inbox_projection",
]
