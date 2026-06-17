#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Query the Feishu "发布文档管理" (published-manual catalog) Base for OpenClaw chat.

Self-contained: shells out to ``lark-cli`` only, no repo-internal imports, so it
runs unchanged from the source repo or the one-way Hello-Docs mirror checkout.

The catalog table lists each shipped product manual with its model, multilingual
product names, region, version, document type, lifecycle stage, owners, and the
canonical manual link (DingTalk alidocs). Use it to answer chat asks like
"JE-2000F 的说明书" or "给我看下产品总览".

Bindings default to the live table but can be overridden by flags or env vars
(FEISHU_PUBLISHED_DOCS_WIKI_TOKEN / _TABLE_ID / _VIEW_ID / _BASE_TOKEN). The base
token is resolved from the stable wiki node at runtime, so a Base copy that keeps
the same wiki node keeps working without a code change.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter

DEFAULT_WIKI_TOKEN = "QKNGwHFwPiY7J7kZ0bzcximKnyb"
DEFAULT_TABLE_ID = "tbldqnNBxFQsxpeN"
DEFAULT_VIEW_ID = "vewytqcvDc"
DEFAULT_PAGE_SIZE = 100
DEFAULT_MAX_RECORDS = 2000

# Fields searched for a free-text product/manual lookup.
SEARCH_FIELDS = (
    "产品型号",
    "产品简称",
    "产品名称_en",
    "产品名称_jp",
    "产品名称_zh",
    "产品名称_kr",
    "说明书名称",
    "文档名称",
    "项目",
    "业务号",
)
# Fields shown in a per-manual result block, in display order.
DETAIL_FIELDS = (
    "产品型号",
    "产品名称_zh",
    "区域",
    "文档类型",
    "源语言",
    "版本",
    "产品阶段",
    "分类",
    "归档日期",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Query the Feishu published-manual catalog table for OpenClaw chat."
    )
    p.add_argument("query", nargs="?", default=None, help="Free-text product/manual search (model, name, project…)")
    p.add_argument("--search", dest="query", default=None, help="Alias for the positional query")
    p.add_argument("--overview", action="store_true", help="Show catalog summary counts instead of records")
    p.add_argument("--list", dest="list_all", action="store_true", help="List every catalog row (subject to filters)")
    p.add_argument("--region", default=None, help="Filter by 区域 substring, e.g. 美加规 / 日规 / 欧英规")
    p.add_argument("--doc-type", default=None, help="Filter by 文档类型 substring, e.g. User Manual")
    p.add_argument("--stage", default=None, help="Filter by 产品阶段 substring, e.g. PVT")
    p.add_argument("--category", default=None, help="Filter by 分类 substring, e.g. 便携储能-主机")
    p.add_argument("--latest-only", action="store_true", help="Keep only Is_latest = True rows")
    p.add_argument("--limit", type=int, default=12, help="Maximum records to print")
    p.add_argument("--format", choices=("markdown", "json"), default="markdown", help="Output format")
    p.add_argument("--cli", default=os.environ.get("LARK_CLI_BIN", "lark-cli"), help="lark-cli executable")
    p.add_argument("--identity", default=os.environ.get("FEISHU_PHASE2_IDENTITY", "bot"),
                   help="lark-cli identity for record reads (default bot)")
    p.add_argument("--wiki-token", default=os.environ.get("FEISHU_PUBLISHED_DOCS_WIKI_TOKEN", DEFAULT_WIKI_TOKEN))
    p.add_argument("--table-id", default=os.environ.get("FEISHU_PUBLISHED_DOCS_TABLE_ID", DEFAULT_TABLE_ID))
    p.add_argument("--view-id", default=os.environ.get("FEISHU_PUBLISHED_DOCS_VIEW_ID", DEFAULT_VIEW_ID))
    p.add_argument("--base-token", default=os.environ.get("FEISHU_PUBLISHED_DOCS_BASE_TOKEN") or None,
                   help="Optional base token override; skips wiki-node resolution")
    return p.parse_args(argv)


def run_lark_json(cmd: list[str]) -> dict:
    completed = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or f"lark-cli failed: {' '.join(cmd)}")
    payload = json.loads(completed.stdout)
    if not payload.get("ok", True) and int(payload.get("code", 0) or 0) != 0:
        raise RuntimeError(json.dumps(payload, ensure_ascii=False))
    return payload


def resolve_base_token(*, cli: str, wiki_token: str, identity: str) -> str:
    payload = run_lark_json([
        cli, "api", "GET", "/open-apis/wiki/v2/spaces/get_node",
        "--params", json.dumps({"token": wiki_token, "obj_type": "wiki"}, ensure_ascii=False),
        "--as", identity,
    ])
    return str(payload["data"]["node"]["obj_token"])


def fetch_records(*, cli: str, base_token: str, table_id: str, view_id: str, identity: str, max_records: int) -> list[dict]:
    items: list[dict] = []
    page_token: str | None = None
    while len(items) < max_records:
        data = {"view_id": view_id, "page_size": DEFAULT_PAGE_SIZE}
        if page_token:
            data["page_token"] = page_token
        payload = run_lark_json([
            cli, "api", "POST",
            f"/open-apis/bitable/v1/apps/{base_token}/tables/{table_id}/records/search",
            "--data", json.dumps(data, ensure_ascii=False), "--as", identity,
        ])
        d = payload.get("data", {})
        items.extend(d.get("items", []) or [])
        if d.get("has_more") and d.get("page_token"):
            page_token = d["page_token"]
        else:
            break
    return items


def flatten(value) -> str:
    """Reduce any Feishu field value to a flat display string."""
    if value is None:
        return ""
    if isinstance(value, list):
        return " / ".join(flatten(v) for v in value if flatten(v))
    if isinstance(value, dict):
        return str(value.get("text") or value.get("link") or value.get("name") or "")
    return str(value)


def link_of(fields: dict) -> tuple[str, str]:
    """Return (anchor_text, url) for the manual link, falling back gracefully."""
    raw = fields.get("说明书链接")
    url = ""
    if isinstance(raw, dict):
        url = str(raw.get("link") or "")
    elif isinstance(raw, list) and raw and isinstance(raw[0], dict):
        url = str(raw[0].get("link") or "")
    anchor = flatten(fields.get("说明书名称")) or flatten(fields.get("文档名称")) or flatten(fields.get("产品型号")) or "说明书"
    return anchor, url


def matches(fields: dict, query: str) -> bool:
    q = query.strip().lower()
    if not q:
        return True
    for fld in SEARCH_FIELDS:
        if q in flatten(fields.get(fld)).lower():
            return True
    return False


def passes_filters(fields: dict, args: argparse.Namespace) -> bool:
    if args.latest_only and flatten(fields.get("Is_latest")).lower() not in ("true", "1"):
        return False
    for fld, needle in (("区域", args.region), ("文档类型", args.doc_type),
                        ("产品阶段", args.stage), ("分类", args.category)):
        if needle and needle.strip() not in flatten(fields.get(fld)):
            return False
    return True


def fmt_date(fields: dict) -> str:
    raw = fields.get("归档日期")
    try:
        ms = int(raw)
    except (TypeError, ValueError):
        return ""
    # Pure offset arithmetic; avoids timezone/locale surprises in chat output.
    import datetime
    return datetime.datetime.utcfromtimestamp(ms / 1000).strftime("%Y-%m-%d")


def render_record_markdown(fields: dict) -> str:
    anchor, url = link_of(fields)
    head = f"- **{flatten(fields.get('产品型号')) or anchor}** — "
    head += f"[{anchor}]({url})" if url else f"{anchor}（无链接）"
    detail_bits = []
    for fld in DETAIL_FIELDS:
        val = fmt_date(fields) if fld == "归档日期" else flatten(fields.get(fld))
        if val:
            label = "归档" if fld == "归档日期" else fld
            detail_bits.append(f"{label}: {val}")
    suffix = "\n  " + " · ".join(detail_bits) if detail_bits else ""
    return head + suffix


def render_overview(records: list[dict]) -> str:
    def col(fld: str) -> Counter:
        return Counter(flatten(r["fields"].get(fld)) or "（空）" for r in records)

    latest = sum(1 for r in records if flatten(r["fields"].get("Is_latest")).lower() in ("true", "1"))
    lines = [f"# 发布文档管理 · 总览", "", f"共 **{len(records)}** 条记录，其中最新版 **{latest}** 条。", ""]
    for title, fld in (("按分类", "分类"), ("按区域", "区域"), ("按产品阶段", "产品阶段"),
                       ("按文档类型", "文档类型"), ("按源语言", "源语言")):
        items = ", ".join(f"{k} {v}" for k, v in col(fld).most_common())
        lines.append(f"- **{title}**：{items}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    base_token = args.base_token or resolve_base_token(
        cli=args.cli, wiki_token=args.wiki_token, identity=args.identity
    )
    records = fetch_records(
        cli=args.cli, base_token=base_token, table_id=args.table_id,
        view_id=args.view_id, identity=args.identity, max_records=DEFAULT_MAX_RECORDS,
    )

    if args.overview:
        # Overview reflects every visible row; per-record filters do not apply.
        print(render_overview(records))
        return 0

    selected = [
        r for r in records
        if passes_filters(r.get("fields", {}), args)
        and (args.list_all or args.query is None or matches(r.get("fields", {}), args.query))
    ]
    # Latest manuals first so the freshest version is the default answer.
    selected.sort(key=lambda r: flatten(r["fields"].get("Is_latest")).lower() not in ("true", "1"))
    selected = selected[: args.limit]

    if args.format == "json":
        out = []
        for r in selected:
            f = r.get("fields", {})
            anchor, url = link_of(f)
            out.append({
                "record_id": r.get("record_id"),
                "model": flatten(f.get("产品型号")),
                "manual_name": anchor,
                "manual_link": url,
                "region": flatten(f.get("区域")),
                "doc_type": flatten(f.get("文档类型")),
                "source_lang": flatten(f.get("源语言")),
                "version": flatten(f.get("版本")),
                "stage": flatten(f.get("产品阶段")),
                "category": flatten(f.get("分类")),
                "archived_at": fmt_date(f),
                "is_latest": flatten(f.get("Is_latest")),
            })
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    if not selected:
        scope = args.query or "（当前筛选条件）"
        print(f"未在「发布文档管理」中找到匹配 {scope} 的说明书。")
        return 0
    print("\n".join(render_record_markdown(r.get("fields", {})) for r in selected))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
