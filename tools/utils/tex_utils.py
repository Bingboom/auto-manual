#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path

from tools.utils.process_utils import find_exe, run


def compile_xelatex(tex_name: str, runs: int, cwd: Path) -> None:
    xelatex = find_exe(["xelatex"])
    if not xelatex:
        raise RuntimeError("xelatex not found. Install MiKTeX/TeX Live.")

    for i in range(1, runs + 1):
        print(f"[build] xelatex pass {i}/{runs}")
        run([xelatex, "-interaction=nonstopmode", "-halt-on-error", tex_name], cwd=cwd)