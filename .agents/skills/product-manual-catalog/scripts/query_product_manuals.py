#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Query the Feishu "发布文档管理" (published-manual catalog) Base for OpenClaw chat.

Self-contained: shells out to ``lark-cli`` only, no repo-internal imports, so it
runs unchanged from the source repo or the one-way Hello-Docs mirror checkout.

By default it queries the primary catalog table (``tbldqnNBxFQsxpeN`` /
``vewytqcvDc``). When the bot identity lacks permission on that table (Feishu
returns ``WrongTableId`` 1254004 or ``not_found`` 800030104), and no explicit
table override was supplied, it automatically falls back to the bot-accessible
published web-manual table ``网页文档`` (``tblY0i9JUElmuuKb``), and on empty
search results checks ``说明书转网页`` (``tbljbjaXaTD6V9PO``) for un-converted
print manuals.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from collections import Counter

DEFAULT_WIKI_TOKEN = "QKNGwHFwPiY7J7kZ0bzcximKnyb"
DEFAULT_TABLE_ID = "tbldqnNBxFQsxpeN"
DEFAULT_VIEW_ID = "vewytqcvDc"
WEB_DOCS_TABLE_ID = "tblY0i9JUElmuuKb"
SOURCE_DOCS_TABLE_ID = "tbljbjaXaTD6V9PO"
DEFAULT_PAGE_SIZE = 100
DEFAULT_MAX_RECORDS = 2000

_TABLE_ACCESS_ERROR_CODES = frozenset({"1254004", "800030104", "1254302", "99991672"})
_TABLE_ACCESS_ERROR_TEXT = ("wrongtableid", "not_found", "permission", "forbidden", "no access")

_MD_LINK_RE = re.compile(r"^\[([^\]]*)\]\((https?://[^)]+)\)$")
_URL_RE = re.compile(r"https?://[^\s)>\]]+")

_REGION_ALIAS_GROUPS: tuple[tuple[str, ...], ...] = (
    ("美加规", "US", "CA", "美规", "加规", "北美"),
    ("欧英规", "EU", "UK", "欧规", "英规", "欧洲"),
    ("日规", "JP", "日本"),
    ("国规", "CN", "中规", "中国"),
    ("台规", "TW", "台湾"),
    ("韩规", "KR", "韩国"),
)

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
    "客户型号",
    "规格型号",
    "适用产品",
)
# Fields shown in a per-manual result block, in display order.
DETAIL_FIELDS = (
    "产品型号",
    "项目",
    "业务号",
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
    env_table = os.environ.get("FEISHU_PUBLISHED_DOCS_TABLE_ID")
    env_view = os.environ.get("FEISHU_PUBLISHED_DOCS_VIEW_ID")
    p = argparse.ArgumentParser(
        description="Query the Feishu published-manual catalog table for OpenClaw chat."
    )
    p.add_argument("query", nargs="?", default=None, help="Free-text product/manual search (model, name, project…)")
    p.add_argument("--search", dest="search", default=None, help="Alias for the positional query")
    p.add_argument("--overview", action="store_true", help="Show catalog summary counts instead of records")
    p.add_argument("--list", dest="list_all", action="store_true", help="List every catalog row (subject to filters)")
    p.add_argument("--region", default=None, help="Filter by 区域/市场 substring or alias, e.g. 美加规 / US / 日规 / JP")
    p.add_argument("--doc-type", default=None, help="Filter by 文档类型 substring, e.g. User Manual / 产品说明书")
    p.add_argument("--stage", default=None, help="Filter by 产品阶段 substring, e.g. PVT / 未转")
    p.add_argument("--category", default=None, help="Filter by 分类 substring, e.g. 便携储能")
    p.add_argument("--latest-only", action="store_true", help="Keep only Is_latest = True rows")
    p.add_argument("--limit", type=int, default=12, help="Maximum records to print")
    p.add_argument("--format", choices=("markdown", "json"), default="markdown", help="Output format")
    p.add_argument("--cli", default=os.environ.get("LARK_CLI_BIN", "lark-cli"), help="lark-cli executable")
    p.add_argument("--identity", default=os.environ.get("FEISHU_PHASE2_IDENTITY", "bot"),
                   help="lark-cli identity for record reads (default bot)")
    p.add_argument("--wiki-token", default=os.environ.get("FEISHU_PUBLISHED_DOCS_WIKI_TOKEN", DEFAULT_WIKI_TOKEN))
    p.add_argument("--table-id", default=None,
                   help=f"Catalog table_id override (defaults to env or {DEFAULT_TABLE_ID})")
    p.add_argument("--view-id", default=None,
                   help=f"Catalog view_id override (defaults to env or {DEFAULT_VIEW_ID})")
    p.add_argument("--base-token", default=os.environ.get("FEISHU_PUBLISHED_DOCS_BASE_TOKEN") or None,
                   help="Optional base token override; skips wiki-node resolution")
    p.add_argument("--no-fallback", action="store_true",
                   help="Fail closed if the primary catalog table is inaccessible under the current identity")
    args = p.parse_args(argv)
    # `--search` and the positional `query` express the same intent but must not
    # share an argparse dest: an absent positional's None default would otherwise
    # clobber a value passed via --search. Resolve to whichever was provided.
    if args.query is None:
        args.query = args.search
    args.explicit_table_override = bool(args.table_id or env_table)
    args.table_id = args.table_id or env_table or DEFAULT_TABLE_ID
    if args.view_id is None:
        args.view_id = env_view if env_view is not None else (DEFAULT_VIEW_ID if args.table_id == DEFAULT_TABLE_ID else "")
    return args


def run_lark_json(cmd: list[str]) -> dict:
    completed = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=False)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or f"lark-cli failed: {' '.join(cmd)}"
        raise RuntimeError(detail)
    payload = json.loads(completed.stdout)
    if not payload.get("ok", True) and int(payload.get("code", 0) or 0) != 0:
        raise RuntimeError(json.dumps(payload, ensure_ascii=False))
    return payload


def is_table_access_error(exc: Exception) -> bool:
    """True when lark-cli failed because the target table is restricted or missing for this identity."""
    text = str(exc)
    lowered = text.lower()
    if any(code in text for code in _TABLE_ACCESS_ERROR_CODES):
        return True
    return any(token in lowered for token in _TABLE_ACCESS_ERROR_TEXT)


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
        data: dict[str, object] = {"page_size": DEFAULT_PAGE_SIZE}
        if view_id:
            data["view_id"] = view_id
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
    """Reduce any Feishu field value (including /records/search lookup wrappers) to a flat display string."""
    if value is None:
        return ""
    if isinstance(value, list):
        if value and all(isinstance(v, dict) and "text" in v and "link" not in v and "name" not in v for v in value):
            return "".join(str(v.get("text") or "") for v in value).strip()
        parts = [flatten(v) for v in value]
        return " / ".join(p for p in parts if p)
    if isinstance(value, dict):
        if "value" in value:
            return flatten(value.get("value"))
        if "link_record_ids" in value and not any(k in value for k in ("text", "link", "name")):
            return ""
        return str(value.get("text") or value.get("link") or value.get("name") or "").strip()
    return str(value).strip()


def _extract_url(raw: object) -> tuple[str, str]:
    """Extract (label, url) from Feishu link dicts, lists, or Markdown link strings."""
    if isinstance(raw, dict):
        return str(raw.get("text") or "").strip(), str(raw.get("link") or "").strip()
    if isinstance(raw, list) and raw:
        for item in raw:
            label, url = _extract_url(item)
            if url:
                return label, url
        return "", ""
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return "", ""
        md_match = _MD_LINK_RE.match(text)
        if md_match:
            return md_match.group(1).strip(), md_match.group(2).strip()
        url_match = _URL_RE.search(text)
        if url_match:
            return "", url_match.group(0).strip()
    return "", ""


def normalize_web_record(record: dict) -> dict:
    """Map a bot-accessible 网页文档 (tblY0i9JUElmuuKb) record into the catalog schema."""
    fields = record.get("fields", {})
    model = flatten(fields.get("型号"))
    short_name = flatten(fields.get("商品简称"))
    region = flatten(fields.get("市场"))
    lang = flatten(fields.get("语言"))
    category_parts = [part for part in (flatten(fields.get("产品类别")), flatten(fields.get("产品系列"))) if part]
    category = " / ".join(category_parts)
    notes = flatten(fields.get("备注"))
    is_latest = "False" if "停用" in notes else "True"

    link_label, url = _extract_url(fields.get("超链接"))
    scope_bits = [bit for bit in (region, lang) if bit]
    scope = " · ".join(scope_bits)
    title_base = " ".join(part for part in (model, short_name) if part) or link_label or "网页说明书"
    anchor = f"{title_base} ({scope})" if scope else title_base
    if link_label and not link_label.startswith("http"):
        anchor = link_label

    normalized = {
        "产品型号": model,
        "产品简称": short_name,
        "项目": flatten(fields.get("项目号")),
        "客户型号": flatten(fields.get("客户型号(关联)")),
        "规格型号": flatten(fields.get("规格型号")),
        "适用产品": flatten(fields.get("适用产品")),
        "区域": region,
        "文档类型": flatten(fields.get("文档类型")) or "产品说明书",
        "源语言": lang,
        "分类": category,
        "容量档": flatten(fields.get("容量档")),
        "说明书名称": anchor,
        "说明书链接": {"text": anchor, "link": url} if url else "",
        "Is_latest": is_latest,
        "_source_table": "网页文档",
    }
    if notes:
        normalized["备注"] = notes
    return {"record_id": record.get("record_id"), "fields": normalized}


def normalize_source_record(record: dict) -> dict:
    """Map a 说明书转网页 (tbljbjaXaTD6V9PO) record for print/unconverted manual fallback."""
    fields = record.get("fields", {})
    model = flatten(fields.get("客户型号")) or flatten(fields.get("项目号"))
    single_lang = flatten(fields.get("单语言"))
    spec_desc = flatten(fields.get("成品规格型号")) or flatten(fields.get("子项规格型号"))
    title = single_lang or spec_desc or model or "印刷源文件"
    converted = flatten(fields.get("已转网页版(自动)")) or "未转"
    normalized = {
        "产品型号": model,
        "项目": flatten(fields.get("项目号")),
        "业务号": flatten(fields.get("子物料编码")),
        "区域": flatten(fields.get("区域")),
        "文档类型": "印刷源文件（说明书转网页）",
        "产品阶段": converted,
        "规格型号": spec_desc,
        "说明书名称": title,
        "说明书链接": "",
        "Is_latest": "False" if converted == "未转" else "True",
        "_source_table": "说明书转网页",
    }
    return {"record_id": record.get("record_id"), "fields": normalized}


def link_of(fields: dict) -> tuple[str, str]:
    """Return (anchor_text, url) for the manual link, falling back gracefully."""
    label, url = _extract_url(fields.get("说明书链接"))
    anchor = (
        flatten(fields.get("说明书名称"))
        or flatten(fields.get("文档名称"))
        or (label if label and not label.startswith("http") else "")
        or flatten(fields.get("产品型号"))
        or "说明书"
    )
    return anchor, url


def matches(fields: dict, query: str) -> bool:
    q = query.strip().lower()
    if not q:
        return True
    for fld in SEARCH_FIELDS:
        if q in flatten(fields.get(fld)).lower():
            return True
    return False


def _region_matches(field_value: str, needle: str) -> bool:
    target = needle.strip()
    if not target:
        return True
    if target.lower() in field_value.lower():
        return True
    target_lower = target.lower()
    field_lower = field_value.lower()
    for group in _REGION_ALIAS_GROUPS:
        group_lower = tuple(item.lower() for item in group)
        if any(target_lower == alias or target_lower in alias for alias in group_lower):
            if any(alias in field_lower for alias in group_lower):
                return True
    return False


def passes_filters(fields: dict, args: argparse.Namespace) -> bool:
    if args.latest_only and flatten(fields.get("Is_latest")).lower() not in ("true", "1"):
        return False
    if args.region and not _region_matches(flatten(fields.get("区域")), args.region):
        return False
    for fld, needle in (("文档类型", args.doc_type), ("产品阶段", args.stage), ("分类", args.category)):
        if needle and needle.strip().lower() not in flatten(fields.get(fld)).lower():
            return False
    return True


def fmt_date(fields: dict) -> str:
    raw = fields.get("归档日期")
    try:
        ms = int(raw)
    except (TypeError, ValueError):
        return ""
    # Pure offset arithmetic; avoids timezone/locale surprises in chat output.
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
    if src_tbl := flatten(fields.get("_source_table")):
        detail_bits.append(f"来源表: {src_tbl}")
    suffix = "\n  " + " · ".join(detail_bits) if detail_bits else ""
    return head + suffix


def render_overview(records: list[dict], *, source_note: str = "") -> str:
    def col(fld: str) -> Counter:
        return Counter(flatten(r["fields"].get(fld)) or "（空）" for r in records)

    latest = sum(1 for r in records if flatten(r["fields"].get("Is_latest")).lower() in ("true", "1"))
    lines = ["# 发布文档管理 · 总览", ""]
    if source_note:
        lines.extend([f"> {source_note}", ""])
    lines.extend([f"共 **{len(records)}** 条记录，其中最新版 **{latest}** 条。", ""])
    for title, fld in (("按分类", "分类"), ("按区域", "区域"), ("按产品阶段", "产品阶段"),
                       ("按文档类型", "文档类型"), ("按源语言", "源语言")):
        counts = col(fld)
        if len(counts) == 1 and "（空）" in counts:
            continue
        items = ", ".join(f"{k} {v}" for k, v in counts.most_common())
        lines.append(f"- **{title}**：{items}")
    return "\n".join(lines)


def load_catalog_records(
    *,
    cli: str,
    base_token: str,
    table_id: str,
    view_id: str,
    identity: str,
    explicit_table_override: bool,
    no_fallback: bool,
    include_source_fallback: bool = False,
) -> tuple[list[dict], str, str]:
    """Fetch catalog records, falling back to bot-accessible tables if tbldqnNBxFQsxpeN is restricted.

    Returns (records, active_table_id, fallback_note).
    """
    try:
        records = fetch_records(
            cli=cli, base_token=base_token, table_id=table_id,
            view_id=view_id, identity=identity, max_records=DEFAULT_MAX_RECORDS,
        )
        if table_id == WEB_DOCS_TABLE_ID:
            return [normalize_web_record(r) for r in records], table_id, ""
        if table_id == SOURCE_DOCS_TABLE_ID:
            return [normalize_source_record(r) for r in records], table_id, ""
        return records, table_id, ""
    except RuntimeError as exc:
        can_fallback = (
            not no_fallback
            and not explicit_table_override
            and table_id == DEFAULT_TABLE_ID
            and is_table_access_error(exc)
        )
        if not can_fallback:
            raise
        web_raw = fetch_records(
            cli=cli, base_token=base_token, table_id=WEB_DOCS_TABLE_ID,
            view_id="", identity=identity, max_records=DEFAULT_MAX_RECORDS,
        )
        note = (
            f"默认总表 {DEFAULT_TABLE_ID} 对当前身份（{identity}）无访问权限，"
            f"已自动切换至 bot 可访问的「网页文档」（{WEB_DOCS_TABLE_ID}）。"
        )
        normalized = [normalize_web_record(r) for r in web_raw]
        if include_source_fallback:
            return normalized, WEB_DOCS_TABLE_ID, note
        return normalized, WEB_DOCS_TABLE_ID, note


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    base_token = args.base_token or resolve_base_token(
        cli=args.cli, wiki_token=args.wiki_token, identity=args.identity
    )
    records, active_table_id, fallback_note = load_catalog_records(
        cli=args.cli,
        base_token=base_token,
        table_id=args.table_id,
        view_id=args.view_id,
        identity=args.identity,
        explicit_table_override=args.explicit_table_override,
        no_fallback=args.no_fallback,
    )

    if args.overview:
        # Overview reflects every visible row; per-record filters do not apply.
        print(render_overview(records, source_note=fallback_note))
        return 0

    def filter_and_sort(rows: list[dict]) -> list[dict]:
        matched = [
            r for r in rows
            if passes_filters(r.get("fields", {}), args)
            and (args.list_all or args.query is None or matches(r.get("fields", {}), args.query))
        ]
        # Latest manuals first so the freshest version is the default answer.
        matched.sort(key=lambda r: flatten(r["fields"].get("Is_latest")).lower() not in ("true", "1"))
        return matched[: args.limit]

    selected = filter_and_sort(records)

    # Secondary fallback: if fallback is active on 网页文档 and a query returned 0 hits,
    # check 说明书转网页 (tbljbjaXaTD6V9PO) for printed / not-yet-converted manuals.
    if (
        not selected
        and args.query
        and active_table_id == WEB_DOCS_TABLE_ID
        and not args.no_fallback
        and not args.explicit_table_override
    ):
        source_raw = fetch_records(
            cli=args.cli, base_token=base_token, table_id=SOURCE_DOCS_TABLE_ID,
            view_id="", identity=args.identity, max_records=DEFAULT_MAX_RECORDS,
        )
        source_records = [normalize_source_record(r) for r in source_raw]
        selected = filter_and_sort(source_records)
        if selected:
            active_table_id = SOURCE_DOCS_TABLE_ID
            fallback_note = (
                f"「网页文档」（{WEB_DOCS_TABLE_ID}）无匹配记录，"
                f"已从「说明书转网页」（{SOURCE_DOCS_TABLE_ID}）返回印刷/待转网页条目。"
            )

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
                "source_table": flatten(f.get("_source_table")) or active_table_id,
            })
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    if not selected:
        scope = args.query or "（当前筛选条件）"
        print(f"未在「发布文档管理」中找到匹配 {scope} 的说明书。")
        return 0
    lines = []
    if fallback_note:
        lines.append(f"> {fallback_note}")
    lines.extend(render_record_markdown(r.get("fields", {})) for r in selected)
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
