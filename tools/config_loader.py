from __future__ import annotations

from pathlib import Path
from typing import Any


def _load_yaml_mapping(config_path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PyYAML not installed. Please run: pip install pyyaml") from exc

    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        raise RuntimeError(f"Config root must be a mapping: {config_path}")
    return data


def load_config_mapping(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        raise RuntimeError(f"Config not found: {config_path}")

    try:
        return _load_yaml_mapping(config_path)
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Failed to load config: {config_path}") from exc


def try_load_config_mapping(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        return {}

    try:
        return _load_yaml_mapping(config_path)
    except Exception:
        return {}
