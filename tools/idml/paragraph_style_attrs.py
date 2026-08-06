"""Paragraph-level IDML attributes shared by the style resource writer."""
from __future__ import annotations

import math

from .app_text_styles import paragraph_attrs as app_paragraph_attrs
from .params import param_pt


def contract_paragraph_attrs(
    name: str,
    kind: str,
    leading: float,
    params: dict[str, tuple[str, str]],
) -> str:
    """Return token-driven keep, indent, spacing, and hyphenation attributes."""
    attrs = ""
    if name in {"HB Title L2", "HB Title L3"}:
        level = "l2" if name == "HB Title L2" else "l3"
        needspace = param_pt(
            params,
            f"comp_title_{level}_needspace",
            28.346 if level == "l2" else 22.677,
        )
        body_leading = param_pt(params, "type_body_font_leading", 7.5)
        keep_lines = max(
            1,
            math.ceil(max(0.0, needspace - leading) / body_leading - 1e-9),
        )
        attrs = f'KeepWithNext="{keep_lines}" '

    if kind == "list":
        attrs += (
            f'LeftIndent="{param_pt(params, "idml_list_left_indent", 3.7):g}" '
            f'FirstLineIndent="{param_pt(params, "idml_list_first_line_indent", -6.25):g}" '
            'RightIndent="0" '
            f'SpaceAfter="{param_pt(params, "comp_list_itemsep", 2.07):g}" '
            'Hyphenation="false" '
        )
    elif kind == "sublist":
        attrs += (
            f'LeftIndent="{param_pt(params, "idml_sublist_left_indent", 10.38):g}" '
            f'FirstLineIndent="{param_pt(params, "idml_sublist_first_line_indent", -6.04):g}" '
            'RightIndent="0" '
            f'SpaceAfter="{param_pt(params, "comp_sublist_itemsep", 2.0):g}" '
            'Hyphenation="false" '
        )
    elif kind == "safety_lead":
        attrs = (
            f'SpaceAfter="{param_pt(params, "idml_safety_lead_space_after", 2.4):g}" '
            'Hyphenation="false" '
        )
    elif kind == "warning_lead":
        attrs = 'Hyphenation="false" '
    elif kind == "preface_body":
        # The approved preface never hyphenates: doing so collapses the
        # governed FR/ES language blocks relative to the reference.
        attrs = (
            f'SpaceAfter="{param_pt(params, "idml_preface_paragraph_space_after", 2.0):g}" '
            'Hyphenation="false" Composer="HL Single" '
        )
    elif kind == "warranty_note":
        attrs = 'Hyphenation="false" '
    elif kind == "warranty_list":
        attrs = (
            f'LeftIndent="{param_pt(params, "idml_warranty_list_left_indent", 5.67):g}" '
            f'FirstLineIndent="{param_pt(params, "idml_warranty_list_first_line_indent", -5.67):g}" '
            'RightIndent="0" SpaceAfter="0.7" Hyphenation="false" '
        )
    return attrs + app_paragraph_attrs(name, kind, params)
