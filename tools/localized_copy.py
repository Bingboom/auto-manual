#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from tools import lang_registry
from tools.utils.spec_master import canonicalize_model_token
from tools.utils.variable_resolver import parse_model_tokens

LOCALIZED_COPY_FILE = "Localized_Copy.csv"
COPY_TOKEN_RE = re.compile(r"\{\{\s*copy:([A-Za-z0-9_.:-]+)\s*\}\}")

_TRUE_VALUES = {"1", "true", "yes", "y"}
_LANG_TEXT_COLUMNS = {
    alias.casefold(): spec.localized_copy_column
    for spec in lang_registry.LANGUAGE_REGISTRY
    for alias in spec.aliases
}


def snapshot_language_suffixes(lang: str | None) -> tuple[str, ...]:
    """Exact historical snapshot suffixes, in registry order (not input order).

    This is column spelling, not language normalization: Japanese remains
    canonical ``ja`` even where the first snapshot suffix is ``jp``. An empty
    language has no candidates; callers own any default language policy.
    """
    spec = lang_registry.language_spec(lang)
    if spec is not None:
        return spec.column_suffixes
    raw = (lang or "").strip().lower()
    return (raw,) if raw else ()


def localized_columns(
    bases: Iterable[str], suffixes: Iterable[str], *, uppercase: bool = False,
) -> tuple[str, ...]:
    """Expand CSV spelling variants without choosing aliases or fallbacks.

    Callers supply registry alias order or table suffix order. Lowercase and
    underscore spellings preserve legacy CSV readers; uppercase is opt-in for
    the spec parser. Base variants are interleaved for each suffix spelling.
    """
    bases = tuple(bases)
    columns: list[str] = []
    for suffix in suffixes:
        if not suffix:
            continue
        variants = [suffix, suffix.casefold()]
        if uppercase:
            variants.append(suffix.upper())
        variants.extend((suffix.replace("-", "_"), suffix.casefold().replace("-", "_")))
        columns.extend(f"{base}_{variant}" for variant in variants for base in bases)
    return tuple(dict.fromkeys(columns))


def table_localized_columns(table: str, base: str, lang: str) -> tuple[str, ...]:
    """Only columns declared for this table/field, then their CSV spellings.

    For example LCD Ukrainian uses ``ukr``; a global ``uk`` alias must not
    outrank it. Bare legacy fields such as footnotes' ``pt-BR`` are not added
    here: a caller using those must explicitly include the table's fields.
    """
    spec = lang_registry.language_spec(lang)
    suffixes = (
        tuple(suffix for column in spec.columns_for_table(table)
              for suffix in spec.column_suffixes if column == f"{base}_{suffix}")
        if spec is not None else ((lang or "").strip(),)
    )
    return localized_columns((base,), suffixes)


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


def localized_cell(
    row: Mapping[str, str | None], base: str, lang: str | None, *,
    fallback_columns: Iterable[str] = (),
) -> str:
    """Read exact snapshot suffixes per cell, then explicit fallback columns."""
    return first_text(
        row, (f"{base}_{suffix}" for suffix in snapshot_language_suffixes(lang)),
        fallback_columns=fallback_columns,
    )


@dataclass(frozen=True)
class LocalizedCopyMatch:
    copy_key: str
    text: str
    row_number: int


def _truthy(value: str, *, default: bool = True) -> bool:
    raw = (value or "").strip().casefold()
    if not raw:
        return default
    return raw in _TRUE_VALUES


def _text_column_for_lang(lang: str) -> str:
    raw = (lang or "").strip().casefold()
    return _LANG_TEXT_COLUMNS.get(raw, f"text_{raw}")


def _split_tokens(value: str) -> list[str]:
    tokens = [token.strip() for token in re.split(r"[,;|/\s\u3001\uff0c]+", value or "")]
    return [token for token in tokens if token]


def _region_score(row_region: str, target_region: str | None) -> int | None:
    raw = (row_region or "").strip()
    if not raw or raw.casefold() == "all":
        return 0
    if target_region and raw.casefold() == target_region.strip().casefold():
        return 2
    return None


def _model_score(row_model: str, target_model: str | None, target_region: str | None) -> int | None:
    tokens = _split_tokens(row_model)
    if not tokens or any(token.casefold() == "all" for token in tokens):
        return 0
    if not target_model:
        return None
    normalized_target = canonicalize_model_token(target_model, region=target_region or "").casefold()
    normalized_tokens = {
        canonicalize_model_token(token, region=target_region or "").casefold()
        for token in parse_model_tokens(row_model)
        if token
    }
    return 2 if normalized_target in normalized_tokens else None


class LocalizedCopyResolver:
    def __init__(self, rows: list[dict[str, str]], *, source_path: Path | None = None):
        self.rows = rows
        self.source_path = source_path

    @classmethod
    def from_csv(cls, path: str | Path) -> "LocalizedCopyResolver":
        return _resolver_from_csv(str(path))

    def resolve(
        self,
        copy_key: str,
        *,
        lang: str,
        model: str | None = None,
        region: str | None = None,
    ) -> str:
        key = (copy_key or "").strip()
        if not key:
            raise KeyError("localized copy key must not be empty")

        text_col = _text_column_for_lang(lang)
        candidates: list[tuple[tuple[int, int, int], LocalizedCopyMatch]] = []
        for index, row in enumerate(self.rows, start=2):
            if (row.get("copy_key") or "").strip() != key:
                continue
            if not _truthy(row.get("Is_Latest") or row.get("is_latest") or "", default=True):
                continue
            region_score = _region_score(row.get("Region") or row.get("region") or "", region)
            if region_score is None:
                continue
            model_score = _model_score(row.get("Model") or row.get("model") or "", model, region)
            if model_score is None:
                continue
            text = (row.get(text_col) or "").strip()
            if not text:
                raise KeyError(
                    f"localized copy '{key}' has no value for lang '{lang}' "
                    f"in {self._source_label()} line {index}"
                )
            version = (row.get("Version") or row.get("version") or "").strip()
            version_score = 1 if version else 0
            candidates.append(
                (
                    (model_score + region_score, version_score, -index),
                    LocalizedCopyMatch(copy_key=key, text=text, row_number=index),
                )
            )

        if not candidates:
            raise KeyError(
                f"localized copy '{key}' not found for lang '{lang}'"
                + (f" model '{model}'" if model else "")
                + (f" region '{region}'" if region else "")
                + f" in {self._source_label()}"
            )

        candidates.sort(key=lambda item: item[0], reverse=True)
        best_score = candidates[0][0]
        best_matches = [match for score, match in candidates if score == best_score]
        distinct = {match.text for match in best_matches}
        if len(distinct) > 1:
            rows = ", ".join(str(match.row_number) for match in best_matches)
            raise KeyError(f"localized copy '{key}' is ambiguous in {self._source_label()} lines {rows}")
        return best_matches[0].text

    def apply(
        self,
        text: str,
        *,
        lang: str,
        model: str | None = None,
        region: str | None = None,
    ) -> str:
        def replace(match: re.Match[str]) -> str:
            return self.resolve(match.group(1), lang=lang, model=model, region=region)

        return COPY_TOKEN_RE.sub(replace, text or "")

    def _source_label(self) -> str:
        return self.source_path.as_posix() if self.source_path is not None else "<memory>"


@lru_cache(maxsize=16)
def _resolver_from_csv(path_text: str) -> LocalizedCopyResolver:
    path = Path(path_text)
    if not path.exists():
        raise FileNotFoundError(f"localized copy csv not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return LocalizedCopyResolver(rows, source_path=path)


def apply_localized_copy_tokens(
    text: str,
    *,
    localized_copy_csv: str | Path,
    lang: str,
    model: str | None = None,
    region: str | None = None,
) -> str:
    if not COPY_TOKEN_RE.search(text or ""):
        return text or ""
    resolver = LocalizedCopyResolver.from_csv(localized_copy_csv)
    return resolver.apply(text, lang=lang, model=model, region=region)
