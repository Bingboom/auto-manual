from __future__ import annotations

from collections.abc import Iterable

_LANGUAGE_ALIASES = {
    "br": "pt-BR",
    "pt-br": "pt-BR",
    "pt_br": "pt-BR",
}

_REGION_ALIASES = {
    "pt-br": "pt-BR",
    "pt_br": "pt-BR",
}


def _clean(value: object) -> str:
    return str(value or "").strip()


def normalize_language(value: object, *, supported: Iterable[str] = ()) -> str:
    token = _clean(value)
    if not token:
        return ""

    aliased = _LANGUAGE_ALIASES.get(token.casefold(), token)
    supported_langs = tuple(_clean(item) for item in supported if _clean(item))
    for supported_lang in supported_langs:
        if supported_lang.casefold() in {token.casefold(), aliased.casefold()}:
            return supported_lang

    return aliased if aliased != token else token.lower()


def language_key(value: object) -> str:
    return normalize_language(value).casefold()


def normalize_region(value: object) -> str:
    token = _clean(value)
    if not token:
        return ""
    return _REGION_ALIASES.get(token.casefold(), token.upper())
