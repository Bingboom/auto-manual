#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Iterable

from tools.script_bootstrap import bootstrap_repo_root
from tools.wide_copy import load_wide_copy_map, require_wide_copy, resolve_wide_copy_csv_path


ROOT = bootstrap_repo_root(__file__, parent_count=1)
DEFAULT_SIGNAL_WORDS_CSV = ROOT / "data" / "phase2" / "signal_words.csv"
SIGNAL_WORDS_FIELDNAMES = ("copy_key", "en", "fr", "es", "pt-BR", "ja", "zh", "de", "it", "uk")


def load_signal_words_map(
    lang: str | None,
    *,
    csv_path: str | None = None,
) -> dict[str, str]:
    path = resolve_wide_copy_csv_path(ROOT, DEFAULT_SIGNAL_WORDS_CSV, csv_path)
    return load_wide_copy_map(
        lang,
        csv_path=str(path),
        table_name="signal_words",
        fieldnames=SIGNAL_WORDS_FIELDNAMES,
    )


def require_signal_words(
    lang: str | None,
    required_keys: Iterable[str],
    *,
    csv_path: str | None = None,
) -> dict[str, str]:
    path = resolve_wide_copy_csv_path(ROOT, DEFAULT_SIGNAL_WORDS_CSV, csv_path)
    return require_wide_copy(
        lang,
        required_keys,
        csv_path=str(path),
        table_name="signal_words",
        fieldnames=SIGNAL_WORDS_FIELDNAMES,
    )


def get_signal_word(lang: str | None, key: str, *, csv_path: str | None = None) -> str:
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise ValueError("unsupported signal word key: ?")
    copy = require_signal_words(lang or "", [normalized_key], csv_path=csv_path)
    return copy[normalized_key]


def get_safety_warning_label(lang: str | None) -> str:
    return get_signal_word(lang, "safety_warning")


def get_symbols_notice_label(lang: str | None) -> str:
    return get_signal_word(lang, "symbols_notice")
