#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from tools.page_copy import require_page_copy

SIGNAL_WORDS_PAGE_ID = "signal_words"


def get_signal_word(lang: str | None, key: str) -> str:
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise ValueError("unsupported signal word key: ?")
    copy = require_page_copy(SIGNAL_WORDS_PAGE_ID, lang or "", [normalized_key])
    return copy[normalized_key]


def get_safety_warning_label(lang: str | None) -> str:
    return get_signal_word(lang, "safety_warning")


def get_symbols_notice_label(lang: str | None) -> str:
    return get_signal_word(lang, "symbols_notice")
