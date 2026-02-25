#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LATEX_DIR = ROOT / "docs" / "_build" / "latex"
TEX = "manual_demo.tex"

def find_exe(names: list[str]) -> str | None:
    # 1) PATH
    for n in names:
        p = shutil.which(n)
        if p:
            return p

    # 2) Common MiKTeX locations (Windows)
    if os.name == "nt":
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
    if not LATEX_DIR.exists():
        print("[diag_xelatex_hang] latex dir not found:", LATEX_DIR)
        return

    xelatex = find_exe(["xelatex"])
    if not xelatex:
        raise RuntimeError("xelatex not found (PATH + common MiKTeX locations).")

    cmd = [xelatex, "-interaction=nonstopmode", TEX]
    print("[diag_xelatex_hang] cwd:", LATEX_DIR)
    print("[diag_xelatex_hang] cmd:", " ".join(cmd))

    p = subprocess.Popen(
        cmd,
        cwd=str(LATEX_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )

    last = time.time()
    last_line = ""

    while True:
        line = p.stdout.readline()
        if line:
            last = time.time()
            last_line = line.rstrip("\n")
            print(last_line)
        else:
            if p.poll() is not None:
                break
            if time.time() - last > 20:
                print("\n[diag_xelatex_hang] No output for 20s.")
                print("[diag_xelatex_hang] Last line:", last_line)
                print("[diag_xelatex_hang] Likely waiting for MiKTeX package install prompt, a locked PDF, or a stalled includepdf.")
                try:
                    p.terminate()
                except Exception:
                    pass
                break

    print("\n[diag_xelatex_hang] return code:", p.returncode)

if __name__ == "__main__":
    main()