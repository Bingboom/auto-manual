#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.config_pages import GeneratedPage, RstIncludePage  # noqa: E402
from tools.build_docs import (  # noqa: E402
    BuildTarget,
    load_config,
    render_build_template,
    resolve_build_targets,
    resolve_product_name_for_build,
)
from tools.check_identity_drift import find_identity_drift_matches  # noqa: E402
from tools.draft_engine import (  # noqa: E402
    collect_registry_snippet_ids,
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
    find_contract_for_source,
    load_page_contracts,
    required_assets_for_lang,
    required_placeholders_for_lang,
    required_spec_keys_for_lang,
    required_tpl_keys_for_lang,
)
from tools.utils.spec_master import (  # noqa: E402
    collect_matching_spec_rows,
    collect_spec_value_matches_from_rows,
    read_spec_master_rows,
    resolve_spec_value_from_rows,
    resolve_template_substitutions_from_spec_master,
)
from tools.word_bundle_common import load_rst_substitutions, resolve_config_path  # noqa: E402

PLACEHOLDER_RE = re.compile(r"\|([A-Z0-9][A-Z0-9_]+)\|")
INCLUDE_RE = re.compile(r"^\s*\.\.\s+include::\s+(\S+)\s*$")
ASSET_RE = re.compile(r"^\s*(?:[-*]\s+)?(?:-\s+)?\.\.\s+(?:image|figure)::\s+(\S+)\s*$")
HTML_SRC_RE = re.compile(r'\bsrc="([^"]+)"', re.IGNORECASE)
SNIPPET_SLOT_RE = re.compile(r"\{\{snippet:([a-zA-Z0-9_.-]+)\}\}")


@dataclass(frozen=True)
class CheckIssue:
    code: str
    message: str
    model: str | None
    region: str | None
    path: Path | None = None
    lang: str | None = None


def resolve_docs_dir(cfg: dict) -> Path:
    paths_cfg_raw = cfg.get("paths", {})
    paths_cfg = paths_cfg_raw if isinstance(paths_cfg_raw, dict) else {}
    raw = paths_cfg.get("docs_dir")
    if isinstance(raw, str) and raw.strip():
        path = Path(raw.strip())
        return path if path.is_absolute() else (ROOT / path)
    return ROOT / "docs"


def _repo_relative(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _build_langs(cfg: dict) -> list[str]:
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    langs = build_cfg.get("languages", ["en"])
    return [str(item).strip() for item in langs if str(item).strip()] or ["en"]


def _checks_cfg(cfg: dict) -> dict:
    checks_cfg_raw = cfg.get("checks", {})
    return checks_cfg_raw if isinstance(checks_cfg_raw, dict) else {}


def resolve_spec_master_csv_path(cfg: dict) -> Path:
    paths_cfg_raw = cfg.get("paths", {})
    paths_cfg = paths_cfg_raw if isinstance(paths_cfg_raw, dict) else {}
    raw = paths_cfg.get("spec_master_csv")
    if isinstance(raw, str) and raw.strip():
        path = Path(raw.strip())
        return path if path.is_absolute() else (ROOT / path)
    return ROOT / "data" / "phase1" / "Spec_Master.csv"


def resolve_contracts_dir(*, docs_dir: Path) -> Path:
    return docs_dir / "templates" / "contracts"


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
    token = value.strip()
    if not token:
        return True
    lowered = token.lower()
    return lowered.startswith(("http://", "https://", "data:", "file://", "mailto:", "#"))


def _resolve_local_reference(
    raw_value: str,
    *,
    rst_path: Path,
    bundle_dir: Path,
    docs_dir: Path,
) -> Path | None:
    token = raw_value.strip()
    if not token or _is_external_reference(token):
        return None

    raw_path = Path(token.lstrip("/"))
    probe_paths = [
        rst_path.parent / raw_path,
        bundle_dir / raw_path,
        docs_dir / raw_path,
        ROOT / raw_path,
    ]
    for probe in probe_paths:
        if probe.exists():
            return probe.resolve()
    return None


def _pick_spec_value(row: dict[str, str], lang: str) -> str:
    for key in (
        f"Value_{lang}",
        f"Value_{lang.lower()}",
        f"Value_{lang.upper()}",
        "Value_en",
        "Value",
        "Spec_Value",
    ):
        value = (row.get(key) or "").strip()
        if value:
            return value
    return ""


def _collect_placeholder_tokens(text: str) -> set[str]:
    return {match.group(1).strip() for match in PLACEHOLDER_RE.finditer(text) if match.group(1).strip()}


def _field_binding_is_used(placeholder: str, used_placeholders: set[str]) -> bool:
    return any(
        candidate in used_placeholders
        for candidate in (
            placeholder,
            f"{placeholder}_BOLD",
            f"{placeholder}_LOWER",
        )
    )


def collect_placeholder_issues(
    *,
    rst_path: Path,
    model: str | None,
    region: str | None,
) -> list[CheckIssue]:
    matches = sorted(set(PLACEHOLDER_RE.findall(rst_path.read_text(encoding="utf-8"))))
    if not matches:
        return []
    return [
        CheckIssue(
            code="UNRESOLVED_PLACEHOLDER",
            message=f"Unresolved placeholders: {', '.join(matches)}",
            model=model,
            region=region,
            path=rst_path,
        )
    ]


def collect_reference_issues(
    *,
    rst_path: Path,
    bundle_dir: Path,
    docs_dir: Path,
    model: str | None,
    region: str | None,
) -> list[CheckIssue]:
    issues: list[CheckIssue] = []
    for line_no, line in enumerate(rst_path.read_text(encoding="utf-8").splitlines(), start=1):
        include_match = INCLUDE_RE.match(line)
        if include_match:
            raw_value = include_match.group(1)
            resolved = _resolve_local_reference(
                raw_value,
                rst_path=rst_path,
                bundle_dir=bundle_dir,
                docs_dir=docs_dir,
            )
            if resolved is None:
                issues.append(
                    CheckIssue(
                        code="MISSING_INCLUDE",
                        message=f"Missing include target on line {line_no}: {raw_value}",
                        model=model,
                        region=region,
                        path=rst_path,
                    )
                )

        asset_match = ASSET_RE.match(line)
        if asset_match:
            raw_value = asset_match.group(1)
            resolved = _resolve_local_reference(
                raw_value,
                rst_path=rst_path,
                bundle_dir=bundle_dir,
                docs_dir=docs_dir,
            )
            if resolved is None:
                issues.append(
                    CheckIssue(
                        code="MISSING_ASSET",
                        message=f"Missing image/figure asset on line {line_no}: {raw_value}",
                        model=model,
                        region=region,
                        path=rst_path,
                    )
                )

        for html_match in HTML_SRC_RE.finditer(line):
            raw_value = html_match.group(1)
            resolved = _resolve_local_reference(
                raw_value,
                rst_path=rst_path,
                bundle_dir=bundle_dir,
                docs_dir=docs_dir,
            )
            if resolved is None:
                issues.append(
                    CheckIssue(
                        code="MISSING_HTML_SRC",
                        message=f"Missing HTML src asset on line {line_no}: {raw_value}",
                        model=model,
                        region=region,
                        path=rst_path,
                    )
                )
    return issues


def collect_target_identity_issues(cfg: dict, *, target: BuildTarget, langs: list[str]) -> list[CheckIssue]:
    issues: list[CheckIssue] = []
    spec_master_csv = resolve_spec_master_csv_path(cfg)
    for lang in langs:
        product_name = resolve_product_name_for_build(
            cfg,
            model=target.model,
            region=target.region,
            lang=lang,
        )
        substitutions = resolve_template_substitutions_from_spec_master(
            spec_master_csv,
            model=target.model,
            region=target.region,
            lang=lang,
        )
        if not (product_name or "").strip():
            issues.append(
                CheckIssue(
                    code="MISSING_PRODUCT_NAME",
                    message="Failed to resolve Product Name from Spec_Master.csv",
                    model=target.model,
                    region=target.region,
                    lang=lang,
                )
            )
        if not (substitutions.get("MODEL_NO") or "").strip():
            issues.append(
                CheckIssue(
                    code="MISSING_MODEL_NO",
                    message="Failed to resolve MODEL_NO from Spec_Master.csv",
                    model=target.model,
                    region=target.region,
                    lang=lang,
                )
            )
    return issues


def collect_bundle_issues(
    *,
    bundle_dir: Path,
    docs_dir: Path,
    model: str | None,
    region: str | None,
) -> list[CheckIssue]:
    issues: list[CheckIssue] = []
    index_path = bundle_dir / "index.rst"
    page_dir = bundle_dir / "page"
    if not index_path.exists():
        issues.append(
            CheckIssue(
                code="MISSING_BUNDLE_INDEX",
                message=f"Prepared bundle index not found: {index_path}",
                model=model,
                region=region,
                path=index_path,
            )
        )
    if not page_dir.exists():
        issues.append(
            CheckIssue(
                code="MISSING_PAGE_DIR",
                message=f"Prepared bundle page directory not found: {page_dir}",
                model=model,
                region=region,
                path=page_dir,
            )
        )
        return issues

    for rst_path in sorted(path for path in bundle_dir.rglob("*.rst") if path.is_file()):
        issues.extend(
            collect_placeholder_issues(
                rst_path=rst_path,
                model=model,
                region=region,
            )
        )
        issues.extend(
            collect_reference_issues(
                rst_path=rst_path,
                bundle_dir=bundle_dir,
                docs_dir=docs_dir,
                model=model,
                region=region,
            )
        )
    return issues


def collect_identity_drift_issues(
    cfg: dict,
    *,
    bundle_dir: Path,
    target: BuildTarget,
    langs: list[str],
) -> list[CheckIssue]:
    spec_master_csv = resolve_spec_master_csv_path(cfg)
    checks_cfg = _checks_cfg(cfg)
    allowlist_raw = checks_cfg.get("allowed_foreign_identity_literals", [])
    allowlist = tuple(str(item).strip() for item in allowlist_raw if str(item).strip()) if isinstance(allowlist_raw, list) else ()

    matches = find_identity_drift_matches(
        bundle_dir=bundle_dir,
        spec_master_csv=spec_master_csv,
        model=target.model,
        region=target.region,
        langs=langs,
        allowlist=allowlist,
    )
    issues: list[CheckIssue] = []
    for match in matches:
        source_target = "/".join(bit for bit in (match.source_model, match.source_region) if bit) or "_shared/_default"
        issues.append(
            CheckIssue(
                code="STALE_IDENTITY_LITERAL",
                message=(
                    f"Found foreign identity literal '{match.literal}' on line {match.line_no} "
                    f"(latest source target: {source_target})"
                ),
                model=target.model,
                region=target.region,
                path=match.path,
            )
        )
    return issues


def collect_page_contract_issues(
    cfg: dict,
    *,
    docs_dir: Path,
    target: BuildTarget,
    langs: list[str],
) -> list[CheckIssue]:
    contracts = load_page_contracts(resolve_contracts_dir(docs_dir=docs_dir))
    if not contracts:
        return []

    pages = resolve_config_pages_or_raise(
        cfg,
        default_languages=langs,
        root=ROOT,
        model=target.model,
        region=target.region,
        error_prefix="config.pages",
    ).pages
    spec_master_csv = resolve_spec_master_csv_path(cfg)
    spec_rows = read_spec_master_rows(spec_master_csv)
    substitutions_by_lang: dict[str, dict[str, str]] = {}
    issues: list[CheckIssue] = []

    for page in pages:
        if not isinstance(page, (RstIncludePage, GeneratedPage)):
            continue
        source_path = _page_source_path(
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

        page_langs = [page.lang] if isinstance(page, RstIncludePage) and page.lang else list(page.langs) if isinstance(page, GeneratedPage) else langs
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
                    CheckIssue(
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
                )
                is None
            ]
            if missing_spec_keys:
                issues.append(
                    CheckIssue(
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
            missing_tpl_keys = [
                row_key
                for row_key in required_tpl_keys_for_lang(contract, lang)
                if resolve_spec_value_from_rows(
                    spec_rows,
                    model=target.model,
                    region=target.region,
                    lang=lang,
                    row_key=row_key,
                )
                is None
            ]
            if missing_tpl_keys:
                issues.append(
                    CheckIssue(
                        code="CONTRACT_MISSING_TPL_KEYS",
                        message=(
                            f"Page contract '{contract.page_id}' is missing required tpl row keys "
                            f"for lang '{lang}': {', '.join(missing_tpl_keys)}"
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
                if not _contract_asset_exists(
                    asset_path,
                    docs_dir=docs_dir,
                    model=target.model,
                    region=target.region,
                    lang=lang,
                )
            ]
            if missing_assets:
                issues.append(
                    CheckIssue(
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


def collect_generated_page_issues(
    cfg: dict,
    *,
    docs_dir: Path,
    target: BuildTarget,
    langs: list[str],
) -> list[CheckIssue]:
    manifest_path = resolve_page_manifest_path(cfg, root=ROOT, model=target.model, region=target.region)
    if manifest_path is None:
        pages_raw = cfg.get("pages")
        if not isinstance(pages_raw, list) or not pages_raw:
            return []

    pages = resolve_config_pages_or_raise(
        cfg,
        default_languages=langs,
        root=ROOT,
        model=target.model,
        region=target.region,
        error_prefix="config.pages",
    ).pages
    generated_pages = [page for page in pages if isinstance(page, GeneratedPage)]
    if not generated_pages:
        return []

    spec_master_csv = resolve_spec_master_csv_path(cfg)
    spec_rows = read_spec_master_rows(spec_master_csv)
    registry_path = resolve_snippet_registry_path(docs_dir)
    registry_entries: list = []
    registry_error: RuntimeError | None = None
    try:
        registry_entries = load_snippet_registry(registry_path)
    except RuntimeError as exc:
        registry_error = exc

    contracts = load_page_contracts(resolve_contracts_dir(docs_dir=docs_dir))
    contract_ids = {contract.page_id for contract in contracts}
    contract_file_names = {f"{contract.page_id}.yaml" for contract in contracts}
    base_substitutions = load_rst_substitutions(docs_dir / "conf_base.py")
    issues: list[CheckIssue] = []
    used_snippet_ids: set[str] = set()

    for page in generated_pages:
        recipe_path = resolve_config_path(docs_dir, page.recipe, target.model, target.region)
        template_path = resolve_config_path(docs_dir, page.template, target.model, target.region)
        if not recipe_path.exists():
            issues.append(
                CheckIssue(
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
                CheckIssue(
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
                CheckIssue(
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
                CheckIssue(
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
                CheckIssue(
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
                CheckIssue(
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
            )
            if missing_row_keys:
                issues.append(
                    CheckIssue(
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
                placeholder
                for placeholder, binding in recipe.field_map.items()
                if resolve_spec_value_from_rows(
                    spec_rows,
                    model=target.model,
                    region=target.region,
                    lang=lang,
                    row_key=binding.row_key,
                    pages=binding.pages,
                    line_order=binding.line_order,
                )
                is None
                and binding.default is None
            ]
            if field_binding_misses:
                issues.append(
                    CheckIssue(
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
                )
                distinct_values = sorted({_pick_spec_value(row, lang) for row in matching_rows if _pick_spec_value(row, lang)})
                if len(distinct_values) > 1:
                    issues.append(
                        CheckIssue(
                            code="AMBIGUOUS_FIELD_MAP_ROWS",
                            message=(
                                f"Recipe '{recipe.page_id}' field_map.{placeholder} resolves to multiple values "
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
                        CheckIssue(
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
                    CheckIssue(
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
                        CheckIssue(
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
                        CheckIssue(
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
                        CheckIssue(
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
                used_placeholders.update(_collect_placeholder_tokens(text))

            unused_field_map = sorted(
                placeholder
                for placeholder in recipe.field_map
                if not _field_binding_is_used(placeholder, used_placeholders)
            )
            if unused_field_map:
                issues.append(
                    CheckIssue(
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
                    CheckIssue(
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
                CheckIssue(
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
                CheckIssue(
                    code="ORPHAN_SNIPPET",
                    message=f"Snippet '{snippet_id}' is defined in the registry but not used by any draft recipe",
                    model=target.model,
                    region=target.region,
                    path=registry_path,
                )
            )

    return issues


def _resolve_contract_asset_path(
    raw_value: str,
    *,
    docs_dir: Path,
    model: str | None,
    region: str | None,
    lang: str | None,
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
    return ROOT / candidate


def _contract_asset_exists(
    raw_value: str,
    *,
    docs_dir: Path,
    model: str | None,
    region: str | None,
    lang: str | None,
) -> bool:
    return _resolve_contract_asset_path(
        raw_value,
        docs_dir=docs_dir,
        model=model,
        region=region,
        lang=lang,
    ).exists()


def collect_check_issues(
    *,
    cfg_path: Path,
    model: str | None,
    region: str | None,
    all_targets: bool,
) -> list[CheckIssue]:
    cfg = load_config(cfg_path)
    docs_dir = resolve_docs_dir(cfg)
    langs = _build_langs(cfg)
    manifest_path = resolve_page_manifest_path(cfg, root=ROOT, model=model, region=region)
    targets = resolve_build_targets(
        cfg,
        arg_model=model,
        arg_region=region,
        all_targets=all_targets,
    )

    issues: list[CheckIssue] = []
    if manifest_path is not None and not manifest_path.exists():
        issues.append(
            CheckIssue(
                code="MISSING_PAGE_MANIFEST",
                message=f"Configured page manifest not found: {manifest_path}",
                model=model,
                region=region,
                path=manifest_path,
            )
        )
    for target in targets:
        target_langs = [target.lang] if (target.lang or "").strip() else langs
        bundle_dir = bundle_dir_for_target(
            docs_dir=docs_dir,
            model=target.model,
            region=target.region,
            lang=target.lang,
        )
        issues.extend(collect_target_identity_issues(cfg, target=target, langs=target_langs))
        issues.extend(
            collect_page_contract_issues(
                cfg,
                docs_dir=docs_dir,
                target=target,
                langs=target_langs,
            )
        )
        issues.extend(
            collect_generated_page_issues(
                cfg,
                docs_dir=docs_dir,
                target=target,
                langs=target_langs,
            )
        )
        issues.extend(
            collect_bundle_issues(
                bundle_dir=bundle_dir,
                docs_dir=docs_dir,
                model=target.model,
                region=target.region,
            )
        )
        issues.extend(
            collect_identity_drift_issues(
                cfg,
                bundle_dir=bundle_dir,
                target=target,
                langs=langs,
            )
        )
    return issues


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Run lightweight quality checks against prepared manual bundles.")
    ap.add_argument("--config", required=True, help="Config YAML path")
    ap.add_argument("--model", default=None, help="Single target model override")
    ap.add_argument("--region", default=None, help="Single target region override")
    ap.add_argument("--all-targets", action="store_true", help="Use build.targets from config")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = ROOT / cfg_path

    try:
        issues = collect_check_issues(
            cfg_path=cfg_path,
            model=args.model,
            region=args.region,
            all_targets=args.all_targets,
        )
    except RuntimeError as exc:
        print(f"[check] ERROR: {exc}", file=sys.stderr)
        return 1

    if issues:
        for issue in issues:
            target_bits = [bit for bit in (issue.model, issue.region) if bit]
            target_text = "/".join(target_bits) if target_bits else "_shared/_default"
            lang_text = f" lang={issue.lang}" if issue.lang else ""
            path_text = f" path={_repo_relative(issue.path)}" if issue.path else ""
            print(f"[check] {issue.code} target={target_text}{lang_text}{path_text}: {issue.message}")
        print(f"[check] FAILED with {len(issues)} issue(s)", file=sys.stderr)
        return 1

    print("[check] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
