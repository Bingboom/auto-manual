"""Shared LaTeX-parity NOTE / TIP / CAUTION / WARNING strip."""
from __future__ import annotations

import math
import unicodedata
from dataclasses import dataclass

from .. import page_objects as _po
from ..params import param_pt
from ..primitives import cell, component_table, path_geometry, psr, wrap_table_paragraph
from .base import RenderContext, figure_paragraph

_GILROY_WIDTHS = {
    **dict(zip(
        "abcdefghijklmnopqrstuvwxyz",
        (0.636, 0.636, 0.552, 0.636, 0.584, 0.320, 0.636, 0.558,
         0.206, 0.230, 0.494, 0.206, 0.848, 0.558, 0.606, 0.636,
         0.636, 0.314, 0.454, 0.375, 0.558, 0.510, 0.770, 0.510,
         0.510, 0.470),
    )),
    **dict(zip(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        (0.630, 0.620, 0.745, 0.720, 0.530, 0.515, 0.789, 0.680,
         0.230, 0.553, 0.580, 0.490, 0.800, 0.680, 0.804, 0.590,
         0.809, 0.610, 0.576, 0.540, 0.660, 0.608, 1.000, 0.580,
         0.595, 0.520),
    )),
    **dict(zip(
        "0123456789",
        (0.630, 0.340, 0.525, 0.530, 0.580,
         0.540, 0.530, 0.490, 0.548, 0.530),
    )),
    **dict(zip(
        ".,:;()/-+%'‑–—°",
        (0.230, 0.240, 0.230, 0.245, 0.266, 0.266, 0.530, 0.520,
         0.540, 0.709, 0.170, 0.500, 0.660, 0.760, 0.386),
    )),
}


@dataclass(frozen=True)
class NoticeBoxLayout:
    body_width: float
    label_width: float
    plate_left: float
    plate_width: float
    body_inset: float
    right_inset: float
    pad_tb: float
    arc: float
    label_size: float
    label_leading: float
    body_size: float
    body_leading: float
    body_horizontal_scale: float
    label_baseline_shift: float
    body_baseline_shift: float
    lines: int
    panel_height: float


def source_notice_label(spec: dict) -> str:
    """Return the notice label verbatim from IR; never synthesize display copy."""
    value = spec.get("label")
    label = str(value).strip() if value is not None else ""
    if not label:
        raise ValueError("notice label is required from source IR")
    return label


def _typed(xml: str, size: float, leading: float, weight: str | None = None,
           *, horizontal_scale: float | None = None,
           baseline_shift: float | None = None) -> str:
    attrs = f'PointSize="{size:g}" Leading="{leading:g}"'
    if weight:
        attrs += f' FontStyle="{weight}"'
    if horizontal_scale is not None:
        attrs += f' HorizontalScale="{horizontal_scale * 100:g}"'
    if baseline_shift is not None:
        attrs += f' BaselineShift="{baseline_shift:g}"'
    return xml.replace(
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" ' + attrs,
    )


def _body_xml(spec: dict, size: float, leading: float,
              horizontal_scale: float, baseline_shift: float) -> str:
    texts = spec.get("texts", [])
    if not spec.get("list"):
        return _typed(
            psr("HB Callout Body", "\n".join(texts), terminal=True),
            size,
            leading,
            "Medium",
            horizontal_scale=horizontal_scale,
            baseline_shift=baseline_shift,
        )
    items = [text.strip() for text in texts if str(text).strip()]
    paragraphs = []
    for index, item in enumerate(items):
        paragraph = _typed(
            psr("HB Callout Body", item, terminal=index == len(items) - 1),
            size,
            leading,
            "Medium",
            horizontal_scale=horizontal_scale,
            baseline_shift=baseline_shift,
        )
        paragraph = paragraph.replace(
            "<ParagraphStyleRange ",
            '<ParagraphStyleRange LeftIndent="3.4" FirstLineIndent="-3.4" ',
            1,
        )
        bullet = (
            '<CharacterStyleRange '
            'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
            f'PointSize="4.8" Leading="{leading:g}" '
            f'BaselineShift="{baseline_shift:g}"><Content>•</Content>'
            '</CharacterStyleRange>'
            '<CharacterStyleRange '
            'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
            f'PointSize="{size:g}" Leading="{leading:g}" FontStyle="Medium" '
            f'HorizontalScale="{horizontal_scale * 100:g}" '
            f'BaselineShift="{baseline_shift:g}"><Content> </Content>'
            '</CharacterStyleRange>'
        )
        paragraph = paragraph.replace(
            "\n    <CharacterStyleRange",
            "\n    " + bullet + "\n    <CharacterStyleRange",
            1,
        )
        paragraphs.append(paragraph)
    return "".join(paragraphs)


def _gilroy_width(text: str, size: float) -> float:
    """Portable width estimate for the regular callout face.

    InDesign performs word wrapping after import, so character counts can
    under-allocate a line near a long token boundary (notably ``100W).``).
    These ratios come from the shipped Gilroy-Regular metrics at 6.5 pt.
    """
    width = 0.0
    for char in text.replace("**", ""):
        if char.isspace():
            ratio = 0.251
        elif char in _GILROY_WIDTHS:
            ratio = _GILROY_WIDTHS[char]
        elif ord(char) > 0x2FFF:
            ratio = 1.0
        elif unicodedata.category(char).startswith("M"):
            ratio = 0.0
        elif char.isalpha():
            base = unicodedata.normalize("NFD", char)[0]
            ratio = _GILROY_WIDTHS.get(base, 0.55)
        elif unicodedata.category(char).startswith("P"):
            ratio = 0.378
        else:
            ratio = 0.55
        width += ratio * size
    return width


def _wrapped_lines(text: str, available: float, size: float) -> int:
    words = text.replace("**", "").split()
    if not words:
        return 1
    lines = 1
    used = 0.0
    space = _gilroy_width(" ", size)
    for word in words:
        word_w = _gilroy_width(word, size)
        if used and used + space + word_w <= available:
            used += space + word_w
        elif used:
            lines += max(1, math.ceil(word_w / available))
            used = word_w % available
        else:
            extra = max(1, math.ceil(word_w / available))
            lines += extra - 1
            used = word_w % available
    return lines


def notice_box_layout(params: dict, body_width: float, label: str,
                      texts: list, *, variant: str = "",
                      is_list: bool = False,
                      body_horizontal_scale_override: float | None = None,
                      ) -> NoticeBoxLayout:
    """Resolve the shared geometry and type tokens for every notice carrier."""
    label_size = param_pt(params, "type_tip_label_font_size", 8.0)
    label_leading = param_pt(params, "type_tip_label_font_leading", 9.0)
    body_size = param_pt(params, "type_tip_body_font_size", 6.5)
    body_leading = param_pt(params, "type_tip_body_font_leading", 7.83)
    body_horizontal_scale = (
        float(body_horizontal_scale_override)
        if body_horizontal_scale_override is not None
        else param_pt(params, "type_tip_body_horizontal_scale", 1.0)
    )
    if body_horizontal_scale <= 0:
        raise ValueError("notice body_horizontal_scale must be greater than zero")
    label_width = param_pt(params, "comp_caution_label_width", 52.44)
    plate_left = param_pt(params, "comp_callout_label_inset", 3.4)
    callout_rule = param_pt(params, "comp_callout_rule", 1.2)
    body_inset = callout_rule + param_pt(
        params, "comp_callout_body_inset", 4.25)
    right_inset = param_pt(params, "comp_tip_pad_lr", 6.24)
    pad_tb = param_pt(params, "comp_caution_pad_tb", 3.4)
    label_available = label_width - plate_left - 1.0
    estimated_label_width = _gilroy_width(label, label_size) * 1.03
    if estimated_label_width > label_available:
        scale = label_available / estimated_label_width
        label_size = max(6.5, label_size * scale)
        label_leading = max(label_size + 0.8, label_leading * scale)
    plate_width = label_width - plate_left
    body_frame_width = body_width - (
        plate_left + plate_width + body_inset + right_inset)
    hanging_indent = 3.4 if is_list else 0.0
    available = max(20.0, body_frame_width - hanging_indent)
    lines = sum(
        _wrapped_lines(
            str(text), available, body_size * body_horizontal_scale,
        )
        for text in texts
    ) or 1
    natural_height = body_leading * lines + 2 * pad_tb + 1.0
    tip_min_height = (
        param_pt(params, "comp_tip_height", 41.67)
        if variant == "tip" else 0.0
    )
    panel_height = max(natural_height, tip_min_height)
    return NoticeBoxLayout(
        body_width=body_width,
        label_width=label_width,
        plate_left=plate_left,
        plate_width=plate_width,
        body_inset=body_inset,
        right_inset=right_inset,
        pad_tb=pad_tb,
        arc=param_pt(params, "comp_tip_arc", 4.9) + callout_rule,
        label_size=label_size,
        label_leading=label_leading,
        body_size=body_size,
        body_leading=body_leading,
        body_horizontal_scale=body_horizontal_scale,
        label_baseline_shift=param_pt(
            params, "idml_callout_label_baseline_shift", 2.63),
        body_baseline_shift=param_pt(
            params, "idml_callout_body_baseline_shift", 0.9),
        lines=lines,
        panel_height=panel_height,
    )


def _rounded_notice(ctx: RenderContext, *, tid: str, terminal: bool,
                    label: str, label_psr: str, body_psr: str,
                    layout: NoticeBoxLayout) -> tuple[str, float]:
    # A four-item anchored group mirrors the LaTeX tcolorbox directly:
    # rounded grey shell, rounded white plate, centred label frame, and
    # the body frame.  A rounded frame nested in a table cell leaves an
    # overset anchor marker in InDesign, so the parts must be siblings.
    body_w = layout.body_width
    plate_left = layout.plate_left
    plate_w = layout.plate_width
    body_inset = layout.body_inset
    right_inset = layout.right_inset
    pad_tb = layout.pad_tb
    panel_h = layout.panel_height
    label_sid = ctx.add_story(
        f"st_anchor_notice_label_{tid}",
        f"{label} notice label plate",
        [label_psr],
    )
    body_sid = ctx.add_story(
        f"st_anchor_notice_body_{tid}",
        f"{label} notice body",
        [body_psr],
    )
    anchor = (
        '    <AnchoredObjectSetting AnchoredPosition="InlinePosition" '
        'SpineRelative="false" LockPosition="false" PinPosition="true" '
        'AnchorPoint="BottomRightAnchor" HorizontalAlignment="LeftAlign" '
        'HorizontalReferencePoint="TextFrame" VerticalAlignment="TopAlign" '
        'VerticalReferencePoint="LineBaseline" AnchorXoffset="0" '
        'AnchorYoffset="0" AnchorSpaceAbove="0"/>\n'
    )
    outer = (
        f'<Rectangle Self="bg_notice_{tid}" ContentType="Unassigned" '
        'AppliedObjectStyle="ObjectStyle/HB Rounded Panel" '
        'FillColor="Color/HB Bg K05" StrokeColor="Swatch/None" '
        'StrokeWeight="0" ItemTransform="1 0 0 1 0 0">\n'
        + _po.rounded_path_geometry(
            0.0,
            -panel_h,
            body_w,
            0.0,
            layout.arc,
        )
        + anchor
        + '</Rectangle>\n'
    )
    plate = (
        f'<Rectangle Self="plate_notice_{tid}" ContentType="Unassigned" '
        'AppliedObjectStyle="ObjectStyle/HB Rounded Panel" '
        'FillColor="Color/Paper" StrokeColor="Swatch/None" '
        'StrokeWeight="0" ItemTransform="1 0 0 1 0 0">\n'
        + _po.left_rounded_path_geometry(
            plate_left,
            -panel_h + plate_left,
            plate_left + plate_w,
            -plate_left,
            max(0.0, layout.arc - plate_left / 2.0),
        )
        + anchor
        + '</Rectangle>\n'
    )

    def _text_frame(sid: str, self_id: str, x1: float, x2: float, *,
                    vertical_inset: float,
                    right_text_inset: float = 0.0) -> str:
        insets = (0.0, 0.0, 0.0, right_text_inset)
        inset_xml = "".join(
            f'<ListItem type="unit">{value:g}</ListItem>' for value in insets)
        return (
            f'<TextFrame Self="{self_id}" ParentStory="{sid}" '
            'PreviousTextFrame="n" NextTextFrame="n" ContentType="TextType" '
            'AppliedObjectStyle="ObjectStyle/$ID/[Normal Text Frame]" '
            'FillColor="Swatch/None" StrokeColor="Swatch/None" StrokeWeight="0" '
            'ItemTransform="1 0 0 1 0 0">\n'
            + path_geometry(
                x1, -panel_h + vertical_inset, x2, -vertical_inset)
            + '    <TextFramePreference TextColumnCount="1" '
            'VerticalJustification="CenterAlign" AutoSizingType="Off">'
            f'<Properties><InsetSpacing type="list">{inset_xml}'
            '</InsetSpacing></Properties></TextFramePreference>\n'
            + anchor
            + '</TextFrame>\n'
        )

    label_frame = _text_frame(
        label_sid,
        f"tf_notice_label_{tid}",
        plate_left,
        plate_left + plate_w,
        vertical_inset=plate_left,
        right_text_inset=1.0,
    )
    body_left = plate_left + plate_w + body_inset
    body_frame = _text_frame(
        body_sid,
        f"tf_notice_body_{tid}",
        body_left,
        body_w - right_inset,
        vertical_inset=pad_tb,
    )
    group = (
        f'<Group Self="grp_notice_{tid}" '
        'AppliedObjectStyle="ObjectStyle/$ID/[None]" '
        'ItemTransform="1 0 0 1 0 0">\n'
        + outer + plate + label_frame + body_frame + '</Group>'
    )
    tail = '<Content></Content>' + ('' if terminal else '<Br/>')
    xml = figure_paragraph(group, tail=tail)
    # The fixed page-frame boundary leaves 0.89 pt after the upper DC
    # callout; LaTeX keeps 2.68 pt before ENERGY SAVING MODE.
    xml = xml.replace(
        "<ParagraphStyleRange ",
        '<ParagraphStyleRange SpaceAfter="1.8" ',
        1,
    )
    gap = param_pt(ctx.params, "comp_data_table_before", 3.4)
    return xml, panel_h + 2 * gap


def render_notice(spec: dict, ctx: RenderContext, *, tid: str, terminal: bool,
                  span_columns: bool = True,
                  measure_w: float | None = None) -> tuple[str, float]:
    body_w = measure_w or ctx.text_measure
    label = source_notice_label(spec)
    texts = spec.get("texts", [])
    layout = notice_box_layout(
        ctx.params,
        body_w,
        label,
        texts,
        variant=str(spec.get("variant", "")),
        is_list=bool(spec.get("list")),
        body_horizontal_scale_override=spec.get("body_horizontal_scale"),
    )
    label_psr = _typed(
        psr("HB Callout Label", label, terminal=True),
        layout.label_size,
        layout.label_leading,
        "Bold",
        baseline_shift=layout.label_baseline_shift,
    )
    body_psr = _body_xml(
        spec,
        layout.body_size,
        layout.body_leading,
        layout.body_horizontal_scale,
        layout.body_baseline_shift,
    )
    if ctx.add_story is not None:
        return _rounded_notice(
            ctx, tid=tid, terminal=terminal, label=label, label_psr=label_psr,
            body_psr=body_psr, layout=layout)
    cols = [layout.label_width, body_w - layout.label_width]
    cells = [
        cell(f"{tid}c0", "0:0", label_psr, fill="Color/Paper", stroke=False,
             top=10, bottom=10, left=6, right=6),
        cell(f"{tid}c1", "1:0", body_psr, fill="Color/HB Bg K05", stroke=False,
             top=10, bottom=10, left=6, right=6),
    ]
    table = component_table(tid, cols, cells, role="notice")
    return wrap_table_paragraph(table, terminal, span_columns), max(
        24.0, layout.body_leading * layout.lines + 10)
