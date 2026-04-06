#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
from typing import Any


def repair_known_spec_master_values(module: Any, rows: list[dict[str, str]]) -> Any:
    repaired_rows: list[dict[str, str]] = []
    applied_repairs: list[Any] = []

    for idx, raw_row in enumerate(rows):
        row = dict(raw_row)
        line_number = module._row_line_num(raw_row, idx)
        model = module._pick_row_model(row)
        region = module._pick_row_region(row)
        row_key = module._pick_row_key(row)
        template_metadata = module._page_value_metadata_from_row(row)

        old_section = row.get("Section", "")
        new_section, _, _ = module._normalize_section_summary(old_section)
        if old_section != new_section:
            row["Section"] = new_section
            applied_repairs.append(
                module.SpecMasterAppliedRepair(
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
                    module.SpecMasterAppliedRepair(
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
                    module.SpecMasterAppliedRepair(
                        line=line_number,
                        model=model or None,
                        region=region or None,
                        row_key=row_key or None,
                        column="Section_order",
                        old_value=old_section_order,
                        new_value=mapped_section_order,
                    )
                )

            source_label_column = module._source_column_name(row, "Row_label")
            old_template_label = module._pick_row_label_source(row)
            if old_template_label != mapped_row_label:
                module._set_source_value(row, "Row_label", mapped_row_label)
                applied_repairs.append(
                    module.SpecMasterAppliedRepair(
                        line=line_number,
                        model=model or None,
                        region=region or None,
                        row_key=row_key or None,
                        column=source_label_column,
                        old_value=old_template_label,
                        new_value=mapped_row_label,
                    )
                )

        source_label_column = module._source_column_name(row, "Row_label")
        old_label = module._pick_row_label_source(row)
        new_label = module._KNOWN_ROW_LABEL_REPAIRS.get(old_label.strip())
        if new_label is not None and old_label != new_label:
            module._set_source_value(row, "Row_label", new_label)
            applied_repairs.append(
                module.SpecMasterAppliedRepair(
                    line=line_number,
                    model=model or None,
                    region=region or None,
                    row_key=row_key or None,
                    column=source_label_column,
                    old_value=old_label,
                    new_value=new_label,
                )
            )

        value_columns = ((module._source_column_name(row, "Value"), "Value_source"),)
        for column, repair_column in value_columns:
            repair_lookup_row_key = module.resolve_legacy_page_value_key(row) or row_key
            repair_key = (model, region, repair_lookup_row_key, repair_column)
            new_value = module._KNOWN_VALUE_REPAIRS.get(repair_key)
            if new_value is None:
                continue
            old_value = row.get(column, "")
            if old_value == new_value:
                continue
            row[column] = new_value
            applied_repairs.append(
                module.SpecMasterAppliedRepair(
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
            removed_duplicate_lines.append(module._row_line_num(row, idx))
            continue
        seen_rows.add(normalized_items)
        deduped_rows.append(row)

    return module.SpecMasterRepairResult(
        repaired_rows=tuple(deduped_rows),
        applied_repairs=tuple(applied_repairs),
        removed_duplicate_lines=tuple(removed_duplicate_lines),
    )


def repair_known_spec_master_csv(module: Any, spec_master_csv: Path) -> Any:
    return repair_known_spec_master_values(module, module.read_spec_master_rows(spec_master_csv))
