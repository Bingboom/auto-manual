#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from .renderers_common import (
    _enabled,
    _scope_allows,
    apply_vars,
    latex_arg_escape,
    raw_latex_block,
    render_latex_cmd,
    rst_escape,
    spec_latex_cell,
)

# Template placeholders (symbols page)
PH_SYMBOLS_CONTENT_LATEX = "{{ symbols_content_latex }}"


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
        left_txt = spec_latex_cell(left)
        right_txt = spec_latex_cell(right)
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

    danger_block = raw_latex_block(
        _build_symbols_table_lines(
            [(f"! {danger_title}", danger_right)],
            left_ratio="0.22",
            with_header=False,
        )
    )

    maintenance_title_block = render_latex_cmd("safetysubbar", maintenance_title)
    maintenance_paragraph_block = render_latex_cmd("safetylead", maintenance_paragraph)
    symbols_title_block = raw_latex_block([rf"\section{{{latex_arg_escape(symbols_title)}}}"])
    main_table_block = raw_latex_block(_build_symbols_table_lines(main_rows, "0.24"))

    side_by_side_block = raw_latex_block(
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

