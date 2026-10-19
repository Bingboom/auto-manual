"""网页说明书进度 on the 说明书工作台 交付物 tab: what is online, per market, and what is left.

The tab shows Web manuals only. Read at build time, with no network:

- ``docs/publish/publish_manifest.json``: every online language version, so the
  counts, the per-market bars and the coverage matrix are always current.
- the committed snapshot of the ``web_progress`` source-registry domain, which
  ``export`` writes (read-only) from two places:

  - the Feishu 网页文档 table of the 发布文档管理 Base: ``checked`` lists the
    routes whose 内容是否核对 box is ticked, and ``sold`` the markets of the
    active SKUs each row links in 规格型号 (models with a Web manual only);
  - the publish manifest's git history: ``timeline`` dates each current
    language version by the first commit that listed it, a renamed legacy
    route counting from its old name.

A missing or unsound snapshot hides only 待转, 已核对 and the timeline, with a
Sphinx warning; one older than the domain's ``stale_after_days`` shows 待复核.
Only markets and counts of published models leave Feishu: no SKU codes,
project codes or unpublished models are written, because the snapshot is
committed to a public repository and shown on the site.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlsplit

from tools.rtd.source_registry import load_registry, stale_reason
from tools.utils.path_utils import Paths, PathSegments, repo_root
from tools.workspace_snapshot import complete_rows, digest, save_snapshot, snapshot_path

ASSETS = Path(__file__).resolve().parents[1] / "rtd_portal_assets"
DOMAIN = "web_progress"
SNAPSHOT_SCHEMA = "hello-docs-web-progress/v1"

# 网页文档 table columns.
LINK_FIELD = "超链接"
CHECK_FIELD = "内容是否核对"
SKU_FIELD = "规格型号"

# Market columns in display order, and the market each SKU code counts toward.
_MARKETS = json.loads((ASSETS / "web_progress.json").read_text(encoding="utf-8"))
MARKET_ORDER: tuple[str, ...] = tuple(_MARKETS["markets"])
SKU_MARKETS: dict[str, str] = dict(_MARKETS["sku_markets"])
CATEGORIES = (("JE-", "电源主机"), ("JHP-", "电源主机"), ("JBP-", "扩容电池"), ("JS-", "太阳能板"))
OTHER_CATEGORY = "配件"
CATEGORY_ORDER = ("电源主机", "扩容电池", "太阳能板", OTHER_CATEGORY)

_SKU = re.compile(r"^\s*[A-Z]{3}[0-9A-Z]*-([A-Z]{2}(?:/[A-Z]{2,5})*)-")
_RETIRED = re.compile(r"停用|禁用|作废|样品|假机")
_ROUTE = re.compile(r"/([A-Za-z0-9][A-Za-z0-9._-]*)/([A-Za-z]{2,3}(?:-[A-Za-z]{2,4})?)/([a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*)/md/")
_ROUTE_KEY = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z]{2,3}(?:-[A-Za-z]{2,4})?/[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*")
_MODEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


# --- cell reading -----------------------------------------------------------------


def _strings(value: object) -> list[str]:
    """Every text inside a cell: lookup lists, rich-text segments, hyperlink objects."""
    if value is None:
        return []
    if isinstance(value, dict):
        found = [text for key in ("link", "url", "text", "name") for text in _strings(value.get(key))]
        return found or _strings(value.get("value"))
    if isinstance(value, list):
        return [text for item in value for text in _strings(item)]
    return [str(value)]


def route_of(value: object) -> str:
    """``MODEL/REGION/LANG`` of a Web manual link on this site, else ""."""
    for text in _strings(value):
        for url in re.findall(r"https://[^\s\]\)\"'<>]+", text):
            match = _ROUTE.search(urlsplit(url).path + "/")
            if match:
                return "/".join(match.groups())
    return ""


def is_checked(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return any(text.strip().lower() in {"true", "1", "是", "yes"} for text in _strings(value))


def sku_markets(value: object) -> set[str]:
    """Markets of the active SKUs in a 规格型号 cell; retired, disabled and sample SKUs are skipped."""
    markets: set[str] = set()
    for text in _strings(value):
        for spec in re.split(r"[,\n]", text):
            match = _SKU.match(spec)
            if not match or _RETIRED.search(spec):
                continue
            markets.update(SKU_MARKETS[code] for code in match.group(1).split("/") if code in SKU_MARKETS)
    return markets


def _market_rank(code: str) -> int:
    return MARKET_ORDER.index(code) if code in MARKET_ORDER else len(MARKET_ORDER)


# --- export (the only Feishu read) -----------------------------------------------------


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout


def _first_seen(repo: Path, path: str, ref: str) -> dict[str, str]:
    """The first day each route appears in ``path`` along ``ref``'s first-parent history."""
    commits = [line.split(" ", 1) for line in _git(repo, "log", "--first-parent", "--format=%H %cI", ref).splitlines() if line]
    first_seen: dict[str, str] = {}
    last_blob = ""
    with subprocess.Popen(["git", "-C", str(repo), "cat-file", "--batch"], stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE) as proc:
        assert proc.stdin is not None and proc.stdout is not None
        for sha, when in reversed(commits):
            proc.stdin.write(f"{sha}:{path}\n".encode())
            proc.stdin.flush()
            header = proc.stdout.readline().decode().split()
            if len(header) < 3 or header[1] != "blob":
                continue
            body = proc.stdout.read(int(header[2]))
            proc.stdout.read(1)
            if header[0] != last_blob:
                last_blob = header[0]
                for route in _routes(body):
                    first_seen.setdefault(route, when[:10])
        proc.stdin.close()
    return first_seen


def _routes(body: bytes) -> list[str]:
    try:
        targets = json.loads(body).get("targets") or []
    except (ValueError, AttributeError):
        return []
    return [str(t["route"]) for t in targets if isinstance(t, dict) and t.get("route")]


def _cumulative(dated: dict[tuple[str, str, str], str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    langs: set[tuple[str, str, str]] = set()
    editions: set[tuple[str, str]] = set()
    models: set[str] = set()
    for day in sorted(set(dated.values())):
        added = [key for key, seen in dated.items() if seen == day]
        langs.update(added)
        editions.update((model, region) for model, region, _ in added)
        models.update(model for model, _, _ in added)
        rows.append({"date": day, "added": len(added), "langs": len(langs),
                     "editions": len(editions), "models": len(models)})
    return rows


def manifest_history(repo: Path, ref: str = "HEAD") -> list[dict[str, Any]]:
    """Cumulative counts per day on which the current catalogue grew, from first-parent history.

    Each current language version counts from the first commit that listed it,
    a renamed legacy route from its old name. Needs the full history: a
    shallow clone would date everything at its cut.
    """
    if _git(repo, "rev-parse", "--is-shallow-repository").strip() == "true":
        raise RuntimeError("manifest history needs a full clone (git fetch --unshallow)")
    path = (Paths(repo).docs_publish_dir / PathSegments.PUBLISH_MANIFEST_JSON).relative_to(repo).as_posix()
    first_seen = _first_seen(repo, path, ref)
    dated: dict[tuple[str, str, str], str] = {}
    for target in json.loads(_git(repo, "show", f"{ref}:{path}"))["targets"]:
        names = [target["route"], target.get("legacy_route"), *(target.get("legacy_routes") or [])]
        days = [first_seen[name] for name in names if name and name in first_seen]
        if days:
            dated[(target["model"], target["region"], target["lang"])] = min(days)
    return _cumulative(dated)


def export_snapshot(*, run, base_token: str, table_id: str, timeline: list[dict[str, Any]],
                    today: dt.date) -> dict[str, Any]:
    """The 网页文档 table's 核对 ticks and active-SKU markets, with ``timeline``; read-only."""
    header, records = complete_rows(run, base_token, table_id)
    missing = [name for name in (LINK_FIELD, CHECK_FIELD, SKU_FIELD) if name not in header]
    if missing:
        raise RuntimeError(f"table {table_id} is missing columns {missing}")
    checked: set[str] = set()
    sold: dict[str, set[str]] = defaultdict(set)
    for _, row in records:
        route = route_of(row.get(LINK_FIELD))
        if not route:
            if is_checked(row.get(CHECK_FIELD)):
                raise RuntimeError("a checked 网页文档 row has no Web manual link")
            continue
        if is_checked(row.get(CHECK_FIELD)):
            checked.add(route)
        sold[route.split("/")[0]].update(sku_markets(row.get(SKU_FIELD)))
    return {"schema": SNAPSHOT_SCHEMA, "exported_at": today.isoformat(), "checked": sorted(checked),
            "sold": {model: sorted(markets, key=_market_rank) for model, markets in sorted(sold.items()) if markets},
            "timeline": timeline}


# --- snapshot ---------------------------------------------------------------------------


def _timeline_problems(timeline: object) -> list[str]:
    if not isinstance(timeline, list):
        return ["timeline is not a list"]
    problems, previous = [], None
    for index, row in enumerate(timeline):
        where = f"timeline[{index}]"
        counts = [row.get(key) for key in ("added", "langs", "editions", "models")] if isinstance(row, dict) else []
        if not counts or not all(type(n) is int and n >= 0 for n in counts):
            problems.append(f"{where} needs whole counts added, langs, editions and models")
            continue
        try:
            day = dt.date.fromisoformat(str(row.get("date")))
        except ValueError:
            problems.append(f"{where} has no ISO date")
            continue
        if previous and (day <= previous[0] or row["langs"] != previous[1] + row["added"]
                         or row["editions"] < previous[2] or row["models"] < previous[3]):
            problems.append(f"{where} does not follow the day before it")
        previous = (day, row["langs"], row["editions"], row["models"])
    return problems


def snapshot_problems(data: object) -> list[str]:
    """Why a snapshot cannot be shown; empty when it is sound."""
    if not isinstance(data, dict):
        return ["the snapshot is not a JSON object"]
    problems = []
    if data.get("schema") != SNAPSHOT_SCHEMA:
        problems.append(f"schema is {data.get('schema')!r}, expected {SNAPSHOT_SCHEMA!r}")
    try:
        dt.date.fromisoformat(str(data.get("exported_at")))
    except ValueError:
        problems.append(f"exported_at {data.get('exported_at')!r} is not an ISO date")
    checked = data.get("checked")
    if not isinstance(checked, list) or not all(isinstance(r, str) and _ROUTE_KEY.fullmatch(r) for r in checked) \
            or len(set(checked)) != len(checked):
        problems.append("checked must list distinct MODEL/REGION/LANG routes")
    sold = data.get("sold")
    if not isinstance(sold, dict) or not all(
            isinstance(model, str) and _MODEL.fullmatch(model) and isinstance(markets, list) and markets
            and all(m in MARKET_ORDER for m in markets) and len(set(markets)) == len(markets)
            for model, markets in sold.items()):
        problems.append("sold must map each model to its known markets")
    return problems + _timeline_problems(data.get("timeline"))


def load_snapshot(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, [f"cannot read {path.name}: {exc}"]
    problems = snapshot_problems(data)
    return (None if problems else data), problems


# --- view -------------------------------------------------------------------------------


def category(model: str) -> str:
    return next((label for prefix, label in CATEGORIES if model.startswith(prefix)), OTHER_CATEGORY)


def _region(region: str) -> str:
    """A locale-style region such as ``pt-BR`` reads as its market."""
    return region if region in MARKET_ORDER else region.rsplit("-", 1)[-1]


def _editions(targets: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    """``(model, market)`` -> the docname of each language and whether a route is legacy."""
    editions: dict[tuple[str, str], dict[str, Any]] = {}
    for target in targets:
        if not all(target.get(k) for k in ("model", "region", "lang", "route", "manual")):
            continue
        entry = editions.setdefault((target["model"], _region(target["region"])), {"langs": {}, "legacy": False})
        entry["langs"][target["lang"]] = f"{target['route']}/{PurePosixPath(target['manual']).stem}"
        entry["legacy"] = entry["legacy"] or target.get("language_scope") == "legacy_unspecified"
    return editions


def _online_cell(market: str, entry: dict[str, Any], expected: set[str], rank) -> dict[str, Any]:
    have, want = sorted(entry["langs"], key=rank), sorted(expected, key=rank)
    missing = [lang for lang in want if lang not in entry["langs"]]
    title = "已有 " + "、".join(lang.upper() for lang in have)
    if missing:
        title += "；缺 " + "、".join(lang.upper() for lang in missing)
    if entry["legacy"]:
        title += "；旧版路由，语言范围待核对"
    first = "en" if "en" in entry["langs"] else have[0]
    return {"market": market, "state": "full" if len(have) >= len(want) else "partial",
            "text": f"{len(have)}/{len(want)}", "legacy": entry["legacy"], "docname": entry["langs"][first], "title": title}


def _cell(model: str, market: str, editions, expected, sold, labels, rank) -> dict[str, Any]:
    entry = editions.get((model, market))
    if entry:
        return _online_cell(market, entry, expected[market], rank)
    if market in sold.get(model, []):
        return {"market": market, "state": "gap", "text": "待转", "legacy": False, "docname": "",
                "title": f"{labels.get(market, market)}有在用 SKU，还没有网页说明书"}
    return {"market": market, "state": "", "text": "", "legacy": False, "docname": "", "title": ""}


def _market_rows(rows: list[dict[str, Any]], markets: list[str], labels: dict[str, str]) -> list[dict[str, Any]]:
    totals = {m: {"full": 0, "partial": 0, "gap": 0} for m in markets}
    for row in rows:
        for cell in row["cells"]:
            if cell["state"]:
                totals[cell["market"]][cell["state"]] += 1
    bar_max = max([sum(t.values()) for t in totals.values()] or [0]) or 1
    return [{"code": m, "label": labels.get(m, m), **totals[m], "online": totals[m]["full"] + totals[m]["partial"],
             "widths": {k: round(100 * totals[m][k] / bar_max, 2) for k in ("full", "partial", "gap")}}
            for m in markets]


def _snapshot_state(snapshot: dict[str, Any] | None, domain: dict[str, Any] | None, today: dt.date) -> tuple[str, list[str]]:
    if snapshot is None:
        return "", []
    exported = dt.date.fromisoformat(snapshot["exported_at"])
    reason = stale_reason(domain, exported, today) if domain else ""
    return exported.isoformat(), [reason] if reason else []


def progress_view(targets: list[dict[str, Any]] | None, snapshot: dict[str, Any] | None, *,
                  labels: dict[str, str], names: dict[tuple[str, str], str],
                  language_order: Sequence[str], today: dt.date,
                  domain: dict[str, Any] | None) -> dict[str, Any]:
    """Counts, per-market bars and the model × market matrix of the Web catalog.

    A cell's languages are counted against every language that market has
    online. ``snapshot`` adds 待转 (a market with active SKUs and no Web
    manual), the 已核对 count and the timeline; without it those stay empty.
    """
    editions = _editions(targets or [])
    expected: dict[str, set[str]] = defaultdict(set)
    for (_, market), entry in editions.items():
        expected[market].update(entry["langs"])
    sold = (snapshot or {}).get("sold") or {}
    models = sorted({model for model, _ in editions}, key=lambda m: (CATEGORY_ORDER.index(category(m)), m))
    markets = sorted({market for _, market in editions} | {m for model in models for m in sold.get(model, [])},
                     key=_market_rank)
    rank = _language_rank(language_order)
    display = _display_names(names)
    rows = [_row(model, display.get(model, ""), [_cell(model, market, editions, expected, sold, labels, rank)
                                                 for market in markets]) for model in models]
    market_rows = _market_rows(rows, markets, labels)
    exported, stale = _snapshot_state(snapshot, domain, today)
    return {
        "available": targets is not None,
        "snapshot": snapshot is not None,
        "snapshot_date": exported,
        "stale": stale,
        "kpis": _kpis(targets or [], snapshot, len(models), len(editions), market_rows),
        "markets": [{"code": m, "label": labels.get(m, m), "expected": len(expected.get(m, ()))} for m in markets],
        "market_rows": market_rows,
        "rows": rows,
        "categories": _categories(rows),
        "timeline": list((snapshot or {}).get("timeline") or []),
    }


def _language_rank(language_order: Sequence[str]):
    order = list(language_order)
    return lambda lang: ((order.index(lang) if lang in order else len(order)), lang)


def _display_names(names: dict[tuple[str, str], str]) -> dict[str, str]:
    display: dict[str, str] = {}
    for (model, _), name in names.items():
        if name:
            display.setdefault(model, name)
    return display


def _row(model: str, name: str, cells: list[dict[str, Any]]) -> dict[str, Any]:
    return {"model": model, "name": name, "category": category(model), "cells": cells,
            "gaps": sum(c["state"] == "gap" for c in cells), "partial": any(c["state"] == "partial" for c in cells)}


def _kpis(targets: list[dict[str, Any]], snapshot: dict[str, Any] | None, models: int, editions: int,
          market_rows: list[dict[str, Any]]) -> dict[str, Any]:
    routes = {"/".join((t["model"], t["region"], t["lang"])) for t in targets
              if all(t.get(k) for k in ("model", "region", "lang"))}
    return {"models": models, "editions": editions, "routes": len(routes),
            "checked": len(routes & set(snapshot["checked"])) if snapshot else None,
            "gaps": sum(m["gap"] for m in market_rows) if snapshot else None,
            "partial": sum(m["partial"] for m in market_rows)}


def _categories(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = {label: sum(1 for r in rows if r["category"] == label) for label in CATEGORY_ORDER}
    return [{"label": label, "count": count} for label, count in counts.items() if count]


def web_only(models: list[dict[str, Any]], regions: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """The deliverables matrix's models and regions narrowed to rows that carry a Web manual."""
    kept = [{**model, "rows": [row for row in model["rows"] if row["web"]]}
            for model in models if any(row["web"] for row in model["rows"])]
    present = {row["region"] for model in kept for row in model["rows"]}
    return kept, [region for region in regions if region["code"] in present]


def progress_page_context(assets: Path, targets: list[dict[str, Any]] | None, *, labels: dict[str, str],
                          names: dict[tuple[str, str], str], language_order: Sequence[str],
                          today: dt.date, warn) -> dict[str, Any]:
    """The view from the registered snapshot; problems go to ``warn``, the view still renders."""
    registry, problems = load_registry(assets)
    domain = (registry or {}).get(DOMAIN)
    snapshot = None
    if domain is not None:
        snapshot, problems = load_snapshot(snapshot_path(assets, str(domain["snapshot"])))
    if problems:
        warn("网页说明书进度 shows no 待转, 已核对 or timeline: " + "; ".join(problems[:3]))
    view = progress_view(targets, snapshot, labels=labels, names=names, language_order=language_order,
                         today=today, domain=domain)
    view["fallback"] = str((domain or {}).get("fallback") or "无数据")
    return view


# --- CLI --------------------------------------------------------------------------------


def _iso_date(value: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not an ISO date: {value!r}") from None


def _summary(snapshot: dict[str, Any]) -> str:
    last = (snapshot["timeline"] or [{}])[-1]
    return (f"{len(snapshot['sold'])} models with SKU markets, {len(snapshot['checked'])} checked routes, "
            f"timeline to {last.get('date', '—')} ({last.get('langs', 0)} language versions)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export or check the 网页说明书进度 snapshot.")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="validate the committed snapshot")
    check.add_argument("--snapshot", type=Path, default=None, help="default: the snapshot named in source_registry.yaml")
    check.add_argument("--today", type=_iso_date, default=None, help="ISO date used for staleness (default: today, UTC)")
    export = commands.add_parser("export", help="write the snapshot from the 网页文档 table and git history (read-only)")
    export.add_argument("--output", type=Path, default=None, help="default: the snapshot named in source_registry.yaml")
    export.add_argument("--base-token", default=os.environ.get("FEISHU_PUBLISHED_DOCS_BASE_TOKEN", ""),
                        help="发布文档管理 base token (default: $FEISHU_PUBLISHED_DOCS_BASE_TOKEN)")
    export.add_argument("--table-id", default=os.environ.get("FEISHU_PUBLISHED_DOCS_WEB_TABLE_ID", ""),
                        help="网页文档 table (default: $FEISHU_PUBLISHED_DOCS_WEB_TABLE_ID)")
    export.add_argument("--history-repo", type=Path, default=repo_root(),
                        help="full clone whose history carries docs/publish/publish_manifest.json (default: this repo)")
    export.add_argument("--ref", default="HEAD", help="history ref to read (default: HEAD)")
    export.add_argument("--cli-bin", default="lark-cli", help='lark-cli command, e.g. "lark-cli --profile prod"')
    export.add_argument("--as", dest="identity", default=os.environ.get("FEISHU_PUBLISHED_DOCS_IDENTITY", "bot"),
                        help="lark-cli identity (default: $FEISHU_PUBLISHED_DOCS_IDENTITY or bot)")
    export.add_argument("--today", type=_iso_date, default=None, help="export date to record (default: today, UTC)")
    args = parser.parse_args(argv)
    registry, problems = load_registry(ASSETS)
    if registry is None:
        print("ERROR   " + "; ".join(problems[:5]))
        return 1
    domain = registry[DOMAIN]
    default_snapshot = snapshot_path(ASSETS, str(domain["snapshot"]))
    today = args.today or dt.datetime.now(dt.timezone.utc).date()

    if args.command == "export":
        missing = [flag for flag, value in (("--base-token", args.base_token), ("--table-id", args.table_id)) if not value]
        if missing:
            print(f"ERROR   need {', '.join(missing)} (or the matching FEISHU_PUBLISHED_DOCS_* variables)")
            return 1
        from tools.rtd.system_workspace import lark_runner

        try:
            timeline = manifest_history(args.history_repo, args.ref)
            snapshot = export_snapshot(run=lark_runner(args.cli_bin, args.identity), base_token=args.base_token,
                                       table_id=args.table_id, timeline=timeline, today=today)
        except (RuntimeError, OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
            print(f"ERROR   export failed ({type(exc).__name__}: {exc}); previous snapshot retained")
            return 1
        output = args.output or default_snapshot
        previous, errors = load_snapshot(output) if output.exists() else (None, [])
        if errors:
            print("ERROR   invalid previous snapshot; repair before refresh")
            return 1
        try:
            result = save_snapshot(output, snapshot, previous=previous, validate=snapshot_problems,
                                   source={"identity_sha256": digest([args.base_token, args.table_id])})
        except (ValueError, OSError) as exc:
            print(f"ERROR   {exc}; previous snapshot retained")
            return 1
        saved = previous if result["status"] == "unchanged" and previous else snapshot
        print(f"{result['status']} {output}: {_summary(saved)}; snapshot dated {saved['exported_at']}")
        return 0

    path = args.snapshot or default_snapshot
    snapshot, problems = load_snapshot(path)
    for problem in problems:
        print(f"ERROR   {path.name}: {problem}")
    if snapshot is None:
        return 1
    reason = stale_reason(domain, dt.date.fromisoformat(snapshot["exported_at"]), today)
    if reason:
        print(f"WARNING {path.name}: {reason}; the page marks it 待复核 — rerun export")
    print(f"web progress snapshot: exported {snapshot['exported_at']}; {_summary(snapshot)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
