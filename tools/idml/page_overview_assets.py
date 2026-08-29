"""Target-neutral asset resolution for the shared Overview component."""
from __future__ import annotations

from pathlib import Path
from typing import Mapping


def resolve_overview_assets(
    writer,
    bundle_root: Path,
    source_refs: list[str],
    overrides: Mapping[str, str] | None,
) -> list[Path]:
    """Resolve the two governed view assets, with optional role overrides."""
    refs = source_refs if overrides is None else [
        str(overrides.get("front_art") or ""),
        str(overrides.get("right_art") or ""),
    ]
    assets = [writer._resolve_bundle_image(bundle_root, ref) for ref in refs]
    if any(asset is None for asset in assets):
        raise ValueError("product overview contains an unresolved governed image")
    return assets


__all__ = ["resolve_overview_assets"]
