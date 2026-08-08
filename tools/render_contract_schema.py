"""Schema-specific validation for the renderer-neutral style contract.

``tools.render_contract`` remains the public loader and CLI facade.  This
module owns schema-v2 structure so adding four-renderer bindings does not turn
the facade into another renderer hot spot.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


SUPPORTED_CAPABILITIES = frozenset(
    {"rendered", "projection-only", "not-applicable"}
)
SUPPORTED_CONFORMANCE_STATES = frozenset({"aligned", "partial"})
WEB_COMPONENT_ADAPTERS = frozenset(
    {"sphinx_html", "web_presentation", "not_applicable"}
)
WORD_COMPONENT_ADAPTERS = frozenset(
    {
        "word_bundle_docx_styles",
        "word_bundle_html",
        "section_properties",
        "not_applicable",
    }
)

_TOP_LEVEL_KEYS = frozenset(
    {
        "schema_version",
        "contract_id",
        "theme_id",
        "latex_registry",
        "token_source",
        "defaults",
        "styles",
    }
)
_STYLE_KEYS = frozenset(
    {
        "role",
        "semantic_source_kinds",
        "variants",
        "token_refs",
        "layout_token_refs",
        "fit_token_refs",
        "theme_token_roles",
        "latex",
        "indesign",
        "web",
        "word",
        "conformance",
        "constraints",
        "approved_variants",
        "final_mile",
    }
)
_LATEX_KEYS = frozenset({"owner", "entrypoints"})
_INDESIGN_KEYS = frozenset(
    {
        "renderer",
        "related_renderers",
        "paragraph_style",
        "paragraph_styles",
        "object_style",
        "table_style",
        "text_layer",
        "sizing",
        "auto_sizing",
    }
)
_WEB_KEYS = frozenset({"capability", "selectors", "component_adapter"})
_WORD_KEYS = frozenset(
    {"capability", "paragraph_styles", "table_styles", "component_adapter"}
)
_CONFORMANCE_KEYS = frozenset({"state", "debt"})
_BOUNDARY_RECORD_KEYS = frozenset({"reason", "owner", "scope", "evidence"})
_FINAL_MILE_KEYS = frozenset({"content_editable", "allowed_adjustments"})
_TOKEN_REF_FIELDS = ("token_refs", "layout_token_refs", "fit_token_refs")


def effective_final_mile(
    contract: Mapping[str, Any], style: Mapping[str, Any]
) -> dict[str, Any]:
    defaults = ((contract.get("defaults") or {}).get("final_mile") or {})
    local = style.get("final_mile") or {}
    if not isinstance(defaults, Mapping) or not isinstance(local, Mapping):
        return {}
    return {**defaults, **local}


def actionable_debt(contract: Mapping[str, Any], style: Mapping[str, Any]) -> list[Any]:
    """Return actionable debt across the v1 compatibility and v2 shapes."""
    if contract.get("schema_version") == 2:
        conformance = style.get("conformance")
        if not isinstance(conformance, Mapping):
            return []
        debt = conformance.get("debt")
    else:
        debt = style.get("debt")
    return list(debt) if isinstance(debt, list) else []


def conformance_state(contract: Mapping[str, Any], style: Mapping[str, Any]) -> Any:
    if contract.get("schema_version") == 2:
        conformance = style.get("conformance")
        return conformance.get("state") if isinstance(conformance, Mapping) else None
    return style.get("status")


def _unknown_keys(prefix: str, value: Mapping[str, Any], allowed: frozenset[str]) -> list[str]:
    return [
        f"{prefix}: unsupported key {key!r}"
        for key in sorted(set(value) - allowed)
    ]


def _string_list(
    prefix: str,
    value: Any,
    *,
    allow_empty: bool = False,
) -> list[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        qualifier = "a list" if allow_empty else "a non-empty list"
        return [f"{prefix} must be {qualifier} of non-empty strings"]
    if not all(isinstance(item, str) and item.strip() for item in value):
        return [f"{prefix} must be a list of non-empty strings"]
    if len(value) != len(set(value)):
        return [f"{prefix} must not contain duplicate values"]
    return []


def _non_empty_string(prefix: str, value: Any) -> list[str]:
    if not isinstance(value, str) or not value.strip():
        return [f"{prefix} must be a non-empty string"]
    return []


def _mapping(prefix: str, value: Any) -> tuple[Mapping[str, Any], list[str]]:
    if not isinstance(value, Mapping):
        return {}, [f"{prefix} must be a mapping"]
    return value, []


def _boundary_records(prefix: str, value: Any) -> list[str]:
    if not isinstance(value, list):
        return [f"{prefix} must be a list"]
    issues: list[str] = []
    for index, record_value in enumerate(value):
        record_prefix = f"{prefix}[{index}]"
        record, record_issues = _mapping(record_prefix, record_value)
        issues.extend(record_issues)
        if record_issues:
            continue
        issues.extend(_unknown_keys(record_prefix, record, _BOUNDARY_RECORD_KEYS))
        issues.extend(_non_empty_string(f"{record_prefix}.reason", record.get("reason")))
        issues.extend(_non_empty_string(f"{record_prefix}.owner", record.get("owner")))
        issues.extend(_string_list(f"{record_prefix}.scope", record.get("scope")))
        issues.extend(_string_list(f"{record_prefix}.evidence", record.get("evidence")))
    return issues


def _validate_latex(prefix: str, value: Any) -> list[str]:
    latex, issues = _mapping(prefix, value)
    if issues:
        return issues
    issues.extend(_unknown_keys(prefix, latex, _LATEX_KEYS))
    issues.extend(_non_empty_string(f"{prefix}.owner", latex.get("owner")))
    issues.extend(_string_list(f"{prefix}.entrypoints", latex.get("entrypoints")))
    return issues


def _validate_indesign(prefix: str, value: Any) -> list[str]:
    indesign, issues = _mapping(prefix, value)
    if issues:
        return issues
    issues.extend(_unknown_keys(prefix, indesign, _INDESIGN_KEYS))
    issues.extend(_non_empty_string(f"{prefix}.renderer", indesign.get("renderer")))
    for key in ("related_renderers", "paragraph_styles"):
        if key in indesign:
            issues.extend(_string_list(f"{prefix}.{key}", indesign.get(key)))
    for key in (
        "paragraph_style",
        "object_style",
        "table_style",
        "text_layer",
        "sizing",
        "auto_sizing",
    ):
        if key in indesign:
            issues.extend(_non_empty_string(f"{prefix}.{key}", indesign.get(key)))
    if not (
        indesign.get("paragraph_style")
        or indesign.get("paragraph_styles")
        or indesign.get("object_style")
        or indesign.get("table_style")
    ):
        issues.append(f"{prefix}: at least one paragraph/object/table style binding is required")
    return issues


def _validate_web(prefix: str, value: Any) -> list[str]:
    web, issues = _mapping(prefix, value)
    if issues:
        return issues
    issues.extend(_unknown_keys(prefix, web, _WEB_KEYS))
    capability = web.get("capability")
    if capability not in SUPPORTED_CAPABILITIES:
        issues.append(f"{prefix}.capability: unsupported capability {capability!r}")
    selectors = web.get("selectors")
    issues.extend(_string_list(f"{prefix}.selectors", selectors, allow_empty=True))
    adapter = web.get("component_adapter")
    if adapter not in WEB_COMPONENT_ADAPTERS:
        issues.append(f"{prefix}.component_adapter: unregistered adapter {adapter!r}")
    if capability == "not-applicable":
        if selectors:
            issues.append(f"{prefix}: not-applicable capability cannot declare selectors")
        if adapter != "not_applicable":
            issues.append(f"{prefix}: not-applicable capability requires not_applicable adapter")
    elif isinstance(selectors, list) and not selectors:
        issues.append(f"{prefix}: rendered capability requires at least one selector")
    return issues


def _validate_word(prefix: str, value: Any) -> list[str]:
    word, issues = _mapping(prefix, value)
    if issues:
        return issues
    issues.extend(_unknown_keys(prefix, word, _WORD_KEYS))
    capability = word.get("capability")
    if capability not in SUPPORTED_CAPABILITIES:
        issues.append(f"{prefix}.capability: unsupported capability {capability!r}")
    paragraph_styles = word.get("paragraph_styles")
    table_styles = word.get("table_styles")
    issues.extend(
        _string_list(f"{prefix}.paragraph_styles", paragraph_styles, allow_empty=True)
    )
    issues.extend(_string_list(f"{prefix}.table_styles", table_styles, allow_empty=True))
    adapter = word.get("component_adapter")
    if adapter not in WORD_COMPONENT_ADAPTERS:
        issues.append(f"{prefix}.component_adapter: unregistered adapter {adapter!r}")
    if capability == "not-applicable":
        if paragraph_styles or table_styles:
            issues.append(f"{prefix}: not-applicable capability cannot declare style bindings")
        if adapter != "not_applicable":
            issues.append(f"{prefix}: not-applicable capability requires not_applicable adapter")
    elif not paragraph_styles and not table_styles and adapter == "not_applicable":
        issues.append(f"{prefix}: rendered capability requires a style or component adapter")
    return issues


def _validate_conformance(prefix: str, value: Any) -> list[str]:
    conformance, issues = _mapping(prefix, value)
    if issues:
        return issues
    issues.extend(_unknown_keys(prefix, conformance, _CONFORMANCE_KEYS))
    state = conformance.get("state")
    if state not in SUPPORTED_CONFORMANCE_STATES:
        issues.append(f"{prefix}.state: unsupported state {state!r}")
    debt = conformance.get("debt")
    issues.extend(_boundary_records(f"{prefix}.debt", debt))
    if state == "aligned" and debt:
        issues.append(f"{prefix}: aligned state cannot contain actionable debt")
    if state == "partial" and isinstance(debt, list) and not debt:
        issues.append(f"{prefix}: partial state requires actionable debt")
    return issues


def validate_v2_contract(
    contract: Mapping[str, Any],
    tokens: Mapping[str, Any],
    *,
    strict: bool = False,
) -> list[str]:
    """Validate schema v2 without importing renderer implementations."""
    issues = _unknown_keys("contract", contract, _TOP_LEVEL_KEYS)
    issues.extend(_non_empty_string("contract_id", contract.get("contract_id")))
    issues.extend(_non_empty_string("theme_id", contract.get("theme_id")))
    styles = contract.get("styles")
    if not isinstance(styles, Mapping) or not styles:
        return issues + ["styles must be a non-empty mapping"]

    defaults, default_issues = _mapping("defaults", contract.get("defaults"))
    issues.extend(default_issues)
    if not default_issues:
        issues.extend(_unknown_keys("defaults", defaults, frozenset({"final_mile"})))
        final_mile, final_mile_issues = _mapping(
            "defaults.final_mile", defaults.get("final_mile")
        )
        issues.extend(final_mile_issues)
        if not final_mile_issues:
            issues.extend(
                _unknown_keys("defaults.final_mile", final_mile, _FINAL_MILE_KEYS)
            )
            issues.extend(
                _string_list(
                    "defaults.final_mile.allowed_adjustments",
                    final_mile.get("allowed_adjustments"),
                )
            )

    for style_id, style_value in styles.items():
        prefix = f"styles.{style_id}"
        if not str(style_id).startswith("HB-"):
            issues.append(f"{prefix}: style ID must start with HB-")
        style, style_issues = _mapping(prefix, style_value)
        issues.extend(style_issues)
        if style_issues:
            continue
        issues.extend(_unknown_keys(prefix, style, _STYLE_KEYS))
        issues.extend(_non_empty_string(f"{prefix}.role", style.get("role")))
        issues.extend(
            _string_list(
                f"{prefix}.semantic_source_kinds",
                style.get("semantic_source_kinds"),
            )
        )
        if "variants" in style:
            issues.extend(_string_list(f"{prefix}.variants", style.get("variants")))
        for token_field in _TOKEN_REF_FIELDS:
            if token_field not in style:
                continue
            token_refs = style.get(token_field)
            issues.extend(_string_list(f"{prefix}.{token_field}", token_refs))
            if isinstance(token_refs, list):
                for token_ref in token_refs:
                    if token_ref not in tokens:
                        issues.append(f"{prefix}: missing layout token {token_ref}")
        if "token_refs" not in style:
            issues.append(f"{prefix}: token_refs is required")
        issues.extend(
            _string_list(f"{prefix}.theme_token_roles", style.get("theme_token_roles"))
        )
        issues.extend(_validate_latex(f"{prefix}.latex", style.get("latex")))
        issues.extend(_validate_indesign(f"{prefix}.indesign", style.get("indesign")))
        issues.extend(_validate_web(f"{prefix}.web", style.get("web")))
        issues.extend(_validate_word(f"{prefix}.word", style.get("word")))
        issues.extend(
            _validate_conformance(f"{prefix}.conformance", style.get("conformance"))
        )
        issues.extend(_boundary_records(f"{prefix}.constraints", style.get("constraints")))
        issues.extend(
            _boundary_records(
                f"{prefix}.approved_variants", style.get("approved_variants")
            )
        )
        if "final_mile" in style:
            final_mile, final_mile_issues = _mapping(
                f"{prefix}.final_mile", style.get("final_mile")
            )
            issues.extend(final_mile_issues)
            if not final_mile_issues:
                issues.extend(
                    _unknown_keys(f"{prefix}.final_mile", final_mile, _FINAL_MILE_KEYS)
                )
        if effective_final_mile(contract, style).get("content_editable") is not False:
            issues.append(f"{prefix}: InDesign content_editable must be false")
        if strict and actionable_debt(contract, style):
            issues.append(f"{prefix}: strict parity requires no actionable debt")
    return issues


__all__ = [
    "SUPPORTED_CAPABILITIES",
    "WEB_COMPONENT_ADAPTERS",
    "WORD_COMPONENT_ADAPTERS",
    "actionable_debt",
    "conformance_state",
    "effective_final_mile",
    "validate_v2_contract",
]
