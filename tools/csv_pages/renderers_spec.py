#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from .renderers_common import (
    html_escape,
    latex_arg_escape,
    raw_latex_block,
    rst_escape,
    spec_latex_cell,
    spec_latex_escape,
    split_spec_lines,
)
from .renderers_spec_parser import collect_spec_content

# Template placeholders (spec page)
PH_SPEC_TITLE_MAIN = "{{ spec_title_main }}"
PH_SPEC_TITLE_MAIN_HTML = "{{ spec_title_main_html }}"
PH_SPEC_SECTIONS_LATEX = "{{ spec_sections_latex }}"
PH_SPEC_NOTES_LATEX = "{{ spec_notes_latex }}"
PH_SPEC_FOOTNOTES_LATEX = "{{ spec_footnotes_latex }}"
PH_SPEC_SECTIONS_HTML = "{{ spec_sections_html }}"
PH_SPEC_NOTES_HTML = "{{ spec_notes_html }}"
PH_SPEC_FOOTNOTES_HTML = "{{ spec_footnotes_html }}"


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
            rf"\specsectiontitle{{{spec_latex_escape(title)}}}",
            r"\begin{spectable}",
            r"\noindent\begin{tabularx}{\linewidth}{@{}>{\raggedright\arraybackslash}m{\csname HBcomp_spec_table_left_ratio\endcsname\linewidth}|>{\raggedright\arraybackslash}X@{}}",
        ]
        row_count = len(rows)
        for idx, (left, right) in enumerate(rows):
            left_txt = spec_latex_cell(str(left))
            right_txt = spec_latex_cell(str(right))
            tex_lines.append(
                rf"\HBTypeSpecLabel{{{left_txt}}} & \HBTypeSpecValue{{{right_txt}}} \\"
            )
            if idx < row_count - 1:
                tex_lines.append(r"\hline")
        tex_lines += [
            r"\end{tabularx}",
            r"\end{spectable}",
        ]
        blocks.append(raw_latex_block(tex_lines))
    return "".join(blocks)


def _render_spec_sections_html(
    sections: list[dict[str, object]],
) -> str:
    lines: list[str] = []
    for sec in sections:
        title = rst_escape(str(sec.get("title") or ""))
        rows = sec.get("rows") or []
        lines.append(".. raw:: html")
        lines.append("")
        lines.append(
            "   <h2 class=\"hb-spec-section\">"
            f"<span class=\"hb-spec-bullet\" aria-hidden=\"true\">&#9679;</span>"
            f"<span class=\"hb-spec-section-text\">{html_escape(title).upper()}</span>"
            "</h2>"
        )
        lines.append("   <table class=\"hb-spec-table\">")
        lines.append("     <tbody>")
        for left, right in rows:
            left_txt = html_escape(rst_escape(str(left)))
            right_txt = "<br/>".join(
                html_escape(rst_escape(line))
                for line in split_spec_lines(str(right))
                if line
            )
            lines.append("       <tr>")
            lines.append(f"         <th scope=\"row\" class=\"hb-spec-label\">{left_txt}</th>")
            lines.append(f"         <td class=\"hb-spec-value\">{right_txt}</td>")
            lines.append("       </tr>")
        lines.append("     </tbody>")
        lines.append("   </table>")
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
        lines.append(rf"\HBTypeSpecNote{{{spec_latex_escape(row)}}}\par")
    lines.append("}")
    return raw_latex_block(lines)


def _render_text_blocks_html(rows: list[str], *, class_name: str, kind: str) -> str:
    if not rows:
        return ""
    lines: list[str] = []
    for row in rows:
        text_html = "<br/>".join(
            html_escape(rst_escape(line))
            for line in split_spec_lines(row)
            if line
        )
        lines.append(".. raw:: html")
        lines.append("")
        lines.append(
            f"   <p class=\"{class_name}\" data-spec-trailer-kind=\"{html_escape(kind)}\">{text_html}</p>"
        )
        lines.append("")
    return "\n".join(lines).strip() + ("\n" if lines else "")


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
    notes_html = _render_text_blocks_html(notes, class_name="hb-spec-note", kind="note")
    footnotes_html = _render_text_blocks_html(footnotes, class_name="hb-spec-footnote", kind="footnote")

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
