#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Ensure repo root is importable when running "python tools/xxx.py"
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.utils.path_utils import get_paths  # noqa: E402

paths = get_paths()


def run(cmd: list[str], cwd: Path | None = None) -> None:
    pretty = " ".join(str(x) for x in cmd)
    print("$", pretty)
    subprocess.run([str(x) for x in cmd], cwd=str(cwd) if cwd else None, check=True)


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


def open_pdf(pdf_path: Path) -> None:
    print(f"[build] Opening PDF: {pdf_path}")
    if sys.platform.startswith("win"):
        os.startfile(str(pdf_path))
    elif sys.platform == "darwin":
        subprocess.run(["open", str(pdf_path)])
    else:
        subprocess.run(["xdg-open", str(pdf_path)])


def load_config() -> dict:
    """
    Load config.yaml from repo root. Requires PyYAML.
    """
    cfg_path = paths.config_yaml
    if not cfg_path.exists():
        raise RuntimeError(f"config.yaml not found: {cfg_path}")

    try:
        import yaml  # type: ignore
    except ImportError:
        raise RuntimeError("PyYAML not installed. Please run: pip install pyyaml")

    with cfg_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def clean_build_dir() -> None:
    if paths.docs_build_dir.exists():
        print(f"[build] Cleaning: {paths.docs_build_dir}")
        shutil.rmtree(paths.docs_build_dir)


def render_safety_all_langs(csv_to_rst: str, langs: list[str]) -> None:
    print(f"[build] Render safety RST for langs: {langs}")
    for lang in langs:
        run([sys.executable, csv_to_rst, "--lang", lang], cwd=paths.root)


def sphinx_build_latex() -> None:
    print("[build] Sphinx -> LaTeX")
    run(["sphinx-build", "-b", "latex", ".", "_build/latex"], cwd=paths.docs_dir)


def patch_fonts(patch_fonts_script: str, main_tex: str) -> None:
    print("[build] Patch fonts (inject fonts.tex)")
    run([sys.executable, patch_fonts_script, "--tex", main_tex], cwd=paths.root)


def compile_xelatex(main_tex: str, runs: int) -> None:
    xelatex = find_exe(["xelatex"])
    if not xelatex:
        raise RuntimeError("xelatex not found. Install MiKTeX/TeX Live.")

    for i in range(1, runs + 1):
        print(f"[build] xelatex pass {i}/{runs}")
        run([xelatex, "-interaction=nonstopmode", "-halt-on-error", main_tex], cwd=paths.latex_build_dir)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean", action="store_true", help="Delete docs/_build before building")
    ap.add_argument("--no-open", action="store_true", help="Do not open PDF after build (override config)")
    args = ap.parse_args()

    cfg = load_config()
    build_cfg = cfg.get("build", {})
    tools_cfg = cfg.get("tools", {})

    langs = build_cfg.get("languages", ["en", "fr", "es"])
    main_tex = build_cfg.get("main_tex", "manual_demo.tex")
    output_pdf = build_cfg.get("output_pdf", "manual_demo.pdf")
    xelatex_runs = int(build_cfg.get("xelatex_runs", 3))
    open_after = bool(build_cfg.get("open_pdf", True)) and (not args.no_open)

    csv_to_rst = str(tools_cfg.get("csv_to_rst", "tools/csv_to_rst.py"))
    patch_fonts_script = str(tools_cfg.get("patch_fonts", "tools/patch_latex_fonts.py"))

    if args.clean:
        clean_build_dir()

    # Pipeline
    render_safety_all_langs(csv_to_rst, list(langs))
    sphinx_build_latex()
    patch_fonts(patch_fonts_script, main_tex)
    compile_xelatex(main_tex, xelatex_runs)

    pdf_path = paths.output_pdf(output_pdf)
    if not pdf_path.exists():
        raise RuntimeError(f"PDF not found: {pdf_path}")

    print(f"[build] Done. PDF: {pdf_path}")
    if open_after:
        open_pdf(pdf_path)


if __name__ == "__main__":
    main()