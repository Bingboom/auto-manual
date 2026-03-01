#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import csv
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


def load_config(cfg_path: Path) -> dict:
    if not cfg_path.exists():
        raise RuntimeError(f"Config not found: {cfg_path}")

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


def validate_loaded_config(cfg: dict) -> None:
    issues = validate_cfg(cfg, strict_files=False)
    errors = [i for i in issues if i.level == "ERROR"]
    for issue in issues:
        print(f"[build] config {issue.level.lower()}: {issue.msg}")
    if errors:
        raise RuntimeError("Config validation failed")


def validate_layout_csv(layout_csv_path: Path) -> None:
    issues = validate_layout(layout_csv_path)
    errors = [i for i in issues if i.level == "ERROR"]
    for issue in issues:
        print(f"[build] layout {issue.level.lower()}: {issue.msg}")
    if errors:
        raise RuntimeError("Layout params validation failed")


def render_csv_pages(cfg: dict, sku: str | None) -> None:
    pages = cfg.get("pages", [])
    build_langs = cfg.get("build", {}).get("languages", [])

    phase1_pages: set[str] = set()
    phase1_langs: set[str] = set()

    for p in pages:
        if p.get("type") != "csv_page":
            continue

        page_name = p.get("page")
        if not isinstance(page_name, str) or not page_name.strip():
            raise RuntimeError("csv_page requires non-empty 'page'")

        source = (p.get("source") or "phase1").strip().lower()
        if source != "phase1":
            raise RuntimeError(f"Unsupported csv_page source='{source}' for page='{page_name}' (phase1-only)")

        phase1_pages.add(page_name)
        langs = p.get("langs", build_langs)
        for lang in langs:
            phase1_langs.add(str(lang))

    if phase1_pages:
        cmd = [sys.executable, "tools/phase1_build.py"]
        cmd += ["--page", ",".join(sorted(phase1_pages))]
        if phase1_langs:
            cmd += ["--lang", ",".join(sorted(phase1_langs))]
        if sku:
            cmd += ["--sku", sku]
        run(cmd, cwd=paths.root)


def _config_uses_sku_token(cfg: dict) -> bool:
    for page in cfg.get("pages", []):
        if not isinstance(page, dict):
            continue
        ptype = (page.get("type") or "").strip()
        if ptype == "cover_pdf":
            file_name = page.get("file")
            if isinstance(file_name, str) and "{sku}" in file_name:
                return True
        elif ptype == "csv_page":
            include_dir = page.get("include_dir")
            if isinstance(include_dir, str) and "{sku}" in include_dir:
                return True
        elif ptype == "pdf_insert":
            file_map = page.get("file_map")
            if isinstance(file_map, dict):
                for v in file_map.values():
                    if isinstance(v, str) and "{sku}" in v:
                        return True
    return False


def _list_skus(product_vars_csv: Path) -> list[str]:
    if not product_vars_csv.exists():
        return []
    skus: set[str] = set()
    with product_vars_csv.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            sku = (row.get("sku_id") or "").strip()
            if sku:
                skus.add(sku)
    return sorted(skus)


def resolve_build_sku(cfg: dict, arg_sku: str | None) -> str | None:
    if arg_sku and arg_sku.strip():
        return arg_sku.strip()

    build_cfg = cfg.get("build", {})
    default_sku = build_cfg.get("default_sku")
    if isinstance(default_sku, str) and default_sku.strip():
        picked = default_sku.strip()
        print(f"[build] sku not provided, using build.default_sku='{picked}'")
        return picked

    if not _config_uses_sku_token(cfg):
        return None

    product_vars_csv = paths.root / "data" / "phase1" / "product_variables.csv"
    skus = _list_skus(product_vars_csv)
    if not skus:
        raise RuntimeError(
            "config uses '{sku}' but no SKU was found in data/phase1/product_variables.csv"
        )

    picked = skus[0]
    if len(skus) > 1:
        print(
            "[build] sku not provided while config uses '{sku}'; "
            f"using '{picked}' from available SKUs {skus}. Pass --sku to override."
        )
    else:
        print(f"[build] sku not provided, inferred '{picked}' from product_variables.csv")
    return picked


def sphinx_build_html() -> None:
    print("[build] Sphinx -> HTML")
    run(["sphinx-build", "-b", "html", ".", "_build/html"], cwd=paths.docs_dir)


def sphinx_build_latex() -> None:
    print("[build] Sphinx -> LaTeX")
    run(["sphinx-build", "-b", "latex", ".", "_build/latex"], cwd=paths.docs_dir)


def patch_fonts(patch_fonts_script: str, main_tex: str) -> None:
    print("[build] Patch fonts (inject fonts.tex)")
    run([sys.executable, patch_fonts_script, "--tex", main_tex], cwd=paths.root)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml", help="Path to config yaml")
    ap.add_argument("--sku", default=None, help="Target SKU for phase1 pages / index includes")
    ap.add_argument("--clean", action="store_true", help="Delete docs/_build before building")
    ap.add_argument("--no-open", action="store_true", help="Do not open PDF after build (override config)")
    args = ap.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = paths.root / cfg_path

    cfg = load_config(cfg_path)
    build_cfg = cfg.get("build", {})
    tools_cfg = cfg.get("tools", {})

    print("[build] validating config...")
    validate_loaded_config(cfg)

    print("[build] validating layout params...")
    layout_csv = cfg.get("paths", {}).get("layout_params_csv")
    if not layout_csv:
        raise RuntimeError("config missing paths.layout_params_csv")

    validate_layout_csv(paths.root / layout_csv)

    main_tex = build_cfg.get("main_tex", "manual_demo.tex")
    output_pdf = build_cfg.get("output_pdf", "manual_demo.pdf")
    xelatex_runs = int(build_cfg.get("xelatex_runs", 3))
    open_after = bool(build_cfg.get("open_pdf", True)) and (not args.no_open)

    patch_fonts_script = str(tools_cfg.get("patch_fonts", "tools/patch_latex_fonts.py"))

    if args.clean:
        clean_build_dir()

    target_sku = resolve_build_sku(cfg, args.sku)

    render_csv_pages(cfg, sku=target_sku)

    doc_type = cfg.get("doc_type", "manual_bundle")
    if doc_type == "manual_bundle":
        index_cmd = [sys.executable, "tools/gen_index_bundle.py", "--config", str(cfg_path)]
        if target_sku:
            index_cmd += ["--sku", target_sku]
        run(index_cmd, cwd=paths.root)
    else:
        raise RuntimeError(f"Unsupported doc_type: {doc_type}")

    build_html = bool(build_cfg.get("build_html", False))
    open_html = bool(build_cfg.get("open_html", False)) and (not args.no_open)

    if build_html:
        sphinx_build_html()

    sphinx_build_latex()
    patch_fonts(patch_fonts_script, main_tex)
    compile_xelatex(main_tex, xelatex_runs, cwd=paths.latex_build_dir)

    pdf_path = paths.output_pdf(output_pdf)
    if not pdf_path.exists():
        raise RuntimeError(f"PDF not found: {pdf_path}")

    print(f"[build] Done. PDF: {pdf_path}")
    if open_after:
        open_file(pdf_path)

    if build_html and open_html:
        index_html = paths.docs_dir / "_build" / "html" / "index.html"
        if index_html.exists():
            open_file(index_html)


if __name__ == "__main__":
    main()
