#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.document_link_queue import scalar_text
from tools.dingtalk.workspace import parse_node_id_from_url
from tools.phase2_support import (
    LarkCliSource,
    cli_bin,
    cli_command_exists,
    cli_command_parts,
    load_config,
    phase2_identity,
    sync_phase2_cfg,
)

OPERATOR_UNION_ID_FIELD = "operator_union_id"
DEFAULT_TARGET_NODE_URL_FIELD = "default_target_node_url"


@dataclass(frozen=True)
class DingTalkControlBinding:
    base_token_env: str
    table_id_env: str
    view_id_env: str | None
    record_id_env: str | None
    base_token: str
    table_id: str
    view_id: str | None
    record_id: str | None


@dataclass(frozen=True)
class DingTalkControlConfig:
    record_id: str
    operator_union_id: str
    default_target_node_url: str
    default_target_node_id: str


def dingtalk_control_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    raw = sync_phase2_cfg(cfg).get("dingtalk_control", {})
    return raw if isinstance(raw, dict) else {}


def dingtalk_control_env_names(cfg: dict[str, Any]) -> tuple[str, str, str | None, str | None]:
    phase2_cfg = sync_phase2_cfg(cfg)
    current_cfg = dingtalk_control_cfg(cfg)
    base_token_env = str(current_cfg.get("base_token_env") or phase2_cfg.get("base_token_env") or "").strip()
    table_id_env = str(current_cfg.get("table_id_env") or "").strip()
    view_id_env = str(current_cfg.get("view_id_env") or "").strip() or None
    record_id_env = str(current_cfg.get("record_id_env") or "").strip() or None
    return base_token_env, table_id_env, view_id_env, record_id_env


def _env_value(name: str, *, environ: dict[str, str] | os._Environ[str]) -> str:
    if not name:
        return ""
    return str(environ.get(name, "")).strip()


def collect_dingtalk_control_preflight_errors(
    cfg: dict[str, Any],
    *,
    environ: dict[str, str] | os._Environ[str] | None = None,
) -> list[str]:
    current_environ = os.environ if environ is None else environ
    errors: list[str] = []

    resolved_cli_bin = cli_bin(cfg)
    try:
        command = cli_command_parts(resolved_cli_bin)[0]
    except RuntimeError as exc:
        errors.append(str(exc))
        command = None
    if command and not cli_command_exists(resolved_cli_bin):
        errors.append(f"sync.phase2.cli_bin executable is not available: {command}")

    base_token_env, table_id_env, view_id_env, record_id_env = dingtalk_control_env_names(cfg)
    missing_env_names = [
        env_name
        for env_name in (base_token_env, table_id_env, view_id_env or "", record_id_env or "")
        if env_name and not _env_value(env_name, environ=current_environ)
    ]
    if not base_token_env:
        errors.append("sync.phase2.dingtalk_control.base_token_env is required, or provide sync.phase2.base_token_env")
    if not table_id_env:
        errors.append("sync.phase2.dingtalk_control.table_id_env is required")
    if missing_env_names:
        errors.append("Required environment variables are not set: " + ", ".join(missing_env_names))
    return errors


def resolve_dingtalk_control_binding(
    cfg: dict[str, Any],
    *,
    environ: dict[str, str] | os._Environ[str] | None = None,
) -> DingTalkControlBinding:
    current_environ = os.environ if environ is None else environ
    base_token_env, table_id_env, view_id_env, record_id_env = dingtalk_control_env_names(cfg)
    if not base_token_env:
        raise RuntimeError("sync.phase2.dingtalk_control.base_token_env is required, or provide sync.phase2.base_token_env")
    if not table_id_env:
        raise RuntimeError("sync.phase2.dingtalk_control.table_id_env is required")
    return DingTalkControlBinding(
        base_token_env=base_token_env,
        table_id_env=table_id_env,
        view_id_env=view_id_env,
        record_id_env=record_id_env,
        base_token=_env_value(base_token_env, environ=current_environ),
        table_id=_env_value(table_id_env, environ=current_environ),
        view_id=_env_value(view_id_env, environ=current_environ) if view_id_env else None,
        record_id=_env_value(record_id_env, environ=current_environ) if record_id_env else None,
    )


def _parse_control_record(raw_record: dict[str, Any]) -> DingTalkControlConfig:
    record_id = str(raw_record.get("record_id") or "").strip()
    if not record_id:
        raise RuntimeError("DingTalk control row is missing record_id")
    fields_raw = raw_record.get("fields", {})
    fields = fields_raw if isinstance(fields_raw, dict) else {}
    operator_union_id = scalar_text(fields.get(OPERATOR_UNION_ID_FIELD))
    default_target_node_url = scalar_text(fields.get(DEFAULT_TARGET_NODE_URL_FIELD))
    default_target_node_id = parse_node_id_from_url(default_target_node_url) if default_target_node_url else ""
    return DingTalkControlConfig(
        record_id=record_id,
        operator_union_id=operator_union_id,
        default_target_node_url=default_target_node_url,
        default_target_node_id=default_target_node_id,
    )


def _select_control_record(
    raw_records: list[dict[str, Any]],
    *,
    requested_record_id: str | None,
) -> DingTalkControlConfig:
    requested = str(requested_record_id or "").strip()
    if requested:
        for raw_record in raw_records:
            if str(raw_record.get("record_id") or "").strip() == requested:
                return _parse_control_record(raw_record)
        raise RuntimeError(f"DingTalk control row not found for record_id={requested}")
    if not raw_records:
        raise RuntimeError("DingTalk control config table returned no rows; provide one control row or bind record_id_env")
    if len(raw_records) > 1:
        raise RuntimeError(
            "DingTalk control config is ambiguous: more than one row is visible. "
            "Restrict the bound view to one row or configure sync.phase2.dingtalk_control.record_id_env."
        )
    return _parse_control_record(raw_records[0])


def read_dingtalk_control_config(
    *,
    cfg: dict[str, Any],
    cli_bin_override: str | None = None,
    identity: str | None = None,
    record_id: str | None = None,
    environ: dict[str, str] | os._Environ[str] | None = None,
    source: Any | None = None,
) -> DingTalkControlConfig:
    current_environ = os.environ if environ is None else environ
    binding = resolve_dingtalk_control_binding(cfg, environ=current_environ)
    current_source = source or LarkCliSource(
        cli_bin=cli_bin_override or cli_bin(cfg),
        identity=identity or phase2_identity(),
    )
    raw_records = current_source.fetch_records_with_ids(
        base_token=binding.base_token,
        table_id=binding.table_id,
        view_id=binding.view_id,
    )
    return _select_control_record(
        raw_records,
        requested_record_id=str(record_id or "").strip() or binding.record_id,
    )


def update_dingtalk_control_config(
    *,
    cfg: dict[str, Any],
    operator_union_id: str | None,
    default_target_node_url: str | None,
    record_id: str | None = None,
    dry_run: bool = False,
    cli_bin_override: str | None = None,
    identity: str | None = None,
    environ: dict[str, str] | os._Environ[str] | None = None,
    source: Any | None = None,
) -> DingTalkControlConfig:
    current_environ = os.environ if environ is None else environ
    binding = resolve_dingtalk_control_binding(cfg, environ=current_environ)
    current_source = source or LarkCliSource(
        cli_bin=cli_bin_override or cli_bin(cfg),
        identity=identity or phase2_identity(),
    )
    raw_records = current_source.fetch_records_with_ids(
        base_token=binding.base_token,
        table_id=binding.table_id,
        view_id=binding.view_id,
    )
    current = _select_control_record(
        raw_records,
        requested_record_id=str(record_id or "").strip() or binding.record_id,
    )
    merged_operator_union_id = current.operator_union_id if operator_union_id is None else str(operator_union_id).strip()
    merged_target_node_url = current.default_target_node_url if default_target_node_url is None else str(default_target_node_url).strip()
    merged_target_node_id = parse_node_id_from_url(merged_target_node_url) if merged_target_node_url else ""
    updated = DingTalkControlConfig(
        record_id=current.record_id,
        operator_union_id=merged_operator_union_id,
        default_target_node_url=merged_target_node_url,
        default_target_node_id=merged_target_node_id,
    )
    if dry_run:
        return updated
    current_source.upsert_record(
        base_token=binding.base_token,
        table_id=binding.table_id,
        record_id=current.record_id,
        record={
            OPERATOR_UNION_ID_FIELD: updated.operator_union_id,
            DEFAULT_TARGET_NODE_URL_FIELD: updated.default_target_node_url,
        },
    )
    return updated


def _payload_from_config(config: DingTalkControlConfig, *, mode: str) -> dict[str, Any]:
    payload = {
        "mode": mode,
        "record_id": config.record_id,
        "operator_union_id": config.operator_union_id,
        "default_target_node_url": config.default_target_node_url,
        "default_target_node_id": config.default_target_node_id,
    }
    return payload


def run_dingtalk_control_config(args: Any, *, config_path: Path) -> None:
    cfg = load_config(config_path)
    has_updates = args.operator_union_id is not None or args.target_node_url is not None
    if has_updates:
        config = update_dingtalk_control_config(
            cfg=cfg,
            operator_union_id=args.operator_union_id,
            default_target_node_url=args.target_node_url,
            record_id=args.record_id,
            dry_run=bool(args.dry_run),
        )
        payload = _payload_from_config(config, mode="dry-run-update" if args.dry_run else "update")
    else:
        config = read_dingtalk_control_config(
            cfg=cfg,
            record_id=args.record_id,
        )
        payload = _payload_from_config(config, mode="read")
    if getattr(args, "json", False):
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    for key, value in payload.items():
        print(f"{key}: {value}")
