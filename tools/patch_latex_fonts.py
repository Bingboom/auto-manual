#!/usr/bin/env python3
# tools/patch_latex_fonts.py
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
BUILD = DOCS / "_build" / "latex"
FONTS_SRC = DOCS / "latex_theme" / "fonts.tex"
FONTS_DST = BUILD / "fonts.tex"

def find_main_tex(build_dir: Path, preferred_name: str) -> Path:
    p = build_dir / preferred_name
    if p.exists():
        return p
    # fallback: any tex that contains \begin{document}
    for tex in sorted(build_dir.glob("*.tex")):
        if tex.name.lower().startswith("sphinx"):
            continue
        txt = tex.read_text(encoding="utf-8", errors="ignore")
        if r"\begin{document}" in txt:
            return tex
    raise RuntimeError("No main .tex found in build dir.")

def inject_before_begin_document(tex_path: Path) -> None:
    s = tex_path.read_text(encoding="utf-8", errors="ignore")
    if r"\input{fonts.tex}" in s:
        return  # already patched

    # Insert just before \begin{document}
    pat = r"(\\begin\{document\})"
    if not re.search(pat, s):
        raise RuntimeError(f"Cannot find \\begin{{document}} in {tex_path.name}")

    s2 = re.sub(pat, r"\\input{fonts.tex}\n\1", s, count=1)
    tex_path.write_text(s2, encoding="utf-8")
    print(f"[patch_latex_fonts] injected into: {tex_path.name}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tex", default="safety_demo.tex", help="main tex filename in _build/latex")
    args = ap.parse_args()

    if not BUILD.exists():
        raise SystemExit(f"[patch_latex_fonts] build dir not found: {BUILD}")

    if not FONTS_SRC.exists():
        raise SystemExit(f"[patch_latex_fonts] fonts.tex not found: {FONTS_SRC}")

    shutil.copyfile(FONTS_SRC, FONTS_DST)
    print(f"[patch_latex_fonts] copied fonts.tex -> {FONTS_DST}")

    main_tex = find_main_tex(BUILD, args.tex)
    inject_before_begin_document(main_tex)

if __name__ == "__main__":
    main()
