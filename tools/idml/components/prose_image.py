"""Prose-page inline art — the extractor's ``("image", ref)`` block
(componentization P2). Returns ``(None, 0.0)`` when the reference does not
resolve in the bundle, so the story skips it without consuming an id.
"""
from __future__ import annotations

from ..params import param_pt
from ..primitives import image_cell_content
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
IMAGE_ROLE_WIDE_DIAGRAM = "wide_diagram"
IMAGE_ROLE_COMPACT_DIAGRAM = "compact_diagram"
IMAGE_ROLE_CHARGING_DIAGRAM = "charging_diagram"

_ROLE_WIDTH_RATIOS = {
    IMAGE_ROLE_FULL_MEASURE: (
        "idml_semantic_image_full_measure_ratio",
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


def render_image_block(
    ref: str,
    ctx: RenderContext,
    *,
    rect_id: str,
    terminal: bool,
    role: str | None = None,
) -> tuple[str | None, float]:
    img = ctx.resolve_bundle_image(ref)
    if img is None:
        return None, 0.0
    max_w = _semantic_max_width(ref, img.as_posix(), ctx, role=role)
    w_pt, h_pt = ctx.art_frame_size(img, max_w=max_w)
    rect = image_cell_content(
        rect_id, img, w_pt, h_pt, anchored_position="AboveLine")
    style_ref = paragraph_style_ref("HB Figure")
    xml = (
        f'  <ParagraphStyleRange AppliedParagraphStyle="{style_ref}">'
        '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
        + rect + ("<Content></Content>" if terminal else "<Br/>")
        + "</CharacterStyleRange></ParagraphStyleRange>\n")
    space_before = param_pt(ctx.params, "idml_figure_space_before", 2.83)
    space_after = param_pt(ctx.params, "idml_figure_space_after", 4.25)
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
