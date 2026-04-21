#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

_SIGNAL_WORDS: dict[str, dict[str, str]] = {
    "en": {
        "safety_warning": "WARNING",
        "symbols_notice": "DANGER",
        "warning": "WARNING",
        "danger": "DANGER",
        "caution": "CAUTION",
        "note": "NOTE",
        "tips": "TIP",
    },
    "de": {
        "safety_warning": "WARNUNG",
        "symbols_notice": "WARNUNG",
        "warning": "WARNUNG",
        "danger": "GEFAHR",
        "caution": "VORSICHT",
        "note": "HINWEIS",
        "tips": "TIPP",
    },
    "fr": {
        "safety_warning": "AVERTISSEMENT",
        "symbols_notice": "AVERTISSEMENT",
        "warning": "AVERTISSEMENT",
        "danger": "ATTENTION",
        "caution": "ATTENTION",
        "note": "REMARQUE",
        "tips": "CONSEILS",
    },
    "es": {
        "safety_warning": "ADVERTENCIA",
        "symbols_notice": "ADVERTENCIA",
        "warning": "ADVERTENCIA",
        "danger": "PELIGRO",
        "caution": "PRECAUCIÓN",
        "note": "NOTA",
        "tips": "CONSEJOS",
    },
    "it": {
        "safety_warning": "AVVERTENZA",
        "symbols_notice": "AVVERTENZA",
        "warning": "AVVERTENZA",
        "danger": "PERICOLO",
        "caution": "ATTENZIONE",
        "note": "NOTA",
        "tips": "SUGGERIMENTO",
    },
    "uk": {
        "safety_warning": "ПОПЕРЕДЖЕННЯ",
        "symbols_notice": "ПОПЕРЕДЖЕННЯ",
        "warning": "ПОПЕРЕДЖЕННЯ",
        "danger": "НЕБЕЗПЕКА",
        "caution": "УВАГА",
        "note": "ПРИМІТКА",
        "tips": "ПОРАДА",
    },
}


def _resolve_lang(lang: str | None) -> str:
    normalized = (lang or "").strip().lower()
    if normalized in _SIGNAL_WORDS:
        return normalized
    return "en"


def get_signal_word(lang: str | None, key: str) -> str:
    resolved_lang = _resolve_lang(lang)
    labels = _SIGNAL_WORDS[resolved_lang]
    if key not in labels:
        raise ValueError(f"unsupported signal word key: {key}")
    return labels[key]


def get_safety_warning_label(lang: str | None) -> str:
    return get_signal_word(lang, "safety_warning")


def get_symbols_notice_label(lang: str | None) -> str:
    return get_signal_word(lang, "symbols_notice")
