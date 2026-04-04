#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from tools.build_docs import load_config


def normalize_release_token(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9._-]+", "-", (value or "").strip())
    return token.strip("-")


def _build_languages(cfg: dict[str, Any]) -> list[str]:
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    languages = build_cfg.get("languages", ["en"])
    return [str(item).strip() for item in languages if str(item).strip()] or ["en"]


def release_lang_for_config(config_path: Path, cfg: dict[str, Any] | None = None) -> str:
    loaded_cfg = cfg if cfg is not None else load_config(config_path)
    languages = _build_languages(loaded_cfg)
    return languages[0] if languages else "default"


def release_root_for_target(
    *,
    repo_root: Path,
    config_path: Path,
    model: str,
    region: str,
    cfg: dict[str, Any] | None = None,
) -> Path:
    lang = release_lang_for_config(config_path, cfg)
    return repo_root / "reports" / "releases" / model / region / lang


def release_latest_dir_for_target(
    *,
    repo_root: Path,
    config_path: Path,
    model: str,
    region: str,
    cfg: dict[str, Any] | None = None,
) -> Path:
    return release_root_for_target(
        repo_root=repo_root,
        config_path=config_path,
        model=model,
        region=region,
        cfg=cfg,
    ) / "latest"


def release_version_dir_for_target(
    *,
    repo_root: Path,
    config_path: Path,
    model: str,
    region: str,
    version: str,
    cfg: dict[str, Any] | None = None,
) -> Path:
    version_token = normalize_release_token(version) or "unversioned"
    return release_root_for_target(
        repo_root=repo_root,
        config_path=config_path,
        model=model,
        region=region,
        cfg=cfg,
    ) / "versions" / version_token


def release_manifests_dir_for_target(
    *,
    repo_root: Path,
    config_path: Path,
    model: str,
    region: str,
    cfg: dict[str, Any] | None = None,
) -> Path:
    return release_root_for_target(
        repo_root=repo_root,
        config_path=config_path,
        model=model,
        region=region,
        cfg=cfg,
    ) / "manifests"
