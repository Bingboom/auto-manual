from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable


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
    return staging_root / "docs" / "_build"


def staging_version_tracking_root(
    *,
    repo_root: Path,
    args: Any,
    env_var: str,
) -> Path | None:
    staging_root = resolve_staging_root(repo_root=repo_root, args=args, env_var=env_var)
    if staging_root is None:
        return None
    return staging_root / "reports" / "version_tracking"


def staging_releases_root(
    *,
    repo_root: Path,
    args: Any,
    env_var: str,
) -> Path | None:
    staging_root = resolve_staging_root(repo_root=repo_root, args=args, env_var=env_var)
    if staging_root is None:
        return None
    return staging_root / "reports" / "releases"


def load_config(config_path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PyYAML not installed. Please run: pip install pyyaml") from exc

    if not config_path.exists():
        raise RuntimeError(f"Config not found: {config_path}")

    try:
        with config_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except Exception as exc:
        raise RuntimeError(f"Failed to load config: {config_path}") from exc

    if not isinstance(data, dict):
        raise RuntimeError(f"Config root must be a mapping: {config_path}")
    return data


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
    return repo_root / "data" / "layout_params.csv"


def resolve_docs_dir(
    config_path: Path,
    *,
    repo_root: Path,
    config_loader: Callable[[Path], dict[str, Any]] = load_config,
) -> Path:
    try:
        cfg = config_loader(config_path)
    except RuntimeError:
        return repo_root / "docs"

    paths_cfg = cfg.get("paths", {})
    if isinstance(paths_cfg, dict):
        raw = paths_cfg.get("docs_dir")
        if isinstance(raw, str) and raw.strip():
            return resolve_path_from_root(repo_root, raw.strip())
    return repo_root / "docs"


def clean_targets_for_config(
    config_path: Path,
    *,
    repo_root: Path,
    config_loader: Callable[[Path], dict[str, Any]] = load_config,
) -> tuple[Path, Path]:
    docs_dir = resolve_docs_dir(config_path, repo_root=repo_root, config_loader=config_loader)
    return docs_dir / "_build", docs_dir / "renderers" / "latex" / "params.tex"


def review_root_for_config(
    config_path: Path,
    *,
    repo_root: Path,
    config_loader: Callable[[Path], dict[str, Any]] = load_config,
) -> Path:
    docs_dir = resolve_docs_dir(config_path, repo_root=repo_root, config_loader=config_loader)
    return docs_dir / "_review"


def version_tracking_root(*, repo_root: Path, base_root: Path | None = None) -> Path:
    actual_base_root = base_root or repo_root
    return actual_base_root / "reports" / "version_tracking"
