#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json

from .renderers_common import (
    _enabled,
    _scope_allows,
    apply_vars,
    build_list_block,
    html_escape,
    latex_arg_escape,
    render_lead_html,
    render_latex_cmd,
    render_list_html,
)

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
