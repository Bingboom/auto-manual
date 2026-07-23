"""Coarse story-chain height estimates, separate from visible style XML."""
from __future__ import annotations

from .app_text_styles import estimated_metrics
from .params import param_pt

_SIZE = {"h1": 9.0, "h2": 8.6, "h3": 7.0, "label": 6.8}
_LEADING = {"h1": 16.0, "h2": 12.0, "h3": 9.0, "label": 12.0}


def paragraph_estimate(
    params: dict[str, tuple[str, str]],
    semantic_kind: str,
    source_kind: str,
    text: str,
    measure: float,
    *,
    is_preface: bool,
    operation_spacing: float | None,
) -> tuple[float, int]:
    size = _SIZE.get(semantic_kind, 6.2)
    leading = _LEADING.get(semantic_kind, 7.5)
    if metrics := estimated_metrics(params, semantic_kind):
        size, leading = metrics
    if is_preface and source_kind == "body":
        size = param_pt(params, "idml_preface_body_font_size", 7.2)
        leading = param_pt(params, "idml_preface_body_font_leading", 8.6)
    elif source_kind == "body_operation_energy_intro":
        leading = 8.1
    per_line = max(20, int(measure / (0.52 * size)))
    lines = sum(
        max(1, (len(segment) + per_line - 1) // per_line)
        for segment in text.split("\n")
    )
    spacing = 0.0
    if is_preface and source_kind == "body":
        spacing = param_pt(
            params, "idml_preface_paragraph_space_after", 2.0,
        ) * len(text.split("\n"))
    if operation_spacing is not None:
        spacing = operation_spacing
    return leading * lines + spacing, lines
