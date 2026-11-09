"""产品分类: each published model's 产品类别, 产品系列 and 商品简称, and the guides beside them.

The 说明书资料库 and 产品矩阵 pages group products by 类别, then 系列, the way the
发布文档管理 Base classifies them. Since 2026-11-09 a product is classified once,
on its row of the 项目号 table (single-select 产品类别, 产品系列 and 容量档); each
网页文档 row names its 项目号 and shows the three values as lookups. A 网页文档 row's
文档类型 says whether it is a product's manual (产品说明书, also when blank), a
通用指南 (a guide that belongs to no one product) or a 快速指南 (a product's
separate quick guide); a guide lists the models it covers in 适用产品, which a
快速指南 must fill with its product. The RTD build cannot reach Feishu, so both pages read a repository
snapshot, ``product_catalog.json`` (the ``product_catalog`` domain of
``source_registry.yaml``). ``refresh`` rewrites it read-only:

- ``categories``: the 项目号 table's 产品类别 options in their order, each with the
  产品系列 options its models use, in that field's order;
- ``capacity_tiers``: the 项目号 table's 容量档 options its models use, in their
  order (1度以下 … 5度电); the 产品矩阵 lays its columns out by them;
- ``models``: every model a 产品说明书 row's 型号 cell lists, with the row's 类别,
  系列, any 容量档 (太阳能板 and 配件 have none) and the 商品简称 at the same
  position of its 商品简称 cell. A model listed
  after the first one (a colour edition sold with the first model's manual, such
  as JE-1000F-SG on the JE-1000F US pages) also records ``pages_of`` and the
  routes it shares, unless it has rows of its own;
- ``guides``: every 通用指南 and 快速指南 by its document code (the 型号 cell, which
  is also the first segment of its route): its kind, 商品简称, routes and 适用产品.

A manual row without a 类别 or 系列 is skipped and reported; rows that disagree
about a model or a guide, a 型号 and 商品简称 cell of different lengths, or a guide
whose link opens another route fail the refresh and keep the previous snapshot.
The 项目号 only joins the two tables inside Feishu and is never read, nor is a
SKU: the snapshot sits in a public repository.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from tools.rtd.web_progress import route_of
from tools.rtd.web_reviews import text_of

DOMAIN = "product_catalog"
SNAPSHOT = "product_catalog.json"
SCHEMA = "hello-docs-product-catalog/v3"
SOURCE = "飞书发布文档管理「网页文档」表与「项目号」表"
PROJECT_TABLE = "项目号"
MODEL_FIELD, SHORT_FIELD, LINK_FIELD = "型号", "商品简称", "超链接"
CATEGORY_FIELD, SERIES_FIELD, CAPACITY_FIELD = "产品类别", "产品系列", "容量档"
DOC_TYPE_FIELD, APPLIES_FIELD = "文档类型", "适用产品"
MANUAL, GUIDE, QUICK = "产品说明书", "通用指南", "快速指南"
KINDS = (MANUAL, GUIDE, QUICK)

_SPLIT = re.compile(r"[,，、;；\n]+")
_MODEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_ROUTE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z]{2,3}(?:-[A-Za-z]{2,4})?/[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*")


class CatalogError(ValueError):
    """The 网页文档 table cannot give a sound catalog."""


def cell_list(value: object) -> list[str]:
    """The comma-separated entries of a text cell, in order."""
    return [part.strip() for part in _SPLIT.split(text_of(value)) if part.strip()]


def field_options(fields: Iterable[object], name: str) -> list[str]:
    """A single-select field's option names in the table's order (lark-cli or Open API field shape)."""
    for field in fields:
        if isinstance(field, dict) and str(field.get("field_name") or field.get("name") or "") == name:
            options = field.get("options") or (field.get("property") or {}).get("options") or []
            names = [str(option.get("name") or "").strip() for option in options if isinstance(option, dict)]
            if not any(names):
                raise CatalogError(f"the {name} field lists no options")
            return [option for option in names if option]
    raise CatalogError(f"the 网页文档 table has no {name} field")


def _row(record: str, row: dict[str, Any], categories: list[str], series: list[str],
         tiers: list[str]) -> tuple[list[str], list[str], dict[str, str], str] | str:
    """A row's models, short names, classification (类别, 系列 and any 容量档) and route, or why it is skipped."""
    models, shorts = cell_list(row.get(MODEL_FIELD)), cell_list(row.get(SHORT_FIELD))
    category, line = text_of(row.get(CATEGORY_FIELD)), text_of(row.get(SERIES_FIELD))
    if not models:
        return f"{record}: no 型号"
    if not category or not line:
        return f"{record} ({models[0]}): no {CATEGORY_FIELD} or {SERIES_FIELD}"
    bad = [model for model in models if not _MODEL.fullmatch(model)]
    if bad:
        raise CatalogError(f"{record}: 型号 {bad} is not a model code")
    if len(shorts) != len(models):
        raise CatalogError(f"{record}: 型号 lists {len(models)} models but 商品简称 {len(shorts)} names")
    if category not in categories or line not in series:
        raise CatalogError(f"{record}: {category}/{line} is not an option of {CATEGORY_FIELD}/{SERIES_FIELD}")
    capacity = text_of(row.get(CAPACITY_FIELD))
    if capacity and capacity not in tiers:
        raise CatalogError(f"{record}: {CAPACITY_FIELD} {capacity!r} is not an option of the 项目号 table")
    route = route_of(row.get(LINK_FIELD))
    if route and route.split("/")[0] != models[0]:
        raise CatalogError(f"{record}: the link opens {route}, but 型号 starts with {models[0]}")
    classes = {"category": category, "series": line, **({"capacity": capacity} if capacity else {})}
    return models, shorts, classes, route


def doc_type(record: str, row: dict[str, Any]) -> str:
    """A row's 文档类型; a blank cell is a product's manual."""
    kind = text_of(row.get(DOC_TYPE_FIELD)) or MANUAL
    if kind not in KINDS:
        raise CatalogError(f"{record}: 文档类型 {kind!r} is not one of {'/'.join(KINDS)}")
    return kind


def _guide(record: str, row: dict[str, Any], kind: str) -> tuple[str, str, str, list[str]]:
    """A guide row's document code, 商品简称, route and the models its 适用产品 cell lists; a 快速指南 needs them."""
    codes, shorts = cell_list(row.get(MODEL_FIELD)), cell_list(row.get(SHORT_FIELD))
    if len(codes) != 1 or not _MODEL.fullmatch(codes[0]) or len(shorts) != 1:
        raise CatalogError(f"{record}: a {kind} needs one document code in 型号 and one 商品简称")
    route = route_of(row.get(LINK_FIELD))
    if not route or route.split("/")[0] != codes[0]:
        raise CatalogError(f"{record}: the {kind} {codes[0]} must link to its own route, not {route or 'nothing'}")
    applies = list(dict.fromkeys(cell_list(row.get(APPLIES_FIELD))))
    bad = [model for model in applies if not _MODEL.fullmatch(model)]
    if bad:
        raise CatalogError(f"{record}: 适用产品 {bad} is not a model code")
    if kind == QUICK and not applies:
        raise CatalogError(f"{record}: the {QUICK} {codes[0]} must name its product in 适用产品")
    return codes[0], shorts[0], route, applies


def _add_guide(guides: dict[str, dict[str, Any]], record: str, row: dict[str, Any], kind: str) -> None:
    code, short, route, applies = _guide(record, row, kind)
    entry = guides.setdefault(code, {"kind": kind, "short": short, "routes": set(), "applies_to": []})
    if (entry["kind"], entry["short"]) != (kind, short):
        raise CatalogError(f"{code}: rows disagree on its 文档类型 or 商品简称 "
                           f"({entry['kind']}/{entry['short']} and {kind}/{short})")
    entry["routes"].add(route)
    entry["applies_to"] = list(dict.fromkeys([*entry["applies_to"], *applies]))


def catalog_from_rows(fields: Iterable[object], rows: Iterable[tuple[str, dict[str, Any]]], *,
                      today: dt.date) -> tuple[dict[str, Any], list[str]]:
    """The snapshot from the 项目号 table's field schema and the 网页文档 rows, and the rows it skipped."""
    category_order, series_order = field_options(fields, CATEGORY_FIELD), field_options(fields, SERIES_FIELD)
    tier_order = field_options(fields, CAPACITY_FIELD)
    models: dict[str, dict[str, str]] = {}
    own: set[str] = set()
    shared: dict[str, dict[str, Any]] = {}
    guides: dict[str, dict[str, Any]] = {}
    skipped: list[str] = []
    for record, row in rows:
        kind = doc_type(record, row)
        if kind != MANUAL:
            _add_guide(guides, record, row, kind)
            continue
        parsed = _row(record, row, category_order, series_order, tier_order)
        if isinstance(parsed, str):
            skipped.append(parsed)
            continue
        names, shorts, classes, route = parsed
        for position, (model, short) in enumerate(zip(names, shorts, strict=True)):
            entry = {**classes, "short": short}
            if models.setdefault(model, entry) != entry:
                raise CatalogError(f"{model}: rows disagree ({models[model]} and {entry})")
            if position == 0:
                own.add(model)
                continue
            share = shared.setdefault(model, {"pages_of": names[0], "routes": set()})
            if share["pages_of"] != names[0]:
                raise CatalogError(f"{model}: listed after both {share['pages_of']} and {names[0]}")
            share["routes"].update([route] if route else [])
    for model, share in shared.items():
        if model not in own:
            models[model] = {**models[model], "pages_of": share["pages_of"], "routes": sorted(share["routes"])}
    snapshot = _snapshot(models, guides, (category_order, series_order, tier_order), today)
    problems = catalog_problems(snapshot)
    if problems:
        raise CatalogError("; ".join(problems))
    return snapshot, skipped


def _snapshot(models: dict[str, dict[str, Any]], guides: dict[str, dict[str, Any]],
              orders: tuple[list[str], list[str], list[str]], today: dt.date) -> dict[str, Any]:
    """The snapshot: the used categories, series and 容量档 in the 项目号 table's option order, then the entries."""
    category_order, series_order, tier_order = orders
    both = sorted(set(guides) & set(models))
    if both:
        raise CatalogError(f"{both} is both a model and a {GUIDE}")
    used = {(entry["category"], entry["series"]) for entry in models.values()}
    categories = [{"name": category, "series": [line for line in series_order if (category, line) in used]}
                  for category in category_order if any(cat == category for cat, _ in used)]
    capacities = {entry.get("capacity") for entry in models.values()}
    return {"schema": SCHEMA, "exported_at": today.isoformat(), "source": SOURCE,
            "categories": categories, "capacity_tiers": [tier for tier in tier_order if tier in capacities],
            "models": dict(sorted(models.items())),
            "guides": {code: {**entry, "routes": sorted(entry["routes"])} for code, entry in sorted(guides.items())}}


def _categories_problems(categories: object) -> tuple[list[str], dict[str, list[str]]]:
    if not isinstance(categories, list) or not categories:
        return ["categories must be a non-empty list"], {}
    order: dict[str, list[str]] = {}
    for item in categories:
        name = item.get("name") if isinstance(item, dict) else None
        series = item.get("series") if isinstance(item, dict) else None
        if not isinstance(name, str) or not name.strip() or name in order or not isinstance(series, list) \
                or not series or not all(isinstance(s, str) and s.strip() for s in series) or len(set(series)) != len(series):
            return ["each category needs a unique name and its distinct series"], {}
        order[name] = series
    return [], order


def _model_problems(model: str, entry: object, order: dict[str, list[str]], models: dict[str, Any],
                    tiers: list[str]) -> list[str]:
    if not _MODEL.fullmatch(model) or not isinstance(entry, dict):
        return [f"models.{model} is not a model entry"]
    if entry.get("series") not in order.get(str(entry.get("category")), []):
        return [f"models.{model}: {entry.get('category')}/{entry.get('series')} is not a listed category and series"]
    if not isinstance(entry.get("short"), str) or not entry["short"].strip():
        return [f"models.{model} needs a 商品简称"]
    if set(entry) - {"category", "series", "capacity", "short", "pages_of", "routes"}:
        return [f"models.{model} has unknown keys"]
    if "capacity" in entry and entry["capacity"] not in tiers:
        return [f"models.{model}: 容量档 {entry['capacity']!r} is not a listed capacity tier"]
    if ("pages_of" in entry) != ("routes" in entry):
        return [f"models.{model}: pages_of and routes come together"]
    if "pages_of" in entry and (entry["pages_of"] not in models or entry["pages_of"] == model or not isinstance(
            entry["routes"], list) or not all(isinstance(r, str) and _ROUTE.fullmatch(r) for r in entry["routes"])):
        return [f"models.{model}: pages_of must name another listed model, with its routes"]
    return []


def catalog_problems(data: object) -> list[str]:
    """Why a snapshot cannot be used; empty when it is sound."""
    if not isinstance(data, dict):
        return ["the snapshot is not a JSON object"]
    problems = [] if data.get("schema") == SCHEMA else [f"schema is {data.get('schema')!r}, expected {SCHEMA!r}"]
    try:
        dt.date.fromisoformat(str(data.get("exported_at")))
    except ValueError:
        problems.append(f"exported_at {data.get('exported_at')!r} is not an ISO date")
    found, order = _categories_problems(data.get("categories"))
    tiers = data.get("capacity_tiers")
    if not isinstance(tiers, list) or not all(isinstance(t, str) and t.strip() for t in tiers) \
            or len(set(tiers)) != len(tiers):
        problems.append("capacity_tiers must list distinct 容量档 names in their order")
        tiers = []
    models = data.get("models")
    if not isinstance(models, dict) or not models:
        return problems + found + ["models must map each model to its category, series and 商品简称"]
    for model, entry in models.items():
        problems += _model_problems(str(model), entry, order, models, tiers)
    guides = data.get("guides")
    if not isinstance(guides, dict):
        return problems + found + ["guides must map each guide to its kind, 商品简称, routes and 适用产品"]
    for code, entry in guides.items():
        problems += _guide_problems(str(code), entry, models)
    return problems + found


def _guide_problems(code: str, entry: object, models: dict[str, Any]) -> list[str]:
    if not _MODEL.fullmatch(code) or not isinstance(entry, dict) \
            or set(entry) != {"kind", "short", "routes", "applies_to"} or entry["kind"] not in (GUIDE, QUICK):
        return [f"guides.{code} is not a guide entry"]
    if code in models:
        return [f"guides.{code} is also a model"]
    if not isinstance(entry["short"], str) or not entry["short"].strip():
        return [f"guides.{code} needs a 商品简称"]
    routes, applies = entry["routes"], entry["applies_to"]
    if not isinstance(routes, list) or not routes or not all(
            isinstance(r, str) and _ROUTE.fullmatch(r) and r.split("/")[0] == code for r in routes):
        return [f"guides.{code} needs its own routes"]
    if not isinstance(applies, list) or not all(isinstance(m, str) and _MODEL.fullmatch(m) for m in applies) \
            or (entry["kind"] == QUICK and not applies):
        return [f"guides.{code}: 适用产品 must list model codes (a {QUICK} at least its product)"]
    return []


def load_catalog(assets: Path) -> tuple[dict[str, Any] | None, list[str]]:
    """The snapshot (business-owned copy first), or None and why it cannot be used."""
    from tools.workspace_snapshot import snapshot_path

    path = snapshot_path(assets, SNAPSHOT)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, [f"cannot read {path.name}: {exc}"]
    problems = catalog_problems(data)
    return (None if problems else data), problems


def short_names(catalog: dict[str, Any] | None) -> dict[str, str]:
    """``{model or guide code: 商品简称}`` from the snapshot."""
    entries = {**(catalog or {}).get("models", {}), **(catalog or {}).get("guides", {})}
    return {code: entry["short"] for code, entry in entries.items()}


def classify(products: list[dict[str, Any]], catalog: dict[str, Any] | None) -> list[str]:
    """Give each portal product its ``product_category`` and ``product_series``, mark each guide with its kind
    (通用指南 or 快速指南), link each product to the guides of its market that list it in 适用产品, and return the
    models left out."""
    models, guides = (catalog or {}).get("models", {}), (catalog or {}).get("guides", {})
    missing = []
    for product in products:
        entry = models.get(product["model"])
        product["product_category"] = entry["category"] if entry else ""
        product["product_series"] = entry["series"] if entry else ""
        product["guide"] = guides[product["model"]]["kind"] if product["model"] in guides else ""
        product["related_guides"] = []
        if entry is None and not product["guide"] and product["model"] not in missing:
            missing.append(product["model"])
    for guide in (product for product in products if product["guide"]):
        covered = set(guides[guide["model"]]["applies_to"])
        for product in products:
            if product["model"] in covered and product["region"] == guide["region"]:
                entry = guides[guide["model"]]
                product["related_guides"].append({"model": guide["model"], "kind": entry["kind"],
                                                  "short": entry["short"], "url": guide["url"]})
    return missing


def _field_items(payload: object) -> list[object]:
    data = payload.get("data") if isinstance(payload, dict) else None
    items = (data.get("fields") if isinstance(data, dict) and data.get("fields") is not None
             else data.get("items") if isinstance(data, dict) else None)
    if not isinstance(items, list):
        raise CatalogError("the field list has no fields")
    return items


def project_table_id(run, base_token: str) -> str:
    """The id of the Base's 项目号 table, found by its name."""
    payload = run(["base", "+table-list", "--base-token", base_token, "--format", "json"])
    data = payload.get("data") if isinstance(payload, dict) else None
    tables = data.get("tables") or data.get("items") if isinstance(data, dict) else None
    found = [str(table.get("id") or table.get("table_id") or "") for table in tables or []
             if isinstance(table, dict) and str(table.get("name") or "") == PROJECT_TABLE]
    if len(found) != 1 or not found[0]:
        raise CatalogError(f"the Base has {len(found)} tables named {PROJECT_TABLE}")
    return found[0]


def export_catalog(*, run, base_token: str, table_id: str, today: dt.date,
                   project_table: str = "") -> tuple[dict[str, Any], list[str]]:
    """Read the 项目号 table's field schema and every 网页文档 row (read-only) and build the snapshot."""
    from tools.workspace_snapshot import complete_rows

    project_table = project_table or project_table_id(run, base_token)
    fields = _field_items(run(["base", "+field-list", "--base-token", base_token, "--table-id", project_table,
                               "--format", "json", "--limit", "200", "--offset", "0"]))
    _, rows = complete_rows(run, base_token, table_id)
    return catalog_from_rows(fields, rows, today=today)


def _summary(snapshot: dict[str, Any]) -> str:
    counts = {item["name"]: sum(1 for entry in snapshot["models"].values() if entry["category"] == item["name"])
              for item in snapshot["categories"]}
    return f"{len(snapshot['models'])} models · " + " · ".join(f"{name} {count}" for name, count in counts.items())


def main(argv: list[str] | None = None) -> int:
    from tools.rtd.portal import ASSETS

    parser = argparse.ArgumentParser(description="The 产品分类 snapshot of the 网页文档 table (read-only).")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="validate the committed snapshot")
    check.add_argument("--snapshot", type=Path, default=None)
    refresh = commands.add_parser("refresh", help="rewrite the snapshot from the 网页文档 table")
    refresh.add_argument("--output", type=Path, default=None)
    refresh.add_argument("--base-token", default=os.environ.get("FEISHU_PUBLISHED_DOCS_BASE_TOKEN", ""))
    refresh.add_argument("--table-id", default=os.environ.get("FEISHU_PUBLISHED_DOCS_WEB_TABLE_ID", ""))
    refresh.add_argument("--project-table-id", default=os.environ.get("FEISHU_PUBLISHED_DOCS_PROJECT_TABLE_ID", ""),
                         help="the 项目号 table (default: the Base's table of that name)")
    refresh.add_argument("--cli-bin", default="lark-cli", help='lark-cli command, e.g. "lark-cli --profile prod"')
    refresh.add_argument("--as", dest="identity", default=os.environ.get("FEISHU_PUBLISHED_DOCS_IDENTITY", "bot"))
    refresh.add_argument("--dry-run", action="store_true", help="print the result without writing the snapshot")
    args = parser.parse_args(argv)

    if args.command == "check":
        path = args.snapshot or ASSETS / SNAPSHOT
        try:
            problems = catalog_problems(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError) as exc:
            problems = [f"cannot read {path}: {exc}"]
        for problem in problems:
            print(f"ERROR   {problem}")
        return 1 if problems else 0
    if not args.base_token or not args.table_id:
        print("ERROR   set FEISHU_PUBLISHED_DOCS_BASE_TOKEN and FEISHU_PUBLISHED_DOCS_WEB_TABLE_ID (or pass them)")
        return 2
    from tools.rtd.system_workspace import lark_runner

    try:
        snapshot, skipped = export_catalog(run=lark_runner(args.cli_bin, args.identity), base_token=args.base_token,
                                           table_id=args.table_id, project_table=args.project_table_id,
                                           today=dt.datetime.now(dt.UTC).date())
    except (CatalogError, RuntimeError, OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"ERROR   refresh failed ({type(exc).__name__}: {exc}); snapshot unchanged")
        return 1
    for reason in skipped:
        print(f"SKIPPED {reason}")
    if args.dry_run:
        print(f"dry run: {_summary(snapshot)}")
        return 0
    from tools.workspace_snapshot import atomic_json

    output = args.output or ASSETS / SNAPSHOT
    atomic_json(output, snapshot)
    print(f"wrote {output.name}: {_summary(snapshot)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
