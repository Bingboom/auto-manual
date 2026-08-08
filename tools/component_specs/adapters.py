"""Renderer adapter dispatch for the Callout ComponentSpec pilot."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from tools.component_specs.callout import callout_spec_from_legacy_notice
from tools.component_specs.model import ComponentSpec, ComponentSpecError
from tools.component_specs.registry import adapter_binding


_EXPECTED_KEYS = {
    "web": "manual_callout_table",
    "latex": "hb_latex_callout",
    "idml": "idml_notice",
    "word": "word_manual_callout_table",
}
_LATEX_MACROS = {
    "warning": "HBWarningBlock",
    "danger": "HBWarningBlock",
    "caution": "HBCautionBlock",
    "note": "HBNoteBlock",
    "tip": "HBTipBlock",
}


def _require_adapter(spec: ComponentSpec, renderer: str) -> Mapping[str, Any]:
    binding = adapter_binding(spec, renderer)
    expected = _EXPECTED_KEYS[renderer]
    if binding.get("key") != expected:
        raise ComponentSpecError(
            f"{spec.component_id}: expected {renderer} adapter {expected!r}; "
            f"got {binding.get('key')!r}"
        )
    return binding


def web_callout_classes(spec: ComponentSpec) -> dict[str, str]:
    _require_adapter(spec, "web")
    return {
        "table": "manual-callout-table",
        "label": "manual-callout-label",
        "body": "manual-callout-body",
    }


def latex_callout_macro(spec: ComponentSpec) -> str:
    _require_adapter(spec, "latex")
    try:
        return _LATEX_MACROS[spec.variant]
    except KeyError as exc:  # guarded by registry validation; defensive boundary
        raise ComponentSpecError(
            f"{spec.component_id}: no LaTeX macro for variant {spec.variant!r}"
        ) from exc


def idml_notice_payload(spec: ComponentSpec) -> dict[str, Any]:
    _require_adapter(spec, "idml")
    legacy = spec.metadata.get("legacy_payload")
    if isinstance(legacy, Mapping):
        return deepcopy(dict(legacy))
    body = str(spec.slot("body").content)
    payload: dict[str, Any] = {
        "kind": "notice",
        "label": str(spec.slot("label").content),
        "variant": spec.variant,
        "texts": [part for part in body.split("\n") if part],
    }
    items = [slot for slot in spec.slots if slot.role == "items"]
    if items:
        payload["texts"] = list(items[0].content)
        payload["list"] = True
    return payload


def idml_notice_payload_from_legacy(
    payload: Mapping[str, Any],
    *,
    source_ref: str,
    language: str = "und",
) -> dict[str, Any]:
    """Validate a legacy notice through ComponentSpec before IDML projection."""
    return idml_notice_payload(
        callout_spec_from_legacy_notice(
            payload,
            source_ref=source_ref,
            language=language,
        )
    )


def word_callout_markup(spec: ComponentSpec) -> dict[str, str]:
    _require_adapter(spec, "word")
    return {
        "table_class": "manual-callout-table",
        "table_style": "width:100%; border-collapse:collapse; margin:0 0 16px 0;",
        "label_class": "manual-callout-label",
        "label_style": "width:16%; border:1px solid #000; padding:6px 8px; vertical-align:top;",
        "body_class": "manual-callout-body",
        "body_style": "border:1px solid #000; padding:6px 8px; vertical-align:top;",
    }


__all__ = [
    "idml_notice_payload",
    "idml_notice_payload_from_legacy",
    "latex_callout_macro",
    "web_callout_classes",
    "word_callout_markup",
]
