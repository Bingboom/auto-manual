#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


# Ensure repo root is importable when running "python tools/xxx.py"
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.utils.path_utils import get_paths  # noqa: E402
from tools.utils.process_utils import open_file, run  # noqa: E402
from tools.utils.tex_utils import compile_xelatex  # noqa: E402

from tools.validate_config import validate as validate_cfg
from tools.validate_layout_params import validate as validate_layout

paths = get_paths()


def load_config() -> dict:
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


def render_csv_pages(cfg: dict) -> None:
    pages = cfg.get("pages", [])
    gens = cfg.get("tools", {}).get("generators", {})

    for p in pages:
        if p.get("type") != "csv_page":
            continue

        page_name = p.get("page")
        if page_name not in gens:
            raise RuntimeError(f"No generator configured for csv_page '{page_name}'")

        script = gens[page_name]
        langs = p.get("langs", cfg.get("build", {}).get("languages", []))
        for lang in langs:
            cmd = [sys.executable, script, "--lang", lang]

            # optional overrides from config
            if "csv" in p:
                cmd += ["--csv", str(p["csv"])]
            if "template" in p:
                cmd += ["--template", str(p["template"])]
            if "out_prefix" in p:
                cmd += ["--out-prefix", str(p["out_prefix"])]

            run(cmd, cwd=paths.root)


def sphinx_build_latex() -> None:
    print("[build] Sphinx -> LaTeX")
    run(["sphinx-build", "-b", "latex", ".", "_build/latex"], cwd=paths.docs_dir)


def patch_fonts(patch_fonts_script: str, main_tex: str) -> None:
    print("[build] Patch fonts (inject fonts.tex)")
    run([sys.executable, patch_fonts_script, "--tex", main_tex], cwd=paths.root)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean", action="store_true", help="Delete docs/_build before building")
    ap.add_argument("--no-open", action="store_true", help="Do not open PDF after build (override config)")
    args = ap.parse_args()

    cfg = load_config()
    build_cfg = cfg.get("build", {})
    tools_cfg = cfg.get("tools", {})

    print("[build] validating config...")
    validate_cfg(load_config(), strict_files=False)

    print("[build] validating layout params...")
    layout_csv = cfg.get("paths", {}).get("layout_params_csv")
    if not layout_csv:
        raise RuntimeError("config.yaml missing paths.layout_params_csv")

    validate_layout(paths.root / layout_csv)

    langs = build_cfg.get("languages", ["en", "fr", "es"])
    main_tex = build_cfg.get("main_tex", "manual_demo.tex")
    output_pdf = build_cfg.get("output_pdf", "manual_demo.pdf")
    xelatex_runs = int(build_cfg.get("xelatex_runs", 3))
    open_after = bool(build_cfg.get("open_pdf", True)) and (not args.no_open)

    csv_to_rst = str(tools_cfg.get("csv_to_rst", "tools/csv_to_rst.py"))
    patch_fonts_script = str(tools_cfg.get("patch_fonts", "tools/patch_latex_fonts.py"))

    if args.clean:
        clean_build_dir()

    render_csv_pages(cfg)

    doc_type = cfg.get("doc_type", "manual_bundle")
    if doc_type == "manual_bundle":
        run([sys.executable, "tools/gen_index_bundle.py"], cwd=paths.root)
    else:
        raise RuntimeError(f"Unsupported doc_type: {doc_type}")
    
    sphinx_build_latex()
    patch_fonts(patch_fonts_script, main_tex)
    compile_xelatex(main_tex, xelatex_runs, cwd=paths.latex_build_dir)

    pdf_path = paths.output_pdf(output_pdf)
    if not pdf_path.exists():
        raise RuntimeError(f"PDF not found: {pdf_path}")

    print(f"[build] Done. PDF: {pdf_path}")
    if open_after:
        open_file(pdf_path)


if __name__ == "__main__":
    main()