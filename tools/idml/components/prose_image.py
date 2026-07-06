"""Prose-page inline art — the extractor's ``("image", ref)`` block
(componentization P2). Returns ``(None, 0.0)`` when the reference does not
resolve in the bundle, so the story skips it without consuming an id.
"""
from __future__ import annotations

from ..primitives import image_cell_content
from ..style_names import paragraph_style_ref
from .base import RenderContext


def render_image_block(ref: str, ctx: RenderContext, *, rect_id: str,
                       terminal: bool) -> tuple[str | None, float]:
    img = ctx.resolve_bundle_image(ref)
    if img is None:
        return None, 0.0
    w_pt, h_pt = ctx.art_frame_size(img)
    rect = image_cell_content(rect_id, img, w_pt, h_pt)
    style_ref = paragraph_style_ref("HB Figure")
    xml = (
        f'  <ParagraphStyleRange AppliedParagraphStyle="{style_ref}">'
        '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
        + rect + ("<Content></Content>" if terminal else "<Br/>")
        + "</CharacterStyleRange></ParagraphStyleRange>\n")
    return xml, h_pt + 4
