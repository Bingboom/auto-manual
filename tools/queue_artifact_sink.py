from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from tools.dingtalk.workspace import parse_node_id_from_url

DEFAULT_ARTIFACT_SINK_PROVIDER = "lark_drive"
DEFAULT_ARTIFACT_SINK_PROVIDER_ENV = "AUTO_MANUAL_ARTIFACT_SINK_PROVIDER"
DEFAULT_DINGTALK_TARGET_NODE_URL_ENV = "DINGTALK_DOCS_TARGET_NODE_URL"
DEFAULT_DINGTALK_A_TOKEN_ENV = "DINGTALK_DOCS_A_TOKEN"
DEFAULT_DINGTALK_XSRF_TOKEN_ENV = "DINGTALK_DOCS_XSRF_TOKEN"
DEFAULT_DINGTALK_COOKIE_ENV = "DINGTALK_DOCS_COOKIE"
DEFAULT_DINGTALK_BX_VERSION_ENV = "DINGTALK_DOCS_BX_V"


@dataclass(frozen=True)
class ArtifactDestination:
    provider: str
    label: str
    details: dict[str, Any]
    runtime_target: Any | None = None


@dataclass(frozen=True)
class ArtifactPublishResult:
    provider: str
    reference_id: str
    latest_link_url: str
    document_link_url: str
    document_link_dd_url: str = ""
    status_notes: tuple[str, ...] = ()


class ArtifactPublishError(RuntimeError):
    def __init__(self, message: str, *, latest_link_url: str | None = None) -> None:
        super().__init__(message)
        self.latest_link_url = (latest_link_url or "").strip() or None


def artifact_sink_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    raw = cfg.get("queue", {})
    if not isinstance(raw, dict):
        return {}
    sink = raw.get("artifact_sink", {})
    return sink if isinstance(sink, dict) else {}


def _normalize_provider(value: str | None) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return DEFAULT_ARTIFACT_SINK_PROVIDER
    aliases = {
        "lark": "lark_drive",
        "feishu": "lark_drive",
        "lark_drive": "lark_drive",
        "lark-drive": "lark_drive",
        "dingtalk": "dingtalk_alidocs_session",
        "dingtalk_alidocs_session": "dingtalk_alidocs_session",
        "dingtalk-alidocs-session": "dingtalk_alidocs_session",
        "alidocs": "dingtalk_alidocs_session",
        "alidocs_session": "dingtalk_alidocs_session",
    }
    normalized = aliases.get(text)
    if normalized:
        return normalized
    raise RuntimeError(
        "Unsupported queue artifact sink provider: "
        + text
        + ". Supported providers: lark_drive, dingtalk_alidocs_session"
    )


def artifact_sink_provider(cfg: dict[str, Any], *, environ: dict[str, str] | os._Environ[str]) -> str:
    current_cfg = artifact_sink_cfg(cfg)
    provider_env = str(current_cfg.get("provider_env") or DEFAULT_ARTIFACT_SINK_PROVIDER_ENV).strip()
    provider_value = str(environ.get(provider_env, "")).strip() if provider_env else ""
    if not provider_value:
        provider_value = str(current_cfg.get("provider") or "").strip()
    return _normalize_provider(provider_value)


def dingtalk_alidocs_env_names(cfg: dict[str, Any]) -> dict[str, str]:
    current_cfg = artifact_sink_cfg(cfg)
    dingtalk_cfg = current_cfg.get("dingtalk_alidocs_session", {})
    if not isinstance(dingtalk_cfg, dict):
        dingtalk_cfg = {}
    return {
        "target_node_url_env": str(dingtalk_cfg.get("target_node_url_env") or DEFAULT_DINGTALK_TARGET_NODE_URL_ENV).strip(),
        "a_token_env": str(dingtalk_cfg.get("a_token_env") or DEFAULT_DINGTALK_A_TOKEN_ENV).strip(),
        "xsrf_token_env": str(dingtalk_cfg.get("xsrf_token_env") or DEFAULT_DINGTALK_XSRF_TOKEN_ENV).strip(),
        "cookie_env": str(dingtalk_cfg.get("cookie_env") or DEFAULT_DINGTALK_COOKIE_ENV).strip(),
        "bx_version_env": str(dingtalk_cfg.get("bx_version_env") or DEFAULT_DINGTALK_BX_VERSION_ENV).strip(),
    }


def resolve_dingtalk_target_node_url(
    cfg: dict[str, Any],
    *,
    environ: dict[str, str] | os._Environ[str],
) -> str:
    env_names = dingtalk_alidocs_env_names(cfg)
    env_name = env_names["target_node_url_env"]
    if not env_name:
        raise RuntimeError("queue.artifact_sink.dingtalk_alidocs_session.target_node_url_env is required")
    value = str(environ.get(env_name, "")).strip()
    if not value:
        raise RuntimeError(f"Required environment variable is not set: {env_name}")
    return value


def collect_artifact_sink_preflight_errors(
    cfg: dict[str, Any],
    *,
    environ: dict[str, str] | os._Environ[str],
) -> list[str]:
    try:
        provider = artifact_sink_provider(cfg, environ=environ)
    except RuntimeError as exc:
        return [str(exc)]
    if provider != "dingtalk_alidocs_session":
        return []
    env_names = dingtalk_alidocs_env_names(cfg)
    missing_env_names = [
        env_name
        for key, env_name in env_names.items()
        if key != "bx_version_env" and env_name and not str(environ.get(env_name, "")).strip()
    ]
    errors: list[str] = []
    if not env_names["target_node_url_env"]:
        errors.append("queue.artifact_sink.dingtalk_alidocs_session.target_node_url_env is required")
    if missing_env_names:
        errors.append("Required environment variables are not set: " + ", ".join(missing_env_names))
    return errors


def resolve_dingtalk_artifact_destination(
    cfg: dict[str, Any],
    *,
    environ: dict[str, str] | os._Environ[str],
) -> ArtifactDestination:
    target_node_url = resolve_dingtalk_target_node_url(cfg, environ=environ)
    target_node_id = parse_node_id_from_url(target_node_url)
    return ArtifactDestination(
        provider="dingtalk_alidocs_session",
        label="DingTalk docs target",
        details={
            "target_node_url": target_node_url,
            "target_node_id": target_node_id,
        },
        runtime_target=target_node_url,
    )
