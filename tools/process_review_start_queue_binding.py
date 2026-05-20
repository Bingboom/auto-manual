from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping


@dataclass(frozen=True)
class ReviewInitBinding:
    base_token_env: str
    table_id_env: str
    view_id_env: str | None
    base_token: str
    table_id: str
    view_id: str | None


def review_init_cfg(cfg: dict[str, Any], *, sync_phase2_cfg: Callable[[dict[str, Any]], dict[str, Any]]) -> dict[str, Any]:
    phase2_cfg = sync_phase2_cfg(cfg)
    raw = phase2_cfg.get("review_init", {})
    return raw if isinstance(raw, dict) else {}


def document_link_cfg(
    cfg: dict[str, Any],
    *,
    sync_phase2_cfg: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    phase2_cfg = sync_phase2_cfg(cfg)
    raw = phase2_cfg.get("document_link", {})
    return raw if isinstance(raw, dict) else {}


def review_init_env_names(
    cfg: dict[str, Any],
    *,
    sync_phase2_cfg: Callable[[dict[str, Any]], dict[str, Any]],
) -> tuple[str, str, str | None]:
    phase2_cfg = sync_phase2_cfg(cfg)
    review_cfg = review_init_cfg(cfg, sync_phase2_cfg=sync_phase2_cfg)
    doc_link_cfg = document_link_cfg(cfg, sync_phase2_cfg=sync_phase2_cfg)
    base_token_env = str(review_cfg.get("base_token_env") or phase2_cfg.get("base_token_env") or "").strip()
    document_link_table_id_env = str(doc_link_cfg.get("table_id_env") or "").strip()
    document_link_view_id_env = str(doc_link_cfg.get("view_id_env") or "").strip() or None
    review_table_id_env = str(review_cfg.get("table_id_env") or "").strip()
    review_view_id_env = str(review_cfg.get("view_id_env") or "").strip() or None
    if review_table_id_env:
        table_id_env = review_table_id_env
        view_id_env = review_view_id_env
        if view_id_env == document_link_view_id_env:
            view_id_env = None
    else:
        table_id_env = document_link_table_id_env
        view_id_env = document_link_view_id_env
    return base_token_env, table_id_env, view_id_env


def collect_review_start_preflight_errors(
    cfg: dict[str, Any],
    *,
    require_github: bool,
    provider_name: Callable[[dict[str, Any]], str],
    cli_bin: Callable[[dict[str, Any]], str],
    cli_command_parts: Callable[[str], list[str]],
    cli_command_exists: Callable[[str], bool],
    review_init_env_names: Callable[[dict[str, Any]], tuple[str, str, str | None]],
    environ: Mapping[str, str],
) -> list[str]:
    errors: list[str] = []
    provider_name(cfg)

    resolved_cli_bin = cli_bin(cfg)
    try:
        command = cli_command_parts(resolved_cli_bin)[0]
    except RuntimeError as exc:
        errors.append(str(exc))
        command = None
    if command and not cli_command_exists(resolved_cli_bin):
        errors.append(f"sync.phase2.cli_bin executable is not available: {command}")

    base_token_env, table_id_env, view_id_env = review_init_env_names(cfg)
    missing_env_names = [
        env_name
        for env_name in (base_token_env, table_id_env, view_id_env or "")
        if env_name and not str(environ.get(env_name, "")).strip()
    ]
    if not base_token_env:
        errors.append("sync.phase2.base_token_env is required")
    if not table_id_env:
        errors.append("sync.phase2.document_link.table_id_env is required because review-init reuses the Document_link binding")
    if missing_env_names:
        errors.append("Required environment variables are not set: " + ", ".join(missing_env_names))

    if require_github:
        for env_name in ("GITHUB_REPOSITORY", "GITHUB_TOKEN"):
            if not str(environ.get(env_name, "")).strip():
                errors.append(f"Required environment variable is not set: {env_name}")
    return errors


def resolve_review_init_binding(
    cfg: dict[str, Any],
    *,
    review_init_env_names: Callable[[dict[str, Any]], tuple[str, str, str | None]],
    env_value: Callable[[str], str],
) -> ReviewInitBinding:
    base_token_env, table_id_env, view_id_env = review_init_env_names(cfg)
    if not base_token_env:
        raise RuntimeError("sync.phase2.base_token_env is required")
    if not table_id_env:
        raise RuntimeError("sync.phase2.document_link.table_id_env is required because review-init reuses the Document_link binding")
    return ReviewInitBinding(
        base_token_env=base_token_env,
        table_id_env=table_id_env,
        view_id_env=view_id_env,
        base_token=env_value(base_token_env),
        table_id=env_value(table_id_env),
        view_id=env_value(view_id_env) if view_id_env else None,
    )
