"""Resolve shared operation-artwork presentation modes for every renderer."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from tools.utils.path_utils import PathSegments, Paths, repo_root
from tools.web_presentation_contract import load_web_presentation_contract


BASE_ART_LIVE_COPY = "base-art-live-copy"


def operation_id_from_ref(ref: str, *, layout: str = "") -> str:
    """Return a stable operation id without making the asset filename a layout API."""

    normalized_layout = str(layout or "").strip().casefold().replace("_", "-")
    if normalized_layout == "energy-saving":
        return "energy-saving"
    stem = Path(str(ref or "").replace("\\", "/")).stem.casefold()
    normalized = stem.replace("_", "-")
    return normalized.removeprefix("op-")


def operation_artwork_mode_from_contract(
    contract: Mapping[str, Any],
    *,
    operation_id: str,
) -> str | None:
    """Return one operation mode from an already resolved target contract."""

    operations = contract.get("operations")
    figures = operations.get("figures", []) if isinstance(operations, Mapping) else []
    normalized_id = str(operation_id or "").strip().casefold()
    matches = [
        figure
        for figure in figures
        if isinstance(figure, Mapping)
        and str(figure.get("id") or "").strip().casefold() == normalized_id
    ]
    if len(matches) > 1:
        raise ValueError(f"duplicate operation presentation id {operation_id!r}")
    if not matches:
        return None
    mode = str(matches[0].get("presentation_mode") or "").strip()
    return mode or None


def operation_artwork_mode(
    *,
    model: str | None,
    region: str | None,
    operation_id: str,
    root: Path | None = None,
) -> str | None:
    """Resolve one target/component mode from the checked-in layered contract."""

    normalized_model = str(model or "").strip()
    normalized_region = str(region or "").strip()
    if not normalized_model or not normalized_region:
        return None
    contract_root = Path(root) if root is not None else repo_root()
    contract_path = (
        Paths(root=contract_root).renderer_contracts_dir
        / PathSegments.WEB_PRESENTATION_CONTRACT
    )
    contract = load_web_presentation_contract(
        contract_path,
        model=normalized_model,
        region=normalized_region,
    )
    return operation_artwork_mode_from_contract(
        contract,
        operation_id=operation_id,
    )


def apply_web_artwork_mode(
    figure: Any,
    component: Mapping[str, Any],
    error_type: type[Exception],
    source_path: Path,
) -> bool:
    """Apply the bounded Web presentation marker; return whether it handled art."""

    presentation_mode = str(component.get("presentation_mode") or "").strip()
    if not presentation_mode:
        return False
    if presentation_mode != BASE_ART_LIVE_COPY:
        raise error_type(
            f"{source_path}: unsupported Web figure presentation mode "
            f"{presentation_mode!r}"
        )
    figure["class"] = [*figure.get("class", []), "hb-base-art-live-copy"]
    figure["data-web-presentation-mode"] = presentation_mode
    figure["data-web-base-art-ref"] = str(component.get("image_key") or "")
    return True


__all__ = [
    "BASE_ART_LIVE_COPY",
    "apply_web_artwork_mode",
    "operation_artwork_mode",
    "operation_artwork_mode_from_contract",
    "operation_id_from_ref",
]
