#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from tools.data_snapshot import LOCALIZED_COPY_FILE, STRUCTURED_DATA_DEFAULT_DIR, SYMBOLS_BLOCKS_FILE
from tools.localized_copy import LocalizedCopyResolver
from tools.utils.path_utils import repo_root
from tools.utils.spec_master import canonicalize_model_token
from tools.utils.variable_resolver import parse_model_tokens

_DEFAULT_LANG = "en"
_SUPPORTED_LANGS = {"en", "zh", "ja", "jp", "fr", "es", "pt-br", "pt_br", "br", "de", "it", "uk", "ukr"}
_SIGNAL_WORD_KEYS = {"warning", "danger", "caution", "note", "tips"}
_SIGNAL_WORD_ALIASES = {"tip": "tips", "safety_warning": "warning", "symbols_notice": "danger"}
_TRUE_VALUES = {"1", "true", "yes", "y"}
_FALSE_VALUES = {"0", "false", "no", "n", "outdated"}
_GLOBAL_MARKET_TOKENS = {"all", "global"}
_SIGNAL_LABEL_BLOCK_TYPES = {"signal_row"}
_LABEL_COLUMN_PREFIXES = (
    "label",
    "labels",
    "alert_label",
    "alert_labels",
    "signal_word",
    "signal_words",
)


@dataclass(frozen=True)
class SignalLabel:
    key: str
    label: str


def _default_symbols_blocks_csv() -> Path:
    return repo_root() / STRUCTURED_DATA_DEFAULT_DIR / SYMBOLS_BLOCKS_FILE


def _default_localized_copy_csv() -> Path:
    return repo_root() / STRUCTURED_DATA_DEFAULT_DIR / LOCALIZED_COPY_FILE


def _resolve_lang(lang: str | None) -> str:
    normalized = (lang or "").strip().casefold()
    return normalized if normalized in _SUPPORTED_LANGS else _DEFAULT_LANG


def _resolve_key(key: str) -> str:
    normalized = _SIGNAL_WORD_ALIASES.get((key or "").strip().casefold(), (key or "").strip().casefold())
    if normalized not in _SIGNAL_WORD_KEYS:
        raise ValueError(f"unsupported signal word key: {key}")
    return normalized


def _truthy(value: str, *, default: bool = True) -> bool:
    raw = (value or "").strip().casefold()
    if not raw:
        return default
    if raw in _TRUE_VALUES:
        return True
    if raw in _FALSE_VALUES:
        return False
    return default


def _split_tokens(value: str) -> list[str]:
    return [
        token.strip()
        for token in (value or "").replace(";", ",").replace("|", ",").split(",")
        if token.strip()
    ]


def _split_label_values(value: str) -> list[str]:
    return [
        token.strip()
        for token in (value or "").replace("\n", ";").replace("|", ";").replace(",", ";").split(";")
        if token.strip()
    ]


def _row_key(row: dict[str, str]) -> str:
    return _resolve_key(row.get("symbol_key") or row.get("Signal_word") or row.get("signal_word") or "")


def _row_key_or_none(row: dict[str, str]) -> str | None:
    try:
        return _row_key(row)
    except ValueError:
        return None


def _row_enabled(row: dict[str, str]) -> bool:
    if not _truthy(row.get("enabled") or row.get("Enabled") or "", default=True):
        return False
    return _truthy(row.get("Is_Latest") or row.get("Is_latest") or row.get("is_latest") or "", default=True)


def _row_matches_market(row: dict[str, str], region: str | None) -> bool:
    target = (region or "").strip().casefold()
    market_tokens = _split_tokens(row.get("Market") or row.get("market") or "")
    if not market_tokens:
        return False
    return any(token.casefold() in _GLOBAL_MARKET_TOKENS or token.casefold() == target for token in market_tokens)


def _row_matches_model(row: dict[str, str], model: str | None, region: str | None) -> bool:
    tokens = parse_model_tokens(row.get("Model") or row.get("model") or "")
    if not tokens:
        return True
    if any(token.casefold() == "all" for token in tokens):
        return True
    target = (model or "").strip()
    if not target:
        return False
    target_region = (region or "").strip()
    normalized_target = canonicalize_model_token(target, region=target_region).casefold()
    return any(
        canonicalize_model_token(token, region=target_region).casefold() == normalized_target
        for token in tokens
        if token
    )


def _sort_order(row: dict[str, str]) -> float:
    try:
        return float(row.get("order") or "0")
    except ValueError:
        return 0.0


def _signal_label_copy_key(signal_key: str) -> str:
    return f"symbols.signal.{signal_key}.label"


def _localized_copy_path(
    *,
    symbols_blocks_csv: str | Path | None = None,
    localized_copy_csv: str | Path | None = None,
) -> Path | None:
    if localized_copy_csv:
        path = Path(localized_copy_csv)
        return path if path.exists() else None
    if symbols_blocks_csv:
        candidate = Path(symbols_blocks_csv).parent / LOCALIZED_COPY_FILE
        return candidate if candidate.exists() else None
    candidate = _default_localized_copy_csv()
    return candidate if candidate.exists() else None


def _localized_signal_labels(
    signal_key: str,
    *,
    lang: str | None,
    symbols_blocks_csv: str | Path | None = None,
    localized_copy_csv: str | Path | None = None,
    model: str | None = None,
    region: str | None = None,
) -> tuple[str, ...]:
    path = _localized_copy_path(
        symbols_blocks_csv=symbols_blocks_csv,
        localized_copy_csv=localized_copy_csv,
    )
    if path is None:
        return ()
    resolver = LocalizedCopyResolver.from_csv(path)
    langs = (_resolve_lang(lang),) if lang is not None else tuple(sorted(_SUPPORTED_LANGS))
    labels: list[str] = []
    for target_lang in langs:
        try:
            label = resolver.resolve(
                _signal_label_copy_key(signal_key),
                lang=target_lang,
                model=model,
                region=region,
            )
        except KeyError:
            continue
        if label and label not in labels:
            labels.append(label)
    return tuple(labels)


@lru_cache(maxsize=16)
def _read_signal_rows_cached(path_text: str) -> tuple[dict[str, str], ...]:
    path = Path(path_text)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [
            row
            for row in reader
            if (row.get("block_type") or row.get("Block_type") or "").strip().casefold()
            in _SIGNAL_LABEL_BLOCK_TYPES
        ]
    return tuple(rows)


def _read_signal_rows(path: Path) -> list[dict[str, str]]:
    return [dict(row) for row in _read_signal_rows_cached(path.resolve().as_posix())]


def _label_columns(lang: str) -> tuple[str, ...]:
    raw = (lang or "").strip()
    normalized = raw.casefold()
    aliases = {
        "ja": ("ja", "jp"),
        "jp": ("jp", "ja"),
        "pt-br": ("pt-BR", "br", "pt_br"),
        "pt_br": ("pt_BR", "pt-BR", "br"),
        "br": ("br", "pt-BR", "pt_br"),
        "uk": ("uk", "ukr"),
        "ukr": ("ukr", "uk"),
    }.get(normalized, (raw, normalized))
    columns: list[str] = []
    for token in aliases:
        if not token:
            continue
        for prefix in _LABEL_COLUMN_PREFIXES:
            columns.append(f"{prefix}_{token}")
            columns.append(f"{prefix.title()}_{token}")
    for prefix in _LABEL_COLUMN_PREFIXES:
        columns.append(prefix)
        columns.append(prefix.title())
    return tuple(dict.fromkeys(columns))


def _all_label_columns(row: dict[str, str]) -> tuple[str, ...]:
    columns: list[str] = []
    for column in row:
        normalized = column.strip().casefold()
        if any(normalized == prefix or normalized.startswith(f"{prefix}_") for prefix in _LABEL_COLUMN_PREFIXES):
            columns.append(column)
    return tuple(columns)


def labels_from_signal_row(
    row: dict[str, str],
    *,
    key: str | None = None,
    lang: str | None = None,
    include_symbol_key: bool = True,
) -> tuple[str, ...]:
    columns = _label_columns(_resolve_lang(lang)) if lang is not None else _all_label_columns(row)
    values: list[str] = []
    for column in columns:
        for value in _split_label_values(row.get(column) or ""):
            if value not in values:
                values.append(value)

    if include_symbol_key:
        signal_key = _resolve_key(key or row.get("symbol_key") or "")
        label = (row.get("symbol_key") or signal_key).strip().upper()
        if label and label not in values:
            values.append(label)

    return tuple(values)


def label_from_signal_row(row: dict[str, str], *, key: str | None = None, lang: str | None = None) -> str:
    """Return the compatibility signal label from a symbols_blocks signal_row."""

    labels = labels_from_signal_row(row, key=key, lang=lang, include_symbol_key=True)
    if labels:
        return labels[0]
    signal_key = _resolve_key(key or row.get("symbol_key") or "")
    row_signal_key = _row_key(row)
    if signal_key != row_signal_key:
        raise ValueError(f"signal row key mismatch: expected {signal_key}, got {row_signal_key}")
    return (row.get("symbol_key") or signal_key).strip().upper()


def signal_label_entries(
    *,
    symbols_blocks_csv: str | Path | None = None,
    localized_copy_csv: str | Path | None = None,
    lang: str | None = None,
    model: str | None = None,
    region: str | None = None,
) -> tuple[SignalLabel, ...]:
    csv_path = Path(symbols_blocks_csv) if symbols_blocks_csv else _default_symbols_blocks_csv()
    entries: list[SignalLabel] = []
    seen: set[tuple[str, str]] = set()
    for signal_key in sorted(_SIGNAL_WORD_KEYS):
        for label in _localized_signal_labels(
            signal_key,
            lang=lang,
            symbols_blocks_csv=symbols_blocks_csv,
            localized_copy_csv=localized_copy_csv,
            model=model,
            region=region,
        ):
            dedupe_key = (signal_key, label)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            entries.append(SignalLabel(key=signal_key, label=label))
    for row in _read_signal_rows(csv_path):
        if not _row_enabled(row):
            continue
        signal_key = _row_key_or_none(row)
        if signal_key is None:
            continue
        labels = [
            *labels_from_signal_row(row, key=signal_key, lang=lang, include_symbol_key=True),
            *labels_from_signal_row(row, key=signal_key, lang=None, include_symbol_key=False),
        ]
        for label in labels:
            dedupe_key = (signal_key, label)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            entries.append(SignalLabel(key=signal_key, label=label))
    return tuple(entries)


def get_signal_word(
    lang: str | None,
    key: str,
    *,
    symbols_blocks_csv: str | Path | None = None,
    localized_copy_csv: str | Path | None = None,
    model: str | None = None,
    region: str | None = None,
) -> str:
    csv_path = Path(symbols_blocks_csv) if symbols_blocks_csv else _default_symbols_blocks_csv()
    signal_key = _resolve_key(key)
    labels = _localized_signal_labels(
        signal_key,
        lang=lang,
        symbols_blocks_csv=symbols_blocks_csv,
        localized_copy_csv=localized_copy_csv,
        model=model,
        region=region,
    )
    if labels:
        return labels[0]

    rows = [
        row
        for row in _read_signal_rows(csv_path)
        if _row_enabled(row) and _row_key_or_none(row) == signal_key
    ]
    if not rows:
        raise KeyError(f"symbols_blocks signal_row missing symbol_key={signal_key}")

    scoped_rows = [
        row
        for row in rows
        if _row_matches_market(row, region) and _row_matches_model(row, model, region)
    ]
    if not scoped_rows:
        raise KeyError(f"symbols_blocks signal_row has no matching Market/Model for symbol_key={signal_key}")
    selected = sorted(scoped_rows, key=_sort_order)[0]
    return label_from_signal_row(selected, key=signal_key, lang=lang)


def get_safety_warning_label(
    lang: str | None,
    *,
    symbols_blocks_csv: str | Path | None = None,
    localized_copy_csv: str | Path | None = None,
    model: str | None = None,
    region: str | None = None,
) -> str:
    return get_signal_word(
        lang,
        "safety_warning",
        symbols_blocks_csv=symbols_blocks_csv,
        localized_copy_csv=localized_copy_csv,
        model=model,
        region=region,
    )


def get_symbols_notice_label(
    lang: str | None,
    *,
    symbols_blocks_csv: str | Path | None = None,
    localized_copy_csv: str | Path | None = None,
    model: str | None = None,
    region: str | None = None,
) -> str:
    return get_signal_word(
        lang,
        "symbols_notice",
        symbols_blocks_csv=symbols_blocks_csv,
        localized_copy_csv=localized_copy_csv,
        model=model,
        region=region,
    )
