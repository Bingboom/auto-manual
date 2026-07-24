#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
import json
import re
import unicodedata
from pathlib import Path

from ..lcd_table_layout import split_lcd_table_rows
from .renderers_common import apply_vars, latex_arg_escape, rst_escape
from ..localized_copy import LocalizedCopyResolver
from ..utils.spec_master import canonicalize_model_token
from ..utils.variable_resolver import parse_model_tokens, resolve_variable_value

PH_LCD_ICONS_HEADING_RST = "{{ lcd_icons_heading_rst }}"
PH_LCD_ICONS_IMAGE_ALT = "{{ lcd_icons_image_alt }}"
PH_LCD_ICONS_TABLE_RST = "{{ lcd_icons_table_rst }}"

_VAR_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_\-]+)\s*\}\}")
_TRUE_VALUES = {"1", "true", "yes", "y"}
_FALSE_VALUES = {"0", "false", "no", "n"}
_STATUS_WORD_MARKER_FIELD = "是否为 status word"
_STATUS_WORDS_FILE = "Status_Words.csv"

_LANG_SUFFIX = {
    "ja": "jp",
    "jp": "jp",
    "uk": "ukr",
    "ukr": "ukr",
    "pt-br": "pt-BR",
    "pt_br": "pt-BR",
    "br": "pt-BR",
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


def _truthy(value: object, *, default: bool = True) -> bool:
    if isinstance(value, list):
        value = ",".join(str(item) for item in value)
    raw = str(value or "").strip().casefold()
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
    headers = set().union(*(row.keys() for row in blocks))
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


def _localized_copy_resolver(vars_map: dict[str, str]) -> LocalizedCopyResolver:
    path = (vars_map.get("localized_copy_csv") or "").strip()
    if not path:
        raise ValueError("lcd_icons renderer requires localized_copy_csv")
    return LocalizedCopyResolver.from_csv(path)


def _copy_text(
    vars_map: dict[str, str],
    key: str,
    *,
    lang: str,
    target_model: str,
    target_region: str,
) -> str:
    return _localized_copy_resolver(vars_map).resolve(
        key,
        lang=lang,
        model=target_model or None,
        region=target_region or None,
    )


def _status_words_csv_path(vars_map: dict[str, str]) -> Path | None:
    for key in ("lcd_status_words_csv", "status_words_csv", "translation_memory_status_words_csv"):
        raw = (vars_map.get(key) or "").strip()
        if raw:
            return Path(raw)
    localized_copy_csv = (vars_map.get("localized_copy_csv") or "").strip()
    if localized_copy_csv:
        return Path(localized_copy_csv).with_name(_STATUS_WORDS_FILE)
    return None


def _status_word_lang_candidates(lang: str) -> list[str]:
    raw = (lang or "").strip()
    normalized = raw.casefold().replace("_", "-")
    candidates = [raw, normalized]
    if normalized in {"ja", "jp"}:
        candidates.extend(["jp", "ja"])
    if normalized in {"uk", "ukr"}:
        candidates.extend(["uk", "ukr"])
    if normalized in {"pt-br", "br"}:
        candidates.extend(["pt-BR", "pt-br", "pt_BR", "br"])
    return list(dict.fromkeys(candidate for candidate in candidates if candidate))


def _status_labels(vars_map: dict[str, str], *, lang: str) -> tuple[str, ...]:
    path = _status_words_csv_path(vars_map)
    if path is None or not path.exists():
        raise ValueError("lcd_icons renderer requires Status_Words.csv exported from Translation Memory")
    rows = _read_csv(str(path))
    if not rows:
        raise ValueError(f"lcd_icons status words snapshot is empty: {path}")
    labels: list[str] = []
    lang_columns = _status_word_lang_candidates(lang)
    for row in rows:
        if not _truthy(row.get(_STATUS_WORD_MARKER_FIELD, ""), default=False):
            continue
        for column in lang_columns:
            label = (row.get(column) or "").strip()
            if label and label not in labels:
                labels.append(label)
    labels.sort(key=len, reverse=True)
    if not labels:
        raise ValueError(f"lcd_icons status words snapshot has no labels for lang={lang}: {path}")
    return tuple(labels)


# Whitespace permitted between a status word and its colon. French typography
# puts a space (often NBSP U+00A0 or narrow NBSP U+202F) before the colon —
# "Clignotant : ..." — so the bold-prefix detector must tolerate it; matching
# only the bare "label:" form left every French (and any " :"-style) status
# line un-bolded.
_STATUS_PREFIX_WS = frozenset({" ", "\t", "\u00a0", "\u202f", "\u2009"})  # space, tab, NBSP, narrow-NBSP, thin space


def _match_status_prefix(
    line: str, status_labels: tuple[str, ...]
) -> tuple[str, str] | None:
    """Return ``(prefix, remainder)`` when *line* opens with a status label
    followed by optional typographic whitespace and a colon (``:`` or ``：``).

    ``prefix`` is the matched ``label[ ws]:`` text as it appears in the source;
    ``remainder`` is the rest of the line. Labels are tried in caller order
    (callers pass them longest-first so ``Blink`` wins over a shorter prefix).
    Returns ``None`` when no status label leads the line.
    """
    for label in status_labels:
        if not label or not line.startswith(label):
            continue
        idx = len(label)
        while idx < len(line) and line[idx] in _STATUS_PREFIX_WS:
            idx += 1
        if idx < len(line) and line[idx] in ":：":
            return line[: idx + 1], line[idx + 1 :]
    return None


def _format_description_line(line: str, *, status_labels: tuple[str, ...]) -> str:
    matched = _match_status_prefix(line, status_labels)
    if matched is not None:
        prefix, remainder = matched
        remainder_text = rst_escape(remainder)
        spacer = " " if remainder_text else ""
        return f"**{rst_escape(prefix)}**{spacer}{remainder_text}"
    return rst_escape(line)


def _canonical_attachment_path(path_value: str) -> str:
    # Synced CSVs store the attachment path anchored at the PHYSICAL export
    # root (an absolute path; e.g. .tmp/review-start/phase2 for queue workers).
    # RST is a deterministic content surface and the asset pipeline's contract
    # is the LOGICAL location, so normalize anything under an ``_attachments``
    # tree to data/phase2/_attachments/...; bundle staging then resolves it
    # against the active data root wherever that physically lives.
    normalized = path_value.replace("\\", "/")
    marker = "_attachments/"
    index = normalized.rfind(marker)
    if index < 0:
        return path_value
    return f"data/phase2/{marker}{normalized[index + len(marker):]}"


def _figure_image_path(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    if not raw.startswith(("{", "[")):
        return _canonical_attachment_path(raw)
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
                return _canonical_attachment_path(path_value)
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


def _append_text_cell(
    lines: list[str],
    prefix: str,
    text: str,
    *,
    format_status: bool = False,
    status_labels: tuple[str, ...] = (),
) -> None:
    raw_text = (text or "").replace("\\n", "\n")
    raw_lines = raw_text.splitlines()
    if not raw_lines:
        lines.append(prefix.rstrip())
        return

    def format_line(raw_line: str) -> str:
        if format_status:
            return _format_description_line(raw_line, status_labels=status_labels)
        return rst_escape(raw_line)

    if len(raw_lines) == 1:
        lines.append(prefix + format_line(raw_lines[0]))
        return

    first = format_line(raw_lines[0])
    lines.append(prefix + (f"| {first}" if first else "|"))
    continuation = " " * len(prefix)
    for raw_line in raw_lines[1:]:
        line = format_line(raw_line)
        lines.append(continuation + (f"| {line}" if line else "|"))


def _rst_table(rows: list[dict[str, str]], *, status_labels: tuple[str, ...]) -> str:
    lines: list[str] = [
        ".. list-table::",
        # longtable: allow page breaks between rows so oversized tables cannot
        # overflow the 130x185 text block into the footer (see reports/typography_gap)
        "   :class: longtable",
        "   :header-rows: 0",
        "   :widths: 8 12 28 52",
        "",
    ]
    for row in rows:
        _append_text_cell(lines, "   * - ", row["no"])
        _append_image_cell(lines, "     - ", row["figure"], alt=row["name"])
        _append_text_cell(lines, "     - ", row["name"])
        _append_text_cell(
            lines,
            "     - ",
            row["description"],
            format_status=True,
            status_labels=status_labels,
        )
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


def _latex_description_line(line: str, *, status_labels: tuple[str, ...]) -> str:
    matched = _match_status_prefix(line, status_labels)
    if matched is not None:
        prefix, remainder = matched
        remainder = remainder.strip()
        spacer = " " if remainder else ""
        return rf"\textbf{{{latex_arg_escape(prefix)}}}{spacer}{latex_arg_escape(remainder)}"
    return latex_arg_escape(line)


def _latex_description_arg(text: str, *, status_labels: tuple[str, ...]) -> str:
    raw = (text or "").replace("\\n", "\n")
    parts = [part.strip() for part in raw.splitlines() if part.strip()]
    return r" \newline ".join(_latex_description_line(part, status_labels=status_labels) for part in parts)


def _latex_table(
    rows: list[dict[str, str]],
    *,
    status_labels: tuple[str, ...],
    lang: str,
) -> str:
    # Every source-driven continuation is a complete rounded table. Page-count
    # drift is accepted while illustration placeholders await final AI artwork.
    segments = split_lcd_table_rows(rows, lang=lang)
    lines: list[str] = []
    for segment_index, segment in enumerate(segments):
        if segment_index:
            lines.append(r"\clearpage")
        lines.append(r"\begin{HBLcdIconTable}")
        for row in segment:
            lines.append(
                r"\HBLcdIconRow"
                f"{{{latex_arg_escape(row['no'])}}}"
                f"{{{_latex_image_arg(row['figure'])}}}"
                f"{{{_latex_lines_arg(row['name'])}}}"
                f"{{{_latex_description_arg(row['description'], status_labels=status_labels)}}}"
            )
        lines.append(r"\end{HBLcdIconTable}")
    return "\n".join(lines)


def _table(
    rows: list[dict[str, str]],
    *,
    status_labels: tuple[str, ...],
    lang: str,
) -> str:
    rst_table = _rst_table(rows, status_labels=status_labels)
    latex_table = _latex_table(rows, status_labels=status_labels, lang=lang)
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
    target_model = _pick_target_model(vars_map)
    target_region = _pick_target_region(vars_map)
    title = _copy_text(
        vars_map,
        "lcd_icons.page_title",
        lang=lang,
        target_model=target_model,
        target_region=target_region,
    )
    status_labels = _status_labels(vars_map, lang=lang)
    rows = _collect_rows(blocks, lang=lang, vars_map=vars_map)
    rendered = template.replace(PH_LCD_ICONS_HEADING_RST, _heading(title))
    rendered = rendered.replace(PH_LCD_ICONS_IMAGE_ALT, rst_escape(title))
    rendered = rendered.replace(
        PH_LCD_ICONS_TABLE_RST,
        _table(rows, status_labels=status_labels, lang=lang),
    )
    return rendered
