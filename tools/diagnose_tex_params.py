#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Diagnose TeX parameter system stability
"""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

CSV_PATH = ROOT / "data" / "layout_params.csv"
PARAMS_PATH = ROOT / "docs" / "latex_theme" / "params.tex"


def check_file(path: Path):
    if not path.exists():
        print(f"[ERROR] Missing file: {path}")
        return False
    print(f"[OK] Found: {path}")
    return True


def analyze_params():
    content = PARAMS_PATH.read_text(encoding="utf-8")

    print("\n--- Checking for dangerous \\newcommand with underscores ---")
    bad_newcommand = re.findall(r"\\newcommand\{\\HB.*?\}", content)
    if bad_newcommand:
        print("[ERROR] Found \\newcommand HB macros (will break with underscores):")
        for b in bad_newcommand:
            print("  ", b)
    else:
        print("[OK] No \\newcommand HB macros")

    print("\n--- Checking for correct \\csname definitions ---")
    good_defs = re.findall(r"\\csname HB.*?\\endcsname", content)
    print(f"[INFO] Found {len(good_defs)} HB csname definitions")

    print("\n--- Checking for raw underscore in macro definitions ---")
    raw_underscore = re.findall(r"\\HB[a-zA-Z0-9_]*_", content)
    if raw_underscore:
        print("[ERROR] Raw underscore macro names detected:")
        for r in raw_underscore:
            print("  ", r)
    else:
        print("[OK] No raw underscore macros")

    print("\n--- Listing all HB keys defined ---")
    keys = re.findall(r"\\csname HB(.*?)\\endcsname", content)
    for k in keys:
        print("  HB" + k)


def main():
    print("========== TeX Param Diagnostic ==========\n")

    if not check_file(CSV_PATH):
        print("\n❌ layout_params.csv not found — this is likely the root cause.")
        return

    if not check_file(PARAMS_PATH):
        print("\n❌ params.tex not generated.")
        return

    analyze_params()

    print("\n========== Done ==========\n")


if __name__ == "__main__":
    main()
