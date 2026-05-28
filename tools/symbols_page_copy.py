#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Iterable

from tools.script_bootstrap import bootstrap_repo_root
from tools.wide_copy import load_wide_copy_map, require_wide_copy, resolve_wide_copy_csv_path


ROOT = bootstrap_repo_root(__file__, parent_count=1)
DEFAULT_SYMBOLS_PAGE_COPY_CSV = ROOT / "data" / "phase2" / "symbols_page_copy.csv"
SYMBOLS_PAGE_COPY_FIELDNAMES = ("copy_key", "en", "fr", "es", "de", "it", "uk")


def load_symbols_page_copy_map(
    lang: str,
    *,
    csv_path: str | None = None,
) -> dict[str, str]:
    path = resolve_wide_copy_csv_path(ROOT, DEFAULT_SYMBOLS_PAGE_COPY_CSV, csv_path)
    return load_wide_copy_map(
        lang,
        csv_path=str(path),
        table_name="symbols_page_copy",
        fieldnames=SYMBOLS_PAGE_COPY_FIELDNAMES,
    )


def require_symbols_page_copy(
    lang: str,
    required_keys: Iterable[str],
    *,
    csv_path: str | None = None,
) -> dict[str, str]:
    path = resolve_wide_copy_csv_path(ROOT, DEFAULT_SYMBOLS_PAGE_COPY_CSV, csv_path)
    return require_wide_copy(
        lang,
        required_keys,
        csv_path=str(path),
        table_name="symbols_page_copy",
        fieldnames=SYMBOLS_PAGE_COPY_FIELDNAMES,
    )
