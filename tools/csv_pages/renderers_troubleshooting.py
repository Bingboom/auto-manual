#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
import unicodedata

from .renderers_common import apply_vars, rst_escape
from ..utils.spec_master import canonicalize_model_token
from ..utils.variable_resolver import parse_model_tokens

PH_TROUBLESHOOTING_HEADING_RST = "{{ troubleshooting_heading_rst }}"
PH_TROUBLESHOOTING_INTRO_RST = "{{ troubleshooting_intro_rst }}"
PH_TROUBLESHOOTING_TABLE_RST = "{{ troubleshooting_table_rst }}"

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

_LANG_COPY = {
    "en": {
        "title": "TROUBLESHOOTING",
        "intro": (
            "If any of the following fault codes appear, follow the listed corrective actions to resolve the issue. "
            "If the fault persists, please contact Jackery Customer Support."
        ),
        "code_header": "Error Code",
        "measures_header": "Corrective Measures",
        "header_rows": "1",
        "widths": "14 86",
    },
    "fr": {
        "title": "DÉPANNAGE",
        "intro": (
            "Si l'un des codes d'erreur suivants apparaît, suivez les actions correctives indiquées pour résoudre le problème. "
            "Si l'erreur persiste, veuillez contacter le service à la clientèle de Jackery."
        ),
        "code_header": "Code d'erreur",
        "measures_header": "Mesures correctives",
        "header_rows": "1",
        "widths": "14 86",
    },
    "es": {
        "title": "RESOLUCIÓN DE PROBLEMAS",
        "intro": (
            "Si aparece alguno de los siguientes códigos de falla, siga las acciones correctivas listadas para resolver el problema. "
            "Si la falla persiste, por favor contacte con atención al cliente de Jackery."
        ),
        "code_header": "Código de error",
        "measures_header": "Medidas correctivas",
        "header_rows": "0",
        "widths": "14 86",
    },
    "de": {
        "title": "FEHLERSUCHE",
        "intro": (
            "Wenn einer der folgenden Fehlercodes angezeigt wird, befolgen Sie die aufgeführten Korrekturmaßnahmen, "
            "um das Problem zu beheben. Wenn der Fehler weiterhin besteht, wenden Sie sich bitte an den Jackery-Kundendienst."
        ),
        "code_header": "Fehlercode",
        "measures_header": "Korrekturmaßnahmen",
        "header_rows": "1",
        "widths": "14 86",
    },
    "it": {
        "title": "RISOLUZIONE DEI PROBLEMI",
        "intro": (
            "Se viene visualizzato uno dei seguenti codici di errore, segui le azioni correttive elencate per risolvere il problema. "
            "Se l'errore persiste, contatta l'Assistenza clienti Jackery."
        ),
        "code_header": "Codice errore",
        "measures_header": "Misure correttive",
        "header_rows": "1",
        "widths": "14 86",
    },
    "uk": {
        "title": "УСУНЕННЯ НЕСПРАВНОСТЕЙ",
        "intro": (
            "Якщо з'являється будь-який із наведених нижче кодів помилки, виконайте вказані дії для усунення проблеми. "
            "Якщо несправність не зникає, зверніться до служби підтримки Jackery."
        ),
        "code_header": "Код помилки",
        "measures_header": "Способи усунення",
        "header_rows": "1",
        "widths": "14 86",
    },
    "pt-BR": {
        "title": "SOLUÇÃO DE PROBLEMAS",
        "intro": (
            "Se qualquer um dos seguintes códigos de falha aparecer, siga as ações corretivas listadas para resolver o problema. "
            "Se a falha persistir, entre em contato com o Suporte ao Cliente da Jackery."
        ),
        "code_header": "Código de erro",
        "measures_header": "Medidas corretivas",
        "header_rows": "1",
        "widths": "14 86",
    },
    "ja": {
        "title": "トラブルシューティング",
        "intro": (
            "次のいずれかのエラーコードが表示された場合は、記載されている対処方法に従って問題を解決してください。"
            "問題が解決しない場合は、Jackeryカスタマーサポートまでご連絡ください。"
        ),
        "code_header": "エラーコード",
        "measures_header": "対処方法",
        "header_rows": "0",
        "widths": "14 86",
    },
    "zh": {
        "title": "故障处理",
        "intro": "如果出现以下任一故障代码，请按照所列的处理方法进行处理。如故障仍然存在，请联系电小二客户支持。",
        "code_header": "故障代码",
        "measures_header": "处理方法",
        "header_rows": "1",
        "widths": "16 84",
    },
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
        code = (row.get("error_code") or row.get("Error Code") or "").strip()
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


def _table(rows: list[dict[str, str]], copy: dict[str, str]) -> str:
    lines: list[str] = [
        ".. list-table::",
        f"   :header-rows: {copy['header_rows']}",
        f"   :widths: {copy['widths']}",
        "",
    ]
    _append_text_cell(lines, "   * - ", copy["code_header"])
    _append_text_cell(lines, "     - ", copy["measures_header"])
    for row in rows:
        _append_text_cell(lines, "   * - ", row["error_code"])
        _append_text_cell(lines, "     - ", row["measures"])
    return "\n".join(lines) + "\n"


def _heading(title: str) -> str:
    clean = rst_escape(title)
    underline_width = sum(2 if unicodedata.east_asian_width(ch) in {"F", "W"} else 1 for ch in clean)
    return clean + "\n" + ("=" * max(len(clean), underline_width))


def render_troubleshooting_page(
    template: str,
    blocks: list[dict[str, str]],
    sku_id: str,
    lang: str,
    vars_map: dict[str, str],
) -> str:
    del sku_id
    copy = _LANG_COPY.get(lang) or _LANG_COPY.get(_lang_suffix(lang)) or _LANG_COPY["en"]
    rows = _collect_rows(blocks, lang=lang, vars_map=vars_map)
    rendered = template.replace(PH_TROUBLESHOOTING_HEADING_RST, _heading(copy["title"]))
    rendered = rendered.replace(PH_TROUBLESHOOTING_INTRO_RST, rst_escape(copy["intro"]))
    rendered = rendered.replace(PH_TROUBLESHOOTING_TABLE_RST, _table(rows, copy))
    return rendered
