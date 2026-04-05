from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

SNIPPET_SLOT_RE = re.compile(r"\{\{snippet:([a-zA-Z0-9_.-]+)\}\}")


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
    generated_pages = [page for page in pages if isinstance(page, generated_page_cls)]
    if not generated_pages:
        return []

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
    contract_ids = {contract.page_id for contract in contracts}
    contract_file_names = {f"{contract.page_id}.yaml" for contract in contracts}
    base_substitutions = load_rst_substitutions(docs_dir / "conf_base.py")
    issues: list[Any] = []
    used_snippet_ids: set[str] = set()

    for page in generated_pages:
        recipe_path = resolve_config_path(docs_dir, page.recipe, target.model, target.region)
        template_path = resolve_config_path(docs_dir, page.template, target.model, target.region)
        if not recipe_path.exists():
            issues.append(
                issue_cls(
                    code="MISSING_RECIPE",
                    message=f"Generated page recipe not found: {recipe_path}",
                    model=target.model,
                    region=target.region,
                    path=recipe_path,
                )
            )
            continue
        if not template_path.exists():
            issues.append(
                issue_cls(
                    code="MISSING_GENERATED_TEMPLATE",
                    message=f"Generated page template not found: {template_path}",
                    model=target.model,
                    region=target.region,
                    path=template_path,
                )
            )
            continue

        try:
            recipe = load_draft_recipe(recipe_path)
        except RuntimeError as exc:
            issues.append(
                issue_cls(
                    code="INVALID_RECIPE",
                    message=str(exc),
                    model=target.model,
                    region=target.region,
                    path=recipe_path,
                )
            )
            continue

        if recipe.page_id != page.page:
            issues.append(
                issue_cls(
                    code="RECIPE_PAGE_ID_MISMATCH",
                    message=(
                        f"Generated page '{page.page}' references recipe page_id '{recipe.page_id}'. "
                        "These values should match."
                    ),
                    model=target.model,
                    region=target.region,
                    path=recipe_path,
                )
            )

        template_text = template_path.read_text(encoding="utf-8")
        template_slots = {match.group(1).strip() for match in SNIPPET_SLOT_RE.finditer(template_text) if match.group(1).strip()}
        missing_slots = sorted(template_slots - set(recipe.snippet_slots))
        if missing_slots:
            issues.append(
                issue_cls(
                    code="UNBOUND_SNIPPET_SLOT",
                    message=f"Recipe '{recipe.page_id}' is missing snippet_slots for: {', '.join(missing_slots)}",
                    model=target.model,
                    region=target.region,
                    path=recipe_path,
                )
            )

        unused_slots = sorted(set(recipe.snippet_slots) - template_slots)
        if unused_slots:
            issues.append(
                issue_cls(
                    code="UNUSED_SNIPPET_SLOT",
                    message=f"Recipe '{recipe.page_id}' declares unused snippet_slots: {', '.join(unused_slots)}",
                    model=target.model,
                    region=target.region,
                    path=recipe_path,
                )
            )

        page_langs = list(page.langs) or langs
        for lang in page_langs:
            combined_placeholder_sources = [template_text]
            missing_row_keys = missing_required_row_keys(
                recipe,
                spec_rows=spec_rows,
                model=target.model,
                region=target.region,
                lang=lang,
                include_field_map=False,
            )
            if missing_row_keys:
                issues.append(
                    issue_cls(
                        code="RECIPE_MISSING_ROW_KEYS",
                        message=(
                            f"Recipe '{recipe.page_id}' is missing required Spec_Master rows for lang '{lang}': "
                            f"{', '.join(missing_row_keys)}"
                        ),
                        model=target.model,
                        region=target.region,
                        path=recipe_path,
                        lang=lang,
                    )
                )

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
            ]
            if field_binding_misses:
                issues.append(
                    issue_cls(
                        code="RECIPE_MISSING_FIELD_MAP_ROWS",
                        message=(
                            f"Recipe '{recipe.page_id}' is missing field_map rows for lang '{lang}': "
                            f"{', '.join(field_binding_misses)}"
                        ),
                        model=target.model,
                        region=target.region,
                        path=recipe_path,
                        lang=lang,
                    )
                )

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
                if len(distinct_values) > 1:
                    issues.append(
                        issue_cls(
                            code="AMBIGUOUS_FIELD_MAP_ROWS",
                            message=(
                                f"Recipe '{recipe.page_id}' {format_field_binding(binding, owner=f'field_map.{placeholder}')} resolves to multiple values "
                                f"for lang '{lang}': {', '.join(distinct_values)}"
                            ),
                            model=target.model,
                            region=target.region,
                            path=recipe_path,
                            lang=lang,
                        )
                    )

            for row_key in recipe.required_row_keys:
                value_matches = collect_spec_value_matches_from_rows(
                    spec_rows,
                    model=target.model,
                    region=target.region,
                    lang=lang,
                    row_key=row_key,
                )
                distinct_values = sorted({match.value for match in value_matches if match.value.strip()})
                if len(distinct_values) > 1:
                    issues.append(
                        issue_cls(
                            code="AMBIGUOUS_REQUIRED_ROW_KEY",
                            message=(
                                f"Recipe '{recipe.page_id}' required_row_key '{row_key}' resolves to multiple values "
                                f"for lang '{lang}': {', '.join(distinct_values)}"
                            ),
                            model=target.model,
                            region=target.region,
                            path=recipe_path,
                            lang=lang,
                        )
                    )

            substitutions = resolve_recipe_substitutions(
                recipe,
                spec_rows=spec_rows,
                model=target.model,
                region=target.region,
                lang=lang,
            )
            available_placeholders = {**base_substitutions, **substitutions}
            if registry_error is not None:
                issues.append(
                    issue_cls(
                        code="MISSING_SNIPPET_REGISTRY",
                        message=str(registry_error),
                        model=target.model,
                        region=target.region,
                        path=registry_path,
                        lang=lang,
                    )
                )
                continue

            for slot_name, snippet_id in recipe.snippet_slots.items():
                used_snippet_ids.add(snippet_id)
                try:
                    entry = select_snippet_entry(
                        registry_entries,
                        snippet_id=snippet_id,
                        lang=lang,
                        region=target.region,
                    )
                except RuntimeError as exc:
                    issues.append(
                        issue_cls(
                            code="MISSING_SNIPPET",
                            message=f"Recipe '{recipe.page_id}' slot '{slot_name}': {exc}",
                            model=target.model,
                            region=target.region,
                            path=recipe_path,
                            lang=lang,
                        )
                    )
                    continue

                snippet_path = resolve_snippet_file_path(
                    entry,
                    docs_dir=docs_dir,
                    registry_path=registry_path,
                    model=target.model,
                    region=target.region,
                )
                if not snippet_path.exists():
                    issues.append(
                        issue_cls(
                            code="MISSING_SNIPPET_FILE",
                            message=f"Snippet '{snippet_id}' file not found: {snippet_path}",
                            model=target.model,
                            region=target.region,
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
                        issue_cls(
                            code="SNIPPET_MISSING_PLACEHOLDERS",
                            message=(
                                f"Snippet '{snippet_id}' is missing required placeholders for lang '{lang}': "
                                f"{', '.join(missing_placeholders)}"
                            ),
                            model=target.model,
                            region=target.region,
                            path=snippet_path,
                            lang=lang,
                        )
                    )

            used_placeholders: set[str] = set()
            for text in combined_placeholder_sources:
                used_placeholders.update(collect_placeholder_tokens(text))

            unused_field_map = sorted(
                placeholder
                for placeholder in recipe.field_map
                if not field_binding_is_used(placeholder, used_placeholders)
            )
            if unused_field_map:
                issues.append(
                    issue_cls(
                        code="UNUSED_FIELD_MAP_PLACEHOLDER",
                        message=(
                            f"Recipe '{recipe.page_id}' declares field_map placeholders not used by the template/snippets "
                            f"for lang '{lang}': {', '.join(unused_field_map)}"
                        ),
                        model=target.model,
                        region=target.region,
                        path=recipe_path,
                        lang=lang,
                    )
                )

            unknown_placeholders = sorted(
                placeholder
                for placeholder in used_placeholders
                if placeholder not in available_placeholders
            )
            if unknown_placeholders:
                issues.append(
                    issue_cls(
                        code="UNKNOWN_RECIPE_PLACEHOLDERS",
                        message=(
                            f"Recipe '{recipe.page_id}' uses placeholders that are not supplied by Spec_Master, "
                            f"field_map, or conf_base for lang '{lang}': {', '.join(unknown_placeholders)}"
                        ),
                        model=target.model,
                        region=target.region,
                        path=template_path,
                        lang=lang,
                    )
                )

        missing_contracts = [
            contract_ref
            for contract_ref in recipe.contracts
            if contract_ref not in contract_ids and contract_ref not in contract_file_names
        ]
        if missing_contracts:
            issues.append(
                issue_cls(
                    code="RECIPE_MISSING_CONTRACTS",
                    message=(
                        f"Recipe '{recipe.page_id}' references missing contracts: "
                        f"{', '.join(missing_contracts)}"
                    ),
                    model=target.model,
                    region=target.region,
                    path=recipe_path,
                )
            )

    if registry_error is None and registry_entries:
        orphan_snippet_ids = sorted(collect_registry_snippet_ids(registry_entries) - used_snippet_ids)
        for snippet_id in orphan_snippet_ids:
            issues.append(
                issue_cls(
                    code="ORPHAN_SNIPPET",
                    message=f"Snippet '{snippet_id}' is defined in the registry but not used by any draft recipe",
                    model=target.model,
                    region=target.region,
                    path=registry_path,
                )
            )

    return issues
