#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import re
from typing import Callable

# Template placeholders (safety page)
PH_TITLE_MAIN = "{{ safety_title_main }}"
PH_WARNING_TITLE = "{{ safety_warning_title }}"
PH_TITLE_OPERATING = "{{ safety_title_operating }}"
PH_LEAD_TOP = "{{ safety_lead_top }}"
PH_SAVE_TITLE = "{{ safety_save_title }}"
PH_TOP = "{{ safety_top_items }}"
PH_BOTTOM = "{{ safety_bottom_items }}"

PH_TITLE_MAIN_HTML = "{{ safety_title_main_html }}"
PH_WARNING_TITLE_HTML = "{{ safety_warning_title_html }}"
PH_TITLE_OPERATING_HTML = "{{ safety_title_operating_html }}"
PH_LEAD_TOP_HTML = "{{ safety_lead_top_html }}"
PH_SAVE_TITLE_HTML = "{{ safety_save_title_html }}"
PH_TOP_HTML = "{{ safety_top_items_html }}"
PH_BOTTOM_HTML = "{{ safety_bottom_items_html }}"

# Template placeholders (spec page)
PH_SPEC_TITLE_MAIN = "{{ spec_title_main }}"
PH_SPEC_TITLE_MAIN_HTML = "{{ spec_title_main_html }}"
PH_SPEC_SECTIONS_LATEX = "{{ spec_sections_latex }}"
PH_SPEC_NOTES_LATEX = "{{ spec_notes_latex }}"
PH_SPEC_FOOTNOTES_LATEX = "{{ spec_footnotes_latex }}"
PH_SPEC_SECTIONS_HTML = "{{ spec_sections_html }}"
PH_SPEC_NOTES_HTML = "{{ spec_notes_html }}"
PH_SPEC_FOOTNOTES_HTML = "{{ spec_footnotes_html }}"

# Template placeholders (symbols page)
PH_SYMBOLS_CONTENT_LATEX = "{{ symbols_content_latex }}"

Renderer = Callable[[str, list[dict[str, str]], str, str, dict[str, str]], str]

VAR_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_\-]+)\s*\}\}")


def apply_vars(text: str, vars_map: dict[str, str]) -> str:
    def repl(m: re.Match[str]) -> str:
        key = m.group(1)
        return vars_map.get(key, m.group(0))

    return VAR_PATTERN.sub(repl, text or "")


def rst_escape(s: str) -> str:
    return (s or "").replace("\u00a0", " ").strip()


def latex_arg_escape(text: str) -> str:
    text = rst_escape(text)
    # Keep escaping centralized: all user-provided CSV text must be safe in LaTeX args.
    mapping = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "%": r"\%",
        "_": r"\_",
        "#": r"\#",
        "&": r"\&",
        "$": r"\$",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(mapping.get(ch, ch) for ch in text)


def html_escape(text: str) -> str:
    import html as _html

    return _html.escape(rst_escape(text), quote=True)


def render_latex_cmd(cmd: str, text: str) -> str:
    text = latex_arg_escape(text)
    return "\n".join(
        [
            ".. raw:: latex",
            "",
            f"      \\{cmd}{{{text}}}",
            "",
        ]
    )


def render_bullet_rst(text: str) -> str:
    """
    Supports '\\n' in CSV.
    Sub-lines starting with '- ' become nested bullets.
    """
    text = rst_escape(text)
    parts = text.split("\\n")
    head = parts[0].strip()
    lines = [f"- {head}"]
    for p in parts[1:]:
        p = p.strip()
        if not p:
            continue
        if p.startswith("- "):
            lines.append(f"  {p}")
        else:
            lines.append(f"  {p}")
    return "\n".join(lines)


def build_list_block(rows: list[dict[str, str]]) -> str:
    lines = ("\n".join(render_bullet_rst(r["text"]) for r in rows)).splitlines()
    if not lines:
        return "\n"

    # The template already contributes three spaces before the placeholder.
    # Keep the first list line unindented here, then indent all following lines.
    first, *rest = lines
    normalized = [first]
    for line in rest:
        normalized.append(("   " + line) if line.strip() else line)
    return "\n".join(normalized) + "\n"


def render_lead_html(text: str) -> str:
    return f'<p class="hb-lead">{html_escape(text)}</p>'


def render_list_html(rows: list[dict[str, str]]) -> str:
    items: list[str] = []
    for r in rows:
        raw = rst_escape(r["text"])
        parts = raw.split("\\n")
        head = html_escape(parts[0])
        li_lines = [head]
        sub_items = []
        for p in parts[1:]:
            p = p.strip()
            if not p:
                continue
            if p.startswith("- "):
                sub_items.append(f"<li>{html_escape(p[2:])}</li>")
            else:
                li_lines.append(html_escape(p))
        li_html = "<br/>".join(li_lines)
        if sub_items:
            li_html += '<ul class="hb-sublist">' + "".join(sub_items) + "</ul>"
        items.append(f"<li>{li_html}</li>")
    return '<ul class="hb-list">' + "".join(items) + "</ul>"


def _enabled(v: str) -> bool:
    return (v or "1").strip().lower() in {"1", "true"}


def _scope_allows(scope: str, sku_id: str) -> bool:
    value = (scope or "").strip()
    if not value or value.upper() == "ALL":
        return True
    allowed = {x.strip() for x in value.split("|") if x.strip()}
    return sku_id in allowed


def collect_safety_content(
    blocks: list[dict[str, str]],
    sku_id: str,
    lang: str,
    vars_map: dict[str, str],
) -> dict[str, object]:
    lang_col = f"text_{lang}"
    if not blocks:
        raise ValueError(f"safety page has no blocks for sku={sku_id} lang={lang}")
    if lang_col not in blocks[0]:
        raise ValueError(f"content_blocks.csv missing language column: {lang_col}")

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
                "meta": b.get("meta_json") or "{}",
                "block_id": (b.get("block_id") or "").strip(),
                "line": (b.get("__line__") or "").strip(),
            }
        )

    if not use:
        raise ValueError(f"safety page has no enabled blocks for sku={sku_id} lang={lang}")

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

    def list_items(part: str) -> list[str]:
        out: list[str] = []
        for r in sorted(use, key=sort_key):
            if r["block_type"] != "list_item":
                continue
            try:
                meta = json.loads(r["meta"] or "{}")
            except Exception as exc:
                block_id = (r.get("block_id") or "").strip() or "?"
                line = (r.get("line") or "").strip() or "?"
                raise ValueError(
                    f"Invalid meta_json for block_id='{block_id}' line {line}: {exc}"
                ) from exc
            if (meta.get("list_part") or "").strip().lower() == part:
                out.append(r["text"])
        if not out:
            raise ValueError(f"No list items for list_part='{part}' sku={sku_id} lang={lang}")
        return out

    return {
        "title_main": pick("title_main"),
        "warning_title": pick("warning_title"),
        "title_operating": pick("title_operating"),
        "lead_top": pick("lead_top"),
        "save_title": pick("save_title"),
        "top_items": list_items("top"),
        "bottom_items": list_items("bottom"),
    }


def render_safety_page(
    template: str,
    blocks: list[dict[str, str]],
    sku_id: str,
    lang: str,
    vars_map: dict[str, str],
) -> str:
    data = collect_safety_content(blocks, sku_id, lang, vars_map)
    title_main = str(data["title_main"])
    warning_title = str(data["warning_title"])
    title_operating = str(data["title_operating"])
    lead_top = str(data["lead_top"])
    save_title = str(data["save_title"])
    top_rows = [{"text": str(item)} for item in data["top_items"]]
    bottom_rows = [{"text": str(item)} for item in data["bottom_items"]]

    title_main_line = rf"\section{{{latex_arg_escape(title_main)}}}"
    warning_line = rf"\safetywarning{{{latex_arg_escape(warning_title)}}}"
    title_oper_line = rf"\safetysubbar{{{latex_arg_escape(title_operating)}}}"

    lead_latex = render_latex_cmd("safetylead", lead_top)
    save_latex = render_latex_cmd("safetylead", save_title)

    top_rst = build_list_block(top_rows)
    bottom_rst = build_list_block(bottom_rows)

    title_main_html = html_escape(title_main)
    warning_html = html_escape(warning_title)
    title_oper_html = html_escape(title_operating)

    lead_html = render_lead_html(lead_top)
    save_html = render_lead_html(save_title)
    top_html = render_list_html(top_rows)
    bottom_html = render_list_html(bottom_rows)

    return (
        template.replace(PH_TITLE_MAIN, title_main_line)
        .replace(PH_WARNING_TITLE, warning_line)
        .replace(PH_TITLE_OPERATING, title_oper_line)
        .replace(PH_LEAD_TOP, lead_latex)
        .replace(PH_SAVE_TITLE, save_latex)
        .replace(PH_TOP, top_rst)
        .replace(PH_BOTTOM, bottom_rst)
        .replace(PH_TITLE_MAIN_HTML, title_main_html)
        .replace(PH_WARNING_TITLE_HTML, warning_html)
        .replace(PH_TITLE_OPERATING_HTML, title_oper_html)
        .replace(PH_LEAD_TOP_HTML, lead_html)
        .replace(PH_SAVE_TITLE_HTML, save_html)
        .replace(PH_TOP_HTML, top_html)
        .replace(PH_BOTTOM_HTML, bottom_html)
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


def _split_spec_lines(text: str) -> list[str]:
    raw = rst_escape(text).replace("\\n", "\n")
    parts = [rst_escape(x) for x in raw.splitlines() if rst_escape(x)]
    return parts or [""]


def _spec_latex_escape(text: str) -> str:
    # Keep special glyphs renderable on environments where brand fonts miss unicode glyphs.
    special = {
        "\u2460": r"\HBSpecMarkerOne{}",
        "\u2461": r"\HBSpecMarkerTwo{}",
        "*": r"\HBSpecMarkerAsterisk{}",
    }
    base = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "%": r"\%",
        "_": r"\_",
        "#": r"\#",
        "&": r"\&",
        "$": r"\$",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    out: list[str] = []
    for ch in rst_escape(text):
        if ch in special:
            out.append(special[ch])
        else:
            out.append(base.get(ch, ch))
    return "".join(out)


def _spec_latex_cell(text: str) -> str:
    parts = _split_spec_lines(text)
    escaped = [_spec_latex_escape(x) for x in parts if x]
    return r" \newline ".join(escaped) if escaped else ""


def _raw_latex_block(lines: list[str]) -> str:
    body = "\n".join(f"   {x}" if x else "   " for x in lines)
    return f".. raw:: latex\n\n{body}\n\n"


def _indent_block(text: str, spaces: int = 3) -> str:
    if not text:
        return ""
    prefix = " " * spaces
    return "\n".join(prefix + line for line in text.splitlines())


def _render_spec_sections_latex(
    sections: list[dict[str, object]],
) -> str:
    blocks: list[str] = []
    for sec in sections:
        title = rst_escape(str(sec.get("title") or ""))
        rows = sec.get("rows") or []
        tex_lines: list[str] = [
            rf"\specsectiontitle{{{_spec_latex_escape(title)}}}",
            r"\begin{spectable}",
            r"\noindent\begin{tabularx}{\linewidth}{@{}>{\raggedright\arraybackslash}m{\csname HBcomp_spec_table_left_ratio\endcsname\linewidth}|>{\raggedright\arraybackslash}X@{}}",
        ]
        row_count = len(rows)
        for idx, (left, right) in enumerate(rows):
            left_txt = _spec_latex_cell(str(left))
            right_txt = _spec_latex_cell(str(right))
            tex_lines.append(
                rf"\HBTypeSpecLabel{{{left_txt}}} & \HBTypeSpecValue{{{right_txt}}} \\"
            )
            if idx < row_count - 1:
                tex_lines.append(r"\hline")
        tex_lines += [
            r"\end{tabularx}",
            r"\end{spectable}",
        ]
        blocks.append(_raw_latex_block(tex_lines))
    return "".join(blocks)


def _render_spec_sections_html(
    sections: list[dict[str, object]],
) -> str:
    lines: list[str] = []
    for sec in sections:
        title = rst_escape(str(sec.get("title") or ""))
        rows = sec.get("rows") or []
        lines.append(f".. rubric:: \u25cf {title}")
        lines.append("")
        lines.append(".. list-table::")
        lines.append("   :widths: 33 67")
        lines.append("   :header-rows: 0")
        lines.append("")
        for left, right in rows:
            left_txt = rst_escape(str(left))
            right_txt = rst_escape(" / ".join(_split_spec_lines(str(right))))
            lines.append(f"   * - {left_txt}")
            lines.append(f"     - {right_txt}")
        lines.append("")
    return "\n".join(lines).strip() + ("\n" if lines else "")


def _render_text_blocks_latex(rows: list[str], before_vspace_tex: str = "") -> str:
    if not rows:
        return ""
    lines: list[str] = []
    if before_vspace_tex:
        lines.append(rf"\vspace*{{{before_vspace_tex}}}")
    lines.append(r"{\noindent")
    for row in rows:
        lines.append(rf"\HBTypeSpecNote{{{_spec_latex_escape(row)}}}\par")
    lines.append("}")
    return _raw_latex_block(lines)


def _render_text_blocks_html(rows: list[str]) -> str:
    if not rows:
        return ""
    lines: list[str] = []
    for row in rows:
        lines.append(rst_escape(row))
        lines.append("")
    return "\n".join(lines)


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
        ["project_code", "product_code", "\u9879\u76ee\u4ee3\u7801", "product_id"],
    )
    var_region = _first_non_empty(vars_map, ["region", "Region"])
    var_model = _first_non_empty(vars_map, ["model", "product_model", "model_no", "Model"])

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

        if "sku_scope" in row and not _scope_allows(row.get("sku_scope", "ALL"), sku_id):
            continue
        if "sku_id" in row:
            row_sku = rst_escape(row.get("sku_id") or "")
            if row_sku and row_sku != sku_id:
                continue

        row_project = _first_non_empty(row, ["project_code", "\u9879\u76ee\u4ee3\u7801"])
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
        else ("SP\u00c9CIFICATIONS" if lang == "fr" else "SPECIFICATIONS")
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


def render_spec_page(
    template: str,
    blocks: list[dict[str, str]],
    sku_id: str,
    lang: str,
    vars_map: dict[str, str],
) -> str:
    data = collect_spec_content(blocks, sku_id, lang, vars_map)
    title_main = str(data["title_main"])
    sections = data["sections"]
    notes = data["notes"]
    footnotes = data["footnotes"]

    title_main_latex = rf"\section{{{latex_arg_escape(title_main)}}}"
    sections_latex = _render_spec_sections_latex(sections)
    notes_latex = _render_text_blocks_latex(
        notes, before_vspace_tex=r"\csname HBcomp_spec_notes_before\endcsname"
    )
    footnotes_latex = _render_text_blocks_latex(
        footnotes, before_vspace_tex=r"\csname HBcomp_spec_footnotes_before\endcsname"
    )

    sections_html = _render_spec_sections_html(sections)
    notes_html = _render_text_blocks_html(notes)
    footnotes_html = _render_text_blocks_html(footnotes)

    return (
        template.replace(PH_SPEC_TITLE_MAIN, title_main_latex)
        .replace(PH_SPEC_TITLE_MAIN_HTML, html_escape(title_main))
        .replace(PH_SPEC_SECTIONS_LATEX, sections_latex)
        .replace(PH_SPEC_NOTES_LATEX, notes_latex)
        .replace(PH_SPEC_FOOTNOTES_LATEX, footnotes_latex)
        .replace(PH_SPEC_SECTIONS_HTML, _indent_block(sections_html, spaces=3))
        .replace(PH_SPEC_NOTES_HTML, _indent_block(notes_html, spaces=3))
        .replace(PH_SPEC_FOOTNOTES_HTML, _indent_block(footnotes_html, spaces=3))
    )

def _split_symbols_row_text(text: str, block_id: str, line: str) -> tuple[str, str]:
    raw = rst_escape(text)
    if "||" not in raw:
        raise ValueError(
            f"symbols row block_id='{block_id or '?'}' line {line or '?'} "
            "must use 'left || right' format"
        )
    left, right = raw.split("||", 1)
    left = left.strip()
    right = right.strip()
    if not left or not right:
        raise ValueError(
            f"symbols row block_id='{block_id or '?'}' line {line or '?'} "
            "has empty left or right cell"
        )
    return left, right


def _build_symbols_table_lines(
    rows: list[tuple[str, str]], left_ratio: str, with_header: bool = True
) -> list[str]:
    lines: list[str] = [
        r"\begin{HBSharedDataTable}{"
        + left_ratio
        + r"}{\csname HBcomp_spec_table_tabcolsep\endcsname}",
        r"\noindent\begin{tabularx}{\linewidth}{@{}>{\raggedright\arraybackslash}m{"
        + left_ratio
        + r"\linewidth}|>{\raggedright\arraybackslash}X@{}}",
    ]
    if with_header:
        lines.append(r"\HBTypeSpecLabel{\textbf{Symbol}} & \HBTypeSpecValue{\textbf{Meaning}} \\")
        lines.append(r"\hline")

    row_count = len(rows)
    for left, right in rows:
        left_txt = _spec_latex_cell(left)
        right_txt = _spec_latex_cell(right)
        lines.append(rf"\HBTypeSpecLabel{{{left_txt}}} & \HBTypeSpecValue{{{right_txt}}} \\")
        row_count -= 1
        if row_count > 0:
            lines.append(r"\hline")
    lines += [
        r"\end{tabularx}",
        r"\end{HBSharedDataTable}",
    ]
    return lines


def render_symbols_page(
    template: str,
    blocks: list[dict[str, str]],
    sku_id: str,
    lang: str,
    vars_map: dict[str, str],
) -> str:
    lang_col = f"text_{lang}"
    if not blocks:
        raise ValueError(f"symbols page has no blocks for sku={sku_id} lang={lang}")
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
        raise ValueError(f"symbols page has no enabled blocks for sku={sku_id} lang={lang}")

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

    def rows_of(block_type: str) -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []
        for r in sorted(use, key=sort_key):
            if r["block_type"] != block_type:
                continue
            out.append(
                _split_symbols_row_text(
                    r["text"], r.get("block_id") or "?", r.get("line") or "?"
                )
            )
        if not out:
            raise ValueError(f"symbols page has no '{block_type}' rows sku={sku_id} lang={lang}")
        return out

    danger_title = rst_escape(pick("danger_title"))
    danger_line = pick("danger_line")
    danger_note = pick("danger_note")
    maintenance_title = pick("maintenance_title")
    maintenance_paragraph = pick("maintenance_paragraph")
    symbols_title = pick("symbols_title")

    main_rows = rows_of("main_row")
    left_rows = rows_of("left_row")
    right_rows = rows_of("right_row")

    danger_right_parts = [x for x in [danger_line, danger_note] if x]
    danger_right = r"\n".join(danger_right_parts)

    danger_block = _raw_latex_block(
        _build_symbols_table_lines(
            [(f"! {danger_title}", danger_right)],
            left_ratio="0.22",
            with_header=False,
        )
    )

    maintenance_title_block = render_latex_cmd("safetysubbar", maintenance_title)
    maintenance_paragraph_block = render_latex_cmd("safetylead", maintenance_paragraph)
    symbols_title_block = _raw_latex_block([rf"\section{{{latex_arg_escape(symbols_title)}}}"])
    main_table_block = _raw_latex_block(_build_symbols_table_lines(main_rows, "0.24"))

    side_by_side_block = _raw_latex_block(
        [
            r"\vspace*{1.0mm}",
            r"\noindent",
            r"\begin{minipage}[t]{0.495\textwidth}",
            *_build_symbols_table_lines(left_rows, "0.27"),
            r"\end{minipage}\hfill",
            r"\begin{minipage}[t]{0.495\textwidth}",
            *_build_symbols_table_lines(right_rows, "0.27"),
            r"\end{minipage}",
        ]
    )

    content_latex = (
        danger_block
        + maintenance_title_block
        + maintenance_paragraph_block
        + symbols_title_block
        + main_table_block
        + side_by_side_block
    )

    return template.replace(PH_SYMBOLS_CONTENT_LATEX, content_latex)


PAGE_RENDERERS: dict[str, Renderer] = {
    "safety": render_safety_page,
    "spec": render_spec_page,
    "symbols": render_symbols_page,
}


def get_renderer(page_id: str) -> Renderer | None:
    return PAGE_RENDERERS.get((page_id or "").strip())
