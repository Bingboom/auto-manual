"""Editable bicolor WARNING lead card used on the safety page."""
from __future__ import annotations

from xml.sax.saxutils import escape

from .. import page_objects as _po
from ..params import param_pt
from ..primitives import path_geometry, psr
from .base import RenderContext, figure_paragraph


def _icon_asset(ctx: RenderContext):
    return (
        ctx.root / "docs" / "templates" / "word_template" / "common_assets"
        / "symbols" / "warning_triangle_white.svg"
    )


def rounded_warninglead(
    spec: dict,
    ctx: RenderContext,
    *,
    tid: str,
    terminal: bool,
    body_w: float,
) -> tuple[str, float]:
    panel_h = param_pt(ctx.params, "comp_warning_lead_height", 39.69)
    panel_w = body_w - param_pt(ctx.params, "comp_warning_lead_width_trim", 2.13)
    rule = param_pt(ctx.params, "comp_warning_box_rule", 0.75)
    radius = param_pt(ctx.params, "comp_warning_box_arc", 5.67)
    dark_w = param_pt(ctx.params, "comp_warning_lead_dark_width", 41.39) + rule
    left_pad = param_pt(ctx.params, "comp_warning_lead_text_left_pad", 4.96) - 0.4
    right_pad = param_pt(ctx.params, "comp_warning_lead_right_pad", 5.10)
    label = str(spec.get("label", ""))
    body = "\n".join(str(text) for text in spec.get("texts", []) if text)
    label_xml = psr("HB Warning Lead Label", label).replace(
        "<ParagraphStyleRange ", '<ParagraphStyleRange SpaceAfter="1.985" ', 1)
    body_xml = psr("HB Warning Lead Body", body, terminal=True)
    text_sid = ctx.add_story(
        f"st_anchor_warninglead_text_{tid}", f"{label} warning lead text",
        [label_xml, body_xml])
    anchor = (
        '    <AnchoredObjectSetting AnchoredPosition="InlinePosition" '
        'SpineRelative="false" LockPosition="false" PinPosition="true" '
        'AnchorPoint="BottomRightAnchor" HorizontalAlignment="LeftAlign" '
        'HorizontalReferencePoint="TextFrame" VerticalAlignment="TopAlign" '
        'VerticalReferencePoint="LineBaseline" AnchorXoffset="0" '
        'AnchorYoffset="0" AnchorSpaceAbove="0"/>\n'
    )
    outer = (
        f'<Rectangle Self="bg_warninglead_{tid}" ContentType="Unassigned" '
        'AppliedObjectStyle="ObjectStyle/HB Rounded Panel" '
        'FillColor="Color/Paper" StrokeColor="Color/HB Brand Dark" '
        f'StrokeWeight="{rule:g}" ItemTransform="1 0 0 1 0 0">\n'
        + _po.rounded_path_geometry(0.0, -panel_h, panel_w, 0.0, radius)
        + anchor + '</Rectangle>\n'
    )
    dark_plate = (
        f'<Rectangle Self="plate_warninglead_{tid}" ContentType="Unassigned" '
        'AppliedObjectStyle="ObjectStyle/HB Rounded Panel" '
        'FillColor="Color/HB Brand Dark" StrokeColor="Swatch/None" '
        'StrokeWeight="0" ItemTransform="1 0 0 1 0 0">\n'
        + _po.left_rounded_path_geometry(0.0, -panel_h, dark_w, 0.0, radius)
        + anchor + '</Rectangle>\n'
    )
    icon = ""
    icon_asset = _icon_asset(ctx)
    if icon_asset.exists():
        icon_w = param_pt(ctx.params, "comp_warning_lead_icon_width", 29.48) * 0.96
        icon_h = param_pt(ctx.params, "comp_warning_lead_icon_height", 26.22) * 0.96
        icon_x = (dark_w - icon_w) / 2.0
        icon_bottom = -(panel_h - icon_h) / 2.0
        uri = escape(icon_asset.resolve().as_uri(), {'"': "&quot;"})
        icon = (
            f'<Rectangle Self="icon_warninglead_{tid}" ContentType="GraphicType" '
            'AppliedObjectStyle="ObjectStyle/$ID/[None]" '
            'FillColor="Swatch/None" StrokeColor="Swatch/None" StrokeWeight="0" '
            'ItemTransform="1 0 0 1 0 0">\n'
            + path_geometry(icon_x, icon_bottom - icon_h, icon_x + icon_w, icon_bottom)
            + anchor
            + f'<Image Self="icon_warninglead_{tid}_img" ItemTransform="1 0 0 1 0 0">'
            f'<Link Self="icon_warninglead_{tid}_lnk" LinkResourceURI="{uri}"/>'
            '</Image><FrameFittingOption FittingOnEmptyFrame="Proportionally"/>'
            '</Rectangle>\n'
        )
    inset_xml = ''.join('<ListItem type="unit">0</ListItem>' for _ in range(4))
    text_frame = (
        f'<TextFrame Self="tf_warninglead_{tid}" ParentStory="{text_sid}" '
        'PreviousTextFrame="n" NextTextFrame="n" ContentType="TextType" '
        'AppliedObjectStyle="ObjectStyle/$ID/[Normal Text Frame]" '
        'FillColor="Swatch/None" StrokeColor="Swatch/None" StrokeWeight="0" '
        'ItemTransform="1 0 0 1 0 0">\n'
        + path_geometry(dark_w + left_pad, -panel_h, panel_w - right_pad, 0.0)
        + '    <TextFramePreference TextColumnCount="1" '
        'VerticalJustification="CenterAlign" AutoSizingType="Off">'
        f'<Properties><InsetSpacing type="list">{inset_xml}'
        '</InsetSpacing></Properties></TextFramePreference>\n'
        + anchor + '</TextFrame>\n'
    )
    group = (
        f'<Group Self="grp_warninglead_{tid}" '
        'AppliedObjectStyle="ObjectStyle/$ID/[None]" ItemTransform="1 0 0 1 0 0">\n'
        + outer + dark_plate + icon + text_frame + '</Group>'
    )
    tail = '<Content></Content>' + ('' if terminal else '<Br/>')
    host = figure_paragraph(group, tail=tail).replace(
        "<ParagraphStyleRange ", '<ParagraphStyleRange SpaceAfter="0.47" ', 1)
    return host, panel_h + 0.47
