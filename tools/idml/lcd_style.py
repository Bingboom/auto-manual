"""Typed LCD layout-token helpers for the IDML renderer."""
from __future__ import annotations

from .params import param_pt


def layout_tokens(writer, body_w: float) -> tuple[tuple[float, ...], float, float]:
    """Resolve LCD column, icon, and cell-padding tokens."""
    no_w = param_pt(writer.params, "comp_lcd_no_col_width", body_w * 0.08)
    icon_w = param_pt(writer.params, "comp_lcd_icon_col_width", body_w * 0.12)
    label_w = body_w * 0.22
    columns = (no_w, icon_w, label_w, body_w - no_w - icon_w - label_w)
    icon_pt = min(
        param_pt(writer.params, "comp_lcd_icon_width", 24.0),
        param_pt(writer.params, "comp_lcd_icon_height", 24.0),
    )
    padding = param_pt(writer.params, "comp_lcd_table_tabcolsep", 1.4)
    return columns, icon_pt, padding


def typed_paragraph(writer, style: str, text: str,
                    size_key: str, leading_key: str) -> str:
    """Apply shared typed LCD tokens without replacing the template style."""
    point_size = param_pt(writer.params, size_key, 5.2)
    leading = param_pt(writer.params, leading_key, 5.8)
    return writer._psr(style, text, terminal=True).replace(
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
        f'PointSize="{point_size:g}" Leading="{leading:g}"', 1)
