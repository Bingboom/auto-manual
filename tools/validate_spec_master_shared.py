#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.build_docs import BuildTarget, load_config, resolve_build_targets  # noqa: E402
from tools.config_pages import GeneratedPage  # noqa: E402
from tools.data_snapshot import resolve_data_snapshot_paths  # noqa: E402
from tools.draft_engine import load_draft_recipe  # noqa: E402
from tools.page_manifest import resolve_config_pages_or_raise  # noqa: E402
from tools.utils.spec_master import (  # noqa: E402
    canonicalize_model_token,
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


def resolve_spec_master_csv_path(cfg: dict, *, data_root: str | None = None) -> Path:
    return resolve_data_snapshot_paths(
        cfg,
        repo_root=ROOT,
        data_root=data_root,
    ).spec_master_csv


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
    row_region = _first_non_empty(row, ("Region", "region"))
    target_region = (region or "").strip()
    row_model = canonicalize_model_token(
        _first_non_empty(row, ("Model", "model")),
        region=row_region or target_region,
    )
    target_model = canonicalize_model_token(model or "", region=target_region)
    if target_model and row_model.casefold() != target_model.casefold():
        return False
    if region and row_region.strip().lower() != region.strip().lower():
        return False
    return _is_truthy(_first_non_empty(row, ("Is_Latest", "is_latest")))


def _should_require_value_source(row: dict[str, str]) -> bool:
    row_kind = _first_non_empty(row, ("row_kind", "Row_kind")).strip().lower()
    return row_kind not in {"note", "footnote"}


def _pick_document_key(row: dict[str, str]) -> str:
    return _first_non_empty(row, ("document_key", "Document_key"))


def _accepted_document_keys(row: dict[str, str]) -> tuple[str, ...]:
    region = _first_non_empty(row, ("Region", "region"))
    model = canonicalize_model_token(_first_non_empty(row, ("Model", "model")), region=region)
    source_lang = _first_non_empty(row, ("Source_lang", "source_lang"))
    if not model or not region:
        return ()
    accepted = [f"{model}_{region}"]
    if source_lang:
        accepted.append(f"{model}_{region}_{source_lang}")
    return tuple(dict.fromkeys(accepted))


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


_LEGACY_FOOTNOTE_MARKER_RE = re.compile(r"[\u2460-\u2473]|\(\d+\)|^\d+\.\s+")


def _parse_ref_ids(value: str) -> tuple[str, ...]:
    refs: list[str] = []
    for token in (value or "").split(","):
        item = token.strip()
        if item and item not in refs:
            refs.append(item)
    return tuple(refs)


def _read_optional_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    return read_spec_master_rows(path)


def _effective_targets(
    cfg: dict,
    *,
    model: str | None,
    region: str | None,
    lang: str | None = None,
    all_targets: bool,
) -> list[BuildTarget]:
    explicit_target = (model or "").strip() or (region or "").strip() or (lang or "").strip()
    return resolve_build_targets(
        cfg,
        arg_model=model,
        arg_region=region,
        arg_lang=lang,
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
            if binding.default is not None or getattr(binding, "page_copy_key", None) is not None:
                continue
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
