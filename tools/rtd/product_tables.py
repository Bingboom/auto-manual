"""产品对比 and 参数表 (step 13 of the 2026-11 redesign; REV-53), read from the product-information snapshot.

Like 产品档案 (``tools/rtd/product_profile.py``), both read the snapshot's decided ``cells`` (schema v1.1) and never
choose a value: each cell gives the base's pick for one product, parameter and test condition, ready to display, with
its number for sorting and comparing. A test condition is its own column or row (``额定功率（STC）``). A snapshot
without cells gives both pages the plain 产品数据暂时读不到 note and no figures.

参数表 (``products/table``) is one table per category: a row per model × market, a column per (parameter,
condition) that category's products state, sortable, filterable by 项目, 市场 and 系列, groupable by project and
downloadable as the filtered table. 产品对比 (``products/compare``) sets two to four models side by side in one
market; the visitor picks them on the page, so the page carries every model's cells as escaped JSON. Both are private
(combined role) only. Every figure and name comes from the file.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from tools.rtd.product_library import MARKET_ORDER, OTHER_CATEGORY, UNSORTED_SERIES, has_cells, market_label
from tools.rtd.product_profile import (
    HIDDEN_PARAMETERS, compare_key, markets_of, models_of, page_name, parameter_rows, product_name, row_key, sku_date,
)

TABLE_PAGE, TABLE_TEMPLATE = "products/table", "product_table.html"
COMPARE_PAGE, COMPARE_TEMPLATE = "products/compare", "product_compare.html"
COMPARE_LIMIT = 4
NO_CELLS = "产品数据暂时读不到，请稍后再看。"
NO_PRODUCTS = "还没有产品数据。"


def _number(cell: dict[str, Any]) -> float | int | None:
    number = cell.get("number")
    return number if isinstance(number, (int, float)) and not isinstance(number, bool) else None


def _index(snapshot: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]],
                                              dict[tuple[str, str], dict[str, Any]]]:
    """Parameters by key, product rows by model (safe codes only), and (product key, row id) → the cell as shown."""
    parameters = {str(p.get("key")): p for p in snapshot.get("parameters") or []
                  if isinstance(p, dict) and str(p.get("key")) not in HIDDEN_PARAMETERS}
    cells: dict[tuple[str, str], dict[str, Any]] = {}
    for cell in snapshot.get("cells") or []:
        if not isinstance(cell, dict) or str(cell.get("parameter")) not in parameters:
            continue
        row_id = f"{cell['parameter']}|{cell.get('condition') or ''}"
        cells[(str(cell.get("product")), row_id)] = {
            "text": str(cell.get("display") or ""), "key": compare_key(cell), "number": _number(cell),
            "conflict": bool(cell.get("sources_disagree")), "parameter": str(cell["parameter"]),
            "condition": str(cell["condition"]) if cell.get("condition") else None}
    return parameters, models_of(snapshot), cells


def _empty(snapshot: dict[str, Any]) -> str:
    """Why the pages show no figures, or "" when they can."""
    if not snapshot.get("products"):
        return NO_PRODUCTS
    return "" if has_cells(snapshot) else NO_CELLS


# --- 参数表 ------------------------------------------------------------------------------------------------------


def _market_rank(market: str) -> int:
    return MARKET_ORDER.index(market) if market in MARKET_ORDER else len(MARKET_ORDER)


def _table_rows(models: dict[str, list[dict[str, Any]]], columns: list[dict[str, Any]],
                cells: dict[tuple[str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for model, market_rows in sorted(models.items()):
        name, date = product_name(market_rows), sku_date(market_rows)
        for row in market_rows:
            key, market = row_key(row), str(row.get("market") or "")
            shown = []
            for column in columns:
                cell = cells.get((key, column["id"])) or {}
                number = cell.get("number")
                shown.append({"text": cell.get("text", ""), "conflict": bool(cell.get("conflict")),
                              "sort": number if number is not None else cell.get("text", "")})
            rows.append({"model": model, "name": name, "page": page_name(model), "market": market,
                         "market_label": market_label(market), "project": str(row.get("project") or ""),
                         "series": str(row.get("series") or "") or UNSORTED_SERIES, "sku_date": date, "cells": shown})
    return sorted(rows, key=lambda r: (r["project"] == "", r["project"], r["model"], _market_rank(r["market"])))


def _category_titles(by_category: dict[str, Any], product_catalog: dict[str, Any] | None) -> list[str]:
    """The 产品分类 snapshot's category order, then others by name, then 其他."""
    order = [str(item.get("name")) for item in (product_catalog or {}).get("categories") or [] if isinstance(item, dict)]
    titles = [title for title in order if title in by_category]
    titles += sorted(set(by_category) - set(titles) - {OTHER_CATEGORY})
    return titles + ([OTHER_CATEGORY] if OTHER_CATEGORY in by_category else [])


def _columns(parameters: dict[str, dict[str, Any]], members: dict[str, list[dict[str, Any]]],
             cells: dict[tuple[str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    """The (parameter, condition) rows the category's products state, in page order; numeric when any is a number."""
    keys = {row_key(row) for rows in members.values() for row in rows}
    stated: dict[tuple[str, str | None], bool] = {}
    for (product, _), cell in cells.items():
        if product in keys and cell["text"]:
            pair = (cell["parameter"], cell["condition"])
            stated[pair] = stated.get(pair, False) or cell["number"] is not None
    return [{**row, "name": row["label"], "numeric": stated[(row["key"], row["condition"])]}
            for group in parameter_rows(parameters, set(stated)) for row in group["rows"]]


def table_view(snapshot: dict[str, Any], product_catalog: dict[str, Any] | None = None) -> dict[str, Any]:
    """参数表: per category, its columns (what its products state) and a row per model × market."""
    problem = _empty(snapshot)
    if problem:
        return {"built": False, "problem": problem, "updated": "", "categories": []}
    parameters, models, cells = _index(snapshot)
    by_category: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(dict)
    for model, rows in models.items():
        category = next((str(row["category"]) for row in rows if row.get("category")), OTHER_CATEGORY)
        by_category[category][model] = rows
    categories = []
    for index, title in enumerate(_category_titles(by_category, product_catalog), 1):
        columns = _columns(parameters, by_category[title], cells)
        rows = _table_rows(by_category[title], columns, cells)
        categories.append({"id": f"t{index}", "title": title, "columns": columns, "rows": rows,
                           "projects": sorted({r["project"] for r in rows if r["project"]}),
                           "unassigned": any(not r["project"] for r in rows),
                           "series": sorted({r["series"] for r in rows}),
                           "markets": [{"code": c, "label": market_label(c)}
                                       for c in markets_of([{"market": r["market"]} for r in rows])]})
    return {"built": bool(categories), "problem": "" if categories else NO_PRODUCTS,
            "updated": str(snapshot.get("read_at") or "")[:10], "categories": categories}


# --- 产品对比 ----------------------------------------------------------------------------------------------------


def compare_view(snapshot: dict[str, Any]) -> dict[str, Any]:
    """产品对比: every model with its cells per market, and the (parameter, condition) rows in page order."""
    problem = _empty(snapshot)
    if problem:
        return {"built": False, "problem": problem, "limit": COMPARE_LIMIT, "markets": [], "data": {}}
    parameters, models, cells = _index(snapshot)
    by_product: dict[str, dict[str, list[Any]]] = defaultdict(dict)
    for (product, row_id), cell in cells.items():
        if cell["text"]:
            by_product[product][row_id] = [cell["text"], cell["key"], cell["conflict"]]
    products = [{"model": model, "name": product_name(rows),
                 "project": next((str(r["project"]) for r in rows if r.get("project")), ""),
                 "page": page_name(model), "markets": markets_of(rows),
                 "values": {str(row.get("market") or ""): by_product.get(row_key(row), {}) for row in rows}}
                for model, rows in sorted(models.items())]
    used = {(cell["parameter"], cell["condition"]) for cell in cells.values() if cell["text"]}
    groups = [{"title": group["title"], "parameters": [[row["id"], row["label"]] for row in group["rows"]]}
              for group in parameter_rows(parameters, used)]
    markets = markets_of([{"market": m} for product in products for m in product["markets"]])
    return {"built": bool(products), "problem": "" if products else NO_PRODUCTS, "limit": COMPARE_LIMIT,
            "markets": [{"code": code, "label": market_label(code)} for code in markets],
            "data": {"products": products, "groups": groups,
                     "labels": {code: market_label(code) for code in markets}}}


__all__ = ["COMPARE_LIMIT", "COMPARE_PAGE", "COMPARE_TEMPLATE", "NO_CELLS", "NO_PRODUCTS", "TABLE_PAGE",
           "TABLE_TEMPLATE", "compare_view", "table_view"]
