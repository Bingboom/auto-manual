#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]

PAGE_REGISTRY = ROOT / "data" / "phase1" / "page_registry.csv"
CONTENT_BLOCKS = ROOT / "data" / "phase1" / "content_blocks.csv"
PRODUCT_VARS = ROOT / "data" / "phase1" / "product_variables.csv"

TEMPLATE_SAFETY = ROOT / "docs" / "templates" / "safety_template.rst"
OUT_DIR = ROOT / "docs" / "generated"  # docs/generated/<sku>/safety_<lang>.rst

# Template placeholders (must match your safety_template.rst)
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


def die(msg: str) -> None:
    print(f"[phase1_build] ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        die(f"Missing CSV: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def parse_langs(s: str) -> List[str]:
    return [x.strip() for x in (s or "").split(",") if x.strip()]


def scope_allows(scope: str, sku_id: str) -> bool:
    s = (scope or "").strip()
    if not s or s.upper() == "ALL":
        return True
    # allow "A|B|C"
    allowed = {x.strip() for x in s.split("|") if x.strip()}
    return sku_id in allowed


VAR_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_\-]+)\s*\}\}")


def apply_vars(text: str, vars_map: Dict[str, str]) -> str:
    def repl(m: re.Match) -> str:
        k = m.group(1)
        return vars_map.get(k, m.group(0))  # keep placeholder if missing
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
    # raw directive content uses 6 spaces to be safely nested under only:: latex (3 spaces)
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


def build_list_block(rows: List[Dict[str, str]]) -> str:
    # indent 3 spaces so it is safe inside only:: latex block in template
    block = "\n".join(render_bullet_rst(r["text"]) for r in rows) + "\n"
    block = "\n".join(("   " + line) if line.strip() else line for line in block.splitlines())
    return block + "\n"


def render_lead_html(text: str) -> str:
    return f'<p class="hb-lead">{html_escape(text)}</p>'


def render_list_html(rows: List[Dict[str, str]]) -> str:
    items = []
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


def build_safety_rst(
    template: str,
    blocks: List[Dict[str, str]],
    sku_id: str,
    lang: str,
    vars_map: Dict[str, str],
) -> str:
    # Select language column
    lang_col = f"text_{lang}"
    if lang_col not in blocks[0]:
        die(f"Missing language column in content_blocks.csv: {lang_col}")

    # Filter enabled + sku_scope
    use: List[Dict[str, str]] = []
    for b in blocks:
        if (b.get("enabled") or "1").strip() not in ("1", "true", "True", "TRUE"):
            continue
        if not scope_allows(b.get("sku_scope", "ALL"), sku_id):
            continue
        txt = apply_vars(b.get(lang_col, "") or "", vars_map)
        if txt.strip() == "":
            continue
        meta = b.get("meta_json") or "{}"
        use.append(
            {
                "block_type": (b.get("block_type") or "").strip(),
                "order": (b.get("order") or "").strip(),
                "text": txt,
                "meta": meta,
            }
        )

    def pick(bt: str) -> str:
        for r in sorted(use, key=lambda x: float(x.get("order") or "0")):
            if r["block_type"] == bt:
                return r["text"]
        die(f"Missing required block_type='{bt}' for sku={sku_id} lang={lang}")

    def list_rows(part: str) -> List[Dict[str, str]]:
        out = []
        for r in sorted(use, key=lambda x: float(x.get("order") or "0")):
            if r["block_type"] != "list_item":
                continue
            try:
                m = json.loads(r["meta"] or "{}")
            except Exception:
                m = {}
            if (m.get("list_part") or "").strip().lower() == part:
                out.append(r)
        if not out:
            die(f"No list items for list_part='{part}' sku={sku_id} lang={lang}")
        return out

    # LaTeX title lines (template will put them in raw latex blocks)
    title_main_line = rf"\section{{{latex_arg_escape(pick('title_main'))}}}"
    warning_line = rf"\safetywarning{{{latex_arg_escape(pick('warning_title'))}}}"
    title_oper_line = rf"\safetysubbar{{{latex_arg_escape(pick('title_operating'))}}}"

    lead_latex = render_latex_cmd("safetylead", pick("lead_top"))
    save_latex = render_latex_cmd("safetylead", pick("save_title"))

    top_rst = build_list_block(list_rows("top"))
    bottom_rst = build_list_block(list_rows("bottom"))

    # HTML snippets
    title_main_html = html_escape(pick("title_main"))
    warning_html = html_escape(pick("warning_title"))
    title_oper_html = html_escape(pick("title_operating"))

    lead_html = render_lead_html(pick("lead_top"))
    save_html = render_lead_html(pick("save_title"))
    top_html = render_list_html(list_rows("top"))
    bottom_html = render_list_html(list_rows("bottom"))

    out = (
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
    return out


def main() -> None:
    reg = read_csv(PAGE_REGISTRY)
    blocks = read_csv(CONTENT_BLOCKS)
    vars_rows = read_csv(PRODUCT_VARS)

    # Build sku -> vars map
    vars_by_sku: Dict[str, Dict[str, str]] = {}
    for r in vars_rows:
        sku = (r.get("sku_id") or "").strip()
        k = (r.get("var_key") or "").strip()
        v = r.get("var_value") or ""
        if not sku or not k:
            continue
        vars_by_sku.setdefault(sku, {})[k] = v

    if not TEMPLATE_SAFETY.exists():
        die(f"Missing template: {TEMPLATE_SAFETY}")
    template = TEMPLATE_SAFETY.read_text(encoding="utf-8")

    # safety only (phase 1)
    pages = [p for p in reg if (p.get("enabled") or "1").strip() in ("1", "true", "True", "TRUE")]
    pages = sorted(pages, key=lambda x: float(x.get("order") or "0"))

    for p in pages:
        if (p.get("page_type") or "").strip() != "csv_page":
            continue
        page_id = (p.get("page_id") or "").strip()
        if page_id != "safety":
            continue

        langs = parse_langs(p.get("langs") or "")
        scope = p.get("sku_scope") or "ALL"

        for sku_id, sku_vars in vars_by_sku.items():
            if not scope_allows(scope, sku_id):
                continue

            sku_out_dir = OUT_DIR / sku_id
            sku_out_dir.mkdir(parents=True, exist_ok=True)

            page_blocks = [b for b in blocks if (b.get("page_id") or "").strip() == page_id]

            for lang in langs:
                rst = build_safety_rst(template, page_blocks, sku_id, lang, sku_vars)
                out_path = sku_out_dir / f"safety_{lang}.rst"
                out_path.write_text(rst, encoding="utf-8")
                print(f"[phase1_build] Wrote: {out_path}")


if __name__ == "__main__":
    main()