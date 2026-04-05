from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


def build_target(
    cfg: dict,
    *,
    target_model: str | None,
    target_region: str | None,
    target_lang: str | None,
    requested_formats: list[str],
    pdf_mode: str,
    build_cfg: dict,
    tools_cfg: dict,
    no_open: bool,
    source_mode: str,
    data_root: str | None,
    page_selector: str | None = None,
    output_root: Path | None = None,
    output_base_root: Path | None = None,
    write_wrapper_index: bool = True,
    default_docs_build_dir: Path,
    resolve_cfg_languages: Callable[[dict], list[str]],
    build_root_for_target: Callable[..., Path],
    ensure_target_identity: Callable[..., None],
    prepare_manual_bundle: Callable[..., Any],
    render_build_template: Callable[..., str],
    resolve_output_path: Callable[[Path, str], Path],
    sphinx_build: Callable[..., None],
    patch_fonts: Callable[..., None],
    compile_xelatex: Callable[..., None],
    export_word_from_bundle: Callable[..., Path],
    export_word_from_html: Callable[..., Path],
    export_word_from_latex: Callable[..., Path],
    export_pdf_from_docx_via_word: Callable[[Path, Path], Path],
    copy_file: Callable[[Path, Path], None],
    open_file: Callable[[Path], None],
    strip_html_cover_section: Callable[[Path], None],
    write_html_manual_meta: Callable[..., None],
    refresh_model_html_switchers: Callable[..., None],
    printer: Callable[[str], None] = print,
) -> None:
    build_langs = resolve_cfg_languages({"build": build_cfg})
    primary_lang = str(target_lang or (build_langs[0] if build_langs else "en"))
    docs_build_root = output_base_root or default_docs_build_dir
    build_root = output_root or build_root_for_target(
        target_model,
        target_region,
        target_lang,
        docs_build_dir=docs_build_root,
    )
    ensure_target_identity(
        cfg,
        model=target_model,
        region=target_region,
        lang=primary_lang,
        data_root=data_root,
    )

    bundle = prepare_manual_bundle(
        cfg,
        model=target_model,
        region=target_region,
        lang=target_lang,
        data_root=data_root,
        source_mode=source_mode,
        page_selector=page_selector,
        output_root=build_root,
        write_wrapper_index=write_wrapper_index,
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
    xelatex_runs = int(build_cfg.get("xelatex_runs", 3))
    word_output_name = render_build_template(
        str(build_cfg.get("word_output", "manual_demo.docx")),
        model=target_model,
        region=target_region,
        lang=primary_lang,
    )
    word_source = str(build_cfg.get("word_source", "bundle")).strip().lower()
    patch_fonts_script = str(tools_cfg.get("patch_fonts", "tools/patch_latex_fonts.py"))

    open_html = bool(build_cfg.get("open_html", False)) and (not no_open)
    open_word = bool(build_cfg.get("open_word", False)) and (not no_open)
    open_pdf = bool(build_cfg.get("open_pdf", False)) and (not no_open)

    html_out_dir = build_root / "html"
    word_out_dir = build_root / "word"
    pdf_out_dir = build_root / "pdf"
    latex_out_dir = build_root / "latex"

    html_built = False
    latex_built = False
    docx_path: Path | None = None

    def ensure_html(*, minimal_theme: bool) -> None:
        nonlocal html_built
        if html_built:
            return
        sphinx_build(
            "html",
            src_dir=bundle.bundle_dir,
            out_dir=html_out_dir,
            conf_dir=bundle.bundle_dir,
            model=target_model,
            region=target_region,
            lang=target_lang or primary_lang,
            minimal_theme=minimal_theme,
        )
        html_built = True

    def ensure_latex() -> None:
        nonlocal latex_built
        if latex_built:
            return
        sphinx_build(
            "latex",
            src_dir=bundle.bundle_dir,
            out_dir=latex_out_dir,
            conf_dir=bundle.bundle_dir,
            model=target_model,
            region=target_region,
            lang=target_lang or primary_lang,
        )
        patch_fonts(patch_fonts_script, main_tex, build_dir=latex_out_dir)
        compile_xelatex(main_tex, xelatex_runs, cwd=latex_out_dir)
        latex_built = True

    if "html" in requested_formats or word_source == "html":
        ensure_html(minimal_theme=("html" not in requested_formats and word_source == "html"))

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
            ensure_html(minimal_theme=True)
            docx_path = export_word_from_html(
                html_out_dir / "index.html",
                out_path=word_target_path,
            )
        elif word_source == "latex":
            ensure_latex()
            docx_path = export_word_from_latex(
                latex_out_dir / main_tex,
                resource_dir=latex_out_dir,
                out_path=word_target_path,
            )
        else:
            raise RuntimeError("build.word_source must be one of 'bundle', 'html', or 'latex'")

        printer(f"[build] Done. DOCX: {docx_path}")
        if "word" in requested_formats and open_word and docx_path.exists():
            open_file(docx_path)

    if "pdf" in requested_formats:
        if pdf_mode == "latex":
            ensure_latex()
            latex_pdf = latex_out_dir / output_pdf_name
            if not latex_pdf.exists():
                fallback_pdf = latex_out_dir / Path(main_tex).with_suffix(".pdf")
                if fallback_pdf.exists():
                    latex_pdf = fallback_pdf
                else:
                    raise RuntimeError(f"PDF not found after LaTeX build: {latex_pdf}")
            pdf_target_path = resolve_output_path(pdf_out_dir, output_pdf_name)
            pdf_target_path.parent.mkdir(parents=True, exist_ok=True)
            copy_file(latex_pdf, pdf_target_path)
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

        printer(f"[build] Done. PDF: {pdf_path}")
        if open_pdf and pdf_path.exists():
            open_file(pdf_path)

    if html_built and (target_model or "").strip() and (target_region or "").strip():
        strip_html_cover_section(html_out_dir / "index.html")
        write_html_manual_meta(
            html_out_dir,
            docs_build_dir=docs_build_root,
            model=target_model,
            region=target_region,
            lang=primary_lang,
            title=bundle.title,
            lang_in_output_path=bool((target_lang or "").strip()),
        )
        refresh_model_html_switchers(model=target_model, docs_build_dir=docs_build_root)

    if "html" in requested_formats:
        html_index = html_out_dir / "index.html"
        printer(f"[build] Done. HTML: {html_index}")
        if open_html and html_index.exists():
            open_file(html_index)
