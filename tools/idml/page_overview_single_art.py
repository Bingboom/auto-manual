"""Target-independent single-art product-overview component frames."""
from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from .page_objects import (
    frame_with_background,
    h1_bar_h_pt,
    heading_bar_opts,
    heading_text,
)
from .params import param_pt

_ATTR = {'"': "&quot;"}
Block = tuple[str, object]


def _graphic_frame(writer, rect_id: str, asset: Path,
                   rect: tuple[float, float, float, float]) -> str:
    """Absolute linked-art frame; deliberately smaller than a full page."""
    x1, y1, x2, y2 = writer._page_rect(*rect)
    return (
        f'  <Rectangle Self="{rect_id}" ContentType="GraphicType" '
        'AppliedObjectStyle="ObjectStyle/$ID/[None]" '
        'StrokeColor="Swatch/None" StrokeWeight="0" '
        'ItemTransform="1 0 0 1 0 0">\n'
        + writer._path_geometry(x1, y1, x2, y2)
        + f'    <Image Self="{rect_id}_img" ItemTransform="1 0 0 1 {x1:g} {y1:g}">\n'
        f'      <Link Self="{rect_id}_lnk" '
        f'LinkResourceURI="{escape(asset.resolve().as_uri(), _ATTR)}"/>\n'
        '    </Image>\n'
        '    <FrameFittingOption FittingOnEmptyFrame="Proportionally" '
        'FittingAlignment="CenterAnchor" AutoFit="true"/>\n'
        '  </Rectangle>\n'
    )


def single_image_overview_frames(
    writer,
    sid: str,
    blocks: list[Block],
    bundle_root: Path,
    *,
    page_top: float | None = None,
    image_height: float | None = None,
) -> list[str]:
    """Build the shared single-art overview component without owning a page.

    A page compositor may place these frames alone or combine them with other
    components.  The semantic and asset validation is identical in both cases.
    """

    h1 = next((str(value) for kind, value in blocks if kind == "h1"), "")
    h2s = [str(value) for kind, value in blocks if kind == "h2"]
    image_refs = [str(value) for kind, value in blocks if kind == "image"]
    if not h1 or h2s or len(image_refs) != 1:
        raise ValueError("single-art product overview requires one h1 and one image")
    asset = writer._resolve_bundle_image(bundle_root, image_refs[0])
    if asset is None:
        raise ValueError("product overview contains an unresolved governed image")
    body_x = writer.m_l
    body_w = writer.page_w - writer.m_l - writer.m_r
    top = (
        param_pt(writer.params, "idml_shared_page_top", 27.7)
        if page_top is None
        else page_top
    )
    title_h = h1_bar_h_pt(writer)
    image_gap = param_pt(
        writer.params,
        "idml_overview_composite_title_gap",
        4.0,
    )
    image_h = (
        param_pt(writer.params, "idml_overview_composite_height", 142.0)
        if image_height is None
        else image_height
    )
    title_sid = writer._add_story_parts(
        f"{sid}_title", h1, [heading_text(writer, h1, level=1)],
    )
    return [
        frame_with_background(
            writer,
            sid,
            "title",
            title_sid,
            (body_x, top, body_w, title_h),
            {
                **heading_bar_opts(1, (1.5, 5.0, 1.0, 6.0)),
                "text_rect": (body_x + 6.0, top, body_w - 12.0, title_h),
            },
        ),
        _graphic_frame(
            writer,
            f"art_{sid}_composite",
            asset,
            (body_x, top + title_h + image_gap, body_w, image_h),
        ),
    ]
