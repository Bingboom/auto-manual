#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path


# Ensure repo root is importable when running "python tools/xxx.py"
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.config_pages import CsvPage, parse_config_pages_or_raise
from tools.gen_index_bundle import MaterializedBundle, materialize_bundle
from tools.utils.path_utils import get_paths  # noqa: E402
from tools.utils.process_utils import find_exe, open_file, run  # noqa: E402
from tools.utils.spec_master import (
    resolve_product_name_from_spec_master,
    resolve_template_substitutions_from_spec_master,
)
from tools.utils.targets import (
    config_uses_token_in_pages,
    resolve_build_model as resolve_target_model,
    resolve_build_region as resolve_target_region,
)
from tools.utils.tex_utils import compile_xelatex  # noqa: E402
from tools.word_bundle import export_word_from_bundle  # noqa: E402
from tools.word_bundle_common import load_rst_substitutions  # noqa: E402

from tools.validate_config import validate as validate_cfg
from tools.validate_layout_params import validate as validate_layout

paths = get_paths()
VALID_FORMATS = {"html", "word", "pdf"}
VALID_PDF_MODES = {"latex", "word"}


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


def _load_configured_html_theme(conf_base_path: Path) -> str | None:
    if not conf_base_path.exists():
        return None
    for line in conf_base_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("html_theme"):
            continue
        _, _, raw = stripped.partition("=")
        value = raw.split("#", 1)[0].strip().strip("\"'")
        return value or None
    return None


def _should_use_minimal_html_theme(conf_dir: Path, requested_minimal: bool) -> bool:
    if requested_minimal:
        return True
    theme_name = _load_configured_html_theme(conf_dir / "conf_base.py")
    if not theme_name or theme_name in {"alabaster", "classic", "basic"}:
        return False
    if importlib.util.find_spec(theme_name) is not None:
        return False
    print(f"[build] HTML theme '{theme_name}' not available, fallback to alabaster")
    return True


def _target_component(value: str | None, fallback: str) -> str:
    text = (value or "").strip() or fallback
    return text.replace("/", "_").replace("\\", "_").replace(":", "_")


def build_root_for_target(model: str | None, region: str | None) -> Path:
    return paths.docs_build_dir / _target_component(model, "_shared") / _target_component(region, "_default")


def _parse_csv_values(raw: str) -> list[str]:
    items = [item.strip().lower() for item in raw.split(",")]
    return [item for item in items if item]


def resolve_requested_formats(cfg: dict, cli_formats: str | None) -> list[str]:
    if cli_formats and cli_formats.strip():
        formats = _parse_csv_values(cli_formats)
    else:
        build_cfg_raw = cfg.get("build", {})
        build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
        configured = build_cfg.get("formats")
        if isinstance(configured, str) and configured.strip():
            formats = _parse_csv_values(configured)
        elif isinstance(configured, list):
            formats = [str(item).strip().lower() for item in configured if str(item).strip()]
        else:
            formats = []
            if bool(build_cfg.get("build_html", False)):
                formats.append("html")
            if bool(build_cfg.get("build_word", False)):
                formats.append("word")
            if not formats:
                formats.append("pdf")

    unknown = sorted(set(formats) - VALID_FORMATS)
    if unknown:
        raise RuntimeError(f"Unsupported formats: {', '.join(unknown)}")
    return list(dict.fromkeys(formats))


def resolve_pdf_mode(cfg: dict, cli_pdf_mode: str | None) -> str:
    if cli_pdf_mode and cli_pdf_mode.strip():
        mode = cli_pdf_mode.strip().lower()
    else:
        pdf_cfg_raw = cfg.get("pdf", {})
        pdf_cfg = pdf_cfg_raw if isinstance(pdf_cfg_raw, dict) else {}
        mode = str(pdf_cfg.get("mode", "latex")).strip().lower()
    if mode not in VALID_PDF_MODES:
        raise RuntimeError(f"Unsupported pdf mode: {mode}")
    return mode


def resolve_output_path(base_dir: Path, configured_name: str) -> Path:
    out_path = Path(configured_name)
    if out_path.is_absolute():
        return out_path
    return base_dir / out_path


def sphinx_build(
    builder: str,
    *,
    src_dir: Path,
    out_dir: Path,
    conf_dir: Path,
    minimal_theme: bool = False,
    substitutions: dict[str, str] | None = None,
) -> None:
    print(f"[build] Sphinx -> {builder.upper()}")
    out_dir.mkdir(parents=True, exist_ok=True)
    actual_minimal_theme = _should_use_minimal_html_theme(conf_dir, minimal_theme) if builder == "html" else False
    cmd = _resolve_sphinx_build_cmd(builder) + [str(src_dir), str(out_dir), "-c", str(conf_dir)]
    if builder == "html" and actual_minimal_theme:
        cmd += [
            "-D",
            "html_theme=alabaster",
            "-D",
            "html_css_files=[]",
            "-D",
            "html_js_files=[]",
        ]
    cmd = _with_rst_epilog(cmd, substitutions)
    run(cmd, cwd=paths.root)


def patch_fonts(patch_fonts_script: str, main_tex: str, *, build_dir: Path) -> None:
    print("[build] Patch fonts (inject fonts.tex)")
    run(
        [
            sys.executable,
            patch_fonts_script,
            "--tex",
            main_tex,
            "--build-dir",
            str(build_dir),
        ],
        cwd=paths.root,
    )


def export_word_from_latex(
    tex_path: Path,
    *,
    resource_dir: Path,
    out_path: Path,
) -> Path:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise RuntimeError("pandoc is required for Word export. Please install pandoc first.")
    if not tex_path.exists():
        raise RuntimeError(f"LaTeX source not found for Word export: {tex_path}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    print("[build] Convert LaTeX -> DOCX")
    run(
        [
            pandoc,
            str(tex_path),
            "--from=latex",
            "--to=docx",
            "--resource-path",
            str(resource_dir),
            "-o",
            str(out_path),
        ],
        cwd=paths.root,
    )
    return out_path


def export_word_from_html(
    html_index: Path,
    *,
    out_path: Path,
) -> Path:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise RuntimeError("pandoc is required for Word export. Please install pandoc first.")
    if not html_index.exists():
        raise RuntimeError(f"HTML source not found for Word export: {html_index}")

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


def export_pdf_from_docx_via_word(docx_path: Path, pdf_path: Path) -> Path:
    if not sys.platform.startswith("win"):
        raise RuntimeError("pdf mode 'word' is supported on Windows only")
    if not docx_path.exists():
        raise RuntimeError(f"DOCX source not found for PDF export: {docx_path}")

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    docx_literal = str(docx_path).replace("'", "''")
    pdf_literal = str(pdf_path).replace("'", "''")
    script = f"""
$ErrorActionPreference = 'Stop'
$docxPath = '{docx_literal}'
$pdfPath = '{pdf_literal}'
$word = $null
$doc = $null
$wdFormatPDF = 17
try {{
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $doc = $word.Documents.Open($docxPath, $false, $true)
    $doc.SaveAs([ref]$pdfPath, [ref]$wdFormatPDF)
}} finally {{
    if ($doc) {{
        $doc.Close([ref]$false)
    }}
    if ($word) {{
        $word.Quit()
    }}
}}
"""
    subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        check=True,
        cwd=str(paths.root),
    )
    return pdf_path


def ensure_target_identity(
    cfg: dict,
    *,
    model: str | None,
    region: str | None,
    lang: str,
) -> None:
    if not model:
        return
    product_name = resolve_product_name_for_build(
        cfg,
        model=model,
        region=region,
        lang=lang,
    )
    if product_name:
        return
    spec_master_csv = _resolve_spec_master_csv_path(cfg)
    raise RuntimeError(
        "Failed to resolve Product Name from Spec_Master.csv for "
        f"model='{model}', region='{region or ''}', lang='{lang}'. "
        f"Source: {spec_master_csv}"
    )


def prepare_manual_bundle(
    cfg: dict,
    *,
    model: str | None,
    region: str | None,
) -> MaterializedBundle:
    render_csv_pages(cfg, model=model, region=region)

    doc_type = cfg.get("doc_type", "manual_bundle")
    if doc_type != "manual_bundle":
        raise RuntimeError(f"Unsupported doc_type: {doc_type}")

    bundle = materialize_bundle(cfg, model=model, region=region)
    print(f"[build] Prepared bundle: {bundle.bundle_dir}")
    return bundle


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml", help="Path to config yaml")
    ap.add_argument("--model", default=None, help="Target product model for spec filtering")
    ap.add_argument("--region", default=None, help="Target region for spec/product-name filtering")
    ap.add_argument("--formats", default=None, help="Comma-separated outputs: html,word,pdf")
    ap.add_argument("--pdf-mode", default=None, help="PDF backend: latex or word")
    ap.add_argument("--prepare-only", action="store_true", help="Only materialize target rst bundle")
    ap.add_argument("--clean", action="store_true", help="Delete docs/_build before building")
    ap.add_argument("--no-open", action="store_true", help="Do not open outputs after build (override config)")
    args = ap.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = paths.root / cfg_path

    cfg = load_config(cfg_path)
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    tools_cfg_raw = cfg.get("tools", {})
    tools_cfg = tools_cfg_raw if isinstance(tools_cfg_raw, dict) else {}

    print("[build] validating config...")
    validate_loaded_config(cfg)

    print("[build] validating layout params...")
    layout_csv = cfg.get("paths", {}).get("layout_params_csv")
    if not layout_csv:
        raise RuntimeError("config missing paths.layout_params_csv")
    validate_layout_csv(paths.root / layout_csv)

    if args.clean:
        clean_build_dir()

    target_model = resolve_build_model(cfg, args.model)
    target_region = resolve_build_region(cfg, args.region)
    if _config_uses_model_token(cfg) and not target_model:
        raise RuntimeError("config uses '{model}' but no --model was provided and build.default_model is empty")
    if _config_uses_region_token(cfg) and not target_region:
        raise RuntimeError("config uses '{region}' but no --region was provided and build.default_region is empty")

    build_langs = list(build_cfg.get("languages", ["en"]))
    primary_lang = str(build_langs[0]) if build_langs else "en"
    ensure_target_identity(
        cfg,
        model=target_model,
        region=target_region,
        lang=primary_lang,
    )

    bundle = prepare_manual_bundle(
        cfg,
        model=target_model,
        region=target_region,
    )
    if args.prepare_only:
        return

    requested_formats = resolve_requested_formats(cfg, args.formats)
    pdf_mode = resolve_pdf_mode(cfg, args.pdf_mode) if "pdf" in requested_formats else "latex"

    main_tex = str(build_cfg.get("main_tex", "manual_demo.tex"))
    output_pdf_name = str(build_cfg.get("output_pdf", "manual_demo.pdf"))
    xelatex_runs = int(build_cfg.get("xelatex_runs", 3))
    word_output_name = str(build_cfg.get("word_output", "manual_demo.docx"))
    word_source = str(build_cfg.get("word_source", "bundle")).strip().lower()
    patch_fonts_script = str(tools_cfg.get("patch_fonts", "tools/patch_latex_fonts.py"))

    open_html = bool(build_cfg.get("open_html", False)) and (not args.no_open)
    open_word = bool(build_cfg.get("open_word", False)) and (not args.no_open)
    open_pdf = bool(build_cfg.get("open_pdf", False)) and (not args.no_open)

    build_root = build_root_for_target(target_model, target_region)
    html_out_dir = build_root / "html"
    word_out_dir = build_root / "word"
    pdf_out_dir = build_root / "pdf"
    latex_out_dir = build_root / "latex"

    html_built = False
    latex_built = False
    docx_path: Path | None = None

    if "html" in requested_formats or word_source == "html":
        sphinx_build(
            "html",
            src_dir=bundle.bundle_dir,
            out_dir=html_out_dir,
            conf_dir=bundle.bundle_dir,
            minimal_theme=("html" not in requested_formats and word_source == "html"),
        )
        html_built = True

    if "word" in requested_formats or ("pdf" in requested_formats and pdf_mode == "word"):
        word_target_path = resolve_output_path(word_out_dir, word_output_name)
        if word_source == "bundle":
            docx_path = export_word_from_bundle(
                cfg,
                target_model,
                target_region,
                str(word_target_path),
                materialized_bundle=bundle,
                output_dir=word_target_path.parent,
            )
        elif word_source == "html":
            if not html_built:
                sphinx_build(
                    "html",
                    src_dir=bundle.bundle_dir,
                    out_dir=html_out_dir,
                    conf_dir=bundle.bundle_dir,
                    minimal_theme=True,
                )
                html_built = True
            docx_path = export_word_from_html(
                html_out_dir / "index.html",
                out_path=word_target_path,
            )
        elif word_source == "latex":
            if not latex_built:
                sphinx_build(
                    "latex",
                    src_dir=bundle.bundle_dir,
                    out_dir=latex_out_dir,
                    conf_dir=bundle.bundle_dir,
                )
                patch_fonts(patch_fonts_script, main_tex, build_dir=latex_out_dir)
                compile_xelatex(main_tex, xelatex_runs, cwd=latex_out_dir)
                latex_built = True
            docx_path = export_word_from_latex(
                latex_out_dir / main_tex,
                resource_dir=latex_out_dir,
                out_path=word_target_path,
            )
        else:
            raise RuntimeError("build.word_source must be one of 'bundle', 'html', or 'latex'")

        print(f"[build] Done. DOCX: {docx_path}")
        if "word" in requested_formats and open_word and docx_path.exists():
            open_file(docx_path)

    if "pdf" in requested_formats:
        if pdf_mode == "latex":
            if not latex_built:
                sphinx_build(
                    "latex",
                    src_dir=bundle.bundle_dir,
                    out_dir=latex_out_dir,
                    conf_dir=bundle.bundle_dir,
                )
                patch_fonts(patch_fonts_script, main_tex, build_dir=latex_out_dir)
                compile_xelatex(main_tex, xelatex_runs, cwd=latex_out_dir)
                latex_built = True
            latex_pdf = latex_out_dir / output_pdf_name
            if not latex_pdf.exists():
                raise RuntimeError(f"PDF not found after LaTeX build: {latex_pdf}")
            pdf_target_path = resolve_output_path(pdf_out_dir, output_pdf_name)
            pdf_target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(latex_pdf, pdf_target_path)
            pdf_path = pdf_target_path
        else:
            if docx_path is None:
                temp_docx_path = resolve_output_path(word_out_dir, word_output_name)
                docx_path = export_word_from_bundle(
                    cfg,
                    target_model,
                    target_region,
                    str(temp_docx_path),
                    materialized_bundle=bundle,
                    output_dir=temp_docx_path.parent,
                )
            pdf_target_path = resolve_output_path(pdf_out_dir, output_pdf_name)
            pdf_path = export_pdf_from_docx_via_word(docx_path, pdf_target_path)

        print(f"[build] Done. PDF: {pdf_path}")
        if open_pdf and pdf_path.exists():
            open_file(pdf_path)

    if "html" in requested_formats:
        html_index = html_out_dir / "index.html"
        print(f"[build] Done. HTML: {html_index}")
        if open_html and html_index.exists():
            open_file(html_index)


if __name__ == "__main__":
    main()
