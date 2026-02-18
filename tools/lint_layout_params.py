#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "layout_params.csv"

LATEX_DIRS = [
    ROOT / "docs" / "latex_theme",
]

KEY_REF_RE = re.compile(r"\\csname\s+HB([A-Za-z0-9_]+)\\endcsname")
NUM_RE = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)$")


ALLOWED_UNITS: Set[str] = {
    "", "none", "null",
    "mm", "pt", "em", "ex",
    "ratio", "int",
    "cmyk",
}


@dataclass
class Row:
    key: str
    value: str
    unit: str
    comment: str


def die(msg: str) -> None:
    print(f"[lint_layout_params] ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def warn(msg: str) -> None:
    print(f"[lint_layout_params] WARN: {msg}", file=sys.stderr)


def load_csv() -> List[Row]:
    if not CSV_PATH.exists():
        die(f"CSV not found: {CSV_PATH}")

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            die("CSV has no header row.")
        for col in ("key", "value", "unit", "comment"):
            if col not in reader.fieldnames:
                die(f"CSV missing required column: {col}")

        rows: List[Row] = []
        for r in reader:
            key = (r.get("key") or "").strip()
            value = (r.get("value") or "").strip()
            unit = (r.get("unit") or "").strip()
            comment = (r.get("comment") or "").strip()

            # allow blank separator rows
            if key == "" and value == "" and unit == "" and comment != "":
                rows.append(Row(key="", value="", unit="", comment=comment))
                continue
            if key == "" and value == "" and unit == "" and comment == "":
                continue

            rows.append(Row(key=key, value=value, unit=unit, comment=comment))
        return rows


def check_units_and_values(rows: List[Row]) -> Dict[str, Row]:
    seen: Dict[str, Row] = {}
    for row in rows:
        if not row.key:
            continue

        if row.key in seen:
            die(f"duplicate key: {row.key}")
        seen[row.key] = row

        u = row.unit.lower()
        if u not in ALLOWED_UNITS:
            die(f"invalid unit '{row.unit}' for key '{row.key}' (allowed: {sorted(ALLOWED_UNITS)})")

        if row.value == "":
            die(f"empty value for key '{row.key}'")

        # numeric validations
        if u in {"mm", "pt", "em", "ex", "ratio", "int"}:
            # viewport is special (space separated 4 ints)
            if row.key.endswith("_viewport"):
                parts = row.value.split()
                if len(parts) != 4 or not all(p.isdigit() for p in parts):
                    die(f"viewport must be 4 integers (x y w h): key='{row.key}', value='{row.value}'")
            elif u == "int":
                if not re.fullmatch(r"[+-]?\d+", row.value):
                    die(f"int must be integer: key='{row.key}', value='{row.value}'")
            else:
                if not NUM_RE.match(row.value):
                    die(f"numeric unit '{row.unit}' requires number: key='{row.key}', value='{row.value}'")

        if u == "cmyk":
            parts = [p.strip() for p in row.value.split(",")]
            if len(parts) != 4 or not all(NUM_RE.match(p) for p in parts):
                die(f"cmyk must be 4 numbers separated by commas: key='{row.key}', value='{row.value}'")
            

        # naming rule sanity
        if not (
            row.key.startswith("page_")
            or row.key.startswith("type_")
            or row.key.startswith("comp_")
            or row.key.startswith("brand_color_")
            or row.key == "section_after_fix"
        ):

            warn(f"non-v2 key naming detected: '{row.key}' (expected page_/type_/comp_ or section_after_fix)")

        # TeX escape sanity for bullet: should be single backslash style
        if row.key.endswith("bullet_symbol"):
            if "\\\\" in row.value:
                warn(f"'{row.key}' contains double backslash. CSV uses single backslash for TeX cmds: value='{row.value}'")

    return seen


def scan_tex_key_refs() -> Set[str]:
    refs: Set[str] = set()
    for d in LATEX_DIRS:
        if not d.exists():
            continue
        for p in d.rglob("*.tex"):
            text = p.read_text(encoding="utf-8", errors="ignore")
            for m in KEY_REF_RE.finditer(text):
                refs.add(m.group(1))
    return refs


def main() -> None:
    rows = load_csv()
    items = check_units_and_values(rows)

    refs = scan_tex_key_refs()

    # missing keys used by TeX
    missing = sorted(k for k in refs if k not in items)
    if missing:
        die("missing keys referenced in latex_theme/*.tex:\n  - " + "\n  - ".join(missing))

    # unused keys in CSV
    unused = sorted(k for k in items.keys() if k not in refs)
    if unused:
        warn("unused keys in layout_params.csv (defined but not referenced in latex_theme/*.tex):")
        for k in unused:
            warn(f"  - {k}")

    print("[lint_layout_params] OK")


if __name__ == "__main__":
    main()
