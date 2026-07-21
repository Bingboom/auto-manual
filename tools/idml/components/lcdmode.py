"""LCD screen-mode table component (componentization P2)."""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from unicodedata import east_asian_width

from ..params import param_pt
from ..primitives import cell, component_table, image_cell_content, psr, wrap_table_paragraph
from .base import RenderContext, figure_paragraph
from .oppanel import (
    _editable_text_frame,
    _estimated_lines,
    _panel_bounds,
    _positioned_image,
    _shape,
    _sized_psr,
    _special_panel_paragraph,
)
from .rounded_table import rounded_table_panel, table_text_indent


_REFERENCE_MEASURE = 312.09
_REFERENCE_PANEL_WIDTH = 312.74
_REFERENCE_ART_WIDTH = 117.60
_REFERENCE_ART_HEIGHT = 85.90
_REFERENCE_ART_VISIBLE_LEFT = 6.91
_ART_SOURCE_WIDTH_PX = 536.0
_ART_SOURCE_HEIGHT_PX = 404.0
_ART_VISIBLE_BOUNDS_PX = (8.0, 37.0, 480.0, 383.0)


@dataclass(frozen=True)
class _ReferenceGeometry:
    """Measured LCD-panel geometry from the EN/FR/ES reference pages."""

    panel_height: float
    left_indent: float
    row_heights: tuple[float, float, float, float, float, float]
    column_widths: tuple[float, float, float]
    table_top_margin: float
    art_top_margin: float
    space_before: float
    space_after: float


_REFERENCE_GEOMETRY = {
    "en": _ReferenceGeometry(
        panel_height=111.48,
        left_indent=-6.24,
        row_heights=(15.00, 8.75, 24.50, 20.00, 8.30, 19.44),
        column_widths=(43.05, 29.33, 79.35),
        table_top_margin=13.69,
        art_top_margin=20.445,
        space_before=4.13,
        space_after=0.42,
    ),
    "fr": _ReferenceGeometry(
        panel_height=123.01,
        left_indent=-2.05,
        row_heights=(18.12, 12.01, 18.09, 17.22, 12.33, 16.74),
        column_widths=(39.05, 33.33, 85.17),
        table_top_margin=20.85,
        art_top_margin=26.275,
        space_before=6.35,
        space_after=2.79,
    ),
    "es": _ReferenceGeometry(
        panel_height=124.53,
        left_indent=-6.18,
        row_heights=(17.78, 11.76, 18.96, 17.00, 12.94, 20.63),
        column_widths=(39.05, 33.33, 79.35),
        table_top_margin=20.23,
        art_top_margin=20.285,
        space_before=6.49,
        space_after=5.43,
    ),
}


def _reference_geometry(language: str | None) -> _ReferenceGeometry | None:
    """Return measured geometry only for an explicitly governed locale."""
    normalized = (language or "").strip().lower().replace("_", "-")
    if not normalized:
        return None
    return _REFERENCE_GEOMETRY.get(normalized.split("-", 1)[0])


def _compensated_art_placement(
    *,
    scale: float,
    visible_top: float,
) -> tuple[float, float, float, float]:
    """Return the full PNG frame needed to place its visible art at reference size.

    The approved ``op_lcd_mode.png`` keeps white extraction margins around the
    line art.  Enlarging and offsetting the linked image frame compensates for
    those margins without mutating the governed source asset.  A geometric
    mean keeps the proportional placement within 0.4 pt of both independently
    measured reference dimensions.
    """
    visible_left_px, visible_top_px, visible_right_px, visible_bottom_px = (
        _ART_VISIBLE_BOUNDS_PX
    )
    visible_width_px = visible_right_px - visible_left_px
    visible_height_px = visible_bottom_px - visible_top_px
    x_scale = _REFERENCE_ART_WIDTH / visible_width_px
    y_scale = _REFERENCE_ART_HEIGHT / visible_height_px
    point_scale = (x_scale * y_scale) ** 0.5 * scale

    frame_width = _ART_SOURCE_WIDTH_PX * point_scale
    frame_height = _ART_SOURCE_HEIGHT_PX * point_scale
    frame_left = (
        _REFERENCE_ART_VISIBLE_LEFT * scale
        - visible_left_px * point_scale
    )
    frame_top = visible_top - visible_top_px * point_scale
    return frame_width, frame_height, frame_left, frame_top + frame_height


def _fallback_lcdmode(
    spec: dict,
    ctx: RenderContext,
    *,
    tid: str,
    terminal: bool,
    span_columns: bool,
    body_w: float,
) -> tuple[str, float]:
    """Keep the portable image + editable-table renderer.

    Rounded/composed objects need ``RenderContext.add_story``.  Unit callers,
    downstream render contexts, and bundles without the approved LCD artwork
    must still receive the original, fully editable table representation.
    """
    groups = spec.get("groups", [])
    img_ref = spec.get("img", "")
    art = ""
    img = ctx.resolve_bundle_image(img_ref) if img_ref else None
    if img is not None:
        iw, ih = ctx.art_frame_size(img, max_w=110.0)
        art = figure_paragraph(image_cell_content(f"{tid}art", img, iw, ih))

    inner_w = body_w - 1.5
    state_w = param_pt(ctx.params, "comp_lcd_mode_state_col_width", 59.53)
    action_w = param_pt(ctx.params, "comp_lcd_mode_action_col_width", 42.52)
    cols = [state_w, action_w, inner_w - state_w - action_w]
    rule = max(0.2, param_pt(ctx.params, "comp_table_outer_rule", 0.75) / 2.0)
    text_indent = table_text_indent(ctx.params)
    cells = []
    row_index = 0
    for group in groups:
        actions = group.get("actions", [])
        for action_index, (action, description) in enumerate(actions):
            if action_index == 0:
                state_cell = cell(
                    f"{tid}c{row_index}_0",
                    f"0:{row_index}",
                    psr("HB Spec Label", group.get("state", ""), terminal=True),
                    fill="Color/HB Bg K05",
                    top=2,
                    bottom=2,
                    left=text_indent,
                    right=3,
                    edge_weight=rule,
                    edge_color="Color/HB Line K40",
                    valign="CenterAlign",
                ).replace('RowSpan="1"', f'RowSpan="{len(actions)}"', 1)
                cells.append(state_cell)
            cells.append(
                cell(
                    f"{tid}c{row_index}_1",
                    f"1:{row_index}",
                    psr("HB Spec Label", action, terminal=True),
                    top=2,
                    bottom=2,
                    left=text_indent,
                    right=3,
                    edge_weight=rule,
                    edge_color="Color/HB Line K40",
                    valign="CenterAlign",
                )
            )
            cells.append(
                cell(
                    f"{tid}c{row_index}_2",
                    f"2:{row_index}",
                    psr("HB Spec Value", description, terminal=True),
                    top=2,
                    bottom=2,
                    left=text_indent,
                    right=4,
                    edge_weight=rule,
                    edge_color="Color/HB Line K40",
                    valign="CenterAlign",
                )
            )
            row_index += 1

    table = component_table(tid, cols, cells, n_rows=row_index, role="data")
    if ctx.add_story is not None:
        # This path is used only when the approved composed-panel artwork is
        # unavailable.  Preserve the old rounded-table behavior, including
        # its corner masks, for compatibility with partial bundles.
        table_text = " ".join(
            str(value)
            for group in groups
            for value in (
                group.get("state", ""),
                *(
                    item
                    for action in group.get("actions", [])
                    for item in action
                ),
            )
        )
        localized = any(ord(char) > 127 for char in table_text)
        if row_index >= 6 and localized:
            framed_h = 87.9
        else:
            framed_h = ((13.2 if row_index <= 3 else 10.5) * row_index + 1.5)
        table_xml = rounded_table_panel(
            ctx.add_story,
            ctx.params,
            sid=f"st_anchor_lcdmode_{tid}",
            title="LCD mode table",
            table_xml=table,
            width=body_w,
            height=framed_h,
            n_cols=3,
            terminal=terminal,
            fill="Color/Paper",
            stroke="Color/HB Line K40",
            corner_fills={
                "top_left": "Color/HB Bg K05",
                "bottom_left": "Color/HB Bg K05",
                "top_right": "Color/Paper",
                "bottom_right": "Color/Paper",
            },
        )
    else:
        table_xml = wrap_table_paragraph(table, terminal, span_columns)
    return art + table_xml, 70.0 + 12.0 * row_index


def _compact_lines(text: str, width: float, *, size: float) -> int:
    """Estimate wraps in the reference's deliberately narrow table cells."""
    shared_estimate = _estimated_lines(text, width, size=size)
    compact_estimate = sum(
        max(
            1,
            ceil(
                sum(
                    1.0 if east_asian_width(char) in {"W", "F"} else 0.52
                    for char in line.strip()
                )
                * size
                / max(1.0, width)
            ),
        )
        for line in text.splitlines() or [""]
    )
    return max(shared_estimate, compact_estimate)


def _editable_lcdmode_panel(
    spec: dict,
    ctx: RenderContext,
    *,
    tid: str,
    terminal: bool,
    body_w: float,
    asset,
) -> tuple[str, float]:
    """Compose the reference LCD art and its movable three-column copy."""
    scale = min(1.0, max(0.65, body_w / _REFERENCE_MEASURE))
    geometry = _reference_geometry(ctx.language)
    panel_width = _REFERENCE_PANEL_WIDTH * scale
    visible_art_height = _REFERENCE_ART_HEIGHT * scale

    table_left = 140.04 * scale
    if geometry is not None:
        state_w, action_w, description_w = (
            width * scale for width in geometry.column_widths
        )
    else:
        # Non-governed locales keep the editable side-by-side composition, but
        # size its columns from the portable component tokens and let copy grow
        # the rows below.  Never silently inherit EN's measured fixed geometry.
        generic_table_width = panel_width - table_left - 6.0 * scale
        preferred_state = max(
            12.0 * scale,
            param_pt(ctx.params, "comp_lcd_mode_state_col_width", 59.53) * scale,
        )
        preferred_action = max(
            12.0 * scale,
            param_pt(ctx.params, "comp_lcd_mode_action_col_width", 42.52) * scale,
        )
        minimum_description = 30.0 * scale
        available_labels = max(
            24.0 * scale,
            generic_table_width - minimum_description,
        )
        preferred_labels = preferred_state + preferred_action
        label_scale = min(1.0, available_labels / preferred_labels)
        state_w = preferred_state * label_scale
        action_w = preferred_action * label_scale
        description_w = generic_table_width - state_w - action_w
    state_right = table_left + state_w
    action_right = state_right + action_w
    table_right = action_right + description_w

    state_size = 5.25
    state_leading = 5.8
    action_size = 5.0
    action_leading = 6.0
    description_size = 4.5
    description_leading = 4.5
    row_minima = (14.5 * scale, 9.5 * scale, 23.5 * scale)

    groups: list[dict[str, object]] = []
    for raw_group in spec.get("groups", []):
        actions: list[tuple[str, str]] = []
        for raw_action in raw_group.get("actions", []):
            if isinstance(raw_action, (list, tuple)) and len(raw_action) >= 2:
                actions.append((str(raw_action[0]), str(raw_action[1])))
        if actions:
            groups.append({
                "state": str(raw_group.get("state", "")),
                "actions": actions,
            })

    reference_six_rows = (
        geometry is not None
        and len(groups) == 2
        and all(
            isinstance(group["actions"], list)
            and len(group["actions"]) == 3
            for group in groups
        )
    )
    row_heights: list[list[float]] = []
    if reference_six_rows:
        measured = [height * scale for height in geometry.row_heights]
        row_heights = [measured[:3], measured[3:]]
        panel_height = geometry.panel_height * scale
        table_top = -panel_height + geometry.table_top_margin * scale
        art_top = -panel_height + geometry.art_top_margin * scale
    else:
        for group in groups:
            heights = []
            actions = group["actions"]
            assert isinstance(actions, list)
            for action_index, (action, description) in enumerate(actions):
                action_lines = _compact_lines(
                    action,
                    max(8.0, action_w - 5.0),
                    size=action_size,
                )
                description_lines = _compact_lines(
                    description,
                    max(12.0, table_right - action_right - 6.0),
                    size=description_size,
                )
                copy_height = max(
                    action_lines * action_leading,
                    description_lines * description_leading,
                ) + 3.0
                minimum = row_minima[min(action_index, len(row_minima) - 1)]
                heights.append(max(minimum, copy_height))

            state = str(group["state"])
            state_height = (
                _compact_lines(
                    state,
                    max(10.0, state_w - 9.0),
                    size=state_size,
                )
                * state_leading
                + 4.0
            )
            if heights and sum(heights) < state_height:
                extra = (state_height - sum(heights)) / len(heights)
                heights = [height + extra for height in heights]
            row_heights.append(heights)

        dynamic_table_height = sum(
            height for group in row_heights for height in group
        )
        vertical_padding = 8.0 * scale
        panel_height = max(
            dynamic_table_height + 2.0 * vertical_padding,
            visible_art_height + 26.0 * scale,
        )
        table_top = -panel_height + (
            panel_height - dynamic_table_height
        ) / 2.0
        art_top = -panel_height + (panel_height - visible_art_height) / 2.0

    table_height = sum(height for group in row_heights for height in group)
    table_bottom = table_top + table_height
    art_w, art_h, art_left, art_bottom = _compensated_art_placement(
        scale=scale,
        visible_top=art_top,
    )

    dark = "Color/HB Brand Dark"
    line_weight = 0.55 * scale
    shapes = [
        _panel_bounds(tid, panel_width, panel_height),
        _positioned_image(
            f"lcdmode_art_{tid}",
            asset,
            art_w,
            art_h,
            left=art_left,
            bottom=art_bottom,
        ),
        _shape(
            shape_id=f"lcdmode_table_bg_{tid}",
            left=table_left,
            top=table_top,
            right=table_right,
            bottom=table_bottom,
            radius=4.2 * scale,
            fill="Color/Paper",
            stroke=dark,
            stroke_weight=0.8 * scale,
        ),
    ]
    text_layers: list[str] = []
    row_top = table_top
    for group_index, (group, heights) in enumerate(zip(groups, row_heights)):
        group_top = row_top
        group_bottom = group_top + sum(heights)
        shapes.append(_shape(
            shape_id=f"lcdmode_state_bg_{group_index}_{tid}",
            left=table_left + line_weight,
            top=group_top + line_weight,
            right=state_right - line_weight / 2.0,
            bottom=group_bottom - line_weight,
            fill="Color/HB Bg K05",
        ))
        text_layers.append(_editable_text_frame(
            ctx,
            story_id=f"st_anchor_lcdmode_state_{group_index}_{tid}",
            frame_id=f"tf_lcdmode_state_{group_index}_{tid}",
            title=f"{tid} LCD state {group_index + 1}",
            parts=[_sized_psr(
                "HB Spec Label",
                str(group["state"]),
                size=state_size,
                leading=state_leading,
                terminal=True,
            )],
            left=table_left,
            top=group_top,
            right=state_right,
            bottom=group_bottom,
            inset=(2.0, 5.0, 2.0, 4.0),
            valign="CenterAlign",
        ))

        actions = group["actions"]
        assert isinstance(actions, list)
        for action_index, ((action, description), row_height) in enumerate(
            zip(actions, heights)
        ):
            row_bottom = row_top + row_height
            text_layers.extend([
                _editable_text_frame(
                    ctx,
                    story_id=(
                        f"st_anchor_lcdmode_action_{group_index}_"
                        f"{action_index}_{tid}"
                    ),
                    frame_id=(
                        f"tf_lcdmode_action_{group_index}_"
                        f"{action_index}_{tid}"
                    ),
                    title=(
                        f"{tid} LCD action {group_index + 1}."
                        f"{action_index + 1}"
                    ),
                    parts=[_sized_psr(
                        "HB Spec Label",
                        action,
                        size=action_size,
                        leading=action_leading,
                        terminal=True,
                    )],
                    left=state_right,
                    top=row_top,
                    right=action_right,
                    bottom=row_bottom,
                    inset=(1.5, 3.0, 1.5, 2.0),
                    valign="CenterAlign",
                ),
                _editable_text_frame(
                    ctx,
                    story_id=(
                        f"st_anchor_lcdmode_description_{group_index}_"
                        f"{action_index}_{tid}"
                    ),
                    frame_id=(
                        f"tf_lcdmode_description_{group_index}_"
                        f"{action_index}_{tid}"
                    ),
                    title=(
                        f"{tid} LCD description {group_index + 1}."
                        f"{action_index + 1}"
                    ),
                    parts=[_sized_psr(
                        "HB Spec Value",
                        description,
                        size=description_size,
                        leading=description_leading,
                        terminal=True,
                    )],
                    left=action_right,
                    top=row_top,
                    right=table_right,
                    bottom=row_bottom,
                    # The compact 4.25pt localized copy needs the complete
                    # measured row height.  Horizontal padding remains, while
                    # zero vertical inset avoids consuming one extra baseline
                    # in FR/ES fixed-height frames during native import.
                    inset=(0.0, 3.5, 0.0, 2.5),
                    valign="CenterAlign",
                ),
            ])
            row_top = row_bottom
            if action_index < len(heights) - 1:
                shapes.append(_shape(
                    shape_id=(
                        f"lcdmode_row_rule_{group_index}_"
                        f"{action_index}_{tid}"
                    ),
                    left=state_right,
                    top=row_top - line_weight / 2.0,
                    right=table_right,
                    bottom=row_top + line_weight / 2.0,
                    fill=dark,
                ))

        if group_index < len(groups) - 1:
            shapes.append(_shape(
                shape_id=f"lcdmode_group_rule_{group_index}_{tid}",
                left=table_left,
                top=row_top - line_weight / 2.0,
                right=table_right,
                bottom=row_top + line_weight / 2.0,
                fill=dark,
            ))

    shapes.extend([
        _shape(
            shape_id=f"lcdmode_state_rule_{tid}",
            left=state_right - line_weight / 2.0,
            top=table_top,
            right=state_right + line_weight / 2.0,
            bottom=table_bottom,
            fill=dark,
        ),
        _shape(
            shape_id=f"lcdmode_action_rule_{tid}",
            left=action_right - line_weight / 2.0,
            top=table_top,
            right=action_right + line_weight / 2.0,
            bottom=table_bottom,
            fill=dark,
        ),
        # Redraw the rounded outline last among the underlays so every square
        # grid/fill edge terminates cleanly at the approved outer silhouette.
        _shape(
            shape_id=f"lcdmode_table_outline_{tid}",
            left=table_left,
            top=table_top,
            right=table_right,
            bottom=table_bottom,
            radius=4.2 * scale,
            stroke=dark,
            stroke_weight=0.8 * scale,
        ),
    ])

    xml, estimated_height = _special_panel_paragraph(
        ctx,
        tid=tid,
        title="LCD screen operation panel",
        group_content="".join(shapes) + "".join(text_layers),
        width=panel_width,
        height=panel_height,
        terminal=terminal,
        space_after=(
            geometry.space_after * scale
            if geometry is not None
            else param_pt(ctx.params, "comp_data_table_after", 3.4)
        ),
        anchor_x_offset=0.0,
    )
    space_before = (
        geometry.space_before * scale
        if geometry is not None
        else param_pt(ctx.params, "comp_data_table_before", 3.4)
    )
    first_line_indent = (
        geometry.left_indent * scale - ctx.inline_origin_shift
        if geometry is not None
        else -ctx.inline_origin_shift
    )
    paragraph_attrs = (
        'LeftIndent="0" '
        f'FirstLineIndent="{first_line_indent:g}" '
        f'SpaceBefore="{space_before:g}"'
    )
    xml = xml.replace(
        "<ParagraphStyleRange ",
        f"<ParagraphStyleRange {paragraph_attrs} ",
        1,
    )
    return xml, estimated_height + space_before


def render_lcdmode(
    spec: dict,
    ctx: RenderContext,
    *,
    tid: str,
    terminal: bool,
    span_columns: bool = True,
    measure_w: float | None = None,
) -> tuple[str, float]:
    """Render the reference LCD panel, with a portable table fallback."""
    body_w = measure_w or ctx.text_measure
    img_ref = str(spec.get("img", "")).strip()
    asset = ctx.resolve_bundle_image(img_ref) if img_ref else None
    if ctx.add_story is None or asset is None or not asset.exists():
        return _fallback_lcdmode(
            spec,
            ctx,
            tid=tid,
            terminal=terminal,
            span_columns=span_columns,
            body_w=body_w,
        )
    return _editable_lcdmode_panel(
        spec,
        ctx,
        tid=tid,
        terminal=terminal,
        body_w=body_w,
        asset=asset,
    )
