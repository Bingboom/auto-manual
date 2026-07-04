from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from tools.build_docs_artifacts import (
    build_markdown_artifact,
    build_pdf_artifact,
    build_word_artifact,
    finalize_html_artifact,
    resolve_build_artifact_plan,
)


def _copy_attachment_images_for_latex(
    bundle_dir: Path,
    latex_out_dir: Path,
    printer: Callable[[str], None],
) -> None:
    """Flat-copy synced bitable attachment images into the LaTeX build dir.

    Raw-latex renderers reference these by bare basename via
    \\HBImageOrPlaceholder -> \\IfFileExists; Sphinx only copies images it
    sees in ``.. image::`` directives, so without this step every icon
    cell silently rendered as an empty placeholder
    (reports/typography_gap/2026-07-03 #3).
    """
    image_roots = sorted(
        (bundle_dir / "_repo_assets").glob("**/_attachments"),
    )
    # word_template common assets are also referenced by bare basename from
    # raw latex (e.g. HBInBoxThree -> main_unit1.png); the static
    # latex_additional_files list in conf_base.py only carries a couple of
    # them, so sweep the whole bundled common_assets tree as well.
    common_assets = bundle_dir / "_assets" / "templates" / "word_template" / "common_assets"
    if common_assets.is_dir():
        image_roots.append(common_assets)
    copied = 0
    for root in image_roots:
        for src in sorted(root.rglob("*")):
            if not src.is_file() or src.suffix.lower() not in (".png", ".jpg", ".jpeg", ".pdf"):
                continue
            dst = latex_out_dir / src.name
            if not dst.exists():
                dst.write_bytes(src.read_bytes())
                copied += 1
    if copied:
        printer(f"[build] Copied {copied} attachment/asset image(s) into latex dir")


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
    draft_placeholders: bool = False,
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
    export_markdown_from_bundle: Callable[..., Path],
    export_pdf_from_docx_via_word: Callable[[Path, Path], Path],
    copy_file: Callable[[Path, Path], None],
    open_file: Callable[[Path], None],
    strip_html_cover_section: Callable[[Path], None],
    write_html_manual_meta: Callable[..., None],
    refresh_model_html_switchers: Callable[..., None],
    printer: Callable[[str], None] = print,
) -> None:
    artifact_plan = resolve_build_artifact_plan(
        build_cfg=build_cfg,
        tools_cfg=tools_cfg,
        target_model=target_model,
        target_region=target_region,
        target_lang=target_lang,
        no_open=no_open,
        output_root=output_root,
        output_base_root=output_base_root,
        default_docs_build_dir=default_docs_build_dir,
        resolve_cfg_languages=resolve_cfg_languages,
        build_root_for_target=build_root_for_target,
        render_build_template=render_build_template,
    )
    ensure_target_identity(
        cfg,
        model=target_model,
        region=target_region,
        lang=artifact_plan.primary_lang,
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
        output_root=artifact_plan.build_root,
        write_wrapper_index=write_wrapper_index,
        draft_placeholders=draft_placeholders,
    )

    html_built = False
    latex_built = False

    def ensure_html(*, minimal_theme: bool) -> None:
        nonlocal html_built
        if html_built:
            return
        sphinx_build(
            "html",
            src_dir=bundle.bundle_dir,
            out_dir=artifact_plan.html_out_dir,
            conf_dir=bundle.bundle_dir,
            model=target_model,
            region=target_region,
            lang=target_lang or artifact_plan.primary_lang,
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
            out_dir=artifact_plan.latex_out_dir,
            conf_dir=bundle.bundle_dir,
            model=target_model,
            region=target_region,
            lang=target_lang or artifact_plan.primary_lang,
        )
        _copy_attachment_images_for_latex(
            Path(bundle.bundle_dir), Path(artifact_plan.latex_out_dir), printer,
        )
        patch_fonts(artifact_plan.patch_fonts_script, artifact_plan.main_tex, build_dir=artifact_plan.latex_out_dir)
        compile_xelatex(artifact_plan.main_tex, artifact_plan.xelatex_runs, cwd=artifact_plan.latex_out_dir)
        latex_built = True

    if "html" in requested_formats or artifact_plan.word_source == "html":
        ensure_html(minimal_theme=("html" not in requested_formats and artifact_plan.word_source == "html"))

    docx_path = build_word_artifact(
        cfg=cfg,
        target_model=target_model,
        target_region=target_region,
        requested_formats=requested_formats,
        pdf_mode=pdf_mode,
        plan=artifact_plan,
        bundle=bundle,
        resolve_output_path=resolve_output_path,
        ensure_html=ensure_html,
        ensure_latex=ensure_latex,
        export_word_from_bundle=export_word_from_bundle,
        export_word_from_html=export_word_from_html,
        export_word_from_latex=export_word_from_latex,
        open_file=open_file,
        printer=printer,
    )

    build_pdf_artifact(
        cfg=cfg,
        target_model=target_model,
        target_region=target_region,
        requested_formats=requested_formats,
        pdf_mode=pdf_mode,
        plan=artifact_plan,
        bundle=bundle,
        docx_path=docx_path,
        resolve_output_path=resolve_output_path,
        ensure_latex=ensure_latex,
        export_word_from_bundle=export_word_from_bundle,
        export_pdf_from_docx_via_word=export_pdf_from_docx_via_word,
        copy_file=copy_file,
        open_file=open_file,
        printer=printer,
    )

    build_markdown_artifact(
        cfg=cfg,
        target_model=target_model,
        target_region=target_region,
        requested_formats=requested_formats,
        plan=artifact_plan,
        bundle=bundle,
        resolve_output_path=resolve_output_path,
        export_markdown_from_bundle=export_markdown_from_bundle,
        open_file=open_file,
        printer=printer,
    )

    finalize_html_artifact(
        requested_formats=requested_formats,
        html_built=html_built,
        plan=artifact_plan,
        target_model=target_model,
        target_region=target_region,
        target_lang=target_lang,
        bundle_title=bundle.title,
        strip_html_cover_section=strip_html_cover_section,
        write_html_manual_meta=write_html_manual_meta,
        refresh_model_html_switchers=refresh_model_html_switchers,
        open_file=open_file,
        printer=printer,
    )
