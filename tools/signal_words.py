#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
from pathlib import Path

from tools.data_snapshot import STRUCTURED_DATA_DEFAULT_DIR, SYMBOLS_BLOCKS_FILE
from tools.utils.path_utils import repo_root
from tools.utils.spec_master import canonicalize_model_token
from tools.utils.variable_resolver import parse_model_tokens

_DEFAULT_LANG = "en"
_SUPPORTED_LANGS = {"en", "zh", "ja", "jp", "fr", "es", "pt-br", "pt_br", "br", "de", "it", "uk", "ukr"}
_SIGNAL_WORD_KEYS = {"warning", "danger", "caution", "note", "tips"}
_SIGNAL_WORD_ALIASES = {"tip": "tips", "safety_warning": "warning", "symbols_notice": "danger"}
_TRUE_VALUES = {"1", "true", "yes", "y"}
_FALSE_VALUES = {"0", "false", "no", "n", "outdated"}


def _default_symbols_blocks_csv() -> Path:
    return repo_root() / STRUCTURED_DATA_DEFAULT_DIR / SYMBOLS_BLOCKS_FILE


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


def _row_matches_region(row: dict[str, str], region: str | None) -> bool:
    target = (region or "").strip().casefold()
    market_tokens = _split_tokens(row.get("Market") or row.get("market") or "")
    if market_tokens:
        return any(token.casefold() == "all" or token.casefold() == target for token in market_tokens)

    row_region = (row.get("Region") or row.get("region") or "").strip().casefold()
    if not row_region or row_region == "all":
        return True
    return bool(target) and row_region == target


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


def _read_signal_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [
            row
            for row in reader
            if (row.get("block_type") or row.get("Block_type") or "").strip().casefold() == "signal_row"
        ]


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
        columns.extend(
            (
                f"label_{token}",
                f"Label_{token}",
                f"signal_word_{token}",
                f"Signal_word_{token}",
            )
        )
    columns.extend(("label", "Label", "signal_word", "Signal_word"))
    return tuple(dict.fromkeys(columns))


def label_from_signal_row(row: dict[str, str], *, key: str | None = None, lang: str | None = None) -> str:
    """Return the visible signal label from a symbols_blocks signal_row.

    Current Feishu rows use ``symbol_key`` as the maintained signal token. If
    future rows add explicit label columns, those values take precedence.
    """

    resolved_lang = _resolve_lang(lang)
    for column in _label_columns(resolved_lang):
        value = (row.get(column) or "").strip()
        if value:
            return value

    signal_key = _resolve_key(key or row.get("symbol_key") or "")
    row_signal_key = _row_key(row)
    if signal_key != row_signal_key:
        raise ValueError(f"signal row key mismatch: expected {signal_key}, got {row_signal_key}")
    return (row.get("symbol_key") or signal_key).strip().upper()


def get_signal_word(
    lang: str | None,
    key: str,
    *,
    symbols_blocks_csv: str | Path | None = None,
    model: str | None = None,
    region: str | None = None,
) -> str:
    csv_path = Path(symbols_blocks_csv) if symbols_blocks_csv else _default_symbols_blocks_csv()
    signal_key = _resolve_key(key)
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
        if _row_matches_region(row, region) and _row_matches_model(row, model, region)
    ]
    selected = sorted(scoped_rows or rows, key=_sort_order)[0]
    return label_from_signal_row(selected, key=signal_key, lang=lang)


def get_safety_warning_label(
    lang: str | None,
    *,
    symbols_blocks_csv: str | Path | None = None,
    model: str | None = None,
    region: str | None = None,
) -> str:
    return get_signal_word(
        lang,
        "safety_warning",
        symbols_blocks_csv=symbols_blocks_csv,
        model=model,
        region=region,
    )


def get_symbols_notice_label(
    lang: str | None,
    *,
    symbols_blocks_csv: str | Path | None = None,
    model: str | None = None,
    region: str | None = None,
) -> str:
    return get_signal_word(
        lang,
        "symbols_notice",
        symbols_blocks_csv=symbols_blocks_csv,
        model=model,
        region=region,
    )
