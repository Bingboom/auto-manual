"""Four renderer projections for warranty ComponentSpecs."""
from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from tools.component_specs.model import ComponentSpec, ComponentSpecError
from tools.component_specs.registry import adapter_binding
from tools.component_specs.warranty import (
    WARRANTY_LEAD_COMPONENT_ID,
    WARRANTY_SECTION_COMPONENT_ID,
    WARRANTY_YEARS_COMPONENT_ID,
    warranty_semantic_projection,
)


_EXPECTED_KEYS = {
    WARRANTY_LEAD_COMPONENT_ID: {
        "web": "hb_warranty_lead",
        "latex": "hb_latex_warranty_lead",
        "idml": "idml_warranty_lead",
        "word": "word_warranty_lead",
    },
    WARRANTY_SECTION_COMPONENT_ID: {
        "web": "hb_warranty_section",
        "latex": "hb_latex_warranty_section",
        "idml": "idml_warranty_section",
        "word": "word_warranty_section",
    },
    WARRANTY_YEARS_COMPONENT_ID: {
        "web": "hb_warranty_years",
        "latex": "hb_latex_warranty_years",
        "idml": "idml_warranty_years",
        "word": "word_warranty_years",
    },
}


def _projection(spec: ComponentSpec, renderer: str) -> dict[str, Any]:
    try:
        expected = _EXPECTED_KEYS[spec.component_id][renderer]
    except KeyError as exc:
        raise ComponentSpecError(
            f"unsupported warranty adapter for {spec.component_id!r}"
        ) from exc
    binding = adapter_binding(spec, renderer)
    if binding.get("key") != expected:
        raise ComponentSpecError(
            f"{spec.component_id}: expected {renderer} adapter {expected!r}; "
            f"got {binding.get('key')!r}"
        )
    return warranty_semantic_projection(spec)


def _plain(value: str) -> str:
    return BeautifulSoup(value, "html.parser").get_text(" ", strip=True)


def web_warranty_projection(spec: ComponentSpec) -> dict[str, Any]:
    classes = {
        WARRANTY_LEAD_COMPONENT_ID: "hb-warranty-intro-composition",
        WARRANTY_SECTION_COMPONENT_ID: "hb-warranty-card",
        WARRANTY_YEARS_COMPONENT_ID: "hb-warranty-period-card",
    }
    return {**_projection(spec, "web"), "component_class": classes[spec.component_id]}


def latex_warranty_projection(spec: ComponentSpec) -> dict[str, Any]:
    projection = _projection(spec, "latex")
    if spec.component_id == WARRANTY_LEAD_COMPONENT_ID:
        return {**projection, "environment": "HBWarrantyLead"}
    if spec.component_id == WARRANTY_SECTION_COMPONENT_ID:
        return {**projection, "environment": "HBWarrantySection"}
    return {
        **projection,
        "environment": "HBWarrantyYears",
        "column_environment": "HBWarrantyYearColumn",
    }


def idml_warranty_payload(spec: ComponentSpec) -> dict[str, Any]:
    projection = _projection(spec, "idml")
    if spec.component_id == WARRANTY_LEAD_COMPONENT_ID:
        # The existing IDML flow represents the second lead paragraph as the
        # immediately following ``warrantynote`` block, not as part of the lead
        # panel. Keep that two-carrier shape explicit so a future IR consumer
        # cannot silently drop or restyle the local-law note.
        return {
            "kind": "warrantylead",
            "texts": [_plain(projection["lead_html"])],
            "following_blocks": [
                {
                    "kind": "warrantynote",
                    "text": _plain(projection["local_note_html"]),
                }
            ],
        }
    if spec.component_id == WARRANTY_SECTION_COMPONENT_ID:
        blocks: list[dict[str, Any]] = []
        for block in projection["blocks"]:
            if block["kind"] == "paragraph":
                blocks.append({"kind": "body", "text": block["text"]})
            else:
                blocks.extend(
                    {"kind": "list", "text": f"• {item}"}
                    for item in block["items"]
                )
        return {
            "kind": "warrantysection",
            "title": projection["title"],
            "index": projection["section_index"],
            "blocks": blocks,
        }
    return {
        "kind": "warrantyyears",
        "items": [
            {
                "number": period["number"],
                "unit": period["unit"],
                "label": period["label"],
                "text": period["body_text"],
            }
            for period in projection["periods"]
        ],
    }


def word_warranty_projection(spec: ComponentSpec) -> dict[str, Any]:
    projection = _projection(spec, "word")
    classes = {
        WARRANTY_LEAD_COMPONENT_ID: "hb-warranty-word-lead",
        WARRANTY_SECTION_COMPONENT_ID: "hb-warranty-word-section",
        WARRANTY_YEARS_COMPONENT_ID: "hb-warranty-word-years",
    }
    return {
        **projection,
        "editable": True,
        "component_class": classes[spec.component_id],
    }


__all__ = [
    "idml_warranty_payload",
    "latex_warranty_projection",
    "web_warranty_projection",
    "word_warranty_projection",
]
