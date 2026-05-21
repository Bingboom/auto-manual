#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
import json
import re
import unicodedata
from pathlib import Path

from .renderers_common import apply_vars, latex_arg_escape, rst_escape
from ..utils.spec_master import canonicalize_model_token
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
    "pt-br": "pt-BR",
    "pt_br": "pt-BR",
    "br": "pt-BR",
}

_LANG_COPY = {
    "en": {"title": "LCD DISPLAY", "alt": "LCD icon map placeholder."},
    "fr": {"title": "AFFICHAGE LCD", "alt": "Carte des icônes de l'écran LCD."},
    "es": {"title": "PANTALLA LCD", "alt": "Mapa de iconos de la pantalla LCD."},
    "de": {"title": "LCD-ANZEIGE", "alt": "Abbildung der LCD-Symbole als Platzhalter."},
    "it": {"title": "DISPLAY LCD", "alt": "Segnaposto mappa icone LCD."},
    "uk": {"title": "ЕКРАН LCD", "alt": "Заглушка схеми значків LCD."},
    "ja": {"title": "液晶画面", "alt": "LCDアイコンマップ。"},
    "zh": {"title": "显示屏界面", "alt": "LCD 图标示意图。"},
    "pt-BR": {"title": "TELA LCD", "alt": "Mapa de ícones da tela LCD."},
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
    table_candidate_keys: list[str] = []

    def resolve_from_render_vars(key: str) -> bool:
        if key in resolved:
            return True
        alias_value = render_var_aliases.get(key.casefold())
        if alias_value is not None:
            resolved[key] = alias_value
            return True
        return False

    for key in declared_keys:
        if resolve_from_render_vars(key):
            continue
        table_candidate_keys.append(key)
    for key in placeholder_keys:
        if resolve_from_render_vars(key):
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
    if not blocks:
        raise ValueError(f"lcd_icons page has no rows for lang={lang}")
    headers = set(blocks[0].keys())
    name_col = _first_existing(
        headers,
        [*(f"icon_{suffix}" for suffix in _lang_suffix_candidates(lang)), "icon_en"],
    )
    desc_col = _first_existing(
        headers,
        [*(f"icon_desc_{suffix}" for suffix in _lang_suffix_candidates(lang)), "icon_desc_en"],
    )
    if desc_col not in headers:
        raise ValueError(f"lcd_icons csv missing language description column: {desc_col}")

    target_model = _pick_target_model(vars_map)
    target_region = _pick_target_region(vars_map)
    rows: list[dict[str, str]] = []

    def collect(*, allow_model_fallback: bool) -> list[dict[str, str]]:
        collected: list[dict[str, str]] = []
        for row in blocks:
            if not _truthy(row.get("Is_latest") or row.get("Is_Latest") or row.get("is_latest"), default=True):
                continue
            if not allow_model_fallback and not _matches_model(row, target_model=target_model, target_region=target_region):
                continue
            name = (row.get(name_col) or row.get("icon_en") or "").strip()
            description = (row.get(desc_col) or row.get("icon_desc_en") or "").strip()
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
            collected.append(
                {
                    "no": (row.get("No.") or row.get("No") or "").strip(),
                    "figure": _figure_image_path(row.get("figure") or row.get("Figure") or ""),
                    "name": apply_vars(name, row_vars),
                    "description": apply_vars(description, row_vars),
                    "sort_no": row.get("No.") or row.get("No") or "",
                    "sort_name": row.get("icon_en") or name,
                }
            )
        return collected

    rows = collect(allow_model_fallback=False)
    if not rows:
        rows = collect(allow_model_fallback=True)

    rows.sort(key=lambda row: _sort_key({"No.": row["sort_no"], "icon_en": row["sort_name"]}))
    if not rows:
        raise ValueError(f"lcd_icons page has no matching rows for model={target_model or '?'} lang={lang}")
    return rows


def _format_description_line(line: str) -> str:
    for label in ("On", "Off", "Blink", "Ligado", "Desligado", "Piscando", "点亮", "熄灭", "闪烁"):
        for separator in (":", "："):
            prefix = f"{label}{separator}"
            if line.startswith(prefix):
                remainder = line[len(prefix):]
                spacer = "" if not remainder or remainder.startswith(" ") else " "
                return f"**{prefix}**{spacer}{remainder}"
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


def _rst_table(rows: list[dict[str, str]]) -> str:
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


def _indent_block(text: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join((prefix + line) if line else line for line in text.rstrip("\n").splitlines())


def _latex_image_arg(path: str) -> str:
    raw = (path or "").strip()
    if not raw:
        return ""
    return Path(raw).name


def _latex_lines_arg(text: str) -> str:
    raw = (text or "").replace("\\n", "\n")
    parts = [part.strip() for part in raw.splitlines() if part.strip()]
    return r" \newline ".join(latex_arg_escape(part) for part in parts)


def _latex_description_line(line: str) -> str:
    for label in ("On", "Off", "Blink", "点亮", "熄灭", "闪烁"):
        for separator in (":", "："):
            prefix = f"{label}{separator}"
            if line.startswith(prefix):
                remainder = line[len(prefix):]
                remainder = remainder.strip()
                spacer = " " if remainder else ""
                return rf"\textbf{{{latex_arg_escape(prefix)}}}{spacer}{latex_arg_escape(remainder)}"
    return latex_arg_escape(line)


def _latex_description_arg(text: str) -> str:
    raw = (text or "").replace("\\n", "\n")
    parts = [part.strip() for part in raw.splitlines() if part.strip()]
    return r" \newline ".join(_latex_description_line(part) for part in parts)


def _latex_table(rows: list[dict[str, str]]) -> str:
    # Worker A owns the macro definitions. Keep this renderer limited to calling
    # the shared LCD table interface with escaped text and basename image args.
    lines: list[str] = [
        r"\begin{HBLcdIconTable}",
    ]
    for row in rows:
        lines.append(
            r"\HBLcdIconRow"
            f"{{{latex_arg_escape(row['no'])}}}"
            f"{{{_latex_image_arg(row['figure'])}}}"
            f"{{{_latex_lines_arg(row['name'])}}}"
            f"{{{_latex_description_arg(row['description'])}}}"
        )
    lines.append(r"\end{HBLcdIconTable}")
    return "\n".join(lines)


def _table(rows: list[dict[str, str]]) -> str:
    rst_table = _rst_table(rows)
    latex_table = _latex_table(rows)
    return "\n".join(
        [
            ".. only:: not latex",
            "",
            _indent_block(rst_table, 3),
            "",
            ".. only:: latex",
            "",
            "   .. raw:: latex",
            "",
            _indent_block(latex_table, 6),
            "",
        ]
    )


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
    copy = _LANG_COPY.get(lang) or _LANG_COPY.get(_lang_suffix(lang)) or _LANG_COPY["en"]
    rows = _collect_rows(blocks, lang=lang, vars_map=vars_map)
    rendered = template.replace(PH_LCD_ICONS_HEADING_RST, _heading(copy["title"]))
    rendered = rendered.replace(PH_LCD_ICONS_IMAGE_ALT, rst_escape(copy["alt"]))
    rendered = rendered.replace(PH_LCD_ICONS_TABLE_RST, _table(rows))
    return rendered
