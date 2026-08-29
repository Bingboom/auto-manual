from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from tools.config_loader import load_config_mapping
from tools.utils.path_utils import (
    Paths,
    PathSegments,
    docs_build_dir_of,
    paths_for_docs_dir,
    releases_of,
    review_dir_of,
    version_tracking_of,
)


def resolve_path_from_root(repo_root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else (repo_root / path)


def resolve_staging_root(
    *,
    repo_root: Path,
    args: Any,
    env_var: str,
) -> Path | None:
    raw = ""
    if isinstance(getattr(args, "staging_root", None), str) and args.staging_root.strip():
        raw = args.staging_root.strip()
    elif str(os.environ.get(env_var, "")).strip():
        raw = str(os.environ.get(env_var, "")).strip()
    if not raw:
        return None
    return resolve_path_from_root(repo_root, raw)


def staging_docs_build_dir(
    *,
    repo_root: Path,
    args: Any,
    env_var: str,
) -> Path | None:
    staging_root = resolve_staging_root(repo_root=repo_root, args=args, env_var=env_var)
    if staging_root is None:
        return None
    return docs_build_dir_of(staging_root / PathSegments.DOCS)


def staging_version_tracking_root(
    *,
    repo_root: Path,
    args: Any,
    env_var: str,
) -> Path | None:
    staging_root = resolve_staging_root(repo_root=repo_root, args=args, env_var=env_var)
    if staging_root is None:
        return None
    return version_tracking_of(staging_root)


def staging_releases_root(
    *,
    repo_root: Path,
    args: Any,
    env_var: str,
) -> Path | None:
    staging_root = resolve_staging_root(repo_root=repo_root, args=args, env_var=env_var)
    if staging_root is None:
        return None
    return releases_of(staging_root)


def load_config(config_path: Path) -> dict[str, Any]:
    return load_config_mapping(config_path)


def resolve_layout_params_csv(
    config_path: Path,
    *,
    repo_root: Path,
    config_loader: Callable[[Path], dict[str, Any]] = load_config,
) -> Path:
    cfg = config_loader(config_path)
    paths_cfg = cfg.get("paths", {})
    if isinstance(paths_cfg, dict):
        raw = paths_cfg.get("layout_params_csv")
        if isinstance(raw, str) and raw.strip():
            return resolve_path_from_root(repo_root, raw.strip())
    return Paths(root=repo_root).layout_params_csv


def resolve_idml_layout_param_overlays(
    config_path: Path,
    *,
    repo_root: Path,
    model: str | None = None,
    region: str | None = None,
    config_loader: Callable[[Path], dict[str, Any]] = load_config,
) -> tuple[Path, ...]:
    """Resolve global and target-selected additive IDML token layers."""

    cfg = config_loader(config_path)
    paths_cfg = cfg.get("paths", {})
    if not isinstance(paths_cfg, dict):
        return ()
    raw = paths_cfg.get("idml_layout_params_overlays", [])
    raw_by_target = paths_cfg.get("idml_layout_params_overlays_by_target", {})
    if raw is None:
        raw = []
    if not isinstance(raw, list) or any(
        not isinstance(value, str) or not value.strip() for value in raw
    ):
        raise ValueError("paths.idml_layout_params_overlays must be a list of paths")
    if raw_by_target is None:
        raw_by_target = {}
    if not isinstance(raw_by_target, dict) or any(
        not isinstance(key, str)
        or not key.strip()
        or not isinstance(values, list)
        or any(not isinstance(value, str) or not value.strip() for value in values)
        for key, values in raw_by_target.items()
    ):
        raise ValueError(
            "paths.idml_layout_params_overlays_by_target must map "
            "Document_Key to lists of paths"
        )

    selected = list(raw)
    build_cfg = cfg.get("build", {})
    if not isinstance(build_cfg, dict):
        build_cfg = {}
    resolved_model = str(model or build_cfg.get("default_model") or "").strip()
    resolved_region = str(region or build_cfg.get("default_region") or "").strip()
    if resolved_model and resolved_region:
        document_key = f"{resolved_model}_{resolved_region}".casefold()
        matches = [
            values
            for key, values in raw_by_target.items()
            if key.strip().casefold() == document_key
        ]
        if len(matches) > 1:
            raise ValueError(
                "paths.idml_layout_params_overlays_by_target contains duplicate "
                "case-insensitive Document_Key entries for "
                f"{resolved_model}_{resolved_region}"
            )
        if matches:
            selected.extend(matches[0])
    if len({value.strip() for value in selected}) != len(selected):
        raise ValueError("IDML layout parameter overlay paths must be unique")
    return tuple(
        resolve_path_from_root(repo_root, value.strip())
        for value in selected
    )


def resolve_idml_assembly_plan(
    config_path: Path,
    *,
    repo_root: Path,
    model: str | None = None,
    region: str | None = None,
    config_loader: Callable[[Path], dict[str, Any]] = load_config,
) -> Path | None:
    """Resolve an explicitly configured candidate IDML assembly contract.

    Candidate target assembly is opt-in data.  There is intentionally no
    filename/model discovery fallback here: approved plans are resolved by
    their own registry, while an unconfigured target keeps the measured-LaTeX
    compatibility path.
    """

    cfg = config_loader(config_path)
    paths_cfg = cfg.get("paths", {})
    if not isinstance(paths_cfg, dict):
        return None
    raw = paths_cfg.get("idml_assembly_plan")
    raw_by_target = paths_cfg.get("idml_assembly_plans")
    if raw is not None and raw_by_target is not None:
        raise ValueError(
            "paths.idml_assembly_plan and paths.idml_assembly_plans are "
            "mutually exclusive"
        )
    if raw is not None:
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError("paths.idml_assembly_plan must be a non-empty path")
        return resolve_path_from_root(repo_root, raw.strip())
    if raw_by_target is None:
        return None
    if not isinstance(raw_by_target, dict) or any(
        not isinstance(key, str)
        or not key.strip()
        or not isinstance(value, str)
        or not value.strip()
        for key, value in raw_by_target.items()
    ):
        raise ValueError(
            "paths.idml_assembly_plans must map Document_Key to non-empty paths"
        )
    build_cfg = cfg.get("build", {})
    if not isinstance(build_cfg, dict):
        build_cfg = {}
    resolved_model = str(model or build_cfg.get("default_model") or "").strip()
    resolved_region = str(region or build_cfg.get("default_region") or "").strip()
    if not resolved_model or not resolved_region:
        return None
    document_key = f"{resolved_model}_{resolved_region}".casefold()
    matches = [
        value
        for key, value in raw_by_target.items()
        if key.strip().casefold() == document_key
    ]
    if len(matches) > 1:
        raise ValueError(
            "paths.idml_assembly_plans contains duplicate case-insensitive "
            f"Document_Key entries for {resolved_model}_{resolved_region}"
        )
    if not matches:
        return None
    return resolve_path_from_root(repo_root, matches[0].strip())


def resolve_docs_dir(
    config_path: Path,
    *,
    repo_root: Path,
    config_loader: Callable[[Path], dict[str, Any]] = load_config,
) -> Path:
    cfg = config_loader(config_path)
    paths_cfg = cfg.get("paths", {})
    if isinstance(paths_cfg, dict):
        raw = paths_cfg.get("docs_dir")
        if isinstance(raw, str) and raw.strip():
            return resolve_path_from_root(repo_root, raw.strip())
    return Paths(root=repo_root).docs_dir


def clean_targets_for_config(
    config_path: Path,
    *,
    repo_root: Path,
    config_loader: Callable[[Path], dict[str, Any]] = load_config,
) -> tuple[Path, Path]:
    docs_dir = resolve_docs_dir(config_path, repo_root=repo_root, config_loader=config_loader)
    return paths_for_docs_dir(repo_root, docs_dir).clean_targets()


def review_root_for_config(
    config_path: Path,
    *,
    repo_root: Path,
    config_loader: Callable[[Path], dict[str, Any]] = load_config,
) -> Path:
    docs_dir = resolve_docs_dir(config_path, repo_root=repo_root, config_loader=config_loader)
    return review_dir_of(docs_dir)


def version_tracking_root(*, repo_root: Path, base_root: Path | None = None) -> Path:
    actual_base_root = base_root or repo_root
    return version_tracking_of(actual_base_root)
