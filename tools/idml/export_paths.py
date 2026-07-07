"""Default bundle and output paths for the IDML exporter."""
from __future__ import annotations

from pathlib import Path

try:
    from tools.utils.path_utils import Paths
except ImportError:  # pragma: no cover - direct script execution fallback
    from utils.path_utils import Paths  # type: ignore


ROOT = Path(__file__).resolve().parents[2]
DOCS_BUILD = Paths(ROOT).docs_build_dir


def default_bundle_root(model: str, region: str, lang: str) -> Path:
    """Pick the prepared RST bundle path used by the current target layout."""
    lang_bundle = DOCS_BUILD / model / region / lang / "rst"
    region_bundle = DOCS_BUILD / model / region / "rst"
    return lang_bundle if lang_bundle.is_dir() else region_bundle


def default_output_path(model: str, region: str, lang: str, bundle_root: Path) -> Path:
    """Match the IDML output location to the prepared bundle layout."""
    region_bundle = DOCS_BUILD / model / region / "rst"
    model_slug = model.replace("-", "").lower()
    region_slug = region.lower()
    try:
        is_region_bundle = bundle_root.resolve() == region_bundle.resolve()
    except FileNotFoundError:
        is_region_bundle = bundle_root == region_bundle
    if is_region_bundle:
        return (
            DOCS_BUILD / model / region / "idml"
            / f"manual_{model_slug}_{region_slug}.idml"
        )
    return (
        DOCS_BUILD / model / region / lang / "idml"
        / f"manual_{model_slug}_{region_slug}_{lang}.idml"
    )
