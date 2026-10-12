"""Derived snapshot writers orchestrated by the phase2 sync entrypoint."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.sync_asset_registry import sync_asset_registry_mirror
from tools.sync_model_capabilities import sync_capability_mirror
from tools.sync_web_composites import sync_web_composites


def collect_derived_snapshot_writes(
    cfg: dict[str, Any],
    *,
    source: Any,
    repo_root: Path,
    export_root: Path,
    dry_run: bool,
    generated_at: str,
    sha256_text: Any,
    sha256_file: Any,
    result_cls: Any,
) -> tuple[list[Any], list[tuple[Path, str]]]:
    """Collect capability, asset-registry, and Web-composite snapshot writes."""
    results: list[Any] = []
    writes: list[tuple[Path, str]] = []

    capability_result, capability_write = sync_capability_mirror(
        cfg,
        source=source,
        repo_root=repo_root,
        sha256_text=sha256_text,
        sha256_file=sha256_file,
        result_cls=result_cls,
    )
    if capability_result is not None and capability_write is not None:
        results.append(capability_result)
        writes.append(capability_write)

    registry_result, registry_write = sync_asset_registry_mirror(
        cfg,
        source=source,
        repo_root=repo_root,
        sha256_text=sha256_text,
        sha256_file=sha256_file,
        result_cls=result_cls,
    )
    if registry_result is not None and registry_write is not None:
        results.append(registry_result)
        writes.append(registry_write)

    composite_result, composite_write = sync_web_composites(
        cfg,
        source=source,
        repo_root=repo_root,
        export_root=export_root,
        dry_run=dry_run,
        generated_at=generated_at,
        sha256_text=sha256_text,
        sha256_file=sha256_file,
        result_cls=result_cls,
    )
    if composite_result is not None and composite_write is not None:
        results.append(composite_result)
        writes.append(composite_write)

    return results, writes


__all__ = ("collect_derived_snapshot_writes",)
