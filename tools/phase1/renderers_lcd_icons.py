#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
import json
import re
import unicodedata
from pathlib import Path

from .renderers_common import apply_vars, rst_escape
from ..utils.variable_resolver import parse_model_tokens, resolve_variable_value

PH_LCD_ICONS_HEADING_RST = "{{ lcd_icons_heading_rst }}"
PH_LCD_ICONS_IMAGE_ALT = "{{ lcd_icons_image_alt }}"
PH_LCD_ICONS_TABLE_RST = "{{ lcd_icons_table_rst }}"

_VAR_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_\-]+)\s*\}\}")
_TRUE_VALUES = {"1", "true", "yes", "y"}
_FALSE_VALUES = {"0", "false", "no", "n"}

_LANG_SUFFIX = {
    "ja": "jp",
    "jp": "jp",
    "uk": "ukr",
    "ukr": "ukr",
}

_LANG_COPY = {
    "en": {"title": "LCD DISPLAY", "alt": "LCD icon map placeholder."},
    "fr": {"title": "AFFICHAGE LCD", "alt": "Carte des icônes de l'écran LCD."},
    "es": {"title": "PANTALLA LCD", "alt": "Mapa de iconos de la pantalla LCD."},
    "de": {"title": "LCD-ANZEIGE", "alt": "Abbildung der LCD-Symbole als Platzhalter."},
    "it": {"title": "DISPLAY LCD", "alt": "Segnaposto mappa icone LCD."},
    "uk": {"title": "ЕКРАН LCD", "alt": "Заглушка схеми значків LCD."},
    "ja": {"title": "液晶画面", "alt": "LCDアイコンマップ。"},
}


def _read_csv(path: str) -> list[dict[str, str]]:
    raw = (path or "").strip()
    if not raw:
        return []
    csv_path = Path(raw)
    if not csv_path.exists():
        return []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


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


def _pick_target_model(vars_map: dict[str, str]) -> str:
    for key in ("model", "product_model", "model_no", "model_number", "Model"):
        value = (vars_map.get(key) or "").strip()
        if value:
            return value
    return ""


def _matches_model(row: dict[str, str], *, target_model: str) -> bool:
    model_value = row.get("Model") or row.get("model") or ""
    tokens = parse_model_tokens(model_value)
    if not tokens:
        return True
    if any(token.casefold() == "all" for token in tokens):
        return True
    if not target_model:
        return False
    return target_model in tokens


def _sort_key(row: dict[str, str]) -> tuple[int, float | str, str]:
    raw_no = (row.get("No.") or row.get("No") or "").strip()
    try:
        no_key: tuple[int, float | str] = (0, float(raw_no))
    except ValueError:
        no_key = (1, raw_no.casefold())
    return (*no_key, (row.get("icon_en") or "").strip().casefold())


def _split_variable_keys(value: str) -> list[str]:
    keys: list[str] = []
    for token in re.split(r"[,;|]", value or ""):
        key = token.strip()
        if key and key not in keys:
            keys.append(key)
    return keys


def _placeholder_keys(*texts: str) -> list[str]:
    keys: list[str] = []
    for text in texts:
        for match in _VAR_RE.finditer(text or ""):
            key = match.group(1)
            if key and key not in keys:
                keys.append(key)
    return keys


def _resolve_row_vars(
    row: dict[str, str],
    *,
    name: str,
    description: str,
    target_model: str,
    lang: str,
    vars_map: dict[str, str],
) -> dict[str, str]:
    resolved = dict(vars_map)
    declared_keys = _split_variable_keys(row.get("variable_keys") or row.get("Variable_keys") or "")
    placeholder_keys = _placeholder_keys(name, description)

    render_var_aliases = {key.casefold(): value for key, value in vars_map.items()}
    table_candidate_keys: list[str] = list(declared_keys)
    for key in placeholder_keys:
        if key in resolved:
            continue
        alias_value = render_var_aliases.get(key.casefold())
        if alias_value is not None:
            resolved[key] = alias_value
            continue
        if key not in table_candidate_keys:
            table_candidate_keys.append(key)
    if not table_candidate_keys:
        return resolved

    defaults_csv = vars_map.get("variable_defaults_csv", "")
    default_rows = _read_csv(defaults_csv)
    if not default_rows:
        raise ValueError(
            "lcd_icons row uses variables but Variable_Defaults.csv is missing or empty: "
            f"{defaults_csv or '?'}"
        )
    override_rows = _read_csv(vars_map.get("variable_lang_overrides_csv", ""))

    for key in table_candidate_keys:
        if key in resolved:
            continue
        value = resolve_variable_value(
            default_rows,
            override_rows,
            key,
            model=target_model,
            lang=lang,
        )
        if value is None:
            if key not in declared_keys:
                continue
            line = (row.get("__line__") or "?").strip()
            raise ValueError(f"lcd_icons row line {line}: unresolved variable key '{key}'")
        resolved[key] = value
    return resolved


def _collect_rows(
    blocks: list[dict[str, str]],
    *,
    lang: str,
    vars_map: dict[str, str],
) -> list[dict[str, str]]:
    suffix = _lang_suffix(lang)
    name_col = f"icon_{suffix}"
    desc_col = f"icon_desc_{suffix}"
    if not blocks:
        raise ValueError(f"lcd_icons page has no rows for lang={lang}")
    headers = set(blocks[0].keys())
    if desc_col not in headers:
        raise ValueError(f"lcd_icons csv missing language description column: {desc_col}")

    target_model = _pick_target_model(vars_map)
    rows: list[dict[str, str]] = []
    for row in blocks:
        if not _truthy(row.get("Is_latest") or row.get("Is_Latest") or row.get("is_latest"), default=True):
            continue
        if not _matches_model(row, target_model=target_model):
            continue
        name = (row.get(name_col) or row.get("icon_en") or "").strip()
        description = (row.get(desc_col) or "").strip()
        if not name or not description:
            continue
        row_vars = _resolve_row_vars(
            row,
            name=name,
            description=description,
            target_model=target_model,
            lang=lang,
            vars_map=vars_map,
        )
        rows.append(
            {
                "no": (row.get("No.") or row.get("No") or "").strip(),
                "figure": _figure_image_path(row.get("figure") or row.get("Figure") or ""),
                "name": apply_vars(name, row_vars),
                "description": apply_vars(description, row_vars),
                "sort_no": row.get("No.") or row.get("No") or "",
                "sort_name": row.get("icon_en") or name,
            }
        )

    rows.sort(key=lambda row: _sort_key({"No.": row["sort_no"], "icon_en": row["sort_name"]}))
    if not rows:
        raise ValueError(f"lcd_icons page has no matching rows for model={target_model or '?'} lang={lang}")
    return rows


def _format_description_line(line: str) -> str:
    for label in ("On", "Off", "Blink"):
        prefix = f"{label}:"
        if line.startswith(prefix):
            return f"**{prefix}**{line[len(prefix):]}"
    return line


def _figure_image_path(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    if not raw.startswith(("{", "[")):
        return raw
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return ""
    items = payload if isinstance(payload, list) else [payload]
    for item in items:
        if not isinstance(item, dict):
            continue
        for key in ("path", "local_path", "relative_path", "file_path"):
            path_value = str(item.get(key) or "").strip()
            if path_value:
                return path_value
        file_token = str(item.get("file_token") or item.get("token") or "").strip()
        if file_token:
            name = str(item.get("name") or item.get("file_name") or "").strip()
            suffix = Path(name).suffix.lower() or ".png"
            return f"data/phase2/_attachments/lcd_icons/{file_token}{suffix}"
    return ""


def _append_image_cell(lines: list[str], prefix: str, path: str, *, alt: str) -> None:
    raw_path = (path or "").strip()
    if not raw_path:
        lines.append(prefix.rstrip())
        return
    option_prefix = " " * (len(prefix) + 3)
    alt_text = " ".join((alt or "").replace("\\n", "\n").split()) or "LCD icon"
    lines.append(prefix + f".. image:: {raw_path}")
    lines.append(option_prefix + f":alt: {rst_escape(alt_text)}")
    lines.append(option_prefix + ":width: 42px")


def _append_text_cell(lines: list[str], prefix: str, text: str, *, format_status: bool = False) -> None:
    raw_text = (text or "").replace("\\n", "\n")
    raw_lines = raw_text.splitlines()
    if not raw_lines:
        lines.append(prefix.rstrip())
        return

    def format_line(raw_line: str) -> str:
        line = rst_escape(raw_line)
        if format_status:
            line = _format_description_line(line)
        return line

    if len(raw_lines) == 1:
        lines.append(prefix + format_line(raw_lines[0]))
        return

    first = format_line(raw_lines[0])
    lines.append(prefix + (f"| {first}" if first else "|"))
    continuation = " " * len(prefix)
    for raw_line in raw_lines[1:]:
        line = format_line(raw_line)
        lines.append(continuation + (f"| {line}" if line else "|"))


def _table(rows: list[dict[str, str]]) -> str:
    lines: list[str] = [
        ".. list-table::",
        "   :header-rows: 0",
        "   :widths: 8 12 28 52",
        "",
    ]
    for row in rows:
        _append_text_cell(lines, "   * - ", row["no"])
        _append_image_cell(lines, "     - ", row["figure"], alt=row["name"])
        _append_text_cell(lines, "     - ", row["name"])
        _append_text_cell(lines, "     - ", row["description"], format_status=True)
    return "\n".join(lines) + "\n"


def _heading(title: str) -> str:
    clean = rst_escape(title)
    underline_width = sum(2 if unicodedata.east_asian_width(ch) in {"F", "W"} else 1 for ch in clean)
    return clean + "\n" + ("=" * max(len(clean), underline_width))


def render_lcd_icons_page(
    template: str,
    blocks: list[dict[str, str]],
    sku_id: str,
    lang: str,
    vars_map: dict[str, str],
) -> str:
    del sku_id
    copy = _LANG_COPY.get(lang, _LANG_COPY["en"])
    rows = _collect_rows(blocks, lang=lang, vars_map=vars_map)
    rendered = template.replace(PH_LCD_ICONS_HEADING_RST, _heading(copy["title"]))
    rendered = rendered.replace(PH_LCD_ICONS_IMAGE_ALT, rst_escape(copy["alt"]))
    rendered = rendered.replace(PH_LCD_ICONS_TABLE_RST, _table(rows))
    return rendered
