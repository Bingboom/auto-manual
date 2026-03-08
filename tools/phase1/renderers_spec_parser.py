#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from .renderers_common import _enabled, _scope_allows, apply_vars, rst_escape


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
    keys = [
        f"{base}_{lang}",
        f"{base}_{lang.lower()}",
        f"{base}_{lang.upper()}",
        f"{base}_en",
        base,
    ]
    if default_keys:
        keys.extend(default_keys)
    return _first_non_empty(row, keys)


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
    title_candidates: list[tuple[float, str]] = []

    var_project_code = _first_non_empty(
        vars_map,
        ["project_code", "product_code", "项目代码", "product_id"],
    )
    var_region = _first_non_empty(vars_map, ["region", "Region"])
    var_model = _first_non_empty(vars_map, ["model", "product_model", "model_no", "Model"])
    target_sku = _first_non_empty(vars_map, ["sku_id", "sku"]) or rst_escape(sku_id)

    for idx, raw in enumerate(blocks):
        row = dict(raw)
        overflow = row.get(None)
        if isinstance(overflow, list) and any(str(x).strip() for x in overflow):
            line = (row.get("__line__") or str(idx + 2)).strip()
            raise ValueError(
                f"Spec_Master CSV line {line} has unquoted commas in a field. "
                "Quote the full cell value (e.g. Value_en=\"A, B, C\")."
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

        row_project = _first_non_empty(row, ["project_code", "项目代码"])
        if var_project_code and row_project and row_project != var_project_code:
            continue
        row_region = _first_non_empty(row, ["Region", "region"])
        if var_region and row_region and row_region != var_region:
            continue
        row_model = _first_non_empty(
            row,
            ["Model", "model", "Product_Model", "product_model", "Model_No", "model_no"],
        )
        if var_model and row_model and row_model != var_model:
            continue

        page_value = _first_non_empty(row, ["Page", "page"])
        if page_value and page_value.lower() not in {"spec", "specifications"}:
            continue

        row_kind = _first_non_empty(row, ["row_kind", "Row_kind", "kind"]).lower() or "data"
        base_order = _to_float(_first_non_empty(row, ["row_order", "Row_order"]), idx)
        title_text = _pick_spec_lang_text(
            row,
            base="page_title",
            lang=lang,
            default_keys=["title_main", "Title_main"],
        )
        if title_text:
            title_candidates.append((base_order, apply_vars(title_text, vars_map)))

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
        if footnote_mark and footnote_text and row_kind in {"footnote", "data"}:
            footnote_order = _to_float(
                _first_non_empty(row, ["footnote_order", "Footnote_order"]),
                base_order,
            )
            footnotes.append((footnote_order, apply_vars(f"{footnote_mark}{footnote_text}", vars_map)))

        if row_kind in {"note", "footnote", "title"}:
            continue

        section_key = _first_non_empty(row, ["Section", "section"])
        row_key = _first_non_empty(row, ["Row_key", "row_key"])
        if not section_key or not row_key:
            continue

        section_title = _pick_spec_lang_text(
            row,
            base="section_title",
            lang=lang,
            default_keys=[f"Section_{lang}", "Section_en", "Section"],
        )
        section_order = _to_float(_first_non_empty(row, ["Section_order", "section_order"]), 99.0)
        row_order = _to_float(_first_non_empty(row, ["row_order", "Row_order"]), idx)
        line_order = _to_float(_first_non_empty(row, ["Line_order", "line_order"]), 1.0)

        row_label = _pick_spec_lang_text(
            row,
            base="Row_label",
            lang=lang,
            default_keys=["Row_label_en", "Row_key"],
        )
        line_text = _pick_spec_lang_text(
            row,
            base="line_text",
            lang=lang,
            default_keys=[],
        )
        if not line_text:
            param = _pick_spec_lang_text(
                row,
                base="Param",
                lang=lang,
                default_keys=["Param_en", "Param_name"],
            )
            value = _pick_spec_lang_text(
                row,
                base="Value",
                lang=lang,
                default_keys=["Value_en", "Spec_Value"],
            )
            sep = _pick_spec_lang_text(
                row,
                base="param_value_sep",
                lang=lang,
                default_keys=["param_value_sep"],
            ) or ": "
            if sep == ":":
                sep = ": "
            if param and value:
                line_text = f"{param}{sep}{value}"
            else:
                line_text = value or param

        if not row_label or not line_text:
            continue

        rows.append(
            {
                "section_key": section_key,
                "section_title": apply_vars(section_title, vars_map),
                "section_order": section_order,
                "row_key": row_key,
                "row_label": apply_vars(row_label, vars_map),
                "row_order": row_order,
                "line_order": line_order,
                "line_text": apply_vars(line_text, vars_map),
                "source_order": idx,
            }
        )

    if not rows:
        model_msg = f" model={var_model}" if var_model else ""
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
                "order": row["row_order"],
                "source_order": row["source_order"],
                "lines": [],
            },
        )
        lines = item["lines"]
        assert isinstance(lines, list)
        lines.append((float(row["line_order"]), int(row["source_order"]), str(row["line_text"])))

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
            lines_sorted = [x[2] for x in sorted(lines, key=lambda t: (t[0], t[1]))]
            out_rows.append((str(row["label"]), "\n".join(lines_sorted)))
        sections.append({"title": str(section["title"]), "rows": out_rows})

    notes_text = [x[1] for x in sorted(notes, key=lambda t: t[0])]
    footnotes_text = [x[1] for x in sorted(footnotes, key=lambda t: t[0])]

    title_main = (
        sorted(title_candidates, key=lambda t: t[0])[0][1]
        if title_candidates
        else ("SPÉCIFICATIONS" if lang == "fr" else "SPECIFICATIONS")
    )
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
