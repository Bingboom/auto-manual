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

PH_TOP = "{{ safety_top_items }}"
PH_BOTTOM = "{{ safety_bottom_items }}"
PH_LEAD_TOP = "{{ safety_lead_top }}"
PH_SAVE_TITLE = "{{ safety_save_title }}"


def die(msg: str) -> None:
    print(f"[csv_to_rst] ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


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
                # 防止 csv 库把某些异常行解析成 list
                if isinstance(v, list):
                    v = ",".join(map(str, v))
                clean[k] = (v or "").strip()
            rows.append(clean)
        return rows


def rst_escape(s: str) -> str:
    # 只做最小清洗：NBSP -> space + strip
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
        die(f"No items for part='{part}'. Check CSV 'part' column.")
    return "\n".join(items)


def pick_single_text(rows: list[dict[str, str]], part: str) -> str:
    texts = [rst_escape(r.get("text", "")) for r in rows if (r.get("part") or "").lower() == part and (r.get("text") or "").strip()]
    if not texts:
        die(f"Missing required single-line part='{part}' in CSV (need one row).")
    # 只取第一条，避免多条造成不可控版式
    return texts[0]


def render_latex_cmd(cmd: str, text: str) -> str:
    """
    Emit a LaTeX command via rst raw block.
    Keeps it in the same flow as other content.
    """
    text = rst_escape(text)
    # 避免花括号破坏 \cmd{...}
    text = text.replace("{", r"\{").replace("}", r"\}")
    return "\n".join(
        [
            ".. raw:: latex",
            "",
            f"   \\{cmd}{{{text}}}",
            "",
        ]
    )


def main() -> None:
    if not TEMPLATE_PATH.exists():
        die(f"Template not found: {TEMPLATE_PATH}")

    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    # 必须包含四个占位符
    for ph in (PH_TOP, PH_BOTTOM, PH_LEAD_TOP, PH_SAVE_TITLE):
        if ph not in template:
            die(f"Template missing placeholder: {ph}")

    rows = load_rows()

    # 1) lead_top / save_title 从 CSV 读，渲染为 latex 命令
    lead_top_text = pick_single_text(rows, "lead_top")
    save_title_text = pick_single_text(rows, "save_title")

    lead_block = render_latex_cmd("safetylead", lead_top_text)
    save_title_block = render_latex_cmd("safetylead", save_title_text)

    # 2) top/bottom bullet lists
    top_block = build_block(rows, "top")
    bottom_block = build_block(rows, "bottom")

    out = (
        template.replace(PH_LEAD_TOP, lead_block)
        .replace(PH_SAVE_TITLE, save_title_block)
        .replace(PH_TOP, top_block)
        .replace(PH_BOTTOM, bottom_block)
    )

    OUT_RST_PATH.write_text(out, encoding="utf-8")
    print(f"[csv_to_rst] Wrote: {OUT_RST_PATH}")


if __name__ == "__main__":
    main()
