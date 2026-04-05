from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


def resolve_contract_asset_path(
    raw_value: str,
    *,
    docs_dir: Path,
    repo_root: Path,
    model: str | None,
    region: str | None,
    lang: str | None,
    render_build_template: Callable[..., str],
) -> Path:
    rendered = render_build_template(
        raw_value,
        model=model,
        region=region,
        lang=lang,
    )
    candidate = Path(rendered)
    if candidate.is_absolute():
        return candidate

    docs_candidate = docs_dir / candidate
    if docs_candidate.exists():
        return docs_candidate
    return repo_root / candidate


def contract_asset_exists(
    raw_value: str,
    *,
    docs_dir: Path,
    repo_root: Path,
    model: str | None,
    region: str | None,
    lang: str | None,
    resolve_contract_asset_path: Callable[..., Path],
) -> bool:
    return resolve_contract_asset_path(
        raw_value,
        docs_dir=docs_dir,
        repo_root=repo_root,
        model=model,
        region=region,
        lang=lang,
    ).exists()


def collect_page_contract_issues(
    cfg: dict,
    *,
    docs_dir: Path,
    repo_root: Path,
    target: Any,
    langs: list[str],
    data_root: str | None,
    issue_cls: type[Any],
    rst_include_page_cls: type[Any],
    generated_page_cls: type[Any],
    resolve_contracts_dir: Callable[..., Path],
    load_page_contracts: Callable[[Path], list[Any]],
    resolve_config_pages_or_raise: Callable[..., Any],
    page_source_path: Callable[..., Path],
    find_contract_for_source: Callable[..., Any | None],
    contract_applies_to: Callable[..., bool],
    required_placeholders_for_lang: Callable[..., tuple[str, ...]],
    required_spec_keys_for_lang: Callable[..., tuple[str, ...]],
    required_page_values_for_lang: Callable[..., tuple[Any, ...]],
    required_assets_for_lang: Callable[..., tuple[str, ...]],
    resolve_template_substitutions_from_spec_master: Callable[..., dict[str, str]],
    resolve_spec_master_csv_path: Callable[..., Path],
    read_spec_master_rows: Callable[[Path], list[dict[str, str]]],
    resolve_spec_value_from_rows: Callable[..., Any | None],
    describe_page_value_selector: Callable[[Any], str],
    contract_asset_exists: Callable[..., bool],
) -> list[Any]:
    contracts = load_page_contracts(resolve_contracts_dir(docs_dir=docs_dir))
    if not contracts:
        return []

    pages = resolve_config_pages_or_raise(
        cfg,
        default_languages=langs,
        root=repo_root,
        model=target.model,
        region=target.region,
        error_prefix="config.pages",
    ).pages
    spec_master_csv = resolve_spec_master_csv_path(cfg, data_root=data_root)
    spec_rows = read_spec_master_rows(spec_master_csv)
    substitutions_by_lang: dict[str, dict[str, str]] = {}
    issues: list[Any] = []

    for page in pages:
        if not isinstance(page, (rst_include_page_cls, generated_page_cls)):
            continue
        source_path = page_source_path(
            docs_dir=docs_dir,
            page=page,
            model=target.model,
            region=target.region,
        )
        try:
            source_rel = source_path.relative_to(docs_dir).as_posix()
        except ValueError:
            source_rel = source_path.as_posix()

        contract = find_contract_for_source(source_rel, contracts)
        if contract is None:
            continue

        page_langs = [page.lang] if isinstance(page, rst_include_page_cls) and page.lang else list(page.langs) if isinstance(page, generated_page_cls) else langs
        for lang in page_langs:
            if not contract_applies_to(contract, lang=lang, model=target.model, region=target.region):
                continue
            required = required_placeholders_for_lang(contract, lang)
            substitutions = substitutions_by_lang.get(lang)
            if substitutions is None:
                substitutions = resolve_template_substitutions_from_spec_master(
                    spec_master_csv,
                    model=target.model,
                    region=target.region,
                    lang=lang,
                )
                substitutions_by_lang[lang] = substitutions

            missing_placeholders = [key for key in required if not (substitutions.get(key) or "").strip()]
            if missing_placeholders:
                issues.append(
                    issue_cls(
                        code="CONTRACT_MISSING_PLACEHOLDERS",
                        message=(
                            f"Page contract '{contract.page_id}' is missing required placeholders "
                            f"for lang '{lang}': {', '.join(missing_placeholders)}"
                        ),
                        model=target.model,
                        region=target.region,
                        path=source_path,
                        lang=lang,
                    )
                )
            missing_spec_keys = [
                row_key
                for row_key in required_spec_keys_for_lang(contract, lang)
                if resolve_spec_value_from_rows(
                    spec_rows,
                    model=target.model,
                    region=target.region,
                    lang=lang,
                    row_key=row_key,
                    pages=None,
                )
                is None
            ]
            if missing_spec_keys:
                issues.append(
                    issue_cls(
                        code="CONTRACT_MISSING_SPEC_KEYS",
                        message=(
                            f"Page contract '{contract.page_id}' is missing required spec row keys "
                            f"for lang '{lang}': {', '.join(missing_spec_keys)}"
                        ),
                        model=target.model,
                        region=target.region,
                        path=source_path,
                        lang=lang,
                    )
                )
            missing_page_values = [
                describe_page_value_selector(selector)
                for selector in required_page_values_for_lang(contract, lang)
                if resolve_spec_value_from_rows(
                    spec_rows,
                    model=target.model,
                    region=target.region,
                    lang=lang,
                    row_key=selector.row_key,
                    pages=selector.pages or None,
                    line_order=selector.line_order,
                    usage_type=selector.usage_type,
                    placement_key=selector.placement_key,
                    value_role=selector.value_role,
                    variant_key=selector.variant_key,
                )
                is None
            ]
            if missing_page_values:
                issues.append(
                    issue_cls(
                        code="CONTRACT_MISSING_PAGE_VALUES",
                        message=(
                            f"Page contract '{contract.page_id}' is missing required page-value rows "
                            f"for lang '{lang}': {', '.join(missing_page_values)}"
                        ),
                        model=target.model,
                        region=target.region,
                        path=source_path,
                        lang=lang,
                    )
                )
            missing_assets = [
                asset_path
                for asset_path in required_assets_for_lang(contract, lang)
                if not contract_asset_exists(
                    asset_path,
                    docs_dir=docs_dir,
                    repo_root=repo_root,
                    model=target.model,
                    region=target.region,
                    lang=lang,
                )
            ]
            if missing_assets:
                issues.append(
                    issue_cls(
                        code="CONTRACT_MISSING_ASSETS",
                        message=(
                            f"Page contract '{contract.page_id}' is missing required assets "
                            f"for lang '{lang}': {', '.join(missing_assets)}"
                        ),
                        model=target.model,
                        region=target.region,
                        path=source_path,
                        lang=lang,
                    )
                )
    return issues
