#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any


def audit_spec_master_rows(module: Any, rows: list[dict[str, str]]) -> Any:
    section_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    order_map: dict[str, set[str]] = defaultdict(set)
    issues: list[Any] = []

    for row in rows:
        section = module._pick_section(row)
        if section:
            section_groups[section].append(row)
            order_value = module._pick_section_order(row)
            if order_value:
                order_map[order_value].add(section)

    order_conflicts: list[Any] = []
    for order_value in module._sort_text_numbers(set(order_map)):
        sections = tuple(sorted(order_map[order_value]))
        if len(sections) <= 1:
            continue
        order_conflicts.append(
            module.SpecMasterSectionOrderConflict(
                section_order=order_value,
                sections=sections,
            )
        )
        issues.append(
            module.SpecMasterAuditIssue(
                code="SECTION_ORDER_COLLISION",
                message=f"`Section_order` {order_value} is shared by: {', '.join(sections)}",
                line=None,
                model=None,
                region=None,
                section=None,
                row_key=None,
            )
        )

    section_summaries: list[Any] = []
    for section in sorted(section_groups):
        group_rows = section_groups[section]
        suggested_section, category, note = module._normalize_section_summary(section)
        orders = module._sort_text_numbers({module._pick_section_order(row) for row in group_rows})
        models = tuple(sorted({value for row in group_rows if (value := module._pick_row_model(row))}))
        regions = tuple(sorted({value for row in group_rows if (value := module._pick_row_region(row))}))
        section_summaries.append(
            module.SpecMasterSectionSummary(
                section=section,
                suggested_section=suggested_section,
                category=category,
                row_count=len(group_rows),
                orders=orders,
                models=models,
                regions=regions,
                note=note,
            )
        )

    seen_rows: dict[tuple[tuple[str, str], ...], int] = {}
    for idx, row in enumerate(rows):
        line_number = module._row_line_num(row, idx)
        model = module._pick_row_model(row) or None
        region = module._pick_row_region(row) or None
        section = module._pick_section(row) or None
        row_key = module._pick_row_key(row) or None
        source_label = module._pick_row_label_source(row)

        if (
            source_label
            and module._source_language_uses_latin_script(module.source_language_for_row(row))
            and module._contains_east_asian_text(source_label)
        ):
            issues.append(
                module.SpecMasterAuditIssue(
                    code="ROW_LABEL_SOURCE_CONTAINS_EAST_ASIAN_TEXT",
                    message=(
                        "`Row_label_source` contains East Asian text for row "
                        f"(region `{(region or '').strip().upper()}`) whose declared source language is "
                        f"`{module.source_language_for_row(row) or 'unknown'}`: {source_label}"
                    ),
                    line=line_number,
                    model=model,
                    region=region,
                    section=section,
                    row_key=row_key,
                )
            )

        raw_slot_key = module._first_non_empty(row, ["Slot_key", "slot_key"])
        if raw_slot_key and module._parse_slot_key(raw_slot_key) is None:
            issues.append(
                module.SpecMasterAuditIssue(
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

        source_value = module._pick_source_value(row, "Value")
        if module._is_template_row(row_key or "", section or "", row) and "?" in source_value:
            issues.append(
                module.SpecMasterAuditIssue(
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
                module.SpecMasterAuditIssue(
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

    return module.SpecMasterAuditResult(
        total_rows=len(rows),
        unique_sections=len(section_summaries),
        section_summaries=tuple(section_summaries),
        order_conflicts=tuple(order_conflicts),
        issues=tuple(issues),
    )


def audit_spec_master_csv(module: Any, spec_master_csv: Path) -> Any:
    return audit_spec_master_rows(module, module.read_spec_master_rows(spec_master_csv))


def _row_issue_map(module: Any, issues: tuple[Any, ...]) -> dict[int, list[Any]]:
    issue_map: dict[int, list[Any]] = defaultdict(list)
    for issue in issues:
        if issue.line is None:
            continue
        issue_map[issue.line].append(issue)
    return issue_map


def normalize_spec_master_rows(module: Any, rows: list[dict[str, str]]) -> Any:
    audit = module.audit_spec_master_rows(rows)
    issue_map = _row_issue_map(module, audit.issues)
    conflicting_orders = {conflict.section_order for conflict in audit.order_conflicts}

    normalized_rows: list[dict[str, str]] = []
    anomaly_rows: list[dict[str, str]] = []

    for idx, raw_row in enumerate(rows):
        row = {key: value for key, value in raw_row.items() if key != "__line__"}
        line_number = str(module._row_line_num(raw_row, idx))
        original_section = module._pick_section(raw_row)
        normalized_section, category, note = module._normalize_section_summary(original_section)
        row_key = module._pick_row_key(raw_row)

        if module._is_template_row(row_key, original_section, raw_row):
            category = "template"
            if not note:
                note = "Template placeholder row should remain distinguishable even when grouped under a mapped section."

        review_flags: list[str] = []
        review_messages: list[str] = []

        if original_section != normalized_section:
            review_flags.append("SECTION_NORMALIZED")
            review_messages.append(f"Section normalized from `{original_section}` to `{normalized_section}`")
        if category == "template":
            review_flags.append("TEMPLATE_RECORD")
            review_messages.append(
                "Template placeholder row is kept in the derived output but should be split from the spec source."
            )
        section_order = module._pick_section_order(raw_row)
        if section_order and section_order in conflicting_orders:
            review_flags.append("SECTION_ORDER_COLLISION")
            review_messages.append(f"Section_order `{section_order}` is shared by multiple sections.")
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

    return module.SpecMasterNormalizationResult(
        normalized_rows=tuple(normalized_rows),
        anomaly_rows=tuple(anomaly_rows),
    )


def normalize_spec_master_csv(module: Any, spec_master_csv: Path) -> Any:
    return normalize_spec_master_rows(module, module.read_spec_master_rows(spec_master_csv))
