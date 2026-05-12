from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class BuildArtifactPlan:
    primary_lang: str
    docs_build_root: Path
    build_root: Path
    main_tex: str
    output_pdf_name: str
    xelatex_runs: int
    word_output_name: str
    myst_output_name: str
    word_source: str
    patch_fonts_script: str
    open_html: bool
    open_word: bool
    open_pdf: bool
    html_out_dir: Path
    word_out_dir: Path
    myst_out_dir: Path
    pdf_out_dir: Path
    latex_out_dir: Path


def resolve_build_artifact_plan(
    *,
    build_cfg: dict,
    tools_cfg: dict,
    target_model: str | None,
    target_region: str | None,
    target_lang: str | None,
    no_open: bool,
    output_root: Path | None,
    output_base_root: Path | None,
    default_docs_build_dir: Path,
    resolve_cfg_languages: Callable[[dict], list[str]],
    build_root_for_target: Callable[..., Path],
    render_build_template: Callable[..., str],
) -> BuildArtifactPlan:
    build_langs = resolve_cfg_languages({"build": build_cfg})
    primary_lang = str(target_lang or (build_langs[0] if build_langs else "en"))
    docs_build_root = output_base_root or default_docs_build_dir
    build_root = output_root or build_root_for_target(
        target_model,
        target_region,
        target_lang,
        docs_build_dir=docs_build_root,
    )

    main_tex = render_build_template(
        str(build_cfg.get("main_tex", "manual_demo.tex")),
        model=target_model,
        region=target_region,
        lang=primary_lang,
    )
    output_pdf_name = render_build_template(
        str(build_cfg.get("output_pdf", "manual_demo.pdf")),
        model=target_model,
        region=target_region,
        lang=primary_lang,
    )
    word_output_name = render_build_template(
        str(build_cfg.get("word_output", "manual_demo.docx")),
        model=target_model,
        region=target_region,
        lang=primary_lang,
    )
    myst_output_template = build_cfg.get("myst_output")
    if isinstance(myst_output_template, str) and myst_output_template.strip():
        myst_output_name = render_build_template(
            myst_output_template,
            model=target_model,
            region=target_region,
            lang=primary_lang,
        )
    else:
        myst_output_name = str(Path(word_output_name).with_suffix(".md"))

    return BuildArtifactPlan(
        primary_lang=primary_lang,
        docs_build_root=docs_build_root,
        build_root=build_root,
        main_tex=main_tex,
        output_pdf_name=output_pdf_name,
        xelatex_runs=int(build_cfg.get("xelatex_runs", 3)),
        word_output_name=word_output_name,
        myst_output_name=myst_output_name,
        word_source=str(build_cfg.get("word_source", "bundle")).strip().lower(),
        patch_fonts_script=str(tools_cfg.get("patch_fonts", "tools/patch_latex_fonts.py")),
        open_html=bool(build_cfg.get("open_html", False)) and (not no_open),
        open_word=bool(build_cfg.get("open_word", False)) and (not no_open),
        open_pdf=bool(build_cfg.get("open_pdf", False)) and (not no_open),
        html_out_dir=build_root / "html",
        word_out_dir=build_root / "word",
        myst_out_dir=build_root / "myst",
        pdf_out_dir=build_root / "pdf",
        latex_out_dir=build_root / "latex",
    )


def build_word_artifact(
    *,
    cfg: dict,
    target_model: str | None,
    target_region: str | None,
    requested_formats: list[str],
    pdf_mode: str,
    plan: BuildArtifactPlan,
    bundle: Any,
    resolve_output_path: Callable[[Path, str], Path],
    ensure_html: Callable[..., None],
    ensure_latex: Callable[[], None],
    export_word_from_bundle: Callable[..., Path],
    export_word_from_html: Callable[..., Path],
    export_word_from_latex: Callable[..., Path],
    open_file: Callable[[Path], None],
    printer: Callable[[str], None],
) -> Path | None:
    if "word" not in requested_formats and not ("pdf" in requested_formats and pdf_mode == "word"):
        return None

    word_target_path = resolve_output_path(plan.word_out_dir, plan.word_output_name)
    if plan.word_source == "bundle":
        docx_path = export_word_from_bundle(
            cfg,
            target_model,
            target_region,
            str(word_target_path),
            materialized_bundle=bundle,
            output_dir=word_target_path.parent,
        )
    elif plan.word_source == "html":
        ensure_html(minimal_theme=True)
        docx_path = export_word_from_html(
            plan.html_out_dir / "index.html",
            out_path=word_target_path,
        )
    elif plan.word_source == "latex":
        ensure_latex()
        docx_path = export_word_from_latex(
            plan.latex_out_dir / plan.main_tex,
            resource_dir=plan.latex_out_dir,
            out_path=word_target_path,
        )
    else:
        raise RuntimeError("build.word_source must be one of 'bundle', 'html', or 'latex'")

    printer(f"[build] Done. DOCX: {docx_path}")
    if "word" in requested_formats and plan.open_word and docx_path.exists():
        open_file(docx_path)
    return docx_path


def build_myst_artifact(
    *,
    cfg: dict,
    target_model: str | None,
    target_region: str | None,
    requested_formats: list[str],
    plan: BuildArtifactPlan,
    bundle: Any,
    resolve_output_path: Callable[[Path, str], Path],
    export_myst_from_bundle: Callable[..., Path],
    printer: Callable[[str], None],
) -> Path | None:
    if "myst" not in requested_formats:
        return None

    myst_target_path = resolve_output_path(plan.myst_out_dir, plan.myst_output_name)
    myst_path = export_myst_from_bundle(
        cfg,
        target_model,
        target_region,
        str(myst_target_path),
        materialized_bundle=bundle,
        output_dir=myst_target_path.parent,
    )
    printer(f"[build] Done. MyST MD: {myst_path}")
    return myst_path


def build_pdf_artifact(
    *,
    cfg: dict,
    target_model: str | None,
    target_region: str | None,
    requested_formats: list[str],
    pdf_mode: str,
    plan: BuildArtifactPlan,
    bundle: Any,
    docx_path: Path | None,
    resolve_output_path: Callable[[Path, str], Path],
    ensure_latex: Callable[[], None],
    export_word_from_bundle: Callable[..., Path],
    export_pdf_from_docx_via_word: Callable[[Path, Path], Path],
    copy_file: Callable[[Path, Path], None],
    open_file: Callable[[Path], None],
    printer: Callable[[str], None],
) -> Path | None:
    if "pdf" not in requested_formats:
        return None

    if pdf_mode == "latex":
        ensure_latex()
        latex_pdf = plan.latex_out_dir / plan.output_pdf_name
        if not latex_pdf.exists():
            fallback_pdf = plan.latex_out_dir / Path(plan.main_tex).with_suffix(".pdf")
            if fallback_pdf.exists():
                latex_pdf = fallback_pdf
            else:
                raise RuntimeError(f"PDF not found after LaTeX build: {latex_pdf}")
        pdf_target_path = resolve_output_path(plan.pdf_out_dir, plan.output_pdf_name)
        pdf_target_path.parent.mkdir(parents=True, exist_ok=True)
        copy_file(latex_pdf, pdf_target_path)
        pdf_path = pdf_target_path
    else:
        resolved_docx_path = docx_path
        if resolved_docx_path is None:
            temp_docx_path = resolve_output_path(plan.word_out_dir, plan.word_output_name)
            resolved_docx_path = export_word_from_bundle(
                cfg,
                target_model,
                target_region,
                str(temp_docx_path),
                materialized_bundle=bundle,
                output_dir=temp_docx_path.parent,
            )
        pdf_target_path = resolve_output_path(plan.pdf_out_dir, plan.output_pdf_name)
        pdf_path = export_pdf_from_docx_via_word(resolved_docx_path, pdf_target_path)

    printer(f"[build] Done. PDF: {pdf_path}")
    if plan.open_pdf and pdf_path.exists():
        open_file(pdf_path)
    return pdf_path


def finalize_html_artifact(
    *,
    requested_formats: list[str],
    html_built: bool,
    plan: BuildArtifactPlan,
    target_model: str | None,
    target_region: str | None,
    target_lang: str | None,
    bundle_title: str,
    strip_html_cover_section: Callable[[Path], None],
    write_html_manual_meta: Callable[..., None],
    refresh_model_html_switchers: Callable[..., None],
    open_file: Callable[[Path], None],
    printer: Callable[[str], None],
) -> None:
    if html_built and (target_model or "").strip() and (target_region or "").strip():
        strip_html_cover_section(plan.html_out_dir / "index.html")
        write_html_manual_meta(
            plan.html_out_dir,
            docs_build_dir=plan.docs_build_root,
            model=target_model,
            region=target_region,
            lang=plan.primary_lang,
            title=bundle_title,
            lang_in_output_path=bool((target_lang or "").strip()),
        )
        refresh_model_html_switchers(model=target_model, docs_build_dir=plan.docs_build_root)

    if "html" in requested_formats:
        html_index = plan.html_out_dir / "index.html"
        printer(f"[build] Done. HTML: {html_index}")
        if plan.open_html and html_index.exists():
            open_file(html_index)
