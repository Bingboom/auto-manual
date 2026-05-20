from __future__ import annotations

from collections.abc import Iterable


_REGION_ALIASES: dict[str, tuple[str, ...]] = {
    "pt-br": ("pt-BR", "Brazil", "BR"),
    "brazil": ("pt-BR", "Brazil", "BR"),
    "br": ("pt-BR", "Brazil", "BR"),
}


def _alias_key(value: str) -> str:
    return (value or "").strip().replace("_", "-").casefold()


def canonical_document_key_region(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    aliases = _REGION_ALIASES.get(_alias_key(text))
    if aliases:
        return aliases[0]
    return text.upper()


def document_key_region_tokens(value: str) -> tuple[str, ...]:
    text = (value or "").strip()
    if not text:
        return ()
    aliases = _REGION_ALIASES.get(_alias_key(text))
    if aliases:
        return _unique_non_empty(aliases)
    return _unique_non_empty((text, text.upper()))


def _unique_non_empty(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        text = (value or "").strip()
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
    return tuple(out)
