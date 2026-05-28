#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from tools.page_copy import page_copy_lang_candidates
from tools.script_bootstrap import bootstrap_repo_root


ROOT = bootstrap_repo_root(__file__, parent_count=1)
DEFAULT_SYMBOLS_PAGE_COPY_CSV = ROOT / "data" / "phase2" / "symbols_page_copy.csv"
SYMBOLS_PAGE_COPY_FIELDNAMES = ("copy_key", "en", "fr", "es", "de", "it", "uk")


def _symbols_page_copy_csv_path(raw_path: str | None) -> Path:
    raw = (raw_path or "").strip()
    if not raw:
        return DEFAULT_SYMBOLS_PAGE_COPY_CSV
    path = Path(raw)
    return path if path.is_absolute() else ROOT / path


@lru_cache(maxsize=16)
def _read_symbols_page_copy_rows(path_text: str) -> tuple[dict[str, str], ...]:
    path = Path(path_text)
    if not path.exists():
        raise FileNotFoundError(f"Missing symbols page copy CSV: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = tuple(dict(row) for row in csv.DictReader(handle))
    for index, row in enumerate(rows, start=2):
        copy_key = (row.get("copy_key") or "").strip()
        if not copy_key:
            raise ValueError(f"symbols_page_copy row {index} is missing copy_key")
    return rows


def _lang_columns(lang: str) -> tuple[str, ...]:
    candidates = list(page_copy_lang_candidates(lang))
    if not candidates:
        candidates.append("en")
    candidates.extend(["en"])
    return tuple(dict.fromkeys(candidates))


def load_symbols_page_copy_map(
    lang: str,
    *,
    csv_path: str | None = None,
) -> dict[str, str]:
    path = _symbols_page_copy_csv_path(csv_path)
    lang_columns = _lang_columns(lang)
    copy: dict[str, str] = {}
    for row in _read_symbols_page_copy_rows(str(path)):
        copy_key = (row.get("copy_key") or "").strip()
        if not copy_key:
            continue
        for column in lang_columns:
            value = row.get(column)
            if value and value.strip():
                copy[copy_key] = value
                break
    return copy


def require_symbols_page_copy(
    lang: str,
    required_keys: Iterable[str],
    *,
    csv_path: str | None = None,
) -> dict[str, str]:
    copy = load_symbols_page_copy_map(lang, csv_path=csv_path)
    missing = [key for key in required_keys if key not in copy or not copy[key].strip()]
    if missing:
        raise ValueError(
            f"symbols_page_copy missing required key(s) for lang={lang!r}: "
            + ", ".join(missing)
        )
    return copy
