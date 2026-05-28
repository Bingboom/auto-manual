#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from tools.script_bootstrap import bootstrap_repo_root


ROOT = bootstrap_repo_root(__file__, parent_count=1)
DEFAULT_PAGE_COPY_CSV = ROOT / "data" / "phase2" / "page_copy.csv"
PAGE_COPY_FIELDNAMES = ("page_id", "lang", "copy_key", "text", "enabled", "order")

_TRUE_VALUES = {"1", "true", "yes", "y", "on"}
_FORBIDDEN_COPY_KEYS = {"tip"}
_LANG_ALIASES = {
    "jp": "ja",
    "pt_br": "pt-BR",
    "pt-br": "pt-BR",
    "br": "pt-BR",
    "ukr": "uk",
}


def normalize_page_copy_lang(lang: str | None) -> str:
    raw = (lang or "").strip()
    if not raw:
        return ""
    folded = raw.casefold()
    return _LANG_ALIASES.get(folded, raw)


def page_copy_lang_candidates(lang: str | None) -> tuple[str, ...]:
    normalized = normalize_page_copy_lang(lang)
    if not normalized:
        return ()
    candidates = [
        normalized,
        normalized.casefold(),
        normalized.replace("-", "_"),
        normalized.casefold().replace("-", "_"),
    ]
    if normalized == "pt-BR":
        candidates.extend(["br", "pt-BR", "pt-br", "pt_BR", "pt_br"])
    if normalized == "ja":
        candidates.append("jp")
    if normalized == "uk":
        candidates.append("ukr")
    return tuple(dict.fromkeys(candidate for candidate in candidates if candidate))


def _truthy(value: str, *, default: bool = True) -> bool:
    raw = (value or "").strip().casefold()
    if not raw:
        return default
    return raw in _TRUE_VALUES


def _page_copy_csv_path(raw_path: str | None) -> Path:
    raw = (raw_path or "").strip()
    if not raw:
        return DEFAULT_PAGE_COPY_CSV
    path = Path(raw)
    return path if path.is_absolute() else ROOT / path


@lru_cache(maxsize=16)
def _read_page_copy_rows(path_text: str) -> tuple[dict[str, str], ...]:
    path = Path(path_text)
    if not path.exists():
        raise FileNotFoundError(f"Missing page copy CSV: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = tuple(dict(row) for row in csv.DictReader(handle))
    for index, row in enumerate(rows, start=2):
        copy_key = (row.get("copy_key") or "").strip().casefold()
        if copy_key in _FORBIDDEN_COPY_KEYS:
            raise ValueError(
                f"page_copy row {index} uses forbidden copy_key={copy_key!r}; "
                "use copy_key='tips'"
            )
    return rows


def load_page_copy_map(
    page_id: str,
    lang: str,
    *,
    csv_path: str | None = None,
) -> dict[str, str]:
    path = _page_copy_csv_path(csv_path)
    lang_candidates = set(page_copy_lang_candidates(lang))
    copy: dict[str, str] = {}
    for row in _read_page_copy_rows(str(path)):
        if (row.get("page_id") or "").strip() != page_id:
            continue
        if not _truthy(row.get("enabled") or "1", default=True):
            continue
        row_lang = (row.get("lang") or "").strip()
        if row_lang and row_lang not in lang_candidates:
            continue
        copy_key = (row.get("copy_key") or "").strip()
        if not copy_key:
            continue
        text = row.get("text") or ""
        copy[copy_key] = text
    return copy


def require_page_copy(
    page_id: str,
    lang: str,
    required_keys: Iterable[str],
    *,
    csv_path: str | None = None,
) -> dict[str, str]:
    copy = load_page_copy_map(page_id, lang, csv_path=csv_path)
    missing = [key for key in required_keys if key not in copy or not copy[key].strip()]
    if missing:
        raise ValueError(
            f"page_copy missing required key(s) for page_id={page_id!r}, "
            f"lang={lang!r}: {', '.join(missing)}"
        )
    return copy


def load_all_copy_values(*, csv_path: str | None = None) -> tuple[dict[str, str], ...]:
    path = _page_copy_csv_path(csv_path)
    return _read_page_copy_rows(str(path))
