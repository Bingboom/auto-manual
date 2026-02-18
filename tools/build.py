#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import List
import argparse
import platform

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
BUILD_LATEX = DOCS / "_build" / "latex"


def run(cmd: List[str], cwd: Path | None = None) -> None:
    print(f"[build] $ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def find_main_tex(build_dir: Path) -> Path:
    # 1) Prefer known main doc name
    preferred = build_dir / "safety_demo.tex"
    if preferred.exists():
        return preferred

    # 2) Otherwise, choose a .tex that looks like a real Sphinx main document
    # Exclude known partials copied from latex_theme/*
    exclude = {
        "colors.tex",
        "params.tex",
        "layout.tex",
        "theme.tex",
        "components.tex",
        "components_base.tex",
        "components_safety.tex",
    }

    candidates = sorted(build_dir.glob("*.tex"))
    if not candidates:
        raise RuntimeError("No .tex found in docs/_build/latex. Did sphinx-build run?")

    for p in candidates:
        name = p.name.lower()
        if p.name in exclude:
            continue
        # Sphinx helper/cls-like files are not build targets
        if name.startswith("sphinx"):
            continue
        # Heuristic: main doc usually contains \begin{document}
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
            if r"\begin{document}" in txt:
                return p
        except Exception:
            pass

    # 3) Fallback: first non-excluded candidate
    for p in candidates:
        if p.name not in exclude:
            return p

    raise RuntimeError(f"Could not determine main .tex to compile in {build_dir}")



def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--open", action="store_true", help="open PDF after build")
    ap.add_argument("--tex", default="safety_demo.tex", help="main tex filename in _build/latex")
    args = ap.parse_args()

    # 1) lint
    run([sys.executable, "tools/lint_layout_params.py"], cwd=ROOT)

    # 2) generate params + rst
    run([sys.executable, "tools/csv_to_tex_params.py"], cwd=ROOT)
    run([sys.executable, "tools/csv_to_rst.py"], cwd=ROOT)

    # 3) clean build dir
    if (DOCS / "_build").exists():
        shutil.rmtree(DOCS / "_build")

    # 4) sphinx -> latex
    run(["sphinx-build", "-b", "latex", ".", "_build/latex"], cwd=DOCS)

    # 5) latexmk
    main_tex = BUILD_LATEX / args.tex
    if not main_tex.exists():
        raise RuntimeError(f"Main tex not found: {main_tex}")

    run(["latexmk", "-C"], cwd=BUILD_LATEX)
    run(["latexmk", "-xelatex", "-interaction=nonstopmode", "-halt-on-error", main_tex.name], cwd=BUILD_LATEX)

    pdf = main_tex.with_suffix(".pdf")
    if not pdf.exists():
        raise RuntimeError("latexmk finished but PDF not found.")

    print(f"[build] OK: {pdf}")

    # 6) open pdf
    if args.open:
        system = platform.system()
        print(f"[build] Opening PDF: {pdf}")
        if system == "Darwin":
            run(["open", pdf.name], cwd=BUILD_LATEX)
        elif system == "Windows":
            run(["cmd", "/c", "start", pdf.name], cwd=BUILD_LATEX)
        else:
            run(["xdg-open", pdf.name], cwd=BUILD_LATEX)


if __name__ == "__main__":
    main()
