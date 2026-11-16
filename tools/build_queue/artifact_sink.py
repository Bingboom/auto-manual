from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

DEFAULT_ARTIFACT_SINK_PROVIDER = "lark_drive"
DEFAULT_ARTIFACT_SINK_PROVIDER_ENV = "AUTO_MANUAL_ARTIFACT_SINK_PROVIDER"
DEFAULT_ARTIFACT_MIRROR_PROVIDER_ENV = "AUTO_MANUAL_ARTIFACT_MIRROR_PROVIDER"


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
    }
    normalized = aliases.get(text)
    if normalized:
        return normalized
    raise RuntimeError(
        "Unsupported queue artifact sink provider: "
        + text
        + ". Supported providers: lark_drive"
    )


def _normalize_optional_provider(value: str | None) -> str | None:
    text = str(value or "").strip().lower()
    if not text or text in {"none", "off", "disabled", "false", "no"}:
        return None
    return _normalize_provider(text)


def artifact_sink_provider(cfg: dict[str, Any], *, environ: dict[str, str] | os._Environ[str]) -> str:
    current_cfg = artifact_sink_cfg(cfg)
    provider_env = str(current_cfg.get("provider_env") or DEFAULT_ARTIFACT_SINK_PROVIDER_ENV).strip()
    provider_value = str(environ.get(provider_env, "")).strip() if provider_env else ""
    if not provider_value:
        provider_value = str(current_cfg.get("provider") or "").strip()
    return _normalize_provider(provider_value)


def artifact_mirror_provider(cfg: dict[str, Any], *, environ: dict[str, str] | os._Environ[str]) -> str | None:
    current_cfg = artifact_sink_cfg(cfg)
    provider_env = str(current_cfg.get("mirror_provider_env") or DEFAULT_ARTIFACT_MIRROR_PROVIDER_ENV).strip()
    provider_value = str(environ.get(provider_env, "")).strip() if provider_env else ""
    if not provider_value:
        provider_value = str(current_cfg.get("mirror_provider") or "").strip()
    return _normalize_optional_provider(provider_value)


def collect_artifact_sink_preflight_errors(
    cfg: dict[str, Any],
    *,
    environ: dict[str, str] | os._Environ[str],
) -> list[str]:
    try:
        artifact_sink_provider(cfg, environ=environ)
    except RuntimeError as exc:
        return [str(exc)]
    try:
        artifact_mirror_provider(cfg, environ=environ)
    except RuntimeError as exc:
        return [str(exc)]
    return []


def resolve_artifact_destination(
    cfg: dict[str, Any],
    *,
    environ: dict[str, str] | os._Environ[str] | None = None,
    **kwargs: Any,
) -> ArtifactDestination:
    env = os.environ if environ is None else environ
    provider = artifact_sink_provider(cfg, environ=env)
    if provider != DEFAULT_ARTIFACT_SINK_PROVIDER:
        raise RuntimeError(
            f"Unsupported queue artifact sink provider: {provider}. Supported providers: {DEFAULT_ARTIFACT_SINK_PROVIDER}"
        )
    return ArtifactDestination(
        provider=DEFAULT_ARTIFACT_SINK_PROVIDER,
        label="Lark wiki target",
        details=dict(kwargs),
        runtime_target=kwargs.get("target_node_url"),
    )


def publish_artifact(
    cfg: dict[str, Any],
    *,
    environ: dict[str, str] | os._Environ[str] | None = None,
    **kwargs: Any,
) -> ArtifactPublishResult:
    env = os.environ if environ is None else environ
    provider = artifact_sink_provider(cfg, environ=env)
    if provider != DEFAULT_ARTIFACT_SINK_PROVIDER:
        raise RuntimeError(
            f"Unsupported queue artifact sink provider: {provider}. Supported providers: {DEFAULT_ARTIFACT_SINK_PROVIDER}"
        )
    raise NotImplementedError("publish_artifact for lark_drive is managed via lark_ops")
