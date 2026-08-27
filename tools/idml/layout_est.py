"""Coarse layout-height estimation for composed IDML pages.

Deliberately rough (same philosophy as package.estimate_spec_height): a
slight underestimate shows InDesign's overset indicator and the designer
drags the frame; the goal is that *typical* content is visible without
dragging, not pixel-perfect fitting.
"""
from __future__ import annotations

import re

from .line_metrics import estimated_line_count


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


def _symbol_key_from_figure(row: dict) -> str:
    """Recover a semantic symbol key from the staged asset basename."""

    figure = str(row.get("figure") or "").replace("\\", "/").rsplit("/", 1)[-1]
    folded = figure.casefold()
    for key in sorted(_SYMBOL_KEY_ORDER, key=len, reverse=True):
        if re.search(
            rf"(?:^|[_-]){re.escape(key.casefold())}(?:[_-]|\.|$)",
            folded,
        ):
            return key
    return ""


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
    figure_key_order = _SYMBOL_KEY_ORDER.get(_symbol_key_from_figure(row))
    if figure_key_order is not None:
        return float(figure_key_order)
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
    # Prepared RST carries only the rendered image basename.  Those basenames
    # restart at 10/20/... in each visual column, so they cannot recover the
    # canonical order (the second column's first row also looks like ``10_``).
    # When semantic keys/order are available, use them.  Otherwise retain the
    # component's group order: normal tables are left 1-6/right 7-11 and the
    # dense split tables are left 1-4/right 7-10 followed by continuation
    # rows 5-6/11.
    has_semantic_order = any(
        row.get("order") not in (None, "") or row.get("symbol_key")
        or _symbol_key_from_figure(row)
        for row in icons
    )
    if not has_semantic_order and len(icons) >= 11:
        if dense:
            return icons[:4], icons[4:8], icons[8:10], icons[10:11]
        return icons[:6], icons[6:11], [], []

    indexed = [(_symbol_order(row, index), index, row)
               for index, row in enumerate(icons, start=1)]
    ordered_entries = [entry for entry in sorted(indexed) if entry[0] >= 1]
    ordered = [row for _, _, row in ordered_entries]
    canonical_orders = {float(index) for index in range(1, 12)}
    current_orders = {order for order, _, _ in ordered_entries}
    if current_orders != canonical_orders:
        # Sparse product families are not forced into the JE-1000F 6/5
        # canonical columns.  Preserve semantic order, keep at least two rows
        # in the second column, and cap the first column at five rows.  This
        # also retains registered marks beyond canonical row 11.
        split_at = min(5, max(1, len(ordered) - 2))
        left_sparse = ordered[:split_at]
        right_sparse = ordered[split_at:]
        if not dense:
            return left_sparse, right_sparse, [], []
        return (
            left_sparse[:4],
            right_sparse[:4],
            left_sparse[4:],
            right_sparse[4:],
        )
    left_all = ordered[:6]
    right_all = ordered[6:11]
    if not dense:
        return left_all, right_all, [], []
    return left_all[:4], right_all[:4], left_all[4:], right_all[4:]


def est_table_height(texts: list[str], text_col_w: float, min_row: float) -> float:
    """Header row plus a Unicode-width-aware wrap estimate per row."""
    # Table body text is HB Spec Value (6.0pt / 6.6 leading).
    height = 16.0
    for text in texts:
        lines = estimated_line_count(
            text,
            text_col_w,
            point_size=6.0,
            narrow_width_ratio=0.525,
            minimum_narrow_chars=16,
        )
        height += max(min_row, 7.0 * lines + 5.0)
    return height
