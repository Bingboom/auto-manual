#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
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
ROW_KEY_MAPPING_FILE = "row_key_mapping.csv"
PAGE_REGISTRY_FILE = "page_registry.csv"
SYMBOLS_BLOCKS_FILE = "symbols_blocks.csv"

PHASE2_REQUIRED_TABLE_FILES: dict[str, str] = {
    "spec_master": SPEC_MASTER_FILE,
    "spec_footnotes": SPEC_FOOTNOTES_FILE,
    "spec_notes": SPEC_NOTES_FILE,
    "spec_titles": SPEC_TITLES_FILE,
    "symbols_blocks": SYMBOLS_BLOCKS_FILE,
}
PHASE2_REQUIRED_DERIVED_FILES: dict[str, str] = {
    "row_key_mapping": ROW_KEY_MAPPING_FILE,
}


@dataclass(frozen=True)
class DataSnapshotPaths:
    structured_data_dir: Path
    page_registry_csv: Path
    page_blocks_dir: Path
    spec_master_csv: Path
    spec_footnotes_csv: Path
    spec_notes_csv: Path
    spec_titles_csv: Path
    row_key_mapping_csv: Path


@dataclass(frozen=True)
class Phase2SnapshotStatus:
    valid: bool
    export_root: Path
    manifest_path: Path
    issues: tuple[str, ...] = ()


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


def _phase2_candidate_export_root(
    cfg: dict[str, Any],
    *,
    repo_root: Path,
    model: str | None = None,
    region: str | None = None,
) -> Path:
    sync_cfg = _sync_phase2_cfg(cfg)
    configured_export_root = resolve_optional_repo_path(
        repo_root,
        sync_cfg.get("export_root"),
        model=model,
        region=region,
    )
    if configured_export_root is not None:
        return configured_export_root
    return repo_root / PHASE2_DEFAULT_EXPORT_DIR


def _phase2_candidate_manifest_path(
    cfg: dict[str, Any],
    *,
    repo_root: Path,
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
    return _phase2_candidate_export_root(
        cfg,
        repo_root=repo_root,
        model=model,
        region=region,
    ) / SNAPSHOT_MANIFEST_FILE


def _phase2_snapshot_required_files(export_root: Path) -> tuple[Path, ...]:
    return tuple(
        export_root / file_name
        for file_name in (
            *PHASE2_REQUIRED_TABLE_FILES.values(),
            *PHASE2_REQUIRED_DERIVED_FILES.values(),
        )
    )


def _load_phase2_manifest(manifest_path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, f"snapshot manifest is not valid JSON: {exc.msg}"
    except OSError as exc:
        return None, f"snapshot manifest cannot be read: {exc}"
    if not isinstance(payload, dict):
        return None, "snapshot manifest root must be a mapping"
    return payload, None


def _manifest_logical_names(raw_entries: Any) -> set[str]:
    if not isinstance(raw_entries, list):
        return set()
    names: set[str] = set()
    for entry in raw_entries:
        if not isinstance(entry, dict):
            continue
        logical_name = str(entry.get("logical_name") or "").strip()
        if logical_name:
            names.add(logical_name)
    return names


def inspect_phase2_snapshot(
    cfg: dict[str, Any],
    *,
    repo_root: Path,
    model: str | None = None,
    region: str | None = None,
) -> Phase2SnapshotStatus:
    export_root = _phase2_candidate_export_root(
        cfg,
        repo_root=repo_root,
        model=model,
        region=region,
    )
    manifest_path = _phase2_candidate_manifest_path(
        cfg,
        repo_root=repo_root,
        model=model,
        region=region,
    )
    issues: list[str] = []
    if not manifest_path.exists():
        return Phase2SnapshotStatus(
            valid=False,
            export_root=export_root,
            manifest_path=manifest_path,
            issues=(f"snapshot manifest not found: {manifest_path}",),
        )

    manifest, manifest_error = _load_phase2_manifest(manifest_path)
    if manifest_error:
        return Phase2SnapshotStatus(
            valid=False,
            export_root=export_root,
            manifest_path=manifest_path,
            issues=(manifest_error,),
        )

    for file_name in (
        *PHASE2_REQUIRED_TABLE_FILES.values(),
        *PHASE2_REQUIRED_DERIVED_FILES.values(),
    ):
        path = export_root / file_name
        if not path.exists():
            issues.append(f"required snapshot file is missing: {path}")

    requested_tables = {
        str(item).strip()
        for item in (manifest or {}).get("requested_tables", [])
        if str(item).strip()
    }
    synced_tables = _manifest_logical_names((manifest or {}).get("tables"))
    derived_files = _manifest_logical_names((manifest or {}).get("derived_files"))
    skipped_tables = {
        str(item).strip()
        for item in (manifest or {}).get("skipped_tables", [])
        if str(item).strip()
    }

    missing_requested = sorted(set(PHASE2_REQUIRED_TABLE_FILES) - requested_tables)
    if missing_requested:
        issues.append(
            "snapshot manifest did not request required table(s): "
            + ", ".join(missing_requested)
        )

    missing_synced = sorted(set(PHASE2_REQUIRED_TABLE_FILES) - synced_tables)
    if missing_synced:
        issues.append(
            "snapshot manifest does not include synced result(s) for required table(s): "
            + ", ".join(missing_synced)
        )

    skipped_required = sorted(set(PHASE2_REQUIRED_TABLE_FILES) & skipped_tables)
    if skipped_required:
        issues.append(
            "snapshot manifest skipped required table(s): "
            + ", ".join(skipped_required)
        )

    missing_derived = sorted(set(PHASE2_REQUIRED_DERIVED_FILES) - derived_files)
    if missing_derived:
        issues.append(
            "snapshot manifest does not include required derived file(s): "
            + ", ".join(missing_derived)
        )

    return Phase2SnapshotStatus(
        valid=not issues,
        export_root=export_root,
        manifest_path=manifest_path,
        issues=tuple(issues),
    )


def _repo_phase1_root(repo_root: Path) -> Path:
    return (repo_root / STRUCTURED_DATA_DEFAULT_DIR).resolve(strict=False)


def _should_prefer_phase2_root(*, configured: Path | None, repo_root: Path) -> bool:
    if configured is None:
        return True
    return configured.resolve(strict=False) == _repo_phase1_root(repo_root)


def _should_prefer_phase2_file(*, configured: Path | None, repo_root: Path, default_file_name: str) -> bool:
    if configured is None:
        return True
    return configured.resolve(strict=False) == (_repo_phase1_root(repo_root) / default_file_name).resolve(strict=False)


def phase2_snapshot_is_valid(
    cfg: dict[str, Any],
    *,
    repo_root: Path,
    model: str | None = None,
    region: str | None = None,
) -> bool:
    return inspect_phase2_snapshot(
        cfg,
        repo_root=repo_root,
        model=model,
        region=region,
    ).valid


def resolve_active_data_root(
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

    if phase2_snapshot_is_valid(
        cfg,
        repo_root=repo_root,
        model=model,
        region=region,
    ) and _should_prefer_phase2_root(configured=configured, repo_root=repo_root):
        return _phase2_candidate_export_root(
            cfg,
            repo_root=repo_root,
            model=model,
            region=region,
        )
    if configured is not None:
        return configured
    return repo_root / STRUCTURED_DATA_DEFAULT_DIR


def resolve_structured_data_dir(
    cfg: dict[str, Any],
    *,
    repo_root: Path,
    data_root: str | Path | None = None,
    model: str | None = None,
    region: str | None = None,
) -> Path:
    return resolve_active_data_root(
        cfg,
        repo_root=repo_root,
        data_root=data_root,
        model=model,
        region=region,
    )


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

    if phase2_snapshot_is_valid(
        cfg,
        repo_root=repo_root,
        model=model,
        region=region,
    ) and _should_prefer_phase2_root(configured=configured, repo_root=repo_root):
        return resolve_active_data_root(
            cfg,
            repo_root=repo_root,
            data_root=None,
            model=model,
            region=region,
        )
    if configured is not None:
        return configured
    return resolve_active_data_root(
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

    if phase2_snapshot_is_valid(
        cfg,
        repo_root=repo_root,
        model=model,
        region=region,
    ) and _should_prefer_phase2_file(
        configured=configured,
        repo_root=repo_root,
        default_file_name=default_file_name,
    ):
        structured_dir = resolve_active_data_root(
            cfg,
            repo_root=repo_root,
            data_root=None,
            model=model,
            region=region,
        )
        return structured_dir / default_file_name
    if configured is not None:
        return configured

    structured_dir = resolve_active_data_root(
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
        row_key_mapping_csv=_resolve_structured_file_path(
            cfg,
            repo_root=repo_root,
            data_root=data_root,
            config_key="row_key_mapping_csv",
            default_file_name=ROW_KEY_MAPPING_FILE,
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
    return _phase2_candidate_export_root(
        cfg,
        repo_root=repo_root,
        model=model,
        region=region,
    )


def resolve_phase2_manifest_path(
    cfg: dict[str, Any],
    *,
    repo_root: Path,
    data_root: str | Path | None = None,
    model: str | None = None,
    region: str | None = None,
) -> Path:
    cli_root = _resolve_cli_data_root(repo_root, data_root=data_root)
    if cli_root is not None:
        return cli_root / SNAPSHOT_MANIFEST_FILE
    return _phase2_candidate_manifest_path(
        cfg,
        repo_root=repo_root,
        model=model,
        region=region,
    )
