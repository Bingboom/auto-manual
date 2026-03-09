#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProductNameMatch:
    product_name: str
    region: str | None


@dataclass(frozen=True)
class SpecValueMatch:
    value: str
    region: str | None
    row: dict[str, str]


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows: list[dict[str, str]] = []
        for line, row in enumerate(csv.DictReader(f), start=2):
            row["__line__"] = str(line)
            rows.append(row)
        return rows


def _first_non_empty(row: dict[str, str], keys: list[str]) -> str:
    for key in keys:
        value = (row.get(key) or "").strip()
        if value:
            return value
    return ""


def _is_truthy(value: str) -> bool:
    text = (value or "").strip().lower()
    if not text:
        return True
    return text in {"1", "true", "yes", "y"}


def _pick_lang_value(row: dict[str, str], base: str, lang: str) -> str:
    keys = [
        f"{base}_{lang}",
        f"{base}_{lang.lower()}",
        f"{base}_{lang.upper()}",
        f"{base}_en",
        base,
        "Spec_Value",
    ]
    return _first_non_empty(row, keys)


def _pick_row_key(row: dict[str, str]) -> str:
    return _first_non_empty(row, ["Row_key", "row_key"]).lower()


def _pick_row_model(row: dict[str, str]) -> str:
    return _first_non_empty(
        row,
        ["Model", "model", "Product_Model", "product_model", "Model_No", "model_no"],
    )


def _pick_row_region(row: dict[str, str]) -> str:
    return _first_non_empty(row, ["Region", "region"])


def _normalize_page_filters(pages: str | list[str] | tuple[str, ...] | set[str] | None) -> set[str] | None:
    if pages is None:
        return None
    if isinstance(pages, str):
        raw_items = [pages]
    else:
        raw_items = list(pages)

    normalized = {(item or "").strip().lower() for item in raw_items if (item or "").strip()}
    return normalized or None


def _row_matches_target(
    row: dict[str, str],
    *,
    model: str | None,
    region: str | None,
    row_key: str | None = None,
    pages: str | list[str] | tuple[str, ...] | set[str] | None = None,
    line_order: str | int | None = None,
) -> bool:
    if not _is_truthy(_first_non_empty(row, ["enabled", "Enabled"])):
        return False
    if not _is_truthy(_first_non_empty(row, ["Is_Latest", "is_latest"])):
        return False

    target_key = (row_key or "").strip().lower()
    if target_key and _pick_row_key(row) != target_key:
        return False

    page_filters = _normalize_page_filters(pages)
    page_value = _first_non_empty(row, ["Page", "page"]).lower()
    if page_filters and page_value and page_value not in page_filters:
        return False

    target_model = (model or "").strip()
    row_model = _pick_row_model(row)
    if target_model and row_model and row_model != target_model:
        return False

    target_region = (region or "").strip()
    row_region = _pick_row_region(row)
    if target_region and row_region and row_region != target_region:
        return False

    if line_order is not None:
        wanted = str(line_order).strip()
        if wanted and _first_non_empty(row, ["Line_order", "line_order"]) != wanted:
            return False

    return True


def _score_row(
    row: dict[str, str],
    *,
    model: str | None,
    region: str | None,
    lang: str,
) -> int:
    target_model = (model or "").strip()
    target_region = (region or "").strip()
    row_model = _pick_row_model(row)
    row_region = _pick_row_region(row)

    score = 0
    if row_model and target_model and row_model == target_model:
        score += 8
    if row_region and target_region and row_region == target_region:
        score += 8
    if not target_region and not row_region:
        score += 2

    if _first_non_empty(row, [f"Value_{lang}", f"Value_{lang.lower()}"]):
        score += 2
    if _first_non_empty(row, ["Is_Latest", "is_latest"]):
        score += 1
    return score


def _row_line_num(row: dict[str, str], idx: int) -> int:
    line_num_text = (row.get("__line__") or "0").strip()
    try:
        return int(line_num_text)
    except ValueError:
        return idx + 2


def _iter_ranked_rows(
    rows: list[dict[str, str]],
    *,
    model: str | None,
    region: str | None,
    lang: str,
    row_key: str | None = None,
    pages: str | list[str] | tuple[str, ...] | set[str] | None = None,
    line_order: str | int | None = None,
) -> list[dict[str, str]]:
    target_model = (model or "").strip()
    target_region = (region or "").strip()
    candidates: list[tuple[int, int, int, dict[str, str]]] = []
    for idx, row in enumerate(rows):
        if not _row_matches_target(
            row,
            model=target_model or None,
            region=target_region or None,
            row_key=row_key,
            pages=pages,
            line_order=line_order,
        ):
            continue
        score = _score_row(row, model=target_model or None, region=target_region or None, lang=lang)
        candidates.append((score, _row_line_num(row, idx), idx, row))

    candidates.sort(key=lambda x: (-x[0], x[1], x[2]))
    return [item[3] for item in candidates]


def resolve_spec_value_from_rows(
    rows: list[dict[str, str]],
    *,
    model: str | None,
    region: str | None,
    lang: str,
    row_key: str,
    pages: str | list[str] | tuple[str, ...] | set[str] | None = ("spec", "specifications"),
    line_order: str | int | None = None,
) -> SpecValueMatch | None:
    for row in _iter_ranked_rows(
        rows,
        model=model,
        region=region,
        lang=lang,
        row_key=row_key,
        pages=pages,
        line_order=line_order,
    ):
        value = _pick_lang_value(row, "Value", lang)
        if value:
            return SpecValueMatch(
                value=value,
                region=_pick_row_region(row) or None,
                row=row,
            )
    return None


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
    )
    if model_match:
        substitutions["MODEL_NO"] = model_match.value

    for row in _iter_ranked_rows(
        rows,
        model=model,
        region=region,
        lang=lang,
        pages=("spec", "specifications"),
    ):
        raw_key = _pick_row_key(row)
        if not raw_key.startswith("tpl_"):
            continue

        value = _pick_lang_value(row, "Value", lang)
        if not value:
            continue

        placeholder = raw_key[4:].upper()
        line_order_value = _first_non_empty(row, ["Line_order", "line_order"])
        if line_order_value not in {"", "1", "1.0"}:
            placeholder = f"{placeholder}_{line_order_value.replace('.', '_')}"
        substitutions.setdefault(placeholder, value)

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
