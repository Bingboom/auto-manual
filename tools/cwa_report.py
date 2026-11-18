"""Tabular manual-traffic report over the Cloudflare Web Analytics GraphQL API.

Read-only: one authenticated query, grouped by page path, printed as Markdown
tables with the operations taxonomy (print/QR alias entries vs in-site manual
routes vs the portal home). Credentials come from the environment only:

  CLOUDFLARE_API_TOKEN   an "Account Analytics: Read" API token
  CLOUDFLARE_ACCOUNT_ID  the Cloudflare account id

The site tag is the Web Analytics site's own identifier (visible as the
``siteTag`` parameter in the dashboard URL — it is NOT the page beacon token);
pass it with ``--site-tag`` or ``CLOUDFLARE_SITE_TAG``.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

_API = "https://api.cloudflare.com/client/v4/graphql"
_QUERY = """
query ($account: String!, $site: String!, $since: Time!, $until: Time!, $limit: Int!) {
  viewer {
    accounts(filter: {accountTag: $account}) {
      rumPageloadEventsAdaptiveGroups(
        filter: {AND: [{siteTag: $site}, {datetime_geq: $since}, {datetime_lt: $until}]}
        limit: $limit
        orderBy: [count_DESC]
      ) {
        count
        sum { visits }
        dimensions { requestPath }
      }
    }
  }
}
"""


def classify(path: str) -> str:
    """Map one request path onto the operations taxonomy."""
    trimmed = path.strip()
    if not trimmed.startswith("/"):
        trimmed = f"/{trimmed}"
    if trimmed in ("/", "/index.html"):
        return "门户首页"
    if trimmed in ("/search.html",) or trimmed.startswith("/_"):
        return "站内功能页"
    if "/" not in trimmed[1:]:
        return "扫码/印刷入口（根别名）"
    return "站内手册页"


# The adaptive dataset silently degrades (partial rows, no error) past roughly
# a one-week query span, so longer windows are fetched as half-open chunks and
# aggregated client-side. Verified live on 2026-09-16: 30-day single query
# returned 1 row / 10 views while 1..7-day queries returned 7 rows / 63 views.
_MAX_CHUNK_DAYS = 7


def window_chunks(since: "datetime", until: "datetime") -> list[tuple["datetime", "datetime"]]:
    """Split [since, until) into half-open chunks the API answers faithfully."""
    chunks = []
    cursor = since
    while cursor < until:
        upper = min(cursor + timedelta(days=_MAX_CHUNK_DAYS), until)
        chunks.append((cursor, upper))
        cursor = upper
    return chunks


def merge_rows(chunks_rows: list[list[dict]]) -> list[dict]:
    """Aggregate per-chunk rows by path, ordered by pageviews descending."""
    merged: dict[str, dict] = {}
    for rows in chunks_rows:
        for row in rows:
            slot = merged.get(row["path"])
            if slot is None:
                merged[row["path"]] = dict(row)
            else:
                slot["pageviews"] += row["pageviews"]
                slot["visits"] += row["visits"]
    return sorted(merged.values(), key=lambda r: -r["pageviews"])


def rows_from_payload(payload: dict) -> list[dict]:
    """Flatten the GraphQL payload into {path, category, pageviews, visits} rows."""
    errors = payload.get("errors")
    if errors:
        raise RuntimeError(f"Cloudflare GraphQL errors: {json.dumps(errors, ensure_ascii=False)}")
    accounts = (payload.get("data") or {}).get("viewer", {}).get("accounts") or []
    if not accounts:
        raise RuntimeError("Cloudflare GraphQL returned no account; check the account id and token scope")
    rows = []
    for group in accounts[0].get("rumPageloadEventsAdaptiveGroups") or []:
        path = group["dimensions"]["requestPath"]
        rows.append({
            "path": path,
            "category": classify(path),
            "pageviews": int(group["count"]),
            "visits": int((group.get("sum") or {}).get("visits") or 0),
        })
    return rows


def markdown_report(rows: list[dict], *, since: str, until: str, top: int) -> str:
    """Two tables: taxonomy totals, then the top paths."""
    lines = [f"# 手册访问报表（{since} → {until}，UTC）", ""]
    if not rows:
        lines.append("（区间内没有任何浏览记录）")
        return "\n".join(lines)
    totals: dict[str, dict[str, int]] = {}
    for row in rows:
        bucket = totals.setdefault(row["category"], {"pageviews": 0, "visits": 0})
        bucket["pageviews"] += row["pageviews"]
        bucket["visits"] += row["visits"]
    lines += ["## 按入口分类", "", "| 分类 | 浏览量 | 访问数 |", "| --- | ---: | ---: |"]
    for category, bucket in sorted(totals.items(), key=lambda kv: -kv[1]["pageviews"]):
        lines.append(f"| {category} | {bucket['pageviews']} | {bucket['visits']} |")
    lines.append(f"| 合计 | {sum(r['pageviews'] for r in rows)} | {sum(r['visits'] for r in rows)} |")
    lines += ["", f"## Top {top} 页面", "", "| 页面 | 分类 | 浏览量 | 访问数 |", "| --- | --- | ---: | ---: |"]
    for row in rows[:top]:
        lines.append(f"| `{row['path']}` | {row['category']} | {row['pageviews']} | {row['visits']} |")
    return "\n".join(lines)


def fetch_payload(*, token: str, variables: dict) -> dict:
    request = urllib.request.Request(
        _API,
        data=json.dumps({"query": _QUERY, "variables": variables}).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main(argv: list[str] | None = None, *, fetch=fetch_payload) -> int:
    parser = argparse.ArgumentParser(description="Manual-traffic tables from Cloudflare Web Analytics")
    parser.add_argument("--days", type=int, default=7, help="report window ending now (default 7)")
    parser.add_argument("--top", type=int, default=20, help="rows in the per-page table (default 20)")
    parser.add_argument("--site-tag", default="", help="Web Analytics site tag (or CLOUDFLARE_SITE_TAG)")
    parser.add_argument("--json", action="store_true", help="print raw rows as JSON instead of Markdown")
    args = parser.parse_args(argv)

    token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
    site = args.site_tag or os.environ.get("CLOUDFLARE_SITE_TAG", "")
    missing = [name for name, value in (
        ("CLOUDFLARE_API_TOKEN", token), ("CLOUDFLARE_ACCOUNT_ID", account), ("CLOUDFLARE_SITE_TAG", site),
    ) if not value]
    if missing:
        print(f"missing: {', '.join(missing)} (token needs Account Analytics: Read)", file=sys.stderr)
        return 2

    until = datetime.now(timezone.utc).replace(microsecond=0)
    since = until - timedelta(days=args.days)
    chunks_rows = []
    for lower, upper in window_chunks(since, until):
        payload = fetch(token=token, variables={
            "account": account, "site": site, "limit": 1000,
            "since": lower.isoformat().replace("+00:00", "Z"),
            "until": upper.isoformat().replace("+00:00", "Z"),
        })
        chunks_rows.append(rows_from_payload(payload))
    rows = merge_rows(chunks_rows)
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print(markdown_report(rows, since=since.date().isoformat(), until=until.date().isoformat(), top=args.top))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
