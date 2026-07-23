"""Typed LCD layout-token helpers for the IDML renderer."""
from __future__ import annotations

from .params import param_pt


def layout_tokens(
    writer,
    body_w: float,
    *,
    segment_index: int = 0,
) -> tuple[tuple[float, ...], float, float]:
    """Resolve segment-aware LCD column, icon, and cell-padding tokens."""
    prefix = "idml_lcd_first" if segment_index == 0 else "idml_lcd_continuation"
    no_w = param_pt(
        writer.params,
        f"{prefix}_no_col_width",
        param_pt(writer.params, "comp_lcd_no_col_width", body_w * 0.08),
    )
    icon_w = param_pt(
        writer.params,
        f"{prefix}_icon_col_width",
        param_pt(writer.params, "comp_lcd_icon_col_width", body_w * 0.12),
    )
    label_w = param_pt(writer.params, f"{prefix}_label_col_width", 0.0)
    if label_w <= 0:
        raw_label_ratio = writer.params.get(
            "comp_lcd_label_col_width", ("0.24", "ratio")
        )[0].replace("\\linewidth", "")
        try:
            label_ratio = float(raw_label_ratio)
        except ValueError:
            label_ratio = 0.24
        label_w = body_w * label_ratio
    columns = (no_w, icon_w, label_w, body_w - no_w - icon_w - label_w)
    icon_pt = min(
        param_pt(writer.params, "comp_lcd_icon_width", 24.0),
        param_pt(writer.params, "comp_lcd_icon_height", 24.0),
    )
    padding = param_pt(writer.params, "comp_lcd_table_tabcolsep", 1.4)
    return columns, icon_pt, padding


def typed_paragraph(writer, style: str, text: str,
                    size_key: str, leading_key: str, *,
                    bold: bool = False,
                    font: str | None = None) -> str:
    """Apply shared typed LCD tokens without replacing the template style."""
    point_size = param_pt(writer.params, size_key, 5.2)
    leading = param_pt(writer.params, leading_key, 5.8)
    font_style = ' FontStyle="Bold"' if bold else ""
    paragraph = writer._psr(style, text, terminal=True).replace(
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
        f'PointSize="{point_size:g}" Leading="{leading:g}"{font_style}', 1)
    if font:
        paragraph = paragraph.replace(
            '<AppliedFont type="string">Arial Unicode MS</AppliedFont>',
            f'<AppliedFont type="string">{font}</AppliedFont>',
        )
    return paragraph
