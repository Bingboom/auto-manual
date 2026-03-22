#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Iterable

from pathlib import Path

from tools.config_pages import CoverPdfPage, CsvPage, GeneratedPage, PdfInsertPage, RstIncludePage, parse_config_pages
from tools.page_manifest import resolve_config_pages


def format_tokenized(
    text: str,
    sku: str | None,
    model: str | None,
    region: str | None = None,
) -> str:
    if "{sku}" in text:
        raise RuntimeError("config uses unsupported '{sku}' token; use '{model}' and/or '{region}'")
    if "{model}" in text and not model:
        raise RuntimeError("config uses '{model}' but no --model was provided")
    if "{region}" in text and not region:
        raise RuntimeError("config uses '{region}' but no --region was provided")
    return text.format(sku=sku or "", model=model or "", region=region or "")


def config_uses_token_in_pages(
    cfg: dict[str, Any],
    token: str,
    *,
    include_rst_include: bool = False,
) -> bool:
    placeholder = f"{{{token}}}"
    build_cfg = cfg.get("build", {})
    langs = build_cfg.get("languages", []) if isinstance(build_cfg, dict) else []
    try:
        resolved_pages = resolve_config_pages(
            cfg,
            default_languages=langs if isinstance(langs, list) else [],
            root=Path(__file__).resolve().parents[2],
        )
        pages = resolved_pages.pages
    except RuntimeError:
        pages, _issues = parse_config_pages(
            cfg.get("pages"),
            default_languages=langs if isinstance(langs, list) else [],
        )

    for page in pages:
        if isinstance(page, CoverPdfPage):
            if placeholder in page.file:
                return True
        elif isinstance(page, CsvPage):
            if page.include_dir and placeholder in page.include_dir:
                return True
        elif isinstance(page, GeneratedPage):
            if placeholder in page.recipe or placeholder in page.template:
                return True
            if page.include_dir and placeholder in page.include_dir:
                return True
        elif isinstance(page, PdfInsertPage):
            if any(placeholder in value for value in page.file_map.values()):
                return True
        elif include_rst_include and isinstance(page, RstIncludePage):
            if placeholder in page.file:
                return True
    return False


def config_uses_token(
    cfg: dict[str, Any],
    token: str,
    *,
    include_rst_include: bool = False,
    paths_keys: Iterable[str] = (),
    build_keys: Iterable[str] = (),
) -> bool:
    placeholder = f"{{{token}}}"
    if config_uses_token_in_pages(cfg, token, include_rst_include=include_rst_include):
        return True

    paths_cfg = cfg.get("paths", {})
    if isinstance(paths_cfg, dict):
        for key in paths_keys:
            value = paths_cfg.get(key)
            if isinstance(value, str) and placeholder in value:
                return True

    build_cfg = cfg.get("build", {})
    if isinstance(build_cfg, dict):
        for key in build_keys:
            value = build_cfg.get(key)
            if isinstance(value, str) and placeholder in value:
                return True

    return False


def resolve_build_model(cfg: dict[str, Any], arg_model: str | None) -> str | None:
    if arg_model and arg_model.strip():
        return arg_model.strip()
    build_cfg = cfg.get("build", {})
    if not isinstance(build_cfg, dict):
        return None
    default_model = build_cfg.get("default_model")
    if isinstance(default_model, str) and default_model.strip():
        return default_model.strip()
    return None


def resolve_build_region(cfg: dict[str, Any], arg_region: str | None) -> str | None:
    if arg_region and arg_region.strip():
        return arg_region.strip()
    build_cfg = cfg.get("build", {})
    if not isinstance(build_cfg, dict):
        return None
    default_region = build_cfg.get("default_region")
    if isinstance(default_region, str) and default_region.strip():
        return default_region.strip()
    return None


def resolve_build_languages(cfg: dict[str, Any]) -> list[str]:
    build_cfg = cfg.get("build", {})
    if not isinstance(build_cfg, dict):
        return []
    raw = build_cfg.get("languages", [])
    if not isinstance(raw, list):
        return []
    return [str(item).strip() for item in raw if str(item).strip()]


def include_lang_in_output_path(cfg: dict[str, Any]) -> bool:
    build_cfg = cfg.get("build", {})
    if not isinstance(build_cfg, dict):
        return False
    return bool(build_cfg.get("include_lang_in_output_path", False))


def resolve_output_lang(cfg: dict[str, Any]) -> str | None:
    if not include_lang_in_output_path(cfg):
        return None
    langs = resolve_build_languages(cfg)
    if not langs:
        return None
    return langs[0]
