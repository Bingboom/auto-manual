"""Shared paragraph-style contract for editable App setup stories."""
from __future__ import annotations

from .params import param_pt

APP_PROSE_STYLE = {
    "h2_app_download": "HB App H2 Download",
    "h2_app": "HB App H2",
    "body_app_primary": "HB App Body Primary",
    "body_app_tail": "HB App Body Tail",
    "body_app_result": "HB App Body Result",
    "body_app_section": "HB App Body Section",
    "h3_app": "HB App H3",
    "list_app": "HB App List",
    "body_app_notes": "HB App Notes",
}

_STYLE_SPECS = (
    ("HB App H2 Download", "idml_app_h2_font_size", 10.0, "idml_app_h2_font_leading", 11.0, "Bold", "app_h2_download"),
    ("HB App H2", "idml_app_h2_font_size", 10.0, "idml_app_h2_font_leading", 11.0, "Bold", "app_h2"),
    ("HB App Body Primary", "idml_app_primary_body_font_size", 7.0, "idml_app_primary_body_font_leading", 9.0, "Regular", ""),
    ("HB App Body Tail", "idml_app_tail_body_font_size", 6.6, "idml_app_tail_body_font_leading", 7.5, "Regular", ""),
    ("HB App Body Result", "idml_app_result_body_font_size", 6.8, "idml_app_result_body_font_leading", 7.8, "Regular", ""),
    ("HB App Body Section", "idml_app_section_body_font_size", 6.6, "idml_app_section_body_font_leading", 7.5, "Regular", ""),
    ("HB App H3", "idml_app_notes_font_size", 7.0, "idml_app_notes_font_leading", 8.0, "Bold", ""),
    ("HB App List", "idml_app_notes_font_size", 7.0, "idml_app_notes_font_leading", 8.0, "Regular", "app_list"),
    ("HB App Notes", "idml_app_notes_font_size", 7.0, "idml_app_notes_font_leading", 8.0, "Regular", ""),
)


def paragraph_styles(params: dict[str, tuple[str, str]]) -> list[tuple[str, float, float, str, str]]:
    return [
        (name, param_pt(params, size_key, size), param_pt(params, leading_key, leading), weight, kind)
        for name, size_key, size, leading_key, leading, weight, kind in _STYLE_SPECS
    ]


def paragraph_attrs(name: str, kind: str, params: dict[str, tuple[str, str]]) -> str:
    if kind == "app_h2_download":
        return f'SpaceAfter="{param_pt(params, "idml_app_download_h2_space_after", 8.5):g}" Hyphenation="false" '
    if kind == "app_h2":
        return f'SpaceAfter="{param_pt(params, "idml_app_h2_space_after", 3.5):g}" Hyphenation="false" '
    if kind == "app_list":
        return (
            f'LeftIndent="{param_pt(params, "idml_app_list_left_indent", 19.2):g}" '
            f'FirstLineIndent="{param_pt(params, "idml_app_list_first_line_indent", -5.7):g}" '
            'RightIndent="0" SpaceAfter="0.7" Hyphenation="false" '
        )
    indent_tokens = {
        "HB App Body Primary": ("idml_app_primary_body_left_indent", 14.2),
        "HB App Body Tail": ("idml_app_tail_body_left_indent", 14.2),
        "HB App Body Result": ("idml_app_result_body_left_indent", 11.2),
        "HB App Body Section": ("idml_app_section_body_left_indent", 13.2),
        "HB App H3": ("idml_app_notes_left_indent", 13.5),
        "HB App Notes": ("idml_app_notes_left_indent", 13.5),
    }
    token = indent_tokens.get(name)
    return (
        f'LeftIndent="{param_pt(params, token[0], token[1]):g}" Hyphenation="false" '
        if token else ""
    )


def estimated_metrics(params: dict[str, tuple[str, str]], semantic_kind: str) -> tuple[float, float] | None:
    style_name = APP_PROSE_STYLE.get(semantic_kind)
    row = next((row for row in _STYLE_SPECS if row[0] == style_name), None)
    if row is None:
        return None
    return param_pt(params, row[1], row[2]), param_pt(params, row[3], row[4])
