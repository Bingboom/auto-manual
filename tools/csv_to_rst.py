#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CSV -> RST generator (template-driven)

- Reads safety items from: data/safety_items.csv
- Loads RST template from: docs/templates/safety_template.rst
- Renders list items into a single RST bullet list block
- Replaces placeholder: {{ safety_items }}
- Writes output to: docs/safety.rst

Usage:
  python tools/csv_to_rst.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import List, Dict


ROOT = Path(__file__).resolve().parents[1]

CSV_PATH = ROOT / "data" / "safety_items.csv"
TEMPLATE_PATH = ROOT / "docs" / "templates" / "safety_template.rst"
OUT_RST_PATH = ROOT / "docs" / "safety.rst"

# Placeholder token in template
PLACEHOLDER = "{{ safety_items }}"


def die(msg: str, code: int = 1) -> None:
    print(f"[csv_to_rst] ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def read_csv_rows(csv_path: Path) -> List[Dict[str, str]]:
    if not csv_path.exists():
        die(f"CSV not found: {csv_path}")

    rows: List[Dict[str, str]] = []
    try:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                die(f"CSV has no header: {csv_path}")

            # Normalize headers
            headers = [h.strip() for h in reader.fieldnames if h]
            if "text" not in headers:
                die(f"CSV header must contain 'text' column. Got: {headers}")

            for row in reader:
                # DictReader may return None values; normalize to str
                clean = {k.strip(): (v or "").strip() for k, v in row.items() if k}
                rows.append(clean)

    except UnicodeDecodeError:
        die(
            f"CSV encoding error. Please save as UTF-8 (with or without BOM): {csv_path}"
        )

    return rows


def sanitize_rst_text(s: str) -> str:
    """
    Very lightweight sanitation for RST list items:
    - Replace non-breaking spaces
    - Strip trailing spaces
    """
    s = s.replace("\u00a0", " ").strip()

    # Optional: avoid accidental starting tokens that can break list parsing
    # (rare in safety sentences, but safe to guard)
    if s.startswith((".. ", ":")):
        s = "\\ " + s  # escape directive-like / field-like start

    return s


def build_bullet_list(rows: List[Dict[str, str]]) -> str:
    """
    Build an RST bullet list block:
      - item
      - item
    """
    items: List[str] = []
    for r in rows:
        text = (r.get("text") or "").strip()
        if not text:
            continue

        text = sanitize_rst_text(text)

        # Skip meaningless short fragments (optional, you can disable)
        # If you don't want this, comment out the next 2 lines.
        if len(text) < 8:
            continue

        items.append(f"- {text}")

    if not items:
        die(f"No valid 'text' rows found in {CSV_PATH}")

    return "\n".join(items)


def load_template(template_path: Path) -> str:
    if not template_path.exists():
        die(
            f"Template not found: {template_path}\n"
            f"Create it and include placeholder: {PLACEHOLDER}"
        )

    template = template_path.read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        die(
            f"Template missing placeholder token: {PLACEHOLDER}\n"
            f"File: {template_path}"
        )
    return template


def render(template: str, safety_items_block: str) -> str:
    """
    Simple placeholder replacement.
    Keeps template as the single source of structure.
    """
    return template.replace(PLACEHOLDER, safety_items_block)


def write_output(out_path: Path, content: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    print(f"[csv_to_rst] Wrote: {out_path}")


def main() -> None:
    rows = read_csv_rows(CSV_PATH)
    safety_items_block = build_bullet_list(rows)
    template = load_template(TEMPLATE_PATH)
    output = render(template, safety_items_block)
    write_output(OUT_RST_PATH, output)


if __name__ == "__main__":
    main()
