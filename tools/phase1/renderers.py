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


def render_safety_page(
    template: str,
    blocks: list[dict[str, str]],
    sku_id: str,
    lang: str,
    vars_map: dict[str, str],
) -> str:
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

    def list_rows(part: str) -> list[dict[str, str]]:
        out: list[dict[str, str]] = []
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
                out.append(r)
        if not out:
            raise ValueError(f"No list items for list_part='{part}' sku={sku_id} lang={lang}")
        return out

    title_main_line = rf"\section{{{latex_arg_escape(pick('title_main'))}}}"
    warning_line = rf"\safetywarning{{{latex_arg_escape(pick('warning_title'))}}}"
    title_oper_line = rf"\safetysubbar{{{latex_arg_escape(pick('title_operating'))}}}"

    lead_latex = render_latex_cmd("safetylead", pick("lead_top"))
    save_latex = render_latex_cmd("safetylead", pick("save_title"))

    top_rst = build_list_block(list_rows("top"))
    bottom_rst = build_list_block(list_rows("bottom"))

    title_main_html = html_escape(pick("title_main"))
    warning_html = html_escape(pick("warning_title"))
    title_oper_html = html_escape(pick("title_operating"))

    lead_html = render_lead_html(pick("lead_top"))
    save_html = render_lead_html(pick("save_title"))
    top_html = render_list_html(list_rows("top"))
    bottom_html = render_list_html(list_rows("bottom"))

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
        "①": r"\HBSpecMarkerOne{}",
        "②": r"\HBSpecMarkerTwo{}",
        "※": r"\HBSpecMarkerAsterisk{}",
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
        lines.append(f".. rubric:: ● {title}")
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


def render_spec_page(
    template: str,
    blocks: list[dict[str, str]],
    sku_id: str,
    lang: str,
    vars_map: dict[str, str],
) -> str:
    lang_col = f"text_{lang}"
    if not blocks:
        raise ValueError(f"spec page has no blocks for sku={sku_id} lang={lang}")
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

    title_main = pick("title_main")
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
