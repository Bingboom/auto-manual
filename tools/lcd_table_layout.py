"""Shared LCD-table pagination rules for LaTeX and IDML.

Every segment is a complete rounded table.  The limits preserve the master
type and icon sizes; extra source rows therefore create another continuation
page instead of clipping into the footer.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

Row = TypeVar("Row")

EN_FIRST_SEGMENT_ROWS = 7
TRANSLATED_FIRST_SEGMENT_ROWS = 6
EN_CONTINUATION_SEGMENT_ROWS = 18
TRANSLATED_CONTINUATION_SEGMENT_ROWS = 16


def split_lcd_table_rows(
    rows: Sequence[Row],
    *,
    lang: str,
    first_segment_rows: int | None = None,
    continuation_segment_rows: int | None = None,
) -> list[list[Row]]:
    """Split rows into bounded, independently rounded page segments."""
    if not rows:
        return []
    is_english = (lang or "en").strip().casefold().replace("_", "-").startswith("en")
    first_limit = first_segment_rows or (
        EN_FIRST_SEGMENT_ROWS if is_english else TRANSLATED_FIRST_SEGMENT_ROWS
    )
    continuation_limit = continuation_segment_rows or (
        EN_CONTINUATION_SEGMENT_ROWS
        if is_english else TRANSLATED_CONTINUATION_SEGMENT_ROWS
    )
    first_limit = max(1, int(first_limit))
    continuation_limit = max(1, int(continuation_limit))
    segments = [list(rows[:first_limit])]
    for start in range(first_limit, len(rows), continuation_limit):
        segments.append(list(rows[start:start + continuation_limit]))
    return segments
