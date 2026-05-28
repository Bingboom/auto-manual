#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from tools.page_copy import page_copy_lang_candidates


def resolve_wide_copy_csv_path(root: Path, default_path: Path, raw_path: str | None) -> Path:
    raw = (raw_path or "").strip()
    if not raw:
        return default_path
    path = Path(raw)
    return path if path.is_absolute() else root / path


@lru_cache(maxsize=32)
def read_wide_copy_rows(
    path_text: str,
    table_name: str,
    fieldnames: tuple[str, ...],
) -> tuple[dict[str, str], ...]:
    path = Path(path_text)
    if not path.exists():
        raise FileNotFoundError(f"Missing {table_name} CSV: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        actual_fieldnames = tuple(reader.fieldnames or ())
        missing_fields = [field for field in fieldnames if field not in actual_fieldnames]
        if missing_fields:
            raise ValueError(f"{table_name} CSV missing required field(s): {', '.join(missing_fields)}")
        rows = tuple(dict(row) for row in reader)
    for index, row in enumerate(rows, start=2):
        copy_key = (row.get("copy_key") or "").strip()
        if not copy_key:
            raise ValueError(f"{table_name} row {index} is missing copy_key")
    return rows


def wide_copy_lang_columns(lang: str | None, fieldnames: Iterable[str]) -> tuple[str, ...]:
    available = set(fieldnames)
    candidates = list(page_copy_lang_candidates(lang))
    candidates.extend(["en"])
    return tuple(dict.fromkeys(candidate for candidate in candidates if candidate in available))


def load_wide_copy_map(
    lang: str | None,
    *,
    csv_path: str | None,
    table_name: str,
    fieldnames: tuple[str, ...],
) -> dict[str, str]:
    lang_columns = wide_copy_lang_columns(lang, fieldnames[1:])
    copy: dict[str, str] = {}
    for row in read_wide_copy_rows(str(csv_path), table_name, fieldnames):
        copy_key = (row.get("copy_key") or "").strip()
        if not copy_key:
            continue
        for column in lang_columns:
            value = row.get(column)
            if value and value.strip():
                copy[copy_key] = value
                break
    return copy


def require_wide_copy(
    lang: str | None,
    required_keys: Iterable[str],
    *,
    csv_path: str | None,
    table_name: str,
    fieldnames: tuple[str, ...],
) -> dict[str, str]:
    copy = load_wide_copy_map(
        lang,
        csv_path=csv_path,
        table_name=table_name,
        fieldnames=fieldnames,
    )
    missing = [key for key in required_keys if key not in copy or not copy[key].strip()]
    if missing:
        raise ValueError(
            f"{table_name} missing required key(s) for lang={lang!r}: "
            + ", ".join(missing)
        )
    return copy
