#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.utils.targets import format_tokenized

STRUCTURED_DATA_DEFAULT_DIR = "data/phase1"
PHASE2_DEFAULT_EXPORT_DIR = "data/phase2"
SNAPSHOT_MANIFEST_FILE = "snapshot_manifest.json"

SPEC_MASTER_FILE = "Spec_Master.csv"
SPEC_FOOTNOTES_FILE = "Spec_Footnotes.csv"
SPEC_NOTES_FILE = "Spec_Notes.csv"
SPEC_TITLES_FILE = "spec_titles.csv"
PAGE_REGISTRY_FILE = "page_registry.csv"


@dataclass(frozen=True)
class DataSnapshotPaths:
    structured_data_dir: Path
    page_registry_csv: Path
    page_blocks_dir: Path
    spec_master_csv: Path
    spec_footnotes_csv: Path
    spec_notes_csv: Path
    spec_titles_csv: Path


def _paths_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    raw = cfg.get("paths", {})
    return raw if isinstance(raw, dict) else {}


def _sync_phase2_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    sync_cfg_raw = cfg.get("sync", {})
    sync_cfg = sync_cfg_raw if isinstance(sync_cfg_raw, dict) else {}
    phase2_raw = sync_cfg.get("phase2", {})
    return phase2_raw if isinstance(phase2_raw, dict) else {}


def resolve_repo_path(
    repo_root: Path,
    raw_path: str,
    *,
    model: str | None = None,
    region: str | None = None,
) -> Path:
    rendered = format_tokenized(raw_path, None, model, region)
    path = Path(rendered)
    if path.is_absolute():
        return path
    return repo_root / path


def resolve_optional_repo_path(
    repo_root: Path,
    raw_path: object,
    *,
    model: str | None = None,
    region: str | None = None,
) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None
    return resolve_repo_path(
        repo_root,
        raw_path.strip(),
        model=model,
        region=region,
    )


def _resolve_cli_data_root(
    repo_root: Path,
    *,
    data_root: str | Path | None,
) -> Path | None:
    if data_root is None:
        return None
    if isinstance(data_root, Path):
        return data_root if data_root.is_absolute() else (repo_root / data_root)
    raw = str(data_root).strip()
    if not raw:
        return None
    path = Path(raw)
    return path if path.is_absolute() else (repo_root / path)


def resolve_structured_data_dir(
    cfg: dict[str, Any],
    *,
    repo_root: Path,
    data_root: str | Path | None = None,
    model: str | None = None,
    region: str | None = None,
) -> Path:
    cli_root = _resolve_cli_data_root(repo_root, data_root=data_root)
    if cli_root is not None:
        return cli_root

    paths_cfg = _paths_cfg(cfg)
    configured = resolve_optional_repo_path(
        repo_root,
        paths_cfg.get("structured_data_dir"),
        model=model,
        region=region,
    )
    if configured is not None:
        return configured
    return repo_root / STRUCTURED_DATA_DEFAULT_DIR


def resolve_page_registry_csv(
    cfg: dict[str, Any],
    *,
    repo_root: Path,
    model: str | None = None,
    region: str | None = None,
) -> Path:
    paths_cfg = _paths_cfg(cfg)
    configured = resolve_optional_repo_path(
        repo_root,
        paths_cfg.get("page_registry_csv"),
        model=model,
        region=region,
    )
    if configured is not None:
        return configured
    return repo_root / STRUCTURED_DATA_DEFAULT_DIR / PAGE_REGISTRY_FILE


def resolve_page_blocks_dir(
    cfg: dict[str, Any],
    *,
    repo_root: Path,
    data_root: str | Path | None = None,
    model: str | None = None,
    region: str | None = None,
) -> Path:
    cli_root = _resolve_cli_data_root(repo_root, data_root=data_root)
    if cli_root is not None:
        return cli_root

    paths_cfg = _paths_cfg(cfg)
    configured = resolve_optional_repo_path(
        repo_root,
        paths_cfg.get("page_blocks_dir"),
        model=model,
        region=region,
    )
    if configured is not None:
        return configured
    return resolve_structured_data_dir(
        cfg,
        repo_root=repo_root,
        data_root=None,
        model=model,
        region=region,
    )


def _resolve_structured_file_path(
    cfg: dict[str, Any],
    *,
    repo_root: Path,
    data_root: str | Path | None,
    config_key: str,
    default_file_name: str,
    model: str | None = None,
    region: str | None = None,
) -> Path:
    cli_root = _resolve_cli_data_root(repo_root, data_root=data_root)
    if cli_root is not None:
        return cli_root / default_file_name

    paths_cfg = _paths_cfg(cfg)
    configured = resolve_optional_repo_path(
        repo_root,
        paths_cfg.get(config_key),
        model=model,
        region=region,
    )
    if configured is not None:
        return configured

    structured_dir = resolve_structured_data_dir(
        cfg,
        repo_root=repo_root,
        data_root=None,
        model=model,
        region=region,
    )
    return structured_dir / default_file_name


def resolve_data_snapshot_paths(
    cfg: dict[str, Any],
    *,
    repo_root: Path,
    data_root: str | Path | None = None,
    model: str | None = None,
    region: str | None = None,
) -> DataSnapshotPaths:
    return DataSnapshotPaths(
        structured_data_dir=resolve_structured_data_dir(
            cfg,
            repo_root=repo_root,
            data_root=data_root,
            model=model,
            region=region,
        ),
        page_registry_csv=resolve_page_registry_csv(
            cfg,
            repo_root=repo_root,
            model=model,
            region=region,
        ),
        page_blocks_dir=resolve_page_blocks_dir(
            cfg,
            repo_root=repo_root,
            data_root=data_root,
            model=model,
            region=region,
        ),
        spec_master_csv=_resolve_structured_file_path(
            cfg,
            repo_root=repo_root,
            data_root=data_root,
            config_key="spec_master_csv",
            default_file_name=SPEC_MASTER_FILE,
            model=model,
            region=region,
        ),
        spec_footnotes_csv=_resolve_structured_file_path(
            cfg,
            repo_root=repo_root,
            data_root=data_root,
            config_key="spec_footnotes_csv",
            default_file_name=SPEC_FOOTNOTES_FILE,
            model=model,
            region=region,
        ),
        spec_notes_csv=_resolve_structured_file_path(
            cfg,
            repo_root=repo_root,
            data_root=data_root,
            config_key="spec_notes_csv",
            default_file_name=SPEC_NOTES_FILE,
            model=model,
            region=region,
        ),
        spec_titles_csv=_resolve_structured_file_path(
            cfg,
            repo_root=repo_root,
            data_root=data_root,
            config_key="spec_titles_csv",
            default_file_name=SPEC_TITLES_FILE,
            model=model,
            region=region,
        ),
    )


def resolve_phase2_export_root(
    cfg: dict[str, Any],
    *,
    repo_root: Path,
    data_root: str | Path | None = None,
    model: str | None = None,
    region: str | None = None,
) -> Path:
    cli_root = _resolve_cli_data_root(repo_root, data_root=data_root)
    if cli_root is not None:
        return cli_root

    sync_cfg = _sync_phase2_cfg(cfg)
    configured_export_root = resolve_optional_repo_path(
        repo_root,
        sync_cfg.get("export_root"),
        model=model,
        region=region,
    )
    if configured_export_root is not None:
        return configured_export_root

    structured_dir = resolve_optional_repo_path(
        repo_root,
        _paths_cfg(cfg).get("structured_data_dir"),
        model=model,
        region=region,
    )
    if structured_dir is not None:
        return structured_dir
    return repo_root / PHASE2_DEFAULT_EXPORT_DIR


def resolve_phase2_manifest_path(
    cfg: dict[str, Any],
    *,
    repo_root: Path,
    data_root: str | Path | None = None,
    model: str | None = None,
    region: str | None = None,
) -> Path:
    sync_cfg = _sync_phase2_cfg(cfg)
    configured = resolve_optional_repo_path(
        repo_root,
        sync_cfg.get("manifest_path"),
        model=model,
        region=region,
    )
    if configured is not None:
        return configured
    return resolve_phase2_export_root(
        cfg,
        repo_root=repo_root,
        data_root=data_root,
        model=model,
        region=region,
    ) / SNAPSHOT_MANIFEST_FILE
