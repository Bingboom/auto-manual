#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

MAIN_TEX = "manual_demo.tex"
XE_RUNS = 3  # xelatex runs

def run(cmd, cwd=None):
    pretty = " ".join(str(x) for x in cmd)
    print("$", pretty)
    subprocess.run([str(x) for x in cmd], cwd=str(cwd) if cwd else None, check=True)

def find_exe(names: list[str]) -> str | None:
    # 1) PATH
    for n in names:
        p = shutil.which(n)
        if p:
            return p

    # 2) Common MiKTeX locations (Windows)
    candidates = [
        r"C:\Program Files\MiKTeX\miktex\bin\x64",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\MiKTeX\miktex\bin\x64"),
        os.path.expandvars(r"%LOCALAPPDATA%\MiKTeX\miktex\bin\x64"),
        os.path.expandvars(r"%APPDATA%\MiKTeX\miktex\bin\x64"),
    ]
    for base in candidates:
        if not base:
            continue
        base_path = Path(base)
        if not base_path.exists():
            continue
        for n in names:
            exe = base_path / f"{n}.exe"
            if exe.exists():
                return str(exe)
    return None

def main():
    # 1) Generate multi-language safety rst files
    for lang in ["en", "fr", "es"]:
        run([sys.executable, "tools/csv_to_rst.py", "--lang", lang], cwd=ROOT)

    # 2) Sphinx -> LaTeX
    run(["sphinx-build", "-b", "latex", ".", "_build/latex"], cwd=DOCS)

    latex_dir = DOCS / "_build" / "latex"
    
    run([sys.executable, "tools/patch_latex_fonts.py", "--tex", "manual_demo.tex"], cwd=ROOT)
    
    # 3) Compile TeX -> PDF (avoid latexmk on MiKTeX without perl)
    xelatex = find_exe(["xelatex"])
    if not xelatex:
        raise RuntimeError(
            "xelatex not found. Please install MiKTeX/TeX Live and ensure xelatex exists."
        )

    for i in range(1, XE_RUNS + 1):
        print(f"[build_multilang_bundle] xelatex pass {i}/{XE_RUNS}")
        run([xelatex, "-interaction=nonstopmode", "-halt-on-error", MAIN_TEX], cwd=latex_dir)

if __name__ == "__main__":
    main()