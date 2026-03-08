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


def resolve_product_name_from_rows(
    rows: list[dict[str, str]],
    *,
    model: str | None,
    region: str | None,
    lang: str,
) -> ProductNameMatch | None:
    target_model = (model or "").strip()
    if not target_model:
        return None

    target_region = (region or "").strip() or None

    candidates: list[tuple[int, int, int, str, str | None]] = []
    for idx, row in enumerate(rows):
        if not _is_truthy(_first_non_empty(row, ["enabled", "Enabled"])):
            continue
        if not _is_truthy(_first_non_empty(row, ["Is_Latest", "is_latest"])):
            continue

        row_key = _first_non_empty(row, ["Row_key", "row_key"]).lower()
        if row_key != "product_name":
            continue

        page = _first_non_empty(row, ["Page", "page"]).lower()
        if page and page not in {"spec", "specifications"}:
            continue

        row_model = _first_non_empty(
            row,
            ["Model", "model", "Product_Model", "product_model", "Model_No", "model_no"],
        )
        if row_model and row_model != target_model:
            continue

        row_region = _first_non_empty(row, ["Region", "region"])
        if target_region and row_region and row_region != target_region:
            continue

        value = _pick_lang_value(row, "Value", lang)
        if not value:
            continue

        score = 0
        if row_model == target_model:
            score += 8
        if target_region and row_region == target_region:
            score += 8
        if not target_region and not row_region:
            score += 2

        if _first_non_empty(row, [f"Value_{lang}", f"Value_{lang.lower()}"]):
            score += 2
        if _first_non_empty(row, ["Is_Latest", "is_latest"]):
            score += 1

        line_num_text = (row.get("__line__") or "0").strip()
        try:
            line_num = int(line_num_text)
        except ValueError:
            line_num = idx + 2

        candidates.append((score, line_num, idx, value, row_region or None))

    if not candidates:
        return None

    candidates.sort(key=lambda x: (-x[0], x[1], x[2]))
    best = candidates[0]
    return ProductNameMatch(product_name=best[3], region=best[4])


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
