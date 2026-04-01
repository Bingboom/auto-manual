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

from tools.build_docs import BuildTarget, load_config, resolve_build_targets  # noqa: E402
from tools.config_pages import GeneratedPage  # noqa: E402
from tools.data_snapshot import resolve_data_snapshot_paths  # noqa: E402
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


def _pick_document_key(row: dict[str, str]) -> str:
    return _first_non_empty(row, ("document_key", "Document_key"))


def _accepted_document_keys(row: dict[str, str]) -> tuple[str, ...]:
    model = _first_non_empty(row, ("Model", "model"))
    region = _first_non_empty(row, ("Region", "region"))
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
    data_root: str | None = None,
) -> list[SpecMasterValidationIssue]:
    cfg = load_config(cfg_path)
    snapshot_paths = resolve_data_snapshot_paths(
        cfg,
        repo_root=ROOT,
        data_root=data_root,
        model=model,
        region=region,
    )
    spec_master_csv = snapshot_paths.spec_master_csv
    spec_footnotes_csv = snapshot_paths.spec_footnotes_csv
    spec_notes_csv = snapshot_paths.spec_notes_csv
    rows = read_spec_master_rows(spec_master_csv)
    footnote_rows = _read_optional_rows(spec_footnotes_csv)
    note_rows = _read_optional_rows(spec_notes_csv)
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

    has_document_key_header = "document_key" in rows[0] or "Document_key" in rows[0]
    if not has_document_key_header:
        issues.append(
            SpecMasterValidationIssue(
                code="MISSING_DOCUMENT_KEY_HEADER",
                message=(
                    "Spec_Master.csv must include a `document_key` column derived as "
                    "[Model]_[Region] or [Model]_[Region]_[Source_lang]."
                ),
                path=spec_master_csv,
                model=model,
                region=region,
            )
        )

    for target in targets:
        target_rows = [row for row in rows if _row_matches_target(row, model=target.model, region=target.region)]
        target_footnote_rows = [
            row for row in footnote_rows if _row_matches_target(row, model=target.model, region=target.region)
        ]
        target_note_rows = [
            row for row in note_rows if _row_matches_target(row, model=target.model, region=target.region)
        ]

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
            if has_document_key_header:
                document_key = _pick_document_key(row)
                if not document_key:
                    issues.append(
                        SpecMasterValidationIssue(
                            code="MISSING_DOCUMENT_KEY",
                            message=(
                                f"Latest row_key '{row_key}' must declare `document_key` as "
                                "[Model]_[Region] or [Model]_[Region]_[Source_lang]"
                            ),
                            path=spec_master_csv,
                            line=line_no,
                            model=target.model,
                            region=target.region,
                            row_key=row_key,
                        )
                    )
                else:
                    accepted_document_keys = _accepted_document_keys(row)
                    if accepted_document_keys and document_key not in accepted_document_keys:
                        expected_display = " or ".join(f"'{item}'" for item in accepted_document_keys)
                        issues.append(
                            SpecMasterValidationIssue(
                                code="INVALID_DOCUMENT_KEY",
                                message=(
                                    f"Latest row_key '{row_key}' has document_key '{document_key}' "
                                    f"but expected {expected_display}"
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

        footnote_ids_by_page: dict[str, dict[str, dict[str, str]]] = {}
        footnote_orders_by_page: dict[str, dict[str, dict[str, str]]] = {}
        for row in target_footnote_rows:
            line_no = _pick_line_number(row)
            footnote_id = _first_non_empty(row, ("Footnote_id", "footnote_id"))
            page = _first_non_empty(row, ("Page", "page")) or "specifications"
            order = _first_non_empty(row, ("Footnote_order", "footnote_order"))
            raw_source_lang = _first_non_empty(row, ("Source_lang", "source_lang"))
            if not footnote_id:
                issues.append(
                    SpecMasterValidationIssue(
                        code="MISSING_FOOTNOTE_ID",
                        message="Spec_Footnotes row must declare Footnote_id",
                        path=spec_footnotes_csv,
                        line=line_no,
                        model=target.model,
                        region=target.region,
                    )
                )
                continue
            if not order:
                issues.append(
                    SpecMasterValidationIssue(
                        code="MISSING_FOOTNOTE_ORDER",
                        message=f"Spec_Footnotes row '{footnote_id}' must declare Footnote_order",
                        path=spec_footnotes_csv,
                        line=line_no,
                        model=target.model,
                        region=target.region,
                    )
                )
            if not raw_source_lang:
                issues.append(
                    SpecMasterValidationIssue(
                        code="MISSING_FOOTNOTE_SOURCE_LANG",
                        message=f"Spec_Footnotes row '{footnote_id}' must declare Source_lang",
                        path=spec_footnotes_csv,
                        line=line_no,
                        model=target.model,
                        region=target.region,
                    )
                )
            elif not normalize_source_lang(raw_source_lang):
                issues.append(
                    SpecMasterValidationIssue(
                        code="INVALID_FOOTNOTE_SOURCE_LANG",
                        message=f"Spec_Footnotes row '{footnote_id}' has unsupported Source_lang '{raw_source_lang}'",
                        path=spec_footnotes_csv,
                        line=line_no,
                        model=target.model,
                        region=target.region,
                    )
                )
            text_value = _first_non_empty(row, ("Text_en", "Text_fr", "Text_es", "Text_ja", "text_en", "text_fr", "text_es", "text_ja"))
            if _LEGACY_FOOTNOTE_MARKER_RE.search(text_value):
                issues.append(
                    SpecMasterValidationIssue(
                        code="FOOTNOTE_TEXT_CONTAINS_MARKER",
                        message=f"Spec_Footnotes row '{footnote_id}' should not hardcode footnote markers in text",
                        path=spec_footnotes_csv,
                        line=line_no,
                        model=target.model,
                        region=target.region,
                    )
                )

            page_ids = footnote_ids_by_page.setdefault(page, {})
            if footnote_id in page_ids:
                issues.append(
                    SpecMasterValidationIssue(
                        code="DUPLICATE_FOOTNOTE_ID",
                        message=f"Duplicate Spec_Footnotes Footnote_id '{footnote_id}' on page '{page}'",
                        path=spec_footnotes_csv,
                        line=line_no,
                        model=target.model,
                        region=target.region,
                    )
                )
            else:
                page_ids[footnote_id] = row

            if order:
                page_orders = footnote_orders_by_page.setdefault(page, {})
                if order in page_orders:
                    issues.append(
                        SpecMasterValidationIssue(
                            code="DUPLICATE_FOOTNOTE_ORDER",
                            message=f"Duplicate Spec_Footnotes Footnote_order '{order}' on page '{page}'",
                            path=spec_footnotes_csv,
                            line=line_no,
                            model=target.model,
                            region=target.region,
                        )
                    )
                else:
                    page_orders[order] = row

        for row in target_note_rows:
            line_no = _pick_line_number(row)
            note_id = _first_non_empty(row, ("Note_id", "note_id"))
            if not note_id:
                issues.append(
                    SpecMasterValidationIssue(
                        code="MISSING_NOTE_ID",
                        message="Spec_Notes row must declare Note_id",
                        path=spec_notes_csv,
                        line=line_no,
                        model=target.model,
                        region=target.region,
                    )
                )

        used_footnote_refs: dict[str, set[str]] = {}
        for row in target_rows:
            line_no = _pick_line_number(row)
            page = _first_non_empty(row, ("Page", "page")) or "specifications"
            for ref_column in (
                "Row_label_footnote_refs",
                "row_label_footnote_refs",
                "Param_footnote_refs",
                "param_footnote_refs",
                "Value_footnote_refs",
                "value_footnote_refs",
            ):
                for footnote_id in _parse_ref_ids(_first_non_empty(row, (ref_column,))):
                    used_footnote_refs.setdefault(page, set()).add(footnote_id)
                    if footnote_id not in footnote_ids_by_page.get(page, {}):
                        issues.append(
                            SpecMasterValidationIssue(
                                code="UNKNOWN_FOOTNOTE_REF",
                                message=(
                                    f"Spec_Master row_key '{_first_non_empty(row, ('Row_key', 'row_key'))}' "
                                    f"references missing footnote '{footnote_id}' on page '{page}'"
                                ),
                                path=spec_master_csv,
                                line=line_no,
                                model=target.model,
                                region=target.region,
                                row_key=_first_non_empty(row, ("Row_key", "row_key")),
                            )
                        )

            for column in ("Row_label_source", "Param_source", "Value_source"):
                value = _first_non_empty(row, (column, column.lower()))
                if _LEGACY_FOOTNOTE_MARKER_RE.search(value):
                    issues.append(
                        SpecMasterValidationIssue(
                            code="LEGACY_INLINE_FOOTNOTE_MARKER",
                            message=(
                                f"Spec_Master row_key '{_first_non_empty(row, ('Row_key', 'row_key'))}' "
                                f"still hardcodes a footnote marker in {column}"
                            ),
                            path=spec_master_csv,
                            line=line_no,
                            model=target.model,
                            region=target.region,
                            row_key=_first_non_empty(row, ("Row_key", "row_key")),
                        )
                    )

        for page, page_defs in footnote_ids_by_page.items():
            unused_ids = sorted(set(page_defs) - used_footnote_refs.get(page, set()))
            for footnote_id in unused_ids:
                issues.append(
                    SpecMasterValidationIssue(
                        code="UNUSED_FOOTNOTE",
                        message=f"Spec_Footnotes row '{footnote_id}' on page '{page}' is not referenced by Spec_Master",
                        path=spec_footnotes_csv,
                        line=_pick_line_number(page_defs[footnote_id]),
                        model=target.model,
                        region=target.region,
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
    ap.add_argument("--data-root", default=None, help="Override structured content snapshot root")
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
            data_root=args.data_root,
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
