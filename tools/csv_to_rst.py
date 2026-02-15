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
        return [{k: (v or "").strip() for k, v in row.items()} for row in reader]


def rst_escape(s: str) -> str:
    return s.replace("\u00a0", " ").strip()


def render_bullet(text: str) -> str:
    """
    Support '\n' in CSV to create nested sub-bullets.
    Example:
      "Line1\n- sub1\n- sub2"
    We treat '\n' as actual newline.
    If a line starts with '- ' we render it as nested bullet under the parent.
    """
    text = rst_escape(text)
    parts = text.split("\\n")
    head = parts[0].strip()

    lines = [f"- {head}"]
    if len(parts) > 1:
        for p in parts[1:]:
            p = p.strip()
            if not p:
                continue
            # allow author to write "- xxx" in CSV; we keep it as nested bullet
            if p.startswith("- "):
                lines.append(f"  {p}")  # nested bullet needs 2-space indent
            else:
                # fallback: treat as continuation paragraph under same bullet
                lines.append(f"  {p}")
    return "\n".join(lines)


def build_block(rows: list[dict[str, str]], part: str) -> str:
    items = []
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


def main() -> None:
    if not TEMPLATE_PATH.exists():
        die(f"Template not found: {TEMPLATE_PATH}")

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    if PLACEHOLDER_TOP not in template or PLACEHOLDER_BOTTOM not in template:
        die(f"Template must contain placeholders: {PLACEHOLDER_TOP} and {PLACEHOLDER_BOTTOM}")

    rows = load_rows()
    top_block = build_block(rows, "top")
    bottom_block = build_block(rows, "bottom")

    out = template.replace(PLACEHOLDER_TOP, top_block).replace(PLACEHOLDER_BOTTOM, bottom_block)
    OUT_RST_PATH.write_text(out, encoding="utf-8")
    print(f"[csv_to_rst] Wrote: {OUT_RST_PATH}")


if __name__ == "__main__":
    main()
