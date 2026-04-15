#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/validate_layout_params.py

Validates layout_params.csv
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)


@dataclass
class Issue:
    level: str
    msg: str


KNOWN_UNITS = {"mm", "pt", "em", "ex", "ratio", "int", "none", "cmyk"}

REQUIRED_KEYS = {
    "page_paperwidth",
    "page_paperheight",
    "page_margin_left",
    "page_margin_right",
    "page_margin_top",
    "page_margin_bottom",
}


def as_path(p: str) -> Path:
    pp = Path(p)
    return pp if pp.is_absolute() else (ROOT / pp)


def parse_number(val: str) -> bool:
    try:
        float(val)
        return True
    except Exception:
        return False


def validate(csv_path: Path) -> list[Issue]:
    issues: list[Issue] = []

    if not csv_path.exists():
        return [Issue("ERROR", f"CSV not found: {csv_path}")]

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        if not reader.fieldnames:
            return [Issue("ERROR", "CSV has no header")]

        for col in ["key", "value", "unit", "comment"]:
            if col not in reader.fieldnames:
                issues.append(Issue("ERROR", f"Missing column: {col}"))

        seen = set()
        keys_present = set()

        for idx, row in enumerate(reader, start=2):
            key = (row.get("key") or "").strip()
            val = (row.get("value") or "").strip()
            unit = (row.get("unit") or "").strip()

            if not key:
                continue

            if key in seen:
                issues.append(Issue("ERROR", f"Duplicate key '{key}' line {idx}"))
                continue
            seen.add(key)
            keys_present.add(key)

            if unit not in KNOWN_UNITS:
                issues.append(Issue("ERROR", f"Unknown unit '{unit}' for key '{key}' line {idx}"))

            if unit in {"mm", "pt", "em", "ex", "ratio"}:
                if not parse_number(val):
                    issues.append(Issue("ERROR", f"Numeric value expected for '{key}' line {idx}"))
            elif unit == "int":
                try:
                    int(val)
                except Exception:
                    issues.append(Issue("ERROR", f"Integer value expected for '{key}' line {idx}"))
            elif unit == "cmyk":
                parts = val.strip('"').split(",")
                if len(parts) != 4:
                    issues.append(Issue("ERROR", f"CMYK requires 4 values for '{key}' line {idx}"))

        missing = REQUIRED_KEYS - keys_present
        if missing:
            issues.append(Issue("ERROR", f"Missing required keys: {sorted(missing)}"))

    return issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="data/layout_params.csv")
    args = ap.parse_args()

    csv_path = as_path(args.csv)
    issues = validate(csv_path)

    errors = [i for i in issues if i.level == "ERROR"]

    for i in issues:
        print(f"[validate_layout_params] {i.level}: {i.msg}")

    if errors:
        raise SystemExit(1)

    print("[validate_layout_params] OK")


if __name__ == "__main__":
    main()
