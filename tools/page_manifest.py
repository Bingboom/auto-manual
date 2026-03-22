#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.config_pages import ConfigPage, PageParseIssue, parse_config_pages, parse_config_pages_or_raise


@dataclass(frozen=True)
class ResolvedPageSource:
    pages: list[ConfigPage]
    issues: list[PageParseIssue]
    manifest_path: Path | None
    manifest_id: str | None


def _format_manifest_path(
    raw_value: str,
    *,
    model: str | None,
    region: str | None,
) -> str:
    if "{sku}" in raw_value:
        raise RuntimeError("paths.page_manifest uses unsupported '{sku}' token; use '{model}' and/or '{region}'")
    if "{model}" in raw_value and not (model or "").strip():
        raise RuntimeError("paths.page_manifest uses '{model}' but no model was provided")
    if "{region}" in raw_value and not (region or "").strip():
        raise RuntimeError("paths.page_manifest uses '{region}' but no region was provided")
    return raw_value.format(model=model or "", region=region or "")


def resolve_page_manifest_path(
    cfg: dict,
    *,
    root: Path,
    model: str | None = None,
    region: str | None = None,
) -> Path | None:
    paths_cfg_raw = cfg.get("paths", {})
    paths_cfg = paths_cfg_raw if isinstance(paths_cfg_raw, dict) else {}
    raw = paths_cfg.get("page_manifest")
    if not isinstance(raw, str) or not raw.strip():
        return None

    rendered = _format_manifest_path(raw.strip(), model=model, region=region)
    path = Path(rendered)
    return path if path.is_absolute() else (root / path)


def _load_yaml(path: Path) -> Any:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PyYAML not installed. Please run: pip install pyyaml") from exc

    if not path.exists():
        raise RuntimeError(f"Page manifest not found: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _load_page_manifest_data(path: Path) -> tuple[Any, str | None]:
    data = _load_yaml(path)
    if isinstance(data, list):
        return data, None
    if not isinstance(data, dict):
        raise RuntimeError(f"Page manifest root must be a mapping or list: {path}")

    pages = data.get("pages")
    if not isinstance(pages, list) or not pages:
        raise RuntimeError(f"Page manifest pages must be a non-empty list: {path}")
    manifest_id_raw = data.get("manifest_id")
    manifest_id = str(manifest_id_raw).strip() if isinstance(manifest_id_raw, str) and manifest_id_raw.strip() else None
    return pages, manifest_id


def resolve_config_pages(
    cfg: dict,
    *,
    default_languages: list[str] | None = None,
    root: Path,
    model: str | None = None,
    region: str | None = None,
) -> ResolvedPageSource:
    manifest_path = resolve_page_manifest_path(cfg, root=root, model=model, region=region)
    manifest_id: str | None = None
    if manifest_path is None:
        pages_raw = cfg.get("pages")
    else:
        pages_raw, manifest_id = _load_page_manifest_data(manifest_path)

    pages, issues = parse_config_pages(
        pages_raw,
        default_languages=default_languages,
    )
    return ResolvedPageSource(
        pages=pages,
        issues=issues,
        manifest_path=manifest_path,
        manifest_id=manifest_id,
    )


def resolve_config_pages_or_raise(
    cfg: dict,
    *,
    default_languages: list[str] | None = None,
    root: Path,
    model: str | None = None,
    region: str | None = None,
    error_prefix: str | None = None,
) -> ResolvedPageSource:
    manifest_path = resolve_page_manifest_path(cfg, root=root, model=model, region=region)
    manifest_id: str | None = None
    if manifest_path is None:
        pages = parse_config_pages_or_raise(
            cfg.get("pages"),
            default_languages=default_languages,
            error_prefix=error_prefix,
        )
    else:
        pages_raw, manifest_id = _load_page_manifest_data(manifest_path)
        pages = parse_config_pages_or_raise(
            pages_raw,
            default_languages=default_languages,
            error_prefix=error_prefix,
        )

    return ResolvedPageSource(
        pages=pages,
        issues=[],
        manifest_path=manifest_path,
        manifest_id=manifest_id,
    )
