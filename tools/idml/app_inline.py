"""Approved inline controls used by App prose stories."""
from __future__ import annotations

from pathlib import Path

from .asset_contracts import APP_ADD_DEVICE_ICON_ASSET_URI
from .params import param_pt

_ADD_DEVICE_ICON_MARKER = "|ADD_DEVICE_ICON|"


def prepare_app_body_inline(
    writer,
    *,
    semantic_kind: str,
    text: str,
    bundle_root: Path,
    page_language: str,
    story_id: str,
    block_index: int,
) -> tuple[str, dict[str, str] | None]:
    """Replace the reviewed Add-device wording with its governed inline icon."""
    if (
        semantic_kind == "body_app_primary"
        and "Click the **Add device** button" in text
    ):
        text = text.replace(
            "Click the **Add device** button",
            f"Click the button {_ADD_DEVICE_ICON_MARKER}",
            1,
        )
    if _ADD_DEVICE_ICON_MARKER not in text:
        return text, None

    context = writer._render_context(bundle_root, language=page_language)
    icon = context.resolve_bundle_image(
        APP_ADD_DEVICE_ICON_ASSET_URI,
        format_name="png",
        consumer="idml-renderer",
        reference_kind="idml-component-contract",
    )
    if icon is None or not icon.exists():
        if writer.strict_component_assets:
            raise FileNotFoundError(
                "approved App step icon is unavailable: "
                f"{APP_ADD_DEVICE_ICON_ASSET_URI}"
            )
        return text, None

    icon_size = param_pt(writer.params, "idml_app_add_device_icon_size", 8.0)
    return text, {
        _ADD_DEVICE_ICON_MARKER: writer._image_cell_content(
            f"{story_id}_app_add_device_icon_{block_index}",
            icon,
            icon_size,
            icon_size,
        ),
    }
