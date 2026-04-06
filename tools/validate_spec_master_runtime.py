from __future__ import annotations

from pathlib import Path

from tools.data_snapshot import resolve_data_snapshot_paths
from tools.utils.spec_master import (
    collect_matching_spec_rows,
    collect_spec_value_matches_from_rows,
    normalize_source_lang,
    read_spec_master_rows,
)
from tools.validate_spec_master_shared import (
    ROOT,
    _LEGACY_FOOTNOTE_MARKER_RE,
    _LEGACY_SOURCE_HEADERS,
    _accepted_document_keys,
    _build_langs,
    _collect_target_selectors,
    _effective_targets,
    _first_non_empty,
    _is_truthy,
    _parse_ref_ids,
    _pick_document_key,
    _pick_line_number,
    _pick_value,
    _read_optional_rows,
    _row_matches_target,
    _should_require_value_source,
    SpecMasterValidationIssue,
    load_config,
)


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
