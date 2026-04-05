from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.config_loader import load_config_mapping
from tools.sync_data import (
    LarkCliSource,
    _cli_bin as _sync_cli_bin,
    _cli_command_exists as _sync_cli_command_exists,
    _cli_command_parts as _sync_cli_command_parts,
    _env_value as _sync_env_value,
    _parse_json_payload as _sync_parse_json_payload,
    _phase2_identity as _sync_phase2_identity,
    _provider_name as _sync_provider_name,
    _resolved_cli_command_parts as _sync_resolved_cli_command_parts,
    _sync_phase2_cfg as _sync_phase2_cfg,
)


def load_config(config_path: Path) -> dict[str, Any]:
    return load_config_mapping(config_path)


def cli_bin(cfg: dict[str, Any]) -> str:
    return _sync_cli_bin(cfg)


def cli_command_exists(cli_bin: str) -> bool:
    return _sync_cli_command_exists(cli_bin)


def cli_command_parts(cli_bin: str) -> list[str]:
    return _sync_cli_command_parts(cli_bin)


def resolved_cli_command_parts(cli_bin: str) -> list[str]:
    return _sync_resolved_cli_command_parts(cli_bin)


def parse_json_payload(raw_text: str) -> dict[str, Any]:
    return _sync_parse_json_payload(raw_text)


def env_value(name: str) -> str:
    return _sync_env_value(name)


def phase2_identity() -> str:
    return _sync_phase2_identity()


def provider_name(cfg: dict[str, Any]) -> str:
    return _sync_provider_name(cfg)


def sync_phase2_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    return _sync_phase2_cfg(cfg)
