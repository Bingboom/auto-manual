"""Warning/notice callout components (componentization P2)."""
from __future__ import annotations

from pathlib import Path

from ..primitives import cell, component_table, psr, image_cell_content, wrap_table_paragraph
from .base import RenderContext, figure_paragraph


def _warning_icon_asset(ctx: RenderContext) -> Path:
    return (
        ctx.root / "docs" / "templates" / "word_template" / "common_assets"
        / "symbols" / "warning_triangle.png"
    )


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
    warning_icon_asset = _warning_icon_asset(ctx)
    label = spec.get("label", "")
    texts = spec.get("texts", [])
    icon = ""
    if warning_icon_asset.exists():
        iw, ih = ctx.art_frame_size(warning_icon_asset, max_w=24.0)
        icon = figure_paragraph(image_cell_content(f"{tid}wi", warning_icon_asset, iw, ih))
    body = "\n".join(texts)
    right = psr("HB Title L2", label) + psr("HB Body", body, terminal=True)
    icon_w = min(36.0, max(28.0, body_w * 0.25))
    cols = [icon_w, max(36.0, body_w - icon_w)]
    cells = [
        cell(f"{tid}c0", "0:0", icon,
             top=4, bottom=4, left=4, right=4),
        cell(f"{tid}c1", "1:0", right,
             top=4, bottom=4, left=5, right=4),
    ]
    table = component_table(tid, cols, cells, role="warning")
    per_line = max(12, int((body_w - icon_w) / (0.52 * 6.6)))
    lines = sum(max(1, (len(t) + per_line - 1) // per_line) for t in texts) or 1
    return wrap_table_paragraph(table, terminal, span_columns), max(36.0, 7.4 * (lines + 1) + 10)


def render_tailwarnbox(spec: dict, ctx: RenderContext, *, tid: str, terminal: bool,
                       span_columns: bool = True,
                       measure_w: float | None = None) -> tuple[str, float]:
    body_w = measure_w or ctx.text_measure
    warning_icon_asset = _warning_icon_asset(ctx)
    label = spec.get("label", "")
    texts = spec.get("texts", [])
    icon = ""
    if warning_icon_asset.exists():
        iw, ih = ctx.art_frame_size(warning_icon_asset, max_w=22.0)
        icon = figure_paragraph(image_cell_content(f"{tid}wi", warning_icon_asset, iw, ih),
                                tail="<Content></Content>")
    body = " ".join(t.strip() for t in texts if str(t).strip())
    label_psr = psr("HB Safety Tail Label", label, terminal=True).replace(
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
        'BaselineShift="0.68"', 1)
    label_w = 58.0
    icon_w = 32.0
    cols = [icon_w, label_w, max(80.0, body_w - icon_w - label_w)]
    cells = [
        cell(f"{tid}c0", "0:0", icon,
             stroke=False, top=0, bottom=0, left=4, right=3,
             valign="CenterAlign"),
        cell(f"{tid}c1", "1:0", label_psr,
             stroke=False, top=0, bottom=0, left=3, right=3,
             valign="CenterAlign"),
        cell(f"{tid}c2", "2:0",
             psr("HB Safety Tail Body", body, terminal=True),
             stroke=False, top=0, bottom=0, left=3, right=4,
             valign="CenterAlign"),
    ]
    table = component_table(tid, cols, cells, role="warning")
    per_line = max(20, int((body_w - icon_w - label_w) / (0.52 * 6.2)))
    lines = max(1, (len(body) + per_line - 1) // per_line)
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
    per_line = max(20, int((body_w - 36.0) / (0.52 * 6.6)))
    lines = sum(max(1, (len(t) + per_line - 1) // per_line) for t in texts) or 1
    return wrap_table_paragraph(table, terminal, span_columns), max(34.0, 7.4 * (lines + 1) + 12)
