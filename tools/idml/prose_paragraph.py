"""Paragraph preparation shared by the main IDML story builder."""
from __future__ import annotations

from pathlib import Path

from .app_inline import prepare_app_body_inline


def build_text_paragraph(
    writer,
    *,
    kind: str,
    text: str,
    terminal: bool,
    is_preface: bool,
    has_twocol_layout: bool,
    in_twocol: bool,
    bundle_root: Path,
    page_language: str,
    story_id: str,
    block_index: int,
) -> tuple[str, str, bool, str]:
    """Return paragraph XML, semantic kind, h2 state, and measured text."""
    is_h2 = kind in {
        "h2",
        "h2_overview_front",
        "h2_overview_right",
        "h2_operation_energy",
        "h2_operation_led",
        "h2_charging_car",
    } or kind.startswith("h2_app")
    semantic_kind = "h2" if kind in {
        "h2_overview_front",
        "h2_overview_right",
        "h2_operation_energy",
        "h2_operation_led",
        "h2_charging_car",
    } else kind
    if kind in {
        "body_operation_energy_intro",
        "body_operation_inter_section",
    }:
        semantic_kind = "body"
    style = writer._PROSE_STYLE.get(semantic_kind, "HB Body")
    normalized_language = (page_language or "en").split("-", 1)[0].lower()
    density_key = f"lang_{normalized_language}_type_list_font_leading"
    if semantic_kind in {"list", "sublist"} and density_key in writer.params:
        base = "HB List" if semantic_kind == "list" else "HB Sublist"
        style = f"{base} {normalized_language.upper()}"
    if is_preface and kind == "body":
        style = "HB Preface Body"
    text = "\u25cf " + text if is_h2 else text
    text, inline_replacements = prepare_app_body_inline(
        writer,
        semantic_kind=semantic_kind,
        text=text,
        bundle_root=bundle_root,
        page_language=page_language,
        story_id=story_id,
        block_index=block_index,
    )
    paragraph = writer._psr(
        style,
        text,
        terminal=terminal,
        span_columns=(has_twocol_layout and not in_twocol and is_h2),
        inline_replacements=inline_replacements,
    )
    return paragraph, semantic_kind, is_h2, text
