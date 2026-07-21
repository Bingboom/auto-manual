"""Editable figure composites used by approved reference-page replicas.

The linked artwork remains the immutable bottom layer.  Every localized label
is emitted as its own unlocked text frame at the end of the group, so an
InDesign operator can move or edit copy without repainting the illustration.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

try:
    from tools.safe_copy import prepare_file_destination_no_symlinks
except ModuleNotFoundError:  # direct tools/export_idml.py execution
    from safe_copy import prepare_file_destination_no_symlinks  # type: ignore

from ..primitives import (
    cell,
    component_table,
    image_cell_content,
    psr,
    wrap_table_paragraph,
)
from .base import RenderContext, figure_paragraph
from .oppanel import (
    _editable_text_frame,
    _inline_anchor,
    _positioned_image,
    _shape,
    _sized_psr,
)


def _fallback(spec: dict, *, tid: str, terminal: bool) -> tuple[str, float]:
    """Keep registry-only and non-story contexts useful and testable."""
    texts = [
        str(value).strip()
        for key in ("caption", "copy", "vehicle", "note", "reference_note")
        if (value := spec.get(key)) and str(value).strip()
    ]
    body = psr("HB Body", "\n".join(texts) or "Editable reference figure")
    table = component_table(
        tid,
        [100.0],
        [cell(f"{tid}c", "0:0", body, stroke=False)],
        outer_stroke=False,
    )
    return wrap_table_paragraph(table, terminal), 16.0


def _figure_group(
    content: str,
    *,
    tid: str,
    terminal: bool,
    height: float,
    x_offset: float = 0.0,
    space_after: float = 0.0,
) -> tuple[str, float]:
    group = (
        f'<Group Self="grp_referencefigure_{tid}" '
        'AppliedObjectStyle="ObjectStyle/$ID/[None]" '
        f'ItemTransform="1 0 0 1 {x_offset:g} 0">'
        + content
        + "</Group>"
    )
    tail = "<Content></Content>" + ("" if terminal else "<Br/>")
    xml = figure_paragraph(group, tail=tail)
    if space_after:
        xml = xml.replace(
            "<ParagraphStyleRange ",
            f'<ParagraphStyleRange SpaceAfter="{space_after:g}" ',
            1,
        )
    return xml, height + space_after


def _resolved_image(spec: dict, ctx: RenderContext) -> Path | None:
    ref = str(spec.get("image") or "").strip()
    return ctx.resolve_bundle_image(ref) if ref else None


def _derived_crop(
    ctx: RenderContext,
    asset: Path,
    *,
    name: str,
    box: tuple[int, int, int, int],
) -> Path:
    """Create a deterministic build-only crop beside the prepared bundle."""
    from PIL import Image

    requested_target = (
        ctx.bundle_root
        / "_generated"
        / "idml_reference_assets"
        / f"{asset.stem}_{name}.png"
    )
    target = prepare_file_destination_no_symlinks(
        requested_target,
        destination_root=ctx.bundle_root,
        label="derived IDML crop",
    )
    temp_path: Path | None = None
    try:
        with Image.open(asset) as source, tempfile.NamedTemporaryFile(
            mode="w+b",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            cropped = source.convert("RGBA").crop(box)
            cropped.save(
                handle,
                format="PNG",
                optimize=False,
                compress_level=9,
            )
            handle.flush()
            os.fsync(handle.fileno())

        # Re-check immediately before the atomic replacement.  ``os.replace``
        # replaces a target symlink itself rather than following it, while the
        # repeated parent check rejects a swapped symlinked directory.
        target = prepare_file_destination_no_symlinks(
            target,
            destination_root=ctx.bundle_root,
            label="derived IDML crop",
        )
        os.replace(temp_path, target)
        temp_path = None
        target = prepare_file_destination_no_symlinks(
            target,
            destination_root=ctx.bundle_root,
            label="derived IDML crop",
        )
        if not target.is_file():
            raise RuntimeError(f"derived IDML crop is not a regular file: {target}")
        return target
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _inline_path(
    path_id: str,
    points: tuple[tuple[float, float], ...],
    *,
    color: str = "Color/HB Brand Dark",
    weight: float = 0.3,
) -> str:
    anchors = "".join(
        f'<PathPointType Anchor="{x:g} {y:g}" '
        f'LeftDirection="{x:g} {y:g}" RightDirection="{x:g} {y:g}"/>'
        for x, y in points
    )
    return (
        f'<GraphicLine Self="{path_id}" ContentType="Unassigned" '
        'AppliedObjectStyle="ObjectStyle/$ID/[None]" FillColor="Swatch/None" '
        f'StrokeColor="{color}" StrokeWeight="{weight:g}" '
        'ItemTransform="1 0 0 1 0 0">'
        '<Properties><PathGeometry><GeometryPathType PathOpen="true">'
        f'<PathPointArray>{anchors}</PathPointArray>'
        '</GeometryPathType></PathGeometry></Properties>'
        + _inline_anchor()
        + '</GraphicLine>'
    )


def _charging_ac(
    spec: dict,
    ctx: RenderContext,
    *,
    tid: str,
    terminal: bool,
    measure_w: float | None,
) -> tuple[str, float]:
    asset = _resolved_image(spec, ctx)
    if asset is None or not asset.exists():
        return _fallback(spec, tid=tid, terminal=terminal)
    width = measure_w or ctx.text_measure
    image_w, image_h = ctx.art_frame_size(asset, max_w=width)
    caption = str(spec.get("caption") or "").strip()
    image = _positioned_image(
        f"{tid}img", asset, image_w, image_h, left=0.0, bottom=0.0,
    )
    text = _editable_text_frame(
        ctx,
        story_id=f"st_anchor_referencefigure_ac_caption_{tid}",
        frame_id=f"tf_referencefigure_ac_caption_{tid}",
        title=f"{tid} AC caption",
        parts=[_sized_psr(
            "HB Body", caption, size=6.2, leading=7.2,
            terminal=True, justification="CenterAlign",
        )],
        left=14.0,
        top=-image_h * 0.17,
        right=image_w - 14.0,
        bottom=-image_h * 0.045,
        valign="CenterAlign",
    )
    return _figure_group(
        image + text,
        tid=tid,
        terminal=terminal,
        height=image_h,
        space_after=3.0,
    )


def _charging_car(
    spec: dict,
    ctx: RenderContext,
    *,
    tid: str,
    terminal: bool,
    measure_w: float | None,
) -> tuple[str, float]:
    asset = _resolved_image(spec, ctx)
    if asset is None or not asset.exists():
        return _fallback(spec, tid=tid, terminal=terminal)
    width = measure_w or ctx.text_measure
    image_w, image_h = ctx.art_frame_size(asset, max_w=width)
    vehicle = str(spec.get("vehicle") or "").strip()
    note = str(spec.get("note") or "").strip()
    note_left = image_w * 0.55
    note_top = -image_h + 5.0
    image = _positioned_image(
        f"{tid}img", asset, image_w, image_h, left=0.0, bottom=0.0,
    )
    note_bg = _shape(
        shape_id=f"referencefigure_car_note_bg_{tid}",
        left=note_left,
        top=note_top,
        right=image_w - 9.0,
        bottom=note_top + 13.0,
        radius=6.5,
        fill="Color/Paper",
    )
    # Text frames are deliberately appended after every graphic/shape.
    note_frame = _editable_text_frame(
        ctx,
        story_id=f"st_anchor_referencefigure_car_note_{tid}",
        frame_id=f"tf_referencefigure_car_note_{tid}",
        title=f"{tid} car charging note",
        parts=[_sized_psr(
            "HB Body", note, size=6.2, leading=7.2, terminal=True,
            justification="CenterAlign",
        )],
        left=note_left + 3.0,
        top=note_top,
        right=image_w - 12.0,
        bottom=note_top + 13.0,
        valign="CenterAlign",
    )
    vehicle_frame = _editable_text_frame(
        ctx,
        story_id=f"st_anchor_referencefigure_car_vehicle_{tid}",
        frame_id=f"tf_referencefigure_car_vehicle_{tid}",
        title=f"{tid} car vehicle label",
        parts=[_sized_psr(
            "HB Body", vehicle, size=6.2, leading=7.2, terminal=True,
        )],
        left=image_w * 0.64,
        top=-image_h + 41.0,
        right=image_w * 0.82,
        bottom=-image_h + 53.0,
        valign="CenterAlign",
    )
    return _figure_group(
        image + note_bg + note_frame + vehicle_frame,
        tid=tid,
        terminal=terminal,
        height=image_h,
        space_after=2.0,
    )


def _download_copy(text: str) -> tuple[str, str]:
    """Split a localized download paragraph into left/right sentence groups."""
    import re

    sentences = [part.strip() for part in re.split(r"(?<=[.!?。！？])\s+", text) if part.strip()]
    if len(sentences) >= 2:
        return " ".join(sentences[:-1]), sentences[-1]
    words = text.split()
    split_at = max(1, len(words) // 2)
    return " ".join(words[:split_at]), " ".join(words[split_at:])


def _app_download(
    spec: dict,
    ctx: RenderContext,
    *,
    tid: str,
    terminal: bool,
    measure_w: float | None,
) -> tuple[str, float]:
    asset = _resolved_image(spec, ctx)
    if asset is None or not asset.exists():
        return _fallback(spec, tid=tid, terminal=terminal)
    width = measure_w or ctx.text_measure
    copy_left, copy_right = _download_copy(str(spec.get("copy") or "").strip())
    stores = _derived_crop(
        ctx, asset, name="stores", box=(23, 14, 180, 116),
    )
    qr = _derived_crop(
        ctx, asset, name="qr", box=(524, 11, 649, 138),
    )
    # The QR is 1.353 pt higher than the marketplace stack in the reference.
    # Keep the earliest visible edge as the group's measured top so the two
    # independent links retain their exact page geometry.
    total_h = 82.153
    stores_top = -80.8
    qr_top = -82.153
    stores_image = _positioned_image(
        f"{tid}stores",
        stores,
        71.966,
        46.632,
        left=19.80,
        bottom=stores_top + 46.632,
    )
    qr_image = _positioned_image(
        f"{tid}qr",
        qr,
        48.977,
        49.414,
        left=172.232,
        bottom=qr_top + 49.414,
    )
    bounds = _shape(
        shape_id=f"referencefigure_download_bounds_{tid}",
        left=0.0,
        top=-total_h,
        right=width,
        bottom=0.0,
    )
    left_frame = _editable_text_frame(
        ctx,
        story_id=f"st_anchor_referencefigure_download_left_{tid}",
        frame_id=f"tf_referencefigure_download_left_{tid}",
        title=f"{tid} download copy left",
        parts=[_sized_psr(
            "HB Body", copy_left, size=7.0, leading=8.4, terminal=True,
        )],
        left=20.109,
        top=-26.75,
        right=141.587,
        bottom=0.0,
        auto_height=True,
    )
    right_frame = _editable_text_frame(
        ctx,
        story_id=f"st_anchor_referencefigure_download_right_{tid}",
        frame_id=f"tf_referencefigure_download_right_{tid}",
        title=f"{tid} download copy right",
        parts=[_sized_psr(
            "HB Body", copy_right, size=7.0, leading=8.4, terminal=True,
        )],
        left=171.932,
        top=-26.16,
        right=min(width, 268.693),
        bottom=0.0,
        auto_height=True,
    )
    return _figure_group(
        bounds + stores_image + qr_image + left_frame + right_frame,
        tid=tid,
        terminal=terminal,
        height=total_h,
        space_after=2.0,
    )


def _app_add_device(
    spec: dict,
    ctx: RenderContext,
    *,
    tid: str,
    terminal: bool,
    measure_w: float | None,
) -> tuple[str, float]:
    asset = _resolved_image(spec, ctx)
    if asset is None or not asset.exists():
        return _fallback(spec, tid=tid, terminal=terminal)
    del measure_w
    # Absolute geometry measured from physical page 20 of the approved
    # reference.  The host story begins at x=28.347 pt.
    phone_w, phone_h = 170.974, 150.925
    panel_w, panel_h = 300.368, 66.017
    panel_gap = 17.1
    phone_bottom = -(panel_h + panel_gap)
    total_h = phone_h + panel_h + panel_gap
    phone_left = 66.974
    phone = _positioned_image(
        f"{tid}img", asset, phone_w, phone_h,
        left=phone_left, bottom=phone_bottom,
    )

    step_labels = [str(value).strip() for value in spec.get("step_labels", [])]
    step_labels.extend(["", ""])
    caption_y = phone_bottom + 4.9
    caption_centers = (104.621, 203.793)
    step_frames = [
        _editable_text_frame(
            ctx,
            story_id=f"st_anchor_referencefigure_app_step_{index}_{tid}",
            frame_id=f"tf_referencefigure_app_step_{index}_{tid}",
            title=f"{tid} App step {index + 1}",
            parts=[_sized_psr(
                "HB Body", step_labels[index], size=5.5, leading=6.2,
                terminal=True, justification="CenterAlign",
            )],
            left=caption_centers[index] - 35.0,
            top=caption_y,
            right=caption_centers[index] + 35.0,
            bottom=caption_y + 10.0,
            valign="CenterAlign",
        )
        for index in range(2)
    ]

    panel_left = 12.858
    panel_top = -panel_h
    graphics = [_shape(
        shape_id=f"referencefigure_app_panel_bg_{tid}",
        left=panel_left,
        top=panel_top,
        right=panel_left + panel_w,
        bottom=0.0,
        radius=7.0,
        fill="Color/HB Bg K05",
    )]
    control_ref = str(spec.get("control_image") or "").strip()
    control_asset = (
        ctx.resolve_bundle_image(
            control_ref,
            format_name="pdf",
            consumer="idml-renderer",
            reference_kind="idml-component-contract",
        )
        if control_ref
        else None
    )
    if control_asset is not None and control_asset.exists():
        graphics.append(_positioned_image(
            f"{tid}controls", control_asset, panel_w, panel_h,
            left=panel_left,
            bottom=0.0,
        ))

    # The source panel retains its original short leader stubs.  These native
    # paths extend them to the exact reference endpoints and stay underneath
    # all editable label frames.
    graphics.extend([
        _inline_path(
            f"referencefigure_app_rule_power_extension_{tid}",
            ((77.905, -40.118), (108.25, -40.118)),
        ),
        _inline_path(
            f"referencefigure_app_rule_dc_extension_{tid}",
            ((87.983, -22.786), (108.0, -22.786)),
        ),
        _inline_path(
            f"referencefigure_app_rule_ac_extension_{tid}",
            ((230.0, -22.686), (248.268, -22.686)),
        ),
    ])

    labels = [str(value).strip() for value in spec.get("labels", [])]
    labels.extend(["", "", ""])
    # Source order is Power, AC, DC/USB; visual order is Power, DC/USB, AC.
    label_specs = (
        (labels[0], 23.161, -47.5, 75.097, -40.3, "LeftAlign"),
        (labels[2], 22.681, -30.099, 84.523, -22.899, "LeftAlign"),
        (labels[1], 251.395, -29.001, 298.381, -21.801, "RightAlign"),
    )
    label_frames = [
        _editable_text_frame(
            ctx,
            story_id=f"st_anchor_referencefigure_app_label_{index}_{tid}",
            frame_id=f"tf_referencefigure_app_label_{index}_{tid}",
            title=f"{tid} App control label {index + 1}",
            parts=[_sized_psr(
                "HB Body", text, size=6.0, leading=6.8, terminal=True,
                justification=align,
            )],
            left=left,
            top=top,
            right=right,
            bottom=bottom,
            valign="CenterAlign",
        )
        for index, (text, left, top, right, bottom, align) in enumerate(label_specs)
        if text
    ]
    return _figure_group(
        phone + "".join(graphics) + "".join(step_frames) + "".join(label_frames),
        tid=tid,
        terminal=terminal,
        height=total_h,
        space_after=2.0,
    )


def _app_connect_result(
    spec: dict,
    ctx: RenderContext,
    *,
    tid: str,
    terminal: bool,
    measure_w: float | None,
) -> tuple[str, float]:
    asset = _resolved_image(spec, ctx)
    if asset is None or not asset.exists():
        return _fallback(spec, tid=tid, terminal=terminal)
    del measure_w
    cropped = _derived_crop(
        ctx, asset, name="screens", box=(0, 0, 1046, 587),
    )
    image_left = 25.935
    image_w, image_h = 262.624, 147.301
    caption_tail = 18.699
    total_h = image_h + caption_tail
    image = _positioned_image(
        f"{tid}img",
        cropped,
        image_w,
        image_h,
        left=image_left,
        bottom=-caption_tail,
    )

    step_labels = [str(value).strip() for value in spec.get("step_labels", [])]
    step_labels.extend(["", "", ""])
    caption_centers = (58.0165, 156.5305, 253.841)
    step_frames = [
        _editable_text_frame(
            ctx,
            story_id=f"st_anchor_referencefigure_connect_step_{index}_{tid}",
            frame_id=f"tf_referencefigure_connect_step_{index}_{tid}",
            title=f"{tid} App result step {index + 1}",
            parts=[_sized_psr(
                "HB Body",
                step_labels[index],
                size=5.5,
                leading=6.2,
                terminal=True,
                justification="CenterAlign",
            )],
            left=caption_centers[index] - 23.0,
            top=-16.85,
            right=caption_centers[index] + 23.0,
            bottom=-9.2,
            valign="CenterAlign",
        )
        for index in range(3)
        if step_labels[index]
    ]
    reference_note = str(spec.get("reference_note") or "").strip()
    note_frame = _editable_text_frame(
        ctx,
        story_id=f"st_anchor_referencefigure_connect_note_{tid}",
        frame_id=f"tf_referencefigure_connect_note_{tid}",
        title=f"{tid} App result reference note",
        parts=[_sized_psr(
            "HB Body", reference_note, size=5.8, leading=6.5, terminal=True,
        )],
        left=25.934,
        top=-8.6,
        right=180.0,
        bottom=0.0,
        valign="CenterAlign",
    )
    return _figure_group(
        image + "".join(step_frames) + note_frame,
        tid=tid,
        terminal=terminal,
        height=total_h,
    )


def render_referencefigure(
    spec: dict,
    ctx: RenderContext,
    *,
    tid: str,
    terminal: bool,
    span_columns: bool = True,
    measure_w: float | None = None,
) -> tuple[str, float]:
    """Render one approved editable reference figure."""
    del span_columns
    if ctx.add_story is None:
        return _fallback(spec, tid=tid, terminal=terminal)
    layout = str(spec.get("layout") or "").strip().casefold()
    renderers = {
        "charging_ac": _charging_ac,
        "charging_car": _charging_car,
        "app_download": _app_download,
        "app_add_device": _app_add_device,
        "app_connect_result": _app_connect_result,
    }
    renderer = renderers.get(layout)
    if renderer is None:
        return _fallback(spec, tid=tid, terminal=terminal)
    return renderer(
        spec, ctx, tid=tid, terminal=terminal, measure_w=measure_w,
    )


__all__ = ["render_referencefigure"]
