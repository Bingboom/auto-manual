#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CSV_PATH = ROOT / "data" / "safety_items.csv"
TEMPLATE_PATH = ROOT / "docs" / "templates" / "safety_template.rst"
OUT_RST_PATH = ROOT / "docs" / "safety.rst"

PH = {
    "lead_top": "{{ safety_lead_top }}",
    "top_items": "{{ safety_top_items }}",
    "save_title": "{{ safety_save_title }}",
    "bottom_items": "{{ safety_bottom_items }}",
}


def die(msg: str) -> None:
    print(f"[csv_to_rst] ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def rst_escape(s: str) -> str:
    # keep it simple: normalize NBSP and strip
    return (s or "").replace("\u00a0", " ").strip()


def tex_escape(s: str) -> str:
    # minimal safe escaping for raw latex argument
    # (we mainly need braces; you can extend later if needed)
    return s.replace("{", r"\{").replace("}", r"\}")


def load_rows() -> list[dict[str, str]]:
    if not CSV_PATH.exists():
        die(f"CSV not found: {CSV_PATH}")

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            die("CSV has no header.")
        for col in ("part", "text"):
            if col not in reader.fieldnames:
                die(f"CSV missing required column: {col}")

        rows: list[dict[str, str]] = []
        for row in reader:
            clean: dict[str, str] = {}
            for k, v in row.items():
                # csv module may return None for missing cells
                clean[k] = rst_escape(v if isinstance(v, str) else "")
            rows.append(clean)
        return rows


def render_bullet(text: str) -> str:
    """
    Support '\\n' in CSV to create nested sub-bullets.
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
            lines.append(f"  {p}")      # nested bullet
        else:
            lines.append(f"  {p}")      # continuation line
    return "\n".join(lines)


def pick_single(rows: list[dict[str, str]], part: str) -> str:
    # pick first non-empty text for the given part
    for r in rows:
        if (r.get("part") or "").strip().lower() == part:
            t = (r.get("text") or "").strip()
            if t:
                return t
    return ""


def build_block(rows: list[dict[str, str]], part: str) -> str:
    items: list[str] = []
    for r in rows:
        if (r.get("part") or "").strip().lower() != part:
            continue
        text = (r.get("text") or "").strip()
        if not text:
            continue
        items.append(render_bullet(text))

    if not items:
        die(f"No items for part='{part}'. Check CSV 'part' column.")
    return "\n".join(items)


def render_lead_as_raw_latex(text: str) -> str:
    if not text:
        return ""
    text = tex_escape(rst_escape(text))
    return "\n".join([
        ".. raw:: latex",
        "",
        f"   \\safetylead{{{text}}}",
        "",
    ])


def main() -> None:
    if not TEMPLATE_PATH.exists():
        die(f"Template not found: {TEMPLATE_PATH}")

    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    # Ensure placeholders exist (fail fast)
    missing = [name for name, ph in PH.items() if ph not in template]
    if missing:
        die(f"Template missing placeholders: {missing}")

    rows = load_rows()

    lead_top_text = pick_single(rows, "lead_top")
    save_title_text = pick_single(rows, "save_title")

    top_block = build_block(rows, "top")
    bottom_block = build_block(rows, "bottom")

    out = template
    out = out.replace(PH["lead_top"], render_lead_as_raw_latex(lead_top_text))
    out = out.replace(PH["save_title"], render_lead_as_raw_latex(save_title_text))
    out = out.replace(PH["top_items"], top_block)
    out = out.replace(PH["bottom_items"], bottom_block)

    OUT_RST_PATH.write_text(out, encoding="utf-8")
    print(f"[csv_to_rst] Wrote: {OUT_RST_PATH}")


if __name__ == "__main__":
    main()
