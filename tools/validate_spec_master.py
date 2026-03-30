#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_docs import BuildTarget, load_config, resolve_build_targets  # noqa: E402
from tools.config_pages import GeneratedPage  # noqa: E402
from tools.draft_engine import load_draft_recipe  # noqa: E402
from tools.page_manifest import resolve_config_pages_or_raise  # noqa: E402
from tools.utils.spec_master import (  # noqa: E402
    collect_matching_spec_rows,
    collect_spec_value_matches_from_rows,
    normalize_source_lang,
    read_spec_master_rows,
    source_language_for_row,
)
from tools.word_bundle_common import resolve_config_path  # noqa: E402


@dataclass(frozen=True)
class SpecSelector:
    owner: str
    row_key: str
    pages: tuple[str, ...]
    line_order: str | None = None
    usage_type: str | None = None
    placement_key: str | None = None
    value_role: str | None = None
    variant_key: str | None = None


@dataclass(frozen=True)
class SpecMasterValidationIssue:
    code: str
    message: str
    path: Path | None = None
    line: int | None = None
    model: str | None = None
    region: str | None = None
    lang: str | None = None
    row_key: str | None = None


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


def resolve_spec_master_csv_path(cfg: dict) -> Path:
    paths_cfg_raw = cfg.get("paths", {})
    paths_cfg = paths_cfg_raw if isinstance(paths_cfg_raw, dict) else {}
    raw = paths_cfg.get("spec_master_csv")
    if isinstance(raw, str) and raw.strip():
        path = Path(raw.strip())
        return path if path.is_absolute() else (ROOT / path)
    return ROOT / "data" / "phase1" / "Spec_Master.csv"


def resolve_docs_dir(cfg: dict) -> Path:
    paths_cfg_raw = cfg.get("paths", {})
    paths_cfg = paths_cfg_raw if isinstance(paths_cfg_raw, dict) else {}
    raw = paths_cfg.get("docs_dir")
    if isinstance(raw, str) and raw.strip():
        path = Path(raw.strip())
        return path if path.is_absolute() else (ROOT / path)
    return ROOT / "docs"


def _first_non_empty(row: dict[str, str], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = (row.get(key) or "").strip()
        if value:
            return value
    return ""


def _pick_line_number(row: dict[str, str]) -> int | None:
    raw = (row.get("__line__") or "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


_LEGACY_SOURCE_HEADERS = ("Row_label_en", "Param_en", "Value_en")


def _is_truthy(value: str) -> bool:
    text = (value or "").strip().lower()
    if not text:
        return True
    return text in {"1", "true", "yes", "y"}


def _row_matches_target(row: dict[str, str], *, model: str | None, region: str | None) -> bool:
    row_model = _first_non_empty(row, ("Model", "model"))
    row_region = _first_non_empty(row, ("Region", "region"))
    if model and row_model.strip().lower() != model.strip().lower():
        return False
    if region and row_region.strip().lower() != region.strip().lower():
        return False
    return _is_truthy(_first_non_empty(row, ("Is_Latest", "is_latest")))


def _should_require_value_source(row: dict[str, str]) -> bool:
    row_kind = _first_non_empty(row, ("row_kind", "Row_kind")).strip().lower()
    return row_kind not in {"note", "footnote"}


def _pick_value(row: dict[str, str], lang: str) -> str:
    normalized_lang = (lang or "").strip().lower()
    source_lang = source_language_for_row(row)
    if normalized_lang == "en" or (source_lang and normalized_lang == source_lang):
        return _first_non_empty(row, ("Value_source", "value_source", "Value", "Spec_Value"))
    return _first_non_empty(
        row,
        (
            f"Value_{lang}",
            f"Value_{lang.lower()}",
            f"Value_{lang.upper()}",
            "Value_source",
            "value_source",
            "Value",
            "Spec_Value",
        ),
    )


def _effective_targets(
    cfg: dict,
    *,
    model: str | None,
    region: str | None,
    all_targets: bool,
) -> list[BuildTarget]:
    explicit_target = (model or "").strip() or (region or "").strip()
    return resolve_build_targets(
        cfg,
        arg_model=model,
        arg_region=region,
        all_targets=all_targets or not bool(explicit_target),
    )


def _collect_target_selectors(
    cfg: dict,
    *,
    target: BuildTarget,
    langs: list[str],
) -> tuple[list[SpecSelector], list[SpecMasterValidationIssue]]:
    selectors = [
        SpecSelector(owner="target identity", row_key="product_name", pages=None),
        SpecSelector(owner="target identity", row_key="model_no", pages=None),
    ]
    issues: list[SpecMasterValidationIssue] = []
    docs_dir = resolve_docs_dir(cfg)

    try:
        pages = resolve_config_pages_or_raise(
            cfg,
            default_languages=langs,
            root=ROOT,
            model=target.model,
            region=target.region,
            error_prefix="config.pages",
        ).pages
    except RuntimeError as exc:
        issues.append(
            SpecMasterValidationIssue(
                code="INVALID_PAGE_CONFIG",
                message=str(exc),
                model=target.model,
                region=target.region,
            )
        )
        return selectors, issues

    for page in pages:
        if not isinstance(page, GeneratedPage):
            continue
        recipe_path = resolve_config_path(docs_dir, page.recipe, target.model, target.region)
        if not recipe_path.exists():
            issues.append(
                SpecMasterValidationIssue(
                    code="MISSING_RECIPE",
                    message=f"Generated page recipe not found: {recipe_path}",
                    path=recipe_path,
                    model=target.model,
                    region=target.region,
                )
            )
            continue
        try:
            recipe = load_draft_recipe(recipe_path)
        except RuntimeError as exc:
            issues.append(
                SpecMasterValidationIssue(
                    code="INVALID_RECIPE",
                    message=str(exc),
                    path=recipe_path,
                    model=target.model,
                    region=target.region,
                )
            )
            continue

        for row_key in recipe.required_row_keys:
            selectors.append(
                SpecSelector(
                    owner=f"recipe '{recipe.page_id}' required_row_keys",
                    row_key=row_key,
                    pages=None,
                )
            )
        for placeholder, binding in recipe.field_map.items():
            selectors.append(
                SpecSelector(
                    owner=f"recipe '{recipe.page_id}' field_map.{placeholder}",
                    row_key=binding.row_key,
                    pages=tuple(binding.pages),
                    line_order=binding.line_order,
                    usage_type=binding.usage_type,
                    placement_key=binding.placement_key,
                    value_role=binding.value_role,
                    variant_key=binding.variant_key,
                )
            )

    deduped = list(
        {
            (
                selector.owner,
                selector.row_key,
                selector.pages,
                selector.line_order,
                selector.usage_type,
                selector.placement_key,
                selector.value_role,
                selector.variant_key,
            ): selector
            for selector in selectors
        }.values()
    )
    return deduped, issues


def collect_spec_master_validation_issues(
    *,
    cfg_path: Path,
    model: str | None,
    region: str | None,
    all_targets: bool,
) -> list[SpecMasterValidationIssue]:
    cfg = load_config(cfg_path)
    spec_master_csv = resolve_spec_master_csv_path(cfg)
    rows = read_spec_master_rows(spec_master_csv)
    langs = _build_langs(cfg)
    targets = _effective_targets(
        cfg,
        model=model,
        region=region,
        all_targets=all_targets,
    )

    issues: list[SpecMasterValidationIssue] = []
    if not spec_master_csv.exists():
        return [
            SpecMasterValidationIssue(
                code="MISSING_SPEC_MASTER",
                message=f"Spec_Master.csv not found: {spec_master_csv}",
                path=spec_master_csv,
                model=model,
                region=region,
            )
        ]
    if not rows:
        return [
            SpecMasterValidationIssue(
                code="EMPTY_SPEC_MASTER",
                message=f"Spec_Master.csv has no data rows: {spec_master_csv}",
                path=spec_master_csv,
                model=model,
                region=region,
            )
        ]

    present_legacy_headers = [header for header in _LEGACY_SOURCE_HEADERS if header in rows[0]]
    if present_legacy_headers:
        issues.append(
            SpecMasterValidationIssue(
                code="LEGACY_SOURCE_HEADERS_PRESENT",
                message=(
                    "Spec_Master.csv still uses legacy source headers: "
                    + ", ".join(present_legacy_headers)
                    + ". Rename them to *_source and keep source text in *_source only."
                ),
                path=spec_master_csv,
                model=model,
                region=region,
            )
        )

    for target in targets:
        for row in rows:
            if not _row_matches_target(row, model=target.model, region=target.region):
                continue
            row_key = _first_non_empty(row, ("Row_key", "row_key"))
            if not row_key:
                continue
            line_no = _pick_line_number(row)
            raw_source_lang = _first_non_empty(row, ("Source_lang", "source_lang"))
            normalized_source_lang = normalize_source_lang(raw_source_lang)
            if not raw_source_lang:
                issues.append(
                    SpecMasterValidationIssue(
                        code="MISSING_SOURCE_LANG",
                        message=f"Latest row_key '{row_key}' must declare Source_lang",
                        path=spec_master_csv,
                        line=line_no,
                        model=target.model,
                        region=target.region,
                        row_key=row_key,
                    )
                )
            elif not normalized_source_lang:
                issues.append(
                    SpecMasterValidationIssue(
                        code="INVALID_SOURCE_LANG",
                        message=(
                            f"Latest row_key '{row_key}' has unsupported Source_lang "
                            f"'{raw_source_lang}'"
                        ),
                        path=spec_master_csv,
                        line=line_no,
                        model=target.model,
                        region=target.region,
                        row_key=row_key,
                    )
                )
            if not _first_non_empty(row, ("Row_label_source", "row_label_source")):
                issues.append(
                    SpecMasterValidationIssue(
                        code="MISSING_SOURCE_ROW_LABEL",
                        message=f"Latest row_key '{row_key}' must store source text in Row_label_source",
                        path=spec_master_csv,
                        line=line_no,
                        model=target.model,
                        region=target.region,
                        row_key=row_key,
                    )
                )
            if _should_require_value_source(row) and not _first_non_empty(row, ("Value_source", "value_source")):
                issues.append(
                    SpecMasterValidationIssue(
                        code="MISSING_SOURCE_VALUE",
                        message=f"Latest row_key '{row_key}' must store source text in Value_source",
                        path=spec_master_csv,
                        line=line_no,
                        model=target.model,
                        region=target.region,
                        row_key=row_key,
                    )
                )

        target_langs = [target.lang] if (target.lang or "").strip() else langs
        selectors, selector_issues = _collect_target_selectors(cfg, target=target, langs=target_langs)
        issues.extend(selector_issues)

        for lang in target_langs:
            for selector in selectors:
                matching_rows = collect_matching_spec_rows(
                    rows,
                    model=target.model,
                    region=target.region,
                    lang=lang,
                    row_key=selector.row_key,
                    pages=selector.pages,
                    line_order=selector.line_order,
                    usage_type=selector.usage_type,
                    placement_key=selector.placement_key,
                    value_role=selector.value_role,
                    variant_key=selector.variant_key,
                )
                if not matching_rows:
                    issues.append(
                        SpecMasterValidationIssue(
                            code="MISSING_REQUIRED_SPEC_ROW",
                            message=(
                                f"{selector.owner} requires row_key '{selector.row_key}' "
                                f"but no matching latest Spec_Master row was found"
                            ),
                            path=spec_master_csv,
                            model=target.model,
                            region=target.region,
                            lang=lang,
                            row_key=selector.row_key,
                        )
                    )
                    continue

                exact_groups: dict[tuple[str, str, str, str, str], list[dict[str, str]]] = {}
                for row in matching_rows:
                    line_order_value = _first_non_empty(row, ("Line_order", "line_order"))
                    key = (
                        _first_non_empty(row, ("Model", "model")),
                        _first_non_empty(row, ("Region", "region")),
                        _first_non_empty(row, ("Page", "page")),
                        _first_non_empty(row, ("Row_key", "row_key")).lower(),
                        line_order_value,
                    )
                    exact_groups.setdefault(key, []).append(row)
                for grouped_rows in exact_groups.values():
                    if len(grouped_rows) <= 1:
                        continue
                    line_numbers = ", ".join(
                        str(line_no)
                        for line_no in sorted(
                            line_no for line_no in (_pick_line_number(row) for row in grouped_rows) if line_no is not None
                        )
                    )
                    issues.append(
                        SpecMasterValidationIssue(
                            code="DUPLICATE_LATEST_SPEC_ROW",
                            message=(
                                f"{selector.owner} matched duplicate latest rows for '{selector.row_key}'"
                                + (f" on lines {line_numbers}" if line_numbers else "")
                            ),
                            path=spec_master_csv,
                            line=_pick_line_number(grouped_rows[0]),
                            model=target.model,
                            region=target.region,
                            lang=lang,
                            row_key=selector.row_key,
                        )
                    )

                value_matches = collect_spec_value_matches_from_rows(
                    rows,
                    model=target.model,
                    region=target.region,
                    lang=lang,
                    row_key=selector.row_key,
                    pages=selector.pages,
                    line_order=selector.line_order,
                    usage_type=selector.usage_type,
                    placement_key=selector.placement_key,
                    value_role=selector.value_role,
                    variant_key=selector.variant_key,
                )
                if not value_matches:
                    issues.append(
                        SpecMasterValidationIssue(
                            code="EMPTY_REQUIRED_SPEC_VALUE",
                            message=(
                                f"{selector.owner} matched row_key '{selector.row_key}' "
                                f"but every matching latest row resolved to an empty value"
                            ),
                            path=spec_master_csv,
                            line=_pick_line_number(matching_rows[0]),
                            model=target.model,
                            region=target.region,
                            lang=lang,
                            row_key=selector.row_key,
                        )
                    )
                    continue

                distinct_values = sorted({match.value for match in value_matches if match.value.strip()})
                if len(distinct_values) > 1:
                    issues.append(
                        SpecMasterValidationIssue(
                            code="AMBIGUOUS_SPEC_SELECTOR",
                            message=(
                                f"{selector.owner} matched multiple values for '{selector.row_key}' "
                                f"under lang '{lang}': {', '.join(distinct_values)}"
                            ),
                            path=spec_master_csv,
                            line=_pick_line_number(value_matches[0].row),
                            model=target.model,
                            region=target.region,
                            lang=lang,
                            row_key=selector.row_key,
                        )
                    )

                if any(not _pick_value(row, lang).strip() for row in matching_rows):
                    issues.append(
                        SpecMasterValidationIssue(
                            code="PARTIAL_EMPTY_SPEC_VALUE",
                            message=(
                                f"{selector.owner} matched at least one empty latest value for '{selector.row_key}' "
                                f"under lang '{lang}'"
                            ),
                            path=spec_master_csv,
                            line=_pick_line_number(matching_rows[0]),
                            model=target.model,
                            region=target.region,
                            lang=lang,
                            row_key=selector.row_key,
                        )
                    )

    return sorted(
        issues,
        key=lambda item: (
            item.code,
            item.model or "",
            item.region or "",
            item.lang or "",
            item.row_key or "",
            item.line or -1,
        ),
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Validate target-bound Spec_Master selectors used by the manual pipeline.")
    ap.add_argument("--config", required=True, help="Config YAML path")
    ap.add_argument("--model", default=None, help="Single target model override")
    ap.add_argument("--region", default=None, help="Single target region override")
    ap.add_argument("--all-targets", action="store_true", help="Validate all build targets from the config")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = ROOT / cfg_path

    try:
        issues = collect_spec_master_validation_issues(
            cfg_path=cfg_path,
            model=args.model,
            region=args.region,
            all_targets=args.all_targets,
        )
    except RuntimeError as exc:
        print(f"[validate_spec_master] ERROR: {exc}", file=sys.stderr)
        return 1

    if issues:
        for issue in issues:
            target_bits = [bit for bit in (issue.model, issue.region) if bit]
            target_text = "/".join(target_bits) if target_bits else "_shared/_default"
            lang_text = f" lang={issue.lang}" if issue.lang else ""
            path_text = f" path={_repo_relative(issue.path)}" if issue.path else ""
            line_text = f" line={issue.line}" if issue.line is not None else ""
            print(f"[validate_spec_master] {issue.code} target={target_text}{lang_text}{path_text}{line_text}: {issue.message}")
        print(f"[validate_spec_master] FAILED with {len(issues)} issue(s)", file=sys.stderr)
        return 1

    print("[validate_spec_master] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
