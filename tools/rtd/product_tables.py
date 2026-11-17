"""产品对比 and 参数表 (step 13 of the 2026-11 redesign; REV-53), read from the product-information snapshot.

参数表 (``products/table``) is one table per category: a row per model × market, a column per parameter that
category's products state, sortable, filterable by 项目, 市场 and 系列, groupable by project and downloadable as the
filtered table. 产品对比 (``products/compare``) sets two to four models side by side in one market; the visitor picks
them on the page, so the page carries the values of every model as escaped JSON. Both are private (combined role)
only, like 产品库 (``tools/rtd/product_library.py``) and 产品档案 (``tools/rtd/product_profile.py``), whose display rules
they share. Every figure and name comes from the file.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from tools.rtd.product_library import MARKET_ORDER, OTHER_CATEGORY, UNSORTED_SERIES, market_label
from tools.rtd.product_profile import (
    HIDDEN_PARAMETERS, compare_key, display, page_name, parameter_groups, product_name, sku_date,
)

TABLE_PAGE, TABLE_TEMPLATE = "products/table", "product_table.html"
COMPARE_PAGE, COMPARE_TEMPLATE = "products/compare", "product_compare.html"
COMPARE_LIMIT = 4


def _index(snapshot: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]],
                                              dict[tuple[str, str], dict[str, Any]]]:
    """Parameters by key, product rows by model, and (product key, parameter) → the shown value."""
    parameters = {str(p.get("key")): p for p in snapshot.get("parameters") or []
                  if isinstance(p, dict) and str(p.get("key")) not in HIDDEN_PARAMETERS}
    models: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in snapshot.get("products") or []:
        if isinstance(row, dict) and row.get("model"):
            models[str(row["model"]).strip()].append(row)
    values: dict[tuple[str, str], dict[str, Any]] = {}
    for value in snapshot.get("values") or []:
        parameter = parameters.get(str(value.get("parameter"))) if isinstance(value, dict) else None
        if parameter is None:
            continue
        number = value.get("number")
        values[(str(value.get("product")), parameter["key"])] = {
            "text": display(value, parameter.get("unit")), "key": compare_key(value),
            "number": number if isinstance(number, (int, float)) and not isinstance(number, bool) else None,
            "conflict": bool(value.get("sources_disagree"))}
    return parameters, models, values


def _row_key(row: dict[str, Any]) -> str:
    return str(row.get("key") or f"{row['model']}/{row.get('market')}")


def _markets(rows: list[dict[str, Any]]) -> list[str]:
    present = {str(row.get("market")) for row in rows if row.get("market")}
    return [code for code in MARKET_ORDER if code in present] + sorted(present - set(MARKET_ORDER))


# --- 参数表 ------------------------------------------------------------------------------------------------------


def _table_rows(models: dict[str, list[dict[str, Any]]], columns: list[dict[str, Any]],
                values: dict[tuple[str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for model, market_rows in sorted(models.items()):
        name, date = product_name(market_rows), sku_date(market_rows)
        for row in sorted(market_rows, key=lambda r: _markets([r])[0] if r.get("market") else ""):
            key, market = _row_key(row), str(row.get("market") or "")
            cells = []
            for column in columns:
                cell = values.get((key, column["key"]))
                cells.append({"text": cell["text"] if cell else "", "conflict": bool(cell and cell["conflict"]),
                              "sort": cell["number"] if cell and cell["number"] is not None else (cell or {}).get("text", "")})
            rows.append({"model": model, "name": name, "page": page_name(model), "market": market,
                         "market_label": market_label(market), "project": str(row.get("project") or ""),
                         "series": str(row.get("series") or "") or UNSORTED_SERIES, "sku_date": date, "cells": cells})
    return sorted(rows, key=lambda r: (r["project"] == "", r["project"], r["model"],
                                       MARKET_ORDER.index(r["market"]) if r["market"] in MARKET_ORDER else 99))


def _category_titles(by_category: dict[str, Any], product_catalog: dict[str, Any] | None) -> list[str]:
    """The 产品分类 snapshot's category order, then others by name, then 其他."""
    order = [str(item.get("name")) for item in (product_catalog or {}).get("categories") or [] if isinstance(item, dict)]
    titles = [title for title in order if title in by_category]
    titles += sorted(set(by_category) - set(titles) - {OTHER_CATEGORY})
    return titles + ([OTHER_CATEGORY] if OTHER_CATEGORY in by_category else [])


def _columns(parameters: dict[str, dict[str, Any]], members: dict[str, list[dict[str, Any]]],
             values: dict[tuple[str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    """The parameters the category's products state, in page order; numeric when any of its values is a number."""
    keys = {_row_key(row) for rows in members.values() for row in rows}
    stated: dict[str, bool] = {}
    for (product, key), cell in values.items():
        if product in keys:
            stated[key] = stated.get(key, False) or cell["number"] is not None
    return [{"key": p["key"], "name": p["name_zh"], "unit": str(p.get("unit") or ""), "numeric": stated[p["key"]]}
            for group in parameter_groups(parameters, set(stated)) for p in group["parameters"]]


def table_view(snapshot: dict[str, Any], product_catalog: dict[str, Any] | None = None) -> dict[str, Any]:
    """参数表: per category, its columns (the parameters its products state) and a row per model × market."""
    parameters, models, values = _index(snapshot)
    by_category: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(dict)
    for model, rows in models.items():
        category = next((str(row["category"]) for row in rows if row.get("category")), OTHER_CATEGORY)
        by_category[category][model] = rows
    categories = []
    for index, title in enumerate(_category_titles(by_category, product_catalog), 1):
        columns = _columns(parameters, by_category[title], values)
        rows = _table_rows(by_category[title], columns, values)
        categories.append({"id": f"t{index}", "title": title, "columns": columns, "rows": rows,
                           "projects": sorted({r["project"] for r in rows if r["project"]}),
                           "unassigned": any(not r["project"] for r in rows),
                           "series": sorted({r["series"] for r in rows}),
                           "markets": [{"code": c, "label": market_label(c)}
                                       for c in _markets([{"market": r["market"]} for r in rows])]})
    return {"built": bool(categories), "updated": str(snapshot.get("read_at") or "")[:10], "categories": categories}


# --- 产品对比 ----------------------------------------------------------------------------------------------------


def compare_view(snapshot: dict[str, Any]) -> dict[str, Any]:
    """产品对比: every model with its values per market, and the parameter groups in page order."""
    parameters, models, values = _index(snapshot)
    products = []
    for model, rows in sorted(models.items()):
        per_market: dict[str, dict[str, list[Any]]] = {}
        for row in rows:
            key = _row_key(row)
            per_market[str(row.get("market") or "")] = {
                param: [cell["text"], cell["key"], cell["conflict"]] for (product, param), cell in values.items()
                if product == key}
        products.append({"model": model, "name": product_name(rows),
                         "project": next((str(r["project"]) for r in rows if r.get("project")), ""),
                         "page": page_name(model), "markets": _markets(rows), "values": per_market})
    used = {param for (_, param) in values}
    groups = [{"title": group["title"], "parameters": [[p["key"], p["name_zh"]] for p in group["parameters"]]}
              for group in parameter_groups(parameters, used)]
    markets = _markets([{"market": m} for product in products for m in product["markets"]])
    return {"built": bool(products), "limit": COMPARE_LIMIT,
            "markets": [{"code": code, "label": market_label(code)} for code in markets],
            "data": {"products": products, "groups": groups,
                     "labels": {code: market_label(code) for code in markets}}}


__all__ = ["COMPARE_LIMIT", "COMPARE_PAGE", "COMPARE_TEMPLATE", "TABLE_PAGE", "TABLE_TEMPLATE", "compare_view",
           "table_view"]
