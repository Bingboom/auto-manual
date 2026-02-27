#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
import sys
import argparse
from pathlib import Path
import html as _html

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_CSV_PATH = ROOT / "data" / "safety_items.csv"
DEFAULT_TEMPLATE_PATH = ROOT / "docs" / "templates" / "safety_template.rst"
DEFAULT_OUT_PREFIX = "safety"

# LaTeX placeholders
PH_TOP = "{{ safety_top_items }}"
PH_BOTTOM = "{{ safety_bottom_items }}"
PH_LEAD_TOP = "{{ safety_lead_top }}"
PH_SAVE_TITLE = "{{ safety_save_title }}"

PH_TITLE_MAIN = "{{ safety_title_main }}"
PH_WARNING_TITLE = "{{ safety_warning_title }}"
PH_TITLE_OPERATING = "{{ safety_title_operating }}"

# HTML placeholders
PH_TITLE_MAIN_HTML = "{{ safety_title_main_html }}"
PH_WARNING_TITLE_HTML = "{{ safety_warning_title_html }}"
PH_TITLE_OPERATING_HTML = "{{ safety_title_operating_html }}"

PH_LEAD_TOP_HTML = "{{ safety_lead_top_html }}"
PH_SAVE_TITLE_HTML = "{{ safety_save_title_html }}"
PH_TOP_HTML = "{{ safety_top_items_html }}"
PH_BOTTOM_HTML = "{{ safety_bottom_items_html }}"


def die(msg: str) -> None:
    print(f"[csv_to_rst] ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def rst_escape(s: str) -> str:
    return (s or "").replace("\u00a0", " ").strip()


def latex_arg_escape(text: str) -> str:
    text = rst_escape(text)
    return text.replace("{", r"\{").replace("}", r"\}")


def html_escape(text: str) -> str:
    return _html.escape(rst_escape(text), quote=True)


def load_rows(csv_path: Path, lang: str) -> list[dict[str, str]]:
    if not csv_path.exists():
        die(f"CSV not found: {csv_path}")

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            die("CSV has no header.")

        if "text" in reader.fieldnames:
            text_col = "text"
        else:
            text_col = f"text_{lang}"
            if text_col not in reader.fieldnames:
                die(f"CSV missing language column: {text_col}")

        rows: list[dict[str, str]] = []
        for row in reader:
            clean: dict[str, str] = {}
            for k, v in row.items():
                if isinstance(v, list):
                    v = ",".join(map(str, v))
                clean[k] = (v or "").strip()
            clean["text"] = clean.get(text_col, "").strip()
            rows.append(clean)
        return rows


def pick_single_text(rows: list[dict[str, str]], part: str) -> str:
    texts = [
        rst_escape(r.get("text", ""))
        for r in rows
        if (r.get("part") or "").lower() == part and (r.get("text") or "").strip()
    ]
    if not texts:
        die(f"Missing required single-line part='{part}'.")
    return texts[0]


def render_bullet_rst(text: str) -> str:
    """
    Render one CSV cell into an RST bullet item.
    Supports '\\n' for sub-lines; '- ' starts a nested bullet.
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
            lines.append(f"  {p}")  # nested bullet
        else:
            lines.append(f"  {p}")  # continuation line
    return "\n".join(lines)


def render_list_latex(rows: list[dict[str, str]], part: str) -> str:
    items: list[str] = []
    for r in rows:
        if (r.get("part") or "").lower() != part:
            continue
        text = (r.get("text") or "").strip()
        if not text:
            continue
        # 简化：不做嵌套，直接当一条 item
        items.append(latex_arg_escape(text))

    if not items:
        die(f"No items for part='{part}'.")

    body = "\n".join([f"\\item {t}" for t in items])

    # 输出 raw latex block，注意 6 空格缩进让它在 only:: latex 里稳定
    return "\n".join(
        [
            ".. raw:: latex",
            "",
            "      \\begin{itemize}",
            *[f"      {line}" for line in body.splitlines()],
            "      \\end{itemize}",
            "",
        ]
    )


def render_latex_cmd(cmd: str, text: str) -> str:
    """
    Render a raw-latex directive block.
    IMPORTANT: The LaTeX command line uses 6 spaces indentation so that when this block
    itself is placed under `.. only:: latex` (3 spaces), the raw content is still
    indented one level deeper than the directive.
    """
    text = latex_arg_escape(text)
    return "\n".join(
        [
            ".. raw:: latex",
            "",
            f"      \\{cmd}{{{text}}}",  # 6 spaces
            "",
        ]
    )


def render_lead_html_snippet(text: str) -> str:
    return f'<p class="hb-lead">{html_escape(text)}</p>'


def render_list_html_snippet(rows: list[dict[str, str]], part: str) -> str:
    """
    Render list items as HTML <ul><li>...</li></ul>.
    Supports '\\n' for sub-lines; '- ' starts a nested bullet.
    """
    items: list[str] = []
    for r in rows:
        if (r.get("part") or "").lower() != part:
            continue
        raw = (r.get("text") or "").strip()
        if not raw:
            continue

        parts = rst_escape(raw).split("\\n")
        head = html_escape(parts[0])

        li_lines = [head]
        sub_items: list[str] = []
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

    if not items:
        die(f"No items for part='{part}'.")
    return '<ul class="hb-list">' + "".join(items) + "</ul>"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="en", help="language code: en/fr/es")
    ap.add_argument("--csv", default=None, help="override input CSV path")
    ap.add_argument("--template", default=None, help="override template path")
    ap.add_argument("--out-prefix", default=None, help="output rst prefix (default=safety)")
    ap.add_argument("--out", default=None, help="explicit output file path (overrides out-prefix)")
    args = ap.parse_args()

    lang = args.lang.lower()

    csv_path = Path(args.csv) if args.csv else DEFAULT_CSV_PATH
    template_path = Path(args.template) if args.template else DEFAULT_TEMPLATE_PATH
    out_prefix = args.out_prefix or DEFAULT_OUT_PREFIX

    if not template_path.exists():
        die(f"Template not found: {template_path}")

    template = template_path.read_text(encoding="utf-8")

    required_ph = [
        PH_TOP, PH_BOTTOM, PH_LEAD_TOP, PH_SAVE_TITLE,
        PH_TITLE_MAIN, PH_WARNING_TITLE, PH_TITLE_OPERATING,
        PH_TITLE_MAIN_HTML, PH_WARNING_TITLE_HTML, PH_TITLE_OPERATING_HTML,
        PH_LEAD_TOP_HTML, PH_SAVE_TITLE_HTML, PH_TOP_HTML, PH_BOTTOM_HTML,
    ]
    for ph in required_ph:
        if ph not in template:
            die(f"Template missing placeholder: {ph}")

    rows = load_rows(csv_path, lang)

    # LaTeX title lines (inserted into raw latex blocks in template)
    title_main = latex_arg_escape(pick_single_text(rows, "title_main"))
    title_oper = latex_arg_escape(pick_single_text(rows, "title_operating"))
    warning_title = latex_arg_escape(pick_single_text(rows, "warning_title"))

    title_main_line = rf"\section{{{title_main}}}"
    title_oper_line = rf"\safetysubbar{{{title_oper}}}"
    warning_line = rf"\safetywarning{{{warning_title}}}"

    # HTML text/snippets
    title_main_html = html_escape(pick_single_text(rows, "title_main"))
    title_oper_html = html_escape(pick_single_text(rows, "title_operating"))
    warning_title_html = html_escape(pick_single_text(rows, "warning_title"))

    lead_top_text = pick_single_text(rows, "lead_top")
    save_title_text = pick_single_text(rows, "save_title")

    # LaTeX blocks (raw directive blocks)
    lead_block_latex = render_latex_cmd("safetylead", lead_top_text)
    save_title_block_latex = render_latex_cmd("safetylead", save_title_text)

    # RST lists for LaTeX/PDF path (indented 3 spaces)
    top_block_rst = render_list_latex(rows, "top")
    bottom_block_rst = render_list_latex(rows, "bottom")

    # HTML snippets
    lead_block_html = render_lead_html_snippet(lead_top_text)
    save_title_block_html = render_lead_html_snippet(save_title_text)
    top_block_html = render_list_html_snippet(rows, "top")
    bottom_block_html = render_list_html_snippet(rows, "bottom")

    out = (
        template.replace(PH_TITLE_MAIN, title_main_line)
        .replace(PH_WARNING_TITLE, warning_line)
        .replace(PH_TITLE_OPERATING, title_oper_line)
        .replace(PH_LEAD_TOP, lead_block_latex)
        .replace(PH_SAVE_TITLE, save_title_block_latex)
        .replace(PH_TOP, top_block_rst)
        .replace(PH_BOTTOM, bottom_block_rst)
        .replace(PH_TITLE_MAIN_HTML, title_main_html)
        .replace(PH_WARNING_TITLE_HTML, warning_title_html)
        .replace(PH_TITLE_OPERATING_HTML, title_oper_html)
        .replace(PH_LEAD_TOP_HTML, lead_block_html)
        .replace(PH_SAVE_TITLE_HTML, save_title_block_html)
        .replace(PH_TOP_HTML, top_block_html)
        .replace(PH_BOTTOM_HTML, bottom_block_html)
    )

    if args.out:
        out_path = Path(args.out)
    else:
        out_path = ROOT / "docs" / f"{out_prefix}_{lang}.rst"

    out_path.write_text(out, encoding="utf-8")
    print(f"[csv_to_rst] Wrote: {out_path}")


if __name__ == "__main__":
    main()