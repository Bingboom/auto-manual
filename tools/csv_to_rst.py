#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CSV_PATH = ROOT / "data" / "safety_items.csv"
TEMPLATE_PATH = ROOT / "docs" / "templates" / "safety_template.rst"

PH_TOP = "{{ safety_top_items }}"
PH_BOTTOM = "{{ safety_bottom_items }}"
PH_LEAD_TOP = "{{ safety_lead_top }}"
PH_SAVE_TITLE = "{{ safety_save_title }}"

# NEW placeholders (LaTeX lines, NOT raw blocks)
PH_TITLE_MAIN = "{{ safety_title_main }}"
PH_WARNING_TITLE = "{{ safety_warning_title }}"
PH_TITLE_OPERATING = "{{ safety_title_operating }}"


def die(msg: str) -> None:
    print(f"[csv_to_rst] ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def load_rows(lang: str) -> list[dict[str, str]]:
    if not CSV_PATH.exists():
        die(f"CSV not found: {CSV_PATH}")

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            die("CSV has no header.")

        # Supported formats:
        # 1) legacy: part,text
        # 2) i18n:  part,text_en,text_fr,text_es...
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


def rst_escape(s: str) -> str:
    return (s or "").replace("\u00a0", " ").strip()


def render_bullet(text: str) -> str:
    """
    Support literal '\\n' in CSV to create nested sub-bullets.
    Example:
      "Line1\\n- sub1\\n- sub2"
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
            lines.append(f"  {p}")  # continuation
    return "\n".join(lines)


def build_block(rows: list[dict[str, str]], part: str) -> str:
    items: list[str] = []
    for r in rows:
        if (r.get("part") or "").lower() != part:
            continue
        text = (r.get("text") or "").strip()
        if not text:
            continue
        items.append(render_bullet(text))

    if not items:
        die(f"No items for part='{part}'.")
    return "\n".join(items)


def pick_single_text(rows: list[dict[str, str]], part: str) -> str:
    texts = [
        rst_escape(r.get("text", ""))
        for r in rows
        if (r.get("part") or "").lower() == part
        and (r.get("text") or "").strip()
    ]
    if not texts:
        die(f"Missing required single-line part='{part}'.")
    return texts[0]


def render_latex_cmd(cmd: str, text: str) -> str:
    """
    Emit a LaTeX command via rst raw block.
    Used for lead/save title blocks because template expects raw blocks there.
    """
    text = rst_escape(text)
    text = text.replace("{", r"\{").replace("}", r"\}")
    return "\n".join(
        [
            ".. raw:: latex",
            "",
            f"   \\{cmd}{{{text}}}",
            "",
        ]
    )


def latex_arg_escape(text: str) -> str:
    """Escape braces for safe LaTeX macro arguments."""
    text = rst_escape(text)
    return text.replace("{", r"\{").replace("}", r"\}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="en", help="language code: en/fr/es")
    ap.add_argument("--out", default=None, help="custom output path")
    args = ap.parse_args()

    lang = args.lang.lower()

    if not TEMPLATE_PATH.exists():
        die(f"Template not found: {TEMPLATE_PATH}")

    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    # require placeholders
    for ph in (
        PH_TOP, PH_BOTTOM, PH_LEAD_TOP, PH_SAVE_TITLE,
        PH_TITLE_MAIN, PH_WARNING_TITLE, PH_TITLE_OPERATING
    ):
        if ph not in template:
            die(f"Template missing placeholder: {ph}")

    rows = load_rows(lang)

    # ---- NEW multilingual titles (LaTeX lines only; template wraps raw:: latex) ----
    title_main = latex_arg_escape(pick_single_text(rows, "title_main"))
    title_oper = latex_arg_escape(pick_single_text(rows, "title_operating"))
    warning_title = latex_arg_escape(pick_single_text(rows, "warning_title"))

    title_main_line = rf"\section{{{title_main}}}"
    title_oper_line = rf"\safetysubbar{{{title_oper}}}"
    warning_line = rf"\safetywarning{{{warning_title}}}"

    # existing blocks
    lead_top_text = pick_single_text(rows, "lead_top")
    save_title_text = pick_single_text(rows, "save_title")

    lead_block = render_latex_cmd("safetylead", lead_top_text)
    save_title_block = render_latex_cmd("safetylead", save_title_text)

    top_block = build_block(rows, "top")
    bottom_block = build_block(rows, "bottom")

    out = (
        template.replace(PH_TITLE_MAIN, title_main_line)
        .replace(PH_WARNING_TITLE, warning_line)
        .replace(PH_TITLE_OPERATING, title_oper_line)
        .replace(PH_LEAD_TOP, lead_block)
        .replace(PH_SAVE_TITLE, save_title_block)
        .replace(PH_TOP, top_block)
        .replace(PH_BOTTOM, bottom_block)
    )

    out_path = Path(args.out) if args.out else (ROOT / "docs" / f"safety_{lang}.rst")
    out_path.write_text(out, encoding="utf-8")
    print(f"[csv_to_rst] Wrote: {out_path}")


if __name__ == "__main__":
    main()