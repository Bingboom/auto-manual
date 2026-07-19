"""Editable KEY COMBINATION panel matching the approved manual artwork.

The source stays a three-column list-table.  Production IDML replaces only the
visual treatment: linked button/clock assets and native grid shapes sit below
independent text frames, so every caption, plus sign, duration, instruction,
and function remains movable and editable in InDesign.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from pathlib import Path
import re
import unicodedata

from .. import page_objects
from ..params import param_pt
from ..primitives import psr
from .base import RenderContext
from .oppanel import (
    _editable_text_frame,
    _positioned_image,
    _shape,
    _sized_psr,
)


_BUTTON_ASSETS = (
    ("button_power.png", "button_ac.png"),
    ("button_power.png", "button_dc_usb.png"),
    ("button_dc_usb.png", "button_ac.png"),
    ("button_power.png", "button_led.png"),
)

_REFERENCE_PANEL_WIDTH = 311.02
_REFERENCE_COLUMN_WIDTHS = (128.49, 90.70, 91.83)
_REFERENCE_HEADER_HEIGHT = 14.71


@dataclass(frozen=True)
class _ReferenceGeometry:
    """Measured KEY COMBINATIONS geometry from reference pages 13/31/49."""

    panel_height: float
    left_indent: float
    space_before: float


_REFERENCE_GEOMETRY = {
    "en": _ReferenceGeometry(
        panel_height=152.92,
        left_indent=-4.34,
        space_before=10.62,
    ),
    "fr": _ReferenceGeometry(
        panel_height=167.06,
        left_indent=-1.42,
        space_before=3.53,
    ),
    "es": _ReferenceGeometry(
        panel_height=166.70,
        left_indent=-2.83,
        space_before=4.14,
    ),
}

_BUTTON_PAIR_ORDER = (
    ("main_power", "ac"),
    ("main_power", "dc_usb"),
    ("dc_usb", "ac"),
    ("main_power", "led"),
)
_GOVERNED_BUTTON_TOKEN_RULES = {
    "main_power": (
        frozenset({"main", "power"}),
        frozenset({"power", "principal"}),
        frozenset({"alimentation", "principal"}),
        frozenset({"encendido", "principal"}),
        frozenset({"energia", "principal"}),
    ),
    "ac": (frozenset({"ac"}), frozenset({"ca"})),
    "dc_usb": (
        frozenset({"dc", "usb"}),
        frozenset({"cc", "usb"}),
    ),
    "led": (frozenset({"led"}),),
}


def _plain(text: object) -> str:
    """Remove inline-emphasis markers that must not appear in frame copy."""
    return str(text).replace("**", "").strip()


def _button_kind(text: object) -> str | None:
    """Map one localized governed button label to its asset role."""
    folded = unicodedata.normalize("NFKD", _plain(text).casefold())
    tokens = frozenset(re.findall(
        r"[a-z0-9]+",
        "".join(char for char in folded if not unicodedata.combining(char)),
    ))
    matches = [
        kind
        for kind, rules in _GOVERNED_BUTTON_TOKEN_RULES.items()
        if any(rule <= tokens for rule in rules)
    ]
    return matches[0] if len(matches) == 1 else None


def _reference_geometry(language: str | None) -> _ReferenceGeometry | None:
    """Use fixed measurements only for an explicitly governed locale."""
    normalized = (language or "").strip().lower().replace("_", "-")
    language_code = normalized.split("-", 1)[0]
    return _REFERENCE_GEOMETRY.get(language_code)


def is_key_combinations_rows(raw_rows: list[list]) -> bool:
    """Recognize the governed four button pairs without header-language coupling."""
    if (
        len(raw_rows) != 5
        or any(len(row) != 3 for row in raw_rows)
        or any(not _plain(cell) for row in raw_rows for cell in row)
    ):
        return False
    pairs: list[tuple[str | None, str | None]] = []
    for row in raw_rows[1:]:
        buttons = _plain(row[0])
        if buttons.count("+") != 1:
            return False
        left, right = _split_button_labels(buttons)
        pairs.append((_button_kind(left), _button_kind(right)))
    return tuple(pairs) == _BUTTON_PAIR_ORDER


def _split_button_labels(text: object) -> tuple[str, str]:
    parts = [_plain(part) for part in _plain(text).split("+", 1)]
    if len(parts) == 1:
        parts.append("")
    return parts[0], parts[1]


def _duration(text: object) -> str:
    match = re.search(r"\d+", _plain(text))
    return f"{match.group(0)}s" if match else ""


def _line_count(text: str, width: float, *, size: float) -> int:
    """Conservative glyph-width estimate tuned to the compact 5-6pt copy."""
    chars_per_line = max(12, int(width / (size * 0.48)))
    legacy_estimate = max(1, (len(text) + chars_per_line - 1) // chars_per_line)
    glyph_estimate = sum(
        max(
            1,
            ceil(
                sum(
                    0.0
                    if unicodedata.combining(char)
                    else 1.0
                    if unicodedata.east_asian_width(char) in {"W", "F"}
                    else 0.48
                    for char in line.strip()
                )
                * size
                / max(1.0, width)
            ),
        )
        for line in text.splitlines() or [""]
    )
    return max(legacy_estimate, glyph_estimate)


def _resolve_panel_assets(
    ctx: RenderContext,
) -> tuple[tuple[tuple[Path, Path], ...], Path] | None:
    """Resolve the complete governed asset set before emitting any stories.

    A partial panel is worse than the native editable-table fallback: skipped
    links leave blank button or duration slots while still passing missing-link
    preflight.  Treat the five unique files as one atomic visual dependency.
    """
    names = {
        asset_name
        for pair in _BUTTON_ASSETS
        for asset_name in pair
    }
    names.add("icon_clock_3s.png")
    resolved: dict[str, Path] = {}
    for name in sorted(names):
        asset = ctx.resolve_bundle_image(name)
        if asset is None or not asset.is_file():
            return None
        resolved[name] = asset
    return (
        tuple(
            (resolved[left_name], resolved[right_name])
            for left_name, right_name in _BUTTON_ASSETS
        ),
        resolved["icon_clock_3s.png"],
    )


def _row_height(row: list, first_w: float, middle_w: float,
                function_w: float) -> float:
    left, right = _split_button_labels(row[0])
    label_slot = first_w * 0.43
    label_lines = max(
        _line_count(left, label_slot, size=5.1),
        _line_count(right, label_slot, size=5.1),
    )
    operation_lines = _line_count(
        _plain(row[1]), middle_w - 11.0, size=5.35,
    )
    function_lines = _line_count(
        _plain(row[2]), function_w - 10.0, size=6.0,
    )
    return max(
        34.5,
        26.4 + label_lines * 5.8,
        19.0 + operation_lines * 6.4,
        8.0 + function_lines * 8.5,
    )


def render_key_combinations(
    raw_rows: list[list],
    ctx: RenderContext,
    *,
    tid: str,
    terminal: bool,
    measure_w: float | None = None,
) -> tuple[str, float]:
    """Render editable art; estimated height includes its leading flow gap."""
    if ctx.add_story is None or not is_key_combinations_rows(raw_rows):
        return "", 0.0
    resolved_assets = _resolve_panel_assets(ctx)
    if resolved_assets is None:
        return "", 0.0
    button_assets, clock_asset = resolved_assets

    # Measured from physical PDF pages 13/31/49. Keep all editions on the
    # same horizontal skeleton, while the governed locales use their exact
    # reference panel heights and vertical positions.
    available = measure_w or ctx.text_measure
    scale = min(1.0, available / _REFERENCE_PANEL_WIDTH)
    width = _REFERENCE_PANEL_WIDTH * scale
    first_w, middle_w, function_w = (
        column_width * scale for column_width in _REFERENCE_COLUMN_WIDTHS
    )
    header_h = _REFERENCE_HEADER_HEIGHT * scale
    rows = raw_rows[1:5]
    geometry = _reference_geometry(ctx.language)
    if geometry is not None:
        height = geometry.panel_height * scale
        body_row_height = (height - header_h) / len(rows)
        row_heights = [body_row_height] * len(rows)
        left_indent = geometry.left_indent * scale - ctx.inline_origin_shift
        space_before = geometry.space_before * scale
    else:
        row_heights = [
            _row_height(row, first_w, middle_w, function_w) for row in rows
        ]
        height = header_h + sum(row_heights)
        left_indent = 0.0
        space_before = param_pt(ctx.params, "comp_data_table_before", 3.4)
    top = -height
    x1 = first_w
    x2 = first_w + middle_w
    dark = "Color/HB Brand Dark"

    # Underlays and linked art are deliberately emitted before text layers.
    underlays: list[str] = [
        _shape(
            shape_id=f"key_first_col_bg_{tid}",
            left=0.0,
            top=top,
            right=first_w,
            bottom=0.0,
            fill="Color/HB Bg K05",
        ),
    ]
    line = 0.5
    for index, x in enumerate((x1, x2)):
        underlays.append(_shape(
            shape_id=f"key_vrule_{index}_{tid}",
            left=x - line / 2.0,
            top=top,
            right=x + line / 2.0,
            bottom=0.0,
            fill=dark,
        ))

    row_tops: list[float] = []
    cursor = top + header_h
    underlays.append(_shape(
        shape_id=f"key_hrule_header_{tid}",
        left=0.0,
        top=cursor - line / 2.0,
        right=width,
        bottom=cursor + line / 2.0,
        fill=dark,
    ))
    for index, row_h in enumerate(row_heights):
        row_tops.append(cursor)
        cursor += row_h
        if index < len(row_heights) - 1:
            underlays.append(_shape(
                shape_id=f"key_hrule_{index}_{tid}",
                left=0.0,
                top=cursor - line / 2.0,
                right=width,
                bottom=cursor + line / 2.0,
                fill=dark,
            ))

    button_size = 22.08
    button_lefts = (first_w * 0.253 - button_size / 2.0,
                    first_w * 0.730 - button_size / 2.0)
    plus_center = first_w * 0.484
    clock_size = 10.45
    for index, (row_top, row_h, assets) in enumerate(
        zip(row_tops, row_heights, button_assets)
    ):
        icon_top = row_top + 2.2
        for side, (left, asset) in enumerate(zip(button_lefts, assets)):
            underlays.append(_positioned_image(
                f"key_button_{index}_{side}_{tid}",
                asset,
                button_size,
                button_size,
                left=left,
                bottom=icon_top + button_size,
            ))
        underlays.append(_positioned_image(
            f"key_clock_{index}_{tid}",
            clock_asset,
            clock_size,
            clock_size,
            left=first_w + 0.93,
            bottom=row_top + 4.0 + clock_size,
        ))

    text_layers: list[str] = []
    headers = [_plain(cell) for cell in raw_rows[0][:3]]
    header_ranges = ((0.0, x1), (x1, x2), (x2, width))
    for index, (header, (left, right)) in enumerate(zip(headers, header_ranges)):
        text_layers.append(_editable_text_frame(
            ctx,
            story_id=f"st_anchor_key_header_{index}_{tid}",
            frame_id=f"tf_key_header_{index}_{tid}",
            title=f"{tid} key table header {index + 1}",
            parts=[_sized_psr(
                "HB Data Header", header, size=6.6, leading=7.2,
                terminal=True,
            )],
            left=left + 6.5,
            top=top + 1.0,
            right=right - 3.0,
            bottom=top + header_h - 1.0,
            valign="CenterAlign",
        ))

    for index, (row, row_top, row_h) in enumerate(
        zip(rows, row_tops, row_heights)
    ):
        row_bottom = row_top + row_h
        labels = _split_button_labels(row[0])
        caption_ranges = (
            (3.0, first_w * 0.49),
            (first_w * 0.51, first_w - 3.0),
        )
        for side, (label, (left, right)) in enumerate(
            zip(labels, caption_ranges)
        ):
            text_layers.append(_editable_text_frame(
                ctx,
                story_id=f"st_anchor_key_caption_{index}_{side}_{tid}",
                frame_id=f"tf_key_caption_{index}_{side}_{tid}",
                title=f"{tid} key row {index + 1} button {side + 1}",
                parts=[_sized_psr(
                    "HB Data Body", label, size=5.1, leading=5.8,
                    terminal=True, justification="CenterAlign",
                )],
                left=left,
                top=row_top + 24.0,
                right=right,
                bottom=row_bottom - 1.5,
                valign="CenterAlign",
            ))
        text_layers.append(_editable_text_frame(
            ctx,
            story_id=f"st_anchor_key_plus_{index}_{tid}",
            frame_id=f"tf_key_plus_{index}_{tid}",
            title=f"{tid} key row {index + 1} plus",
            parts=[_sized_psr(
                "HB Title L2", "+", size=12.0, leading=12.0,
                terminal=True, justification="CenterAlign",
            )],
            left=plus_center - 8.0,
            top=row_top + 5.5,
            right=plus_center + 8.0,
            bottom=row_top + 21.0,
            valign="CenterAlign",
        ))
        text_layers.append(_editable_text_frame(
            ctx,
            story_id=f"st_anchor_key_duration_{index}_{tid}",
            frame_id=f"tf_key_duration_{index}_{tid}",
            title=f"{tid} key row {index + 1} duration",
            parts=[_sized_psr(
                "HB Data Body", _duration(row[1]), size=7.0, leading=7.6,
                terminal=True,
            )],
            left=first_w + 12.4,
            top=row_top + 3.0,
            right=first_w + 31.0,
            bottom=row_top + 15.0,
            valign="CenterAlign",
        ))
        text_layers.append(_editable_text_frame(
            ctx,
            story_id=f"st_anchor_key_operation_{index}_{tid}",
            frame_id=f"tf_key_operation_{index}_{tid}",
            title=f"{tid} key row {index + 1} operation",
            parts=[_sized_psr(
                "HB Data Body", _plain(row[1]), size=5.35, leading=6.4,
                terminal=True,
            )],
            left=first_w + 5.5,
            top=row_top + 16.0,
            right=x2 - 3.0,
            bottom=row_bottom - 1.5,
            valign="CenterAlign",
        ))
        text_layers.append(_editable_text_frame(
            ctx,
            story_id=f"st_anchor_key_function_{index}_{tid}",
            frame_id=f"tf_key_function_{index}_{tid}",
            title=f"{tid} key row {index + 1} function",
            parts=[_sized_psr(
                "HB Data Body", _plain(row[2]), size=6.0, leading=8.5,
                terminal=True,
            )],
            left=x2 + 5.0,
            top=row_top + 2.0,
            right=width - 4.0,
            bottom=row_bottom - 2.0,
            valign="CenterAlign",
        ))

    empty = psr("HB Body", "", terminal=True)
    xml = page_objects.anchored_panel_group_paragraph(
        ctx.add_story,
        f"st_anchor_key_{tid}",
        "editable key combinations",
        [empty],
        width,
        height,
        terminal=terminal,
        fill="Color/Paper",
        stroke=dark,
        stroke_weight=0.566,
        radius=8.0,
        group_underlay="".join(underlays),
        group_overlay="".join(text_layers),
    )
    # InDesign normalizes the ItemTransform on an inline Group during native
    # import.  Keep the group's fixed construction transform and move its only
    # line through the host paragraph instead.  FirstLineIndent scopes the
    # locale adjustment to the anchored panel without changing later lines.
    xml = xml.replace(
        "<ParagraphStyleRange ",
        '<ParagraphStyleRange LeftIndent="0" '
        f'FirstLineIndent="{left_indent:g}" '
        f'SpaceBefore="{space_before:g}" ',
        1,
    )
    # The caller adds only the common trailing table gap. This estimate owns
    # the locale-specific leading gap together with the panel itself.
    return xml, height + space_before
