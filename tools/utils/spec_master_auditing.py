
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from tools.utils.spec_master_lookup import read_spec_master_rows
from tools.utils.spec_master_row_helpers import (
    _contains_east_asian_text,
    _first_non_empty,
    _is_template_row,
    _normalize_section_summary,
    _parse_slot_key,
    _pick_row_key,
    _pick_row_model,
    _pick_row_region,
    _pick_row_label_source,
    _pick_section,
    _pick_section_order,
    _pick_source_value,
    _row_line_num,
    _sort_text_numbers,
    _source_language_uses_latin_script,
    source_language_for_row,
)
from tools.utils.spec_master_shared import (
    SpecMasterAuditIssue,
    SpecMasterAuditResult,
    SpecMasterNormalizationResult,
    SpecMasterSectionOrderConflict,
    SpecMasterSectionSummary,
)

def audit_spec_master_rows(rows: list[dict[str, str]]) -> SpecMasterAuditResult:
    section_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    order_map: dict[str, set[str]] = defaultdict(set)
    issues: list[SpecMasterAuditIssue] = []

    for row in rows:
        section = _pick_section(row)
        if section:
            section_groups[section].append(row)
            order_value = _pick_section_order(row)
            if order_value:
                order_map[order_value].add(section)

    order_conflicts: list[SpecMasterSectionOrderConflict] = []
    for order_value in _sort_text_numbers(set(order_map)):
        sections = tuple(sorted(order_map[order_value]))
        if len(sections) <= 1:
            continue
        order_conflicts.append(
            SpecMasterSectionOrderConflict(
                section_order=order_value,
                sections=sections,
            )
        )
        issues.append(
            SpecMasterAuditIssue(
                code="SECTION_ORDER_COLLISION",
                message=(
                    f"Section_order `{order_value}` is shared by multiple sections: "
                    f"{', '.join(sections)}"
                ),
                line=None,
                model=None,
                region=None,
                section=None,
                row_key=None,
            )
        )

    section_summaries: list[SpecMasterSectionSummary] = []
    for section, grouped_rows in section_groups.items():
        suggested_section, category, note = _normalize_section_summary(section)
        section_summaries.append(
            SpecMasterSectionSummary(
                section=section,
                suggested_section=suggested_section,
                category=category,
                row_count=len(grouped_rows),
                orders=_sort_text_numbers({_pick_section_order(row) for row in grouped_rows}),
                models=tuple(sorted({_pick_row_model(row) for row in grouped_rows if _pick_row_model(row)})),
                regions=tuple(sorted({_pick_row_region(row) for row in grouped_rows if _pick_row_region(row)})),
                note=note,
            )
        )

    def summary_sort_key(item: SpecMasterSectionSummary) -> tuple[tuple[int, float | str], str]:
        order_value = item.orders[0] if item.orders else ""
        try:
            return ((0, float(order_value)), item.section)
        except ValueError:
            return ((1, order_value), item.section)

    section_summaries.sort(key=summary_sort_key)

    seen_rows: dict[tuple[tuple[str, str], ...], int] = {}
    for idx, row in enumerate(rows):
        line_number = _row_line_num(row, idx)
        region = _pick_row_region(row) or None
        section = _pick_section(row) or None
        row_key = _pick_row_key(row) or None
        model = _pick_row_model(row) or None

        source_label = _pick_row_label_source(row)
        if (
            source_label
            and _source_language_uses_latin_script(source_language_for_row(row))
            and _contains_east_asian_text(source_label)
        ):
            issues.append(
                SpecMasterAuditIssue(
                    code="ROW_LABEL_SOURCE_CONTAINS_EAST_ASIAN_TEXT",
                    message=(
                        "`Row_label_source` contains East Asian text for row "
                        f"(region `{(region or '').strip().upper()}`) whose declared source language is "
                        f"`{source_language_for_row(row) or 'unknown'}`: {source_label}"
                    ),
                    line=line_number,
                    model=model,
                    region=region,
                    section=section,
                    row_key=row_key,
                )
            )

        raw_slot_key = _first_non_empty(row, ["Slot_key", "slot_key"])
        if raw_slot_key and _parse_slot_key(raw_slot_key) is None:
            issues.append(
                SpecMasterAuditIssue(
                    code="INVALID_SLOT_KEY",
                    message=(
                        f"`Slot_key` must use `role`, `placement.role`, or "
                        f"`placement.variant.role`: {raw_slot_key}"
                    ),
                    line=line_number,
                    model=model,
                    region=region,
                    section=section,
                    row_key=row_key,
                )
            )

        source_value = _pick_source_value(row, "Value")
        if _is_template_row(row_key, section, row) and "?" in source_value:
            issues.append(
                SpecMasterAuditIssue(
                    code="SUSPECT_TEMPLATE_VALUE",
                    message=f"Template value contains literal `?`: {source_value}",
                    line=line_number,
                    model=model,
                    region=region,
                    section=section,
                    row_key=row_key,
                )
            )

        normalized_items = tuple(sorted((key, row.get(key, "")) for key in row if key != "__line__"))
        previous_line = seen_rows.get(normalized_items)
        if previous_line is not None:
            issues.append(
                SpecMasterAuditIssue(
                    code="EXACT_DUPLICATE_ROW",
                    message=f"Row duplicates line {previous_line}",
                    line=line_number,
                    model=model,
                    region=region,
                    section=section,
                    row_key=row_key,
                )
            )
        else:
            seen_rows[normalized_items] = line_number

    issues.sort(
        key=lambda item: (
            item.code,
            item.line if item.line is not None else -1,
            item.section or "",
            item.row_key or "",
        )
    )

    return SpecMasterAuditResult(
        total_rows=len(rows),
        unique_sections=len(section_summaries),
        section_summaries=tuple(section_summaries),
        order_conflicts=tuple(order_conflicts),
        issues=tuple(issues),
    )


def audit_spec_master_csv(spec_master_csv: Path) -> SpecMasterAuditResult:
    return audit_spec_master_rows(read_spec_master_rows(spec_master_csv))


def _row_issue_map(issues: tuple[SpecMasterAuditIssue, ...]) -> dict[int, list[SpecMasterAuditIssue]]:
    issue_map: dict[int, list[SpecMasterAuditIssue]] = defaultdict(list)
    for issue in issues:
        if issue.line is None:
            continue
        issue_map[issue.line].append(issue)
    return issue_map


def normalize_spec_master_rows(rows: list[dict[str, str]]) -> SpecMasterNormalizationResult:
    audit = audit_spec_master_rows(rows)
    issue_map = _row_issue_map(audit.issues)
    conflicting_orders = {conflict.section_order for conflict in audit.order_conflicts}

    normalized_rows: list[dict[str, str]] = []
    anomaly_rows: list[dict[str, str]] = []

    for idx, raw_row in enumerate(rows):
        row = {key: value for key, value in raw_row.items() if key != "__line__"}
        line_number = str(_row_line_num(raw_row, idx))
        original_section = _pick_section(raw_row)
        normalized_section, category, note = _normalize_section_summary(original_section)
        row_key = _pick_row_key(raw_row)

        if _is_template_row(row_key, original_section, raw_row):
            category = "template"
            if not note:
                note = "Template placeholder row should remain distinguishable even when grouped under a mapped section."

        review_flags: list[str] = []
        review_messages: list[str] = []

        if original_section != normalized_section:
            review_flags.append("SECTION_NORMALIZED")
            review_messages.append(
                f"Section normalized from `{original_section}` to `{normalized_section}`"
            )
        if category == "template":
            review_flags.append("TEMPLATE_RECORD")
            review_messages.append(
                "Template placeholder row is kept in the derived output but should be split from the spec source."
            )
        section_order = _pick_section_order(raw_row)
        if section_order and section_order in conflicting_orders:
            review_flags.append("SECTION_ORDER_COLLISION")
            review_messages.append(
                f"Section_order `{section_order}` is shared by multiple sections."
            )
        for issue in issue_map.get(int(line_number), []):
            review_flags.append(issue.code)
            review_messages.append(issue.message)

        deduped_flags = list(dict.fromkeys(review_flags))
        deduped_messages = list(dict.fromkeys(review_messages))

        normalized_row = dict(row)
        normalized_row["Section_original"] = original_section
        normalized_row["Section"] = normalized_section
        normalized_row["Section_normalized"] = normalized_section
        normalized_row["Record_category"] = category
        normalized_row["Normalization_applied"] = "YES" if original_section != normalized_section else "NO"
        normalized_row["Normalization_note"] = note
        normalized_row["Source_line"] = line_number
        normalized_row["Review_flags"] = ";".join(deduped_flags)
        normalized_row["Review_messages"] = " | ".join(deduped_messages)
        normalized_rows.append(normalized_row)

        if deduped_flags:
            anomaly_rows.append(normalized_row)

    return SpecMasterNormalizationResult(
        normalized_rows=tuple(normalized_rows),
        anomaly_rows=tuple(anomaly_rows),
    )


def normalize_spec_master_csv(spec_master_csv: Path) -> SpecMasterNormalizationResult:
    return normalize_spec_master_rows(read_spec_master_rows(spec_master_csv))
