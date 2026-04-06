
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path

from tools.utils.spec_master_lookup import read_spec_master_rows
from tools.utils.spec_master_row_helpers import (
    _normalize_section_summary,
    _page_value_metadata_from_row,
    _pick_row_key,
    _pick_row_label_source,
    _pick_row_model,
    _pick_row_region,
    _row_line_num,
    _set_source_value,
    _source_column_name,
    resolve_legacy_page_value_key,
)
from tools.utils.spec_master_shared import (
    SpecMasterAppliedRepair,
    SpecMasterRepairResult,
    _KNOWN_ROW_LABEL_REPAIRS,
    _KNOWN_VALUE_REPAIRS,
)

def repair_known_spec_master_values(rows: list[dict[str, str]]) -> SpecMasterRepairResult:
    repaired_rows: list[dict[str, str]] = []
    applied_repairs: list[SpecMasterAppliedRepair] = []

    for idx, raw_row in enumerate(rows):
        row = dict(raw_row)
        line_number = _row_line_num(raw_row, idx)
        model = _pick_row_model(row)
        region = _pick_row_region(row)
        row_key = _pick_row_key(row)
        template_metadata = _page_value_metadata_from_row(row)

        old_section = row.get("Section", "")
        new_section, _, _ = _normalize_section_summary(old_section)
        if old_section != new_section:
            row["Section"] = new_section
            applied_repairs.append(
                SpecMasterAppliedRepair(
                    line=line_number,
                    model=model or None,
                    region=region or None,
                    row_key=row_key or None,
                    column="Section",
                    old_value=old_section,
                    new_value=new_section,
                )
            )

        if template_metadata is not None:
            mapped_section, mapped_section_order, mapped_row_label = template_metadata

            if row.get("Section", "") != mapped_section:
                applied_repairs.append(
                    SpecMasterAppliedRepair(
                        line=line_number,
                        model=model or None,
                        region=region or None,
                        row_key=row_key or None,
                        column="Section",
                        old_value=row.get("Section", ""),
                        new_value=mapped_section,
                    )
                )
                row["Section"] = mapped_section

            old_section_order = row.get("Section_order", "")
            if old_section_order != mapped_section_order:
                row["Section_order"] = mapped_section_order
                applied_repairs.append(
                    SpecMasterAppliedRepair(
                        line=line_number,
                        model=model or None,
                        region=region or None,
                        row_key=row_key or None,
                        column="Section_order",
                        old_value=old_section_order,
                        new_value=mapped_section_order,
                    )
                )

            source_label_column = _source_column_name(row, "Row_label")
            old_template_label = _pick_row_label_source(row)
            if old_template_label != mapped_row_label:
                _set_source_value(row, "Row_label", mapped_row_label)
                applied_repairs.append(
                    SpecMasterAppliedRepair(
                        line=line_number,
                        model=model or None,
                        region=region or None,
                        row_key=row_key or None,
                        column=source_label_column,
                        old_value=old_template_label,
                        new_value=mapped_row_label,
                    )
                )

        source_label_column = _source_column_name(row, "Row_label")
        old_label = _pick_row_label_source(row)
        new_label = _KNOWN_ROW_LABEL_REPAIRS.get(old_label.strip())
        if new_label is not None and old_label != new_label:
            _set_source_value(row, "Row_label", new_label)
            applied_repairs.append(
                SpecMasterAppliedRepair(
                    line=line_number,
                    model=model or None,
                    region=region or None,
                    row_key=row_key or None,
                    column=source_label_column,
                    old_value=old_label,
                    new_value=new_label,
                )
            )

        value_columns = ((_source_column_name(row, "Value"), "Value_source"),)
        for column, repair_column in value_columns:
            repair_lookup_row_key = resolve_legacy_page_value_key(row) or row_key
            repair_key = (model, region, repair_lookup_row_key, repair_column)
            new_value = _KNOWN_VALUE_REPAIRS.get(repair_key)
            if new_value is None:
                continue
            old_value = row.get(column, "")
            if old_value == new_value:
                continue
            row[column] = new_value
            applied_repairs.append(
                SpecMasterAppliedRepair(
                    line=line_number,
                    model=model or None,
                    region=region or None,
                    row_key=row_key or None,
                    column=column,
                    old_value=old_value,
                    new_value=new_value,
                )
            )

        repaired_rows.append(row)

    deduped_rows: list[dict[str, str]] = []
    removed_duplicate_lines: list[int] = []
    seen_rows: set[tuple[tuple[str, str], ...]] = set()
    for idx, row in enumerate(repaired_rows):
        normalized_items = tuple(sorted((key, value) for key, value in row.items() if key != "__line__"))
        if normalized_items in seen_rows:
            removed_duplicate_lines.append(_row_line_num(row, idx))
            continue
        seen_rows.add(normalized_items)
        deduped_rows.append(row)

    return SpecMasterRepairResult(
        repaired_rows=tuple(deduped_rows),
        applied_repairs=tuple(applied_repairs),
        removed_duplicate_lines=tuple(removed_duplicate_lines),
    )


def repair_known_spec_master_csv(spec_master_csv: Path) -> SpecMasterRepairResult:
    return repair_known_spec_master_values(read_spec_master_rows(spec_master_csv))
