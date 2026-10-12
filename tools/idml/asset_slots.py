"""Recognise governed bundle art by the asset slot its source named.

A target override resolves ``asset:operation/led_light`` to a file of its own
(for example a model-suffixed basename, because LaTeX flattens its asset
directory). Matching that file by name would put a model into renderer code;
the bundle's usage manifest records the slot instead, so renderers ask for it.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

try:
    from tools.bundle_asset_manifest import AssetSlot, manifest_asset_slot
except ModuleNotFoundError:  # direct tools/export_idml.py execution
    from bundle_asset_manifest import AssetSlot, manifest_asset_slot  # type: ignore

from .primitives import resolve_bundle_image

AssetSlotLookup = Callable[[str], "AssetSlot | None"]


def bundle_asset_slots(bundle_root: Path) -> AssetSlotLookup:
    """Return a lookup from a bundle image reference to its governed slot."""

    def lookup(ref: str) -> AssetSlot | None:
        image = resolve_bundle_image(bundle_root, ref) if ref else None
        return manifest_asset_slot(bundle_root, image) if image is not None else None

    return lookup


__all__ = ["AssetSlot", "AssetSlotLookup", "bundle_asset_slots"]
