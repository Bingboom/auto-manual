#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re

from .renderers_common import apply_vars, rst_escape
from ..utils.spec_master import canonicalize_model_token
from ..utils.variable_resolver import parse_model_tokens

PH_TROUBLESHOOTING_TABLE_RST = "{{ troubleshooting_table_rst }}"
PH_TROUBLESHOOTING_ROWS_RST = "{{ troubleshooting_rows_rst }}"

_TRUE_VALUES = {"1", "true", "yes", "y"}
_FALSE_VALUES = {"0", "false", "no", "n"}

_LANG_SUFFIX = {
    "ja": "jp",
    "jp": "jp",
    "uk": "ukr",
    "ukr": "ukr",
    "pt-br": "pt-BR",
    "pt_br": "pt-BR",
    "br": "pt-BR",
}


def _truthy(value: str, *, default: bool = True) -> bool:
    raw = (value or "").strip().casefold()
    if not raw:
        return default
    if raw in _TRUE_VALUES:
        return True
    if raw in _FALSE_VALUES:
        return False
    return default


def _lang_suffix(lang: str) -> str:
    raw = (lang or "").strip().casefold()
    return _LANG_SUFFIX.get(raw, raw)


def _lang_suffix_candidates(lang: str) -> list[str]:
    suffix = _lang_suffix(lang)
    candidates = [
        suffix,
        str(suffix).casefold(),
        str(suffix).replace("-", "_"),
        str(suffix).casefold().replace("-", "_"),
    ]
    if (lang or "").strip().casefold() in {"br", "pt-br", "pt_br"}:
        candidates.extend(["br", "pt-BR", "pt-br", "pt_BR", "pt_br"])
    return list(dict.fromkeys(candidate for candidate in candidates if candidate))


def _first_existing(headers: set[str], candidates: list[str]) -> str:
    for candidate in candidates:
        if candidate in headers:
            return candidate
    return candidates[0]


def _pick_target_model(vars_map: dict[str, str]) -> str:
    for key in ("model", "product_model", "model_no", "model_number", "Model"):
        value = (vars_map.get(key) or "").strip()
        if value:
            return value
    return ""


def _pick_target_region(vars_map: dict[str, str]) -> str:
    for key in ("region", "Region"):
        value = (vars_map.get(key) or "").strip()
        if value:
            return value
    return ""


def _split_tokens(value: str) -> list[str]:
    tokens: list[str] = []
    for token in re.split(r"[,;|]", value or ""):
        item = token.strip()
        if item:
            tokens.append(item)
    return tokens


def _matches_region(row: dict[str, str], *, target_region: str) -> bool:
    region_value = row.get("Region") or row.get("region") or ""
    tokens = _split_tokens(region_value)
    if not tokens:
        return True
    if any(token.casefold() == "all" for token in tokens):
        return True
    if not target_region:
        return True
    target = target_region.casefold()
    if target == "pt-br":
        target_aliases = {"pt-br", "pt_br", "br"}
    else:
        target_aliases = {target}
    return any(token.casefold() in target_aliases for token in tokens)


def _matches_model(row: dict[str, str], *, target_model: str, target_region: str) -> bool:
    model_value = row.get("Model") or row.get("model") or ""
    tokens = parse_model_tokens(model_value)
    if not tokens:
        return True
    if any(token.casefold() == "all" for token in tokens):
        return True
    if not target_model:
        return False
    normalized_target = canonicalize_model_token(target_model, region=target_region)
    normalized_tokens = {
        canonicalize_model_token(token, region=target_region).casefold()
        for token in tokens
        if token
    }
    return normalized_target.casefold() in normalized_tokens


def _sort_key(row: dict[str, str]) -> tuple[int, float | str, str]:
    raw_no = (row.get("No.") or row.get("No") or "").strip()
    try:
        no_key: tuple[int, float | str] = (0, float(raw_no))
    except ValueError:
        no_key = (1, raw_no.casefold())
    return (*no_key, (row.get("error_code") or "").strip().casefold())


def _collect_rows(
    blocks: list[dict[str, str]],
    *,
    lang: str,
    vars_map: dict[str, str],
) -> list[dict[str, str]]:
    if not blocks:
        raise ValueError(f"troubleshooting page has no rows for lang={lang}")
    headers = set(blocks[0].keys())
    measures_col = _first_existing(
        headers,
        [
            *(f"corrective_measures_{suffix}" for suffix in _lang_suffix_candidates(lang)),
            "corrective_measures_en",
        ],
    )
    if measures_col not in headers:
        raise ValueError(f"troubleshooting csv missing language corrective-measures column: {measures_col}")

    target_model = _pick_target_model(vars_map)
    target_region = _pick_target_region(vars_map)
    rows: list[dict[str, str]] = []

    for row in blocks:
        if not _truthy(row.get("Is_latest") or row.get("Is_Latest") or row.get("is_latest"), default=True):
            continue
        if not _matches_model(row, target_model=target_model, target_region=target_region):
            continue
        if not _matches_region(row, target_region=target_region):
            continue
        code = (row.get("error_code") or "").strip()
        measures = (row.get(measures_col) or row.get("corrective_measures_en") or "").strip()
        if not code or not measures:
            continue
        rows.append(
            {
                "no": (row.get("No.") or row.get("No") or "").strip(),
                "error_code": apply_vars(code, vars_map),
                "measures": apply_vars(measures, vars_map),
                "sort_no": row.get("No.") or row.get("No") or "",
            }
        )

    rows.sort(key=lambda row: _sort_key({"No.": row["sort_no"], "error_code": row["error_code"]}))
    if not rows:
        raise ValueError(f"troubleshooting page has no matching rows for model={target_model or '?'} region={target_region or '?'} lang={lang}")
    return rows


def _append_text_cell(lines: list[str], prefix: str, text: str) -> None:
    raw_text = (text or "").replace("\\n", "\n")
    raw_lines = raw_text.splitlines()
    if not raw_lines:
        lines.append(prefix.rstrip())
        return
    if len(raw_lines) == 1:
        lines.append(prefix + rst_escape(raw_lines[0]))
        return

    first = rst_escape(raw_lines[0])
    lines.append(prefix + (f"| {first}" if first else "|"))
    continuation = " " * len(prefix)
    for raw_line in raw_lines[1:]:
        line = rst_escape(raw_line)
        lines.append(continuation + (f"| {line}" if line else "|"))


def _table_rows(rows: list[dict[str, str]]) -> str:
    lines: list[str] = []
    for row in rows:
        _append_text_cell(lines, "   * - ", row["error_code"])
        _append_text_cell(lines, "     - ", row["measures"])
    return "\n".join(lines) + "\n"


def render_troubleshooting_page(
    template: str,
    blocks: list[dict[str, str]],
    sku_id: str,
    lang: str,
    vars_map: dict[str, str],
) -> str:
    del sku_id
    rows = _collect_rows(blocks, lang=lang, vars_map=vars_map)
    row_rst = _table_rows(rows)
    if PH_TROUBLESHOOTING_ROWS_RST not in template and PH_TROUBLESHOOTING_TABLE_RST not in template:
        raise ValueError(
            "troubleshooting template must contain "
            f"{PH_TROUBLESHOOTING_ROWS_RST} inside the list-table body"
        )
    rendered = template.replace(PH_TROUBLESHOOTING_ROWS_RST, row_rst)
    rendered = rendered.replace(PH_TROUBLESHOOTING_TABLE_RST, row_rst)
    return rendered
