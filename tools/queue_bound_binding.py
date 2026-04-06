from __future__ import annotations

import os
from typing import Any

from tools.document_link_queue import (
    collect_queue_preflight_errors as _collect_queue_preflight_errors_impl,
    document_link_cfg as _document_link_cfg_impl,
    document_link_env_names as _document_link_env_names_impl,
    document_link_wiki_parent_token_env as _document_link_wiki_parent_token_env_impl,
    resolve_document_link_binding as _resolve_document_link_binding_impl,
)
from tools.phase2_support import (
    cli_bin as _cli_bin,
    cli_command_exists as _cli_command_exists,
    cli_command_parts as _cli_command_parts,
    env_value as _env_value,
    provider_name as _provider_name,
    sync_phase2_cfg as _sync_phase2_cfg,
)
from tools.queue_contract import DocumentLinkBinding


def document_link_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    return _document_link_cfg_impl(cfg, sync_phase2_cfg=_sync_phase2_cfg)


def document_link_env_names(cfg: dict[str, Any]) -> tuple[str, str, str | None]:
    return _document_link_env_names_impl(cfg, sync_phase2_cfg=_sync_phase2_cfg)


def document_link_wiki_parent_token_env(cfg: dict[str, Any]) -> str | None:
    return _document_link_wiki_parent_token_env_impl(cfg, sync_phase2_cfg=_sync_phase2_cfg)


def collect_queue_preflight_errors(cfg: dict[str, Any]) -> list[str]:
    return _collect_queue_preflight_errors_impl(
        cfg,
        provider_name=_provider_name,
        cli_bin=_cli_bin,
        cli_command_parts=_cli_command_parts,
        cli_command_exists=_cli_command_exists,
        sync_phase2_cfg=_sync_phase2_cfg,
        environ=os.environ,
    )


def resolve_document_link_binding(cfg: dict[str, Any]) -> DocumentLinkBinding:
    return _resolve_document_link_binding_impl(
        cfg,
        sync_phase2_cfg=_sync_phase2_cfg,
        binding_factory=DocumentLinkBinding,
        env_value=_env_value,
        environ=os.environ,
    )
