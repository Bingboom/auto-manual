"""Coarse layout-height estimation for composed IDML pages.

Deliberately rough (same philosophy as package.estimate_spec_height): a
slight underestimate shows InDesign's overset indicator and the designer
drags the frame; the goal is that *typical* content is visible without
dragging, not pixel-perfect fitting.
"""
from __future__ import annotations


def balanced_icon_split(icons: list[dict], text_col_w: float,
                        min_row: float) -> tuple[list[dict], list[dict]]:
    """Split icon rows into two side-by-side tables, order preserved,
    choosing the split point that minimizes the taller table's estimated
    height (a fixed halfway split leaves one table much taller when a
    long row like the WEEE text lands on one side)."""
    if len(icons) < 2:
        return icons, []
    best = (float("inf"), 1)
    for k in range(1, len(icons)):
        left = est_table_height([r.get("text", "") for r in icons[:k]], text_col_w, min_row)
        right = est_table_height([r.get("text", "") for r in icons[k:]], text_col_w, min_row)
        tall = max(left, right)
        if tall < best[0]:
            best = (tall, k)
    return icons[: best[1]], icons[best[1]:]


def est_table_height(texts: list[str], text_col_w: float, min_row: float) -> float:
    """Header row plus a wrap estimate per row (7.4pt/line, ~0.52em glyphs)."""
    # Table body text is HB Spec Value (6.0pt / 6.6 leading).
    per_line = max(16, int(text_col_w / (0.525 * 6.0)))
    height = 16.0
    for text in texts:
        lines = sum(
            max(1, (len(part) + per_line - 1) // per_line)
            for part in str(text).split("\n")
        )
        height += max(min_row, 7.0 * lines + 5.0)
    return height
