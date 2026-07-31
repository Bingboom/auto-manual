"""Warning/notice callout components (componentization P2)."""
from __future__ import annotations

from pathlib import Path

from ..primitives import (
    cell,
    component_table,
    image_cell_content,
    psr,
    wrap_table_paragraph,
)
from ..params import param_pt
from ..character_metrics import fit_tail_label_xml, with_character_baseline_shift
from ..line_metrics import estimated_line_count
from .base import RenderContext, figure_paragraph
from .warning_lead import rounded_warninglead


def _line_total(texts: list[str], measure: float, size: float, minimum: int) -> int:
    return sum(
        estimated_line_count(
            text, measure, point_size=size, minimum_narrow_chars=minimum,
        )
        for text in texts
    ) or 1


def _warning_icon_asset(ctx: RenderContext) -> Path:
    return (
        ctx.root / "docs" / "templates" / "word_template" / "common_assets"
        / "symbols" / "warning_triangle.png"
    )


def _safety_instruction_icon_asset(ctx: RenderContext) -> Path:
    return (
        ctx.root / "docs" / "templates" / "word_template" / "common_assets"
        / "symbols" / "warning_triangle_dark.svg"
    )


def render_safetyinstruction(
    spec: dict,
    ctx: RenderContext,
    *,
    tid: str,
    terminal: bool,
    span_columns: bool = True,
    measure_w: float | None = None,
) -> tuple[str, float]:
    """Render the solid-icon safety lockup, distinct from safetywarning."""
    body_w = measure_w or ctx.text_measure
    icon_asset = _safety_instruction_icon_asset(ctx)
    icon = ""
    if icon_asset.exists():
        icon_w = param_pt(ctx.params, "idml_safety_instruction_icon_width", 20.0)
        icon_h = param_pt(ctx.params, "idml_safety_instruction_icon_height", 17.4)
        icon = figure_paragraph(
            image_cell_content(f"{tid}wi", icon_asset, icon_w, icon_h),
        )
    lockup_w = param_pt(ctx.params, "idml_safety_instruction_lockup_width", 31.0)
    icon_left = param_pt(ctx.params, "idml_safety_instruction_icon_left_inset", 7.5)
    text_inset = param_pt(ctx.params, "idml_safety_instruction_text_inset", 4.0)
    body = "\n".join(str(text) for text in spec.get("texts", []) if text)
    cols = [lockup_w, max(24.0, body_w - lockup_w)]
    cells = [
        cell(
            f"{tid}c0", "0:0", icon, stroke=False,
            top=2.0, bottom=2.0, left=icon_left, right=3.0,
            valign="CenterAlign",
        ),
        cell(
            f"{tid}c1", "1:0",
            psr("HB Safety Instruction", body, terminal=True),
            stroke=False, top=2.0, bottom=2.0,
            left=text_inset, right=text_inset, valign="CenterAlign",
        ),
    ]
    table = component_table(tid, cols, cells, role="warning")
    return wrap_table_paragraph(table, terminal, span_columns), 28.0


def render_safetywarning(spec: dict, ctx: RenderContext, *, tid: str, terminal: bool,
                         span_columns: bool = True,
                         measure_w: float | None = None) -> tuple[str, float]:
    body_w = measure_w or ctx.text_measure
    warning_icon_asset = _warning_icon_asset(ctx)
    texts = spec.get("texts", [])
    body = "\n".join(texts)
    icon = ""
    if warning_icon_asset.exists():
        iw, ih = ctx.art_frame_size(warning_icon_asset, max_w=18.0)
        icon = figure_paragraph(image_cell_content(f"{tid}wi", warning_icon_asset, iw, ih))
    cols = [24.0, max(24.0, body_w - 24.0)]
    cells = [
        cell(f"{tid}c0", "0:0", icon, stroke=False),
        cell(f"{tid}c1", "1:0",
             psr("HB Title L3", body, terminal=True), stroke=False),
    ]
    table = component_table(tid, cols, cells, role="warning")
    return wrap_table_paragraph(table, terminal, span_columns), 28.0


def render_warninglead(spec: dict, ctx: RenderContext, *, tid: str, terminal: bool,
                       span_columns: bool = True,
                       measure_w: float | None = None) -> tuple[str, float]:
    body_w = measure_w or ctx.text_measure
    if ctx.add_story is not None:
        return rounded_warninglead(
            spec,
            ctx,
            tid=tid,
            terminal=terminal,
            body_w=body_w,
        )
    warning_icon_asset = _warning_icon_asset(ctx)
    label = spec.get("label", "")
    texts = spec.get("texts", [])
    icon = ""
    if warning_icon_asset.exists():
        iw, ih = ctx.art_frame_size(warning_icon_asset, max_w=24.0)
        icon = figure_paragraph(image_cell_content(f"{tid}wi", warning_icon_asset, iw, ih))
    body = "\n".join(texts)
    right = psr("HB Warning Lead Label", label) + psr(
        "HB Warning Lead Body", body, terminal=True,
    )
    icon_w = min(36.0, max(28.0, body_w * 0.25))
    cols = [icon_w, max(36.0, body_w - icon_w)]
    cells = [
        cell(f"{tid}c0", "0:0", icon,
             top=4, bottom=4, left=4, right=4),
        cell(f"{tid}c1", "1:0", right,
             top=4, bottom=4, left=5, right=4),
    ]
    table = component_table(tid, cols, cells, role="warning")
    lines = _line_total(texts, body_w - icon_w, 6.6, 12)
    return wrap_table_paragraph(table, terminal, span_columns), max(36.0, 7.4 * (lines + 1) + 10)


def render_tailwarnbox(spec: dict, ctx: RenderContext, *, tid: str, terminal: bool,
                       span_columns: bool = True,
                       measure_w: float | None = None) -> tuple[str, float]:
    body_w = measure_w or ctx.text_measure
    warning_icon_asset = _safety_instruction_icon_asset(ctx)
    label = spec.get("label", "")
    texts = spec.get("texts", [])
    icon = ""
    if warning_icon_asset.exists():
        iw = param_pt(ctx.params, "idml_safety_tail_icon_width", 22.0)
        ih = param_pt(ctx.params, "idml_safety_tail_icon_height", iw * 80.0 / 92.0)
        icon = figure_paragraph(image_cell_content(f"{tid}wi", warning_icon_asset, iw, ih),
                                tail="<Content></Content>")
    body = " ".join(t.strip() for t in texts if str(t).strip())
    body_style = "HB Safety Tail Body EN" if spec.get("language") == "en" else "HB Safety Tail Body"
    label_w = 58.0
    icon_w = 32.0
    label_psr = fit_tail_label_xml(
        psr("HB Safety Tail Label", label, terminal=True), ctx.params,
        str(spec.get("language") or "en"), label, label_w - 6.0)
    label_psr = with_character_baseline_shift(label_psr, shift=0.68)
    cols = [icon_w, label_w, max(80.0, body_w - icon_w - label_w)]
    cells = [
        cell(f"{tid}c0", "0:0", icon,
             stroke=False, top=0, bottom=0, left=4, right=3,
             valign="CenterAlign"),
        cell(f"{tid}c1", "1:0", label_psr,
             stroke=False, top=0, bottom=0, left=3, right=3,
             valign="CenterAlign"),
        cell(f"{tid}c2", "2:0",
             psr(body_style, body, terminal=True),
             stroke=False, top=0, bottom=0, left=3, right=4,
             valign="CenterAlign"),
    ]
    table = component_table(tid, cols, cells, role="warning")
    lines = _line_total([body], body_w - icon_w - label_w, 6.2, 20)
    return wrap_table_paragraph(table, terminal, span_columns), max(30.0, 7.5 * lines + 8)


def render_warnbox(spec: dict, ctx: RenderContext, *, tid: str, terminal: bool,
                   span_columns: bool = True,
                   measure_w: float | None = None) -> tuple[str, float]:
    body_w = measure_w or ctx.text_measure
    warning_icon_asset = _warning_icon_asset(ctx)
    label = spec.get("label", "")
    texts = spec.get("texts", [])
    icon = ""
    if warning_icon_asset.exists():
        iw, ih = ctx.art_frame_size(warning_icon_asset, max_w=28.0)
        icon = figure_paragraph(image_cell_content(f"{tid}wi", warning_icon_asset, iw, ih))
    body = "\n".join(texts)
    right = psr("HB Title L2", label) + psr("HB Body", body, terminal=True)
    cols = [36.0, max(36.0, body_w - 36.0)]
    cells = [
        cell(f"{tid}c0", "0:0", icon),
        cell(f"{tid}c1", "1:0", right),
    ]
    table = component_table(tid, cols, cells, role="warning")
    lines = _line_total(texts, body_w - 36.0, 6.6, 20)
    return wrap_table_paragraph(table, terminal, span_columns), max(34.0, 7.4 * (lines + 1) + 12)
