#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import shutil
from pathlib import Path

# Ensure repo root is importable (works on mac/win when running "python tools/xxx.py")
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.utils.path_utils import get_paths

paths = get_paths()


def run(cmd, cwd=None):
    pretty = " ".join(str(x) for x in cmd)
    print("$", pretty)
    subprocess.run([str(x) for x in cmd],
                   cwd=str(cwd) if cwd else None,
                   check=True)


def find_exe(names: list[str]) -> str | None:
    # 1) Search in PATH
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


def open_pdf(pdf_path: Path):
    print(f"[build_multilang_bundle] Opening PDF: {pdf_path}")
    if sys.platform.startswith("win"):
        os.startfile(str(pdf_path))
    elif sys.platform == "darwin":
        subprocess.run(["open", str(pdf_path)])
    else:
        subprocess.run(["xdg-open", str(pdf_path)])


def load_config() -> dict:
    """
    Load config.yaml from repo root.
    Requires PyYAML. (Install: pip install pyyaml)
    """
    cfg_path = paths.config_yaml
    if not cfg_path.exists():
        raise RuntimeError(f"config.yaml not found at repo root: {cfg_path}")

    try:
        import yaml
    except ImportError:
        raise RuntimeError("PyYAML not installed. Please run: pip install pyyaml")

    with cfg_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main():
    cfg = load_config()

    build_cfg = cfg.get("build", {})
    tools_cfg = cfg.get("tools", {})
    paths_cfg = cfg.get("paths", {})  # kept for forward compatibility

    languages = build_cfg.get("languages", ["en", "fr", "es"])
    main_tex = build_cfg.get("main_tex", "manual_demo.tex")
    output_pdf = build_cfg.get("output_pdf", "manual_demo.pdf")
    xelatex_runs = int(build_cfg.get("xelatex_runs", 3))
    should_open = bool(build_cfg.get("open_pdf", True))

    # tools paths remain config-driven (future: resolve via Paths too)
    csv_to_rst = str(tools_cfg.get("csv_to_rst", "tools/csv_to_rst.py"))
    patch_fonts = str(tools_cfg.get("patch_fonts", "tools/patch_latex_fonts.py"))

    # 1) Generate multi-language safety rst files
    for lang in languages:
        run([sys.executable, csv_to_rst, "--lang", lang], cwd=paths.root)

    # 2) Sphinx -> LaTeX
    run(["sphinx-build", "-b", "latex", ".", "_build/latex"], cwd=paths.docs_dir)

    # 3) Patch fonts (inject fonts.tex)
    run([sys.executable, patch_fonts, "--tex", main_tex], cwd=paths.root)

    # 4) Compile TeX -> PDF
    xelatex = find_exe(["xelatex"])
    if not xelatex:
        raise RuntimeError("xelatex not found. Please install MiKTeX/TeX Live and ensure xelatex exists.")

    for i in range(1, xelatex_runs + 1):
        print(f"[build_multilang_bundle] xelatex pass {i}/{xelatex_runs}")
        run([xelatex, "-interaction=nonstopmode", "-halt-on-error", main_tex],
            cwd=paths.latex_build_dir)

    # 5) Open generated PDF
    pdf_path = paths.output_pdf(output_pdf)
    if pdf_path.exists():
        if should_open:
            open_pdf(pdf_path)
        else:
            print(f"[build_multilang_bundle] Done. PDF: {pdf_path}")
    else:
        print(f"[build_multilang_bundle] WARNING: PDF not found at {pdf_path}")


if __name__ == "__main__":
    main()