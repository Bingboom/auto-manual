"""Coarse layout-height estimation for composed IDML pages.

Deliberately rough (same philosophy as package.estimate_spec_height): a
slight underestimate shows InDesign's overset indicator and the designer
drags the frame; the goal is that *typical* content is visible without
dragging, not pixel-perfect fitting.
"""
from __future__ import annotations

import re


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


_SYMBOL_KEY_ORDER = {
    "warning_triangle": 1,
    "read_manual": 2,
    "electric_shock": 3,
    "battery_charging": 4,
    "explosive_material": 5,
    "heavy_object": 6,
    "do_not_dismantle": 7,
    "no_open_flame": 8,
    "keep_away_from_children": 9,
    "li_ion": 10,
    "weee": 11,
    "weee2": 12,
}


def _symbol_order(row: dict, fallback: int) -> float:
    """Recover canonical order after the renderer-neutral IR drops row keys."""
    raw_order = row.get("order")
    if raw_order not in (None, ""):
        try:
            return float(raw_order)
        except (TypeError, ValueError):
            pass
    key_order = _SYMBOL_KEY_ORDER.get(str(row.get("symbol_key") or ""))
    if key_order is not None:
        return float(key_order)
    figure = str(row.get("figure") or "")
    match = re.search(r"(?:^|[/\\])(\d+)_", figure)
    if match:
        return float(match.group(1))
    return float(fallback)


def template_symbol_split(
    icons: list[dict],
    *,
    dense: bool = False,
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """Split reference symbol tables into current- and continuation-page rows.

    English fits canonical rows 1-6 and 7-11 on one page.  The denser French
    and Spanish compositions keep rows 1-4 and 7-10 on the symbols page, then
    continue with rows 5-6 and row 11 above the following FCC panel.  Row 12
    (the separate batteries/accumulators mark) is not part of this approved
    US reference composition.
    """
    indexed = [(_symbol_order(row, index), index, row)
               for index, row in enumerate(icons, start=1)]
    ordered = [row for order, _, row in sorted(indexed)
               if 1 <= order <= 11]
    left_all = ordered[:6]
    right_all = ordered[6:11]
    if not dense:
        return left_all, right_all, [], []
    return left_all[:4], right_all[:4], left_all[4:], right_all[4:]


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
