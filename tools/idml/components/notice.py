"""Shared LaTeX-parity NOTE / TIP / CAUTION / WARNING strip."""
from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass, replace

from .. import page_objects as _po
from ..character_metrics import with_character_metrics
from ..params import component_param_pt, param_pt, param_text
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
    xml = with_character_metrics(xml, point_size=size, leading=leading)
    # A paragraph-ending Br run participates in InDesign's line leading.  If
    # it keeps the base HB Callout Body metrics (7.83 pt), a role-calibrated
    # 6 pt list silently expands on import and can overset despite a correct
    # text measurement.  Keep the break run on the same explicit metrics as
    # its visible text; the generic helper intentionally leaves such runs
    # alone for other component families.
    break_pattern = re.compile(
        r'<CharacterStyleRange (?P<attrs>[^>]*)>'
        r'(?P<body>(?:(?!</CharacterStyleRange>).)*<Br/>'
        r'(?:(?!</CharacterStyleRange>).)*)</CharacterStyleRange>',
        re.S,
    )

    def apply_break_metrics(match: re.Match[str]) -> str:
        attrs = re.sub(r'\s+PointSize="[^"]*"', "", match.group("attrs"))
        body = match.group("body")
        leading_xml = f'<Leading type="unit">{leading:g}</Leading>'
        if "<Properties>" in body:
            body = body.replace("<Properties>", "<Properties>" + leading_xml, 1)
        else:
            body = f"<Properties>{leading_xml}</Properties>" + body
        return (
            f'<CharacterStyleRange {attrs} PointSize="{size:g}">'
            f"{body}</CharacterStyleRange>"
        )

    xml = break_pattern.sub(apply_break_metrics, xml)

    def apply_style(match: re.Match[str]) -> str:
        tag = match.group(0)
        attrs: list[str] = []
        # Symbol fallback runs already carry the only valid face for their
        # fallback font.  Preserve it instead of emitting duplicate
        # FontStyle attributes that make the IDML XML invalid.
        if weight and " FontStyle=" not in tag:
            attrs.append(f'FontStyle="{weight}"')
        if horizontal_scale is not None and " HorizontalScale=" not in tag:
            attrs.append(f'HorizontalScale="{horizontal_scale * 100:g}"')
        if baseline_shift is not None and " BaselineShift=" not in tag:
            attrs.append(f'BaselineShift="{baseline_shift:g}"')
        return tag[:-1] + (" " + " ".join(attrs) if attrs else "") + ">"

    return re.sub(r"<CharacterStyleRange\b[^>]*>", apply_style, xml)


def _body_xml(spec: dict, size: float, leading: float,
              horizontal_scale: float, baseline_shift: float,
              paragraph_space_after: float = 0.0,
              unbulleted_first: bool = False,
              font_style: str = "Medium") -> str:
    texts = spec.get("texts", [])
    if not spec.get("list"):
        return _typed(
            psr("HB Callout Body", "\n".join(texts), terminal=True),
            size,
            leading,
            font_style,
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
            font_style,
            horizontal_scale=horizontal_scale,
            baseline_shift=baseline_shift,
        )
        has_bullet = not (unbulleted_first and index == 0)
        if has_bullet:
            paragraph = paragraph.replace(
                "<ParagraphStyleRange ",
                '<ParagraphStyleRange LeftIndent="3.4" FirstLineIndent="-3.4" ',
                1,
            )
        if paragraph_space_after and index < len(items) - 1:
            paragraph = paragraph.replace(
                "<ParagraphStyleRange ",
                f'<ParagraphStyleRange SpaceAfter="{paragraph_space_after:g}" ',
                1,
            )
        bullet = (
            '<CharacterStyleRange '
            'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
            f'PointSize="4.8" BaselineShift="{baseline_shift:g}">'
            f'<Properties><Leading type="unit">{leading:g}</Leading></Properties>'
            '<Content>•</Content>'
            '</CharacterStyleRange>'
            '<CharacterStyleRange '
            'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
            f'PointSize="{size:g}" FontStyle="{font_style}" '
            f'HorizontalScale="{horizontal_scale * 100:g}" '
            f'BaselineShift="{baseline_shift:g}">'
            f'<Properties><Leading type="unit">{leading:g}</Leading></Properties>'
            '<Content> </Content>'
            '</CharacterStyleRange>'
        )
        if has_bullet:
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


def _remeasure_notice_layout(
    layout: NoticeBoxLayout,
    *,
    params: dict,
    spec: dict,
    label: str,
    texts: list,
    text_frame_safety: float = 0.0,
) -> NoticeBoxLayout:
    """Fit label/body after every reference geometry/type override is known."""
    label_available = layout.plate_width - 1.0
    if label_available <= 0:
        raise ValueError("notice label frame has no usable width")
    estimated_label_width = _gilroy_width(label, layout.label_size) * 1.03
    label_size = layout.label_size
    label_leading = layout.label_leading
    if estimated_label_width > label_available:
        scale = label_available / estimated_label_width
        label_size = max(1.0, layout.label_size * scale)
        label_leading = max(
            label_size + 0.8,
            layout.label_leading * scale,
        )

    body_frame_width = layout.body_width - (
        layout.plate_left
        + layout.plate_width
        + layout.body_inset
        + layout.right_inset
    )
    hanging_indent = 3.4 if spec.get("list") else 0.0
    available = body_frame_width - hanging_indent
    if available <= 0:
        raise ValueError("notice body frame has no usable width")
    lines = sum(
        _wrapped_lines(
            str(text),
            available,
            layout.body_size * layout.body_horizontal_scale,
        )
        for text in texts
    ) or 1
    nonempty_items = [text for text in texts if str(text).strip()]
    paragraph_space = (
        float(spec.get("paragraph_space_after") or 0.0)
        * max(0, len(nonempty_items) - 1)
        if spec.get("list")
        else 0.0
    )
    natural_body_height = (
        layout.body_leading * lines
        + paragraph_space
        + 2 * layout.pad_tb
        + 1.0
        + text_frame_safety
    )
    label_height = label_leading + 2 * layout.plate_left + 1.0
    requested_height = float(spec.get("panel_height") or 0.0)
    if requested_height < 0:
        raise ValueError("notice panel_height must be greater than zero")
    variant_height = (
        param_pt(params, "comp_tip_height", 41.67)
        if str(spec.get("variant", "")) == "tip"
        else 0.0
    )
    return replace(
        layout,
        label_size=label_size,
        label_leading=label_leading,
        lines=lines,
        panel_height=max(
            requested_height,
            variant_height,
            natural_body_height,
            label_height,
        ),
    )


def _rounded_notice(ctx: RenderContext, *, tid: str, terminal: bool,
                    label: str, label_psr: str, body_psr: str,
                    layout: NoticeBoxLayout,
                    inline_x_offset: float = 0.0,
                    space_before: float = 0.0,
                    space_after: float = 1.8) -> tuple[str, float]:
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
    def anchor(*, pin: bool) -> str:
        return (
        '    <AnchoredObjectSetting AnchoredPosition="InlinePosition" '
        f'SpineRelative="false" LockPosition="false" PinPosition="{str(pin).lower()}" '
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
        + anchor(pin=True)
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
        + anchor(pin=True)
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
            + anchor(pin=False)
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
        f'ItemTransform="1 0 0 1 {inline_x_offset:g} 0">\n'
        + outer + plate + label_frame + body_frame + '</Group>'
    )
    tail = '<Content></Content>' + ('' if terminal else '<Br/>')
    xml = figure_paragraph(group, tail=tail)
    # The fixed page-frame boundary leaves 0.89 pt after the upper DC
    # callout; LaTeX keeps 2.68 pt before ENERGY SAVING MODE.
    xml = xml.replace(
        "<ParagraphStyleRange ",
        f'<ParagraphStyleRange SpaceBefore="{space_before:g}" '
        f'SpaceAfter="{space_after:g}" ',
        1,
    )
    gap = param_pt(ctx.params, "comp_data_table_before", 3.4)
    return xml, panel_h + 2 * gap


def render_notice(spec: dict, ctx: RenderContext, *, tid: str, terminal: bool,
                  span_columns: bool = True,
                  measure_w: float | None = None) -> tuple[str, float]:
    body_w = float(spec.get("body_width") or measure_w or ctx.text_measure)
    if body_w <= 0:
        raise ValueError("notice body_width must be greater than zero")
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
    plate_left = float(spec.get("plate_left", layout.plate_left))
    label_width = float(spec.get("label_width", layout.label_width))
    if plate_left < 0 or label_width <= plate_left:
        raise ValueError("notice label geometry is invalid")
    layout = replace(
        layout,
        label_width=label_width,
        plate_left=plate_left,
        plate_width=label_width - plate_left,
        body_inset=float(spec.get("body_inset", layout.body_inset)),
        right_inset=float(spec.get("right_inset", layout.right_inset)),
        pad_tb=float(spec.get("pad_tb", layout.pad_tb)),
        label_size=float(spec.get("label_size", layout.label_size)),
        label_leading=float(spec.get("label_leading", layout.label_leading)),
        body_size=float(spec.get("body_size", layout.body_size)),
        body_leading=float(spec.get("body_leading", layout.body_leading)),
    )
    layout_role = str(spec.get("layout_role") or "").strip()
    language = (ctx.language or "en").split("-", 1)[0]

    def role_pt(suffix: str, default: float) -> float:
        key = f"idml_{layout_role}_{suffix}"
        return param_pt(
            ctx.params,
            f"lang_{language}_{key}",
            param_pt(ctx.params, key, default),
        )

    def role_text(suffix: str, default: str) -> str:
        key = f"idml_{layout_role}_{suffix}"
        return param_text(
            ctx.params,
            f"lang_{language}_{key}",
            param_text(ctx.params, key, default),
        )

    body_font_style = str(spec.get("body_font_style") or "Medium")
    paragraph_space_after = float(spec.get("paragraph_space_after") or 0.0)
    notice_space_before = float(spec.get("space_before") or 0.0)
    notice_space_after = float(spec.get("space_after") or 1.8)
    if layout_role in {"ups_caution", "charging_note"}:
        layout = replace(
            layout,
            body_size=role_pt("body_font_size", layout.body_size),
            body_leading=role_pt("body_font_leading", layout.body_leading),
            pad_tb=role_pt("pad_tb", layout.pad_tb),
        )
        body_font_style = role_text("body_font_style", "Regular")
        paragraph_space_after = role_pt("paragraph_after", 1.0)
        notice_space_before = role_pt("space_before", notice_space_before)
        notice_space_after = role_pt("space_after", notice_space_after)
    layout = _remeasure_notice_layout(
        layout,
        params=ctx.params,
        spec={**spec, "paragraph_space_after": paragraph_space_after},
        label=label,
        texts=texts,
        text_frame_safety=(
            component_param_pt(
                ctx.params,
                "idml_app_notice_text_frame_safety",
                1.6,
                strict=ctx.strict_component_assets,
                owner="App notice",
            )
            if spec.get("app_text_frame_safety")
            else 0.0
        ),
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
        paragraph_space_after,
        bool(spec.get("unbulleted_first")),
        body_font_style,
    )
    if ctx.add_story is not None:
        return _rounded_notice(
            ctx, tid=tid, terminal=terminal, label=label, label_psr=label_psr,
            body_psr=body_psr, layout=layout,
            inline_x_offset=float(spec.get("inline_x_offset") or 0.0),
            space_before=notice_space_before,
            space_after=notice_space_after,
        )
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
