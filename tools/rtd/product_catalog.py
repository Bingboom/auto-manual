"""产品分类: each published model's 产品类别, 产品系列 and 商品简称, as the 网页文档 table records them.

The 说明书资料库 and 产品矩阵 pages group products by 类别, then 系列, the way the
网页文档 table of the 发布文档管理 Base classifies them. The RTD build cannot reach
Feishu, so both pages read a repository snapshot, ``product_catalog.json`` (the
``product_catalog`` domain of ``source_registry.yaml``). ``refresh`` rewrites it
read-only from the table:

- ``categories``: the 产品类别 options in the table's order, each with the 产品系列
  options its models use, in the table's order;
- ``models``: every model a row's 型号 cell lists, with the row's 类别 and 系列 and
  the 商品简称 at the same position of its 商品简称 cell. A model listed after the
  first one (a colour edition sold with the first model's manual, such as
  JE-1000F-SG on the JE-1000F US pages) also records ``pages_of`` and the routes
  it shares, unless it has rows of its own.

A row without a 类别 or 系列 is skipped and reported; rows that disagree about a
model, or a 型号 and 商品简称 cell of different lengths, fail the refresh and keep
the previous snapshot. Only these five columns are read, never a SKU or project
code: the snapshot sits in a public repository.
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
SCHEMA = "hello-docs-product-catalog/v1"
SOURCE = "飞书发布文档管理「网页文档」表"
MODEL_FIELD, SHORT_FIELD, LINK_FIELD = "型号", "商品简称", "超链接"
CATEGORY_FIELD, SERIES_FIELD = "产品类别", "产品系列"

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


def _row(record: str, row: dict[str, Any], categories: list[str],
         series: list[str]) -> tuple[list[str], list[str], str, str, str] | str:
    """A row's models, short names, 类别, 系列 and route, or why it is skipped."""
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
    route = route_of(row.get(LINK_FIELD))
    if route and route.split("/")[0] != models[0]:
        raise CatalogError(f"{record}: the link opens {route}, but 型号 starts with {models[0]}")
    return models, shorts, category, line, route


def catalog_from_rows(fields: Iterable[object], rows: Iterable[tuple[str, dict[str, Any]]], *,
                      today: dt.date) -> tuple[dict[str, Any], list[str]]:
    """The snapshot from the table's field schema and rows, and the rows it skipped."""
    category_order, series_order = field_options(fields, CATEGORY_FIELD), field_options(fields, SERIES_FIELD)
    models: dict[str, dict[str, str]] = {}
    own: set[str] = set()
    shared: dict[str, dict[str, Any]] = {}
    skipped: list[str] = []
    for record, row in rows:
        parsed = _row(record, row, category_order, series_order)
        if isinstance(parsed, str):
            skipped.append(parsed)
            continue
        names, shorts, category, line, route = parsed
        for position, (model, short) in enumerate(zip(names, shorts, strict=True)):
            entry = {"category": category, "series": line, "short": short}
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
    used = {(entry["category"], entry["series"]) for entry in models.values()}
    categories = [{"name": category, "series": [line for line in series_order if (category, line) in used]}
                  for category in category_order if any(cat == category for cat, _ in used)]
    snapshot = {"schema": SCHEMA, "exported_at": today.isoformat(), "source": SOURCE,
                "categories": categories, "models": dict(sorted(models.items()))}
    problems = catalog_problems(snapshot)
    if problems:
        raise CatalogError("; ".join(problems))
    return snapshot, skipped


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


def _model_problems(model: str, entry: object, order: dict[str, list[str]], models: dict[str, Any]) -> list[str]:
    if not _MODEL.fullmatch(model) or not isinstance(entry, dict):
        return [f"models.{model} is not a model entry"]
    if entry.get("series") not in order.get(str(entry.get("category")), []):
        return [f"models.{model}: {entry.get('category')}/{entry.get('series')} is not a listed category and series"]
    if not isinstance(entry.get("short"), str) or not entry["short"].strip():
        return [f"models.{model} needs a 商品简称"]
    if set(entry) - {"category", "series", "short", "pages_of", "routes"}:
        return [f"models.{model} has unknown keys"]
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
    models = data.get("models")
    if not isinstance(models, dict) or not models:
        return problems + found + ["models must map each model to its category, series and 商品简称"]
    for model, entry in models.items():
        problems += _model_problems(str(model), entry, order, models)
    return problems + found


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
    """``{model: 商品简称}`` from the snapshot."""
    return {model: entry["short"] for model, entry in (catalog or {}).get("models", {}).items()}


def classify(products: list[dict[str, Any]], catalog: dict[str, Any] | None) -> list[str]:
    """Give each portal product its ``product_category`` and ``product_series``; the models left out."""
    models = (catalog or {}).get("models", {})
    missing = []
    for product in products:
        entry = models.get(product["model"])
        product["product_category"] = entry["category"] if entry else ""
        product["product_series"] = entry["series"] if entry else ""
        if entry is None and product["model"] not in missing:
            missing.append(product["model"])
    return missing


def _field_items(payload: object) -> list[object]:
    data = payload.get("data") if isinstance(payload, dict) else None
    items = (data.get("fields") if isinstance(data, dict) and data.get("fields") is not None
             else data.get("items") if isinstance(data, dict) else None)
    if not isinstance(items, list):
        raise CatalogError("the field list has no fields")
    return items


def export_catalog(*, run, base_token: str, table_id: str, today: dt.date) -> tuple[dict[str, Any], list[str]]:
    """Read the table's field schema and every row (read-only) and build the snapshot."""
    from tools.workspace_snapshot import complete_rows

    fields = _field_items(run(["base", "+field-list", "--base-token", base_token, "--table-id", table_id,
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
                                           table_id=args.table_id, today=dt.datetime.now(dt.UTC).date())
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
