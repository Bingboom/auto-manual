"""Typed LCD layout-token helpers for the IDML renderer."""
from __future__ import annotations

from .params import param_pt


def _language(lang: str) -> str:
    return (lang or "en").strip().casefold().replace("_", "-").split("-", 1)[0]


def _profile_pt(
    writer,
    *,
    language: str,
    segment: str,
    role: str,
    metric: str,
    fallback_key: str,
    fallback: float,
) -> float:
    """Resolve a locale/segment/role LCD token from most to least specific."""
    keys = (
        f"lang_{language}_idml_lcd_{segment}_{role}_{metric}",
        f"lang_{language}_idml_lcd_{segment}_{metric}",
        f"idml_lcd_{segment}_{role}_{metric}",
        f"idml_lcd_{segment}_{metric}",
        fallback_key,
    )
    for key in keys:
        if key in writer.params:
            return param_pt(writer.params, key, fallback)
    return fallback


def typography_tokens(
    writer,
    lang: str,
    row: dict[str, str],
    *,
    segment_index: int,
) -> tuple[float, float, float, float]:
    """Return label/body size and leading for one editable LCD row.

    The approved reference contract assigns semantic density roles; layout
    tokens own the actual locale-specific metrics. This keeps source text and
    source identifiers unchanged while avoiding renderer-local row numbers.
    """
    language = _language(lang)
    segment = "first" if segment_index == 0 else "continuation"
    role = row.get("typography_role", "default").strip() or "default"
    label_size = _profile_pt(
        writer,
        language=language,
        segment=segment,
        role=role,
        metric="label_font_size",
        fallback_key="type_lcd_label_font_size",
        fallback=6.2,
    )
    label_leading = _profile_pt(
        writer,
        language=language,
        segment=segment,
        role=role,
        metric="label_font_leading",
        fallback_key="type_lcd_label_font_leading",
        fallback=6.8,
    )
    body_size = _profile_pt(
        writer,
        language=language,
        segment=segment,
        role=role,
        metric="body_font_size",
        fallback_key="type_lcd_body_font_size",
        fallback=5.2,
    )
    body_leading = _profile_pt(
        writer,
        language=language,
        segment=segment,
        role=role,
        metric="body_font_leading",
        fallback_key="type_lcd_body_font_leading",
        fallback=5.8,
    )
    return label_size, label_leading, body_size, body_leading


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
                    size_key: str | None = None,
                    leading_key: str | None = None, *,
                    point_size: float | None = None,
                    leading: float | None = None,
                    bold: bool = False,
                    font: str | None = None) -> str:
    """Apply shared typed LCD tokens without replacing the template style."""
    if point_size is None:
        point_size = param_pt(writer.params, size_key or "", 5.2)
    if leading is None:
        leading = param_pt(writer.params, leading_key or "", 5.8)
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
