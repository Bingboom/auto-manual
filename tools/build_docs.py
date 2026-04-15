#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.config_pages import CsvPage
from tools.build_docs_bundle import prepare_manual_bundle as _prepare_manual_bundle_impl
from tools.build_docs_cli import parse_args as _parse_args_impl
from tools.build_docs_entry import run_build as _run_build_impl
from tools.build_docs_export import build_target as _build_target_impl
from tools.build_docs_main import run_main as _run_main_impl
from tools.build_docs_html import (
    build_manual_switcher_markup as _build_manual_switcher_markup_impl,
    collect_model_html_variants as _collect_model_html_variants_impl,
    inject_manual_switcher_into_html as _inject_manual_switcher_into_html_impl,
    load_html_manual_variant as _load_html_manual_variant_impl,
    refresh_model_html_switchers as _refresh_model_html_switchers_impl,
    resolve_variant_target_page as _resolve_variant_target_page_impl,
    strip_html_cover_section as _strip_html_cover_section_impl,
    write_html_manual_meta as _write_html_manual_meta_impl,
)
from tools.build_docs_index import write_docs_root_index_for_targets as _write_docs_root_index_for_targets_impl
from tools.build_docs_io import (
    clean_build_targets as _clean_build_targets_impl,
    export_pdf_from_docx_via_word as _export_pdf_from_docx_via_word_impl,
    export_word_from_html as _export_word_from_html_impl,
    export_word_from_latex as _export_word_from_latex_impl,
    is_retryable_cleanup_error as _is_retryable_cleanup_error_impl,
    patch_fonts as _patch_fonts_impl,
    remove_tree_with_retries as _remove_tree_with_retries_impl,
    sphinx_build as _sphinx_build_impl,
)
from tools.build_docs_pages import render_csv_pages as _render_csv_pages_impl
from tools.build_docs_paths import (
    build_root_for_target as _build_root_for_target_impl,
    discover_existing_bundle_targets as _discover_existing_bundle_targets_impl,
    target_component as _target_component_impl,
)
from tools.build_docs_targets import (
    config_uses_model_token as _config_uses_model_token_impl,
    config_uses_region_token as _config_uses_region_token_impl,
    configured_build_targets as _configured_build_targets_impl,
    resolve_build_model as _resolve_build_model_impl,
    resolve_build_region as _resolve_build_region_impl,
    resolve_build_targets as _resolve_build_targets_impl,
)
from tools.build_docs_theme import (
    body_tag_with_class as _body_tag_with_class_impl,
    effective_variants_for_current as _effective_variants_for_current_impl,
    language_label as _language_label_impl,
    load_configured_html_theme as _load_configured_html_theme_impl,
    normalize_sphinx_tag_value as _normalize_sphinx_tag_value_impl,
    should_use_minimal_html_theme as _should_use_minimal_html_theme_impl,
    sphinx_tag_args as _sphinx_tag_args_impl,
    variant_key as _variant_key_impl,
    variant_priority as _variant_priority_impl,
)
from tools.build_docs_resolve import (
    ensure_target_identity as _ensure_target_identity_impl,
    parse_csv_values as _parse_csv_values_impl,
    render_build_template as _render_build_template_impl,
    resolve_output_path as _resolve_output_path_impl,
    resolve_pdf_mode as _resolve_pdf_mode_impl,
    resolve_product_name_for_build as _resolve_product_name_for_build_impl,
    resolve_requested_formats as _resolve_requested_formats_impl,
    resolve_rst_substitutions_for_build as _resolve_rst_substitutions_for_build_impl,
    resolve_spec_master_csv_path as _resolve_spec_master_csv_path_impl,
    slug_token as _slug_token_impl,
)
from tools.build_docs_sphinx import (
    build_rst_epilog as _build_rst_epilog_impl,
    resolve_sphinx_build_cmd as _resolve_sphinx_build_cmd_impl,
    with_product_name_epilog as _with_product_name_epilog_impl,
    with_rst_epilog as _with_rst_epilog_impl,
)
from tools.build_docs_shared import (
    BODY_SWITCHER_CLASS,
    MANUAL_META_FILE_NAME,
    SWITCHER_BLOCK_END,
    SWITCHER_BLOCK_START,
    VALID_FORMATS,
    VALID_PDF_MODES,
    VALID_SOURCE_MODES,
    BuildTarget,
    HtmlManualVariant,
    _BODY_TAG_RE,
    _MANUAL_COVER_SECTION_RE,
    _REMOVE_TREE_RETRY_DELAYS,
    _SWITCHER_BLOCK_RE,
    _TEMPLATE_TOKEN_RE,
)
from tools.build_docs_validation import (
    validate_layout_csv as _validate_layout_csv_impl,
    validate_loaded_config as _validate_loaded_config_impl,
)
from tools.config_loader import load_config_mapping
from tools.data_snapshot import resolve_data_snapshot_paths
from tools.gen_index_bundle import (
    MaterializedBundle,
    bundle_dir_for_target,
    cleanup_legacy_rst_artifacts,
    materialize_bundle,
)
from tools.page_manifest import resolve_config_pages_or_raise
from tools.review_support import (
    overlay_review_content_onto_bundle,
    overlay_review_onto_bundle,
    review_bundle_exists,
    review_content_exists,
)
from tools.utils.path_utils import get_paths  # noqa: E402
from tools.utils.process_utils import find_exe, open_file, run  # noqa: E402
from tools.utils.spec_master import (
    resolve_product_name_from_spec_master,
    resolve_template_substitutions_from_spec_master,
)
from tools.utils.targets import (
    config_uses_token_in_pages,
    resolve_build_languages as resolve_cfg_languages,
    resolve_build_model as resolve_target_model,
    resolve_build_region as resolve_target_region,
    resolve_output_lang,
)
from tools.utils.tex_utils import compile_xelatex  # noqa: E402
from tools.word_bundle import export_word_from_bundle  # noqa: E402
from tools.word_bundle_common import load_rst_substitutions  # noqa: E402

from tools.validate_config import validate as validate_cfg
from tools.validate_layout_params import validate as validate_layout

paths = get_paths()
LANGUAGE_LABELS = {
    "en": "English",
    "es": "Espanol",
    "fr": "Francais",
    "ja": "日本語",
}


load_config = load_config_mapping


def discover_existing_bundle_targets(*, docs_dir: Path | None = None) -> list[BuildTarget]:
    return _discover_existing_bundle_targets_impl(
        docs_dir=docs_dir or paths.docs_dir,
        build_target_cls=BuildTarget,
    )


def build_root_for_target(
    model: str | None,
    region: str | None,
    lang: str | None = None,
    *,
    docs_build_dir: Path | None = None,
    preview_name: str | None = None,
) -> Path:
    return _build_root_for_target_impl(
        model,
        region,
        lang,
        docs_build_dir=docs_build_dir or paths.docs_build_dir,
        preview_name=preview_name,
        target_component=_target_component,
    )


def clean_build_targets(
    targets: list[BuildTarget],
    *,
    docs_dir: Path | None = None,
    preview_name: str | None = None,
) -> None:
    return _clean_build_targets_impl(
        targets,
        docs_dir=docs_dir or paths.docs_dir,
        preview_name=preview_name,
        build_root_for_target=build_root_for_target,
        cleanup_legacy_rst_artifacts=cleanup_legacy_rst_artifacts,
        remove_tree_with_retries=remove_tree_with_retries,
    )


def _is_retryable_cleanup_error(exc: OSError) -> bool:
    return _is_retryable_cleanup_error_impl(exc, os_name=os.name)


def remove_tree_with_retries(path: Path) -> None:
    return _remove_tree_with_retries_impl(
        path,
        remove_tree=shutil.rmtree,
        sleep=time.sleep,
        retry_delays=_REMOVE_TREE_RETRY_DELAYS,
        is_retryable_cleanup_error=_is_retryable_cleanup_error,
    )


def validate_loaded_config(cfg: dict) -> None:
    return _validate_loaded_config_impl(
        cfg,
        validate_cfg=validate_cfg,
    )


def validate_layout_csv(layout_csv_path: Path) -> None:
    return _validate_layout_csv_impl(
        layout_csv_path,
        validate_layout=validate_layout,
    )


def render_csv_pages(
    cfg: dict,
    model: str | None,
    region: str | None,
    *,
    data_root: str | None = None,
) -> None:
    return _render_csv_pages_impl(
        cfg,
        model,
        region,
        data_root=data_root,
        csv_page_cls=CsvPage,
        resolve_config_pages_or_raise=resolve_config_pages_or_raise,
        resolve_data_snapshot_paths=resolve_data_snapshot_paths,
        run=run,
        repo_root=paths.root,
    )


def _config_uses_model_token(cfg: dict) -> bool:
    return _config_uses_model_token_impl(
        cfg,
        config_uses_token_in_pages=config_uses_token_in_pages,
    )


def _config_uses_region_token(cfg: dict) -> bool:
    return _config_uses_region_token_impl(
        cfg,
        config_uses_token_in_pages=config_uses_token_in_pages,
    )


def resolve_build_model(cfg: dict, arg_model: str | None) -> str | None:
    return _resolve_build_model_impl(
        cfg,
        arg_model,
        resolve_target_model=resolve_target_model,
    )


def resolve_build_region(cfg: dict, arg_region: str | None) -> str | None:
    return _resolve_build_region_impl(
        cfg,
        arg_region,
        resolve_target_region=resolve_target_region,
    )


def _configured_build_targets(cfg: dict) -> list[BuildTarget]:
    return _configured_build_targets_impl(
        cfg,
        build_target_cls=BuildTarget,
        resolve_build_model=resolve_build_model,
        resolve_build_region=resolve_build_region,
        resolve_output_lang=resolve_output_lang,
    )


def resolve_build_targets(
    cfg: dict,
    *,
    arg_model: str | None,
    arg_region: str | None,
    all_targets: bool,
) -> list[BuildTarget]:
    return _resolve_build_targets_impl(
        cfg,
        arg_model=arg_model,
        arg_region=arg_region,
        all_targets=all_targets,
        build_target_cls=BuildTarget,
        configured_build_targets=_configured_build_targets,
        resolve_build_model=resolve_build_model,
        resolve_build_region=resolve_build_region,
        resolve_output_lang=resolve_output_lang,
    )


def _resolve_spec_master_csv_path(
    cfg: dict,
    *,
    data_root: str | None = None,
    repo_root: Path | None = None,
) -> Path:
    return _resolve_spec_master_csv_path_impl(
        cfg,
        repo_root=repo_root or paths.root,
        data_root=data_root,
        resolve_data_snapshot_paths=resolve_data_snapshot_paths,
    )


def resolve_product_name_for_build(
    cfg: dict,
    *,
    model: str | None,
    region: str | None,
    lang: str,
    data_root: str | None = None,
    repo_root: Path | None = None,
) -> str | None:
    return _resolve_product_name_for_build_impl(
        cfg,
        model=model,
        region=region,
        lang=lang,
        data_root=data_root,
        repo_root=repo_root or paths.root,
        resolve_spec_master_csv_path=_resolve_spec_master_csv_path,
        resolve_product_name_from_spec_master=resolve_product_name_from_spec_master,
    )


def resolve_rst_substitutions_for_build(
    cfg: dict,
    *,
    model: str | None,
    region: str | None,
    lang: str,
    data_root: str | None = None,
    repo_root: Path | None = None,
) -> dict[str, str]:
    return _resolve_rst_substitutions_for_build_impl(
        cfg,
        model=model,
        region=region,
        lang=lang,
        data_root=data_root,
        repo_root=repo_root or paths.root,
        docs_dir=paths.docs_dir,
        load_rst_substitutions=load_rst_substitutions,
        resolve_spec_master_csv_path=_resolve_spec_master_csv_path,
        resolve_template_substitutions_from_spec_master=resolve_template_substitutions_from_spec_master,
    )


_build_rst_epilog = _build_rst_epilog_impl


def _with_rst_epilog(cmd: list[str], substitutions: dict[str, str] | None) -> list[str]:
    return _with_rst_epilog_impl(
        cmd,
        substitutions,
        build_rst_epilog=_build_rst_epilog,
    )


def _with_product_name_epilog(cmd: list[str], product_name: str | None) -> list[str]:
    return _with_product_name_epilog_impl(
        cmd,
        product_name,
        with_rst_epilog=_with_rst_epilog,
    )


def _resolve_sphinx_build_cmd(builder: str) -> list[str]:
    return _resolve_sphinx_build_cmd_impl(
        builder,
        find_exe=find_exe,
        python_executable=sys.executable,
    )


_normalize_sphinx_tag_value = _normalize_sphinx_tag_value_impl


def _sphinx_tag_args(*, model: str | None = None, region: str | None = None, lang: str | None = None) -> list[str]:
    return _sphinx_tag_args_impl(
        model=model,
        region=region,
        lang=lang,
        normalize_sphinx_tag_value=_normalize_sphinx_tag_value,
    )


_load_configured_html_theme = _load_configured_html_theme_impl


def _should_use_minimal_html_theme(conf_dir: Path, requested_minimal: bool) -> bool:
    return _should_use_minimal_html_theme_impl(
        conf_dir,
        requested_minimal,
        load_configured_html_theme=_load_configured_html_theme,
        find_spec=importlib.util.find_spec,
    )


_target_component = _target_component_impl


_body_tag_with_class = _body_tag_with_class_impl


def _language_label(lang: str) -> str:
    return _language_label_impl(lang, labels=LANGUAGE_LABELS)


_variant_key = _variant_key_impl


_variant_priority = _variant_priority_impl


def _effective_variants_for_current(
    variants: list[HtmlManualVariant],
    *,
    current_variant: HtmlManualVariant,
) -> list[HtmlManualVariant]:
    return _effective_variants_for_current_impl(
        variants,
        current_variant=current_variant,
        variant_key=_variant_key,
        variant_priority=_variant_priority,
    )


def write_html_manual_meta(
    html_out_dir: Path,
    *,
    docs_build_dir: Path,
    model: str | None,
    region: str | None,
    lang: str,
    title: str,
    lang_in_output_path: bool,
) -> Path:
    return _write_html_manual_meta_impl(
        html_out_dir,
        docs_build_dir=docs_build_dir,
        model=model,
        region=region,
        lang=lang,
        title=title,
        lang_in_output_path=lang_in_output_path,
        manual_meta_file_name=MANUAL_META_FILE_NAME,
    )


def _load_html_manual_variant(meta_path: Path, *, docs_build_dir: Path) -> HtmlManualVariant | None:
    return _load_html_manual_variant_impl(
        meta_path,
        docs_build_dir=docs_build_dir,
        variant_cls=HtmlManualVariant,
    )


def collect_model_html_variants(
    *,
    model: str | None,
    docs_build_dir: Path | None = None,
) -> list[HtmlManualVariant]:
    actual_docs_build_dir = docs_build_dir or paths.docs_build_dir
    return _collect_model_html_variants_impl(
        model=model,
        docs_build_dir=actual_docs_build_dir,
        manual_meta_file_name=MANUAL_META_FILE_NAME,
        target_component=_target_component,
        load_html_manual_variant=lambda meta_path: _load_html_manual_variant(
            meta_path,
            docs_build_dir=actual_docs_build_dir,
        ),
    )


_resolve_variant_target_page = _resolve_variant_target_page_impl


build_manual_switcher_markup = _build_manual_switcher_markup_impl


def inject_manual_switcher_into_html(html_path: Path, markup: str | None) -> bool:
    return _inject_manual_switcher_into_html_impl(
        html_path,
        markup,
        switcher_block_re=_SWITCHER_BLOCK_RE,
        body_tag_re=_BODY_TAG_RE,
        body_tag_with_class=_body_tag_with_class,
        body_switcher_class=BODY_SWITCHER_CLASS,
    )


def strip_html_cover_section(html_path: Path) -> bool:
    return _strip_html_cover_section_impl(
        html_path,
        manual_cover_section_re=_MANUAL_COVER_SECTION_RE,
    )


def refresh_model_html_switchers(
    *,
    model: str | None,
    docs_build_dir: Path | None = None,
) -> None:
    actual_docs_build_dir = docs_build_dir or paths.docs_build_dir
    return _refresh_model_html_switchers_impl(
        model=model,
        docs_build_dir=actual_docs_build_dir,
        collect_model_html_variants=lambda: collect_model_html_variants(
            model=model,
            docs_build_dir=actual_docs_build_dir,
        ),
        build_manual_switcher_markup=build_manual_switcher_markup,
        inject_manual_switcher_into_html=inject_manual_switcher_into_html,
    )


_parse_csv_values = _parse_csv_values_impl


def resolve_requested_formats(cfg: dict, cli_formats: str | None) -> list[str]:
    return _resolve_requested_formats_impl(
        cfg,
        cli_formats,
        valid_formats=VALID_FORMATS,
        parse_csv_values=_parse_csv_values,
    )


def resolve_pdf_mode(cfg: dict, cli_pdf_mode: str | None) -> str:
    return _resolve_pdf_mode_impl(
        cfg,
        cli_pdf_mode,
        valid_pdf_modes=VALID_PDF_MODES,
    )


resolve_output_path = _resolve_output_path_impl


_slug_token = _slug_token_impl


def render_build_template(
    template: str,
    *,
    model: str | None,
    region: str | None,
    lang: str | None,
) -> str:
    return _render_build_template_impl(
        template,
        model=model,
        region=region,
        lang=lang,
        template_token_re=_TEMPLATE_TOKEN_RE,
        slug_token=_slug_token,
    )


def sphinx_build(
    builder: str,
    *,
    src_dir: Path,
    out_dir: Path,
    conf_dir: Path,
    model: str | None = None,
    region: str | None = None,
    lang: str | None = None,
    minimal_theme: bool = False,
    substitutions: dict[str, str] | None = None,
) -> None:
    return _sphinx_build_impl(
        builder,
        src_dir=src_dir,
        out_dir=out_dir,
        conf_dir=conf_dir,
        model=model,
        region=region,
        lang=lang,
        minimal_theme=minimal_theme,
        substitutions=substitutions,
        should_use_minimal_html_theme=_should_use_minimal_html_theme,
        resolve_sphinx_build_cmd=_resolve_sphinx_build_cmd,
        sphinx_tag_args=_sphinx_tag_args,
        with_rst_epilog=_with_rst_epilog,
        run=run,
        repo_root=paths.root,
    )


def patch_fonts(patch_fonts_script: str, main_tex: str, *, build_dir: Path) -> None:
    return _patch_fonts_impl(
        patch_fonts_script,
        main_tex,
        build_dir=build_dir,
        run=run,
        repo_root=paths.root,
        python_executable=sys.executable,
    )


def export_word_from_latex(
    tex_path: Path,
    *,
    resource_dir: Path,
    out_path: Path,
) -> Path:
    return _export_word_from_latex_impl(
        tex_path,
        resource_dir=resource_dir,
        out_path=out_path,
        which=shutil.which,
        run=run,
        repo_root=paths.root,
    )


def export_word_from_html(
    html_index: Path,
    *,
    out_path: Path,
) -> Path:
    return _export_word_from_html_impl(
        html_index,
        out_path=out_path,
        which=shutil.which,
        run=run,
        repo_root=paths.root,
    )


def export_pdf_from_docx_via_word(docx_path: Path, pdf_path: Path) -> Path:
    return _export_pdf_from_docx_via_word_impl(
        docx_path,
        pdf_path,
        platform=sys.platform,
        run_subprocess=subprocess.run,
        repo_root=paths.root,
    )


def ensure_target_identity(
    cfg: dict,
    *,
    model: str | None,
    region: str | None,
    lang: str,
    data_root: str | None = None,
    repo_root: Path | None = None,
) -> None:
    return _ensure_target_identity_impl(
        cfg,
        model=model,
        region=region,
        lang=lang,
        data_root=data_root,
        repo_root=repo_root or paths.root,
        resolve_product_name_for_build=resolve_product_name_for_build,
        resolve_spec_master_csv_path=_resolve_spec_master_csv_path,
    )


def prepare_manual_bundle(
    cfg: dict,
    *,
    model: str | None,
    region: str | None,
    lang: str | None = None,
    data_root: str | None = None,
    source_mode: str = "auto",
    page_selector: str | None = None,
    output_root: Path | None = None,
    write_wrapper_index: bool = True,
) -> MaterializedBundle:
    return _prepare_manual_bundle_impl(
        cfg,
        model=model,
        region=region,
        lang=lang,
        data_root=data_root,
        source_mode=source_mode,
        page_selector=page_selector,
        output_root=output_root,
        write_wrapper_index=write_wrapper_index,
        valid_source_modes=VALID_SOURCE_MODES,
        materialize_bundle=materialize_bundle,
        review_bundle_exists=review_bundle_exists,
        overlay_review_onto_bundle=overlay_review_onto_bundle,
        review_content_exists=review_content_exists,
        overlay_review_content_onto_bundle=overlay_review_content_onto_bundle,
        docs_dir=paths.docs_dir,
    )


def write_docs_root_index_for_targets(targets: list[BuildTarget]) -> None:
    return _write_docs_root_index_for_targets_impl(
        targets,
        discover_existing_bundle_targets=discover_existing_bundle_targets,
        bundle_dir_for_target=bundle_dir_for_target,
        docs_dir=paths.docs_dir,
    )


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
) -> None:
    return _build_target_impl(
        cfg,
        target_model=target_model,
        target_region=target_region,
        target_lang=target_lang,
        requested_formats=requested_formats,
        pdf_mode=pdf_mode,
        build_cfg=build_cfg,
        tools_cfg=tools_cfg,
        no_open=no_open,
        source_mode=source_mode,
        data_root=data_root,
        page_selector=page_selector,
        output_root=output_root,
        output_base_root=output_base_root,
        write_wrapper_index=write_wrapper_index,
        default_docs_build_dir=paths.docs_build_dir,
        resolve_cfg_languages=resolve_cfg_languages,
        build_root_for_target=build_root_for_target,
        ensure_target_identity=ensure_target_identity,
        prepare_manual_bundle=prepare_manual_bundle,
        render_build_template=render_build_template,
        resolve_output_path=resolve_output_path,
        sphinx_build=sphinx_build,
        patch_fonts=patch_fonts,
        compile_xelatex=compile_xelatex,
        export_word_from_bundle=export_word_from_bundle,
        export_word_from_html=export_word_from_html,
        export_word_from_latex=export_word_from_latex,
        export_pdf_from_docx_via_word=export_pdf_from_docx_via_word,
        copy_file=shutil.copy2,
        open_file=open_file,
        strip_html_cover_section=strip_html_cover_section,
        write_html_manual_meta=write_html_manual_meta,
        refresh_model_html_switchers=refresh_model_html_switchers,
    )


parse_args = _parse_args_impl


def main(argv: list[str] | None = None) -> None:
    _run_main_impl(
        argv,
        parse_args=parse_args,
        run_build=_run_build_impl,
        paths=paths,
        load_config=load_config,
        validate_loaded_config=validate_loaded_config,
        validate_layout_csv=validate_layout_csv,
        resolve_build_targets=resolve_build_targets,
        config_uses_model_token=_config_uses_model_token,
        config_uses_region_token=_config_uses_region_token,
        clean_build_targets=clean_build_targets,
        resolve_requested_formats=resolve_requested_formats,
        resolve_pdf_mode=resolve_pdf_mode,
        build_target=build_target,
        write_docs_root_index_for_targets=write_docs_root_index_for_targets,
    )


if __name__ == "__main__":
    main()
