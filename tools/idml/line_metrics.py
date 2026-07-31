"""Deterministic Unicode-aware line estimates for editable IDML text.

The renderer cannot depend on desktop font files because builds run on both
developer Macs and headless CI hosts.  It therefore keeps the existing
average Latin-glyph model, but counts Unicode East Asian Width ``W`` and ``F``
characters as full-em glyphs.  Ambiguous-width characters stay narrow so the
same source produces the same geometry on every host.
"""
from __future__ import annotations

import math
import unicodedata


DEFAULT_NARROW_WIDTH_RATIO = 0.52


def east_asian_width_units(
    text: object,
    *,
    narrow_width_ratio: float = DEFAULT_NARROW_WIDTH_RATIO,
) -> float:
    """Return *narrow-character equivalents* for one text segment.

    A normal Latin character is one unit.  A wide/fullwidth character is
    ``1 / narrow_width_ratio`` units, so at the default ratio it occupies one
    em instead of 0.52 em.  Combining marks add no width.
    """
    if narrow_width_ratio <= 0:
        raise ValueError("narrow_width_ratio must be positive")

    units = 0.0
    source = "" if text is None else str(text)
    for char in source:
        if unicodedata.category(char).startswith("M"):
            continue
        if unicodedata.east_asian_width(char) in {"W", "F"}:
            units += 1.0 / narrow_width_ratio
        else:
            units += 1.0
    return units


def estimated_text_width(
    text: object,
    *,
    point_size: float,
    narrow_width_ratio: float = DEFAULT_NARROW_WIDTH_RATIO,
) -> float:
    """Return the portable point-width estimate for one text segment."""
    if point_size <= 0:
        raise ValueError("point_size must be positive")
    return (
        east_asian_width_units(
            text,
            narrow_width_ratio=narrow_width_ratio,
        )
        * narrow_width_ratio
        * point_size
    )


def estimated_line_count(
    text: object,
    measure: float,
    *,
    point_size: float,
    narrow_width_ratio: float = DEFAULT_NARROW_WIDTH_RATIO,
    minimum_narrow_chars: int = 1,
) -> int:
    """Estimate wrapped lines while preserving explicit source line breaks.

    ``minimum_narrow_chars`` retains each call site's approved lower bound.
    For narrow-only text this is byte-for-byte geometry compatible with the
    former ``len(text) / chars_per_line`` calculation; only combining and
    East-Asian wide/fullwidth characters change the estimate.
    """
    if point_size <= 0:
        raise ValueError("point_size must be positive")
    if narrow_width_ratio <= 0:
        raise ValueError("narrow_width_ratio must be positive")
    if minimum_narrow_chars < 1:
        raise ValueError("minimum_narrow_chars must be at least 1")

    narrow_capacity = max(
        minimum_narrow_chars,
        int(max(0.0, measure) / (point_size * narrow_width_ratio)),
    )
    source = "" if text is None else str(text)
    normalized = source.replace("\r\n", "\n").replace("\r", "\n")
    return sum(
        max(
            1,
            math.ceil(
                east_asian_width_units(
                    segment,
                    narrow_width_ratio=narrow_width_ratio,
                )
                / narrow_capacity
            ),
        )
        for segment in normalized.split("\n")
    )
