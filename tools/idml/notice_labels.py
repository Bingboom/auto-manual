"""Localized notice labels shared by the IDML RST extractor.

Signal-word semantics belong to the shared Callout ComponentSpec. This thin
adapter preserves the extractor's historical ``(display, variant)`` API while
preventing its label vocabulary from drifting away from the other renderers.
"""
from __future__ import annotations

from tools.component_specs.callout import display_label, variant_for_label


def notice_label_variant(label: str) -> tuple[str, str] | None:
    """Return (display label, component variant) for a localized notice label."""
    display = display_label(label)
    variant = variant_for_label(display)
    if variant is None:
        return None
    return display, variant
