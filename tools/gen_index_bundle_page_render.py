from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Callable


def prepend_latex_lang(
    text: str,
    lang: str | None,
    *,
    latex_apply_lang: Callable[[str], list[str]],
) -> str:
    body = text if text.endswith("\n") else f"{text}\n"
    if not (lang or "").strip():
        return body
    return "\n".join(latex_apply_lang(lang)) + "\n" + body


def render_cover_page_rst(
    title: str,
    file_name: str,
    *,
    latex_cover_block: Callable[[str], list[str]],
) -> str:
    title_html = html.escape(title)
    return "\n".join(
        [
            ".. only:: html",
            "",
            "   .. raw:: html",
            "",
            f"      <section class=\"manual-cover\"><div class=\"cover-title\">{title_html}</div></section>",
            "",
            ".. only:: latex",
            "",
            *("   " + line if line else "" for line in latex_cover_block(file_name)),
            "",
        ]
    )


def render_pdf_insert_page_rst(
    file_name: str,
    lang: str,
    *,
    latex_apply_lang: Callable[[str], list[str]],
    latex_overview_block: Callable[[str], list[str]],
) -> str:
    return "\n".join(
        [
            ".. only:: html",
            "",
            "   .. raw:: html",
            "",
            "      <div class=\"manual-pdf-insert\"></div>",
            "",
            ".. only:: latex",
            "",
            *("   " + line if line else "" for line in (latex_apply_lang(lang) + latex_overview_block(file_name))),
            "",
        ]
    )


def materialize_planned_page(
    planned: Any,
    *,
    target_path: Path,
    bundle_dir: Path,
    docs_dir: Path,
    repo_root: Path,
    spec_master_csv: Path,
    base_substitutions: dict[str, str],
    base_vars_map: dict[str, str],
    primary_lang: str,
    title: str,
    model: str | None,
    region: str | None,
    cover_pdf_page_cls: type[Any],
    pdf_insert_page_cls: type[Any],
    csv_page_cls: type[Any],
    generated_page_cls: type[Any],
    rst_include_page_cls: type[Any],
    format_tokenized: Callable[[str, str | None, str | None], str],
    render_cover_page_rst: Callable[[str, str], str],
    render_pdf_insert_page_rst: Callable[[str, str], str],
    fill_product_name_from_spec_master: Callable[..., dict[str, str]],
    resolve_spec_master_substitutions: Callable[..., dict[str, str]],
    resolve_csv_rst_path: Callable[..., Path],
    resolve_generated_recipe_path: Callable[..., Path],
    resolve_generated_template_path: Callable[..., Path],
    resolve_generated_source_path: Callable[..., Path | None],
    render_generated_page: Callable[..., Any],
    resolve_snippet_registry_path: Callable[[Path], Path],
    resolve_config_path: Callable[..., Path],
    apply_rst_substitutions: Callable[[str, dict[str, str], dict[str, str]], str],
    rewrite_rst_asset_paths: Callable[..., str],
    normalize_rst_empty_line_blocks: Callable[[str], str],
    prepend_latex_lang: Callable[[str, str | None], str],
) -> tuple[str, Any | None]:
    page = planned.page

    if isinstance(page, cover_pdf_page_cls):
        return render_cover_page_rst(title, format_tokenized(page.file, model, region)), None

    if isinstance(page, pdf_insert_page_cls):
        if planned.lang is None:
            raise RuntimeError("pdf_insert planned page is missing lang")
        return (
            render_pdf_insert_page_rst(
                format_tokenized(page.file_map[planned.lang], model, region),
                planned.lang,
            ),
            None,
        )

    page_lang = planned.lang or primary_lang
    page_vars = fill_product_name_from_spec_master(
        base_vars_map,
        spec_master_csv=spec_master_csv,
        model=model,
        region=region,
        lang=page_lang,
    )
    page_vars["lang"] = page_lang
    page_substitutions = {
        **base_substitutions,
        **resolve_spec_master_substitutions(
            spec_master_csv=spec_master_csv,
            model=model,
            region=region,
            lang=page_lang,
        ),
    }

    if isinstance(page, csv_page_cls):
        if planned.lang is None:
            raise RuntimeError("csv_page planned page is missing lang")
        source_path = resolve_csv_rst_path(
            source_root=bundle_dir,
            page=page,
            lang=planned.lang,
            model=model,
            region=region,
        )
        generated_render: Any | None = None
    elif isinstance(page, generated_page_cls):
        if planned.lang is None:
            raise RuntimeError("generated_page planned page is missing lang")
        recipe_path = resolve_generated_recipe_path(
            docs_dir=docs_dir,
            page=page,
            model=model,
            region=region,
        )
        template_path = resolve_generated_template_path(
            docs_dir=docs_dir,
            page=page,
            model=model,
            region=region,
        )
        generated_source_path = resolve_generated_source_path(
            bundle_dir=bundle_dir,
            page=page,
            lang=planned.lang,
            model=model,
            region=region,
        )
        generated_render = render_generated_page(
            docs_dir=docs_dir,
            recipe_path=recipe_path,
            template_path=template_path,
            spec_master_csv=spec_master_csv,
            registry_path=resolve_snippet_registry_path(docs_dir),
            vars_map=page_vars,
            base_substitutions=page_substitutions,
            model=model,
            region=region,
            lang=planned.lang,
            rendered_source_path=generated_source_path,
        )
        source_path = generated_render.template_path
        rst_text = generated_render.text
    elif isinstance(page, rst_include_page_cls):
        source_path = resolve_config_path(docs_dir, page.file, model, region)
        generated_render = None
    else:
        raise RuntimeError(f"Unsupported page type: {type(page).__name__}")

    if not source_path.exists():
        raise RuntimeError(f"Missing source RST for bundle materialization: {source_path}")

    if not isinstance(page, generated_page_cls):
        rst_text = source_path.read_text(encoding="utf-8")
        rst_text = apply_rst_substitutions(rst_text, page_substitutions, page_vars)
    rst_text = rewrite_rst_asset_paths(
        rst_text,
        source_path=source_path,
        target_path=target_path,
        bundle_dir=bundle_dir,
        docs_dir=docs_dir,
        repo_root=repo_root,
    )
    final_text = normalize_rst_empty_line_blocks(prepend_latex_lang(rst_text, planned.lang))
    if generated_render is not None and generated_render.rendered_source_path is not None:
        generated_render.rendered_source_path.parent.mkdir(parents=True, exist_ok=True)
        generated_render.rendered_source_path.write_text(final_text, encoding="utf-8")
    return final_text, generated_render
