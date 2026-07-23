"""Editable figure composites used by approved reference-page replicas.

The linked artwork remains the immutable bottom layer.  Every localized label
is emitted as its own unlocked text frame at the end of the group, so an
InDesign operator can move or edit copy without repainting the illustration.
"""
from __future__ import annotations

import math
import os
import tempfile
import unicodedata
from dataclasses import dataclass
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
from ..params import component_param_pt
from .base import RenderContext, figure_paragraph
from .oppanel import (
    _editable_text_frame,
    _inline_anchor,
    _positioned_image,
    _shape,
    _sized_psr,
)


_APP_CONTROL_ROLES = ("main_power", "dc_usb", "ac")


@dataclass(frozen=True)
class AppFigureStyle:
    """Shared editable type/fit contract for every App reference composite."""

    control_label_size: float
    control_label_leading: float
    control_label_min_height: float
    connect_step_size: float
    connect_step_leading: float
    connect_note_size: float
    connect_note_leading: float
    connect_note_width: float
    text_frame_safety: float

    def __post_init__(self) -> None:
        for name, value in vars(self).items():
            if not math.isfinite(value) or value <= 0:
                raise ValueError(
                    f"AppFigureStyle {name} must be finite and greater than zero"
                )

    @classmethod
    def from_context(cls, ctx: RenderContext) -> AppFigureStyle:
        def token(key: str, default: float) -> float:
            return component_param_pt(
                ctx.params, key, default,
                strict=ctx.strict_component_assets,
                owner="AppFigureStyle",
            )

        return cls(
            control_label_size=token(
                "idml_app_control_label_font_size", 5.0,
            ),
            control_label_leading=token(
                "idml_app_control_label_font_leading", 5.8,
            ),
            control_label_min_height=token(
                "idml_app_control_label_min_height", 7.2,
            ),
            connect_step_size=token(
                "idml_app_connect_step_font_size", 5.5,
            ),
            connect_step_leading=token(
                "idml_app_connect_step_font_leading", 6.2,
            ),
            connect_note_size=token(
                "idml_app_connect_note_font_size", 5.8,
            ),
            connect_note_leading=token(
                "idml_app_connect_note_font_leading", 6.5,
            ),
            connect_note_width=token(
                "idml_app_connect_note_width", 174.0,
            ),
            text_frame_safety=token("idml_app_text_frame_safety", 0.8),
        )


def _estimated_text_width(text: str, size: float) -> float:
    """Conservative portable width estimate for compact App overlay copy."""
    width = 0.0
    for char in text:
        if char.isspace():
            ratio = 0.26
        elif unicodedata.combining(char):
            ratio = 0.0
        elif unicodedata.east_asian_width(char) in {"W", "F"}:
            ratio = 1.0
        elif char.isupper():
            ratio = 0.62
        elif char.islower() or char.isdigit():
            ratio = 0.50
        else:
            ratio = 0.34
        width += ratio * size
    return width


def _wrapped_line_count(text: str, width: float, size: float) -> int:
    words = text.split()
    if not words:
        return 1
    lines = 1
    used = 0.0
    space = _estimated_text_width(" ", size)
    for word in words:
        word_width = _estimated_text_width(word, size)
        if used and used + space + word_width <= width:
            used += space + word_width
        elif used:
            lines += max(1, math.ceil(word_width / width))
            used = word_width % width
        else:
            extra = max(1, math.ceil(word_width / width))
            lines += extra - 1
            used = word_width % width
    return lines


def _frame_height(
    text: str,
    width: float,
    *,
    size: float,
    leading: float,
    minimum: float,
    safety: float,
) -> float:
    return max(
        minimum,
        _wrapped_line_count(text, width, size) * leading + safety,
    )


def _legacy_control_role(label: str) -> str:
    """Classify legacy array labels only for ungoverned compatibility calls."""
    import re

    folded = unicodedata.normalize("NFKD", label.casefold())
    tokens = set(re.findall(
        r"[a-z0-9]+",
        "".join(char for char in folded if not unicodedata.combining(char)),
    ))
    if "usb" in tokens and tokens & {"dc", "cc"}:
        return "dc_usb"
    if tokens & {"ac", "ca"}:
        return "ac"
    return "main_power"


def _control_labels_by_role(spec: dict, ctx: RenderContext) -> dict[str, str]:
    explicit = spec.get("labels_by_role")
    if explicit is not None:
        if not isinstance(explicit, dict):
            raise ValueError("app_add_device labels_by_role must be a mapping")
        labels = {
            role: str(explicit.get(role) or "").strip()
            for role in _APP_CONTROL_ROLES
        }
        missing = [role for role, value in labels.items() if not value]
        if missing:
            raise ValueError(
                "app_add_device labels_by_role missing required roles: "
                + ", ".join(missing)
            )
        return labels

    if ctx.strict_component_assets:
        raise ValueError(
            "approved app_add_device requires labels_by_role with "
            "main_power, dc_usb, and ac"
        )

    labels: dict[str, str] = {}
    for value in spec.get("labels", []):
        text = str(value).strip()
        if not text:
            continue
        role = _legacy_control_role(text)
        if role in labels:
            return {}
        labels[role] = text
    return labels


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
    space_before: float = 0.0,
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
    if space_before or space_after:
        xml = xml.replace(
            "<ParagraphStyleRange ",
            f'<ParagraphStyleRange SpaceBefore="{space_before:g}" '
            f'SpaceAfter="{space_after:g}" ',
            1,
        )
    return xml, space_before + height + space_after


def _resolved_image(spec: dict, ctx: RenderContext) -> Path | None:
    ref = str(spec.get("image") or "").strip()
    if not ref:
        if ctx.strict_component_assets:
            raise ValueError("approved referencefigure requires an image reference")
        return None
    asset = ctx.resolve_bundle_image(ref)
    if ctx.strict_component_assets and (asset is None or not asset.exists()):
        raise FileNotFoundError(
            f"approved referencefigure image is unavailable: {ref}"
        )
    return asset


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
    style = AppFigureStyle.from_context(ctx)
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
                "HB Body", step_labels[index],
                size=style.connect_step_size,
                leading=style.connect_step_leading,
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
    if ctx.strict_component_assets and not control_ref:
        raise ValueError(
            "approved app_add_device requires a control_image reference"
        )
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
    if (
        ctx.strict_component_assets
        and (control_asset is None or not control_asset.exists())
    ):
        raise FileNotFoundError(
            f"approved app_add_device control_image is unavailable: {control_ref}"
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
            ((102.5, -22.786), (108.0, -22.786)),
        ),
        _inline_path(
            f"referencefigure_app_rule_ac_extension_{tid}",
            ((230.0, -22.686), (248.268, -22.686)),
        ),
    ])

    labels = _control_labels_by_role(spec, ctx)
    # Roles are explicit in source/IR. Localized array order never controls
    # placement: the fixed visual slots are main power, DC/USB, then AC.
    label_specs = (
        ("main_power", 23.161, 75.097, -40.3, "LeftAlign"),
        ("dc_usb", 22.681, 100.5, -22.899, "LeftAlign"),
        ("ac", 248.268, 310.0, -21.801, "RightAlign"),
    )
    label_frames = []
    for index, (role, left, right, bottom, align) in enumerate(label_specs):
        text = labels.get(role, "")
        if not text:
            continue
        height = _frame_height(
            text,
            right - left,
            size=style.control_label_size,
            leading=style.control_label_leading,
            minimum=style.control_label_min_height,
            safety=style.text_frame_safety,
        )
        label_frames.append(_editable_text_frame(
            ctx,
            story_id=f"st_anchor_referencefigure_app_label_{index}_{tid}",
            frame_id=f"tf_referencefigure_app_label_{index}_{tid}",
            title=f"{tid} App control label {index + 1}",
            parts=[_sized_psr(
                "HB Body", text,
                size=style.control_label_size,
                leading=style.control_label_leading,
                terminal=True,
                justification=align,
            )],
            left=left,
            top=bottom - height,
            right=right,
            bottom=bottom,
            valign="CenterAlign",
            auto_height=True,
        ))
    return _figure_group(
        phone + "".join(graphics) + "".join(step_frames) + "".join(label_frames),
        tid=tid,
        terminal=terminal,
        height=total_h,
        space_before=component_param_pt(
            ctx.params,
            "idml_app_add_device_space_before",
            8.0,
            strict=ctx.strict_component_assets,
            owner="app_add_device",
        ),
        space_after=component_param_pt(
            ctx.params,
            "idml_app_add_device_space_after",
            3.5,
            strict=ctx.strict_component_assets,
            owner="app_add_device",
        ),
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
    style = AppFigureStyle.from_context(ctx)
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
                size=style.connect_step_size,
                leading=style.connect_step_leading,
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
    note_left = 25.934
    note_height = _frame_height(
        reference_note,
        style.connect_note_width,
        size=style.connect_note_size,
        leading=style.connect_note_leading,
        minimum=style.connect_note_leading + style.text_frame_safety,
        safety=style.text_frame_safety,
    )
    note_frame = _editable_text_frame(
        ctx,
        story_id=f"st_anchor_referencefigure_connect_note_{tid}",
        frame_id=f"tf_referencefigure_connect_note_{tid}",
        title=f"{tid} App result reference note",
        parts=[_sized_psr(
            "HB Body", reference_note,
            size=style.connect_note_size,
            leading=style.connect_note_leading,
            terminal=True,
        )],
        left=note_left,
        top=-note_height,
        right=note_left + style.connect_note_width,
        bottom=0.0,
        valign="CenterAlign",
        auto_height=True,
    )
    return _figure_group(
        image + "".join(step_frames) + note_frame,
        tid=tid,
        terminal=terminal,
        height=total_h,
        space_before=component_param_pt(
            ctx.params,
            "idml_app_connect_result_space_before",
            12.0,
            strict=ctx.strict_component_assets,
            owner="app_connect_result",
        ),
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


__all__ = ["AppFigureStyle", "render_referencefigure"]
