from __future__ import annotations

import re
from pathlib import Path

from tools.diff_report_fields_extract import _build_field_entries
from tools.diff_report_fields_shared import (
    _clean_field_text,
    derive_label_lower,
    derive_short_product_name,
    first_non_empty,
    is_truthy,
    load_spec_title_map,
    pick_lang_value,
    read_csv_rows,
)
from tools.diff_report_models import PlaceholderValueSource, SpecFieldSource
from tools.utils.spec_master import (
    is_page_value_row,
    page_value_matches,
    page_value_role,
    resolve_legacy_page_value_key,
)


def build_spec_source_lookup(
    *,
    spec_master_csv: Path,
    spec_titles_csv: Path | None,
    model: str,
    region: str,
    lang: str,
) -> dict[tuple[str, str], SpecFieldSource]:
    rows = read_csv_rows(spec_master_csv)
    if not rows:
        return {}

    title_map = load_spec_title_map(spec_titles_csv, lang=lang)
    filtered: list[dict[str, str]] = []
    for row in rows:
        if not is_truthy(first_non_empty(row, ["enabled", "Enabled"])):
            continue
        if not is_truthy(first_non_empty(row, ["Is_Latest", "is_latest"])):
            continue
        page = first_non_empty(row, ["Page", "page"])
        if not page_value_matches(page, ("spec", "specifications")):
            continue
        row_model = first_non_empty(row, ["Model", "model", "Product_Model", "product_model", "Model_No", "model_no"])
        row_region = first_non_empty(row, ["Region", "region"])
        if model and row_model and row_model != model:
            continue
        if region and row_region and row_region != region:
            continue
        row_key = first_non_empty(row, ["Row_key", "row_key"])
        section_key = first_non_empty(row, ["Section", "section"])
        if not row_key or not section_key:
            continue
        if is_page_value_row(row) or section_key.strip().lower() == "template vars":
            continue
        filtered.append(row)

    grouped: dict[tuple[str, str], dict[str, object]] = {}
    for idx, row in enumerate(filtered):
        section_key = first_non_empty(row, ["Section", "section"])
        row_key = first_non_empty(row, ["Row_key", "row_key"])
        section_title = pick_lang_value(
            row,
            "section_title",
            lang,
            default_keys=[f"Section_{lang}", "Section_en", "Section"],
        ) or section_key
        rendered_section_title = title_map.get(_clean_field_text(section_title), _clean_field_text(section_title))
        row_label = pick_lang_value(row, "Row_label", lang, default_keys=["Row_label_source", "Row_key"]) or row_key

        value = pick_lang_value(row, "line_text", lang)
        if not value:
            param = pick_lang_value(row, "Param", lang, default_keys=["Param_source", "Param_name"])
            spec_value = pick_lang_value(row, "Value", lang, default_keys=["Value_source", "Spec_Value"])
            sep = pick_lang_value(row, "param_value_sep", lang, default_keys=["param_value_sep"]) or ": "
            if sep == ":":
                sep = ": "
            if param and spec_value:
                value = f"{param}{sep}{spec_value}"
            else:
                value = spec_value or param
        if not value:
            continue

        key = (section_key, row_key)
        entry = grouped.setdefault(
            key,
            {
                "section_title": rendered_section_title,
                "field_key": _clean_field_text(row_label),
                "source_section_key": section_key,
                "source_row_key": row_key,
                "source_csv_line": first_non_empty(row, ["__line__"]),
                "values": [],
            },
        )
        values = entry["values"]
        assert isinstance(values, list)
        line_order = first_non_empty(row, ["Line_order", "line_order"]) or str(idx + 1)
        sort_order = float(line_order.replace(",", ".")) if re.fullmatch(r"[0-9.]+", line_order) else float(idx + 1)
        values.append((sort_order, line_order, _clean_field_text(value)))

    seen: dict[tuple[str, str], int] = {}
    lookup: dict[tuple[str, str], SpecFieldSource] = {}
    for section_key, row_key in sorted(grouped, key=lambda item: (str(item[0]), str(item[1]))):
        entry = grouped[(section_key, row_key)]
        values = entry["values"]
        assert isinstance(values, list)
        sorted_values = [item[2] for item in sorted(values, key=lambda item: item[0])]
        line_orders = [item[1] for item in sorted(values, key=lambda item: item[0])]
        field_entry = _build_field_entries(
            str(entry["section_title"]),
            str(entry["field_key"]),
            " / ".join(value for value in sorted_values if value),
            seen=seen,
        )
        if field_entry is None:
            continue
        lookup[(field_entry.section_title, field_entry.field_key)] = SpecFieldSource(
            section_title=field_entry.section_title,
            field_key=field_entry.field_key,
            source_section_key=str(entry["source_section_key"]),
            source_row_key=str(entry["source_row_key"]),
            source_line_order="|".join(line_orders),
            source_csv_line=str(entry["source_csv_line"]),
        )
    return lookup


def build_placeholder_source_lookup(
    *,
    spec_master_csv: Path,
    model: str,
    region: str,
    lang: str,
) -> dict[str, list[PlaceholderValueSource]]:
    rows = read_csv_rows(spec_master_csv)
    if not rows:
        return {}

    lookup: dict[str, list[PlaceholderValueSource]] = {}
    for idx, row in enumerate(rows):
        if not is_truthy(first_non_empty(row, ["enabled", "Enabled"])):
            continue
        if not is_truthy(first_non_empty(row, ["Is_Latest", "is_latest"])):
            continue
        row_model = first_non_empty(row, ["Model", "model", "Product_Model", "product_model", "Model_No", "model_no"])
        row_region = first_non_empty(row, ["Region", "region"])
        if model and row_model and row_model != model:
            continue
        if region and row_region and row_region != region:
            continue

        row_key = first_non_empty(row, ["Row_key", "row_key"])
        if not row_key:
            continue
        if row_key.lower() not in {"product_name", "model_no"} and not is_page_value_row(row):
            continue

        raw_value = pick_lang_value(row, "Value", lang, default_keys=["Value_source", "Spec_Value"])
        if not raw_value:
            continue

        line_order = first_non_empty(row, ["Line_order", "line_order"]) or str(idx + 1)
        source_row_key = resolve_legacy_page_value_key(row) or row_key
        base_source = PlaceholderValueSource(
            match_value="",
            source_section_key=first_non_empty(row, ["Section", "section"]),
            source_row_key=source_row_key,
            source_line_order=line_order,
            source_csv_line=first_non_empty(row, ["__line__"]),
        )

        candidate_values = [raw_value]
        lowered_row_key = row_key.lower()
        if lowered_row_key == "product_name":
            short_name = derive_short_product_name(raw_value)
            if short_name and short_name != raw_value:
                candidate_values.append(short_name)
        if page_value_role(row) == "label":
            lower_value = derive_label_lower(raw_value)
            if lower_value and lower_value != raw_value:
                candidate_values.append(lower_value)

        for candidate in candidate_values:
            normalized = _clean_field_text(candidate).lower()
            if not normalized:
                continue
            entry = PlaceholderValueSource(
                match_value=normalized,
                source_section_key=base_source.source_section_key,
                source_row_key=base_source.source_row_key,
                source_line_order=base_source.source_line_order,
                source_csv_line=base_source.source_csv_line,
            )
            existing = lookup.setdefault(normalized, [])
            if entry not in existing:
                existing.append(entry)
    return lookup


def match_placeholder_sources(
    *,
    field_key: str,
    old_value: str,
    new_value: str,
    placeholder_lookup: dict[str, list[PlaceholderValueSource]],
) -> list[PlaceholderValueSource]:
    search_texts = [
        _clean_field_text(field_key).lower(),
        _clean_field_text(old_value).lower(),
        _clean_field_text(new_value).lower(),
    ]
    matches: list[tuple[int, PlaceholderValueSource]] = []
    seen: set[tuple[str, str, str, str]] = set()

    for normalized_value, sources in placeholder_lookup.items():
        if not normalized_value:
            continue
        if not any(normalized_value in text for text in search_texts if text):
            continue
        for source in sources:
            dedupe_key = (
                source.source_section_key,
                source.source_row_key,
                source.source_line_order,
                source.source_csv_line,
            )
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            matches.append((len(normalized_value), source))

    matches.sort(
        key=lambda item: (
            -item[0],
            item[1].source_section_key,
            item[1].source_row_key,
            item[1].source_line_order,
            item[1].source_csv_line,
        )
    )
    return [item[1] for item in matches]


def merge_sources(sources: list[PlaceholderValueSource | SpecFieldSource]) -> tuple[str, str, str, str]:
    if not sources:
        return "", "", "", ""

    section_keys: list[str] = []
    row_keys: list[str] = []
    line_orders: list[str] = []
    csv_lines: list[str] = []
    seen_sections: set[str] = set()
    seen_rows: set[str] = set()
    seen_line_orders: set[str] = set()
    seen_csv_lines: set[str] = set()

    for source in sources:
        if source.source_section_key and source.source_section_key not in seen_sections:
            seen_sections.add(source.source_section_key)
            section_keys.append(source.source_section_key)
        if source.source_row_key and source.source_row_key not in seen_rows:
            seen_rows.add(source.source_row_key)
            row_keys.append(source.source_row_key)
        if source.source_line_order and source.source_line_order not in seen_line_orders:
            seen_line_orders.add(source.source_line_order)
            line_orders.append(source.source_line_order)
        if source.source_csv_line and source.source_csv_line not in seen_csv_lines:
            seen_csv_lines.add(source.source_csv_line)
            csv_lines.append(source.source_csv_line)

    return "; ".join(section_keys), "; ".join(row_keys), "; ".join(line_orders), "; ".join(csv_lines)
