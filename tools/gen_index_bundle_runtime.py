from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class BundleMaterializationContext:
    docs_dir: Path
    repo_root: Path
    target_model: str | None
    target_region: str | None
    build_langs: tuple[str, ...]
    primary_lang: str
    output_lang: str | None
    page_manifest_path: Path | None
    planned_pages: tuple[Any, ...]
    spec_master_csv: Path
    base_vars_map: dict[str, str]
    base_substitutions: dict[str, str]
    reference_doc: Path | None
    title: str
    bundle_dir: Path
    generated_dir: Path
    page_dir: Path
    index_path: Path
    wrapper_index_path: Path
    bundle_manifest_path: Path


def resolve_bundle_materialization_context(
    cfg: dict,
    *,
    model: str | None,
    region: str | None,
    lang: str | None,
    data_root: str | None,
    docs_dir: Path,
    repo_root: Path,
    page_selector: str | None,
    bundle_dir_override: Path | None,
    resolve_build_model: Callable[[dict, str | None], str | None],
    resolve_build_region: Callable[[dict, str | None], str | None],
    build_langs: Callable[[dict], list[str]],
    resolve_output_lang: Callable[[dict], str | None],
    resolve_config_pages_or_raise: Callable[..., Any],
    select_planned_pages: Callable[[list[Any], str | None], list[Any]],
    plan_materialized_pages: Callable[..., list[Any]],
    preflight_contract_assets: Callable[..., None],
    resolve_spec_master_csv_path: Callable[..., Path],
    pick_vars_map: Callable[[str | None, str | None], dict[str, str]],
    fill_product_name_from_spec_master: Callable[..., dict[str, str]],
    load_rst_substitutions: Callable[[Path], dict[str, str]],
    load_config_rst_substitutions: Callable[[dict], dict[str, str]],
    resolve_spec_master_substitutions: Callable[..., dict[str, str]],
    resolve_reference_doc: Callable[..., Path | None],
    derive_word_title: Callable[..., str],
    bundle_dir_for_target: Callable[..., Path],
) -> BundleMaterializationContext:
    target_model = resolve_build_model(cfg, model)
    target_region = resolve_build_region(cfg, region)
    configured_langs = tuple(build_langs(cfg))
    requested_lang = ""
    if (lang or "").strip():
        from tools.language_aliases import normalize_language

        requested_lang = normalize_language(lang, supported=configured_langs)
        if requested_lang not in configured_langs:
            raise RuntimeError(
                f"Requested lang {lang!r} is not declared in build.languages: {list(configured_langs)}"
            )
    resolved_langs = (requested_lang,) if requested_lang else configured_langs
    primary_lang = str(resolved_langs[0]) if resolved_langs else "en"
    output_lang = requested_lang or resolve_output_lang(cfg)

    resolved_page_source = resolve_config_pages_or_raise(
        cfg,
        default_languages=list(resolved_langs),
        root=repo_root,
        model=target_model,
        region=target_region,
        error_prefix="config.pages",
    )
    page_manifest_path = resolved_page_source.manifest_path
    planned_pages = tuple(
        select_planned_pages(
            plan_materialized_pages(
                cfg,
                model=target_model,
                region=target_region,
                langs=list(resolved_langs),
                root=repo_root,
            ),
            page_selector,
        )
    )
    preflight_contract_assets(
        cfg=cfg,
        docs_dir=docs_dir,
        repo_root=repo_root,
        model=target_model,
        region=target_region,
        langs=list(resolved_langs),
        planned_pages=list(planned_pages),
    )

    spec_master_csv = resolve_spec_master_csv_path(
        cfg,
        repo_root=repo_root,
        data_root=data_root,
        model=target_model,
        region=target_region,
    )
    page_copy_csv = spec_master_csv.parent / "page_copy.csv"
    base_vars_map = pick_vars_map(target_model, target_region)
    title_vars = fill_product_name_from_spec_master(
        base_vars_map,
        spec_master_csv=spec_master_csv,
        model=target_model,
        region=target_region,
        lang=primary_lang,
    )
    base_substitutions = {
        **load_rst_substitutions(docs_dir / "conf_base.py"),
        **load_config_rst_substitutions(cfg, lang=primary_lang, page_copy_csv=page_copy_csv),
    }
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
    reference_doc = resolve_reference_doc(build_cfg.get("word_reference_doc"), root=repo_root)
    title = derive_word_title(
        build_cfg,
        reference_doc,
        title_substitutions,
        title_vars,
        lang=primary_lang,
        page_copy_csv=page_copy_csv,
    )

    bundle_dir = bundle_dir_override or bundle_dir_for_target(
        docs_dir=docs_dir,
        model=target_model,
        region=target_region,
        lang=output_lang,
    )
    generated_dir = bundle_dir / "generated"
    page_dir = bundle_dir / "page"
    index_path = bundle_dir / "index.rst"
    wrapper_index_path = docs_dir / "index.rst"
    bundle_manifest_path = bundle_dir / "bundle_manifest.json"

    return BundleMaterializationContext(
        docs_dir=docs_dir,
        repo_root=repo_root,
        target_model=target_model,
        target_region=target_region,
        build_langs=resolved_langs,
        primary_lang=primary_lang,
        output_lang=output_lang,
        page_manifest_path=page_manifest_path,
        planned_pages=planned_pages,
        spec_master_csv=spec_master_csv,
        base_vars_map=base_vars_map,
        base_substitutions=base_substitutions,
        reference_doc=reference_doc,
        title=title,
        bundle_dir=bundle_dir,
        generated_dir=generated_dir,
        page_dir=page_dir,
        index_path=index_path,
        wrapper_index_path=wrapper_index_path,
        bundle_manifest_path=bundle_manifest_path,
    )


def prepare_bundle_workspace(
    context: BundleMaterializationContext,
    *,
    cfg: dict,
    data_root: str | None,
    ensure_csv_pages: bool,
    bundle_dir_override: Path | None,
    csv_page_cls: type[Any],
    cleanup_legacy_rst_artifacts: Callable[..., None],
    remove_tree: Callable[[Path], None],
    load_word_context: Callable[..., Any],
    ensure_csv_page_rsts: Callable[..., None],
    copy_bundle_support_assets: Callable[..., None],
    write_bundle_conf_files: Callable[..., tuple[Path, Path]],
) -> tuple[Path, Path]:
    if bundle_dir_override is None:
        cleanup_legacy_rst_artifacts(
            docs_dir=context.docs_dir,
            model=context.target_model,
            region=context.target_region,
        )

    if context.bundle_dir.exists():
        remove_tree(context.bundle_dir)

    if ensure_csv_pages and any(isinstance(item.page, csv_page_cls) for item in context.planned_pages):
        builder = load_word_context(
            cfg,
            context.target_model,
            context.target_region,
            csv_page_output_dir=context.generated_dir,
            data_root=data_root,
        )
        ensure_csv_page_rsts(
            cfg,
            builder,
            context.target_model,
            context.target_region,
            langs=context.build_langs,
        )

    context.page_dir.mkdir(parents=True, exist_ok=True)
    copy_bundle_support_assets(docs_dir=context.docs_dir, bundle_dir=context.bundle_dir)
    return write_bundle_conf_files(
        cfg=cfg,
        docs_dir=context.docs_dir,
        bundle_dir=context.bundle_dir,
    )


def materialize_bundle_pages(
    context: BundleMaterializationContext,
    *,
    cfg: dict,
    materialize_planned_page: Callable[..., tuple[str, Any | None]],
) -> tuple[list[Path], list[str], list[str]]:
    page_paths: list[Path] = []
    recipe_ids: list[str] = []
    snippet_ids: list[str] = []

    for planned in context.planned_pages:
        target_path = context.page_dir / planned.file_name
        rendered, generated_render = materialize_planned_page(
            planned,
            cfg=cfg,
            target_path=target_path,
            bundle_dir=context.bundle_dir,
            docs_dir=context.docs_dir,
            repo_root=context.repo_root,
            spec_master_csv=context.spec_master_csv,
            base_substitutions=context.base_substitutions,
            base_vars_map=context.base_vars_map,
            primary_lang=context.primary_lang,
            title=context.title,
            model=context.target_model,
            region=context.target_region,
        )
        target_path.write_text(rendered if rendered.endswith("\n") else f"{rendered}\n", encoding="utf-8")
        page_paths.append(target_path)
        if generated_render is not None:
            recipe_ids.append(generated_render.recipe_path.stem)
            snippet_ids.extend(generated_render.used_snippet_ids)

    return page_paths, recipe_ids, snippet_ids


def write_bundle_outputs(
    context: BundleMaterializationContext,
    *,
    cfg: dict,
    write_wrapper_index: bool,
    page_paths: list[Path],
    recipe_ids: list[str],
    snippet_ids: list[str],
    build_index_from_pages: Callable[..., str],
    build_wrapper_index_text: Callable[..., str],
    build_bundle_manifest: Callable[..., dict[str, object]],
    repo_relative: Callable[[Path | None], str | None],
    file_sha256: Callable[[Path | None], str | None],
) -> None:
    index_text = build_index_from_pages(
        cfg,
        model=context.target_model,
        region=context.target_region,
        langs=list(context.build_langs),
        root=context.repo_root,
    )
    context.index_path.write_text(index_text, encoding="utf-8")

    if write_wrapper_index:
        context.wrapper_index_path.write_text(
            build_wrapper_index_text(
                docs_dir=context.docs_dir,
                bundle_dir=context.bundle_dir,
            ),
            encoding="utf-8",
        )

    bundle_manifest = build_bundle_manifest(
        model=context.target_model,
        region=context.target_region,
        lang=context.output_lang,
        page_manifest_path=context.page_manifest_path,
        spec_master_csv=context.spec_master_csv,
        page_paths=page_paths,
        generated_dir=context.generated_dir,
        recipe_ids=recipe_ids,
        snippet_ids=snippet_ids,
        repo_root=context.repo_root,
        repo_relative=repo_relative,
        file_sha256=file_sha256,
    )
    context.bundle_manifest_path.write_text(
        json.dumps(bundle_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_materialized_bundle_result(
    context: BundleMaterializationContext,
    *,
    conf_path: Path,
    conf_base_path: Path,
    page_paths: list[Path],
    recipe_ids: list[str],
    snippet_ids: list[str],
    materialized_bundle_cls: type[Any],
) -> Any:
    return materialized_bundle_cls(
        bundle_dir=context.bundle_dir,
        page_dir=context.page_dir,
        index_path=context.index_path,
        conf_path=conf_path,
        conf_base_path=conf_base_path,
        wrapper_index_path=context.wrapper_index_path,
        page_paths=tuple(page_paths),
        title=context.title,
        reference_doc=context.reference_doc,
        model=context.target_model,
        region=context.target_region,
        lang=context.output_lang,
        manifest_path=context.bundle_manifest_path,
        page_manifest_path=context.page_manifest_path,
        recipe_ids=tuple(dict.fromkeys(recipe_ids)),
        snippet_ids=tuple(dict.fromkeys(snippet_ids)),
    )
