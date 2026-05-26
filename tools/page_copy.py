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
SYMBOLS_COPY_BLOCK_TYPE = "copy_row"
SYMBOLS_COPY_PAGE_ID = "symbols"
SYMBOLS_COPY_LANG_COLUMNS = (
    ("", "text_en"),
    ("fr", "text_fr"),
    ("es", "text_es"),
    ("pt-BR", "text_pt-BR"),
    ("de", "text_de"),
    ("it", "text_it"),
    ("uk", "text_uk"),
)

_TRUE_VALUES = {"1", "true", "yes", "y", "on"}
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
        return tuple(dict(row) for row in csv.DictReader(handle))


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


def normalize_symbols_copy_key(value: str) -> str:
    raw = (value or "").strip()
    if raw in {"signal_label.tip", "signal_meaning.tip", "alt.signal.tip"}:
        return raw[:-3] + "tips"
    return raw


def is_symbols_copy_row(row: dict[str, str]) -> bool:
    return (row.get("page_id") or "").strip() == SYMBOLS_COPY_PAGE_ID and (
        row.get("block_type") or ""
    ).strip() == SYMBOLS_COPY_BLOCK_TYPE


def symbols_copy_rows_from_blocks(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    page_copy_rows: list[dict[str, str]] = []
    for row in rows:
        if not is_symbols_copy_row(row):
            continue
        copy_key = normalize_symbols_copy_key(row.get("copy_key") or row.get("symbol_key") or "")
        if not copy_key:
            continue
        enabled = row.get("enabled") or "1"
        order = row.get("order") or ""
        for lang, column in SYMBOLS_COPY_LANG_COLUMNS:
            text = row.get(column) or ""
            if not text.strip():
                continue
            page_copy_rows.append(
                {
                    "page_id": SYMBOLS_COPY_PAGE_ID,
                    "lang": lang,
                    "copy_key": copy_key,
                    "text": text,
                    "enabled": enabled,
                    "order": order,
                }
            )
    return page_copy_rows


def symbols_copy_map_from_blocks(
    rows: Iterable[dict[str, str]],
    lang: str,
) -> dict[str, str]:
    candidates = set(page_copy_lang_candidates(lang))
    values: dict[str, str] = {}
    for row in symbols_copy_rows_from_blocks(rows):
        if not _truthy(row.get("enabled") or "1", default=True):
            continue
        row_lang = (row.get("lang") or "").strip()
        if row_lang and row_lang not in candidates:
            continue
        copy_key = (row.get("copy_key") or "").strip()
        if not copy_key:
            continue
        values[copy_key] = row.get("text") or ""
    return values


def merge_symbols_copy_rows(
    existing_page_copy_rows: Iterable[dict[str, str]],
    symbols_rows: Iterable[dict[str, str]],
) -> list[dict[str, str]]:
    derived_symbols_rows = symbols_copy_rows_from_blocks(symbols_rows)
    if not derived_symbols_rows:
        return [
            {column: row.get(column, "") for column in PAGE_COPY_FIELDNAMES}
            for row in existing_page_copy_rows
        ]

    merged: list[dict[str, str]] = []
    inserted_symbols = False
    for row in existing_page_copy_rows:
        if (row.get("page_id") or "").strip() == SYMBOLS_COPY_PAGE_ID:
            if not inserted_symbols:
                merged.extend(derived_symbols_rows)
                inserted_symbols = True
            continue
        merged.append({column: row.get(column, "") for column in PAGE_COPY_FIELDNAMES})
    if not inserted_symbols:
        merged.extend(derived_symbols_rows)
    return merged
