"""Shared LaTeX-parity NOTE / TIP / CAUTION / WARNING strip."""
from __future__ import annotations

import math
import unicodedata

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


def _typed(xml: str, size: float, leading: float, weight: str | None = None) -> str:
    attrs = f'PointSize="{size:g}" Leading="{leading:g}"'
    if weight:
        attrs += f' FontStyle="{weight}"'
    return xml.replace(
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" ' + attrs,
    )


def _body_xml(spec: dict, size: float, leading: float) -> str:
    texts = spec.get("texts", [])
    if not spec.get("list"):
        return _typed(psr("HB Body", "\n".join(texts), terminal=True), size, leading)
    items = [text.strip() for text in texts if str(text).strip()]
    paragraphs = []
    for index, item in enumerate(items):
        paragraph = _typed(
            psr("HB List", item, terminal=index == len(items) - 1),
            size,
            leading,
        )
        paragraph = paragraph.replace(
            "<ParagraphStyleRange ",
            '<ParagraphStyleRange LeftIndent="3.4" FirstLineIndent="-3.4" ',
            1,
        )
        bullet = (
            '<CharacterStyleRange '
            'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
            f'PointSize="4.8" Leading="{leading:g}"><Content>•</Content>'
            '</CharacterStyleRange>'
            '<CharacterStyleRange '
            'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
            f'PointSize="{size:g}" Leading="{leading:g}"><Content> </Content>'
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


def _rounded_notice(ctx: RenderContext, *, tid: str, terminal: bool,
                    label: str, label_psr: str, body_psr: str, body_w: float,
                    label_w: float, lines: int) -> tuple[str, float]:
    # A four-item anchored group mirrors the LaTeX tcolorbox directly:
    # rounded grey shell, rounded white plate, centred label frame, and
    # the body frame.  A rounded frame nested in a table cell leaves an
    # overset anchor marker in InDesign, so the parts must be siblings.
    plate_left = param_pt(ctx.params, "comp_callout_label_inset", 3.4)
    body_inset = 3.75
    right_inset = param_pt(ctx.params, "comp_tip_pad_lr", 6.24)
    pad_tb = param_pt(ctx.params, "comp_caution_pad_tb", 3.4)
    plate_w = label_w - plate_left
    leading = param_pt(ctx.params, "type_tip_body_font_leading", 7.4)
    panel_h = leading * lines + 2 * pad_tb + 1.0
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
            param_pt(ctx.params, "comp_tip_arc", 6.8),
        )
        + anchor
        + '</Rectangle>\n'
    )
    plate = (
        f'<Rectangle Self="plate_notice_{tid}" ContentType="Unassigned" '
        'AppliedObjectStyle="ObjectStyle/HB Rounded Panel" '
        'FillColor="Color/Paper" StrokeColor="Swatch/None" '
        'StrokeWeight="0" ItemTransform="1 0 0 1 0 0">\n'
        + _po.rounded_path_geometry(
            plate_left,
            -panel_h + pad_tb,
            plate_left + plate_w,
            -pad_tb,
            5.5,
        )
        + anchor
        + '</Rectangle>\n'
    )

    def _text_frame(sid: str, self_id: str, x1: float, x2: float, *,
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
            + path_geometry(x1, -panel_h + pad_tb, x2, -pad_tb)
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
        right_text_inset=1.0,
    )
    body_left = plate_left + plate_w + body_inset
    body_frame = _text_frame(
        body_sid,
        f"tf_notice_body_{tid}",
        body_left,
        body_w - right_inset,
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
    label = spec.get("label", "")
    texts = spec.get("texts", [])
    label_size = param_pt(ctx.params, "type_tip_label_font_size", 8.0)
    label_leading = param_pt(ctx.params, "type_tip_label_font_leading", 9.0)
    body_size = param_pt(ctx.params, "type_tip_body_font_size", 6.5)
    body_leading = param_pt(ctx.params, "type_tip_body_font_leading", 7.4)
    label_w = param_pt(ctx.params, "comp_caution_label_width", 52.44)
    plate_left = param_pt(ctx.params, "comp_callout_label_inset", 3.4)
    label_available = label_w - plate_left - 1.0
    estimated_label_w = _gilroy_width(label, label_size) * 1.03
    if estimated_label_w > label_available:
        scale = label_available / estimated_label_w
        label_size = max(6.5, label_size * scale)
        label_leading = max(label_size + 0.8, label_leading * scale)
    label_psr = _typed(
        psr("HB Notice Side Label", label, terminal=True),
        label_size, label_leading, "Medium")
    body_psr = _body_xml(spec, body_size, body_leading)
    right_inset = param_pt(ctx.params, "comp_tip_pad_lr", 6.24)
    plate_w = label_w - plate_left
    body_frame_w = body_w - (
        plate_left + plate_w + 3.75 + right_inset)
    hanging_indent = 3.4 if spec.get("list") else 0.0
    available = max(20.0, body_frame_w - hanging_indent)
    lines = sum(_wrapped_lines(str(text), available, body_size)
                for text in texts) or 1
    if ctx.add_story is not None:
        return _rounded_notice(
            ctx, tid=tid, terminal=terminal, label=label, label_psr=label_psr,
            body_psr=body_psr, body_w=body_w, label_w=label_w, lines=lines)
    cols = [label_w, body_w - label_w]
    cells = [
        cell(f"{tid}c0", "0:0", label_psr, fill="Color/Paper", stroke=False,
             top=10, bottom=10, left=6, right=6),
        cell(f"{tid}c1", "1:0", body_psr, fill="Color/HB Bg K05", stroke=False,
             top=10, bottom=10, left=6, right=6),
    ]
    table = component_table(tid, cols, cells, role="notice")
    return wrap_table_paragraph(table, terminal, span_columns), max(
        24.0, body_leading * lines + 10)
