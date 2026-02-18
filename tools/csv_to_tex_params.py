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
- Grouped output sections by key prefix (page_/type_/comp_/other)
- Optional alias mapping: old_key -> new_key (\\let HBold HBnew)
- Duplicate key detection (hard error)
"""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "layout_params.csv"
OUT_TEX = ROOT / "docs" / "latex_theme" / "params.tex"


# --- alias mapping (old_key -> new_key) ---
# Only emits alias when BOTH keys exist in CSV.
ALIASES: dict[str, str] = {
    # --- CORE decoupling you want ---
    # old lead_* should map to type_body_*
    "lead_font_size": "type_body_font_size",
    "lead_font_leading": "type_body_font_leading",
    "lead_force_upper": "type_body_force_upper",
    "lead_vspace_after": "comp_lead_after",

    # old twocol_font_* should map to type_list_*
    "twocol_font_size": "type_list_font_size",
    "twocol_font_leading": "type_list_font_leading",

    # title_* used by pills -> split (initially can share, later you can change values)
    "title_font_size": "type_h1_font_size",
    "title_font_leading": "type_h1_font_leading",
    "title_force_upper": "type_h1_force_upper",

    # warning text -> type_warning_text_*
    "warn_text_size": "type_warning_text_font_size",
    "warn_text_leading": "type_warning_text_font_leading",
    "warn_text_uppercase": "type_warning_text_force_upper",

    # box params mirrors (optional but nice)
    "brand_title_arc": "comp_h1_pill_arc",
    "brand_title_pad_lr": "comp_h1_pill_pad_lr",
    "brand_title_pad_tb": "comp_h1_pill_pad_tb",
    "brand_title_width": "comp_h1_pill_width",
    "brand_title_vspace_after": "comp_h1_pill_after",

    "warn_box_arc": "comp_warning_box_arc",
    "warn_box_rule": "comp_warning_box_rule",
    "warn_box_pad_lr": "comp_warning_box_pad_lr",
    "warn_box_pad_tb": "comp_warning_box_pad_tb",
    "warn_box_before": "comp_warning_box_before",
    "warn_box_after": "comp_warning_box_after",
    "warn_box_width": "comp_warning_box_width",

    "warn_lockup_height": "comp_lockup_height",
    "warn_lockup_width": "comp_lockup_width",
    "warn_lockup_gap": "comp_lockup_gap",
    "warn_lockup_viewport": "comp_lockup_viewport",

    "subbar_arc": "comp_subbar_arc",
    "subbar_pad_lr": "comp_subbar_pad_lr",
    "subbar_pad_tb": "comp_subbar_pad_tb",
    "subbar_width": "comp_subbar_width",
    "subbar_vspace_after": "comp_subbar_after",

    "twocol_sep": "comp_twocol_sep",
    "list_leftmargin": "comp_list_leftmargin",
    "list_labelsep": "comp_list_labelsep",
    "list_itemsep": "comp_list_itemsep",
    "list_topsep": "comp_list_topsep",
    "list_parsep": "comp_list_parsep",
    "list_partopsep": "comp_list_partopsep",
    "list_bullet_raise": "comp_list_bullet_raise",
    "list_bullet_symbol": "comp_list_bullet_symbol",

    "rubric_before": "comp_rubric_before",
    "rubric_after": "comp_rubric_after",

    "table_inner_rule": "comp_table_inner_rule",
    "table_tabcolsep": "comp_table_tabcolsep",
    "table_outer_arc": "comp_table_outer_arc",
    "table_outer_rule": "comp_table_outer_rule",

    "note_arc": "comp_note_arc",
    "note_pad_lr": "comp_note_pad_lr",
    "note_pad_tb": "comp_note_pad_tb",
}


def fmt_value(value: str, unit: str) -> str:
    """Format value with unit. 'ratio' means raw number with no unit suffix."""
    value = (value or "").strip()
    unit = (unit or "").strip()

    if value == "":
        return ""

    if unit == "" or unit.lower() in {"none", "null"}:
        return value

    u = unit.lower()
    if u in {"", "none", "null"}:
        return value
    if u in {"ratio", "int"}:
        return value
    return f"{value}{unit}"



def escape_tex_comment(s: str) -> str:
    """Escape % in comments to avoid TeX comment issues."""
    return (s or "").replace("%", r"\%").strip()


def group_of_key(key: str) -> str:
    k = key.lower()
    if k.startswith("page_"):
        return "PAGE"
    if k.startswith("type_"):
        return "TYPE SYSTEM"
    if k.startswith("comp_"):
        return "COMPONENTS"
    return "OTHER"


GROUP_ORDER = {
    "PAGE": 0,
    "TYPE SYSTEM": 1,
    "COMPONENTS": 2,
    "OTHER": 3,
}


def main() -> None:
    if not CSV_PATH.exists():
        raise SystemExit(f"[csv_to_tex_params] ERROR: CSV not found: {CSV_PATH}")

    # key -> (value_with_unit, comment)
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

            # ignore blank rows / separator rows / comment rows
            if not key or not value:
                continue

            v = fmt_value(value, unit)
            if v == "":
                continue

            if key in items:
                raise SystemExit(f"[csv_to_tex_params] ERROR: duplicate key in CSV: {key}")

            items[key] = (v, comment)

    # sort by group then key
    sorted_keys = sorted(items.keys(), key=lambda k: (GROUP_ORDER[group_of_key(k)], k))

    OUT_TEX.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("% AUTO-GENERATED. DO NOT EDIT BY HAND.")
    lines.append("% Source: data/layout_params.csv")
    lines.append("% Access pattern: \\csname HB<key>\\endcsname")
    lines.append("")

    # grouped output
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
        if key.endswith("_viewport"):
            # body is v (no extra brace layer inside)
            lines.append(rf"\expandafter\def\csname HB{key}\endcsname{{{v}}}".replace("{{{v}}}", "{"+v+"}"))
        else:
            # body is {v} (extra brace layer inside)
            lines.append(rf"\expandafter\def\csname HB{key}\endcsname{{{v}}}")

        lines.append("")

    # aliases (only if both keys exist)
    emitted = []
    for old_key, new_key in ALIASES.items():
        if old_key in items and new_key in items:
            emitted.append((old_key, new_key))

    if emitted:
        lines.append("% ===== ALIASES (compat) =====")
        lines.append("% Format: \\def\\HB<old>{\\HB<new>} (forwarding)")
        lines.append("")
        for old_key, new_key in emitted:
            lines.append(f"% alias: {old_key} -> {new_key}")
            # OLD (remove)
            # lines.append(rf"\expandafter\let\csname HB{old_key}\expandafter\endcsname\csname HB{new_key}\endcsname")

            # NEW (use def forwarding)
            lines.append(rf"\expandafter\def\csname HB{old_key}\endcsname{{\csname HB{new_key}\endcsname}}")
            lines.append("")

    OUT_TEX.write_text("\n".join(lines), encoding="utf-8")
    print(f"[csv_to_tex_params] Wrote: {OUT_TEX}")


if __name__ == "__main__":
    main()
