"""Fail-closed boundary for reader-visible copy consumed by IDML.

Renderers may rearrange or style source text, but must not invent a title,
label, duration, instruction, or placeholder when its semantic source is
missing.
"""
from __future__ import annotations

from collections.abc import Iterable


def source_text(value: object, *, owner: str, strict: bool = True) -> str:
    """Return normalized source copy or reject a required missing value."""
    text = str(value or "").strip()
    if not text and strict:
        raise ValueError(f"{owner} is required from source content")
    return text


def source_block_text(
    blocks: Iterable[tuple[str, str]], kind: str, *, owner: str,
) -> str:
    """Return the first required source block of ``kind``."""
    return source_text(
        next((text for block_kind, text in blocks if block_kind == kind), ""),
        owner=owner,
    )


__all__ = ("source_block_text", "source_text")
