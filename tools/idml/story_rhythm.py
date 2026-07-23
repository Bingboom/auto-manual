"""Localized vertical rhythm for flowed operation-story headings."""
from __future__ import annotations

import json

from .components.prose_table import body_data_table_kind
from .oppanel import operation_story_rhythm
from .params import param_pt


_LCD_HEADING_BEFORE = {"en": 0.41, "fr": 9.11, "es": 1.5}
_KEY_HEADING_BEFORE = {"en": 11.8, "fr": 20.9, "es": 35.2}


def _next_operation_heading(
    kind: str,
    next_block: tuple[str, str],
) -> str | None:
    """Classify an H2 by the LCD or Key object that immediately follows."""
    if kind != "h2":
        return None
    next_kind, payload = next_block
    if next_kind == "component":
        try:
            next_spec = json.loads(payload)
        except (TypeError, json.JSONDecodeError):
            next_spec = {}
        return "lcd" if next_spec.get("kind") == "lcdmode" else None
    if next_kind == "table":
        try:
            next_rows = json.loads(payload)
        except (TypeError, json.JSONDecodeError):
            next_rows = []
        if body_data_table_kind(next_rows) == "key_combinations":
            return "key"
    return None


def operation_story_rhythm_for_next_block(
    kind: str,
    next_block: tuple[str, str],
    page_language: str | None,
    *,
    title: str | None = None,
    intro_lines: int | None,
    energy_panel_height: float | None,
    baseline_panel_height: float,
    params: dict[str, tuple[str, str]] | None = None,
    first_operation_h2: bool = False,
) -> tuple[str | None, float | None]:
    """Return base operation rhythm with localized LCD/Key overrides."""
    normalized_language = (page_language or "en").split("-", 1)[0]
    rhythm_params = params or {}
    heading = _next_operation_heading(kind, next_block)
    attrs, spacing = operation_story_rhythm(
        kind,
        intro_lines=intro_lines,
        energy_panel_height=energy_panel_height,
        baseline_panel_height=baseline_panel_height,
    )
    if heading == "lcd" and page_language in _LCD_HEADING_BEFORE:
        before = _LCD_HEADING_BEFORE[page_language]
        return f'SpaceBefore="{before:g}"', before
    if heading == "key" and page_language in _KEY_HEADING_BEFORE:
        # The first-page calibration adds real story depth. InDesign carries
        # that depth through the linked four-page story even though the
        # intervening semantic breaks pin page starts. Counter it once at the
        # final Key heading so the approved fourth-page composition remains
        # stable and the editable panel does not move below trim.
        first_before = param_pt(
            rhythm_params,
            f"lang_{normalized_language}_idml_operation_first_h2_space_before",
            param_pt(
                rhythm_params,
                "idml_operation_first_h2_space_before",
                7.5,
            ),
        )
        inter_after = param_pt(
            rhythm_params,
            f"lang_{normalized_language}_idml_operation_inter_section_space_after",
            param_pt(
                rhythm_params,
                "idml_operation_inter_section_space_after",
                48.2,
            ),
        )
        added_story_depth = first_before + inter_after - 7.5
        before = _KEY_HEADING_BEFORE[page_language] - added_story_depth
        return f'SpaceBefore="{before:g}"', before
    if title and "operation_guide" in title and first_operation_h2 and kind == "h2":
        before = param_pt(
            rhythm_params,
            f"lang_{normalized_language}_idml_operation_first_h2_space_before",
            param_pt(
                rhythm_params,
                "idml_operation_first_h2_space_before",
                7.5,
            ),
        )
        attrs = f'SpaceBefore="{before:g}"'
        return attrs, before
    if title and "operation_guide" in title and kind == "body" and next_block[0] == "h2":
        # The approved first operation page deliberately holds the second
        # panel near the foot. Locale-specific copy density changes the gap,
        # but the semantic body-to-heading relationship is shared.
        after = param_pt(
            rhythm_params,
            f"lang_{normalized_language}_idml_operation_inter_section_space_after",
            param_pt(
                rhythm_params,
                "idml_operation_inter_section_space_after",
                48.2,
            ),
        )
        return f'SpaceAfter="{after:g}"', after
    return attrs, spacing


def operation_key_visual_raise(
    kind: str,
    next_block: tuple[str, str],
    page_language: str | None,
    params: dict[str, tuple[str, str]],
) -> float:
    """Return the non-flowing raise shared by the final Key heading/panel."""
    if _next_operation_heading(kind, next_block) != "key":
        return 0.0
    language = (page_language or "en").split("-", 1)[0]
    return param_pt(
        params,
        f"lang_{language}_idml_key_visual_raise",
        param_pt(params, "idml_key_visual_raise", 36.68),
    )
