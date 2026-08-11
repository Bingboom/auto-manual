"""Shared paragraph-style contract for editable App setup stories."""
from __future__ import annotations

from dataclasses import dataclass
import re

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

_APP_LIST_MARKER = re.compile(r"^\s*([•◦–-])(?:\s+|\t|$)")


@dataclass(frozen=True)
class AppMarkerLayout:
    """Editable marker/tab geometry for one App heading or list paragraph."""

    text: str
    tab_position: float
    marker: str | None = None
    marker_point_size: float | None = None
    marker_baseline_shift: float = 0.0


def marked_paragraph_layout(
    semantic_kind: str,
    text: str,
    params: dict[str, tuple[str, str]],
) -> AppMarkerLayout | None:
    """Replace glyph-width-dependent spaces with the shared App tab contract."""
    if semantic_kind in {"h2_app", "h2_app_download"}:
        number_left = param_pt(params, "idml_app_notes_left_indent", 5.7)
        return AppMarkerLayout(
            f"●\t{text}",
            number_left,
            marker="●",
            marker_point_size=param_pt(
                params, "idml_app_h2_marker_font_size", 5.4,
            ),
            marker_baseline_shift=param_pt(
                params, "idml_app_h2_marker_baseline_shift", 1.25,
            ),
        )
    if semantic_kind != "list_app":
        return None

    marker_match = _APP_LIST_MARKER.match(text)
    marker = marker_match.group(1) if marker_match else "•"
    list_text = text[marker_match.end():] if marker_match else text.lstrip()
    bullet_left = param_pt(params, "idml_app_list_left_indent", 5.7)
    first_line = param_pt(params, "idml_app_list_first_line_indent", -5.7)
    return AppMarkerLayout(
        f"{marker}\t{list_text}",
        bullet_left - first_line,
    )


def apply_marker_metrics(xml: str, layout: AppMarkerLayout) -> str:
    """Keep an App H2 marker inside its custom tab without shrinking the title.

    The governed fallback font gives ``●`` a full-em advance. At the inherited
    10 pt heading size that advance crosses the 5.7 pt tab stop and InDesign
    jumps to its next default tab. Restrict only the marker character range;
    the editable heading text continues to inherit the 10 pt paragraph style.
    """
    if layout.marker is None or layout.marker_point_size is None:
        return xml

    marker_content = f"<Content>{re.escape(layout.marker)}</Content>"
    pattern = re.compile(
        r'<CharacterStyleRange (?P<attrs>[^>]*)>'
        rf'(?P<body>.*?{marker_content}.*?)'
        r'</CharacterStyleRange>',
        re.S,
    )

    def rewrite(match: re.Match[str]) -> str:
        attrs = re.sub(r'\s+PointSize="[^"]*"', "", match.group("attrs"))
        attrs = re.sub(r'\s+BaselineShift="[^"]*"', "", attrs)
        return (
            f'<CharacterStyleRange {attrs} '
            f'PointSize="{layout.marker_point_size:g}" '
            f'BaselineShift="{layout.marker_baseline_shift:g}">'
            f'{match.group("body")}</CharacterStyleRange>'
        )

    rewritten, count = pattern.subn(rewrite, xml, count=1)
    if count != 1:
        raise ValueError(
            f"App marker range was not found for governed marker {layout.marker!r}"
        )
    return rewritten


def tab_list_properties(tab_position: float) -> str:
    """IDML tab stop shared by App heading markers and hanging list items."""
    return (
        '<Properties><TabList type="list"><ListItem type="record">'
        '<Alignment type="enumeration">LeftAlign</Alignment>'
        '<AlignmentCharacter type="string"></AlignmentCharacter>'
        '<Leader type="string"></Leader>'
        f'<Position type="unit">{tab_position:g}</Position>'
        '</ListItem></TabList></Properties>'
    )


def paragraph_styles(params: dict[str, tuple[str, str]]) -> list[tuple[str, float, float, str, str]]:
    return [
        (name, param_pt(params, size_key, size), param_pt(params, leading_key, leading), weight, kind)
        for name, size_key, size, leading_key, leading, weight, kind in _STYLE_SPECS
    ]


def paragraph_attrs(name: str, kind: str, params: dict[str, tuple[str, str]]) -> str:
    if kind == "app_h2_download":
        number_left = param_pt(params, "idml_app_notes_left_indent", 5.7)
        return (
            f'LeftIndent="{number_left:g}" FirstLineIndent="{-number_left:g}" '
            f'SpaceAfter="{param_pt(params, "idml_app_download_h2_space_after", 8.5):g}" '
            'Hyphenation="false" '
        )
    if kind == "app_h2":
        number_left = param_pt(params, "idml_app_notes_left_indent", 5.7)
        return (
            f'LeftIndent="{number_left:g}" FirstLineIndent="{-number_left:g}" '
            f'SpaceAfter="{param_pt(params, "idml_app_h2_space_after", 3.5):g}" '
            'Hyphenation="false" '
        )
    if kind == "app_list":
        # The bullet shares the numbered heading edge.  A fixed tab at the
        # continuation edge makes the first prose line and all wraps coincide.
        bullet_left = param_pt(params, "idml_app_list_left_indent", 5.7)
        first_line = param_pt(
            params, "idml_app_list_first_line_indent", -5.7,
        )
        continuation_left = bullet_left - first_line
        return (
            f'LeftIndent="{continuation_left:g}" '
            f'FirstLineIndent="{first_line:g}" '
            'RightIndent="0" SpaceAfter="0.7" Hyphenation="false" '
        )
    indent_tokens = {
        "HB App Body Primary": ("idml_app_primary_body_left_indent", 14.2),
        "HB App Body Tail": ("idml_app_tail_body_left_indent", 14.2),
        "HB App Body Result": ("idml_app_result_body_left_indent", 11.2),
        "HB App Body Section": ("idml_app_section_body_left_indent", 13.2),
        "HB App H3": ("idml_app_notes_left_indent", 5.7),
        "HB App Notes": ("idml_app_notes_left_indent", 5.7),
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
