"""Restore semantic asset URIs from a finalized bundle's rewrite provenance."""

from __future__ import annotations

import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from tools.asset_registry import AssetRegistryError
from tools.asset_usage import ASSET_USAGE_MANIFEST_FILENAME, parse_asset_uri
from tools.gen_index_bundle_assets import map_rst_asset_paths

_SEMANTIC_REFERENCE_KINDS = frozenset({"registry-uri", "review-override"})


def _safe_relative_path(raw_value: object, *, label: str) -> Path:
    value = str(raw_value or "").strip()
    path = Path(value)
    if not value or path.is_absolute() or ".." in path.parts:
        raise AssetRegistryError(f"asset rewrite has unsafe {label}: {value!r}")
    return path


def _load_rewrites(manifest_path: Path) -> tuple[dict[str, Any], ...]:
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssetRegistryError(f"asset usage manifest is invalid: {manifest_path}") from exc
    raw_rewrites = payload.get("rewrites", ()) if isinstance(payload, dict) else ()
    if not isinstance(raw_rewrites, list):
        raise AssetRegistryError(f"asset usage manifest has invalid rewrites: {manifest_path}")
    return tuple(row for row in raw_rewrites if isinstance(row, dict))


def _safe_bundle_file(root: Path, relative: Path, *, label: str) -> Path | None:
    bundle_root = root.resolve(strict=True)
    candidate = bundle_root
    for part in relative.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise AssetRegistryError(f"{label} must not be a symbolic link: {relative.as_posix()}")
    if not candidate.exists():
        return None
    canonical = candidate.resolve(strict=True)
    try:
        canonical.relative_to(bundle_root)
    except ValueError as exc:
        raise AssetRegistryError(f"{label} escapes its bundle: {relative.as_posix()}") from exc
    if not canonical.is_file():
        raise AssetRegistryError(f"{label} is not a file: {relative.as_posix()}")
    return canonical


def restore_registry_asset_uris(
    *,
    source_bundle_dir: Path,
    target_bundle_dir: Path,
    strict: bool,
) -> int:
    """Restore registry URIs in copied or already-finalized RST files.

    ``source_bundle_dir`` owns the usage manifest.  ``target_bundle_dir`` owns
    the RST tree to mutate; this differs when a runtime bundle is seeded into
    ``docs/_review``.
    """

    manifest_relative = Path(ASSET_USAGE_MANIFEST_FILENAME)
    manifest_path = _safe_bundle_file(
        source_bundle_dir,
        manifest_relative,
        label="asset usage manifest",
    )
    if manifest_path is None:
        return 0
    rewrites = _load_rewrites(manifest_path)
    by_reference: dict[Path, list[dict[str, Any]]] = defaultdict(list)
    for row in rewrites:
        reference_path = _safe_relative_path(row.get("reference_path"), label="reference path")
        if row.get("reference_kind") in _SEMANTIC_REFERENCE_KINDS:
            original_value = str(row.get("original_value") or "").strip()
            if parse_asset_uri(original_value) is None:
                raise AssetRegistryError(
                    f"semantic asset rewrite has invalid original asset URI: {original_value!r}"
                )
        by_reference[reference_path].append(row)

    restored = 0
    for reference_path, events in sorted(by_reference.items(), key=lambda item: item[0].as_posix()):
        target_path = _safe_bundle_file(
            target_bundle_dir,
            reference_path,
            label="asset rewrite target",
        )
        semantic_events = [
            row for row in events if row.get("reference_kind") in _SEMANTIC_REFERENCE_KINDS
        ]
        if target_path is None:
            if strict and semantic_events:
                raise AssetRegistryError(
                    f"asset rewrite reference was not copied: {reference_path.as_posix()}"
                )
            continue

        queues: dict[str, deque[dict[str, Any]]] = defaultdict(deque)
        for row in events:
            rendered_value = str(row.get("rendered_value") or "").strip()
            if not rendered_value:
                raise AssetRegistryError(
                    f"asset rewrite has no rendered value: {reference_path.as_posix()}"
                )
            queues[rendered_value].append(row)

        def restore(raw_value: str) -> str:
            nonlocal restored
            queue = queues.get(raw_value)
            if not queue:
                return raw_value
            row = queue.popleft()
            if row.get("reference_kind") not in _SEMANTIC_REFERENCE_KINDS:
                return raw_value
            original_value = str(row.get("original_value") or "").strip()
            restored += 1
            return original_value

        text = target_path.read_text(encoding="utf-8")
        rewritten = map_rst_asset_paths(text, transform=restore)
        if strict:
            missing = [
                row
                for queue in queues.values()
                for row in queue
                if row.get("reference_kind") in _SEMANTIC_REFERENCE_KINDS
            ]
            if missing:
                raise AssetRegistryError(
                    f"semantic asset rewrite provenance no longer matches "
                    f"{reference_path.as_posix()}"
                )
        if rewritten != text:
            target_path.write_text(rewritten, encoding="utf-8")
    return restored


__all__ = ("restore_registry_asset_uris",)
