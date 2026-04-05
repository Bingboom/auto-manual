#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass
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
from tools.config_loader import load_config_mapping
from tools.data_snapshot import resolve_data_snapshot_paths
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
from tools.gen_index_bundle_plan import (
    base_file_name_for_plan as _base_file_name_for_plan_impl,
    build_index_from_pages as _build_index_from_pages_impl,
    build_wrapper_index_text as _build_wrapper_index_text_impl,
    ensure_unique_name as _ensure_unique_name_impl,
    plan_materialized_pages as _plan_materialized_pages_impl,
)
from tools.page_manifest import resolve_config_pages_or_raise
from tools.utils.path_utils import get_paths  # noqa: E402
from tools.utils.targets import (
    format_tokenized,
    resolve_build_languages,
    resolve_build_model as resolve_target_model,
    resolve_build_region as resolve_target_region,
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

_INCLUDE_RE = re.compile(r"^\s*\.\.\s+include::\s+(\S+)\s*$")


@dataclass(frozen=True)
class PlannedPage:
    page: ConfigPage
    lang: str | None
    file_name: str


@dataclass(frozen=True)
class MaterializedBundle:
    bundle_dir: Path
    page_dir: Path
    index_path: Path
    conf_path: Path
    conf_base_path: Path
    wrapper_index_path: Path
    page_paths: tuple[Path, ...]
    title: str
    reference_doc: Path | None
    model: str | None
    region: str | None
    lang: str | None
    manifest_path: Path | None = None
    page_manifest_path: Path | None = None
    recipe_ids: tuple[str, ...] = ()
    snippet_ids: tuple[str, ...] = ()


def _repo_relative(path: Path | None, *, repo_root: Path) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve(strict=False).relative_to(repo_root.resolve(strict=False)).as_posix()
    except ValueError:
        return path.as_posix()


def _file_sha256(path: Path | None) -> str | None:
    if path is None or not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _select_planned_pages(planned_pages: list[PlannedPage], page_selector: str | None) -> list[PlannedPage]:
    if not (page_selector or "").strip():
        return planned_pages

    selector = page_selector.strip()
    csv_matches = [planned for planned in planned_pages if isinstance(planned.page, CsvPage) and planned.page.page == selector]
    if csv_matches:
        return csv_matches
    generated_matches = [
        planned for planned in planned_pages if isinstance(planned.page, GeneratedPage) and planned.page.page == selector
    ]
    if generated_matches:
        return generated_matches

    stem_matches = [planned for planned in planned_pages if Path(planned.file_name).stem == selector]
    if not stem_matches:
        raise RuntimeError(f"Page selector did not match any materialized page: {selector}")
    if len(stem_matches) > 1:
        raise RuntimeError(f"Page selector matched multiple materialized pages: {selector}")
    return stem_matches


def load_config(cfg_path: Path) -> dict:
    return load_config_mapping(cfg_path)


def latex_cover_block(file_name: str) -> list[str]:
    return [
        ".. raw:: latex",
        "",
        f"   \\includepdf[pages=1-,fitpaper=true,pagecommand={{\\thispagestyle{{empty}}}}]{{{file_name}}}",
        "   \\clearpage",
        "   \\pagenumbering{arabic}",
        "   \\setcounter{page}{1}",
        "",
    ]


def latex_apply_lang(lang: str) -> list[str]:
    return [
        ".. raw:: latex",
        "",
        f"   \\HBApplyLang{{{lang}}}",
        "",
    ]


def latex_overview_block(file_name: str) -> list[str]:
    return [
        ".. raw:: latex",
        "",
        f"   \\includepdf[pages=1-,fitpaper=true,pagecommand={{\\thispagestyle{{normal}}}}]{{{file_name}}}",
        "",
    ]


def _format_tokenized(
    text: str,
    model: str | None,
    region: str | None,
) -> str:
    return format_tokenized(text, None, model, region)


def resolve_build_model(cfg: dict, arg_model: str | None) -> str | None:
    return resolve_target_model(cfg, arg_model)


def resolve_build_region(cfg: dict, arg_region: str | None) -> str | None:
    return resolve_target_region(cfg, arg_region)


def _build_langs(cfg: dict) -> list[str]:
    langs = resolve_build_languages(cfg)
    return langs or ["en"]


def _bundle_component(value: str | None, fallback: str) -> str:
    text = (value or "").strip() or fallback
    return text.replace("/", "_").replace("\\", "_").replace(":", "_")


def bundle_dir_for_target(
    *,
    docs_dir: Path,
    docs_build_dir: Path | None = None,
    model: str | None,
    region: str | None,
    lang: str | None = None,
) -> Path:
    actual_docs_build_dir = docs_build_dir or (docs_dir / "_build")
    target_root = actual_docs_build_dir / _bundle_component(model, "_shared") / _bundle_component(region, "_default")
    if (lang or "").strip():
        target_root = target_root / _bundle_component(lang, "_default")
    return target_root / "rst"


def _legacy_bundle_dir_for_target(
    *,
    docs_dir: Path,
    model: str | None,
    region: str | None,
) -> Path:
    return docs_dir / _bundle_component(model, "_shared") / _bundle_component(region, "_default")


def _legacy_generated_dir_for_target(
    *,
    docs_dir: Path,
    model: str | None,
) -> Path:
    return docs_dir / "generated" / _bundle_component(model, "_shared")


def cleanup_legacy_rst_artifacts(
    *,
    docs_dir: Path,
    model: str | None,
    region: str | None,
) -> None:
    legacy_bundle_dir = _legacy_bundle_dir_for_target(
        docs_dir=docs_dir,
        model=model,
        region=region,
    )
    legacy_generated_dir = _legacy_generated_dir_for_target(
        docs_dir=docs_dir,
        model=model,
    )

    if legacy_bundle_dir.exists():
        shutil.rmtree(legacy_bundle_dir)
        parent = legacy_bundle_dir.parent
        if parent != docs_dir and parent.exists() and not any(parent.iterdir()):
            parent.rmdir()

    if legacy_generated_dir.exists():
        shutil.rmtree(legacy_generated_dir)
        parent = legacy_generated_dir.parent
        if parent.exists() and not any(parent.iterdir()):
            parent.rmdir()


def _resolve_spec_master_csv_path(
    cfg: dict,
    *,
    repo_root: Path,
    data_root: str | None,
    model: str | None,
    region: str | None,
) -> Path:
    return resolve_data_snapshot_paths(
        cfg,
        repo_root=repo_root,
        data_root=data_root,
        model=model,
        region=region,
    ).spec_master_csv


def _resolve_csv_rst_path(
    *,
    source_root: Path,
    page: CsvPage,
    lang: str,
    model: str | None,
    region: str | None,
) -> Path:
    if page.include_dir is None:
        rel = f"{page.page}_{lang}.rst"
    else:
        rel = str(Path(_format_tokenized(page.include_dir, model, region)) / f"{page.page}_{lang}.rst")
    return source_root / rel


def _resolve_generated_source_path(
    *,
    bundle_dir: Path,
    page: GeneratedPage,
    lang: str,
    model: str | None,
    region: str | None,
) -> Path | None:
    if page.include_dir is None:
        return None
    rel = Path(_format_tokenized(page.include_dir, model, region)) / f"{page.page}_{lang}.rst"
    return bundle_dir / rel


def _resolve_generated_template_path(
    *,
    docs_dir: Path,
    page: GeneratedPage,
    model: str | None,
    region: str | None,
) -> Path:
    return resolve_config_path(docs_dir, page.template, model, region)


def _resolve_generated_recipe_path(
    *,
    docs_dir: Path,
    page: GeneratedPage,
    model: str | None,
    region: str | None,
) -> Path:
    return resolve_config_path(docs_dir, page.recipe, model, region)


def _source_path_for_contract(
    page: ConfigPage,
    *,
    docs_dir: Path,
    bundle_dir: Path,
    model: str | None,
    region: str | None,
    lang: str | None,
) -> Path | None:
    if isinstance(page, RstIncludePage):
        return resolve_config_path(docs_dir, page.file, model, region)
    if isinstance(page, GeneratedPage):
        return _resolve_generated_template_path(docs_dir=docs_dir, page=page, model=model, region=region)
    if isinstance(page, CsvPage):
        if lang is None:
            return None
        return _resolve_csv_rst_path(
            source_root=bundle_dir,
            page=page,
            lang=lang,
            model=model,
            region=region,
        )
    return None


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


def read_included_page_paths(index_path: Path) -> list[Path]:
    out: list[Path] = []
    for line in index_path.read_text(encoding="utf-8").splitlines():
        match = _INCLUDE_RE.match(line)
        if not match:
            continue
        out.append((index_path.parent / match.group(1)).resolve())
    return out


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
    actual_docs_dir = docs_dir or paths.docs_dir
    actual_root = repo_root or paths.root
    target_model = resolve_build_model(cfg, model)
    target_region = resolve_build_region(cfg, region)
    build_langs = _build_langs(cfg)
    primary_lang = str(build_langs[0]) if build_langs else "en"
    output_lang = resolve_output_lang(cfg)
    resolved_page_source = resolve_config_pages_or_raise(
        cfg,
        default_languages=build_langs,
        root=actual_root,
        model=target_model,
        region=target_region,
        error_prefix="config.pages",
    )
    page_manifest_path = resolved_page_source.manifest_path
    planned_pages = _select_planned_pages(
        plan_materialized_pages(cfg, model=target_model, region=target_region, root=actual_root),
        page_selector,
    )
    _preflight_contract_assets(
        cfg=cfg,
        docs_dir=actual_docs_dir,
        repo_root=actual_root,
        model=target_model,
        region=target_region,
        langs=build_langs,
        planned_pages=planned_pages,
    )

    spec_master_csv = _resolve_spec_master_csv_path(
        cfg,
        repo_root=actual_root,
        data_root=data_root,
        model=target_model,
        region=target_region,
    )
    base_vars_map = pick_vars_map(target_model, target_region)
    title_vars = fill_product_name_from_spec_master(
        base_vars_map,
        spec_master_csv=spec_master_csv,
        model=target_model,
        region=target_region,
        lang=primary_lang,
    )
    base_substitutions = load_rst_substitutions(actual_docs_dir / "conf_base.py")
    title_substitutions = {
        **base_substitutions,
        **resolve_spec_master_substitutions(
            spec_master_csv=spec_master_csv,
            model=target_model,
            region=target_region,
            lang=primary_lang,
        ),
    }
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    reference_doc = resolve_reference_doc(build_cfg.get("word_reference_doc"), root=actual_root)
    title = derive_word_title(build_cfg, reference_doc, title_substitutions, title_vars)

    bundle_dir = bundle_dir_override or bundle_dir_for_target(
        docs_dir=actual_docs_dir,
        model=target_model,
        region=target_region,
        lang=output_lang,
    )
    generated_dir = bundle_dir / "generated"
    page_dir = bundle_dir / "page"
    index_path = bundle_dir / "index.rst"
    wrapper_index_path = actual_docs_dir / "index.rst"
    bundle_manifest_path = bundle_dir / "bundle_manifest.json"

    if bundle_dir_override is None:
        cleanup_legacy_rst_artifacts(
            docs_dir=actual_docs_dir,
            model=target_model,
            region=target_region,
        )

    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)

    if ensure_csv_pages and any(isinstance(item.page, CsvPage) for item in planned_pages):
        builder = load_word_context(
            cfg,
            target_model,
            target_region,
            phase1_output_dir=generated_dir,
            data_root=data_root,
        )
        ensure_csv_page_rsts(cfg, builder, target_model, target_region)
    page_dir.mkdir(parents=True, exist_ok=True)
    _copy_bundle_support_assets(docs_dir=actual_docs_dir, bundle_dir=bundle_dir)
    conf_path, conf_base_path = _write_bundle_conf_files(
        cfg=cfg,
        docs_dir=actual_docs_dir,
        bundle_dir=bundle_dir,
    )

    page_paths: list[Path] = []
    recipe_ids: list[str] = []
    snippet_ids: list[str] = []
    for planned in planned_pages:
        target_path = page_dir / planned.file_name
        rendered, generated_render = _materialize_planned_page(
            planned,
            cfg=cfg,
            target_path=target_path,
            bundle_dir=bundle_dir,
            docs_dir=actual_docs_dir,
            repo_root=actual_root,
            spec_master_csv=spec_master_csv,
            base_substitutions=base_substitutions,
            base_vars_map=base_vars_map,
            primary_lang=primary_lang,
            title=title,
            model=target_model,
            region=target_region,
        )
        target_path.write_text(rendered if rendered.endswith("\n") else f"{rendered}\n", encoding="utf-8")
        page_paths.append(target_path)
        if generated_render is not None:
            recipe_ids.append(generated_render.recipe_path.stem)
            snippet_ids.extend(generated_render.used_snippet_ids)

    index_text = build_index_from_pages(cfg, model=target_model, region=target_region, root=actual_root)
    index_path.write_text(index_text, encoding="utf-8")
    if write_wrapper_index:
        wrapper_index_path.write_text(
            build_wrapper_index_text(
                docs_dir=actual_docs_dir,
                bundle_dir=bundle_dir,
            ),
            encoding="utf-8",
        )

    bundle_manifest = _build_bundle_manifest_impl(
        model=target_model,
        region=target_region,
        lang=output_lang,
        page_manifest_path=page_manifest_path,
        spec_master_csv=spec_master_csv,
        page_paths=page_paths,
        generated_dir=generated_dir,
        recipe_ids=recipe_ids,
        snippet_ids=snippet_ids,
        repo_root=actual_root,
        repo_relative=lambda path: _repo_relative(path, repo_root=actual_root),
        file_sha256=_file_sha256,
    )
    bundle_manifest_path.write_text(json.dumps(bundle_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return MaterializedBundle(
        bundle_dir=bundle_dir,
        page_dir=page_dir,
        index_path=index_path,
        conf_path=conf_path,
        conf_base_path=conf_base_path,
        wrapper_index_path=wrapper_index_path,
        page_paths=tuple(page_paths),
        title=title,
        reference_doc=reference_doc,
        model=target_model,
        region=target_region,
        lang=output_lang,
        manifest_path=bundle_manifest_path,
        page_manifest_path=page_manifest_path,
        recipe_ids=tuple(dict.fromkeys(recipe_ids)),
        snippet_ids=tuple(dict.fromkeys(snippet_ids)),
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
