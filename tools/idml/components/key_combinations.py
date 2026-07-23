"""Editable KEY COMBINATION panel matching the approved manual artwork.

The source stays a three-column list-table.  Production IDML replaces only the
visual treatment: linked button/clock assets and native grid shapes sit below
independent text frames, so every caption, plus sign, duration, instruction,
and function remains movable and editable in InDesign.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil, isfinite
from pathlib import Path
import re
import unicodedata

from .. import page_objects
from ..character_metrics import with_character_baseline_shift
from ..params import component_param_pt
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
KEY_STYLE_BASE_TOKENS = (
    "idml_key_panel_width",
    "comp_key_table_left_ratio",
    "comp_key_table_middle_ratio",
    "idml_key_header_height",
    "idml_key_panel_height",
    "idml_key_panel_left_indent",
    "idml_key_panel_space_before",
    "idml_key_visual_raise",
    "idml_key_inner_rule",
    "idml_key_outer_rule",
    "idml_key_outer_radius",
    "idml_key_button_size",
    "idml_key_clock_size",
    "type_data_table_header_font_size",
    "idml_key_header_font_leading",
    "idml_key_caption_font_size",
    "idml_key_caption_font_leading",
    "idml_key_plus_font_size",
    "idml_key_plus_font_leading",
    "idml_key_duration_font_size",
    "idml_key_duration_font_leading",
    "idml_key_operation_font_size",
    "idml_key_operation_font_leading",
    "idml_key_function_font_size",
    "idml_key_function_font_leading",
)
KEY_STYLE_LOCALE_TOKENS = (
    "idml_key_panel_height",
    "idml_key_panel_left_indent",
    "idml_key_panel_space_before",
    "idml_key_visual_raise",
)


@dataclass(frozen=True)
class KeyCombinationStyle:
    """Shared, token-driven visual contract for the editable component."""

    panel_width: float
    left_ratio: float
    middle_ratio: float
    header_height: float
    governed_panel_height: float | None
    left_indent: float
    space_before: float
    visual_raise: float
    inner_rule: float
    outer_rule: float
    radius: float
    button_size: float
    clock_size: float
    header_size: float
    header_leading: float
    caption_size: float
    caption_leading: float
    plus_size: float
    plus_leading: float
    duration_size: float
    duration_leading: float
    operation_size: float
    operation_leading: float
    function_size: float
    function_leading: float

    def validate(self, *, available: float) -> None:
        """Fail closed when shared style tokens cannot form valid geometry."""
        positive = {
            "available width": available,
            "idml_key_panel_width": self.panel_width,
            "idml_key_header_height": self.header_height,
            "idml_key_button_size": self.button_size,
            "idml_key_clock_size": self.clock_size,
            "type_data_table_header_font_size": self.header_size,
            "idml_key_header_font_leading": self.header_leading,
            "idml_key_caption_font_size": self.caption_size,
            "idml_key_caption_font_leading": self.caption_leading,
            "idml_key_plus_font_size": self.plus_size,
            "idml_key_plus_font_leading": self.plus_leading,
            "idml_key_duration_font_size": self.duration_size,
            "idml_key_duration_font_leading": self.duration_leading,
            "idml_key_operation_font_size": self.operation_size,
            "idml_key_operation_font_leading": self.operation_leading,
            "idml_key_function_font_size": self.function_size,
            "idml_key_function_font_leading": self.function_leading,
        }
        if self.governed_panel_height is not None:
            positive["idml_key_panel_height"] = self.governed_panel_height
        for name, value in positive.items():
            if not isfinite(value) or value <= 0:
                raise ValueError(
                    f"key_combinations style {name} must be a finite positive value"
                )

        for name, value in {
            "idml_key_inner_rule": self.inner_rule,
            "idml_key_outer_rule": self.outer_rule,
            "idml_key_outer_radius": self.radius,
            "idml_key_panel_space_before": self.space_before,
            "idml_key_visual_raise": self.visual_raise,
        }.items():
            if not isfinite(value) or value < 0:
                raise ValueError(
                    f"key_combinations style {name} must be finite and non-negative"
                )
        if not isfinite(self.left_indent):
            raise ValueError(
                "key_combinations style idml_key_panel_left_indent must be finite"
            )
        if not 0 < self.left_ratio < 1:
            raise ValueError(
                "key_combinations style comp_key_table_left_ratio must be between 0 and 1"
            )
        if not 0 < self.middle_ratio < 1:
            raise ValueError(
                "key_combinations style comp_key_table_middle_ratio must be between 0 and 1"
            )
        if self.left_ratio + self.middle_ratio >= 1:
            raise ValueError(
                "key_combinations column ratios must leave a positive function column"
            )
        if (
            self.governed_panel_height is not None
            and self.governed_panel_height <= self.header_height
        ):
            raise ValueError(
                "key_combinations panel height must exceed its header height"
            )

    @classmethod
    def from_context(cls, ctx: RenderContext) -> KeyCombinationStyle:
        """Resolve one base style plus the governed locale geometry."""
        language = _language_code(ctx.language)

        def token(key: str, default: float) -> float:
            return component_param_pt(
                ctx.params, key, default,
                strict=ctx.strict_component_assets,
                owner="key_combinations",
            )

        def localized(key: str, default: float) -> float:
            base = token(key, default)
            if language not in {"fr", "es"}:
                return base
            return token(f"lang_{language}_{key}", base)

        governed = language in {"en", "fr", "es"}
        return cls(
            panel_width=token("idml_key_panel_width", 311.02),
            left_ratio=token(
                "comp_key_table_left_ratio", 128.49 / 311.02,
            ),
            middle_ratio=token(
                "comp_key_table_middle_ratio", 90.70 / 311.02,
            ),
            header_height=token("idml_key_header_height", 14.71),
            governed_panel_height=(
                localized("idml_key_panel_height", 152.92)
                if governed else None
            ),
            left_indent=(
                localized("idml_key_panel_left_indent", -4.34)
                if governed else 0.0
            ),
            space_before=(
                localized("idml_key_panel_space_before", 10.62)
                if governed
                else token("comp_data_table_before", 3.4)
            ),
            visual_raise=(
                localized("idml_key_visual_raise", 36.68)
                if governed else 0.0
            ),
            inner_rule=token("idml_key_inner_rule", 0.5),
            outer_rule=token("idml_key_outer_rule", 0.566),
            radius=token("idml_key_outer_radius", 8.0),
            button_size=token("idml_key_button_size", 22.08),
            clock_size=token("idml_key_clock_size", 10.45),
            header_size=token("type_data_table_header_font_size", 6.6),
            header_leading=token("idml_key_header_font_leading", 7.2),
            caption_size=token("idml_key_caption_font_size", 5.1),
            caption_leading=token("idml_key_caption_font_leading", 5.8),
            plus_size=token("idml_key_plus_font_size", 12.0),
            plus_leading=token("idml_key_plus_font_leading", 12.0),
            duration_size=token("idml_key_duration_font_size", 7.0),
            duration_leading=token("idml_key_duration_font_leading", 7.6),
            operation_size=token("idml_key_operation_font_size", 5.35),
            operation_leading=token("idml_key_operation_font_leading", 6.4),
            function_size=token("idml_key_function_font_size", 6.0),
            function_leading=token("idml_key_function_font_leading", 8.5),
        )

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


def _language_code(language: str | None) -> str:
    """Return the normalized primary language subtag."""
    normalized = (language or "").strip().lower().replace("_", "-")
    return normalized.split("-", 1)[0]


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
    missing: list[str] = []
    for name in sorted(names):
        asset = ctx.resolve_bundle_image(name)
        if asset is None or not asset.is_file():
            missing.append(name)
        else:
            resolved[name] = asset
    if missing:
        if ctx.strict_component_assets:
            raise ValueError(
                "key_combinations missing required component assets: "
                + ", ".join(missing)
            )
        return None
    return (
        tuple(
            (resolved[left_name], resolved[right_name])
            for left_name, right_name in _BUTTON_ASSETS
        ),
        resolved["icon_clock_3s.png"],
    )


def _row_height(
    row: list,
    first_w: float,
    middle_w: float,
    function_w: float,
    style: KeyCombinationStyle,
    scale: float,
) -> float:
    caption_size = style.caption_size * scale
    caption_leading = style.caption_leading * scale
    operation_size = style.operation_size * scale
    operation_leading = style.operation_leading * scale
    function_size = style.function_size * scale
    function_leading = style.function_leading * scale
    left, right = _split_button_labels(row[0])
    label_slot = first_w * 0.43
    label_lines = max(
        _line_count(left, label_slot, size=caption_size),
        _line_count(right, label_slot, size=caption_size),
    )
    operation_lines = _line_count(
        _plain(row[1]), middle_w - 11.0 * scale, size=operation_size,
    )
    function_lines = _line_count(
        _plain(row[2]), function_w - 10.0 * scale, size=function_size,
    )
    return max(
        34.5 * scale,
        26.4 * scale + label_lines * caption_leading,
        19.0 * scale + operation_lines * operation_leading,
        8.0 * scale + function_lines * function_leading,
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

    # Measured from physical PDF pages 13/31/49. All editions consume the same
    # tokenized horizontal skeleton; governed locales add only localized
    # height/position overrides from that shared style contract.
    style = KeyCombinationStyle.from_context(ctx)
    available = measure_w if measure_w is not None else ctx.text_measure
    style.validate(available=available)
    scale = min(1.0, available / style.panel_width)

    def scaled(value: float) -> float:
        return value * scale

    width = style.panel_width * scale
    first_w = width * style.left_ratio
    middle_w = width * style.middle_ratio
    function_w = width - first_w - middle_w
    header_h = style.header_height * scale
    rows = raw_rows[1:5]
    if style.governed_panel_height is not None:
        height = style.governed_panel_height * scale
        body_row_height = (height - header_h) / len(rows)
        row_heights = [body_row_height] * len(rows)
        left_indent = style.left_indent * scale - ctx.inline_origin_shift
        space_before = style.space_before * scale
    else:
        row_heights = [
            _row_height(row, first_w, middle_w, function_w, style, scale)
            for row in rows
        ]
        height = header_h + sum(row_heights)
        left_indent = 0.0
        space_before = style.space_before * scale
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
    line = style.inner_rule * scale
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

    button_size = style.button_size * scale
    button_lefts = (first_w * 0.253 - button_size / 2.0,
                    first_w * 0.730 - button_size / 2.0)
    plus_center = first_w * 0.484
    clock_size = style.clock_size * scale
    for index, (row_top, row_h, assets) in enumerate(
        zip(row_tops, row_heights, button_assets)
    ):
        icon_top = row_top + scaled(2.2)
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
            left=first_w + scaled(0.93),
            bottom=row_top + scaled(4.0) + clock_size,
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
                "HB Data Header", header, size=scaled(style.header_size),
                leading=scaled(style.header_leading),
                terminal=True,
            )],
            left=left + scaled(6.5),
            top=top + scaled(1.0),
            right=right - scaled(3.0),
            bottom=top + header_h - scaled(1.0),
            valign="CenterAlign",
        ))

    for index, (row, row_top, row_h) in enumerate(
        zip(rows, row_tops, row_heights)
    ):
        row_bottom = row_top + row_h
        labels = _split_button_labels(row[0])
        caption_ranges = (
            (scaled(3.0), first_w * 0.49),
            (first_w * 0.51, first_w - scaled(3.0)),
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
                    "HB Data Body", label, size=scaled(style.caption_size),
                    leading=scaled(style.caption_leading),
                    terminal=True, justification="CenterAlign",
                )],
                left=left,
                top=row_top + scaled(24.0),
                right=right,
                bottom=row_bottom - scaled(1.5),
                valign="CenterAlign",
            ))
        text_layers.append(_editable_text_frame(
            ctx,
            story_id=f"st_anchor_key_plus_{index}_{tid}",
            frame_id=f"tf_key_plus_{index}_{tid}",
            title=f"{tid} key row {index + 1} plus",
            parts=[_sized_psr(
                "HB Title L2", "+", size=scaled(style.plus_size),
                leading=scaled(style.plus_leading),
                terminal=True, justification="CenterAlign",
            )],
            left=plus_center - scaled(8.0),
            top=row_top + scaled(5.5),
            right=plus_center + scaled(8.0),
            bottom=row_top + scaled(21.0),
            valign="CenterAlign",
        ))
        text_layers.append(_editable_text_frame(
            ctx,
            story_id=f"st_anchor_key_duration_{index}_{tid}",
            frame_id=f"tf_key_duration_{index}_{tid}",
            title=f"{tid} key row {index + 1} duration",
            parts=[_sized_psr(
                "HB Data Body", _duration(row[1]), size=scaled(style.duration_size),
                leading=scaled(style.duration_leading),
                terminal=True,
            )],
            left=first_w + scaled(12.4),
            top=row_top + scaled(3.0),
            right=first_w + scaled(31.0),
            bottom=row_top + scaled(15.0),
            valign="CenterAlign",
        ))
        text_layers.append(_editable_text_frame(
            ctx,
            story_id=f"st_anchor_key_operation_{index}_{tid}",
            frame_id=f"tf_key_operation_{index}_{tid}",
            title=f"{tid} key row {index + 1} operation",
            parts=[_sized_psr(
                "HB Data Body", _plain(row[1]), size=scaled(style.operation_size),
                leading=scaled(style.operation_leading),
                terminal=True,
            )],
            left=first_w + scaled(5.5),
            top=row_top + scaled(16.0),
            right=x2 - scaled(3.0),
            bottom=row_bottom - scaled(1.5),
            valign="CenterAlign",
        ))
        text_layers.append(_editable_text_frame(
            ctx,
            story_id=f"st_anchor_key_function_{index}_{tid}",
            frame_id=f"tf_key_function_{index}_{tid}",
            title=f"{tid} key row {index + 1} function",
            parts=[_sized_psr(
                "HB Data Body", _plain(row[2]), size=scaled(style.function_size),
                leading=scaled(style.function_leading),
                terminal=True,
            )],
            left=x2 + scaled(5.0),
            top=row_top + scaled(2.0),
            right=width - scaled(4.0),
            bottom=row_bottom - scaled(2.0),
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
        stroke_weight=style.outer_rule * scale,
        radius=style.radius * scale,
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
    if style.visual_raise:
        xml = with_character_baseline_shift(xml, shift=style.visual_raise)
    # The caller adds only the common trailing table gap. This estimate owns
    # the locale-specific leading gap together with the panel itself.
    return xml, height + space_before
