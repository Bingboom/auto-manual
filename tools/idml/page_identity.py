"""Stable page language and ID helpers shared by IDML orchestration."""
from __future__ import annotations

import re
from pathlib import Path

from .loaders import normalize_lang


def page_language(page: Path, fallback: str) -> str:
    try:
        text = page.read_text(encoding="utf-8")
    except OSError:
        text = ""
    match = re.search(r"\\HBApplyLang\{([^}]+)\}", text)
    if match:
        return normalize_lang(match.group(1))
    suffix = page.stem.rsplit("_", 1)[-1]
    return normalize_lang(suffix if len(suffix) <= 5 else fallback)


def stem_has(page: Path, suffix: str) -> bool:
    return page.stem == suffix or page.stem.endswith("_" + suffix)


def slug(stem: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", stem.lower()).strip("_")
