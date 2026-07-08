"""Prepared-bundle and IDML output path resolution for the exporter.

Split out of export_idml.py so the main module stays under its
maintainability line cap; the layout rules (region- vs lang-level bundle)
are load-bearing and shared by every export path.
"""
from __future__ import annotations

from pathlib import Path


def default_bundle_root(root: Path, model: str, region: str, lang: str) -> Path:
    """Pick the prepared RST bundle path used by the current target layout."""
    lang_bundle = root / "docs" / "_build" / model / region / lang / "rst"
    region_bundle = root / "docs" / "_build" / model / region / "rst"
    return lang_bundle if lang_bundle.is_dir() else region_bundle


def default_output_path(root: Path, model: str, region: str, lang: str,
                        bundle_root: Path) -> Path:
    """Match the IDML output location to the prepared bundle layout."""
    region_bundle = root / "docs" / "_build" / model / region / "rst"
    model_slug = model.replace("-", "").lower()
    region_slug = region.lower()
    try:
        is_region_bundle = bundle_root.resolve() == region_bundle.resolve()
    except FileNotFoundError:
        is_region_bundle = bundle_root == region_bundle
    if is_region_bundle:
        return (root / "docs" / "_build" / model / region / "idml"
                / f"manual_{model_slug}_{region_slug}.idml")
    return (root / "docs" / "_build" / model / region / lang / "idml"
            / f"manual_{model_slug}_{region_slug}_{lang}.idml")
