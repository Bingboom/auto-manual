#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import html
import re
from dataclasses import dataclass
from pathlib import Path

from .renderers_common import _enabled, _scope_allows, apply_vars, latex_arg_escape, rst_escape
from ..localized_copy import LocalizedCopyResolver
from ..utils.spec_master import canonicalize_model_token
from ..utils.variable_resolver import parse_model_tokens

PH_SYMBOLS_SIGNAL_SECTION_RST = "{{ symbols_signal_section_rst }}"
PH_SYMBOLS_ICON_TABLE_RST = "{{ symbols_icon_table_rst }}"

_TRUE_VALUES = {"1", "true", "yes", "y"}
_FALSE_VALUES = {"0", "false", "no", "n"}
_GLOBAL_MARKET_TOKENS = {"all", "global"}


@dataclass(frozen=True)
class SymbolAsset:
    path: str
    width: str = "40px"


SYMBOL_ASSETS: dict[str, SymbolAsset] = {
    "warning_triangle": SymbolAsset(
        path="templates/word_template/common_assets/symbols/warning_triangle.png",
    ),
    "read_manual": SymbolAsset(
        path="templates/word_template/common_assets/symbols/read_manual_operator.png",
    ),
    "electric_shock": SymbolAsset(
        path="templates/word_template/common_assets/symbols/electric_shock.png",
    ),
    "battery_charging": SymbolAsset(
        path="templates/word_template/common_assets/symbols/battery_charging.png",
    ),
    "explosive_material": SymbolAsset(
        path="templates/word_template/common_assets/symbols/explosive_material.png",
    ),
    "heavy_object": SymbolAsset(
        path="templates/word_template/common_assets/symbols/heavy_object.png",
    ),
    "do_not_dismantle": SymbolAsset(
        path="templates/word_template/common_assets/symbols/do_not_dismantle.png",
    ),
    "no_open_flame": SymbolAsset(
        path="templates/word_template/common_assets/symbols/no_open_flame.png",
    ),
    "keep_away_from_children": SymbolAsset(
        path="templates/word_template/common_assets/symbols/keep_away_from_children.png",
    ),
    "li_ion": SymbolAsset(
        path="templates/word_template/common_assets/symbols/li_ion.png",
    ),
    "weee": SymbolAsset(
        path="templates/word_template/common_assets/symbols/weee.png",
    ),
    "weee2": SymbolAsset(
        path="templates/word_template/common_assets/symbols/weee2.png",
    ),
}

DISPLAY_SIGNAL_ROW_KEYS = ("warning", "caution", "note", "tips")
SIGNAL_ROW_KEYS = (*DISPLAY_SIGNAL_ROW_KEYS, "danger")
SIGNAL_KEY_ALIASES = {"tip": "tips"}
SIGNAL_DEFAULT_ASSETS: dict[str, SymbolAsset] = {
    "warning": SymbolAsset(
        path="templates/word_template/common_assets/symbols/warning_triangle.png",
    ),
    "caution": SymbolAsset(
        path="templates/word_template/common_assets/symbols/warning_triangle.png",
    ),
    "note": SymbolAsset(
        path="templates/word_template/common_assets/symbols/mandatory.png",
    ),
    "tips": SymbolAsset(
        path="templates/word_template/common_assets/symbols/mandatory.png",
    ),
}
SUPPORTED_SYMBOL_BLOCK_TYPES = {"table_row", "signal_row"}


def _localized_copy_resolver(vars_map: dict[str, str]) -> LocalizedCopyResolver:
    path = (vars_map.get("localized_copy_csv") or "").strip()
    if not path:
        raise ValueError("symbols renderer requires localized_copy_csv")
    return LocalizedCopyResolver.from_csv(path)


def _copy_text(vars_map: dict[str, str], key: str, *, lang: str) -> str:
    return _localized_copy_resolver(vars_map).resolve(
        key,
        lang=lang,
        model=_pick_target_model(vars_map) or None,
        region=_pick_target_region(vars_map) or None,
    )


def _signal_copy_key(signal_key: str, copy_type: str) -> str:
    return f"symbols.signal.{signal_key}.{copy_type}"


def _text_column_for_lang(row: dict[str, str], lang: str) -> str:
    raw = (lang or "").strip()
    normalized = raw.casefold()
    source_lang = (row.get("Source_lang") or row.get("source_lang") or "").strip()
    aliases = {
        "ja": ("ja", "jp"),
        "jp": ("jp", "ja"),
        "pt-br": ("pt-BR", "br", "pt_br"),
        "pt_br": ("pt_BR", "pt-BR", "br"),
        "br": ("br", "pt-BR", "pt_br"),
        "uk": ("uk", "ukr"),
        "ukr": ("ukr", "uk"),
    }.get(normalized, (raw, normalized))
    candidates = [
        *(f"text_{token}" for token in aliases if token),
        f"text_{raw.replace('-', '_')}",
        f"text_{source_lang}",
        f"text_{source_lang.casefold()}",
        "text_en",
    ]
    for candidate in candidates:
        if candidate in row:
            return candidate
    return f"text_{raw}"


def _sort_key(row: dict[str, str]) -> float:
    try:
        return float(row.get("order") or "0")
    except ValueError:
        return 0.0


def _has_unique_explicit_orders(rows: list[dict[str, str]]) -> bool:
    orders = [(row.get("order") or "").strip() for row in rows]
    if any(not order for order in orders):
        return False
    return len({order.casefold() for order in orders}) == len(orders)


def _distribute_ordered_rows(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    ordered = sorted(rows, key=_sort_key)
    split_at = (len(ordered) + 1) // 2
    return {
        "left": ordered[:split_at],
        "right": ordered[split_at:],
    }


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


def _truthy(value: str, *, default: bool = True) -> bool:
    raw = (value or "").strip().casefold()
    if not raw:
        return default
    if raw in _TRUE_VALUES:
        return True
    if raw in _FALSE_VALUES:
        return False
    return default


def _split_condition_tokens(value: str) -> list[str]:
    raw = (value or "").strip()
    if not raw:
        return []
    if raw.startswith(("[", "{")):
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, list):
            tokens: list[str] = []
            for item in payload:
                if isinstance(item, dict):
                    item_value = item.get("text") or item.get("name") or item.get("value")
                else:
                    item_value = item
                token = str(item_value or "").strip()
                if token:
                    tokens.append(token)
            return tokens
    return [token for token in re.split(r"[,;|/\s\u3001\uff0c]+", raw) if token]


def _matches_market(block: dict[str, str], *, vars_map: dict[str, str]) -> bool:
    value = block.get("Market") or block.get("market") or block.get("Markets") or block.get("markets") or ""
    tokens = _split_condition_tokens(value)
    if not tokens:
        return False
    if any(token.casefold() in _GLOBAL_MARKET_TOKENS for token in tokens):
        return True
    target_region = _pick_target_region(vars_map)
    if not target_region:
        return False
    return any(token.casefold() == target_region.casefold() for token in tokens)


def _matches_symbols_model(block: dict[str, str], *, target_model: str, target_region: str) -> bool:
    model_value = block.get("Model") or block.get("model") or ""
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


def _matches_symbols_target(
    block: dict[str, str],
    *,
    sku_id: str,
    vars_map: dict[str, str],
) -> bool:
    target_region = _pick_target_region(vars_map)
    target_model = _pick_target_model(vars_map)
    model_tokens = parse_model_tokens(block.get("Model") or block.get("model") or "")

    if model_tokens:
        return _matches_symbols_model(block, target_model=target_model, target_region=target_region)

    return _scope_allows(block.get("sku_scope", "ALL"), sku_id)


def _rst_heading(title: str, underline: str = "-") -> list[str]:
    title = rst_escape(title)
    return [title, underline * len(title)]


def _append_text_cell(lines: list[str], prefix: str, text: str) -> None:
    raw_lines = [rst_escape(part) for part in (text or "").splitlines()]
    if not raw_lines:
        lines.append(prefix.rstrip())
        return
    lines.append(prefix + raw_lines[0])
    continuation = " " * len(prefix)
    for line in raw_lines[1:]:
        lines.append(continuation + line)


def _append_notice_table(
    lines: list[str],
    *,
    title: str,
    paragraphs: list[str],
    note_prefix: str = "- ",
) -> None:
    lines.extend(
        [
            ".. list-table::",
            "   :class: longtable",
            "   :header-rows: 0",
            "   :widths: 18 82",
            "",
            f"   * - **{rst_escape(title)}**",
        ]
    )

    if not paragraphs:
        lines.append("     -")
        return

    first = rst_escape(paragraphs[0])
    lines.append(f"     - {first}")

    for extra in paragraphs[1:]:
        text = rst_escape(extra)
        lines.append("")
        lines.append(f"       {note_prefix}{text}")


def _only_not_latex_block(block_lines: list[str]) -> list[str]:
    lines = [".. only:: not latex", ""]
    lines.extend(f"   {line}" if line else "" for line in block_lines)
    return lines


def _only_latex_raw_block(tex_lines: list[str]) -> list[str]:
    lines = [".. only:: latex", "", "   .. raw:: latex", ""]
    lines.extend(f"      {line}" if line else "      " for line in tex_lines)
    return lines


def _latex_image_name(image_path: str) -> str:
    return Path(image_path).name


def _latex_text_arg(text: str) -> str:
    parts = [latex_arg_escape(part) for part in (text or "").splitlines()]
    return r" \newline ".join(part for part in parts if part) or ""


def _notice_table_rst(
    *,
    title: str,
    paragraphs: list[str],
    note_prefix: str = "- ",
) -> list[str]:
    lines: list[str] = []
    _append_notice_table(lines, title=title, paragraphs=paragraphs, note_prefix=note_prefix)
    return lines


def _notice_block_latex(*, title: str, paragraphs: list[str]) -> list[str]:
    # LaTeX component contract, provided by the shared symbols component layer:
    # \HBNoticeBlock{title}{primary paragraph}{secondary paragraph}
    primary = _latex_text_arg(paragraphs[0]) if paragraphs else ""
    secondary = _latex_text_arg("\n".join(paragraphs[1:])) if len(paragraphs) > 1 else ""
    return _only_latex_raw_block(
        [
            rf"\HBNoticeBlock{{{latex_arg_escape(title)}}}{{{primary}}}{{{secondary}}}",
        ]
    )


def _append_image_cell(
    lines: list[str],
    prefix: str,
    *,
    image_path: str,
    alt: str,
    width: str,
    label: str | None = None,
) -> None:
    lines.append(prefix + f".. image:: {image_path}")
    lines.append(f"          :alt: {rst_escape(alt)}")
    lines.append(f"          :width: {width}")
    if label:
        lines.append("")
        lines.append(f"       **{rst_escape(label)}**")


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
            return f"data/phase2/_attachments/symbols/{file_token}{suffix}"
    return ""


def _symbol_block_type(block: dict[str, str]) -> str:
    block_type = (block.get("block_type") or "").strip()
    if block_type not in SUPPORTED_SYMBOL_BLOCK_TYPES:
        raise ValueError(
            "symbols page supports block_type='table_row' or block_type='signal_row', "
            f"got '{block_type or '?'}'"
        )
    return block_type


def _matching_symbol_blocks(
    blocks: list[dict[str, str]],
    *,
    block_type: str,
    sku_id: str,
    vars_map: dict[str, str],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for block in blocks:
        if not _enabled(block.get("enabled", "1")):
            continue
        is_latest = block.get("Is_Latest") or block.get("Is_latest") or block.get("is_latest") or ""
        if not _truthy(is_latest, default=True):
            continue
        if _symbol_block_type(block) != block_type:
            continue
        if _matches_market(block, vars_map=vars_map) and _matches_symbols_target(block, sku_id=sku_id, vars_map=vars_map):
            rows.append(block)
    return rows


def _normalize_signal_key(value: str) -> str:
    raw = (value or "").strip().casefold()
    raw = SIGNAL_KEY_ALIASES.get(raw, raw)
    if raw not in SIGNAL_ROW_KEYS:
        raise ValueError(f"unknown symbols signal_row symbol_key='{value or '?'}'")
    return raw


def _signal_lockup_html(label: str) -> str:
    escaped = html.escape(label)
    return (
        '<span class="hb-warning-lockup" '
        'style="display:inline-block; width:140px; box-sizing:border-box; '
        "background:#4a4a4a; color:#ffffff; padding:5px 8px; "
        'font-weight:700; line-height:1; white-space:nowrap;">'
        '<span aria-hidden="true" style="font-size:13px; margin-right:7px;">&#9888;</span>'
        f"<span>{escaped}</span>"
        "</span>"
    )


def _append_signal_lockup_cell(lines: list[str], prefix: str, label: str) -> None:
    lines.append(prefix + ".. raw:: html")
    lines.append("")
    lines.append("          " + _signal_lockup_html(label))


def _collect_signal_rows(
    blocks: list[dict[str, str]],
    *,
    sku_id: str,
    lang: str,
    vars_map: dict[str, str],
) -> list[dict[str, object]]:
    rows = _matching_symbol_blocks(
        blocks,
        block_type="signal_row",
        sku_id=sku_id,
        vars_map=vars_map,
    )
    if not rows:
        raise ValueError(f"symbols page has no matching signal_row data sku={sku_id} lang={lang}")
    if not _has_unique_explicit_orders(rows):
        raise ValueError(f"symbols signal rows require unique non-empty order values sku={sku_id} lang={lang}")

    ordered_rows = sorted(rows, key=_sort_key)
    keyed_rows = [(block, _normalize_signal_key(block.get("symbol_key") or "")) for block in ordered_rows]
    display_rows = [
        (block, signal_key)
        for block, signal_key in keyed_rows
        if signal_key in DISPLAY_SIGNAL_ROW_KEYS
    ]
    signal_keys = [signal_key for _block, signal_key in display_rows]
    if len(set(signal_keys)) != len(signal_keys):
        raise ValueError(f"symbols signal rows require unique symbol_key values sku={sku_id} lang={lang}")
    missing_keys = [signal_key for signal_key in DISPLAY_SIGNAL_ROW_KEYS if signal_key not in signal_keys]
    if missing_keys:
        missing = ", ".join(missing_keys)
        raise ValueError(f"symbols signal rows missing required symbol_key values: {missing}")

    signal_rows: list[dict[str, object]] = []
    for block, signal_key in display_rows:
        text = apply_vars(_copy_text(vars_map, _signal_copy_key(signal_key, "meaning"), lang=lang), vars_map)
        if not text.strip():
            raise ValueError(
                f"symbols signal copy is empty for key={signal_key} lang={lang} "
                f"at line {(block.get('__line__') or '?').strip()}"
            )

        default_asset = SIGNAL_DEFAULT_ASSETS[signal_key]
        image_path = _figure_image_path(block.get("Figure") or block.get("figure") or "")
        image_path = image_path or (block.get("image_path") or "").strip() or default_asset.path
        label = _copy_text(vars_map, _signal_copy_key(signal_key, "label"), lang=lang)
        signal_rows.append(
            {
                "mode": "signal_lockup",
                "image": image_path,
                "alt": label or signal_key,
                "width": "140px",
                "label": label,
                "meaning": text,
                "signal_key": signal_key,
            }
        )

    return signal_rows


def _signal_section(
    lang: str,
    vars_map: dict[str, str],
    signal_rows: list[dict[str, object]],
) -> str:
    page_title = _copy_text(vars_map, "symbols.page_title", lang=lang)
    header_symbol = _copy_text(vars_map, "symbols.header_symbol", lang=lang)
    header_meaning = _copy_text(vars_map, "symbols.header_meaning", lang=lang)

    lines: list[str] = []
    lines.extend(_rst_heading(page_title, "="))
    lines.append("")
    # LaTeX component contract:
    # \HBSymbolTable{symbol header}{meaning header}{row macro calls}
    # \HBSymbolSignalRow{image basename}{optional signal label}{meaning}
    signal_tex_rows = []
    for row in signal_rows:
        signal_tex_rows.append(
            rf"\HBSymbolSignalRow{{{_latex_image_name(str(row['image']))}}}"
            rf"{{{latex_arg_escape(str(row['label']))}}}{{{_latex_text_arg(str(row['meaning']))}}}"
        )
    lines.extend(
        _only_latex_raw_block(
            [
                rf"\HBSymbolTable{{{latex_arg_escape(header_symbol)}}}{{{latex_arg_escape(header_meaning)}}}{{%",
                *signal_tex_rows,
                "}",
            ]
        )
    )
    lines.append("")

    signal_table_lines: list[str] = [
        ".. list-table::",
        "   :class: longtable",
        "   :header-rows: 1",
        "   :widths: 22 78",
        "",
        f"   * - {header_symbol}",
        f"     - {header_meaning}",
    ]

    for row in signal_rows:
        _append_signal_lockup_cell(
            signal_table_lines,
            "   * - ",
            str(row["label"]),
        )
        _append_text_cell(signal_table_lines, "     - ", str(row["meaning"]))

    lines.extend(_only_not_latex_block(signal_table_lines))

    return "\n".join(lines) + "\n"


def _collect_icon_rows(
    blocks: list[dict[str, str]],
    *,
    sku_id: str,
    lang: str,
    vars_map: dict[str, str],
) -> dict[str, list[dict[str, str]]]:
    if not blocks:
        raise ValueError(f"symbols page has no blocks for sku={sku_id} lang={lang}")
    lang_col = _text_column_for_lang(blocks[0], lang)
    if lang_col not in blocks[0]:
        raise ValueError(f"content csv missing language column: {lang_col}")

    rows: list[dict[str, str]] = []
    for block in _matching_symbol_blocks(
        blocks,
        block_type="table_row",
        sku_id=sku_id,
        vars_map=vars_map,
    ):
        text = apply_vars(block.get(lang_col, "") or "", vars_map)
        if not text.strip():
            raise ValueError(
                f"symbols row missing {lang_col} text at line {(block.get('__line__') or '?').strip()}"
            )

        symbol_key = (block.get("symbol_key") or "").strip()
        if not symbol_key:
            raise ValueError(
                f"symbols row missing symbol_key at line {(block.get('__line__') or '?').strip()}"
            )
        if symbol_key not in SYMBOL_ASSETS:
            raise ValueError(f"unknown symbols symbol_key='{symbol_key}'")
        # The JE-1000F US V2.0 master ends at the product-WEEE row. The
        # battery-WEEE2 notice belongs to the EU disposal set and must not
        # create a twelfth row or a continuation page in the US manual.
        if symbol_key == "weee2" and _pick_target_region(vars_map).casefold() == "us":
            continue
        asset = SYMBOL_ASSETS[symbol_key]
        image_path = _figure_image_path(block.get("Figure") or block.get("figure") or "")
        image_path = image_path or (block.get("image_path") or "").strip() or asset.path

        row = {
            "symbol_key": symbol_key,
            "image_path": image_path,
            "text": rst_escape(text),
            "order": (block.get("order") or "").strip(),
        }
        rows.append(row)

    if not rows:
        raise ValueError(f"symbols page has no matching rows sku={sku_id} lang={lang}")
    if not _has_unique_explicit_orders(rows):
        raise ValueError(f"symbols page requires unique non-empty order values sku={sku_id} lang={lang}")

    groups = _distribute_ordered_rows(rows)
    return groups


def _icon_table(lang: str, vars_map: dict[str, str], groups: dict[str, list[dict[str, str]]]) -> str:
    header_symbol = _copy_text(vars_map, "symbols.header_symbol", lang=lang)
    header_meaning = _copy_text(vars_map, "symbols.header_meaning", lang=lang)
    left_rows = groups["left"]
    right_rows = groups["right"]
    max_rows = max(len(left_rows), len(right_rows))

    # LaTeX component contract:
    # \HBSymbolTwoColumnTables{symbol header}{meaning header}{left rows}{right rows}
    # \HBSymbolIconRow{image basename}{meaning}
    def latex_rows(rows: list[dict[str, str]]) -> list[str]:
        return [
            rf"\HBSymbolIconRow{{{_latex_image_name(str(row['image_path']))}}}"
            rf"{{{_latex_text_arg(row['text'])}}}"
            for row in rows
        ]

    left_tex_rows = latex_rows(left_rows)
    right_tex_rows = latex_rows(right_rows)

    lines: list[str] = []
    if lang.casefold() in {"fr", "es"}:
        left_top, left_rest = left_tex_rows[:4], left_tex_rows[4:]
        right_top, right_rest = right_tex_rows[:4], right_tex_rows[4:]
        latex_component = [
            rf"\HBSymbolTwoColumnTablesSplit{{{latex_arg_escape(header_symbol)}}}"
            rf"{{{latex_arg_escape(header_meaning)}}}{{%",
            *left_top,
            "}{%",
            *right_top,
            "}{%",
            *left_rest,
            "}{%",
            *right_rest,
            "}",
        ]
    else:
        latex_component = [
            rf"\HBSymbolTwoColumnTables{{{latex_arg_escape(header_symbol)}}}"
            rf"{{{latex_arg_escape(header_meaning)}}}{{%",
            *left_tex_rows,
            "}{%",
            *right_tex_rows,
            "}",
        ]
    lines.extend(_only_latex_raw_block(latex_component))
    lines.append("")

    table_lines: list[str] = [
        ".. list-table::",
        "   :class: longtable",
        "   :header-rows: 0",
        "   :widths: 12 38 12 38",
        "",
        f"   * - **{header_symbol}**",
        f"     - **{header_meaning}**",
        f"     - **{header_symbol}**",
        f"     - **{header_meaning}**",
    ]

    for idx in range(max_rows):
        left = left_rows[idx] if idx < len(left_rows) else None
        right = right_rows[idx] if idx < len(right_rows) else None

        if left is not None:
            left_asset = SYMBOL_ASSETS[left["symbol_key"]]
            _append_image_cell(
                table_lines,
                "   * - ",
                image_path=str(left["image_path"]),
                alt=left["symbol_key"],
                width=left_asset.width,
            )
            _append_text_cell(table_lines, "     - ", left["text"])
        else:
            table_lines.append("   * -")
            table_lines.append("     -")

        if right is not None:
            right_asset = SYMBOL_ASSETS[right["symbol_key"]]
            _append_image_cell(
                table_lines,
                "     - ",
                image_path=str(right["image_path"]),
                alt=right["symbol_key"],
                width=right_asset.width,
            )
            _append_text_cell(table_lines, "     - ", right["text"])
        else:
            table_lines.append("     -")
            table_lines.append("     -")

    lines.extend(_only_not_latex_block(table_lines))

    return "\n".join(lines) + "\n"


def render_symbols_page(
    template: str,
    blocks: list[dict[str, str]],
    sku_id: str,
    lang: str,
    vars_map: dict[str, str],
) -> str:
    groups = _collect_icon_rows(blocks, sku_id=sku_id, lang=lang, vars_map=vars_map)
    signal_rows = _collect_signal_rows(blocks, sku_id=sku_id, lang=lang, vars_map=vars_map)
    rendered = template.replace(PH_SYMBOLS_SIGNAL_SECTION_RST, _signal_section(lang, vars_map, signal_rows))
    rendered = rendered.replace(PH_SYMBOLS_ICON_TABLE_RST, _icon_table(lang, vars_map, groups))
    return rendered
