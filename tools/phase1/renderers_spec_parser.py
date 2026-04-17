#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
from pathlib import Path
import re
from typing import cast

from .renderers_common import _enabled, _scope_allows, apply_vars, rst_escape
from ..utils.spec_master import (
    canonicalize_model_token,
    is_page_value_row,
    page_value_matches,
    source_language_for_row,
)


def _split_spec_row_text(text: str, block_id: str, line: str) -> tuple[str, str]:
    raw = rst_escape(text)
    if "||" not in raw:
        raise ValueError(
            f"spec row_item block_id='{block_id or '?'}' line {line or '?'} "
            "must use 'left || right' format"
        )
    left, right = raw.split("||", 1)
    left = left.strip()
    right = right.strip()
    if not left or not right:
        raise ValueError(
            f"spec row_item block_id='{block_id or '?'}' line {line or '?'} "
            "has empty left or right cell"
        )
    return left, right


def _to_float(value: str, default: float = 0.0) -> float:
    try:
        return float((value or "").strip())
    except Exception:
        return default


def _first_non_empty(row: dict[str, str], keys: list[str]) -> str:
    for key in keys:
        if key not in row:
            continue
        value = rst_escape(row.get(key) or "")
        if value:
            return value
    return ""


def _is_enabled_row(row: dict[str, str]) -> bool:
    if "enabled" in row:
        return _enabled(row.get("enabled", "1"))
    if "Enabled" in row:
        return _enabled(row.get("Enabled", "1"))
    return True


def _is_latest_row(row: dict[str, str]) -> bool:
    if "Is_Latest" in row:
        return _enabled(row.get("Is_Latest", "1"))
    if "is_latest" in row:
        return _enabled(row.get("is_latest", "1"))
    return True


def _looks_like_spec_master_schema(blocks: list[dict[str, str]]) -> bool:
    if not blocks:
        return False
    headers = set(blocks[0].keys())
    if "block_type" in headers:
        return False
    required = {"Section", "Row_key", "Line_order"}
    return required.issubset(headers)


def _pick_spec_lang_text(
    row: dict[str, str],
    *,
    base: str,
    lang: str,
    default_keys: list[str] | None = None,
) -> str:
    source_lang = source_language_for_row(row)
    normalized_lang = (lang or "").strip().lower()
    if base in {"Row_label", "Param", "Value"} and (normalized_lang == "en" or (source_lang and normalized_lang == source_lang)):
        keys = [
            f"{base}_source",
            f"{base.lower()}_source",
            base,
        ]
    else:
        keys = [
            f"{base}_{lang}",
            f"{base}_{lang.lower()}",
            f"{base}_{lang.upper()}",
            f"{base}_source",
            f"{base.lower()}_source",
            base,
        ]
    if default_keys:
        keys.extend(default_keys)
    return _first_non_empty(row, keys)


def _pick_title_lang(lang: str, vars_map: dict[str, str]) -> str:
    explicit = _first_non_empty(vars_map, ["title_lang", "spec_title_lang", "language"])
    if explicit:
        value = explicit.strip().lower()
    else:
        region = _first_non_empty(vars_map, ["region", "Region"]).strip().upper()
        if region in {"JP", "JAPAN"}:
            value = "jp"
        elif region in {"CN", "CHINA", "ZH"}:
            value = "zh"
        else:
            value = (lang or "").strip().lower()

    if value in {"ja", "jp"}:
        return "jp"
    if value.startswith("fr"):
        return "fr"
    if value.startswith("es"):
        return "es"
    if value.startswith("zh"):
        return "zh"
    return "en"


_CIRCLED_NUMBER_MARKERS: dict[int, str] = {
    1: "\u2460",
    2: "\u2461",
    3: "\u2462",
    4: "\u2463",
    5: "\u2464",
    6: "\u2465",
    7: "\u2466",
    8: "\u2467",
    9: "\u2468",
    10: "\u2469",
}
_LEGACY_FOOTNOTE_PREFIX_RE = re.compile(r"^(?:[\u2460-\u2473]|\(\d+\)|\d+\.)\s*")


def _footnote_marker_for_order(order: float) -> str:
    normalized = int(order)
    if normalized <= 0:
        return ""
    return _CIRCLED_NUMBER_MARKERS.get(normalized, f"({normalized})")


def _parse_footnote_refs(value: str) -> list[str]:
    refs: list[str] = []
    for token in (value or "").split(","):
        item = token.strip()
        if item and item not in refs:
            refs.append(item)
    return refs


def _append_footnote_markers(text: str, refs: list[str], marker_by_id: dict[str, str]) -> str:
    if not text:
        return text
    markers = "".join(marker_by_id.get(ref, "") for ref in refs if marker_by_id.get(ref, ""))
    if not markers:
        return text
    return f"{text}{markers}"


def _strip_legacy_footnote_prefix(text: str) -> str:
    return _LEGACY_FOOTNOTE_PREFIX_RE.sub("", text or "", count=1).strip()


def _load_spec_title_metadata(
    csv_path: Path,
    *,
    title_lang: str,
) -> tuple[dict[str, str], dict[str, float]]:
    if not csv_path.exists():
        return {}, {}
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return {}, {}

    target_col = f"title_{title_lang}"
    title_map: dict[str, str] = {}
    section_order_map: dict[str, float] = {}
    for row in rows:
        key = rst_escape(row.get("title_en") or "")
        if not key:
            continue

        value = rst_escape(row.get(target_col) or "")
        if not value:
            value = key
        title_map[key.lower()] = value

        raw_section_order = rst_escape(row.get("section_order") or row.get("Section_order") or "")
        if raw_section_order:
            section_order_map[key.lower()] = _to_float(raw_section_order)
    return title_map, section_order_map


def _load_spec_title_map(csv_path: Path, *, title_lang: str) -> dict[str, str]:
    title_map, _section_order_map = _load_spec_title_metadata(csv_path, title_lang=title_lang)
    return title_map


def _apply_spec_title_map(title: str, title_map: dict[str, str]) -> str:
    raw = rst_escape(title)
    if not raw:
        return raw
    return title_map.get(raw.lower(), raw)


def _parse_spec_master_sections(
    blocks: list[dict[str, str]],
    *,
    sku_id: str,
    lang: str,
    vars_map: dict[str, str],
) -> tuple[str, list[dict[str, object]], list[str], list[str]]:
    rows: list[dict[str, object]] = []
    notes: list[tuple[float, str]] = []
    footnotes: list[tuple[float, str]] = []
    footnote_defs: list[tuple[float, str, str]] = []
    title_candidates: list[tuple[float, str]] = []
    section_title_overrides: dict[str, str] = {}

    var_region = _first_non_empty(vars_map, ["region", "Region"])
    raw_var_model = _first_non_empty(vars_map, ["model", "product_model", "model_no", "Model"])
    var_model = canonicalize_model_token(raw_var_model, region=var_region)
    target_sku = _first_non_empty(vars_map, ["sku_id", "sku"]) or rst_escape(sku_id)
    title_map: dict[str, str] = {}
    section_order_map: dict[str, float] = {}
    spec_titles_cfg = _first_non_empty(vars_map, ["spec_titles_csv"])
    if spec_titles_cfg:
        title_map, section_order_map = _load_spec_title_metadata(
            Path(spec_titles_cfg),
            title_lang=_pick_title_lang(lang, vars_map),
        )

    for idx, raw in enumerate(blocks):
        row = dict(raw)
        overflow = row.get(None)
        if isinstance(overflow, list) and any(str(x).strip() for x in overflow):
            line = (row.get("__line__") or str(idx + 2)).strip()
            raise ValueError(
                f"Spec_Master CSV line {line} has unquoted commas in a field. "
                "Quote the full cell value (e.g. Value_source=\"A, B, C\")."
            )

        if not _is_enabled_row(row):
            continue
        if not _is_latest_row(row):
            continue

        if target_sku and "sku_scope" in row and not _scope_allows(row.get("sku_scope", "ALL"), target_sku):
            continue
        if target_sku and "sku_id" in row:
            row_sku = rst_escape(row.get("sku_id") or "")
            if row_sku and row_sku != target_sku:
                continue

        row_region = _first_non_empty(row, ["Region", "region"])
        if var_region and row_region and row_region != var_region:
            continue
        row_model = _first_non_empty(
            row,
            ["Model", "model", "Product_Model", "product_model", "Model_No", "model_no"],
        )
        row_model = canonicalize_model_token(row_model, region=row_region or var_region)
        if var_model and row_model and row_model.casefold() != var_model.casefold():
            continue

        page_value = _first_non_empty(row, ["Page", "page"])
        if not page_value_matches(page_value, ("spec", "specifications")):
            continue

        footnote_id = _first_non_empty(row, ["Footnote_id", "footnote_id"])
        note_id = _first_non_empty(row, ["Note_id", "note_id"])
        row_kind = _first_non_empty(row, ["row_kind", "Row_kind", "kind"]).lower()
        if not row_kind:
            if footnote_id:
                row_kind = "footnote"
            elif note_id:
                row_kind = "note"
            else:
                row_kind = "data"
        base_order = _to_float(_first_non_empty(row, ["row_order", "Row_order"]), idx)
        title_text = _pick_spec_lang_text(
            row,
            base="page_title",
            lang=lang,
            default_keys=["title_main", "Title_main"],
        )
        if title_text:
            title_candidates.append((base_order, apply_vars(title_text, vars_map)))

        section_key_for_title = _first_non_empty(row, ["Section", "section"])
        section_title_for_title = _pick_spec_lang_text(
            row,
            base="section_title",
            lang=lang,
            default_keys=[f"Section_{lang}", "Section_en", "Section"],
        )
        if (
            section_key_for_title
            and section_title_for_title
            and row_kind in {"title", "section_title", "title_map"}
        ):
            section_title_overrides[section_key_for_title] = apply_vars(
                section_title_for_title,
                vars_map,
            )

        note_text = _pick_spec_lang_text(
            row,
            base="note_text",
            lang=lang,
            default_keys=["note", "Note"],
        )
        if note_text and row_kind in {"note", "data"}:
            note_order = _to_float(_first_non_empty(row, ["note_order", "Note_order"]), base_order)
            notes.append((note_order, apply_vars(note_text, vars_map)))

        footnote_mark = _first_non_empty(row, ["footnote_mark", "Footnote_mark"])
        footnote_text = _pick_spec_lang_text(
            row,
            base="footnote_text",
            lang=lang,
            default_keys=["footnote", "Footnote"],
        )
        if footnote_text and row_kind in {"footnote", "data"}:
            footnote_order = _to_float(
                _first_non_empty(row, ["footnote_order", "Footnote_order"]),
                base_order,
            )
            if footnote_id:
                footnote_defs.append(
                    (
                        footnote_order,
                        footnote_id,
                        apply_vars(_strip_legacy_footnote_prefix(footnote_text), vars_map),
                    )
                )
            else:
                footnotes.append(
                    (
                        footnote_order,
                        apply_vars(f"{footnote_mark}{footnote_text}", vars_map),
                    )
                )

        if row_kind in {"note", "footnote", "title"}:
            continue

        section_key = _first_non_empty(row, ["Section", "section"])
        row_key = _first_non_empty(row, ["Row_key", "row_key"])
        if not section_key or not row_key:
            continue
        if is_page_value_row(row) or section_key.strip().lower() == "template vars":
            continue

        section_title = _pick_spec_lang_text(
            row,
            base="section_title",
            lang=lang,
            default_keys=[f"Section_{lang}", "Section_en", "Section"],
        )
        section_order = _to_float(
            _first_non_empty(row, ["Section_order", "section_order"]),
            section_order_map.get(section_key.strip().lower(), 99.0),
        )
        row_order = _to_float(_first_non_empty(row, ["row_order", "Row_order"]), idx)
        line_order = _to_float(_first_non_empty(row, ["Line_order", "line_order"]), 1.0)

        row_label = _pick_spec_lang_text(
            row,
            base="Row_label",
            lang=lang,
            default_keys=["Row_label_source", "Row_key"],
        )
        explicit_line_text = _pick_spec_lang_text(
            row,
            base="line_text",
            lang=lang,
            default_keys=[],
        )
        param_text = _pick_spec_lang_text(
            row,
            base="Param",
            lang=lang,
            default_keys=["Param_source", "Param_name"],
        )
        value_text = _pick_spec_lang_text(
            row,
            base="Value",
            lang=lang,
            default_keys=["Value_source", "Spec_Value"],
        )
        if not row_label or (not explicit_line_text and not param_text and not value_text):
            continue

        row_label_refs = _parse_footnote_refs(
            _first_non_empty(row, ["Row_label_footnote_refs", "row_label_footnote_refs"])
        )
        param_refs = _parse_footnote_refs(
            _first_non_empty(row, ["Param_footnote_refs", "param_footnote_refs"])
        )
        value_refs = _parse_footnote_refs(
            _first_non_empty(row, ["Value_footnote_refs", "value_footnote_refs"])
        )
        sep = _pick_spec_lang_text(
            row,
            base="param_value_sep",
            lang=lang,
            default_keys=["param_value_sep"],
        ) or ": "
        if sep == ":":
            sep = ": "

        rows.append(
            {
                "section_key": section_key,
                "section_title": apply_vars(section_title, vars_map),
                "section_order": section_order,
                "row_key": row_key,
                "row_label": apply_vars(row_label, vars_map),
                "row_order": row_order,
                "line_order": line_order,
                "line_text": apply_vars(explicit_line_text, vars_map),
                "param_text": apply_vars(param_text, vars_map),
                "value_text": apply_vars(value_text, vars_map),
                "param_value_sep": apply_vars(sep, vars_map),
                "row_label_refs": row_label_refs,
                "param_refs": param_refs,
                "value_refs": value_refs,
                "source_order": idx,
            }
        )

    if section_title_overrides:
        for row in rows:
            key = str(row.get("section_key") or "")
            if key in section_title_overrides:
                row["section_title"] = section_title_overrides[key]

    footnote_marker_by_id = {
        footnote_id: _footnote_marker_for_order(order)
        for order, footnote_id, _text in sorted(footnote_defs, key=lambda item: item[0])
    }

    if not rows:
        model_msg = f" model={raw_var_model}" if raw_var_model else ""
        raise ValueError(
            f"spec page has no usable Spec_Master rows for sku={sku_id} lang={lang}{model_msg}"
        )

    section_dict: dict[str, dict[str, object]] = {}
    for row in sorted(rows, key=lambda x: (x["section_order"], x["source_order"])):
        section_key = str(row["section_key"])
        section = section_dict.setdefault(
            section_key,
            {
                "title": row["section_title"] or row["section_key"],
                "order": row["section_order"],
                "rows": {},
                "source_order": row["source_order"],
            },
        )
        rows_map = section["rows"]
        assert isinstance(rows_map, dict)
        row_key = str(row["row_key"])
        item = rows_map.setdefault(
            row_key,
            {
                "label": row["row_label"],
                "label_refs": row["row_label_refs"],
                "order": row["row_order"],
                "source_order": row["source_order"],
                "lines": [],
            },
        )
        lines = item["lines"]
        assert isinstance(lines, list)
        lines.append(
            (
                float(row["line_order"]),
                int(row["source_order"]),
                str(row["line_text"]),
                str(row["param_text"]),
                str(row["value_text"]),
                str(row["param_value_sep"]),
                cast(list[str], row["param_refs"]),
                cast(list[str], row["value_refs"]),
            )
        )

    sections: list[dict[str, object]] = []
    for section in sorted(
        section_dict.values(),
        key=lambda x: (float(x["order"]), int(x["source_order"])),
    ):
        rows_map = section["rows"]
        assert isinstance(rows_map, dict)
        out_rows: list[tuple[str, str]] = []
        for row in sorted(
            rows_map.values(),
            key=lambda x: (float(x["order"]), int(x["source_order"])),
        ):
            lines = row["lines"]
            assert isinstance(lines, list)
            lines_sorted: list[str] = []
            for _line_order, _source_order, explicit_line_text, param_text, value_text, sep, param_refs, value_refs in sorted(
                lines,
                key=lambda t: (t[0], t[1]),
            ):
                if explicit_line_text:
                    combined_refs = list(dict.fromkeys([*param_refs, *value_refs]))
                    lines_sorted.append(
                        _append_footnote_markers(explicit_line_text, combined_refs, footnote_marker_by_id)
                    )
                    continue

                param_with_markers = _append_footnote_markers(param_text, param_refs, footnote_marker_by_id)
                value_with_markers = _append_footnote_markers(value_text, value_refs, footnote_marker_by_id)
                if param_with_markers and value_with_markers:
                    lines_sorted.append(f"{param_with_markers}{sep}{value_with_markers}")
                else:
                    lines_sorted.append(value_with_markers or param_with_markers)

            label_text = _append_footnote_markers(
                str(row["label"]),
                cast(list[str], row.get("label_refs") or []),
                footnote_marker_by_id,
            )
            out_rows.append((label_text, "\n".join(lines_sorted)))
        sections.append({"title": str(section["title"]), "rows": out_rows})

    notes_text = [x[1] for x in sorted(notes, key=lambda t: t[0])]
    generated_footnotes = [
        (order, f"{_footnote_marker_for_order(order)} {text}".strip())
        for order, _footnote_id, text in sorted(footnote_defs, key=lambda item: item[0])
    ]
    footnotes_text = [x[1] for x in sorted([*footnotes, *generated_footnotes], key=lambda t: t[0])]

    if title_candidates:
        title_main = sorted(title_candidates, key=lambda t: t[0])[0][1]
    elif lang == "fr":
        title_main = "SPÉCIFICATIONS"
    elif lang in {"ja", "jp"}:
        title_main = "主な仕様"
    else:
        title_main = "SPECIFICATIONS"

    if title_map:
        title_main = _apply_spec_title_map(title_main, title_map)
        for sec in sections:
            sec["title"] = _apply_spec_title_map(str(sec.get("title") or ""), title_map)

    return title_main, sections, notes_text, footnotes_text


def collect_spec_content(
    blocks: list[dict[str, str]],
    sku_id: str,
    lang: str,
    vars_map: dict[str, str],
) -> dict[str, object]:
    if not blocks:
        raise ValueError(f"spec page has no blocks for sku={sku_id} lang={lang}")

    if _looks_like_spec_master_schema(blocks):
        title_main, sections, notes, footnotes = _parse_spec_master_sections(
            blocks,
            sku_id=sku_id,
            lang=lang,
            vars_map=vars_map,
        )
        return {
            "title_main": title_main,
            "sections": sections,
            "notes": notes,
            "footnotes": footnotes,
        }

    lang_col = f"text_{lang}"
    if lang_col not in blocks[0]:
        raise ValueError(f"content csv missing language column: {lang_col}")

    use: list[dict[str, str]] = []
    for b in blocks:
        if not _enabled(b.get("enabled", "1")):
            continue
        if not _scope_allows(b.get("sku_scope", "ALL"), sku_id):
            continue
        txt = apply_vars(b.get(lang_col, "") or "", vars_map)
        if txt.strip() == "":
            continue
        use.append(
            {
                "block_type": (b.get("block_type") or "").strip(),
                "order": (b.get("order") or "").strip(),
                "text": txt,
                "block_id": (b.get("block_id") or "").strip(),
                "line": (b.get("__line__") or "").strip(),
            }
        )

    if not use:
        raise ValueError(f"spec page has no enabled blocks for sku={sku_id} lang={lang}")

    def sort_key(r: dict[str, str]) -> float:
        try:
            return float(r.get("order") or "0")
        except ValueError:
            return 0.0

    def pick(block_type: str) -> str:
        for r in sorted(use, key=sort_key):
            if r["block_type"] == block_type:
                return r["text"]
        raise ValueError(f"Missing required block_type='{block_type}' sku={sku_id} lang={lang}")

    sections: list[dict[str, object]] = []
    notes: list[str] = []
    footnotes: list[str] = []
    current_section: dict[str, object] | None = None

    for r in sorted(use, key=sort_key):
        bt = r["block_type"]
        if bt in {"title_main"}:
            continue
        if bt == "section_title":
            current_section = {"title": r["text"], "rows": []}
            sections.append(current_section)
            continue
        if bt == "row_item":
            if current_section is None:
                raise ValueError(
                    f"spec row_item appears before section_title "
                    f"(block_id='{r.get('block_id') or '?'}' line {r.get('line') or '?'})"
                )
            left, right = _split_spec_row_text(
                r["text"], r.get("block_id") or "?", r.get("line") or "?"
            )
            rows = current_section.get("rows")
            assert isinstance(rows, list)
            rows.append((left, right))
            continue
        if bt == "note_line":
            notes.append(r["text"])
            continue
        if bt == "footnote":
            footnotes.append(r["text"])
            continue

    if not sections:
        raise ValueError(f"spec page has no section_title blocks sku={sku_id} lang={lang}")

    return {
        "title_main": pick("title_main"),
        "sections": sections,
        "notes": notes,
        "footnotes": footnotes,
    }
