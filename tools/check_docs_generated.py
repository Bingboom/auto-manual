from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

SNIPPET_SLOT_RE = re.compile(r"\{\{snippet:([a-zA-Z0-9_.-]+)\}\}")


@dataclass(frozen=True)
class GeneratedPageRuntime:
    spec_rows: list[dict[str, str]]
    page_copy_csv: Path
    registry_path: Path
    registry_entries: list[Any]
    registry_error: RuntimeError | None
    contract_ids: set[str]
    contract_file_names: set[str]
    base_substitutions: dict[str, str]


def _issue(
    issue_cls: type[Any],
    *,
    code: str,
    message: str,
    target: Any,
    path: Path,
    lang: str | None = None,
) -> Any:
    payload: dict[str, Any] = {
        "code": code,
        "message": message,
        "model": target.model,
        "region": target.region,
        "path": path,
    }
    if lang is not None:
        payload["lang"] = lang
    return issue_cls(**payload)


def _resolve_generated_pages(
    cfg: dict,
    *,
    repo_root: Path,
    target: Any,
    langs: list[str],
    generated_page_cls: type[Any],
    resolve_page_manifest_path: Callable[..., Path | None],
    resolve_config_pages_or_raise: Callable[..., Any],
) -> list[Any]:
    manifest_path = resolve_page_manifest_path(cfg, root=repo_root, model=target.model, region=target.region)
    if manifest_path is None:
        pages_raw = cfg.get("pages")
        if not isinstance(pages_raw, list) or not pages_raw:
            return []

    pages = resolve_config_pages_or_raise(
        cfg,
        default_languages=langs,
        root=repo_root,
        model=target.model,
        region=target.region,
        error_prefix="config.pages",
    ).pages
    return [page for page in pages if isinstance(page, generated_page_cls)]


def _load_generated_runtime(
    cfg: dict,
    *,
    docs_dir: Path,
    data_root: str | None,
    resolve_spec_master_csv_path: Callable[..., Path],
    read_spec_master_rows: Callable[[Path], list[dict[str, str]]],
    resolve_snippet_registry_path: Callable[[Path], Path],
    load_snippet_registry: Callable[[Path], list[Any]],
    load_page_contracts: Callable[[Path], list[Any]],
    resolve_contracts_dir: Callable[..., Path],
    load_rst_substitutions: Callable[[Path], dict[str, str]],
) -> GeneratedPageRuntime:
    spec_master_csv = resolve_spec_master_csv_path(cfg, data_root=data_root)
    spec_rows = read_spec_master_rows(spec_master_csv)
    registry_path = resolve_snippet_registry_path(docs_dir)
    registry_entries: list[Any] = []
    registry_error: RuntimeError | None = None
    try:
        registry_entries = load_snippet_registry(registry_path)
    except RuntimeError as exc:
        registry_error = exc

    contracts = load_page_contracts(resolve_contracts_dir(docs_dir=docs_dir))
    return GeneratedPageRuntime(
        spec_rows=spec_rows,
        page_copy_csv=spec_master_csv.parent / "page_copy.csv",
        registry_path=registry_path,
        registry_entries=registry_entries,
        registry_error=registry_error,
        contract_ids={contract.page_id for contract in contracts},
        contract_file_names={f"{contract.page_id}.yaml" for contract in contracts},
        base_substitutions=load_rst_substitutions(docs_dir / "conf_base.py"),
    )


def _load_page_artifacts(
    *,
    docs_dir: Path,
    page: Any,
    target: Any,
    issue_cls: type[Any],
    resolve_config_path: Callable[..., Path],
    load_draft_recipe: Callable[[Path], Any],
) -> tuple[Any | None, str | None, Path, Path, list[Any]]:
    issues: list[Any] = []
    recipe_path = resolve_config_path(docs_dir, page.recipe, target.model, target.region)
    template_path = resolve_config_path(docs_dir, page.template, target.model, target.region)

    if not recipe_path.exists():
        issues.append(
            _issue(
                issue_cls,
                code="MISSING_RECIPE",
                message=f"Generated page recipe not found: {recipe_path}",
                target=target,
                path=recipe_path,
            )
        )
        return None, None, recipe_path, template_path, issues

    if not template_path.exists():
        issues.append(
            _issue(
                issue_cls,
                code="MISSING_GENERATED_TEMPLATE",
                message=f"Generated page template not found: {template_path}",
                target=target,
                path=template_path,
            )
        )
        return None, None, recipe_path, template_path, issues

    try:
        recipe = load_draft_recipe(recipe_path)
    except RuntimeError as exc:
        issues.append(
            _issue(
                issue_cls,
                code="INVALID_RECIPE",
                message=str(exc),
                target=target,
                path=recipe_path,
            )
        )
        return None, None, recipe_path, template_path, issues

    return recipe, template_path.read_text(encoding="utf-8"), recipe_path, template_path, issues


def _template_slot_issues(
    *,
    page: Any,
    recipe: Any,
    target: Any,
    recipe_path: Path,
    template_text: str,
    issue_cls: type[Any],
) -> list[Any]:
    issues: list[Any] = []
    if recipe.page_id != page.page:
        issues.append(
            _issue(
                issue_cls,
                code="RECIPE_PAGE_ID_MISMATCH",
                message=(
                    f"Generated page '{page.page}' references recipe page_id '{recipe.page_id}'. "
                    "These values should match."
                ),
                target=target,
                path=recipe_path,
            )
        )

    template_slots = {
        match.group(1).strip() for match in SNIPPET_SLOT_RE.finditer(template_text) if match.group(1).strip()
    }
    missing_slots = sorted(template_slots - set(recipe.snippet_slots))
    if missing_slots:
        issues.append(
            _issue(
                issue_cls,
                code="UNBOUND_SNIPPET_SLOT",
                message=f"Recipe '{recipe.page_id}' is missing snippet_slots for: {', '.join(missing_slots)}",
                target=target,
                path=recipe_path,
            )
        )

    unused_slots = sorted(set(recipe.snippet_slots) - template_slots)
    if unused_slots:
        issues.append(
            _issue(
                issue_cls,
                code="UNUSED_SNIPPET_SLOT",
                message=f"Recipe '{recipe.page_id}' declares unused snippet_slots: {', '.join(unused_slots)}",
                target=target,
                path=recipe_path,
            )
        )

    return issues


def _field_map_missing_row_issues(
    *,
    recipe: Any,
    target: Any,
    lang: str,
    recipe_path: Path,
    spec_rows: list[dict[str, str]],
    issue_cls: type[Any],
    format_field_binding: Callable[..., str],
    resolve_spec_value_from_rows: Callable[..., Any | None],
) -> list[Any]:
    field_binding_misses = [
        format_field_binding(binding, owner=f"field_map.{placeholder}")
        for placeholder, binding in recipe.field_map.items()
        if resolve_spec_value_from_rows(
            spec_rows,
            model=target.model,
            region=target.region,
            lang=lang,
            row_key=binding.row_key,
            pages=binding.pages,
            line_order=binding.line_order,
            usage_type=binding.usage_type,
            placement_key=binding.placement_key,
            value_role=binding.value_role,
            variant_key=binding.variant_key,
        )
        is None
        and binding.default is None
        and getattr(binding, "page_copy_key", None) is None
    ]
    if not field_binding_misses:
        return []

    return [
        _issue(
            issue_cls,
            code="RECIPE_MISSING_FIELD_MAP_ROWS",
            message=(
                f"Recipe '{recipe.page_id}' is missing field_map rows for lang '{lang}': "
                f"{', '.join(field_binding_misses)}"
            ),
            target=target,
            path=recipe_path,
            lang=lang,
        )
    ]


def _field_map_ambiguity_issues(
    *,
    recipe: Any,
    target: Any,
    lang: str,
    recipe_path: Path,
    spec_rows: list[dict[str, str]],
    issue_cls: type[Any],
    format_field_binding: Callable[..., str],
    collect_matching_spec_rows: Callable[..., list[dict[str, str]]],
    pick_spec_value: Callable[[dict[str, str], str], str],
) -> list[Any]:
    issues: list[Any] = []
    for placeholder, binding in recipe.field_map.items():
        matching_rows = collect_matching_spec_rows(
            spec_rows,
            model=target.model,
            region=target.region,
            lang=lang,
            row_key=binding.row_key,
            pages=binding.pages,
            line_order=binding.line_order,
            usage_type=binding.usage_type,
            placement_key=binding.placement_key,
            value_role=binding.value_role,
            variant_key=binding.variant_key,
        )
        distinct_values = sorted({pick_spec_value(row, lang) for row in matching_rows if pick_spec_value(row, lang)})
        if len(distinct_values) <= 1:
            continue
        issues.append(
            _issue(
                issue_cls,
                code="AMBIGUOUS_FIELD_MAP_ROWS",
                message=(
                    f"Recipe '{recipe.page_id}' {format_field_binding(binding, owner=f'field_map.{placeholder}')} "
                    f"resolves to multiple values for lang '{lang}': {', '.join(distinct_values)}"
                ),
                target=target,
                path=recipe_path,
                lang=lang,
            )
        )
    return issues


def _required_row_key_issues(
    *,
    recipe: Any,
    target: Any,
    lang: str,
    recipe_path: Path,
    spec_rows: list[dict[str, str]],
    issue_cls: type[Any],
    missing_required_row_keys: Callable[..., list[str]],
) -> list[Any]:
    missing_row_keys = missing_required_row_keys(
        recipe,
        spec_rows=spec_rows,
        model=target.model,
        region=target.region,
        lang=lang,
        include_field_map=False,
    )
    if not missing_row_keys:
        return []

    return [
        _issue(
            issue_cls,
            code="RECIPE_MISSING_ROW_KEYS",
            message=(
                f"Recipe '{recipe.page_id}' is missing required Spec_Master rows for lang '{lang}': "
                f"{', '.join(missing_row_keys)}"
            ),
            target=target,
            path=recipe_path,
            lang=lang,
        )
    ]


def _required_row_key_ambiguity_issues(
    *,
    recipe: Any,
    target: Any,
    lang: str,
    recipe_path: Path,
    spec_rows: list[dict[str, str]],
    issue_cls: type[Any],
    collect_spec_value_matches_from_rows: Callable[..., list[Any]],
) -> list[Any]:
    issues: list[Any] = []
    for row_key in recipe.required_row_keys:
        value_matches = collect_spec_value_matches_from_rows(
            spec_rows,
            model=target.model,
            region=target.region,
            lang=lang,
            row_key=row_key,
        )
        distinct_values = sorted({match.value for match in value_matches if match.value.strip()})
        if len(distinct_values) <= 1:
            continue
        issues.append(
            _issue(
                issue_cls,
                code="AMBIGUOUS_REQUIRED_ROW_KEY",
                message=(
                    f"Recipe '{recipe.page_id}' required_row_key '{row_key}' resolves to multiple values "
                    f"for lang '{lang}': {', '.join(distinct_values)}"
                ),
                target=target,
                path=recipe_path,
                lang=lang,
            )
        )
    return issues


def _binding_issues(
    *,
    recipe: Any,
    target: Any,
    lang: str,
    recipe_path: Path,
    runtime: GeneratedPageRuntime,
    issue_cls: type[Any],
    missing_required_row_keys: Callable[..., list[str]],
    format_field_binding: Callable[..., str],
    resolve_spec_value_from_rows: Callable[..., Any | None],
    collect_matching_spec_rows: Callable[..., list[dict[str, str]]],
    pick_spec_value: Callable[[dict[str, str], str], str],
    collect_spec_value_matches_from_rows: Callable[..., list[Any]],
) -> list[Any]:
    issues: list[Any] = []
    issues.extend(
        _required_row_key_issues(
            recipe=recipe,
            target=target,
            lang=lang,
            recipe_path=recipe_path,
            spec_rows=runtime.spec_rows,
            issue_cls=issue_cls,
            missing_required_row_keys=missing_required_row_keys,
        )
    )
    issues.extend(
        _field_map_missing_row_issues(
            recipe=recipe,
            target=target,
            lang=lang,
            recipe_path=recipe_path,
            spec_rows=runtime.spec_rows,
            issue_cls=issue_cls,
            format_field_binding=format_field_binding,
            resolve_spec_value_from_rows=resolve_spec_value_from_rows,
        )
    )
    issues.extend(
        _field_map_ambiguity_issues(
            recipe=recipe,
            target=target,
            lang=lang,
            recipe_path=recipe_path,
            spec_rows=runtime.spec_rows,
            issue_cls=issue_cls,
            format_field_binding=format_field_binding,
            collect_matching_spec_rows=collect_matching_spec_rows,
            pick_spec_value=pick_spec_value,
        )
    )
    issues.extend(
        _required_row_key_ambiguity_issues(
            recipe=recipe,
            target=target,
            lang=lang,
            recipe_path=recipe_path,
            spec_rows=runtime.spec_rows,
            issue_cls=issue_cls,
            collect_spec_value_matches_from_rows=collect_spec_value_matches_from_rows,
        )
    )
    return issues


def _snippet_issues(
    *,
    docs_dir: Path,
    recipe: Any,
    target: Any,
    lang: str,
    recipe_path: Path,
    runtime: GeneratedPageRuntime,
    issue_cls: type[Any],
    resolve_recipe_substitutions: Callable[..., dict[str, str]],
    select_snippet_entry: Callable[..., Any],
    resolve_snippet_file_path: Callable[..., Path],
    used_snippet_ids: set[str],
) -> tuple[list[Any], list[str], dict[str, str]]:
    issues: list[Any] = []
    combined_placeholder_sources: list[str] = []
    substitutions = resolve_recipe_substitutions(
        recipe,
        spec_rows=runtime.spec_rows,
        model=target.model,
        region=target.region,
        lang=lang,
        page_copy_csv=runtime.page_copy_csv,
    )
    available_placeholders = {**runtime.base_substitutions, **substitutions}
    if runtime.registry_error is not None:
        return (
            [
                _issue(
                    issue_cls,
                    code="MISSING_SNIPPET_REGISTRY",
                    message=str(runtime.registry_error),
                    target=target,
                    path=runtime.registry_path,
                    lang=lang,
                )
            ],
            combined_placeholder_sources,
            available_placeholders,
        )

    for slot_name, snippet_id in recipe.snippet_slots.items():
        used_snippet_ids.add(snippet_id)
        try:
            entry = select_snippet_entry(
                runtime.registry_entries,
                snippet_id=snippet_id,
                lang=lang,
                region=target.region,
            )
        except RuntimeError as exc:
            issues.append(
                _issue(
                    issue_cls,
                    code="MISSING_SNIPPET",
                    message=f"Recipe '{recipe.page_id}' slot '{slot_name}': {exc}",
                    target=target,
                    path=recipe_path,
                    lang=lang,
                )
            )
            continue

        snippet_path = resolve_snippet_file_path(
            entry,
            docs_dir=docs_dir,
            registry_path=runtime.registry_path,
            model=target.model,
            region=target.region,
        )
        if not snippet_path.exists():
            issues.append(
                _issue(
                    issue_cls,
                    code="MISSING_SNIPPET_FILE",
                    message=f"Snippet '{snippet_id}' file not found: {snippet_path}",
                    target=target,
                    path=snippet_path,
                    lang=lang,
                )
            )
            continue

        combined_placeholder_sources.append(snippet_path.read_text(encoding="utf-8"))
        missing_placeholders = [
            placeholder
            for placeholder in entry.required_placeholders
            if not (available_placeholders.get(placeholder) or "").strip()
        ]
        if missing_placeholders:
            issues.append(
                _issue(
                    issue_cls,
                    code="SNIPPET_MISSING_PLACEHOLDERS",
                    message=(
                        f"Snippet '{snippet_id}' is missing required placeholders for lang '{lang}': "
                        f"{', '.join(missing_placeholders)}"
                    ),
                    target=target,
                    path=snippet_path,
                    lang=lang,
                )
            )

    return issues, combined_placeholder_sources, available_placeholders


def _placeholder_consistency_issues(
    *,
    recipe: Any,
    target: Any,
    lang: str,
    recipe_path: Path,
    template_path: Path,
    template_text: str,
    available_placeholders: dict[str, str],
    snippet_sources: list[str],
    issue_cls: type[Any],
    collect_placeholder_tokens: Callable[[str], set[str]],
    field_binding_is_used: Callable[[str, set[str]], bool],
) -> list[Any]:
    issues: list[Any] = []
    used_placeholders: set[str] = set()
    for text in [template_text, *snippet_sources]:
        used_placeholders.update(collect_placeholder_tokens(text))

    unused_field_map = sorted(
        placeholder for placeholder in recipe.field_map if not field_binding_is_used(placeholder, used_placeholders)
    )
    if unused_field_map:
        issues.append(
            _issue(
                issue_cls,
                code="UNUSED_FIELD_MAP_PLACEHOLDER",
                message=(
                    f"Recipe '{recipe.page_id}' declares field_map placeholders not used by the template/snippets "
                    f"for lang '{lang}': {', '.join(unused_field_map)}"
                ),
                target=target,
                path=recipe_path,
                lang=lang,
            )
        )

    unknown_placeholders = sorted(
        placeholder for placeholder in used_placeholders if placeholder not in available_placeholders
    )
    if unknown_placeholders:
        issues.append(
            _issue(
                issue_cls,
                code="UNKNOWN_RECIPE_PLACEHOLDERS",
                message=(
                    f"Recipe '{recipe.page_id}' uses placeholders that are not supplied by Spec_Master, "
                    f"field_map, or conf_base for lang '{lang}': {', '.join(unknown_placeholders)}"
                ),
                target=target,
                path=template_path,
                lang=lang,
            )
        )

    return issues


def _contract_reference_issues(
    *,
    recipe: Any,
    target: Any,
    recipe_path: Path,
    runtime: GeneratedPageRuntime,
    issue_cls: type[Any],
) -> list[Any]:
    missing_contracts = [
        contract_ref
        for contract_ref in recipe.contracts
        if contract_ref not in runtime.contract_ids and contract_ref not in runtime.contract_file_names
    ]
    if not missing_contracts:
        return []

    return [
        _issue(
            issue_cls,
            code="RECIPE_MISSING_CONTRACTS",
            message=f"Recipe '{recipe.page_id}' references missing contracts: {', '.join(missing_contracts)}",
            target=target,
            path=recipe_path,
        )
    ]


def _orphan_snippet_issues(
    *,
    runtime: GeneratedPageRuntime,
    used_snippet_ids: set[str],
    issue_cls: type[Any],
    target: Any,
    collect_registry_snippet_ids: Callable[[list[Any]], set[str]],
) -> list[Any]:
    if runtime.registry_error is not None or not runtime.registry_entries:
        return []

    issues: list[Any] = []
    orphan_snippet_ids = sorted(collect_registry_snippet_ids(runtime.registry_entries) - used_snippet_ids)
    for snippet_id in orphan_snippet_ids:
        issues.append(
            _issue(
                issue_cls,
                code="ORPHAN_SNIPPET",
                message=f"Snippet '{snippet_id}' is defined in the registry but not used by any draft recipe",
                target=target,
                path=runtime.registry_path,
            )
        )
    return issues


def collect_generated_page_issues(
    cfg: dict,
    *,
    docs_dir: Path,
    repo_root: Path,
    target: Any,
    langs: list[str],
    data_root: str | None,
    issue_cls: type[Any],
    generated_page_cls: type[Any],
    resolve_page_manifest_path: Callable[..., Path | None],
    resolve_config_pages_or_raise: Callable[..., Any],
    resolve_spec_master_csv_path: Callable[..., Path],
    read_spec_master_rows: Callable[[Path], list[dict[str, str]]],
    resolve_snippet_registry_path: Callable[[Path], Path],
    load_snippet_registry: Callable[[Path], list[Any]],
    load_page_contracts: Callable[[Path], list[Any]],
    resolve_contracts_dir: Callable[..., Path],
    load_rst_substitutions: Callable[[Path], dict[str, str]],
    resolve_config_path: Callable[..., Path],
    load_draft_recipe: Callable[[Path], Any],
    missing_required_row_keys: Callable[..., list[str]],
    format_field_binding: Callable[..., str],
    resolve_spec_value_from_rows: Callable[..., Any | None],
    collect_matching_spec_rows: Callable[..., list[dict[str, str]]],
    pick_spec_value: Callable[[dict[str, str], str], str],
    collect_spec_value_matches_from_rows: Callable[..., list[Any]],
    resolve_recipe_substitutions: Callable[..., dict[str, str]],
    select_snippet_entry: Callable[..., Any],
    resolve_snippet_file_path: Callable[..., Path],
    collect_placeholder_tokens: Callable[[str], set[str]],
    field_binding_is_used: Callable[[str, set[str]], bool],
    collect_registry_snippet_ids: Callable[[list[Any]], set[str]],
) -> list[Any]:
    generated_pages = _resolve_generated_pages(
        cfg,
        repo_root=repo_root,
        target=target,
        langs=langs,
        generated_page_cls=generated_page_cls,
        resolve_page_manifest_path=resolve_page_manifest_path,
        resolve_config_pages_or_raise=resolve_config_pages_or_raise,
    )
    if not generated_pages:
        return []

    runtime = _load_generated_runtime(
        cfg,
        docs_dir=docs_dir,
        data_root=data_root,
        resolve_spec_master_csv_path=resolve_spec_master_csv_path,
        read_spec_master_rows=read_spec_master_rows,
        resolve_snippet_registry_path=resolve_snippet_registry_path,
        load_snippet_registry=load_snippet_registry,
        load_page_contracts=load_page_contracts,
        resolve_contracts_dir=resolve_contracts_dir,
        load_rst_substitutions=load_rst_substitutions,
    )

    issues: list[Any] = []
    used_snippet_ids: set[str] = set()
    for page in generated_pages:
        recipe, template_text, recipe_path, template_path, page_issues = _load_page_artifacts(
            docs_dir=docs_dir,
            page=page,
            target=target,
            issue_cls=issue_cls,
            resolve_config_path=resolve_config_path,
            load_draft_recipe=load_draft_recipe,
        )
        issues.extend(page_issues)
        if recipe is None or template_text is None:
            continue

        issues.extend(
            _template_slot_issues(
                page=page,
                recipe=recipe,
                target=target,
                recipe_path=recipe_path,
                template_text=template_text,
                issue_cls=issue_cls,
            )
        )

        page_langs = list(page.langs) or langs
        for lang in page_langs:
            issues.extend(
                _binding_issues(
                    recipe=recipe,
                    target=target,
                    lang=lang,
                    recipe_path=recipe_path,
                    runtime=runtime,
                    issue_cls=issue_cls,
                    missing_required_row_keys=missing_required_row_keys,
                    format_field_binding=format_field_binding,
                    resolve_spec_value_from_rows=resolve_spec_value_from_rows,
                    collect_matching_spec_rows=collect_matching_spec_rows,
                    pick_spec_value=pick_spec_value,
                    collect_spec_value_matches_from_rows=collect_spec_value_matches_from_rows,
                )
            )

            snippet_issues, snippet_sources, available_placeholders = _snippet_issues(
                docs_dir=docs_dir,
                recipe=recipe,
                target=target,
                lang=lang,
                recipe_path=recipe_path,
                runtime=runtime,
                issue_cls=issue_cls,
                resolve_recipe_substitutions=resolve_recipe_substitutions,
                select_snippet_entry=select_snippet_entry,
                resolve_snippet_file_path=resolve_snippet_file_path,
                used_snippet_ids=used_snippet_ids,
            )
            issues.extend(snippet_issues)
            if runtime.registry_error is None:
                issues.extend(
                    _placeholder_consistency_issues(
                        recipe=recipe,
                        target=target,
                        lang=lang,
                        recipe_path=recipe_path,
                        template_path=template_path,
                        template_text=template_text,
                        available_placeholders=available_placeholders,
                        snippet_sources=snippet_sources,
                        issue_cls=issue_cls,
                        collect_placeholder_tokens=collect_placeholder_tokens,
                        field_binding_is_used=field_binding_is_used,
                    )
                )

        issues.extend(
            _contract_reference_issues(
                recipe=recipe,
                target=target,
                recipe_path=recipe_path,
                runtime=runtime,
                issue_cls=issue_cls,
            )
        )

    issues.extend(
        _orphan_snippet_issues(
            runtime=runtime,
            used_snippet_ids=used_snippet_ids,
            issue_cls=issue_cls,
            target=target,
            collect_registry_snippet_ids=collect_registry_snippet_ids,
        )
    )
    return issues
