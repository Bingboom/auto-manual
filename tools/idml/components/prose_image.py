"""Prose-page inline art — the extractor's ``("image", ref)`` block
(componentization P2). Returns ``(None, 0.0)`` when the reference does not
resolve in the bundle, so the story skips it without consuming an id.
"""
from __future__ import annotations

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


def _semantic_max_width(ref: str, resolved: str, ctx: RenderContext) -> float:
    paths = (ref.replace("\\", "/"), resolved.replace("\\", "/"))
    if any(path.endswith(("front_product.jpg", "right_side_ports.png")) for path in paths):
        return ctx.text_measure
    if any(path.endswith(_FULL_MEASURE_SUFFIXES) for path in paths):
        return ctx.text_measure
    for suffix, ratio in _APP_MEASURE_RATIOS.items():
        if any(path.endswith(suffix) for path in paths):
            return ctx.text_measure * ratio
    return 120.0


def render_image_block(ref: str, ctx: RenderContext, *, rect_id: str,
                       terminal: bool) -> tuple[str | None, float]:
    img = ctx.resolve_bundle_image(ref)
    if img is None:
        return None, 0.0
    max_w = _semantic_max_width(ref, img.as_posix(), ctx)
    w_pt, h_pt = ctx.art_frame_size(img, max_w=max_w)
    rect = image_cell_content(
        rect_id, img, w_pt, h_pt, anchored_position="AboveLine")
    style_ref = paragraph_style_ref("HB Figure")
    xml = (
        f'  <ParagraphStyleRange AppliedParagraphStyle="{style_ref}">'
        '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
        + rect + ("<Content></Content>" if terminal else "<Br/>")
        + "</CharacterStyleRange></ParagraphStyleRange>\n")
    if ref.endswith("front_product.jpg"):
        xml = xml.replace(
            "<ParagraphStyleRange ",
            '<ParagraphStyleRange SpaceAfter="1.58" ',
            1,
        )
    return xml, h_pt + 4
