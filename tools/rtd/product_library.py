"""产品库 (step 13 of the 2026-11 redesign; REV-53): the product-information matrix read from the base snapshot.

The matrix window exports the 产品信息矩阵 base to the private repository as ``product-matrix/snapshot.json``
under the knowledge directory (schema ``hello-docs-product-matrix-snapshot/v1``). Each product row there is one
model in one market, with its 产品类别, 产品系列, 容量档 and project. This module reads that file and lays the
products out as the operator asked: a tab per category, rows by series, columns by capacity tier (one 产品 column
for a category without tiers), and in each cell the model codes as chips, the models of one project merged into one
chip written ``A(B)``.

Project numbers and product values are private: the file is read only for the private (combined) site, and only
from the knowledge directory, which the public role never reads (``tools/rtd/portal.py``). Nothing here is ever
hard-coded: every count and date comes from the file. A missing or unreadable file gives a context that says so,
and the page shows no figures.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

SNAPSHOT = Path("product-matrix") / "snapshot.json"
SCHEMA = "hello-docs-product-matrix-snapshot/v1"
# v1.1 only adds fields (value ids and the decided cells); both read the same.
SCHEMAS = (SCHEMA, "hello-docs-product-matrix-snapshot/v1.1")
OTHER_CATEGORY = "其他"
UNSORTED_SERIES = "未分类"
UNSTATED_TIER = "容量未注明"
FLAT_COLUMN = "产品"
# Market codes as colleagues say them; a code not listed shows as itself.
MARKET_LABELS = {"US": "美规", "EU": "欧规", "JP": "日规", "CN": "国内", "KR": "韩规", "TW": "台规"}
MARKET_ORDER = ("US", "EU", "JP", "CN", "KR", "TW")


# A model code becomes a 产品档案 page path: letters, digits, dot, dash and underscore only, never "..".
_MODEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def safe_model(model: str) -> bool:
    return bool(_MODEL.match(model)) and ".." not in model


def has_cells(snapshot: dict[str, Any] | None) -> bool:
    """产品档案 and the tables need the decided cells (schema v1.1); without them those pages are not built."""
    return isinstance((snapshot or {}).get("cells"), list)


class SnapshotError(ValueError):
    """The snapshot exists but cannot be used."""


def snapshot_path(knowledge_dir: Path) -> Path:
    return knowledge_dir / SNAPSHOT


def load_snapshot(knowledge_dir: Path) -> dict[str, Any] | None:
    """The snapshot, None when the file is absent; SnapshotError when it is unusable."""
    path = snapshot_path(knowledge_dir)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SnapshotError(f"cannot read {SNAPSHOT.as_posix()}: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema") not in SCHEMAS:
        raise SnapshotError(f"schema is {data.get('schema') if isinstance(data, dict) else None!r}, not one of "
                            f"{', '.join(SCHEMAS)}")
    products = data.get("products")
    if not isinstance(products, list) or not all(isinstance(row, dict) and row.get("model") for row in products):
        raise SnapshotError("products must be a list of rows with a model")
    return data


def market_label(code: str) -> str:
    return MARKET_LABELS.get(code, code)


def _ordered(values: Iterable[str], preferred: Iterable[str]) -> list[str]:
    values = set(values)
    first = [value for value in preferred if value in values]
    return first + sorted(values - set(first))


def _models(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """One entry per model: its markets, project, classification and (project, market) rows."""
    models: dict[str, dict[str, Any]] = {}
    for row in rows:
        model = str(row["model"]).strip()
        entry = models.setdefault(model, {"model": model, "markets": set(), "project": None, "category": None,
                                          "series": None, "tier": None, "rows": set(), "names": set()})
        # What the home search matches: the printed names and the short name (the code and project come from rows).
        entry["names"].update(str(name).strip() for name in (row.get("names") or {}).values() if str(name or "").strip())
        if row.get("short_name"):
            entry["names"].add(str(row["short_name"]).strip())
        if row.get("market"):
            entry["markets"].add(str(row["market"]))
        # The filters match per model × market row: a project chosen together with a market needs both on one row.
        entry["rows"].add((str(row.get("project") or "").strip(), str(row.get("market") or "")))
        for field, key in (("project", "project"), ("category", "category"), ("series", "series"),
                           ("tier", "capacity_tier")):
            if entry[field] is None and row.get(key):
                entry[field] = str(row[key]).strip()
    return models


def _chip_order(model: dict[str, Any]) -> str:
    # By model code: the alphabetically first code goes outside the brackets (FAKE-A(FAKE-B)).
    return model["model"]


def _chips(models: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """A cell's chips: the models of one project merged into one chip, a model without a project alone."""
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    alone: list[list[dict[str, Any]]] = []
    for model in models:
        if model["project"]:
            groups[model["project"]].append(model)
        else:
            alone.append([model])
    chips = []
    # A chip sorts by its first (alphabetically first) member, which is also written outside the brackets.
    for members in sorted((sorted(group, key=_chip_order) for group in [*groups.values(), *alone]),
                          key=lambda group: _chip_order(group[0])):
        markets = set().union(*(member["markets"] for member in members))
        rows = sorted({pair for member in members for pair in member["rows"]})
        terms = {member["model"] for member in members} | {name for member in members for name in member["names"]}
        terms |= {project for project, _ in rows if project}
        chips.append({"project": members[0]["project"] or "", "markets": _ordered(markets, MARKET_ORDER),
                      # [[project, market], …]: the page writes it as JSON, so no project text can split a row.
                      "rows": [[project, market] for project, market in rows],
                      "search": " ".join(sorted(terms)).lower(),
                      "models": [{"model": member["model"], "markets": _ordered(member["markets"], MARKET_ORDER),
                                  "label": "、".join(map(market_label, _ordered(member["markets"], MARKET_ORDER)))}
                                 for member in members]})
    return chips


def _category_view(index: int, title: str, models: list[dict[str, Any]], series_order: list[str],
                   tier_order: list[str]) -> dict[str, Any]:
    tiers = {model["tier"] for model in models if model["tier"]}
    tiered = bool(tiers)
    columns = _ordered(tiers, tier_order) + ([UNSTATED_TIER] if tiered and any(not m["tier"] for m in models) else [])
    if not tiered:
        columns = [FLAT_COLUMN]
    named = {model["series"] for model in models if model["series"]}
    series = _ordered(named, series_order) + ([UNSORTED_SERIES] if any(not m["series"] for m in models) else [])
    rows = []
    for title_ in series:
        members = [m for m in models if (m["series"] or UNSORTED_SERIES) == title_]
        cells = []
        for column in columns:
            if not tiered:
                in_cell = members
            else:
                in_cell = [m for m in members if (m["tier"] or UNSTATED_TIER) == column]
            cells.append(_chips(in_cell))
        rows.append({"title": title_, "count": len(members), "cells": cells})
    return {"id": f"c{index}", "title": title, "count": len(models), "tiered": tiered, "columns": columns,
            "rows": rows}


def _catalog_order(catalog: dict[str, Any] | None) -> tuple[list[str], dict[str, list[str]], list[str]]:
    """The 产品分类 snapshot's category order, each category's series order, and the capacity-tier order."""
    items = [item for item in (catalog or {}).get("categories") or [] if isinstance(item, dict)]
    categories = [str(item.get("name")) for item in items]
    series = {str(item.get("name")): [str(name) for name in item.get("series") or []] for item in items}
    return categories, series, [str(tier) for tier in (catalog or {}).get("capacity_tiers") or []]


def _categories(models: list[dict[str, Any]], catalog: dict[str, Any] | None) -> list[dict[str, Any]]:
    category_order, series_by_category, tier_order = _catalog_order(catalog)
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for model in models:
        by_category[model["category"] or OTHER_CATEGORY].append(model)
    titles = _ordered(set(by_category) - {OTHER_CATEGORY}, category_order)
    titles += [OTHER_CATEGORY] if OTHER_CATEGORY in by_category else []
    return [_category_view(index, title, by_category[title], series_by_category.get(title, []), tier_order)
            for index, title in enumerate(titles, 1)]


def library_view(snapshot: dict[str, Any], product_catalog: dict[str, Any] | None = None) -> dict[str, Any]:
    """The 产品库 context from a loaded snapshot; categories, series and tiers follow the 产品分类 order."""
    rows = [row for row in snapshot.get("products") or [] if isinstance(row, dict)]
    models = list(_models(rows).values())
    markets = _ordered({market for model in models for market in model["markets"]}, MARKET_ORDER)
    updated = str(snapshot.get("read_at") or "")[:10]
    categories = _categories(models, product_catalog)
    # A code links to its 产品档案 only when that page is built (the snapshot has cells and the code is a safe page
    # name); otherwise to the manual library filtered to it, so no link points to a missing page.
    profiles = has_cells(snapshot)
    for chip in (chip for category in categories for row in category["rows"] for cell in row["cells"] for chip in cell):
        for member in chip["models"]:
            member["page"] = profiles and safe_model(member["model"])
    return {"built": True, "problem": "", "count": len(models), "updated": updated,
            "categories": categories,
            "projects": sorted({model["project"] for model in models if model["project"]}),
            "unassigned": any(not model["project"] for model in models),
            "markets": [{"code": code, "label": market_label(code)} for code in markets],
            # 知识库首页's 产品信息 card reads these two.
            "facts": {"products": len(models)}, "built_on": updated}


def library_context(knowledge_dir: Path, product_catalog: dict[str, Any] | None, warn=None) -> dict[str, Any]:
    """The page context; without a usable snapshot, or with no product in it, the page says so and shows no figures.

    An unusable snapshot is a Sphinx warning, which never fails the build: the RTD build runs without ``-W`` or
    ``fail_on_warning`` (``.readthedocs.yaml``), so a bad snapshot cannot hold back the manuals.
    """
    try:
        snapshot = load_snapshot(knowledge_dir)
    except SnapshotError as exc:
        if warn:
            warn("产品库 snapshot unusable: %s", exc)
        return empty_context("产品数据暂时读不到，请稍后再看。")
    if snapshot is None or not snapshot.get("products"):
        return empty_context("还没有产品数据。")
    return library_view(snapshot, product_catalog)


def empty_context(problem: str) -> dict[str, Any]:
    return {"built": False, "problem": problem, "count": None, "updated": "", "categories": [], "projects": [],
            "unassigned": False, "markets": [], "facts": {}, "built_on": ""}


__all__ = ["FLAT_COLUMN", "has_cells", "safe_model", "MARKET_LABELS", "OTHER_CATEGORY", "SCHEMA", "SCHEMAS", "SNAPSHOT", "SnapshotError",
           "UNSORTED_SERIES", "UNSTATED_TIER", "empty_context", "library_context", "library_view", "load_snapshot",
           "market_label", "snapshot_path"]
