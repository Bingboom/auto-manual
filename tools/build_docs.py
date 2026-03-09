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
from tools.utils.process_utils import find_exe, open_file, run  # noqa: E402
from tools.utils.tex_utils import compile_xelatex  # noqa: E402
from tools.config_pages import CsvPage, parse_config_pages_or_raise
from tools.utils.spec_master import (
    resolve_product_name_from_spec_master,
    resolve_template_substitutions_from_spec_master,
)
from tools.utils.targets import (
    config_uses_token_in_pages,
    resolve_build_model as resolve_target_model,
    resolve_build_region as resolve_target_region,
)
from tools.word_bundle import export_word_from_bundle  # noqa: E402
from tools.word_bundle_common import load_rst_substitutions  # noqa: E402

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


def render_csv_pages(
    cfg: dict,
    model: str | None,
    region: str | None,
) -> None:
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
        if model:
            cmd += ["--model", model]
        if region:
            cmd += ["--region", region]
        spec_master_csv = paths_cfg.get("spec_master_csv")
        if isinstance(spec_master_csv, str) and spec_master_csv.strip():
            cmd += ["--spec-master-csv", spec_master_csv.strip()]
        spec_footnotes_csv = paths_cfg.get("spec_footnotes_csv")
        if isinstance(spec_footnotes_csv, str):
            cmd += ["--spec-footnotes-csv", spec_footnotes_csv.strip()]
        spec_titles_csv = paths_cfg.get("spec_titles_csv")
        if isinstance(spec_titles_csv, str):
            cmd += ["--spec-titles-csv", spec_titles_csv.strip()]
        run(cmd, cwd=paths.root)


def _config_uses_model_token(cfg: dict) -> bool:
    return config_uses_token_in_pages(cfg, "model")


def _config_uses_region_token(cfg: dict) -> bool:
    return config_uses_token_in_pages(cfg, "region")


def resolve_build_model(cfg: dict, arg_model: str | None) -> str | None:
    return resolve_target_model(cfg, arg_model)


def resolve_build_region(cfg: dict, arg_region: str | None) -> str | None:
    return resolve_target_region(cfg, arg_region)


def _resolve_spec_master_csv_path(cfg: dict) -> Path:
    paths_cfg_raw = cfg.get("paths", {})
    paths_cfg = paths_cfg_raw if isinstance(paths_cfg_raw, dict) else {}
    raw = paths_cfg.get("spec_master_csv")
    if isinstance(raw, str) and raw.strip():
        p = Path(raw.strip())
        return p if p.is_absolute() else (paths.root / p)
    return paths.root / "data" / "phase1" / "Spec_Master.csv"


def resolve_product_name_for_build(
    cfg: dict,
    *,
    model: str | None,
    region: str | None,
    lang: str,
) -> str | None:
    if not (model or "").strip():
        return None
    spec_master_csv = _resolve_spec_master_csv_path(cfg)
    match = resolve_product_name_from_spec_master(
        spec_master_csv,
        model=model,
        region=region,
        lang=lang,
    )
    if not match:
        return None
    return match.product_name


def resolve_rst_substitutions_for_build(
    cfg: dict,
    *,
    model: str | None,
    region: str | None,
    lang: str,
) -> dict[str, str]:
    base_substitutions = load_rst_substitutions(paths.docs_dir / "conf_base.py")
    if not (model or "").strip():
        return base_substitutions
    spec_master_csv = _resolve_spec_master_csv_path(cfg)
    return {
        **base_substitutions,
        **resolve_template_substitutions_from_spec_master(
            spec_master_csv,
            model=model,
            region=region,
            lang=lang,
        ),
    }


def _build_rst_epilog(substitutions: dict[str, str]) -> str:
    lines: list[str] = []
    for key, value in substitutions.items():
        text = (value or "").strip()
        if not text:
            continue
        lines.append(f".. |{key}| replace:: {text}")
    return "\n".join(lines)


def _with_rst_epilog(cmd: list[str], substitutions: dict[str, str] | None) -> list[str]:
    if not substitutions:
        return cmd
    epilog = _build_rst_epilog(substitutions)
    if not epilog:
        return cmd
    return [*cmd, "-D", f"rst_epilog={epilog}"]


def _with_product_name_epilog(cmd: list[str], product_name: str | None) -> list[str]:
    if not (product_name or "").strip():
        return cmd
    name = product_name.strip()
    return _with_rst_epilog(
        cmd,
        {
            "PRODUCT_NAME": name,
            "PRODUCT_NAME_BOLD": f"**{name}**",
        },
    )


def _resolve_sphinx_build_cmd(builder: str) -> list[str]:
    sphinx_build = find_exe(["sphinx-build"])
    if sphinx_build:
        return [sphinx_build, "-b", builder]
    return [sys.executable, "-m", "sphinx", "-b", builder]


def sphinx_build_html(
    minimal_theme: bool = False,
    substitutions: dict[str, str] | None = None,
) -> None:
    print("[build] Sphinx -> HTML")
    cmd = _resolve_sphinx_build_cmd("html") + [".", "_build/html"]
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
    cmd = _with_rst_epilog(cmd, substitutions)
    run(cmd, cwd=paths.docs_dir)


def sphinx_build_latex(substitutions: dict[str, str] | None = None) -> None:
    print("[build] Sphinx -> LaTeX")
    cmd = _with_rst_epilog(
        _resolve_sphinx_build_cmd("latex") + [".", "_build/latex"],
        substitutions,
    )
    run(cmd, cwd=paths.docs_dir)


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
    ap.add_argument("--model", default=None, help="Target product model for spec filtering")
    ap.add_argument("--region", default=None, help="Target region for spec/product-name filtering")
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
    target_region = resolve_build_region(cfg, args.region)
    needs_model_token = _config_uses_model_token(cfg)
    needs_region_token = _config_uses_region_token(cfg)
    if needs_model_token and not target_model:
        raise RuntimeError("config uses '{model}' but no --model was provided and build.default_model is empty")
    if needs_region_token and not target_region:
        raise RuntimeError("config uses '{region}' but no --region was provided and build.default_region is empty")

    build_langs = list(build_cfg.get("languages", ["en"]))
    primary_lang = str(build_langs[0]) if build_langs else "en"
    product_name = resolve_product_name_for_build(
        cfg,
        model=target_model,
        region=target_region,
        lang=primary_lang,
    )
    if target_model and not product_name:
        spec_master_csv = _resolve_spec_master_csv_path(cfg)
        raise RuntimeError(
            "Failed to resolve Product Name from Spec_Master.csv for "
            f"model='{target_model}', region='{target_region or ''}', lang='{primary_lang}'. "
            f"Source: {spec_master_csv}"
        )
    rst_substitutions = resolve_rst_substitutions_for_build(
        cfg,
        model=target_model,
        region=target_region,
        lang=primary_lang,
    )

    render_csv_pages(cfg, model=target_model, region=target_region)

    doc_type = cfg.get("doc_type", "manual_bundle")
    if doc_type == "manual_bundle":
        index_cmd = [sys.executable, "tools/gen_index_bundle.py", "--config", str(cfg_path)]
        if target_model:
            index_cmd += ["--model", target_model]
        if target_region:
            index_cmd += ["--region", target_region]
        run(index_cmd, cwd=paths.root)
    else:
        raise RuntimeError(f"Unsupported doc_type: {doc_type}")

    build_html = bool(build_cfg.get("build_html", False))
    open_html = bool(build_cfg.get("open_html", False)) and (not args.no_open)

    if build_html:
        sphinx_build_html(substitutions=rst_substitutions)

    if build_word and word_source == "html" and not build_html:
        sphinx_build_html(minimal_theme=True, substitutions=rst_substitutions)

    sphinx_build_latex(substitutions=rst_substitutions)
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
            docx_path = export_word_from_bundle(cfg, target_model, target_region, word_output)
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
