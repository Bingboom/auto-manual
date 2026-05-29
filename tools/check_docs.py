#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.config_pages import GeneratedPage, RstIncludePage  # noqa: E402
from tools.data_snapshot import resolve_data_snapshot_paths  # noqa: E402
from tools.utils.path_utils import contracts_dir_of  # noqa: E402
from tools.build_docs import (  # noqa: E402
    BuildTarget,
    load_config,
    render_build_template,
    resolve_build_targets,
    resolve_product_name_for_build,
)
from tools.check_docs_contracts import (  # noqa: E402
    collect_page_contract_issues as _collect_page_contract_issues_impl,
    contract_asset_exists as _contract_asset_exists_impl,
    resolve_contract_asset_path as _resolve_contract_asset_path_impl,
)
from tools.check_docs_cli import parse_args as _parse_args_impl  # noqa: E402
from tools.check_docs_bundle import (  # noqa: E402
    collect_bundle_issues as _collect_bundle_issues_impl,
    collect_placeholder_issues as _collect_placeholder_issues_impl,
    collect_reference_issues as _collect_reference_issues_impl,
    collect_placeholder_tokens as _collect_placeholder_tokens_impl,
    field_binding_is_used as _field_binding_is_used_impl,
    is_external_reference as _is_external_reference_impl,
    resolve_local_reference as _resolve_local_reference_impl,
)
from tools.check_docs_entry import run_check_entry as _run_check_entry_impl  # noqa: E402
from tools.check_docs_generated import collect_generated_page_issues as _collect_generated_page_issues_impl  # noqa: E402
from tools.check_docs_identity import (  # noqa: E402
    collect_identity_drift_issues as _collect_identity_drift_issues_impl,
    collect_target_identity_issues as _collect_target_identity_issues_impl,
)
from tools.check_docs_duplicate_text import (  # noqa: E402
    collect_duplicate_render_text_issues as _collect_duplicate_render_text_issues_impl,
)
from tools.check_docs_runtime import (  # noqa: E402
    build_langs as _build_langs_impl,
    checks_cfg as _checks_cfg_impl,
    collect_check_issues as _collect_check_issues_impl,
    repo_relative as _repo_relative_impl,
    resolve_docs_dir as _resolve_docs_dir_impl,
)
from tools.check_identity_drift import find_identity_drift_matches  # noqa: E402
from tools.draft_engine import (  # noqa: E402
    collect_registry_snippet_ids,
    format_field_binding,
    load_draft_recipe,
    load_snippet_registry,
    missing_required_row_keys,
    resolve_recipe_substitutions,
    resolve_snippet_file_path,
    resolve_snippet_registry_path,
    select_snippet_entry,
)
from tools.gen_index_bundle import bundle_dir_for_target  # noqa: E402
from tools.page_manifest import resolve_config_pages_or_raise, resolve_page_manifest_path  # noqa: E402
from tools.page_contracts import (  # noqa: E402
    contract_applies_to,
    describe_page_value_selector,
    find_contract_for_source,
    load_page_contracts,
    required_assets_for_lang,
    required_page_values_for_lang,
    required_placeholders_for_lang,
    required_spec_keys_for_lang,
)
from tools.utils.spec_master import (  # noqa: E402
    collect_matching_spec_rows,
    collect_spec_value_matches_from_rows,
    read_spec_master_rows,
    resolve_spec_value_from_rows,
    source_language_for_row,
    resolve_template_substitutions_from_spec_master,
)
from tools.word_bundle_common import load_rst_substitutions, resolve_config_path  # noqa: E402

@dataclass(frozen=True)
class CheckIssue:
    code: str
    message: str
    model: str | None
    region: str | None
    path: Path | None = None
    lang: str | None = None


def resolve_docs_dir(cfg: dict) -> Path:
    return _resolve_docs_dir_impl(cfg, repo_root=ROOT)


def _repo_relative(path: Path | None) -> str:
    return _repo_relative_impl(path, repo_root=ROOT)


def _build_langs(cfg: dict) -> list[str]:
    return _build_langs_impl(cfg)


def _checks_cfg(cfg: dict) -> dict:
    return _checks_cfg_impl(cfg)


def resolve_spec_master_csv_path(cfg: dict, *, data_root: str | None = None) -> Path:
    return resolve_data_snapshot_paths(
        cfg,
        repo_root=ROOT,
        data_root=data_root,
    ).spec_master_csv


def resolve_contracts_dir(*, docs_dir: Path) -> Path:
    return contracts_dir_of(docs_dir)


def _page_source_path(
    *,
    docs_dir: Path,
    page: RstIncludePage | GeneratedPage,
    model: str | None,
    region: str | None,
) -> Path:
    raw_path = page.file if isinstance(page, RstIncludePage) else page.template
    return resolve_config_path(docs_dir, raw_path, model, region)


def _is_external_reference(value: str) -> bool:
    return _is_external_reference_impl(value)


def _resolve_local_reference(
    raw_value: str,
    *,
    rst_path: Path,
    bundle_dir: Path,
    docs_dir: Path,
    repo_root: Path | None = None,
) -> Path | None:
    return _resolve_local_reference_impl(
        raw_value,
        rst_path=rst_path,
        bundle_dir=bundle_dir,
        docs_dir=docs_dir,
        repo_root=repo_root or ROOT,
    )


def _pick_spec_value(row: dict[str, str], lang: str) -> str:
    source_lang = source_language_for_row(row)
    raw_lang = (lang or "").strip()
    normalized_lang = raw_lang.casefold()
    normalized_source_lang = (source_lang or "").strip().casefold()
    if normalized_lang in {"br", "pt-br", "pt_br"}:
        normalized_lang = "pt-br"
    if normalized_source_lang in {"br", "pt-br", "pt_br"}:
        normalized_source_lang = "pt-br"
    lang_suffixes = [
        raw_lang,
        raw_lang.lower(),
        raw_lang.upper(),
        raw_lang.replace("-", "_"),
        raw_lang.lower().replace("-", "_"),
    ]
    if normalized_lang == "pt-br":
        lang_suffixes.extend(["br", "pt-BR", "pt-br", "pt_BR", "pt_br"])
    keys = (
        ("Value_source", "value_source", "Value", "Spec_Value")
        if normalized_lang == "en" or (normalized_source_lang and normalized_lang == normalized_source_lang)
        else (
            *(f"Value_{suffix}" for suffix in dict.fromkeys(suffix for suffix in lang_suffixes if suffix)),
            "Value_source",
            "value_source",
            "Value",
            "Spec_Value",
        )
    )
    for key in keys:
        value = (row.get(key) or "").strip()
        if value:
            return value
    return ""


def _collect_placeholder_tokens(text: str) -> set[str]:
    return _collect_placeholder_tokens_impl(text)


def _field_binding_is_used(placeholder: str, used_placeholders: set[str]) -> bool:
    return _field_binding_is_used_impl(placeholder, used_placeholders)


def collect_placeholder_issues(
    *,
    rst_path: Path,
    model: str | None,
    region: str | None,
) -> list[CheckIssue]:
    return _collect_placeholder_issues_impl(
        rst_path=rst_path,
        model=model,
        region=region,
        issue_cls=CheckIssue,
    )


def collect_reference_issues(
    *,
    rst_path: Path,
    bundle_dir: Path,
    docs_dir: Path,
    repo_root: Path | None = None,
    model: str | None,
    region: str | None,
) -> list[CheckIssue]:
    return _collect_reference_issues_impl(
        rst_path=rst_path,
        bundle_dir=bundle_dir,
        docs_dir=docs_dir,
        repo_root=repo_root or ROOT,
        model=model,
        region=region,
        issue_cls=CheckIssue,
        resolve_local_reference=_resolve_local_reference,
    )


def collect_target_identity_issues(
    cfg: dict,
    *,
    target: BuildTarget,
    langs: list[str],
    data_root: str | None = None,
) -> list[CheckIssue]:
    return _collect_target_identity_issues_impl(
        cfg,
        target=target,
        langs=langs,
        data_root=data_root,
        issue_cls=CheckIssue,
        resolve_spec_master_csv_path=resolve_spec_master_csv_path,
        resolve_product_name_for_build=resolve_product_name_for_build,
        resolve_template_substitutions_from_spec_master=resolve_template_substitutions_from_spec_master,
    )


def collect_bundle_issues(
    *,
    bundle_dir: Path,
    docs_dir: Path,
    model: str | None,
    region: str | None,
) -> list[CheckIssue]:
    return _collect_bundle_issues_impl(
        bundle_dir=bundle_dir,
        docs_dir=docs_dir,
        repo_root=ROOT,
        model=model,
        region=region,
        issue_cls=CheckIssue,
        collect_placeholder_issues=collect_placeholder_issues,
        collect_reference_issues=collect_reference_issues,
    )


def collect_duplicate_render_text_issues(
    *,
    docs_dir: Path,
    bundle_dir: Path,
    model: str | None,
    region: str | None,
) -> list[CheckIssue]:
    return _collect_duplicate_render_text_issues_impl(
        repo_root=ROOT,
        docs_dir=docs_dir,
        bundle_dir=bundle_dir,
        model=model,
        region=region,
        issue_cls=CheckIssue,
    )


def collect_identity_drift_issues(
    cfg: dict,
    *,
    bundle_dir: Path,
    target: BuildTarget,
    langs: list[str],
    data_root: str | None = None,
) -> list[CheckIssue]:
    return _collect_identity_drift_issues_impl(
        cfg,
        bundle_dir=bundle_dir,
        target=target,
        langs=langs,
        data_root=data_root,
        issue_cls=CheckIssue,
        resolve_spec_master_csv_path=resolve_spec_master_csv_path,
        checks_cfg=_checks_cfg,
        find_identity_drift_matches=find_identity_drift_matches,
    )


def collect_page_contract_issues(
    cfg: dict,
    *,
    docs_dir: Path,
    target: BuildTarget,
    langs: list[str],
    data_root: str | None = None,
) -> list[CheckIssue]:
    return _collect_page_contract_issues_impl(
        cfg,
        docs_dir=docs_dir,
        repo_root=ROOT,
        target=target,
        langs=langs,
        data_root=data_root,
        issue_cls=CheckIssue,
        rst_include_page_cls=RstIncludePage,
        generated_page_cls=GeneratedPage,
        resolve_contracts_dir=resolve_contracts_dir,
        load_page_contracts=load_page_contracts,
        resolve_config_pages_or_raise=resolve_config_pages_or_raise,
        page_source_path=_page_source_path,
        find_contract_for_source=find_contract_for_source,
        contract_applies_to=contract_applies_to,
        required_placeholders_for_lang=required_placeholders_for_lang,
        required_spec_keys_for_lang=required_spec_keys_for_lang,
        required_page_values_for_lang=required_page_values_for_lang,
        required_assets_for_lang=required_assets_for_lang,
        resolve_template_substitutions_from_spec_master=resolve_template_substitutions_from_spec_master,
        resolve_spec_master_csv_path=resolve_spec_master_csv_path,
        read_spec_master_rows=read_spec_master_rows,
        resolve_spec_value_from_rows=resolve_spec_value_from_rows,
        describe_page_value_selector=describe_page_value_selector,
        contract_asset_exists=_contract_asset_exists,
    )


def collect_generated_page_issues(
    cfg: dict,
    *,
    docs_dir: Path,
    target: BuildTarget,
    langs: list[str],
    data_root: str | None = None,
) -> list[CheckIssue]:
    return _collect_generated_page_issues_impl(
        cfg,
        docs_dir=docs_dir,
        repo_root=ROOT,
        target=target,
        langs=langs,
        data_root=data_root,
        issue_cls=CheckIssue,
        generated_page_cls=GeneratedPage,
        resolve_page_manifest_path=resolve_page_manifest_path,
        resolve_config_pages_or_raise=resolve_config_pages_or_raise,
        resolve_spec_master_csv_path=resolve_spec_master_csv_path,
        read_spec_master_rows=read_spec_master_rows,
        resolve_snippet_registry_path=resolve_snippet_registry_path,
        load_snippet_registry=load_snippet_registry,
        load_page_contracts=load_page_contracts,
        resolve_contracts_dir=resolve_contracts_dir,
        load_rst_substitutions=load_rst_substitutions,
        resolve_config_path=resolve_config_path,
        load_draft_recipe=load_draft_recipe,
        missing_required_row_keys=missing_required_row_keys,
        format_field_binding=format_field_binding,
        resolve_spec_value_from_rows=resolve_spec_value_from_rows,
        collect_matching_spec_rows=collect_matching_spec_rows,
        pick_spec_value=_pick_spec_value,
        collect_spec_value_matches_from_rows=collect_spec_value_matches_from_rows,
        resolve_recipe_substitutions=resolve_recipe_substitutions,
        select_snippet_entry=select_snippet_entry,
        resolve_snippet_file_path=resolve_snippet_file_path,
        collect_placeholder_tokens=_collect_placeholder_tokens,
        field_binding_is_used=_field_binding_is_used,
        collect_registry_snippet_ids=collect_registry_snippet_ids,
    )


def _resolve_contract_asset_path(
    raw_value: str,
    *,
    docs_dir: Path,
    repo_root: Path | None = None,
    model: str | None,
    region: str | None,
    lang: str | None,
) -> Path:
    return _resolve_contract_asset_path_impl(
        raw_value,
        docs_dir=docs_dir,
        repo_root=repo_root or ROOT,
        model=model,
        region=region,
        lang=lang,
        render_build_template=render_build_template,
    )


def _contract_asset_exists(
    raw_value: str,
    *,
    docs_dir: Path,
    repo_root: Path | None = None,
    model: str | None,
    region: str | None,
    lang: str | None,
) -> bool:
    return _contract_asset_exists_impl(
        raw_value,
        docs_dir=docs_dir,
        repo_root=repo_root or ROOT,
        model=model,
        region=region,
        lang=lang,
        resolve_contract_asset_path=_resolve_contract_asset_path,
    )


def collect_check_issues(
    *,
    cfg_path: Path,
    model: str | None,
    region: str | None,
    lang: str | None = None,
    all_targets: bool,
    data_root: str | None = None,
    docs_build_dir: Path | None = None,
) -> list[CheckIssue]:
    return _collect_check_issues_impl(
        cfg_path=cfg_path,
        model=model,
        region=region,
        lang=lang,
        all_targets=all_targets,
        data_root=data_root,
        docs_build_dir=docs_build_dir,
        issue_cls=CheckIssue,
        repo_root=ROOT,
        load_config=load_config,
        resolve_docs_dir=resolve_docs_dir,
        build_langs=_build_langs,
        resolve_page_manifest_path=resolve_page_manifest_path,
        resolve_build_targets=resolve_build_targets,
        bundle_dir_for_target=bundle_dir_for_target,
        collect_target_identity_issues=collect_target_identity_issues,
        collect_page_contract_issues=collect_page_contract_issues,
        collect_generated_page_issues=collect_generated_page_issues,
        collect_bundle_issues=collect_bundle_issues,
        collect_identity_drift_issues=collect_identity_drift_issues,
        collect_duplicate_render_text_issues=collect_duplicate_render_text_issues,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return _parse_args_impl(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    return _run_check_entry_impl(
        args,
        repo_root=ROOT,
        collect_check_issues=collect_check_issues,
        repo_relative=_repo_relative,
    )


if __name__ == "__main__":
    raise SystemExit(main())
