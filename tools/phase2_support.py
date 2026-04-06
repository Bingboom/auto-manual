from __future__ import annotations

import os
import shlex
import shutil
from pathlib import Path
from typing import Any

from tools.config_loader import load_config_mapping
from tools.sync_data_config import (
    cli_bin as _cli_bin_impl,
    cli_command_exists as _cli_command_exists_impl,
    cli_command_parts as _cli_command_parts_impl,
    env_value as _env_value_impl,
    phase2_identity as _phase2_identity_impl,
    provider_name as _provider_name_impl,
    resolved_cli_command_parts as _resolved_cli_command_parts_impl,
    sync_phase2_cfg as _sync_phase2_cfg_impl,
)
from tools.sync_data import (
    LarkCliSource,
    _parse_json_payload as _sync_parse_json_payload,
)

_SUPPORTED_PROVIDERS = {"lark_cli", "lark-cli", "cli"}
_SUPPORTED_IDENTITIES = {"user", "bot"}


def load_config(config_path: Path) -> dict[str, Any]:
    return load_config_mapping(config_path)


def cli_bin(cfg: dict[str, Any]) -> str:
    return _cli_bin_impl(cfg)


def cli_command_exists(cli_bin: str) -> bool:
    return _cli_command_exists_impl(
        cli_bin,
        split_command=shlex.split,
        which=shutil.which,
        path_type=Path,
    )


def cli_command_parts(cli_bin: str) -> list[str]:
    return _cli_command_parts_impl(cli_bin, split_command=shlex.split)


def resolved_cli_command_parts(cli_bin: str) -> list[str]:
    return _resolved_cli_command_parts_impl(
        cli_bin,
        split_command=shlex.split,
        which=shutil.which,
        path_type=Path,
    )


def parse_json_payload(raw_text: str) -> dict[str, Any]:
    return _sync_parse_json_payload(raw_text)


def env_value(name: str) -> str:
    return _env_value_impl(name, os.environ)


def phase2_identity() -> str:
    return _phase2_identity_impl(os.environ, supported_identities=_SUPPORTED_IDENTITIES)


def provider_name(cfg: dict[str, Any]) -> str:
    return _provider_name_impl(cfg, supported_providers=_SUPPORTED_PROVIDERS)


def sync_phase2_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    return _sync_phase2_cfg_impl(cfg)
