#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
from typing import Any


def resolve_spec_value_from_rows(
    module: Any,
    rows: list[dict[str, str]],
    *,
    model: str | None,
    region: str | None,
    lang: str,
    row_key: str,
    pages: str | list[str] | tuple[str, ...] | set[str] | None = ("spec", "specifications"),
    line_order: str | int | None = None,
    usage_type: str | None = None,
    placement_key: str | None = None,
    value_role: str | None = None,
    variant_key: str | None = None,
) -> Any | None:
    for row in module._iter_ranked_rows(
        rows,
        model=model,
        region=region,
        lang=lang,
        row_key=row_key,
        pages=pages,
        line_order=line_order,
        usage_type=usage_type,
        placement_key=placement_key,
        value_role=value_role,
        variant_key=variant_key,
    ):
        value = module._pick_lang_value(row, "Value", lang)
        if value:
            return module.SpecValueMatch(
                value=value,
                region=module._pick_row_region(row) or None,
                row=row,
            )
    return None


def collect_matching_spec_rows(
    module: Any,
    rows: list[dict[str, str]],
    *,
    model: str | None,
    region: str | None,
    lang: str,
    row_key: str,
    pages: str | list[str] | tuple[str, ...] | set[str] | None = ("spec", "specifications"),
    line_order: str | int | None = None,
    usage_type: str | None = None,
    placement_key: str | None = None,
    value_role: str | None = None,
    variant_key: str | None = None,
) -> tuple[dict[str, str], ...]:
    return tuple(
        module._iter_ranked_rows(
            rows,
            model=model,
            region=region,
            lang=lang,
            row_key=row_key,
            pages=pages,
            line_order=line_order,
            usage_type=usage_type,
            placement_key=placement_key,
            value_role=value_role,
            variant_key=variant_key,
        )
    )


def collect_spec_value_matches_from_rows(
    module: Any,
    rows: list[dict[str, str]],
    *,
    model: str | None,
    region: str | None,
    lang: str,
    row_key: str,
    pages: str | list[str] | tuple[str, ...] | set[str] | None = ("spec", "specifications"),
    line_order: str | int | None = None,
    usage_type: str | None = None,
    placement_key: str | None = None,
    value_role: str | None = None,
    variant_key: str | None = None,
) -> tuple[Any, ...]:
    matches: list[Any] = []
    for row in collect_matching_spec_rows(
        module,
        rows,
        model=model,
        region=region,
        lang=lang,
        row_key=row_key,
        pages=pages,
        line_order=line_order,
        usage_type=usage_type,
        placement_key=placement_key,
        value_role=value_role,
        variant_key=variant_key,
    ):
        value = module._pick_lang_value(row, "Value", lang)
        if not value:
            continue
        matches.append(
            module.SpecValueMatch(
                value=value,
                region=module._pick_row_region(row) or None,
                row=row,
            )
        )
    return tuple(matches)


def resolve_template_substitutions_from_rows(
    module: Any,
    rows: list[dict[str, str]],
    *,
    model: str | None,
    region: str | None,
    lang: str,
) -> dict[str, str]:
    substitutions: dict[str, str] = {}

    product_match = module.resolve_spec_value_from_rows(
        rows,
        model=model,
        region=region,
        lang=lang,
        row_key="product_name",
        pages=None,
    )
    if product_match:
        substitutions["PRODUCT_NAME"] = product_match.value
        short_name = module._derive_short_product_name(product_match.value)
        if short_name:
            substitutions["PRODUCT_SHORT_NAME"] = short_name

    model_match = module.resolve_spec_value_from_rows(
        rows,
        model=model,
        region=region,
        lang=lang,
        row_key="model_no",
        pages=None,
    )
    if model_match:
        substitutions["MODEL_NO"] = model_match.value

    for row in module._iter_ranked_rows(
        rows,
        model=model,
        region=region,
        lang=lang,
        pages=None,
    ):
        placeholder = module.resolve_page_value_placeholder_name(row)
        if not placeholder:
            continue

        value = module._pick_lang_value(row, "Value", lang)
        if not value:
            continue

        line_order_value = module._first_non_empty(row, ["Line_order", "line_order"])
        if line_order_value not in {"", "1", "1.0"}:
            placeholder = f"{placeholder}_{line_order_value.replace('.', '_')}"
        substitutions.setdefault(placeholder, value)

    for row_key, (placeholder_base, pages) in module._DERIVED_MULTILINE_PLACEHOLDERS.items():
        for row in module._iter_ranked_rows(
            rows,
            model=model,
            region=region,
            lang=lang,
            row_key=row_key,
            pages=pages,
        ):
            line_order_value = module._normalize_line_order_suffix(
                module._first_non_empty(row, ["Line_order", "line_order"])
            )
            param = module._pick_lang_value(row, "Param", lang)
            value = module._pick_lang_value(row, "Value", lang)
            line_value = module._compose_placeholder_line_value(row, lang=lang)
            if line_value:
                substitutions.setdefault(f"{placeholder_base}_LINE_{line_order_value}", line_value)
            if param:
                substitutions.setdefault(f"{placeholder_base}_PARAM_{line_order_value}", param)
            if value:
                substitutions.setdefault(f"{placeholder_base}_VALUE_{line_order_value}", value)

    return module._with_derived_substitutions(substitutions)


def resolve_product_name_from_rows(
    module: Any,
    rows: list[dict[str, str]],
    *,
    model: str | None,
    region: str | None,
    lang: str,
) -> Any | None:
    match = module.resolve_spec_value_from_rows(
        rows,
        model=model,
        region=region,
        lang=lang,
        row_key="product_name",
        pages=None,
    )
    if not match:
        return None
    return module.ProductNameMatch(product_name=match.value, region=match.region)


def resolve_product_name_from_spec_master(
    module: Any,
    spec_master_csv: Path,
    *,
    model: str | None,
    region: str | None,
    lang: str,
) -> Any | None:
    rows = module._read_csv_rows(spec_master_csv)
    if not rows:
        return None
    return module.resolve_product_name_from_rows(rows, model=model, region=region, lang=lang)


def resolve_template_substitutions_from_spec_master(
    module: Any,
    spec_master_csv: Path,
    *,
    model: str | None,
    region: str | None,
    lang: str,
) -> dict[str, str]:
    rows = module._read_csv_rows(spec_master_csv)
    if not rows:
        return {}
    return module.resolve_template_substitutions_from_rows(rows, model=model, region=region, lang=lang)


def read_spec_master_rows(module: Any, spec_master_csv: Path) -> list[dict[str, str]]:
    return module._read_csv_rows(spec_master_csv)
