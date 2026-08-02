"""Assemble responsive web-manual stylesheets into one Sphinx asset."""

from __future__ import annotations

from pathlib import Path

from tools.utils.path_utils import PathSegments, get_paths


WEB_STYLESHEET_NAME = "web_manual.css"
WEB_STYLESHEET_PARTS = (WEB_STYLESHEET_NAME, "web_symbols_fcc_components.css", "web_app_components.css")


def copy_web_stylesheet(destination_dir: Path) -> Path:
    """Copy the ordered web style modules as one stable public stylesheet."""
    contracts_dir = get_paths().renderer_contracts_dir
    sources = [contracts_dir / name for name in WEB_STYLESHEET_PARTS]
    missing = [source for source in sources if not source.is_file()]
    if missing:
        raise RuntimeError(
            "web manual stylesheet is missing: "
            + ", ".join(str(source) for source in missing)
        )
    static_dir = destination_dir / PathSegments.STATIC
    static_dir.mkdir(parents=True, exist_ok=True)
    destination = static_dir / WEB_STYLESHEET_NAME
    destination.write_text(
        "\n\n".join(source.read_text(encoding="utf-8").rstrip() for source in sources)
        + "\n",
        encoding="utf-8",
    )
    return destination


__all__ = ["WEB_STYLESHEET_NAME", "WEB_STYLESHEET_PARTS", "copy_web_stylesheet"]
