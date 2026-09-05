"""Policy-free CSV column spelling and cell selection.

Language aliases, source defaults and table fallbacks belong to the readers.
This module intentionally has no business-reader or language-registry imports.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping


def localized_columns(
    bases: Iterable[str], suffixes: Iterable[str], *, uppercase: bool = False,
    casefold: bool = True,
) -> tuple[str, ...]:
    """Expand CSV spelling variants without choosing aliases or fallbacks.

    Callers supply registry alias order or table suffix order. Lowercase and
    underscore spellings preserve legacy CSV readers; uppercase is opt-in for
    spec readers. ``casefold=False`` keeps Spec_Master's historical lower()
    spelling for unknown tokens without widening it to Unicode case folding.
    Base variants are interleaved for each suffix spelling.
    """
    bases = tuple(bases)
    columns: list[str] = []
    for suffix in suffixes:
        if not suffix:
            continue
        lower = suffix.casefold() if casefold else suffix.lower()
        variants = [suffix, lower]
        if uppercase:
            variants.append(suffix.upper())
        variants.extend((suffix.replace("-", "_"), lower.replace("-", "_")))
        columns.extend(f"{base}_{variant}" for variant in variants for base in bases)
    return tuple(dict.fromkeys(columns))


def first_existing_column(
    headers: Iterable[str], columns: Iterable[str], *,
    fallback_columns: Iterable[str] = (), default: str | None = None,
) -> str:
    """Select by header presence only; blank cells never advance this search.

    If no column exists, return the caller's diagnostic key (or the first
    candidate). The caller retains responsibility for missing-column errors.
    """
    candidates = (*columns, *fallback_columns)
    if not candidates and default is None:
        raise ValueError("column selection requires candidates or an explicit default")
    headers = set(headers)
    return next((key for key in candidates if key in headers),
                default if default is not None else candidates[0])


def first_text(
    row: Mapping[str, str | None], columns: Iterable[str], *,
    fallback_columns: Iterable[str] = (), strip: bool = True,
) -> str:
    """First nonempty cell, followed only by explicitly supplied fallbacks.

    Missing keys, None and empty strings are unavailable. By default whitespace
    is also unavailable. ``strip=False`` preserves raw CSV truthiness, including
    whitespace; callers may strip *after* selection when that is their policy.
    There is no implicit source-language or English fallback.
    """
    for key in (*columns, *fallback_columns):
        value = row.get(key) or ""
        if strip:
            value = value.strip()
        if value:
            return value
    return ""
