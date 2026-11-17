"""产品档案 (step 13 of the 2026-11 redesign; REV-53): one private page per model, read from the product-information
snapshot that 产品库 reads (``tools/rtd/product_library.py``).

The page never chooses a value. The snapshot's ``cells`` (schema v1.1) carry, per product, parameter and test
condition, the value the base's rules picked (rejected and superseded values left out, verified first, then by
source kind, then the newest), already written for display, with its number for comparison and the ids of every
value that took part. A snapshot without ``cells`` builds no product page.

A page shows the model's parameters in plain groups with Chinese names, one market at a time, a condition in its
row label; 各市场差异 lists only the parameters whose values differ between its markets; 说明书 lists its manuals by
market and language. The sources of a value (each value that took part: 来自《…说明书》· market · language, the
edition date when known, the printed sentence and a link) show only when the value is clicked. 各说明书写法不一致
marks a cell whose values disagree; no other verification mark is shown (operator, 2026-11-17).

功能, 搭配 and the quick and general guides are carried over from the former matrix page (``product_matrix``'s
capability table, curated pairings and the 产品分类 snapshot's guides), so nothing a colleague used disappears.
Every figure and name comes from the files; nothing is hard-coded. Private role only.
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from tools.rtd.product_library import MARKET_ORDER, has_cells, market_label, safe_model

PAGE_PREFIX = "products/item/"
TEMPLATE = "product_profile.html"
# Parameter groups as colleagues read them, in page order; a group not listed follows, by name.
GROUPS = (("电池", "电池"), ("输出", "输出"), ("输入", "充电与输入"), ("接口", "接口与扩展"), ("物理", "尺寸与重量"),
          ("环境", "使用环境"), ("认证", "安全与认证"), ("其他", "其他"), ("商业", "保修"))
# Shown in the page head, or never shown (the product's own name and code; a launch date is not what the base
# records: the head carries the SKU 创建时间 instead).
HIDDEN_PARAMETERS = {"product_name", "model_number", "launch_date"}
CONFLICT = "各说明书写法不一致"
# SKU 创建时间: the earliest creation time of the SKUs of the product's project in PLM (Beijing time). It is no launch
# date. Older products loaded in bulk carry only an upper bound. Shown as year-month only.
SKU_DATE, SKU_DATE_UPPER_BOUND = "first_sku_created", "first_sku_created_upper_bound"
_YEAR_MONTH = re.compile(r"^(\d{4})-(\d{2})")


def page_name(model: str) -> str:
    return PAGE_PREFIX + model


def compare_key(cell: dict[str, Any]) -> str:
    """What 各市场差异 compares: the number (rounded, so 1 and 1.0 agree) when there is one, else the text."""
    number = cell.get("number")
    if isinstance(number, (int, float)) and not isinstance(number, bool):
        return f"#{round(float(number), 6):g}"
    return re.sub(r"\s+", "", str(cell.get("text") or cell.get("display") or "")).lower()


def product_name(rows: list[dict[str, Any]]) -> str:
    """The name printed in the product's first market (in the usual market order), else its short name or model."""
    def rank(row: dict[str, Any]) -> int:
        market = str(row.get("market") or "")
        return MARKET_ORDER.index(market) if market in MARKET_ORDER else len(MARKET_ORDER)

    for row in sorted(rows, key=rank):
        name = next((str(text).strip() for text in (row.get("names") or {}).values() if str(text or "").strip()), "")
        if name:
            return name
    return next((str(row.get("short_name")).strip() for row in rows if row.get("short_name")), rows[0]["model"])


def sku_date(rows: list[dict[str, Any]]) -> str:
    """``YYYY-MM``, ``不晚于 YYYY-MM`` for an upper bound, or "" (the page then writes 暂无)."""
    for row in rows:
        match = _YEAR_MONTH.match(str(row.get(SKU_DATE) or ""))
        if match:
            month = f"{match.group(1)}-{match.group(2)}"
            return f"不晚于 {month}" if row.get(SKU_DATE_UPPER_BOUND) is True else month
    return ""


def markets_of(rows: list[dict[str, Any]]) -> list[str]:
    present = {str(row.get("market")) for row in rows if row.get("market")}
    return [code for code in MARKET_ORDER if code in present] + sorted(present - set(MARKET_ORDER))


def row_key(row: dict[str, Any]) -> str:
    return str(row.get("key") or f"{row['model']}/{row.get('market')}")


def row_label(parameter: dict[str, Any], condition: str | None) -> str:
    return f"{parameter['name_zh']}（{condition}）" if condition else str(parameter["name_zh"])


def parameter_rows(parameters: dict[str, dict[str, Any]], keys: set[tuple[str, str | None]]) -> list[dict[str, Any]]:
    """Groups of (parameter, condition) rows present in ``keys``, in page order: group, the base's order, condition."""
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for key, condition in keys:
        parameter = parameters.get(key)
        if parameter and key not in HIDDEN_PARAMETERS:
            by_group[str(parameter.get("group") or "其他")].append(
                {"key": key, "condition": condition, "id": f"{key}|{condition or ''}",
                 "label": row_label(parameter, condition), "order": parameter.get("order") or 0,
                 "unit": str(parameter.get("unit") or "")})
    names = dict(GROUPS)
    order = [group for group, _ in GROUPS if group in by_group] + sorted(set(by_group) - set(names))
    return [{"id": f"g{index}", "title": names.get(group, group),
             "rows": sorted(by_group[group], key=lambda r: (r["order"], r["key"], r["condition"] or ""))}
            for index, group in enumerate(order, 1)]


def _sources(cell: dict[str, Any], name: str, values: dict[str, dict[str, Any]], sources: dict[str, dict[str, Any]],
             labels: dict[str, str]) -> list[dict[str, str]]:
    """Every value that took part in the cell, the chosen one first: where it is printed and how."""
    chosen = str(cell.get("value") or "")
    ids = [str(i) for i in cell.get("candidates") or []] or [chosen]
    listed = []
    for value_id in ids:
        value = values.get(value_id)
        if value is None and value_id == chosen:
            value = {"printed": cell.get("printed"), "source": cell.get("source")}
        if value is None:
            continue
        source = sources.get(str(value.get("source") or "")) or {}
        page = str(source.get("page") or "")
        language = str(source.get("language") or "")
        listed.append({"manual": f"《{name} 说明书》", "market": market_label(str(source.get("market") or "")),
                       "language": labels.get(language, language), "date": str(source.get("edition_date") or ""),
                       "position": str(value.get("position") or ""), "printed": str(value.get("printed") or ""),
                       "doc": page[:-5] if page.endswith(".html") else ""})
    return listed


def _cells(rows: list[dict[str, Any]], snapshot: dict[str, Any], name: str, labels: dict[str, str],
           parameters: dict[str, dict[str, Any]]) -> dict[tuple[str, str, str | None], dict[str, Any]]:
    """(market, parameter, condition) → what the page shows for that cell and its sources."""
    values = {str(v.get("id")): v for v in snapshot.get("values") or [] if isinstance(v, dict) and v.get("id")}
    sources = {str(s.get("id")): s for s in snapshot.get("sources") or [] if isinstance(s, dict)}
    markets = {row_key(row): str(row.get("market") or "") for row in rows}
    cells: dict[tuple[str, str, str | None], dict[str, Any]] = {}
    for cell in snapshot.get("cells") or []:
        if not isinstance(cell, dict) or str(cell.get("product")) not in markets:
            continue
        if str(cell.get("parameter")) not in parameters:
            continue
        condition = str(cell["condition"]) if cell.get("condition") else None
        key = (markets[str(cell["product"])], str(cell["parameter"]), condition)
        cells[key] = {"text": str(cell.get("display") or ""), "key": compare_key(cell),
                      "conflict": bool(cell.get("sources_disagree")),
                      "sources": _sources(cell, name, values, sources, labels)}
    return cells


def _differences(markets: list[str], groups: list[dict[str, Any]],
                 cells: dict[tuple[str, str, str | None], dict[str, Any]]) -> list[dict[str, Any]]:
    """Rows whose values differ between markets; a figure unlike every other market's is marked."""
    found = []
    for row in (row for group in groups for row in group["rows"]):
        present = {}
        for market in markets:
            cell = cells.get((market, row["key"], row["condition"]))
            if cell and cell["text"]:
                present[market] = cell
        keys = {market: cell["key"] for market, cell in present.items()}
        if len(present) < 2 or len(set(keys.values())) < 2:
            continue
        # Only figures are marked: texts in different languages always differ in wording, not necessarily in fact.
        numeric = all(key.startswith("#") for key in keys.values())
        line = []
        for market in markets:
            cell = present.get(market)
            others = [key for other, key in keys.items() if other != market]
            line.append({"text": cell["text"] if cell else "",
                         "odd": numeric and bool(cell) and all(key != keys[market] for key in others)})
        found.append({"label": row["label"], "cells": line})
    return found


def _manuals(model: str, markets: list[str], sources: list[dict[str, Any]], labels: dict[str, str]) -> list[dict]:
    """Per market, the model's Web manuals by language (the sources the snapshot read)."""
    manuals = []
    for market in markets:
        seen: dict[str, str] = {}
        for source in sources:
            page = str(source.get("page") or "")
            if source.get("model") == model and source.get("market") == market and page.endswith(".html"):
                seen.setdefault(str(source.get("language") or ""), page[:-5])
        if seen:
            manuals.append({"market": market_label(market), "docs": [
                {"label": labels.get(code, code), "doc": doc} for code, doc in sorted(seen.items())]})
    return manuals


def _head(model: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    first = rows[0]
    return {"model": model, "name": product_name(rows),
            "project": next((str(row["project"]) for row in rows if row.get("project")), ""),
            "sku_date": sku_date(rows),
            "classes": [str(part) for part in (first.get("category"), first.get("series"), first.get("capacity_tier"))
                        if part]}


def profile_view(model: str, rows: list[dict[str, Any]], snapshot: dict[str, Any], *, labels: dict[str, str],
                 extras: dict[str, Any] | None = None) -> dict[str, Any]:
    """The 产品档案 context of one model from its market rows and the snapshot's cells."""
    parameters = {str(p.get("key")): p for p in snapshot.get("parameters") or [] if isinstance(p, dict)}
    head = _head(model, rows)
    markets = markets_of(rows)
    cells = _cells(rows, snapshot, head["name"], labels, parameters)
    groups = parameter_rows(parameters, {(key, condition) for _, key, condition in cells})
    return {
        **head,
        "markets": [{"code": code, "label": market_label(code)} for code in markets],
        "groups": groups,
        "cells": {f"{market}|{key}|{condition or ''}": cell for (market, key, condition), cell in cells.items()},
        "differences": _differences(markets, groups, cells),
        "manuals": _manuals(model, markets, [s for s in snapshot.get("sources") or [] if isinstance(s, dict)], labels),
        **(extras or {"features": None, "pairing": None, "guides": []}),
    }


def matrix_extras(matrix: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    """功能, 搭配 and guides per model, carried over from the former matrix page's context (None: nothing)."""
    products = [product for category in (matrix or {}).get("categories") or [] for row in category["rows"]
                for product in row["products"]]
    first = {product["key"]: product["rows"][0]["model"] for product in products if product["rows"]}
    extras: dict[str, dict[str, Any]] = {}
    for product in products:
        detail = product.get("detail") or {}
        pairing = detail.get("pairing") or {}
        named = [{"label": item["label"], "model": first.get(item.get("key") or "", "")}
                 for item in pairing.get("named") or []]
        named_by = [{"label": item["label"], "name": item["name"], "model": item["model"]}
                    for item in pairing.get("named_by") or []]
        entry = {"features": detail.get("features"),
                 "pairing": {"named": named, "named_by": named_by} if named or named_by else None,
                 "guides": detail.get("guides") or []}
        for row in product["rows"]:
            extras.setdefault(row["model"], entry)
    return extras


def models_of(snapshot: dict[str, Any], warn=None) -> dict[str, list[dict[str, Any]]]:
    """The snapshot's rows by model; a model code unfit for a page path is skipped with a warning."""
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    skipped: set[str] = set()
    for row in snapshot.get("products") or []:
        if not isinstance(row, dict) or not row.get("model"):
            continue
        model = str(row["model"]).strip()
        if safe_model(model):
            by_model[model].append(row)
        elif model not in skipped:
            skipped.add(model)
            if warn:
                warn("产品档案 skipped for model %r: not a usable page name", model)
    return dict(by_model)


def profile_pages(snapshot: dict[str, Any], *, labels: dict[str, str], extras: dict[str, dict[str, Any]] | None = None,
                  warn=None) -> list[tuple[str, dict[str, Any]]]:
    """(page name, context) for every model in the snapshot; none without the decided cells."""
    if not has_cells(snapshot):
        return []
    by_model = models_of(snapshot, warn)
    return [(page_name(model), profile_view(model, rows, snapshot, labels=labels,
                                             extras=_linkable((extras or {}).get(model), set(by_model))))
            for model, rows in sorted(by_model.items())]


def _linkable(extra: dict[str, Any] | None, models: set[str]) -> dict[str, Any] | None:
    """Pairings link only to models that have a page here; others keep their label without a link."""
    if not extra or not extra.get("pairing"):
        return extra
    pairing = extra["pairing"]
    named = [{**item, "model": item["model"] if item["model"] in models else ""} for item in pairing["named"]]
    named_by = [{**item, "model": item["model"] if item["model"] in models else ""} for item in pairing["named_by"]]
    return {**extra, "pairing": {"named": named, "named_by": named_by}}


__all__ = ["CONFLICT", "GROUPS", "PAGE_PREFIX", "SKU_DATE", "SKU_DATE_UPPER_BOUND", "TEMPLATE", "compare_key",
           "has_cells", "markets_of", "matrix_extras", "models_of", "page_name", "parameter_rows", "product_name",
           "profile_pages", "profile_view", "row_key", "row_label", "safe_model", "sku_date"]
