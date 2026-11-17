"""产品档案 (step 13 of the 2026-11 redesign; REV-53): one private page per model, read from the product-information
snapshot that 产品库 reads (``tools/rtd/product_library.py``).

A page shows the model's parameters in plain groups with Chinese names, one market at a time; 各市场差异 lists only
the parameters whose values differ between its markets; 说明书 lists its manuals by market and language. The source
of a value (manual, market, language, edition date, the printed sentence and a link) shows only when the value is
clicked. A value the manuals print differently carries 各说明书写法不一致; no other verification mark is shown
(operator, 2026-11-17).

功能, 搭配 and the quick and general guides are carried over from the former matrix page (``product_matrix``'s
capability table, curated pairings and the 产品分类 snapshot's guides), so nothing a colleague used disappears.
Every figure and name comes from the files; nothing is hard-coded. Private role only.
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from tools.rtd.product_library import MARKET_ORDER, market_label

PAGE_PREFIX = "products/item/"
TEMPLATE = "product_profile.html"
# Parameter groups as colleagues read them, in page order; a group not listed follows, by name.
GROUPS = (("电池", "电池"), ("输出", "输出"), ("输入", "充电与输入"), ("接口", "接口与扩展"), ("物理", "尺寸与重量"),
          ("环境", "使用环境"), ("认证", "安全与认证"), ("其他", "其他"), ("商业", "保修"))
# Shown in the page head, or never shown (the product's own name and code; a launch date is not what the base
# records: the head carries the SKU 创建时间 instead).
HIDDEN_PARAMETERS = {"product_name", "model_number", "launch_date"}
HIDDEN_UNITS = {"count"}
PREFIX_QUALIFIERS = {"约"}
SUFFIX_QUALIFIERS = {"额定", "峰值"}
CONFLICT = "各说明书写法不一致"
# SKU 创建时间: the earliest creation time of the SKUs of the product's project in PLM (Beijing time). It is no launch
# date. Older products loaded in bulk carry only an upper bound. Shown as year-month only.
SKU_DATE, SKU_DATE_UPPER_BOUND = "first_sku_created", "first_sku_created_upper_bound"
_YEAR_MONTH = re.compile(r"^(\d{4})-(\d{2})")


def page_name(model: str) -> str:
    return PAGE_PREFIX + model


def _number(value: float | int) -> str:
    return f"{value:,.0f}" if float(value).is_integer() else f"{value:,}".rstrip("0").rstrip(".")


_NUMERIC_TEXT = re.compile(r"^[\d.,\s×xX~\-–/+]+$")


def display(value: dict[str, Any], unit: str | None = None) -> str:
    """A value as the page writes it: the text (or number) with its unit and qualifier.

    ``unit`` is the parameter's unit in the base. A number takes it (else the printed unit); a text takes it only
    when the text is bare figures (``366×255×269``), never after words (an AC input described in full).
    """
    unit = str(unit or value.get("printed_unit") or "")
    unit = "" if unit in HIDDEN_UNITS else unit
    if value.get("text"):
        text = str(value["text"]).strip()
        shown = f"{text} {unit}" if unit and _NUMERIC_TEXT.match(text) else text
    elif value.get("number") is not None:
        shown = f"{_number(value['number'])} {unit}".strip()
    else:
        shown = str(value.get("printed") or "").strip()
    qualifier = str(value.get("qualifier") or "")
    if qualifier in PREFIX_QUALIFIERS:
        shown = f"{qualifier} {shown}"
    elif qualifier in SUFFIX_QUALIFIERS:
        shown = f"{shown}（{qualifier}）"
    return shown


def compare_key(value: dict[str, Any]) -> str:
    """What 各市场差异 compares: the number when there is one, else the text without case or spacing."""
    if value.get("number") is not None:
        return f"#{float(value['number'])}"
    return re.sub(r"\s+", "", str(value.get("text") or value.get("printed") or "")).lower()


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


def _source(value: dict[str, Any], sources: dict[str, dict[str, Any]], labels: dict[str, str]) -> dict[str, Any]:
    source = sources.get(str(value.get("source") or "")) or {}
    page = str(source.get("page") or "")
    return {"market": market_label(str(source.get("market") or "")),
            "language": labels.get(str(source.get("language") or ""), str(source.get("language") or "")),
            "date": str(source.get("edition_date") or ""), "position": str(value.get("position") or ""),
            "printed": str(value.get("printed") or ""),
            "doc": page[:-5] if page.endswith(".html") else ""}


def parameter_groups(parameters: dict[str, dict[str, Any]], keys: set[str]) -> list[dict[str, Any]]:
    """The groups holding at least one of ``keys``, each with its parameters in the base's order."""
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for key in keys:
        parameter = parameters.get(key)
        if parameter and key not in HIDDEN_PARAMETERS:
            by_group[str(parameter.get("group") or "其他")].append(parameter)
    names = dict(GROUPS)
    order = [group for group, _ in GROUPS if group in by_group] + sorted(set(by_group) - set(names))
    return [{"id": f"g{index}", "title": names.get(group, group),
             "parameters": sorted(by_group[group], key=lambda p: (p.get("order") or 0, p["key"]))}
            for index, group in enumerate(order, 1)]


def _differences(markets: list[str], parameters: list[dict[str, Any]],
                 cells: dict[tuple[str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    """Parameters whose values differ between markets; a figure unlike every other market's is marked."""
    rows = []
    for parameter in parameters:
        present = {market: cells[(market, parameter["key"])] for market in markets
                   if (market, parameter["key"]) in cells}
        keys = {market: cell["key"] for market, cell in present.items()}
        if len(present) < 2 or len(set(keys.values())) < 2:
            continue
        # Only figures are marked: texts in different languages always differ in wording, not necessarily in fact.
        numeric = all(key.startswith("#") for key in keys.values())
        row = []
        for market in markets:
            cell = present.get(market)
            others = [key for other, key in keys.items() if other != market]
            row.append({"text": cell["text"] if cell else "",
                        "odd": numeric and bool(cell) and all(key != keys[market] for key in others)})
        rows.append({"label": parameter["name_zh"], "cells": row})
    return rows


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


def _cells(rows: list[dict[str, Any]], snapshot: dict[str, Any], parameters: dict[str, dict[str, Any]],
           sources: dict[str, dict[str, Any]], labels: dict[str, str]) -> dict[tuple[str, str], dict[str, Any]]:
    """(market, parameter) → the value as shown, its comparison key, the disagreement flag and its source."""
    by_key = {str(row.get("key") or f"{row['model']}/{row.get('market')}"): row for row in rows}
    cells: dict[tuple[str, str], dict[str, Any]] = {}
    for value in snapshot.get("values") or []:
        row = by_key.get(value.get("product")) if isinstance(value, dict) else None
        parameter = parameters.get(str(value.get("parameter"))) if row is not None else None
        if parameter is None:
            continue
        cells[(str(row.get("market")), parameter["key"])] = {
            "text": display(value, parameter.get("unit")), "key": compare_key(value),
            "conflict": bool(value.get("sources_disagree")), "source": _source(value, sources, labels)}
    return cells


def _head(model: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    first = rows[0]
    return {"model": model, "name": product_name(rows),
            "project": next((str(row["project"]) for row in rows if row.get("project")), ""),
            "sku_date": sku_date(rows),
            "classes": [str(part) for part in (first.get("category"), first.get("series"), first.get("capacity_tier"))
                        if part]}


def sku_date(rows: list[dict[str, Any]]) -> str:
    """``YYYY-MM``, ``不晚于 YYYY-MM`` for an upper bound, or "" (the page then writes 暂无)."""
    for row in rows:
        match = _YEAR_MONTH.match(str(row.get(SKU_DATE) or ""))
        if match:
            month = f"{match.group(1)}-{match.group(2)}"
            return f"不晚于 {month}" if row.get(SKU_DATE_UPPER_BOUND) is True else month
    return ""


def _markets(rows: list[dict[str, Any]]) -> list[str]:
    present = {str(row.get("market")) for row in rows if row.get("market")}
    return [code for code in MARKET_ORDER if code in present] + sorted(present - set(MARKET_ORDER))


def profile_view(model: str, rows: list[dict[str, Any]], snapshot: dict[str, Any], *, labels: dict[str, str],
                 extras: dict[str, Any] | None = None) -> dict[str, Any]:
    """The 产品档案 context of one model from its market rows in the snapshot."""
    parameters = {str(p.get("key")): p for p in snapshot.get("parameters") or [] if isinstance(p, dict)}
    sources = {str(s.get("id")): s for s in snapshot.get("sources") or [] if isinstance(s, dict)}
    markets = _markets(rows)
    cells = _cells(rows, snapshot, parameters, sources, labels)
    groups = parameter_groups(parameters, {key for _, key in cells})
    ordered = [parameter for group in groups for parameter in group["parameters"]]
    return {
        **_head(model, rows),
        "markets": [{"code": code, "label": market_label(code)} for code in markets],
        "groups": groups, "cells": {f"{market}|{key}": cell for (market, key), cell in cells.items()},
        "differences": _differences(markets, ordered, cells),
        "manuals": _manuals(model, markets, list(sources.values()), labels),
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


def profile_pages(snapshot: dict[str, Any], *, labels: dict[str, str],
                  extras: dict[str, dict[str, Any]] | None = None) -> list[tuple[str, dict[str, Any]]]:
    """(page name, context) for every model in the snapshot."""
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in snapshot.get("products") or []:
        if isinstance(row, dict) and row.get("model"):
            by_model[str(row["model"]).strip()].append(row)
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


__all__ = ["CONFLICT", "GROUPS", "PAGE_PREFIX", "SKU_DATE", "SKU_DATE_UPPER_BOUND", "TEMPLATE", "compare_key", "display",
           "matrix_extras", "page_name", "parameter_groups", "product_name", "profile_pages", "profile_view", "sku_date"]
