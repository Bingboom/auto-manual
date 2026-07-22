"""Localized vertical rhythm for flowed operation-story headings."""
from __future__ import annotations

import json

from .components.prose_table import body_data_table_kind
from .oppanel import operation_story_rhythm


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
) -> tuple[str | None, float | None]:
    """Return base operation rhythm with localized LCD/Key overrides."""
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
        before = _KEY_HEADING_BEFORE[page_language]
        return f'SpaceBefore="{before:g}"', before
    if title and "operation_guide" in title and kind == "body" and next_block[0] == "h2":
        # Keep one clear line between the POWER/standby tail and next heading.
        return 'SpaceAfter="7.5"', 7.5
    return attrs, spacing
