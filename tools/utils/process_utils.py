#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path | None = None) -> None:
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


def open_file(path: Path) -> None:
    print(f"[build] Opening: {path}")
    if sys.platform.startswith("win"):
        os.startfile(str(path))
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)