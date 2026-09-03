"""Prose-page inline art — the extractor's ``("image", ref)`` block
(componentization P2). Returns ``(None, 0.0)`` when the reference does not
resolve in the bundle, so the story skips it without consuming an id.
"""
from __future__ import annotations

import json
from collections.abc import Sequence

from ..character_metrics import with_character_metrics
from ..params import param_pt
from ..primitives import image_cell_content, path_geometry, psr
from ..source_copy import source_text
from ..style_names import paragraph_style_ref
from .base import RenderContext


_FULL_MEASURE_SUFFIXES = (
    "/operation/energy_saving.png",
    "/operation/led_light.png",
    "/operation/ups_mode.png",
    "/charging/ac_wall.png",
    "/charging/solar_direct.png",
    "/charging/solar_adapter.png",
    "/charging/car_charge.png",
    "/assets/op_energy_saving.png",
    "/assets/op_ups_mode.png",
    "/assets/solar_adapter.png",
    "/assets/car_charge.png",
)
_APP_MEASURE_RATIOS = {
    "/app/download.png": 0.60,
    "/app/add_device.png": 0.55,
    "/app/connect_result.png": 0.58,
    "/app/je1000f_us/add_device_je1000f_us.png": 0.55,
    "/app/je1000f_us/connect_result_je1000f_us.png": 0.58,
}

IMAGE_ROLE_DEFAULT = "default"
IMAGE_ROLE_FULL_MEASURE = "full_measure"
IMAGE_ROLE_HALF_MEASURE = "half_measure"
IMAGE_ROLE_REFERENCE_MEASURE = "reference_measure"
IMAGE_ROLE_WIDE_DIAGRAM = "wide_diagram"
IMAGE_ROLE_COMPACT_DIAGRAM = "compact_diagram"
IMAGE_ROLE_CHARGING_DIAGRAM = "charging_diagram"

_ROLE_WIDTH_RATIOS = {
    IMAGE_ROLE_FULL_MEASURE: (
        "idml_semantic_image_full_measure_ratio",
        1.0,
    ),
    IMAGE_ROLE_HALF_MEASURE: (
        "idml_semantic_image_half_measure_ratio",
        0.46,
    ),
    IMAGE_ROLE_REFERENCE_MEASURE: (
        "idml_semantic_image_reference_measure_ratio",
        1.0,
    ),
    IMAGE_ROLE_WIDE_DIAGRAM: (
        "idml_semantic_image_wide_diagram_ratio",
        0.78,
    ),
    IMAGE_ROLE_COMPACT_DIAGRAM: (
        "idml_semantic_image_compact_diagram_ratio",
        0.62,
    ),
    IMAGE_ROLE_CHARGING_DIAGRAM: (
        "idml_semantic_image_charging_diagram_ratio",
        0.58,
    ),
}


def _role_max_width(role: str | None, ctx: RenderContext) -> float | None:
    """Resolve target-neutral image geometry before legacy path fallbacks."""

    if role in (None, IMAGE_ROLE_DEFAULT):
        return None
    try:
        token, default = _ROLE_WIDTH_RATIOS[role]
    except KeyError as exc:
        raise ValueError(f"unsupported semantic image role: {role}") from exc
    language = (ctx.language or "").strip().casefold().replace("_", "-")
    language = language.split("-", 1)[0]
    ratio = param_pt(
        ctx.params,
        f"lang_{language}_{token}" if language else token,
        param_pt(ctx.params, token, default),
    )
    if not 0.0 < ratio <= 1.0:
        raise ValueError(
            f"semantic image width ratio must be in (0, 1]: {token}={ratio:g}"
        )
    return ctx.text_measure * ratio


def _semantic_max_width(
    ref: str,
    resolved: str,
    ctx: RenderContext,
    *,
    role: str | None = None,
) -> float:
    role_width = _role_max_width(role, ctx)
    if role_width is not None:
        return role_width
    paths = (ref.replace("\\", "/"), resolved.replace("\\", "/"))
    if any(path.endswith(("front_product.jpg", "right_side_ports.png")) for path in paths):
        return ctx.text_measure
    if any(path.endswith(_FULL_MEASURE_SUFFIXES) for path in paths):
        return ctx.text_measure
    for suffix, ratio in _APP_MEASURE_RATIOS.items():
        if any(path.endswith(suffix) for path in paths):
            return ctx.text_measure * ratio
    return 120.0


# Children of a figure group share the group's own space: x runs 0..image width
# and y runs 0..image height, downward from the art's top-left corner, which is
# the space ``image_cell_content`` already places the art rectangle in.
_FIGURE_CHILD_ANCHOR = (
    '<AnchoredObjectSetting AnchoredPosition="AboveLine" SpineRelative="false" '
    'LockPosition="false" PinPosition="true" AnchorPoint="BottomRightAnchor" '
    'HorizontalAlignment="LeftAlign" HorizontalReferencePoint="TextFrame" '
    'VerticalAlignment="TopAlign" VerticalReferencePoint="LineBaseline" '
    'AnchorXoffset="0" AnchorYoffset="0" AnchorSpaceAbove="0"/>'
)

# The shipped books set these labels at 6 pt Regular.  `HB Spec Value` is the
# one existing paragraph style at that weight, and Japanese inherits Regular
# from it because it carries no entry in the localized weight map.  Size and
# leading are declared here rather than inherited so a spec-table retune cannot
# move a figure callout; a dedicated `HB Figure Callout` style would read better
# but would add a definition to every book's style table, and these labels exist
# in one book.
_CALLOUT_STYLE = "HB Spec Value"


def _callout_frames(
    ctx: RenderContext,
    *,
    rect_id: str,
    callouts: Sequence[tuple[dict, str]],
    w_pt: float,
    h_pt: float,
) -> str:
    """Return editable label frames positioned inside a figure's own space."""

    if ctx.add_story is None:
        return ""
    point_size = param_pt(ctx.params, "idml_figure_callout_font_size", 6.0)
    leading = param_pt(ctx.params, "idml_figure_callout_font_leading", 7.0)
    frames: list[str] = []
    for index, (callout, text) in enumerate(callouts):
        label = source_text(text, owner=f"figure callout {index + 1} label")
        left = float(callout["x"]) * w_pt
        width = float(callout["width"]) * w_pt
        height = leading + 1.0
        top = float(callout["y"]) * h_pt - height / 2.0
        story_id = f"st_anchor_callout_{rect_id}_{index}"
        sid = ctx.add_story(
            story_id,
            f"{rect_id} callout {index + 1}",
            [
                with_character_metrics(
                    psr(_CALLOUT_STYLE, label, terminal=True),
                    point_size=point_size,
                    leading=leading,
                )
            ],
        )
        inset = "".join('<ListItem type="unit">0</ListItem>' for _ in range(4))
        frames.append(
            f'<TextFrame Self="tf_callout_{rect_id}_{index}" ParentStory="{sid}" '
            'PreviousTextFrame="n" NextTextFrame="n" ContentType="TextType" '
            'AppliedObjectStyle="ObjectStyle/$ID/[Normal Text Frame]" '
            'FillColor="Swatch/None" StrokeColor="Swatch/None" StrokeWeight="0" '
            'ItemTransform="1 0 0 1 0 0">'
            + path_geometry(left, top, left + width, top + height)
            + '<TextFramePreference TextColumnCount="1" '
            'VerticalJustification="CenterAlign" AutoSizingType="Off">'
            f'<Properties><InsetSpacing type="list">{inset}'
            '</InsetSpacing></Properties></TextFramePreference>'
            + _FIGURE_CHILD_ANCHOR
            + "</TextFrame>"
        )
    return "".join(frames)


def plan_figure_callouts(
    blocks: list[tuple[str, str]],
    declared_per_figure: tuple[tuple[dict, ...], ...],
) -> tuple[dict[int, tuple[tuple[dict, str], ...]], set[int]]:
    """Resolve each figure's callouts and the label tables they consume.

    Returns the callouts keyed by the figure's own block index, plus the block
    indices of the label tables now printed over the art instead of under it.
    A figure with nothing declared contributes neither, which is what keeps
    every other target rendering exactly what it rendered before.
    """

    planned: dict[int, tuple[tuple[dict, str], ...]] = {}
    consumed: set[int] = set()
    if not declared_per_figure:
        return planned, consumed
    figure = 0
    for index, (kind, _text) in enumerate(blocks):
        if kind != "image":
            continue
        declared = (
            declared_per_figure[figure]
            if figure < len(declared_per_figure)
            else ()
        )
        figure += 1
        if declared:
            planned[index] = _paired_figure_callouts(
                blocks, index, declared, consumed,
            )
    return planned, consumed


def _paired_figure_callouts(
    blocks: list[tuple[str, str]],
    image_index: int,
    declared: tuple[dict, ...],
    consumed: set[int],
) -> tuple[tuple[dict, str], ...]:
    """Bind each declared callout to the label the source table supplies.

    Copy stays in the page source, where translation and review can reach it;
    the target contract supplies only where each label sits. The pairing is by
    cell ordinal, the way the LCD hero callouts bind to their parts rows.
    """

    table_index = next(
        (
            index
            for index in range(image_index + 1, len(blocks))
            if blocks[index][0] == "table"
        ),
        None,
    )
    if table_index is None:
        raise ValueError(
            f"figure callouts at image {image_index} need a following label table"
        )
    rows = json.loads(blocks[table_index][1])
    cells = [str(cell) for cell in (rows[0] if rows else [])]
    paired: list[tuple[dict, str]] = []
    for callout in declared:
        ordinal = int(callout["cell_index"])
        if ordinal >= len(cells):
            raise ValueError(
                f"figure callout cell_index {ordinal} exceeds "
                f"{len(cells)} label cells"
            )
        paired.append((callout, cells[ordinal]))
    consumed.add(table_index)
    return tuple(paired)


def render_image_block(
    ref: str,
    ctx: RenderContext,
    *,
    rect_id: str,
    terminal: bool,
    role: str | None = None,
    spacing_variant: str | None = None,
    callouts: Sequence[tuple[dict, str]] = (),
) -> tuple[str | None, float]:
    img = ctx.resolve_bundle_image(ref)
    if img is None:
        return None, 0.0
    max_w = _semantic_max_width(ref, img.as_posix(), ctx, role=role)
    w_pt, h_pt = ctx.art_frame_size(img, max_w=max_w)
    art = image_cell_content(
        rect_id, img, w_pt, h_pt, anchored_position="AboveLine")
    if callouts:
        # One group is one inline anchored object, so the labels sit over the
        # art instead of being advanced past it, and the whole assembly travels
        # with the flow -- the contract the notice panel already uses.
        art = (
            f'<Group Self="grp_{rect_id}" '
            'AppliedObjectStyle="ObjectStyle/$ID/[None]" '
            'ItemTransform="1 0 0 1 0 0">'
            + art
            + _callout_frames(
                ctx, rect_id=rect_id, callouts=callouts, w_pt=w_pt, h_pt=h_pt,
            )
            + "</Group>"
        )
    style_ref = paragraph_style_ref("HB Figure")
    xml = (
        f'  <ParagraphStyleRange AppliedParagraphStyle="{style_ref}">'
        '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
        + art + ("<Content></Content>" if terminal else "<Br/>")
        + "</CharacterStyleRange></ParagraphStyleRange>\n")
    space_before = param_pt(ctx.params, "idml_figure_space_before", 2.83)
    space_after = param_pt(ctx.params, "idml_figure_space_after", 4.25)
    if spacing_variant == "charging":
        # Above-line image paragraphs already contribute their native line
        # box.  Charging's diagram-to-heading transition therefore needs no
        # second pair of explicit margins on top of that line box.
        space_before = param_pt(
            ctx.params,
            "idml_charging_figure_space_before",
            space_before,
        )
        space_after = param_pt(
            ctx.params,
            "idml_charging_figure_space_after",
            0.0,
        )
    if any(
        path.endswith(("/operation/ups_mode.png", "/assets/op_ups_mode.png"))
        for path in (ref.replace("\\", "/"), img.as_posix())
    ):
        language = (ctx.language or "en").split("-", 1)[0]
        space_before = param_pt(
            ctx.params,
            f"lang_{language}_idml_ups_image_space_before",
            param_pt(ctx.params, "idml_ups_image_space_before", 5.2),
        )
    if ref.endswith("front_product.jpg"):
        space_after = 1.58
    xml = xml.replace(
        "<ParagraphStyleRange ",
        f'<ParagraphStyleRange SpaceBefore="{space_before:g}" '
        f'SpaceAfter="{space_after:g}" ',
        1,
    )
    return xml, h_pt + space_before + space_after
