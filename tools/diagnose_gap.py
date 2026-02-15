#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "docs" / "_build" / "latex"

PARAMS = BUILD / "params.tex"
CSAFETY = BUILD / "components_safety.tex"
TEX = BUILD / "safety_demo.tex"

KEYS = [
    "HBbrand_title_vspace_after",
    "HBwarn_box_before",
    "HBwarn_box_after",
    "HBbrand_title_pad_tb",
    "HBwarn_box_pad_tb",
]

def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")

def find_param_value(params_text: str, key: str) -> str | None:
    # matches: \expandafter\def\csname HBxxx\endcsname{0mm}
    m = re.search(rf"\\csname\s+{re.escape(key)}\\endcsname\{{([^}}]+)\}}", params_text)
    if m:
        return m.group(1).strip()
    return None

def extract_block(text: str, start_pat: str, end_pat: str, max_lines: int = 80) -> str:
    lines = text.splitlines()
    start_idx = None
    for i, l in enumerate(lines):
        if re.search(start_pat, l):
            start_idx = i
            break
    if start_idx is None:
        return f"[NOT FOUND] start pattern: {start_pat}"

    out = []
    for j in range(start_idx, min(len(lines), start_idx + max_lines)):
        out.append(f"{j+1:04d}: {lines[j]}")
        if re.search(end_pat, lines[j]):
            break
    return "\n".join(out)

def scan_parskip(tex_text: str) -> str:
    lines = tex_text.splitlines()
    hits = []
    for i, l in enumerate(lines, 1):
        if "parskip" in l.lower() or "\\parskip" in l:
            hits.append(f"{i:04d}: {l}")
    if not hits:
        return "(no 'parskip' mention found in safety_demo.tex; it may be inside sphinx .sty files)"
    return "\n".join(hits[:120])

def check_spacing_keywords(tex_text: str) -> str:
    # show whether section and safetywarning are adjacent
    lines = tex_text.splitlines()
    idx = None
    for i, l in enumerate(lines):
        if "\\section{IMPORTANT SAFETY INFORMATION}" in l:
            idx = i
            break
    if idx is None:
        return "No \\section{IMPORTANT SAFETY INFORMATION} found."
    start = max(0, idx - 5)
    end = min(len(lines), idx + 20)
    return "\n".join(f"{j+1:04d}: {lines[j]}" for j in range(start, end))

def main():
    print("BUILD DIR:", BUILD)
    for p in [PARAMS, CSAFETY, TEX]:
        print(f"- {p.name}: {'OK' if p.exists() else 'MISSING'}")

    if not (PARAMS.exists() and CSAFETY.exists() and TEX.exists()):
        print("\nRun: cd docs && sphinx-build -b latex . _build/latex")
        return

    params_text = read(PARAMS)
    cs_text = read(CSAFETY)
    tex_text = read(TEX)

    print("\n" + "="*80)
    print("1) PARAM VALUES (from build/params.tex)")
    print("="*80)
    for k in KEYS:
        v = find_param_value(params_text, k)
        print(f"{k:<28} = {v}")

    print("\n" + "="*80)
    print("2) H1 BOX (hbsectiontitle) SNIPPET (from build/components_safety.tex)")
    print("="*80)
    print(extract_block(cs_text, r"\\renewcommand\{\\hbsectiontitle\}", r"\\titleformat\{\\section\}"))

    print("\n" + "="*80)
    print("3) WARNING BOX (safetywarningbox) SNIPPET (from build/components_safety.tex)")
    print("="*80)
    print(extract_block(cs_text, r"\\newtcolorbox\{safetywarningbox\}", r"^\}"))

    print("\n" + "="*80)
    print("4) TEX AROUND SECTION -> WARNING (from build/safety_demo.tex)")
    print("="*80)
    print(check_spacing_keywords(tex_text))

    print("\n" + "="*80)
    print("5) PARSKIP / DEFAULT SPACING CLUES (from build/safety_demo.tex)")
    print("="*80)
    print(scan_parskip(tex_text))

    print("\n" + "="*80)
    print("6) QUICK DIAGNOSIS")
    print("="*80)
    bt = find_param_value(params_text, "HBbrand_title_vspace_after")
    wb = find_param_value(params_text, "HBwarn_box_before")
    if bt in {"0mm", "0"} and wb in {"0mm", "0"}:
        print("- You set both brand_title_vspace_after and warn_box_before to 0.")
        print("- If the gap still exists, it is almost certainly NOT from those two parameters.")
        print("- Most likely sources:")
        print("  (A) \\parskip is non-zero (parskip package).")
        print("  (B) hbsectiontitle tcolorbox still has after skip or is followed by \\par producing glue.")
        print("  (C) Sphinx/howto inserts extra vertical glue around section headings.")
        print("\nNext step fix (usually works immediately):")
        print("  Add to layout.tex:")
        print("    \\setlength{\\parindent}{0pt}")
        print("    \\setlength{\\parskip}{0pt}")
        print("  And inside hbsectiontitle tcolorbox add:")
        print("    before skip=0mm, after skip=0mm")
    else:
        print("- One of the params is not actually 0 in build/params.tex -> generation pipeline issue.")
        print("- Ensure you ran: python tools/csv_to_tex_params.py BEFORE sphinx-build.")
        print("- Ensure conf_base.py includes latex_theme/params.tex in latex_additional_files.")

if __name__ == "__main__":
    main()
