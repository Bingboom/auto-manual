
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path

from tools.utils.spec_master_shared import (
    ProductNameMatch,
    SpecValueMatch,
    _DERIVED_MULTILINE_PLACEHOLDERS,
)
from tools.utils.spec_master_row_helpers import (
    _first_non_empty,
    _iter_ranked_rows,
    _normalize_line_order_suffix,
    _pick_lang_value,
    _pick_row_region,
    _pick_usage_type,
    _pick_value_role,
    _read_csv_rows,
    resolve_page_value_placeholder_name,
    source_language_for_row,
)


def _pick_lang_specific_value(row: dict[str, str], base: str, lang: str) -> str:
    normalized_lang = (lang or "").strip()
    if not normalized_lang:
        return ""
    return _first_non_empty(
        row,
        [
            f"{base}_{normalized_lang}",
            f"{base}_{normalized_lang.lower()}",
            f"{base}_{normalized_lang.upper()}",
        ],
    )


def _looks_like_translation_note(value: str) -> bool:
    text = (value or "").strip()
    if not text:
        return False
    lowered = text.casefold()
    return (
        "\n" in text
        or "\r" in text
        or "说明" in text
        or "占位符" in text
        or "placeholder" in lowered
    )


def _preferred_page_value_text(row: dict[str, str], *, lang: str) -> str:
    normalized_lang = (lang or "").strip().lower()
    source_lang = source_language_for_row(row)
    if (
        normalized_lang
        and normalized_lang != "en"
        and normalized_lang != source_lang
        and _pick_usage_type(row) == "page_value"
        and _pick_value_role(row) == "label"
    ):
        localized_row_label = _pick_lang_specific_value(row, "Row_label", normalized_lang)
        source_row_label = _first_non_empty(row, ["Row_label_source", "row_label_source"])
        source_value = _first_non_empty(row, ["Value_source", "value_source"])
        if (
            localized_row_label
            and not _looks_like_translation_note(localized_row_label)
            and localized_row_label != source_row_label
            and localized_row_label != source_value
        ):
            return localized_row_label
    return _pick_lang_value(row, "Value", lang)

def resolve_spec_value_from_rows(
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
) -> SpecValueMatch | None:
    for row in _iter_ranked_rows(
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
        value = _preferred_page_value_text(row, lang=lang)
        if value:
            return SpecValueMatch(
                value=value,
                region=_pick_row_region(row) or None,
                row=row,
            )
    return None


def collect_matching_spec_rows(
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
        _iter_ranked_rows(
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
) -> tuple[SpecValueMatch, ...]:
    matches: list[SpecValueMatch] = []
    for row in collect_matching_spec_rows(
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
        value = _preferred_page_value_text(row, lang=lang)
        if not value:
            continue
        matches.append(
            SpecValueMatch(
                value=value,
                region=_pick_row_region(row) or None,
                row=row,
            )
        )
    return tuple(matches)


def _derive_short_product_name(name: str) -> str:
    text = (name or "").strip()
    if not text:
        return ""
    prefix = "Jackery "
    if text.startswith(prefix):
        return text[len(prefix) :].strip()
    return text


def _derive_label_lower(value: str) -> str:
    tokens = value.split()
    lowered: list[str] = []
    for token in tokens:
        if token.upper() == "BUTTON":
            lowered.append("button")
            continue
        if token.isupper():
            lowered.append(token)
            continue
        lowered.append(token.lower())
    return " ".join(lowered)


def _compose_placeholder_line_value(row: dict[str, str], *, lang: str) -> str:
    direct_text = _pick_lang_value(row, "line_text", lang)
    if direct_text:
        return direct_text

    param = _pick_lang_value(row, "Param", lang)
    value = _pick_lang_value(row, "Value", lang)
    if param and value:
        separator = _first_non_empty(row, ["param_value_sep", "Param_value_sep"])
        if not separator:
            separator = " : " if lang == "fr" else "：" if lang == "ja" else ": "
        return f"{param}{separator}{value}"
    return value or param


def _with_derived_substitutions(substitutions: dict[str, str]) -> dict[str, str]:
    out = dict(substitutions)
    for key, value in list(out.items()):
        if key.endswith("_BOLD") or key.endswith("_LOWER"):
            continue
        if value:
            out.setdefault(f"{key}_BOLD", f"**{value}**")
        if key.endswith("_LABEL"):
            out.setdefault(f"{key}_LOWER", _derive_label_lower(value))
    return out


def resolve_template_substitutions_from_rows(
    rows: list[dict[str, str]],
    *,
    model: str | None,
    region: str | None,
    lang: str,
) -> dict[str, str]:
    substitutions: dict[str, str] = {}

    product_match = resolve_spec_value_from_rows(
        rows,
        model=model,
        region=region,
        lang=lang,
        row_key="product_name",
        pages=None,
    )
    if product_match:
        substitutions["PRODUCT_NAME"] = product_match.value
        short_name = _derive_short_product_name(product_match.value)
        if short_name:
            substitutions["PRODUCT_SHORT_NAME"] = short_name

    model_match = resolve_spec_value_from_rows(
        rows,
        model=model,
        region=region,
        lang=lang,
        row_key="model_no",
        pages=None,
    )
    if model_match:
        substitutions["MODEL_NO"] = model_match.value

    for row in _iter_ranked_rows(
        rows,
        model=model,
        region=region,
        lang=lang,
        pages=None,
    ):
        placeholder = resolve_page_value_placeholder_name(row)
        if not placeholder:
            continue

        value = _preferred_page_value_text(row, lang=lang)
        if not value:
            continue

        line_order_value = _first_non_empty(row, ["Line_order", "line_order"])
        if line_order_value not in {"", "1", "1.0"}:
            placeholder = f"{placeholder}_{line_order_value.replace('.', '_')}"
        substitutions.setdefault(placeholder, value)

    for row_key, (placeholder_base, pages) in _DERIVED_MULTILINE_PLACEHOLDERS.items():
        for row in _iter_ranked_rows(
            rows,
            model=model,
            region=region,
            lang=lang,
            row_key=row_key,
            pages=pages,
        ):
            line_order_value = _normalize_line_order_suffix(_first_non_empty(row, ["Line_order", "line_order"]))
            param = _pick_lang_value(row, "Param", lang)
            value = _pick_lang_value(row, "Value", lang)
            line_value = _compose_placeholder_line_value(row, lang=lang)
            if line_value:
                substitutions.setdefault(f"{placeholder_base}_LINE_{line_order_value}", line_value)
            if param:
                substitutions.setdefault(f"{placeholder_base}_PARAM_{line_order_value}", param)
            if value:
                substitutions.setdefault(f"{placeholder_base}_VALUE_{line_order_value}", value)

    return _with_derived_substitutions(substitutions)


def resolve_product_name_from_rows(
    rows: list[dict[str, str]],
    *,
    model: str | None,
    region: str | None,
    lang: str,
) -> ProductNameMatch | None:
    match = resolve_spec_value_from_rows(
        rows,
        model=model,
        region=region,
        lang=lang,
        row_key="product_name",
        pages=None,
    )
    if not match:
        return None
    return ProductNameMatch(product_name=match.value, region=match.region)


def resolve_product_name_from_spec_master(
    spec_master_csv: Path,
    *,
    model: str | None,
    region: str | None,
    lang: str,
) -> ProductNameMatch | None:
    rows = _read_csv_rows(spec_master_csv)
    if not rows:
        return None
    return resolve_product_name_from_rows(rows, model=model, region=region, lang=lang)


def resolve_template_substitutions_from_spec_master(
    spec_master_csv: Path,
    *,
    model: str | None,
    region: str | None,
    lang: str,
) -> dict[str, str]:
    rows = _read_csv_rows(spec_master_csv)
    if not rows:
        return {}
    return resolve_template_substitutions_from_rows(rows, model=model, region=region, lang=lang)


def read_spec_master_rows(spec_master_csv: Path) -> list[dict[str, str]]:
    return _read_csv_rows(spec_master_csv)
