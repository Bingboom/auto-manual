"""Localized notice labels shared by the IDML RST extractor."""
from __future__ import annotations

import re

NOTICE_VARIANTS_BY_LABEL = {
    "NOTE": "note", "TIP": "tip", "TIPS": "tip",
    "CAUTION": "caution", "WARNING": "warning", "DANGER": "danger",
    "REMARQUE": "note", "CONSEIL": "tip", "CONSEILS": "tip",
    "ATTENTION": "caution", "AVERTISSEMENT": "warning",
    "NOTA": "note", "CONSEJO": "tip", "CONSEJOS": "tip",
    "PRECAUCIÓN": "caution", "PRECAUCION": "caution",
    "ADVERTENCIA": "warning", "PELIGRO": "danger",
}


def notice_label_variant(label: str) -> tuple[str, str] | None:
    """Return (display label, component variant) for a localized notice label."""
    display = re.sub(r"[\s:：-]+$", "", label.strip()).strip()
    variant = NOTICE_VARIANTS_BY_LABEL.get(display.upper())
    if variant is None:
        return None
    return display, variant
