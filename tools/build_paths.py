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
