#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping

from tools.spec_master_sources import has_source_table_ids


def sync_phase2_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    sync_cfg_raw = cfg.get("sync", {})
    sync_cfg = sync_cfg_raw if isinstance(sync_cfg_raw, dict) else {}
    phase2_raw = sync_cfg.get("phase2", {})
    return phase2_raw if isinstance(phase2_raw, dict) else {}


def phase2_tables_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    phase2_cfg = sync_phase2_cfg(cfg)
    tables_raw = phase2_cfg.get("tables", {})
    return tables_raw if isinstance(tables_raw, dict) else {}


def provider_name(cfg: dict[str, Any], *, supported_providers: set[str]) -> str:
    raw = str(sync_phase2_cfg(cfg).get("provider", "lark_cli")).strip().lower() or "lark_cli"
    if raw not in supported_providers:
        raise RuntimeError(f"Unsupported sync.phase2.provider: {raw}")
    return "lark_cli"


def cli_bin(cfg: dict[str, Any]) -> str:
    raw = str(sync_phase2_cfg(cfg).get("cli_bin", "lark-cli")).strip()
    return raw or "lark-cli"


def phase2_identity(environ: Mapping[str, str], *, supported_identities: set[str]) -> str:
    raw = str(environ.get("FEISHU_PHASE2_IDENTITY", "user")).strip().lower() or "user"
    if raw not in supported_identities:
        raise RuntimeError(
            "FEISHU_PHASE2_IDENTITY must be one of: " + ", ".join(sorted(supported_identities))
        )
    return raw


def selected_tables(
    raw_tables: list[str],
    *,
    table_order: tuple[str, ...],
    table_schemas: Mapping[str, Any],
) -> tuple[str, ...]:
    if not raw_tables:
        return table_order
    selected: list[str] = []
    for raw in raw_tables:
        name = str(raw).strip().lower()
        if name not in table_order:
            raise RuntimeError(
                "Unsupported --table value: "
                + name
                + ". Expected one of: "
                + ", ".join(table_order)
            )
        if name not in selected:
            selected.append(name)
    return tuple(name for name in table_order if name in selected)


def env_value(env_name: str, environ: Mapping[str, str]) -> str:
    value = str(environ.get(env_name, "")).strip()
    if not value:
        raise RuntimeError(f"Required environment variable is not set: {env_name}")
    return value


def table_cfg(cfg: dict[str, Any], logical_name: str) -> dict[str, Any]:
    tables_cfg = phase2_tables_cfg(cfg)
    table_cfg_raw = tables_cfg.get(logical_name, {})
    return table_cfg_raw if isinstance(table_cfg_raw, dict) else {}


def table_env_names(cfg: dict[str, Any], logical_name: str) -> tuple[str, str, str | None]:
    phase2_cfg = sync_phase2_cfg(cfg)
    logical_cfg = table_cfg(cfg, logical_name)
    base_token_env = str(
        logical_cfg.get("base_token_env") or phase2_cfg.get("base_token_env") or ""
    ).strip()
    table_id_env = str(logical_cfg.get("table_id_env") or "").strip()
    view_id_env = str(logical_cfg.get("view_id_env") or "").strip() or None
    return base_token_env, table_id_env, view_id_env


def table_binding_values(cfg: dict[str, Any], logical_name: str) -> tuple[str | None, str | None]:
    logical_cfg = table_cfg(cfg, logical_name)
    table_id = str(logical_cfg.get("table_id") or "").strip() or None
    view_id = str(logical_cfg.get("view_id") or "").strip() or None
    return table_id, view_id


def cli_command_parts(
    cli_bin: str,
    *,
    split_command: Callable[[str], list[str]],
) -> list[str]:
    parts = split_command(cli_bin)
    if not parts:
        raise RuntimeError("sync.phase2.cli_bin must not be empty")
    return parts


def resolved_cli_command_parts(
    cli_bin: str,
    *,
    split_command: Callable[[str], list[str]],
    which: Callable[[str], str | None],
    path_type: type[Path] = Path,
) -> list[str]:
    parts = cli_command_parts(cli_bin, split_command=split_command)
    command = parts[0]
    command_path = path_type(command)
    if command_path.is_absolute():
        resolved_command = command
    else:
        resolved_command = which(command) or command
    return [resolved_command, *parts[1:]]


def cli_command_exists(
    cli_bin: str,
    *,
    split_command: Callable[[str], list[str]],
    which: Callable[[str], str | None],
    path_type: type[Path] = Path,
) -> bool:
    command = cli_command_parts(cli_bin, split_command=split_command)[0]
    command_path = path_type(command)
    if command_path.is_absolute():
        return command_path.exists()
    return which(command) is not None


def collect_sync_preflight_errors(
    cfg: dict[str, Any],
    *,
    table_names: list[str] | tuple[str, ...] | None,
    environ: Mapping[str, str],
    require_cli: bool,
    table_order: tuple[str, ...],
    table_schemas: Mapping[str, Any],
    cli_bin_fn: Callable[[dict[str, Any]], str],
    cli_command_parts_fn: Callable[[str], list[str]],
    cli_command_exists_fn: Callable[[str], bool],
    table_env_names_fn: Callable[[dict[str, Any], str], tuple[str, str, str | None]],
) -> list[str]:
    selected = selected_tables(list(table_names or []), table_order=table_order, table_schemas=table_schemas)
    errors: list[str] = []

    if require_cli:
        cli_bin_value = cli_bin_fn(cfg)
        try:
            command = cli_command_parts_fn(cli_bin_value)[0]
        except RuntimeError as exc:
            errors.append(str(exc))
        else:
            if not cli_command_exists_fn(cli_bin_value):
                errors.append(f"sync.phase2.cli_bin executable is not available: {command}")

    required_env_names: list[str] = []
    seen_env_names: set[str] = set()
    for logical_name in selected:
        base_token_env, table_id_env, view_id_env = table_env_names_fn(cfg, logical_name)
        table_id, view_id = table_binding_values(cfg, logical_name)
        spec_master_uses_sources = logical_name == "spec_master" and has_source_table_ids(cfg, environ=environ)
        if not base_token_env:
            errors.append(
                f"sync.phase2.tables.{logical_name}.base_token_env is required, "
                "or provide sync.phase2.base_token_env"
            )
        elif base_token_env not in seen_env_names:
            seen_env_names.add(base_token_env)
            required_env_names.append(base_token_env)
        if not table_id and not table_id_env:
            if not spec_master_uses_sources:
                errors.append(
                    f"sync.phase2.tables.{logical_name}.table_id or "
                    f"sync.phase2.tables.{logical_name}.table_id_env is required"
                )
        elif table_id is None and table_id_env not in seen_env_names:
            seen_env_names.add(table_id_env)
            required_env_names.append(table_id_env)
        if view_id is None and view_id_env and view_id_env not in seen_env_names:
            seen_env_names.add(view_id_env)
            required_env_names.append(view_id_env)

    missing_env_names = [
        env_name
        for env_name in required_env_names
        if not str(environ.get(env_name, "")).strip()
    ]
    if missing_env_names:
        errors.append(
            "Required environment variables are not set: "
            + ", ".join(missing_env_names)
        )
    return errors


def resolve_table_binding_kwargs(
    cfg: dict[str, Any],
    logical_name: str,
    *,
    table_schemas: Mapping[str, Any],
    table_env_names_fn: Callable[[dict[str, Any], str], tuple[str, str, str | None]],
    env_value_fn: Callable[[str], str],
) -> dict[str, Any]:
    if logical_name not in table_schemas:
        raise RuntimeError(f"Unknown sync table: {logical_name}")
    base_token_env, table_id_env, view_id_env = table_env_names_fn(cfg, logical_name)
    table_id, view_id = table_binding_values(cfg, logical_name)

    if not base_token_env:
        raise RuntimeError(
            f"sync.phase2.tables.{logical_name}.base_token_env is required, "
            "or provide sync.phase2.base_token_env"
        )
    if table_id is None and not table_id_env:
        raise RuntimeError(
            f"sync.phase2.tables.{logical_name}.table_id or "
            f"sync.phase2.tables.{logical_name}.table_id_env is required"
        )

    return {
        "logical_name": logical_name,
        "schema": table_schemas[logical_name],
        "base_token_env": base_token_env,
        "table_id_env": table_id_env,
        "view_id_env": view_id_env,
        "base_token": env_value_fn(base_token_env),
        "table_id": table_id if table_id is not None else env_value_fn(table_id_env),
        "view_id": view_id if view_id is not None else (env_value_fn(view_id_env) if view_id_env else None),
    }
