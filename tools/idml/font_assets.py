"""Verified, redistributable fonts carried beside designer-facing IDML."""
from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

try:
    from tools.utils.path_utils import (
        PathSegments,
        idml_portable_fonts_of,
        repo_root,
    )
except ModuleNotFoundError:  # direct tools/export_idml.py execution
    from utils.path_utils import (  # type: ignore
        PathSegments,
        idml_portable_fonts_of,
        repo_root,
    )


@dataclass(frozen=True)
class PortableFontAsset:
    family: str
    postscript_name: str
    path: Path
    sha256: str
    license_path: Path
    languages: tuple[str, ...]


def portable_font_root() -> Path:
    return idml_portable_fonts_of(repo_root() / PathSegments.DOCS)


def _assets() -> tuple[PortableFontAsset, ...]:
    root = portable_font_root()
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "idml-portable-font-assets/v1":
        raise RuntimeError("unsupported IDML portable-font manifest schema")
    assets = []
    for row in manifest.get("fonts", []):
        assets.append(PortableFontAsset(
            family=str(row["family"]),
            postscript_name=str(row["postscript_name"]),
            path=root / str(row["filename"]),
            sha256=str(row["sha256"]),
            license_path=root / str(row["license_file"]),
            languages=tuple(str(value) for value in row.get("languages", ("*",))),
        ))
    return tuple(assets)


def _validate_asset(asset: PortableFontAsset) -> None:
    if not asset.path.is_file():
        raise RuntimeError(f"portable IDML font is missing: {asset.path}")
    digest = hashlib.sha256(asset.path.read_bytes()).hexdigest()
    if digest != asset.sha256:
        raise RuntimeError(
            f"portable IDML font hash mismatch: {asset.path} "
            f"(expected {asset.sha256}, got {digest})"
        )
    if not asset.license_path.is_file():
        raise RuntimeError(
            f"portable IDML font license is missing: {asset.license_path}"
        )


def _declared_families(idml_path: Path) -> set[str]:
    with zipfile.ZipFile(idml_path) as package:
        try:
            payload = package.read("Resources/Fonts.xml")
        except KeyError:
            # Compatibility for legacy/minimal handoff fixtures that are ZIP
            # packages but do not carry a font resource. They declare no
            # portable families; a real exported IDML always has this part and
            # remains governed by the hash-verified selection below.
            return set()
        root = ET.fromstring(payload)
    return {
        str(family.get("Name"))
        for family in root.iter("FontFamily")
        if family.get("Name")
    }


def portable_font_assets_for_idml(
    idml_path: Path,
) -> tuple[PortableFontAsset, ...]:
    declared = _declared_families(idml_path)
    selected = tuple(asset for asset in _assets() if asset.family in declared)
    for asset in selected:
        _validate_asset(asset)
    return selected


def provision_document_fonts(idml_path: Path) -> tuple[Path, ...]:
    """Copy every declared open font beside one built IDML package."""
    assets = portable_font_assets_for_idml(idml_path)
    destination = idml_path.parent / PathSegments.DOCUMENT_FONTS
    destination.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for asset in assets:
        target = destination / asset.path.name
        shutil.copy2(asset.path, target)
        copied.append(target)
    license_dir = destination / "LICENSES"
    for license_path in sorted({asset.license_path for asset in assets}):
        license_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(license_path, license_dir / license_path.name)
    return tuple(copied)


__all__ = (
    "PortableFontAsset",
    "portable_font_assets_for_idml",
    "portable_font_root",
    "provision_document_fonts",
)
