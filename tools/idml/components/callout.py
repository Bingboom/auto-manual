"""Warning/notice callout components (componentization P2).

Four warning shapes plus the NOTE/TIP/CAUTION notice bar — verbatim moves
from IdmlWriter._render_component. The V2.0-master geometry (column splits,
insets, icon widths) and the height heuristics are load-bearing; change them
only with the golden regenerated deliberately.
"""
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
        iw, ih = ctx.art_frame_size(warning_icon_asset, max_w=24.0)
        icon = figure_paragraph(image_cell_content(f"{tid}wi", warning_icon_asset, iw, ih),
                                tail="<Content></Content>")
    body = " ".join(t.strip() for t in texts if str(t).strip())
    label_w = 58.0
    icon_w = 32.0
    cols = [icon_w, label_w, max(80.0, body_w - icon_w - label_w)]
    cells = [
        cell(f"{tid}c0", "0:0", icon,
             stroke=False, top=1, bottom=1, left=4, right=3),
        cell(f"{tid}c1", "1:0",
             psr("HB Title L2", label, terminal=True),
             stroke=False, top=1, bottom=1, left=3, right=3),
        cell(f"{tid}c2", "2:0",
             psr("HB Body", body, terminal=True),
             stroke=False, top=1, bottom=1, left=3, right=4),
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


def render_notice(spec: dict, ctx: RenderContext, *, tid: str, terminal: bool,
                  span_columns: bool = True,
                  measure_w: float | None = None) -> tuple[str, float]:
    body_w = measure_w or ctx.text_measure
    fill = "Color/HB Bg K05"
    label = spec.get("label", "")
    texts = spec.get("texts", [])
    left = psr("HB Notice Side Label", label, terminal=True)
    body = "\n".join(texts)
    if spec.get("list"):
        items = [t.strip() for t in texts if str(t).strip()]
        right = "".join(
            psr("HB List", "• " + item, terminal=i == len(items) - 1)
            for i, item in enumerate(items)
        )
    else:
        right = psr("HB Body", body, terminal=True)
    label_w = max(34.0, body_w * 0.14)
    per_line = max(20, int((body_w - label_w) / (0.52 * 6.6)))
    lines = sum(max(1, (len(t) + per_line - 1) // per_line) for t in texts) or 1
    if ctx.add_story is not None:
        return _rounded_notice(ctx, tid=tid, terminal=terminal, label=label,
                               body_psr=right, body_w=body_w, label_w=label_w,
                               lines=lines)
    cols = [label_w, body_w - label_w]
    cells = [
        cell(f"{tid}c0", "0:0", left, fill="Color/Paper",
             stroke=False, top=10, bottom=10, left=6, right=6),
        cell(f"{tid}c1", "1:0", right, fill=fill,
             stroke=False, top=10, bottom=10, left=6, right=6),
    ]
    table = component_table(tid, cols, cells, role="notice")
    return wrap_table_paragraph(table, terminal, span_columns), max(24.0, 7.4 * lines + 10)


def _rounded_notice(ctx: RenderContext, *, tid: str, terminal: bool,
                    label: str, body_psr: str, body_w: float, label_w: float,
                    lines: int) -> tuple[str, float]:
    """The master's notice bar: full-measure rounded grey panel with the
    label in a white rounded chip on top (template: 311.8x23.2 panel,
    50.5x18.2 chip for NOTE)."""
    from .. import page_objects as _po
    from ..style_names import paragraph_style_ref
    chip_h = 18.0
    chip_w = min(label_w - 4.0, max(40.0, 7.5 * len(label) + 20.0))
    chip_sid = ctx.add_story(
        f"st_anchor_chip_{tid}", f"{label} chip",
        [psr("HB Notice Side Label", label, terminal=True)])
    chip = _po.anchored_rounded_frame_xml(
        chip_sid, chip_w, chip_h, fill="Color/Paper", radius=5.5,
        inset=(1, 4, 1, 4))
    chip_par = figure_paragraph(chip, tail="<Content></Content>")
    cols = [label_w, body_w - label_w - 10.0]
    cells = [
        cell(f"{tid}c0", "0:0", chip_par, stroke=False,
             top=1, bottom=1, left=2, right=4),
        cell(f"{tid}c1", "1:0", body_psr, stroke=False,
             top=3, bottom=3, left=4, right=6),
    ]
    inner = wrap_table_paragraph(
        component_table(tid, cols, cells, role="notice"), True, False)
    panel_h = max(chip_h + 8.0, 7.4 * lines + 12.0)
    xml = _po.anchored_panel_paragraph(
        ctx.add_story, f"st_anchor_notice_{tid}", f"{label} notice panel",
        [inner], body_w, panel_h, terminal=terminal,
        fill="Color/HB Bg K05", radius=7.0, inset=(2, 2, 2, 2),
        auto_height=True)
    return xml, panel_h + 6.0
