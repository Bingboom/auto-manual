"""Typed LCD layout-token helpers for the IDML renderer."""
from __future__ import annotations

import math
import re

from .character_metrics import with_character_metrics
from .params import param_pt


def _language(lang: str) -> str:
    return (lang or "en").strip().casefold().replace("_", "-").split("-", 1)[0]


def _profile_pt(
    writer,
    *,
    language: str,
    segment: str,
    role: str,
    metric: str,
    fallback_key: str,
    fallback: float,
) -> float:
    """Resolve a locale/segment/role LCD token from most to least specific."""
    keys = (
        f"lang_{language}_idml_lcd_{segment}_{role}_{metric}",
        f"lang_{language}_idml_lcd_{segment}_{metric}",
        f"idml_lcd_{segment}_{role}_{metric}",
        f"idml_lcd_{segment}_{metric}",
        fallback_key,
    )
    for key in keys:
        if key in writer.params:
            return param_pt(writer.params, key, fallback)
    return fallback


def typography_tokens(
    writer,
    lang: str,
    row: dict[str, str],
    *,
    segment_index: int,
) -> tuple[float, float, float, float]:
    """Return label/body size and leading for one editable LCD row.

    The approved reference contract assigns semantic density roles; layout
    tokens own the actual locale-specific metrics. This keeps source text and
    source identifiers unchanged while avoiding renderer-local row numbers.
    """
    language = _language(lang)
    segment = "first" if segment_index == 0 else "continuation"
    role = row.get("typography_role", "default").strip() or "default"
    label_size = _profile_pt(
        writer,
        language=language,
        segment=segment,
        role=role,
        metric="label_font_size",
        fallback_key="type_lcd_label_font_size",
        fallback=6.2,
    )
    label_leading = _profile_pt(
        writer,
        language=language,
        segment=segment,
        role=role,
        metric="label_font_leading",
        fallback_key="type_lcd_label_font_leading",
        fallback=6.8,
    )
    body_size = _profile_pt(
        writer,
        language=language,
        segment=segment,
        role=role,
        metric="body_font_size",
        fallback_key="type_lcd_body_font_size",
        fallback=5.2,
    )
    body_leading = _profile_pt(
        writer,
        language=language,
        segment=segment,
        role=role,
        metric="body_font_leading",
        fallback_key="type_lcd_body_font_leading",
        fallback=5.8,
    )
    return label_size, label_leading, body_size, body_leading


def layout_tokens(
    writer,
    body_w: float,
    *,
    segment_index: int = 0,
    lang: str = "en",
) -> tuple[tuple[float, ...], float, float]:
    """Resolve segment-aware LCD column, icon, and cell-padding tokens."""
    prefix = "idml_lcd_first" if segment_index == 0 else "idml_lcd_continuation"
    language = _language(lang)
    no_w = param_pt(
        writer.params,
        f"lang_{language}_{prefix}_no_col_width",
        param_pt(
            writer.params,
            f"{prefix}_no_col_width",
            param_pt(writer.params, "comp_lcd_no_col_width", body_w * 0.08),
        ),
    )
    icon_w = param_pt(
        writer.params,
        f"lang_{language}_{prefix}_icon_col_width",
        param_pt(
            writer.params,
            f"{prefix}_icon_col_width",
            param_pt(writer.params, "comp_lcd_icon_col_width", body_w * 0.12),
        ),
    )
    label_w = param_pt(
        writer.params,
        f"lang_{language}_{prefix}_label_col_width",
        param_pt(writer.params, f"{prefix}_label_col_width", 0.0),
    )
    if label_w <= 0:
        raw_label_ratio = writer.params.get(
            "comp_lcd_label_col_width", ("0.24", "ratio")
        )[0].replace("\\linewidth", "")
        try:
            label_ratio = float(raw_label_ratio)
        except ValueError:
            label_ratio = 0.24
        label_w = body_w * label_ratio
    columns = (no_w, icon_w, label_w, body_w - no_w - icon_w - label_w)
    icon_pt = min(
        param_pt(writer.params, "comp_lcd_icon_width", 24.0),
        param_pt(writer.params, "comp_lcd_icon_height", 24.0),
    )
    padding = param_pt(writer.params, "comp_lcd_table_tabcolsep", 1.4)
    return columns, icon_pt, padding


def _wrapped_line_count(text: str, width_pt: float, point_size: float) -> int:
    """Estimate InDesign's line count without depending on local font files.

    The IDML build runs on more than one machine, so row allocation must not
    depend on a desktop-only font metric library.  The same average-glyph
    approach used by the writer's existing height estimator gives a
    deterministic lower bound while preserving explicit source line breaks.
    """
    chars_per_line = max(1, int(width_pt / max(0.01, 0.50 * point_size)))
    return sum(
        max(1, math.ceil(len(source_line) / chars_per_line))
        for source_line in str(text or "").splitlines() or [""]
    )


def governed_row_min_height(
    writer,
    row: dict[str, str],
    cols: tuple[float, ...],
    *,
    padding: float,
    vertical_pad: float,
    text_indent: float,
    lang: str,
    segment_index: int,
    governed_icon_line_reserve: float,
) -> float:
    """Return the deterministic minimum height needed by one governed row.

    A governed row has a fixed outer height because it lives inside a fixed
    rounded panel.  This computes the height needed by the label, body, row
    number, and the smallest icon that the governed icon-fit rule allows.
    """
    label_size, label_leading, body_size, body_leading = typography_tokens(
        writer, lang, row, segment_index=segment_index)
    label_width = max(1.0, cols[2] - text_indent - padding)
    body_width = max(1.0, cols[3] - text_indent - padding)
    label_lines = _wrapped_line_count(row.get("name", ""), label_width, label_size)
    body_lines = _wrapped_line_count(row.get("desc", ""), body_width, body_size)
    inner_height = max(
        label_lines * label_leading,
        body_lines * body_leading,
        4.0 + governed_icon_line_reserve,
    )
    if (
        row.get("suppress_number") != "true"
        and int(row.get("number_row_span", "1") or "1") == 1
    ):
        inner_height = max(
            inner_height,
            param_pt(writer.params, "type_lcd_no_font_leading", 9.4),
        )
    return inner_height + 2 * vertical_pad


def _governed_row_min_heights(
    writer,
    rows: list[dict[str, str]],
    cols: tuple[float, ...],
    *,
    padding: float,
    vertical_pad: float,
    text_indent: float,
    lang: str,
    segment_index: int,
    governed_icon_line_reserve: float,
) -> list[float]:
    return [
        governed_row_min_height(
            writer,
            row,
            cols,
            padding=padding,
            vertical_pad=vertical_pad,
            text_indent=text_indent,
            lang=lang,
            segment_index=segment_index,
            governed_icon_line_reserve=governed_icon_line_reserve,
        )
        for row in rows
    ]


def fit_governed_row_heights(
    writer,
    rows: list[dict[str, str]],
    base_heights: list[float],
    cols: tuple[float, ...],
    *,
    padding: float,
    vertical_pad: float,
    text_indent: float,
    lang: str,
    segment_index: int,
    governed_icon_line_reserve: float,
    budget: float | None = None,
) -> list[float]:
    """Fit governed rows to their existing panel budget.

    The approved profile supplies the total physical budget.  Its individual
    row heights are treated as the starting distribution, not an immutable
    per-row minimum: short rows are compacted to a shared floor and the
    recovered space is assigned to rows whose content needs more lines.  The
    resulting heights still sum to the approved budget, so the rounded shell
    and page composition do not move.

    A caller that needs a page-level decision can catch the budget exception
    and use ``split_governed_rows`` to move whole rows to the next page.  This
    helper itself remains strict so a chunk is never silently undersized.
    """
    if len(rows) != len(base_heights):
        raise ValueError("LCD governed rows and heights must have equal length")
    if not rows:
        return []
    if any(height <= 0 for height in base_heights):
        raise ValueError("LCD governed row heights must be positive")

    minimums = _governed_row_min_heights(
        writer,
        rows,
        cols,
        padding=padding,
        vertical_pad=vertical_pad,
        text_indent=text_indent,
        lang=lang,
        segment_index=segment_index,
        governed_icon_line_reserve=governed_icon_line_reserve,
    )
    budget = sum(base_heights) if budget is None else budget
    minimum_total = sum(minimums)
    if minimum_total > budget + 1e-6:
        raise ValueError(
            "LCD governed content exceeds the approved panel budget "
            f"for {lang}: minimum={minimum_total:.3f}pt, budget={budget:.3f}pt"
        )

    # Maximize the common compact floor while keeping every content minimum
    # inside the existing budget.  This makes one-line rows visually uniform
    # without taking height away from translated multi-line rows.
    floor_low = 0.0
    floor_high = min(base_heights)
    for _ in range(48):
        candidate = (floor_low + floor_high) / 2
        if sum(max(candidate, minimum) for minimum in minimums) <= budget:
            floor_low = candidate
        else:
            floor_high = candidate
    compact_floor = round(floor_low, 3)
    while (
        sum(max(compact_floor, minimum) for minimum in minimums)
        > budget + 1e-9
    ):
        compact_floor = round(compact_floor - 0.001, 3)
    heights = [max(compact_floor, minimum) for minimum in minimums]
    leftover = budget - sum(heights)

    # Give spare height to content-demanding rows only.  Short rows therefore
    # stay compact instead of receiving the spare back uniformly.
    weights = [max(0.0, minimum - compact_floor) for minimum in minimums]
    weight_total = sum(weights)
    if leftover > 1e-9:
        if weight_total <= 1e-9:
            weights[-1] = 1.0
            weight_total = 1.0
        heights = [
            height + leftover * weight / weight_total
            for height, weight in zip(heights, weights)
        ]

    # IDML is intentionally kept at millipoint precision.  Correct rounding
    # on the highest-demand row so the shell and rows have the same budget.
    heights = [round(height, 3) for height in heights]
    correction = round(budget - sum(heights), 3)
    target = max(range(len(weights)), key=lambda index: weights[index])
    heights[target] = round(heights[target] + correction, 3)
    if any(height + 1e-6 < minimum for height, minimum in zip(heights, minimums)):
        raise ValueError(
            f"LCD governed row rounding lost content fit for {lang}"
        )
    return heights


def split_governed_rows(
    writer,
    rows: list[dict[str, str]],
    base_heights: list[float],
    cols: tuple[float, ...],
    *,
    padding: float,
    vertical_pad: float,
    text_indent: float,
    lang: str,
    segment_index: int,
    governed_icon_line_reserve: float,
) -> list[tuple[list[dict[str, str]], list[float]]]:
    """Fit a governed segment or split it at whole-row page boundaries.

    Splitting is reached only after all rows have been reduced to their
    content minimums.  A chunk uses the full continuation-page budget when it
    becomes a page of its own; the final chunk may stay compact.  A single row
    larger than one page is retained as one row and remains AutoGrow-enabled
    for InDesign's final-mile recomposition.
    """
    if len(rows) != len(base_heights):
        raise ValueError("LCD governed rows and heights must have equal length")
    budget = sum(base_heights)
    minimums = _governed_row_min_heights(
        writer,
        rows,
        cols,
        padding=padding,
        vertical_pad=vertical_pad,
        text_indent=text_indent,
        lang=lang,
        segment_index=segment_index,
        governed_icon_line_reserve=governed_icon_line_reserve,
    )
    if sum(minimums) <= budget + 1e-6:
        return [(
            rows,
            fit_governed_row_heights(
                writer,
                rows,
                base_heights,
                cols,
                padding=padding,
                vertical_pad=vertical_pad,
                text_indent=text_indent,
                lang=lang,
                segment_index=segment_index,
                governed_icon_line_reserve=governed_icon_line_reserve,
                budget=budget,
            ),
        )]

    chunks: list[tuple[int, int]] = []
    start = 0
    running = 0.0
    for index, minimum in enumerate(minimums):
        if index > start and running + minimum > budget + 1e-6:
            chunks.append((start, index))
            start = index
            running = 0.0
        running += minimum
    chunks.append((start, len(rows)))

    fitted: list[tuple[list[dict[str, str]], list[float]]] = []
    for chunk_index, (chunk_start, chunk_end) in enumerate(chunks):
        chunk_rows = rows[chunk_start:chunk_end]
        chunk_base = base_heights[chunk_start:chunk_end]
        chunk_minimums = minimums[chunk_start:chunk_end]
        # Full chunks get the approved page budget.  The final chunk keeps
        # its compact source budget unless its content needs more space.
        chunk_budget = (
            budget
            if chunk_index < len(chunks) - 1
            else max(sum(chunk_base), sum(chunk_minimums))
        )
        # A single indivisible row can itself exceed one page.  Keep it as a
        # growable row rather than turning a legitimate page-break decision
        # into a build failure.
        chunk_budget = max(chunk_budget, sum(chunk_minimums))
        fitted.append((
            chunk_rows,
            fit_governed_row_heights(
                writer,
                chunk_rows,
                chunk_base,
                cols,
                padding=padding,
                vertical_pad=vertical_pad,
                text_indent=text_indent,
                lang=lang,
                segment_index=segment_index,
                governed_icon_line_reserve=governed_icon_line_reserve,
                budget=chunk_budget,
            ),
        ))
    return fitted


def typed_paragraph(writer, style: str, text: str,
                    size_key: str | None = None,
                    leading_key: str | None = None, *,
                    point_size: float | None = None,
                    leading: float | None = None,
                    bold: bool = False,
                    font: str | None = None) -> str:
    """Apply shared typed LCD tokens without replacing the template style."""
    if point_size is None:
        point_size = param_pt(writer.params, size_key or "", 5.2)
    if leading is None:
        leading = param_pt(writer.params, leading_key or "", 5.8)
    paragraph = writer._psr(style, text, terminal=True).replace(
        "<ParagraphStyleRange ",
        '<ParagraphStyleRange Hyphenation="false" ',
        1,
    )
    paragraph = with_character_metrics(
        paragraph,
        point_size=point_size,
        leading=leading,
    )
    if bold:
        def apply_bold(match: re.Match[str]) -> str:
            attrs = match.group("attrs")
            if ' FontStyle=' in f" {attrs}":
                return match.group(0)
            return f'<CharacterStyleRange FontStyle="Bold" {attrs}>'

        paragraph = re.sub(
            r'<CharacterStyleRange (?P<attrs>[^>]*)>',
            apply_bold,
            paragraph,
        )
    if font:
        paragraph = paragraph.replace(
            '<AppliedFont type="string">Arial Unicode MS</AppliedFont>',
            f'<AppliedFont type="string">{font}</AppliedFont>',
        )
    return paragraph
