#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from collections import defaultdict
from typing import Any, cast


def build_template_row_key_mapping_rows(
    module: Any,
    rows: list[dict[str, str]],
) -> tuple[dict[str, str], ...]:
    usage: dict[str, dict[str, object]] = defaultdict(
        lambda: {
            "count": 0,
            "models": set(),
            "regions": set(),
            "sections": set(),
            "section_orders": set(),
            "row_labels": set(),
        }
    )

    for raw_row in rows:
        row_key = module._pick_row_key(raw_row)
        if not module._is_template_row(row_key, module._pick_section(raw_row), raw_row):
            continue

        metadata = module._page_value_metadata_from_row(raw_row)
        if metadata is None:
            continue

        usage_row = usage[module.resolve_legacy_page_value_key(raw_row) or row_key]
        usage_row["count"] = int(usage_row["count"]) + 1

        model = (module._pick_row_model(raw_row) or "").strip()
        if model:
            cast(set[str], usage_row["models"]).add(model)

        region = (module._pick_row_region(raw_row) or "").strip().upper()
        if region:
            cast(set[str], usage_row["regions"]).add(region)

        section = module._pick_section(raw_row).strip()
        if section:
            cast(set[str], usage_row["sections"]).add(section)

        section_order = module._pick_section_order(raw_row).strip()
        if section_order:
            cast(set[str], usage_row["section_orders"]).add(section_order)

        row_label = module._pick_row_label_source(raw_row).strip()
        if row_label:
            cast(set[str], usage_row["row_labels"]).add(row_label)

    mapping_rows: list[dict[str, str]] = []
    for row_key, binding in module._LEGACY_PAGE_VALUE_BINDINGS.items():
        observed = usage.get(row_key)
        models = sorted(cast(set[str], observed["models"])) if observed else []
        regions = sorted(cast(set[str], observed["regions"])) if observed else []
        sections = sorted(cast(set[str], observed["sections"])) if observed else []
        section_orders = sorted(cast(set[str], observed["section_orders"])) if observed else []
        row_labels = sorted(cast(set[str], observed["row_labels"])) if observed else []
        usage_count = str(int(observed["count"])) if observed else "0"

        mapping_rows.append(
            {
                "Row_key": row_key,
                "Section": binding.section,
                "Section_order": binding.section_order,
                "Row_label_source": binding.row_label_source,
                "Usage_count": usage_count,
                "Models": ",".join(models),
                "Regions": ",".join(regions),
                "Observed_sections": ",".join(sections),
                "Observed_section_orders": ",".join(section_orders),
                "Observed_row_labels_source": " | ".join(row_labels),
            }
        )

    return tuple(
        sorted(
            mapping_rows,
            key=lambda row: (
                int(row["Section_order"]),
                row["Section"],
                row["Row_label_source"],
                row["Row_key"],
            ),
        )
    )


def build_row_label_row_key_mapping_rows(
    module: Any,
    rows: list[dict[str, str]],
    existing_rows: list[dict[str, str]] | None = None,
) -> tuple[dict[str, str], ...]:
    observed_keys: dict[tuple[str, str], set[str]] = defaultdict(set)

    for raw_row in rows:
        if not module._is_truthy(module._first_non_empty(raw_row, ["Is_Latest", "is_latest"])):
            continue

        row_label = module._pick_row_label_source(raw_row).strip()
        if not row_label:
            continue

        line_order = module._normalize_line_order_suffix(
            module._first_non_empty(raw_row, ["Line_order", "line_order"])
        )
        row_key = module._pick_row_key(raw_row).strip()
        if row_key:
            observed_keys[(row_label, line_order)].add(row_key)

    existing_by_pair: dict[tuple[str, str], dict[str, str]] = {}
    existing_by_label: dict[str, dict[str, str]] = {}
    for raw_row in existing_rows or []:
        row_label = (raw_row.get("Row_label_source") or "").strip()
        if not row_label:
            continue

        line_order = (raw_row.get("Line_order") or "").strip()
        record = {
            "Row_key": (raw_row.get("Row_key") or "").strip(),
            "Remark": (raw_row.get("Remark") or "").strip(),
        }
        if line_order:
            existing_by_pair[(row_label, line_order)] = record
        else:
            existing_by_label[row_label] = record

    mapping_rows: list[dict[str, str]] = []
    observed_pairs = set(observed_keys)
    observed_labels = {row_label for row_label, _line_order in observed_pairs}
    observed_pairs.update(existing_by_pair)
    observed_pairs.update((row_label, "") for row_label in existing_by_label if row_label not in observed_labels)

    def _line_order_sort_key(value: str) -> tuple[int, str]:
        if value.isdigit():
            return (0, f"{int(value):08d}")
        if not value:
            return (1, "")
        return (2, value)

    for row_label, line_order in sorted(
        observed_pairs,
        key=lambda item: (item[0], _line_order_sort_key(item[1])),
    ):
        existing_row = existing_by_pair.get((row_label, line_order), {})
        fallback_row = existing_by_label.get(row_label, {})
        row_key = existing_row.get("Row_key", "").strip()
        if not row_key:
            row_key = fallback_row.get("Row_key", "").strip()
        if not row_key:
            candidate_row_keys = sorted(observed_keys.get((row_label, line_order), set()))
            if candidate_row_keys:
                row_key = candidate_row_keys[0]

        mapping_rows.append(
            {
                "Row_label_source": row_label,
                "Line_order": line_order,
                "Row_key": row_key,
                "Remark": existing_row.get("Remark", "").strip()
                or fallback_row.get("Remark", "").strip(),
            }
        )

    return tuple(mapping_rows)


def build_row_label_row_key_mapping_markdown(
    _module: Any,
    mapping_rows: tuple[dict[str, str], ...],
) -> str:
    lines = [
        "# Spec Master Row Label to Row Key Mapping",
        "",
        "Manual mapping reference for `Spec_Master.csv` `Row_label_source + Line_order` to `Row_key` lookup.",
        "",
        "| Row_label_source | Line_order | Row_key | Remark |",
        "| --- | ---: | --- | --- |",
    ]

    for row in mapping_rows:
        lines.append(
            "| {row_label} | {line_order} | {row_key} | {remark} |".format(
                row_label=row["Row_label_source"],
                line_order=row["Line_order"] or "-",
                row_key=row["Row_key"],
                remark=row["Remark"] or "-",
            )
        )

    lines.append("")
    return "\n".join(lines)


def build_template_row_key_mapping_markdown(
    _module: Any,
    mapping_rows: tuple[dict[str, str], ...],
) -> str:
    lines = [
        "# Spec Master Row Key Mapping",
        "",
        "Grouped canonical mapping for template-style `row_key` values.",
        "",
    ]

    grouped_rows: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in mapping_rows:
        grouped_rows[(row["Section_order"], row["Section"])].append(row)

    for section_order, section in sorted(grouped_rows, key=lambda item: (int(item[0]), item[1])):
        rows_in_section = sorted(
            grouped_rows[(section_order, section)],
            key=lambda row: (row["Row_label_source"], row["Row_key"]),
        )
        lines.extend(
            [
                f"## {section} (`{section_order}`)",
                "",
                "| Row_key | Row_label_source | Usage_count | Models | Regions |",
                "| --- | --- | ---: | --- | --- |",
            ]
        )
        for row in rows_in_section:
            lines.append(
                "| {row_key} | {row_label} | {usage} | {models} | {regions} |".format(
                    row_key=row["Row_key"],
                    row_label=row["Row_label_source"],
                    usage=row["Usage_count"],
                    models=row["Models"] or "-",
                    regions=row["Regions"] or "-",
                )
            )
        lines.append("")

    return "\n".join(lines).strip() + "\n"
