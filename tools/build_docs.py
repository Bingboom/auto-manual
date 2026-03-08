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
from tools.config_pages import CsvPage, parse_config_pages_or_raise
from tools.utils.targets import (
    config_uses_token_in_pages,
    resolve_build_model as resolve_target_model,
    resolve_sku_from_inputs,
)
from tools.word_bundle import export_word_from_bundle  # noqa: E402

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


def render_csv_pages(cfg: dict, sku: str | None, model: str | None) -> None:
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    pages = parse_config_pages_or_raise(
        cfg.get("pages"),
        default_languages=list(build_cfg.get("languages", [])),
        error_prefix="config.pages",
    )
    build_langs = cfg.get("build", {}).get("languages", [])
    paths_cfg_raw = cfg.get("paths", {})
    paths_cfg = paths_cfg_raw if isinstance(paths_cfg_raw, dict) else {}

    phase1_pages: set[str] = set()
    phase1_langs: set[str] = set()

    for page in pages:
        if not isinstance(page, CsvPage):
            continue

        page_name = page.page
        source = page.source
        if source != "phase1":
            raise RuntimeError(f"Unsupported csv_page source='{source}' for page='{page_name}' (phase1-only)")

        phase1_pages.add(page_name)
        langs = list(page.langs) or build_langs
        for lang in langs:
            phase1_langs.add(str(lang))

    if phase1_pages:
        cmd = [sys.executable, "tools/phase1_build.py"]
        cmd += ["--page", ",".join(sorted(phase1_pages))]
        if phase1_langs:
            cmd += ["--lang", ",".join(sorted(phase1_langs))]
        if sku:
            cmd += ["--sku", sku]
        if model:
            cmd += ["--model", model]
        spec_master_csv = paths_cfg.get("spec_master_csv")
        if isinstance(spec_master_csv, str) and spec_master_csv.strip():
            cmd += ["--spec-master-csv", spec_master_csv.strip()]
        spec_footnotes_csv = paths_cfg.get("spec_footnotes_csv")
        if isinstance(spec_footnotes_csv, str):
            cmd += ["--spec-footnotes-csv", spec_footnotes_csv.strip()]
        run(cmd, cwd=paths.root)


def _config_uses_sku_token(cfg: dict) -> bool:
    return config_uses_token_in_pages(cfg, "sku")


def _config_uses_model_token(cfg: dict) -> bool:
    return config_uses_token_in_pages(cfg, "model")


def resolve_build_model(cfg: dict, arg_model: str | None) -> str | None:
    return resolve_target_model(cfg, arg_model)


def resolve_build_sku(cfg: dict, arg_sku: str | None, arg_model: str | None = None) -> str | None:
    return resolve_sku_from_inputs(
        cfg,
        arg_sku=arg_sku,
        arg_model=arg_model,
        root=paths.root,
        requires_sku_token=_config_uses_sku_token(cfg),
        log_prefix="build",
    )


def sphinx_build_html(minimal_theme: bool = False) -> None:
    print("[build] Sphinx -> HTML")
    cmd = ["sphinx-build", "-b", "html", ".", "_build/html"]
    if minimal_theme:
        # Built-in theme path for HTML->DOCX conversion, avoids optional third-party theme dependency.
        cmd += [
            "-D",
            "html_theme=alabaster",
            "-D",
            "html_css_files=[]",
            "-D",
            "html_js_files=[]",
        ]
    run(cmd, cwd=paths.docs_dir)


def sphinx_build_latex() -> None:
    print("[build] Sphinx -> LaTeX")
    run(["sphinx-build", "-b", "latex", ".", "_build/latex"], cwd=paths.docs_dir)


def patch_fonts(patch_fonts_script: str, main_tex: str) -> None:
    print("[build] Patch fonts (inject fonts.tex)")
    run([sys.executable, patch_fonts_script, "--tex", main_tex], cwd=paths.root)


def export_word_from_latex(main_tex: str, word_output: str) -> Path:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise RuntimeError("pandoc is required for Word export. Please install pandoc first.")

    tex_path = paths.main_tex(main_tex)
    if not tex_path.exists():
        raise RuntimeError(f"LaTeX source not found for Word export: {tex_path}")

    out_path = Path(word_output)
    if not out_path.is_absolute():
        out_path = paths.docs_build_dir / "word" / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print("[build] Convert LaTeX -> DOCX")
    run(
        [
            pandoc,
            str(tex_path),
            "--from=latex",
            "--to=docx",
            "--resource-path",
            str(paths.latex_build_dir),
            "-o",
            str(out_path),
        ],
        cwd=paths.root,
    )
    return out_path


def export_word_from_html(word_output: str) -> Path:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise RuntimeError("pandoc is required for Word export. Please install pandoc first.")

    html_index = paths.docs_dir / "_build" / "html" / "index.html"
    if not html_index.exists():
        raise RuntimeError(f"HTML source not found for Word export: {html_index}")

    out_path = Path(word_output)
    if not out_path.is_absolute():
        out_path = paths.docs_build_dir / "word" / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print("[build] Convert HTML -> DOCX")
    run(
        [
            pandoc,
            str(html_index),
            "--from=html",
            "--to=docx",
            "--resource-path",
            str(html_index.parent),
            "-o",
            str(out_path),
        ],
        cwd=paths.root,
    )
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml", help="Path to config yaml")
    ap.add_argument("--sku", default=None, help="Target SKU for phase1 pages / index includes")
    ap.add_argument("--model", default=None, help="Target product model for spec filtering / sku resolving")
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
    build_word = bool(build_cfg.get("build_word", False))
    word_output = str(build_cfg.get("word_output", "manual_demo.docx"))
    word_source = str(build_cfg.get("word_source", "latex")).strip().lower()
    open_word = bool(build_cfg.get("open_word", False)) and (not args.no_open)

    patch_fonts_script = str(tools_cfg.get("patch_fonts", "tools/patch_latex_fonts.py"))

    if args.clean:
        clean_build_dir()

    target_model = resolve_build_model(cfg, args.model)
    needs_sku_token = _config_uses_sku_token(cfg)
    needs_model_token = _config_uses_model_token(cfg)
    if needs_model_token and not target_model:
        raise RuntimeError("config uses '{model}' but no --model was provided and build.default_model is empty")

    explicit_sku = (args.sku or "").strip() or None
    if explicit_sku:
        target_sku = explicit_sku
    elif needs_sku_token or not target_model:
        target_sku = resolve_build_sku(cfg, None, args.model)
    else:
        target_sku = None

    render_csv_pages(cfg, sku=target_sku, model=target_model)

    doc_type = cfg.get("doc_type", "manual_bundle")
    if doc_type == "manual_bundle":
        index_cmd = [sys.executable, "tools/gen_index_bundle.py", "--config", str(cfg_path)]
        if target_sku:
            index_cmd += ["--sku", target_sku]
        if target_model:
            index_cmd += ["--model", target_model]
        run(index_cmd, cwd=paths.root)
    else:
        raise RuntimeError(f"Unsupported doc_type: {doc_type}")

    build_html = bool(build_cfg.get("build_html", False))
    open_html = bool(build_cfg.get("open_html", False)) and (not args.no_open)

    if build_html:
        sphinx_build_html()

    if build_word and word_source == "html" and not build_html:
        sphinx_build_html(minimal_theme=True)

    sphinx_build_latex()
    patch_fonts(patch_fonts_script, main_tex)
    compile_xelatex(main_tex, xelatex_runs, cwd=paths.latex_build_dir)

    pdf_path = paths.output_pdf(output_pdf)
    if not pdf_path.exists():
        raise RuntimeError(f"PDF not found: {pdf_path}")

    print(f"[build] Done. PDF: {pdf_path}")
    if open_after:
        open_file(pdf_path)

    if build_word:
        if word_source == "html":
            docx_path = export_word_from_html(word_output)
        elif word_source == "latex":
            docx_path = export_word_from_latex(main_tex, word_output)
        elif word_source == "bundle":
            docx_path = export_word_from_bundle(cfg, target_sku, target_model, word_output)
        else:
            raise RuntimeError("build.word_source must be one of 'latex', 'html', or 'bundle'")
        print(f"[build] Done. DOCX: {docx_path}")
        if open_word:
            open_file(docx_path)

    if build_html and open_html:
        index_html = paths.docs_dir / "_build" / "html" / "index.html"
        if index_html.exists():
            open_file(index_html)


if __name__ == "__main__":
    main()
