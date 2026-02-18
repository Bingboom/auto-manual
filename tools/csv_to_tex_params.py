#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CSV -> TeX params generator (supports underscores in keys)

Input:
  data/layout_params.csv
    columns: key,value,unit,comment

Output:
  docs/latex_theme/params.tex

Generated TeX:
  \\expandafter\\def\\csname HB<key>\\endcsname{<value><unit>}
Access:
  \\csname HB<key>\\endcsname

Enhancements:
- Grouped output sections by key prefix (page_/brand_color_/type_/comp_/other)
- Duplicate key detection (hard error)
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "layout_params.csv"
OUT_TEX = ROOT / "docs" / "latex_theme" / "params.tex"


def fmt_value(value: str, unit: str) -> str:
    """Format value with unit. ratio/int/cmyk/none are raw."""
    value = (value or "").strip()
    unit = (unit or "").strip()
    if value == "":
        return ""

    u = unit.lower()
    # raw units (no suffix)
    if u in {"", "none", "null", "ratio", "int", "cmyk"}:
        return value

    return f"{value}{unit}"



def escape_tex_comment(s: str) -> str:
    """Escape % in comments to avoid TeX comment issues."""
    return (s or "").replace("%", r"\%").strip()


def group_of_key(key: str) -> str:
    k = key.lower()
    if k.startswith("page_") or k == "section_after_fix":
        return "PAGE"
    if k.startswith("brand_color_"):
        return "BRAND"
    if k.startswith("type_"):
        return "TYPE SYSTEM"
    if k.startswith("comp_"):
        return "COMPONENTS"
    return "OTHER"


GROUP_ORDER = {
    "PAGE": 0,
    "BRAND": 1,
    "TYPE SYSTEM": 2,
    "COMPONENTS": 3,
    "OTHER": 4,
}


def main() -> None:
    if not CSV_PATH.exists():
        raise SystemExit(f"[csv_to_tex_params] ERROR: CSV not found: {CSV_PATH}")

    items: dict[str, tuple[str, str]] = {}

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise SystemExit("[csv_to_tex_params] ERROR: CSV has no header row.")

        required = {"key", "value"}
        missing = required - set(reader.fieldnames)
        if missing:
            raise SystemExit(f"[csv_to_tex_params] ERROR: CSV missing columns: {sorted(missing)}")

        for r in reader:
            key = (r.get("key") or "").strip()
            value = (r.get("value") or "").strip()
            unit = (r.get("unit") or "").strip()
            comment = escape_tex_comment(r.get("comment") or "")

            # ignore blank rows / separators
            if not key or value == "":
                continue

            v = fmt_value(value, unit)
            if v == "":
                continue

            if key in items:
                raise SystemExit(f"[csv_to_tex_params] ERROR: duplicate key in CSV: {key}")

            items[key] = (v, comment)

    sorted_keys = sorted(items.keys(), key=lambda k: (GROUP_ORDER[group_of_key(k)], k))

    OUT_TEX.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("% AUTO-GENERATED. DO NOT EDIT BY HAND.")
    lines.append("% Source: data/layout_params.csv")
    lines.append("% Access pattern: \\csname HB<key>\\endcsname")
    lines.append("")

    cur_group = None
    for key in sorted_keys:
        v, c = items[key]
        g = group_of_key(key)
        if g != cur_group:
            cur_group = g
            lines.append(f"% ===== {g} =====")
            lines.append("")

        if c:
            lines.append(f"% {c}")

        # Define as raw tokens (no extra brace layer)
        # This is safest across geometry/setlength/fontsize/etc.
        lines.append(rf"\expandafter\def\csname HB{key}\endcsname{{{v}}}")
        lines.append("")

    OUT_TEX.write_text("\n".join(lines), encoding="utf-8")
    print(f"[csv_to_tex_params] Wrote: {OUT_TEX}")


if __name__ == "__main__":
    main()
