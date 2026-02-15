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
  \expandafter\def\csname HB<key>\endcsname{<value><unit>}
So you can use in TeX:
  \csname HBtwocol_sep\endcsname
  \csname HBwarn_box_arc\endcsname
etc.
"""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "layout_params.csv"
OUT_TEX = ROOT / "docs" / "latex_theme" / "params.tex"


def fmt_value(value: str, unit: str) -> str:
    """Format value with unit. 'ratio' means raw number with no unit suffix."""
    value = (value or "").strip()
    unit = (unit or "").strip()

    if value == "":
        return ""

    if unit == "" or unit.lower() in {"none", "null"}:
        return value

    if unit.lower() == "ratio":
        # ratio used as plain number (e.g., 0.86), caller may append \textwidth etc.
        return value

    # mm/pt/em/... directly concatenated
    return f"{value}{unit}"


def escape_tex_comment(s: str) -> str:
    """Escape % in comments to avoid TeX comment issues."""
    return (s or "").replace("%", r"\%").strip()


def main() -> None:
    if not CSV_PATH.exists():
        raise SystemExit(f"[csv_to_tex_params] ERROR: CSV not found: {CSV_PATH}")

    rows: list[tuple[str, str, str]] = []
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

            if not key or not value:
                continue

            v = fmt_value(value, unit)
            if v == "":
                continue

            rows.append((key, v, comment))

    # stable ordering for diff
    rows.sort(key=lambda x: x[0])

    OUT_TEX.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("% AUTO-GENERATED. DO NOT EDIT BY HAND.")
    lines.append("% Source: data/layout_params.csv")
    lines.append("% Access pattern: \\csname HB<key>\\endcsname")
    lines.append("")

    for key, v, c in rows:
        if c:
            lines.append(f"% {c}")
        # IMPORTANT: define via csname so keys may contain underscores
        lines.append(rf"\expandafter\def\csname HB{key}\endcsname{{{v}}}")
        lines.append("")

    OUT_TEX.write_text("\n".join(lines), encoding="utf-8")
    print(f"[csv_to_tex_params] Wrote: {OUT_TEX}")


if __name__ == "__main__":
    main()
