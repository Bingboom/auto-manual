from __future__ import annotations

import copy
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


def _resolve_extends_path(config_path: Path, raw_extends: Any) -> Path:
    extends_value = str(raw_extends or "").strip()
    if not extends_value:
        raise RuntimeError(f"Config extends must be a non-empty path: {config_path}")

    extends_path = Path(extends_value)
    if not extends_path.is_absolute():
        extends_path = (config_path.parent / extends_path).resolve()
    return extends_path


def _merge_config_mappings(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if key == "extends":
            continue
        if isinstance(merged.get(key), dict) and isinstance(value, dict):
            merged[key] = _merge_config_mappings(merged[key], value)
            continue
        merged[key] = copy.deepcopy(value)
    return merged


def _load_config_mapping_with_extends(config_path: Path, *, stack: tuple[Path, ...]) -> dict[str, Any]:
    resolved_path = config_path.resolve()
    if resolved_path in stack:
        cycle = " -> ".join(path.name for path in (*stack, resolved_path))
        raise RuntimeError(f"Config extends cycle detected: {cycle}")

    data = _load_yaml_mapping(resolved_path)
    raw_extends = data.get("extends")
    if raw_extends is None:
        data.pop("extends", None)
        return data

    base_path = _resolve_extends_path(resolved_path, raw_extends)
    if not base_path.exists():
        raise RuntimeError(f"Extended config not found: {base_path}")

    base_cfg = _load_config_mapping_with_extends(base_path, stack=(*stack, resolved_path))
    return _merge_config_mappings(base_cfg, data)


def load_config_mapping(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        raise RuntimeError(f"Config not found: {config_path}")

    try:
        return _load_config_mapping_with_extends(config_path, stack=())
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
