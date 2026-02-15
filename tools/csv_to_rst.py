#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

CSV_PATH = ROOT / "data" / "safety_items.csv"
TEMPLATE_PATH = ROOT / "docs" / "templates" / "safety_template.rst"
OUT_RST_PATH = ROOT / "docs" / "safety.rst"

PLACEHOLDER_LEAD = "{{ safety_lead }}"
PLACEHOLDER_TOP = "{{ safety_top_items }}"
PLACEHOLDER_BOTTOM = "{{ safety_bottom_items }}"


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
                # DictReader 正常给 str；但为了容错，统一转成 str
                clean[k] = ("" if v is None else str(v)).strip()
            rows.append(clean)
        return rows


def rst_escape(s: str) -> str:
    # 只做轻量清洗：NBSP -> space
    return s.replace("\u00a0", " ").strip()


def render_bullet(text: str) -> str:
    """
    Support real newline in CSV cell to create nested sub-lines.
    - First line => "- xxx"
    - Following lines:
        "- sub" => "  - sub"
        else   => "  continuation"
    """
    text = rst_escape(text)
    parts = text.splitlines()
    if not parts:
        return ""

    head = parts[0].strip()
    lines = [f"- {head}"]

    for p in parts[1:]:
        p = p.rstrip()
        if not p.strip():
            continue
        if p.lstrip().startswith("- "):
            # keep nested bullet
            lines.append("  " + p.lstrip())
        else:
            lines.append("  " + p.strip())
    return "\n".join(lines)


def build_block(rows: list[dict[str, str]], part: str) -> str:
    items: list[str] = []
    for r in rows:
        if (r.get("part") or "").lower() != part:
            continue
        text = rst_escape(r.get("text") or "")
        if not text:
            continue
        items.append(render_bullet(text))

    if not items:
        die(f"No items for part='{part}'. Check CSV 'part' column.")
    return "\n".join(items)


def build_lead(rows: list[dict[str, str]]) -> str:
    # 找 part=lead（允许多行，但只取第一条非空）
    lead_text = ""
    for r in rows:
        if (r.get("part") or "").lower() == "lead":
            lead_text = rst_escape(r.get("text") or "")
            if lead_text:
                break

    if not lead_text:
        die("Missing lead text: add a CSV row with part=lead.")

    # 输出 raw latex，调用 \safetylead{...}
    # 注意：这里不要用 ** **，完全走你 LaTeX 里定义的样式
    return "\n".join([
        ".. raw:: latex",
        "",
        f"   \\safetylead{{{lead_text}}}",
        "",
    ])


def main() -> None:
    if not TEMPLATE_PATH.exists():
        die(f"Template not found: {TEMPLATE_PATH}")

    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    for ph in (PLACEHOLDER_LEAD, PLACEHOLDER_TOP, PLACEHOLDER_BOTTOM):
        if ph not in template:
            die(f"Template must contain placeholder: {ph}")

    rows = load_rows()

    lead_block = build_lead(rows)
    top_block = build_block(rows, "top")
    bottom_block = build_block(rows, "bottom")

    out = (
        template
        .replace(PLACEHOLDER_LEAD, lead_block)
        .replace(PLACEHOLDER_TOP, top_block)
        .replace(PLACEHOLDER_BOTTOM, bottom_block)
    )

    OUT_RST_PATH.write_text(out, encoding="utf-8")
    print(f"[csv_to_rst] Wrote: {OUT_RST_PATH}")


if __name__ == "__main__":
    main()
