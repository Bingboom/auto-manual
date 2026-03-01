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
    return text.replace("{", r"\{").replace("}", r"\}")


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
            except Exception:
                meta = {}
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


PAGE_RENDERERS: dict[str, Renderer] = {
    "safety": render_safety_page,
}


def get_renderer(page_id: str) -> Renderer | None:
    return PAGE_RENDERERS.get((page_id or "").strip())
