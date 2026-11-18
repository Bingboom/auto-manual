"""产品演进时间轴 (products/timeline): swimlane product timeline over SKU creation dates.

Reads the product-information snapshot (``docs/knowledge/product-matrix/snapshot.json``) and optional
``product_catalog.json`` fallback to plot each model along ``first_sku_created`` (YYYY-MM / YYYY-MM-DD),
switchable on the page across series, capacity tier, market, and product category swimlanes. Private
(combined) site role only; no project codes or raw snapshot keys are shown.
"""
from __future__ import annotations

import re
from typing import Any

from tools.rtd.product_library import OTHER_CATEGORY, UNSORTED_SERIES, has_cells, market_label
from tools.rtd.product_profile import markets_of, models_of, page_name, product_name

TIMELINE_PAGE, TIMELINE_TEMPLATE = "products/timeline", "product_timeline.html"
NO_PRODUCTS = "还没有产品数据。"
NO_DATES = "暂无带 SKU 创建时间的产品数据。"
_ISO_DATE = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])(?:-(?:0[1-9]|[12]\d|3[01]))?$")


def _clean_date(raw: Any) -> str:
    text = str(raw or "").strip()[:10]
    if not _ISO_DATE.match(text):
        return ""
    return f"{text}-15" if len(text) == 7 else text


def _catalog_entry(product_catalog: dict[str, Any] | None, model: str) -> dict[str, Any]:
    models = (product_catalog or {}).get("models")
    entry = models.get(model) if isinstance(models, dict) else None
    return entry if isinstance(entry, dict) else {}


def _first_str(rows: list[dict[str, Any]], field: str) -> str:
    for row in rows:
        value = str(row.get(field) or "").strip()
        if value:
            return value
    return ""


def _category_titles(seen: set[str], product_catalog: dict[str, Any] | None) -> list[str]:
    order = [str(item.get("name")) for item in (product_catalog or {}).get("categories") or [] if isinstance(item, dict)]
    titles = [title for title in order if title in seen]
    titles += sorted(seen - set(titles) - {OTHER_CATEGORY})
    return titles + ([OTHER_CATEGORY] if OTHER_CATEGORY in seen else [])


def _model_record(model: str, rows: list[dict[str, Any]], catalog_info: dict[str, Any]) -> dict[str, Any]:
    category = _first_str(rows, "category") or str(catalog_info.get("category") or "").strip() or OTHER_CATEGORY
    series = _first_str(rows, "series") or str(catalog_info.get("series") or "").strip() or UNSORTED_SERIES
    name = product_name(rows)
    short_name = _first_str(rows, "short_name") or str(catalog_info.get("short_name") or "").strip() or name
    capacity = _first_str(rows, "capacity_tier")
    market_entries = []
    for row in rows:
        market = str(row.get("market") or "").strip()
        if not market:
            continue
        market_entries.append({
            "market": market,
            "date": _clean_date(row.get("first_sku_created")),
            "upper": bool(row.get("first_sku_created_upper_bound")),
        })
    market_entries.sort(key=lambda item: (item["date"] == "", item["date"], item["market"]))
    return {
        "model": model,
        "page": page_name(model),
        "name": name,
        "short_name": short_name,
        "category": category,
        "series": series,
        "cap": capacity,
        "markets": market_entries,
    }


def _year_bounds(dated_years: list[int], today: str) -> tuple[int, int]:
    min_year = min(dated_years)
    max_data_year = max(dated_years)
    today_year = int(today[:4]) if len(today) >= 4 and today[:4].isdigit() else max_data_year
    return min_year, max(max_data_year + 1, today_year + 1)


def timeline_view(snapshot: dict[str, Any], product_catalog: dict[str, Any] | None = None, *,
                  today: str = "") -> dict[str, Any]:
    """Build template context for 产品演进时间轴 (products/timeline)."""
    if not snapshot.get("products"):
        return {"built": False, "problem": NO_PRODUCTS, "categories": [], "markets": [], "data": {}}
    models = models_of(snapshot)
    records = [_model_record(model, rows, _catalog_entry(product_catalog, model))
               for model, rows in sorted(models.items())]
    dated_years = [int(m["date"][:4]) for rec in records for m in rec["markets"] if m["date"]]
    if not dated_years:
        return {"built": False, "problem": NO_DATES, "categories": [], "markets": [], "data": {}}

    dated_categories = {rec["category"] for rec in records if any(m["date"] for m in rec["markets"])}
    categories = _category_titles(dated_categories, product_catalog)
    dated_markets = markets_of([{"market": m["market"]} for rec in records for m in rec["markets"] if m["date"]])
    markets = [{"code": code, "label": market_label(code)} for code in dated_markets]
    clean_today = _clean_date(today)
    min_year, max_year = _year_bounds(dated_years, clean_today)
    default_cat = "便携储能" if "便携储能" in categories else categories[0]

    return {
        "built": True,
        "problem": "",
        "categories": categories,
        "default_category": default_cat,
        "markets": markets,
        "data": {
            "today": clean_today,
            "min_year": min_year,
            "max_year": max_year,
            "has_profiles": has_cells(snapshot),
            "default_category": default_cat,
            "categories": categories,
            "labels": {m["code"]: m["label"] for m in markets},
            "products": records,
        },
    }


__all__ = ["NO_DATES", "NO_PRODUCTS", "TIMELINE_PAGE", "TIMELINE_TEMPLATE", "timeline_view"]
