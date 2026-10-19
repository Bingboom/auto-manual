"""Shared-component admission for native portable-manual Web imports.

Requirements follow semantic chapter IDs owned by the native importer, never
model names, translated headings, or the candidate's claimed inventory. This
does not govern arbitrary RST manuals or renderer-neutral prose documents.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from typing import Any


NATIVE_SOURCES = frozenset({"frozen-pdf-json", "frozen-ai-json"})
PROFILE = "native-portable-shared-components/v1"

# A minimum is intentional for variable-length specifications, warranty and
# App sections. No product's row, panel, icon or artwork count is a default.
_CHAPTER_COMPONENTS = {
    "symbols": {"HB-TABLE-SYMBOL-SIGNAL": 1, "HB-TABLE-SYMBOL-ICON": 1},
    "in_the_box": {"HB-SPECIAL-INBOX": 1},
    "lcd_display": {"HB-TABLE-LCD-ICON": 1},
    "operations": {
        "HB-SPECIAL-OPERATION": 1,
        "HB-TABLE-LCD-MODE": 1,
        "HB-TABLE-AUTO-RESUME": 1,
        "HB-TABLE-KEY-COMBINATIONS": 1,
    },
    "troubleshooting": {"HB-TABLE-TROUBLESHOOTING": 1},
    "specifications": {"HB-TABLE-SPEC": 1},
    "warranty": {
        "HB-WARRANTY-LEAD": 1, "HB-WARRANTY-SECTION": 1, "HB-WARRANTY-YEARS": 1,
    },
    "app_setup": {"HB-SPECIAL-APP": 1},
}
_SINGLETONS = frozenset({
    "HB-TABLE-SYMBOL-SIGNAL", "HB-TABLE-SYMBOL-ICON", "HB-SPECIAL-INBOX",
    "HB-TABLE-LCD-ICON", "HB-TABLE-LCD-MODE", "HB-TABLE-AUTO-RESUME",
    "HB-TABLE-KEY-COMBINATIONS", "HB-TABLE-TROUBLESHOOTING",
    "HB-WARRANTY-LEAD", "HB-WARRANTY-YEARS",
})


def audit_frozen_component_coverage(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Inspect actual flow nodes; return a reviewable, language-neutral audit."""
    if raw.get("source") not in NATIVE_SOURCES:
        return {"profile": PROFILE, "applicable": False, "issues": []}
    issues: list[str] = []
    chapters: dict[str, Counter] = {}
    components: Counter = Counter()
    references: list[dict[str, str]] = []

    def visit(node, location, counts):
        if not isinstance(node, dict):
            issues.append(f"{location}: flow node must be an object")
            return
        kind = node.get("kind")
        if kind == "component":
            spec = node.get("component_spec", {})
            identity = spec.get("component_id") if isinstance(spec, dict) else None
            if not isinstance(identity, str):
                issues.append(f"{location}: component identity missing")
                return
            counts[identity] += 1
            components[identity] += 1
            if identity == "HB-SPECIAL-REFERENCE-FIGURE":
                references.append({"location": location, "source_ref": spec.get("source_ref", "")})
            # A registered component owns its carrier and slot markup. Those
            # tables/images are expected and are validated by its own contract.
            return
        if kind in {"table", "image"}:
            issues.append(f"{location}: unbound {kind}; use its shared ComponentSpec")
        for index, child in enumerate(node.get("children", [])):
            visit(child, f"{location}/children[{index}]", counts)

    for page in raw.get("pages", []):
        identity = page.get("page_id")
        if identity in chapters:
            issues.append(f"{identity}: duplicate semantic chapter")
        counts = chapters.setdefault(identity, Counter())
        for block in page.get("blocks", []):
            visit(block.get("payload"), block.get("source_ref", str(identity)), counts)
    for chapter, required in _CHAPTER_COMPONENTS.items():
        if chapter not in chapters:
            issues.append(f"{chapter}: required native-manual chapter missing")
            continue
        for identity, minimum in required.items():
            actual = chapters[chapter][identity]
            if actual < minimum or (identity in _SINGLETONS and actual != 1):
                expected = "exactly one" if identity in _SINGLETONS else "at least one"
                issues.append(f"{chapter}: expected {expected} {identity}, found {actual}")
    # Dense, approved Overview callouts may remain governed reference figures.
    # A generic image or a screenshot cannot satisfy the semantic table rules.
    overview = chapters.get("product_overview", Counter())
    if not (overview["HB-SPECIAL-OVERVIEW"] or overview["HB-SPECIAL-REFERENCE-FIGURE"]):
        issues.append("product_overview: shared Overview or governed reference figure missing")
    for identity in sorted(_SINGLETONS):
        if components[identity] > 1:
            issues.append(f"{identity}: duplicate singleton across chapters")
    metadata = raw.get("metadata") or {}
    inventory = metadata.get("component_inventory")
    if not isinstance(inventory, dict) or inventory != dict(components):
        issues.append("component_inventory: declaration differs from actual flow components")
    return {
        "profile": PROFILE, "applicable": True,
        "model": raw.get("model"), "region": raw.get("region"), "language": raw.get("language"),
        "chapters": {key: dict(value) for key, value in chapters.items()},
        "components": dict(components), "governed_reference_figures": references,
        "issues": issues,
    }


def require_frozen_component_coverage(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Fail closed for a native import whose shared bindings are incomplete."""
    report = audit_frozen_component_coverage(raw)
    if report["issues"]:
        target = "/".join(str(raw.get(key, "?")) for key in ("model", "region", "language"))
        raise ValueError(f"shared component coverage failed for {target}: " + "; ".join(report["issues"]))
    return report
