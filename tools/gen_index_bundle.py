#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.config_pages import (
    ConfigPage,
    CoverPdfPage,
    CsvPage,
    GeneratedPage,
    PdfInsertPage,
    RstIncludePage,
)
from tools.draft_engine import (
    GeneratedPageRender,
    render_generated_page,
    resolve_snippet_registry_path,
)
from tools.gen_index_bundle_assets import (
    bundle_asset_target_path as _bundle_asset_target_path_impl,
    is_external_path as _is_external_path_impl,
    resolve_rst_asset_path as _resolve_rst_asset_path_impl,
    rewrite_rst_asset_paths as _rewrite_rst_asset_paths_impl,
    rewrite_single_asset_path as _rewrite_single_asset_path_impl,
    stage_bundle_asset as _stage_bundle_asset_impl,
)
from tools.gen_index_bundle_cli import parse_args as _parse_args_impl
from tools.gen_index_bundle_entry import run_bundle_entry as _run_bundle_entry_impl
from tools.gen_index_bundle_materialize import (
    build_bundle_manifest as _build_bundle_manifest_impl,
    copy_bundle_support_assets as _copy_bundle_support_assets_impl,
    preflight_contract_assets as _preflight_contract_assets_impl,
    render_contract_asset_path as _render_contract_asset_path_impl,
    resolve_contract_asset_path as _resolve_contract_asset_path_impl,
    write_bundle_conf_files as _write_bundle_conf_files_impl,
)
from tools.gen_index_bundle_page_render import (
    materialize_planned_page as _materialize_planned_page_impl,
    prepend_latex_lang as _prepend_latex_lang_impl,
    render_cover_page_rst as _render_cover_page_rst_impl,
    render_pdf_insert_page_rst as _render_pdf_insert_page_rst_impl,
)
from tools.gen_index_bundle_runtime import (
    build_materialized_bundle_result as _build_materialized_bundle_result_impl,
    materialize_bundle_pages as _materialize_bundle_pages_impl,
    prepare_bundle_workspace as _prepare_bundle_workspace_impl,
    resolve_bundle_materialization_context as _resolve_bundle_materialization_context_impl,
    write_bundle_outputs as _write_bundle_outputs_impl,
)
from tools.gen_index_bundle_plan import (
    base_file_name_for_plan as _base_file_name_for_plan_impl,
    build_index_from_pages as _build_index_from_pages_impl,
    build_wrapper_index_text as _build_wrapper_index_text_impl,
    ensure_unique_name as _ensure_unique_name_impl,
    plan_materialized_pages as _plan_materialized_pages_impl,
)
from tools.gen_index_bundle_models import (
    MaterializedBundle,
    PlannedPage,
    file_sha256 as _file_sha256,
    repo_relative as _repo_relative,
    select_planned_pages as _select_planned_pages,
)
from tools.gen_index_bundle_paths import (
    build_langs as _build_langs,
    bundle_dir_for_target,
    cleanup_legacy_rst_artifacts,
    format_bundle_tokenized as _format_tokenized,
    latex_apply_lang,
    latex_cover_block,
    latex_overview_block,
    load_config,
    read_included_page_paths,
    resolve_build_model,
    resolve_build_region,
    resolve_csv_rst_path as _resolve_csv_rst_path,
    resolve_generated_recipe_path as _resolve_generated_recipe_path,
    resolve_generated_source_path as _resolve_generated_source_path,
    resolve_generated_template_path as _resolve_generated_template_path,
    resolve_spec_master_csv_path as _resolve_spec_master_csv_path,
    source_path_for_contract as _source_path_for_contract,
)
from tools.page_manifest import resolve_config_pages_or_raise
from tools.utils.path_utils import get_paths  # noqa: E402
from tools.utils.targets import (
    resolve_output_lang,
)
from tools.word_bundle_common import (  # noqa: E402
    apply_rst_substitutions,
    derive_word_title,
    ensure_csv_page_rsts,
    fill_product_name_from_spec_master,
    load_rst_substitutions,
    load_word_context,
    pick_vars_map,
    resolve_config_path,
    resolve_reference_doc,
    resolve_spec_master_substitutions,
)

paths = get_paths()


def _base_file_name_for_plan(
    page: ConfigPage,
    *,
    lang: str | None,
    model: str | None,
    region: str | None,
) -> str:
    return _base_file_name_for_plan_impl(
        page,
        lang=lang,
        model=model,
        region=region,
        csv_page_cls=CsvPage,
        generated_page_cls=GeneratedPage,
        pdf_insert_page_cls=PdfInsertPage,
        rst_include_page_cls=RstIncludePage,
        cover_pdf_page_cls=CoverPdfPage,
        format_tokenized=_format_tokenized,
    )


def _ensure_unique_name(file_name: str, seen: set[str], ordinal: int) -> str:
    return _ensure_unique_name_impl(file_name, seen, ordinal)


def plan_materialized_pages(
    cfg: dict,
    model: str | None = None,
    region: str | None = None,
    *,
    root: Path | None = None,
) -> list[PlannedPage]:
    return _plan_materialized_pages_impl(
        cfg,
        model=model,
        region=region,
        root=root or paths.root,
        build_langs=_build_langs,
        resolve_config_pages_or_raise=resolve_config_pages_or_raise,
        planned_page_cls=PlannedPage,
        csv_page_cls=CsvPage,
        generated_page_cls=GeneratedPage,
        pdf_insert_page_cls=PdfInsertPage,
        rst_include_page_cls=RstIncludePage,
        cover_pdf_page_cls=CoverPdfPage,
        format_tokenized=_format_tokenized,
        base_file_name_for_plan=_base_file_name_for_plan,
        ensure_unique_name=_ensure_unique_name,
    )


def build_index_from_pages(
    cfg: dict,
    model: str | None = None,
    region: str | None = None,
    *,
    root: Path | None = None,
) -> str:
    return _build_index_from_pages_impl(
        cfg,
        model=model,
        region=region,
        root=root or paths.root,
        plan_materialized_pages=plan_materialized_pages,
    )


def build_wrapper_index_text(
    *,
    docs_dir: Path,
    bundle_dir: Path,
) -> str:
    return _build_wrapper_index_text_impl(
        docs_dir=docs_dir,
        bundle_dir=bundle_dir,
    )


_is_external_path = _is_external_path_impl


_resolve_rst_asset_path = _resolve_rst_asset_path_impl


_bundle_asset_target_path = _bundle_asset_target_path_impl


_stage_bundle_asset = _stage_bundle_asset_impl


_rewrite_single_asset_path = _rewrite_single_asset_path_impl


rewrite_rst_asset_paths = _rewrite_rst_asset_paths_impl


def _prepend_latex_lang(text: str, lang: str | None) -> str:
    return _prepend_latex_lang_impl(
        text,
        lang,
        latex_apply_lang=latex_apply_lang,
    )


def _render_cover_page_rst(title: str, file_name: str) -> str:
    return _render_cover_page_rst_impl(
        title,
        file_name,
        latex_cover_block=latex_cover_block,
    )


def _render_pdf_insert_page_rst(file_name: str, lang: str) -> str:
    return _render_pdf_insert_page_rst_impl(
        file_name,
        lang,
        latex_apply_lang=latex_apply_lang,
        latex_overview_block=latex_overview_block,
    )


def _copytree_replace(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def _render_contract_asset_path(
    raw_value: str,
    *,
    model: str | None,
    region: str | None,
    lang: str | None,
) -> str:
    return _render_contract_asset_path_impl(
        raw_value,
        model=model,
        region=region,
        lang=lang,
    )


def _resolve_contract_asset_path(
    raw_value: str,
    *,
    docs_dir: Path,
    repo_root: Path,
    model: str | None,
    region: str | None,
    lang: str | None,
) -> Path:
    return _resolve_contract_asset_path_impl(
        raw_value,
        docs_dir=docs_dir,
        repo_root=repo_root,
        model=model,
        region=region,
        lang=lang,
        render_contract_asset_path=_render_contract_asset_path,
    )


def _preflight_contract_assets(
    *,
    cfg: dict,
    docs_dir: Path,
    repo_root: Path,
    model: str | None,
    region: str | None,
    langs: list[str],
    planned_pages: list[PlannedPage],
) -> None:
    return _preflight_contract_assets_impl(
        docs_dir=docs_dir,
        repo_root=repo_root,
        model=model,
        region=region,
        langs=langs,
        planned_pages=planned_pages,
        bundle_dir=bundle_dir_for_target(docs_dir=docs_dir, model=model, region=region),
        source_path_for_contract=_source_path_for_contract,
        resolve_contract_asset_path=_resolve_contract_asset_path,
    )


def _write_bundle_conf_files(
    *,
    cfg: dict,
    docs_dir: Path,
    bundle_dir: Path,
) -> tuple[Path, Path]:
    return _write_bundle_conf_files_impl(
        cfg=cfg,
        docs_dir=docs_dir,
        bundle_dir=bundle_dir,
        copy_file=shutil.copy2,
    )


def _copy_bundle_support_assets(
    *,
    docs_dir: Path,
    bundle_dir: Path,
) -> None:
    return _copy_bundle_support_assets_impl(
        docs_dir=docs_dir,
        bundle_dir=bundle_dir,
        copytree_replace=_copytree_replace,
    )

    # Review overlays can copy page/generated RST that already reference
    # _assets/templates/word_template/common_assets/... paths. Stage the
    # shared template asset tree up front so those references remain valid
    # even when the current target bundle would not otherwise materialize
    # every referenced template asset during runtime generation.
    common_assets_src = docs_dir / "templates" / "word_template" / "common_assets"
    if common_assets_src.exists():
        _copytree_replace(
            common_assets_src,
            bundle_dir / "_assets" / "templates" / "word_template" / "common_assets",
        )


def _materialize_planned_page(
    planned: PlannedPage,
    *,
    cfg: dict,
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
) -> tuple[str, GeneratedPageRender | None]:
    return _materialize_planned_page_impl(
        planned,
        target_path=target_path,
        bundle_dir=bundle_dir,
        docs_dir=docs_dir,
        repo_root=repo_root,
        spec_master_csv=spec_master_csv,
        base_substitutions=base_substitutions,
        base_vars_map=base_vars_map,
        primary_lang=primary_lang,
        title=title,
        model=model,
        region=region,
        cover_pdf_page_cls=CoverPdfPage,
        pdf_insert_page_cls=PdfInsertPage,
        csv_page_cls=CsvPage,
        generated_page_cls=GeneratedPage,
        rst_include_page_cls=RstIncludePage,
        format_tokenized=_format_tokenized,
        render_cover_page_rst=_render_cover_page_rst,
        render_pdf_insert_page_rst=_render_pdf_insert_page_rst,
        fill_product_name_from_spec_master=fill_product_name_from_spec_master,
        resolve_spec_master_substitutions=resolve_spec_master_substitutions,
        resolve_csv_rst_path=_resolve_csv_rst_path,
        resolve_generated_recipe_path=_resolve_generated_recipe_path,
        resolve_generated_template_path=_resolve_generated_template_path,
        resolve_generated_source_path=_resolve_generated_source_path,
        render_generated_page=render_generated_page,
        resolve_snippet_registry_path=resolve_snippet_registry_path,
        resolve_config_path=resolve_config_path,
        apply_rst_substitutions=apply_rst_substitutions,
        rewrite_rst_asset_paths=rewrite_rst_asset_paths,
        prepend_latex_lang=_prepend_latex_lang,
    )


def materialize_bundle(
    cfg: dict,
    model: str | None = None,
    region: str | None = None,
    *,
    data_root: str | None = None,
    docs_dir: Path | None = None,
    repo_root: Path | None = None,
    ensure_csv_pages: bool = True,
    page_selector: str | None = None,
    bundle_dir_override: Path | None = None,
    write_wrapper_index: bool = True,
) -> MaterializedBundle:
    context = _resolve_bundle_materialization_context_impl(
        cfg,
        model=model,
        region=region,
        data_root=data_root,
        docs_dir=docs_dir or paths.docs_dir,
        repo_root=repo_root or paths.root,
        page_selector=page_selector,
        bundle_dir_override=bundle_dir_override,
        resolve_build_model=resolve_build_model,
        resolve_build_region=resolve_build_region,
        build_langs=_build_langs,
        resolve_output_lang=resolve_output_lang,
        resolve_config_pages_or_raise=resolve_config_pages_or_raise,
        select_planned_pages=_select_planned_pages,
        plan_materialized_pages=plan_materialized_pages,
        preflight_contract_assets=_preflight_contract_assets,
        resolve_spec_master_csv_path=_resolve_spec_master_csv_path,
        pick_vars_map=pick_vars_map,
        fill_product_name_from_spec_master=fill_product_name_from_spec_master,
        load_rst_substitutions=load_rst_substitutions,
        resolve_spec_master_substitutions=resolve_spec_master_substitutions,
        resolve_reference_doc=resolve_reference_doc,
        derive_word_title=derive_word_title,
        bundle_dir_for_target=bundle_dir_for_target,
    )

    conf_path, conf_base_path = _prepare_bundle_workspace_impl(
        context,
        cfg=cfg,
        data_root=data_root,
        ensure_csv_pages=ensure_csv_pages,
        bundle_dir_override=bundle_dir_override,
        csv_page_cls=CsvPage,
        cleanup_legacy_rst_artifacts=cleanup_legacy_rst_artifacts,
        remove_tree=shutil.rmtree,
        load_word_context=load_word_context,
        ensure_csv_page_rsts=ensure_csv_page_rsts,
        copy_bundle_support_assets=_copy_bundle_support_assets,
        write_bundle_conf_files=_write_bundle_conf_files,
    )

    page_paths, recipe_ids, snippet_ids = _materialize_bundle_pages_impl(
        context,
        cfg=cfg,
        materialize_planned_page=_materialize_planned_page,
    )

    _write_bundle_outputs_impl(
        context,
        cfg=cfg,
        write_wrapper_index=write_wrapper_index,
        page_paths=page_paths,
        recipe_ids=recipe_ids,
        snippet_ids=snippet_ids,
        build_index_from_pages=build_index_from_pages,
        build_wrapper_index_text=build_wrapper_index_text,
        build_bundle_manifest=_build_bundle_manifest_impl,
        repo_relative=lambda path: _repo_relative(path, repo_root=context.repo_root),
        file_sha256=_file_sha256,
    )

    return _build_materialized_bundle_result_impl(
        context,
        conf_path=conf_path,
        conf_base_path=conf_base_path,
        page_paths=page_paths,
        recipe_ids=recipe_ids,
        snippet_ids=snippet_ids,
        materialized_bundle_cls=MaterializedBundle,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return _parse_args_impl(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    return _run_bundle_entry_impl(
        args,
        repo_root=paths.root,
        load_config=load_config,
        materialize_bundle=materialize_bundle,
    )


if __name__ == "__main__":
    main()
