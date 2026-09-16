"""Tabular manual-traffic report over the Cloudflare Web Analytics GraphQL API.

Read-only: one authenticated query, grouped by page path, printed as Markdown
tables with the operations taxonomy (print/QR alias entries vs in-site manual
routes vs the portal home). Credentials come from the environment only:

  CLOUDFLARE_API_TOKEN   an "Account Analytics: Read" API token
  CLOUDFLARE_ACCOUNT_ID  the Cloudflare account id

The site tag defaults to the committed public beacon token in the portal
settings, so the report needs no extra configuration per run.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

_API = "https://api.cloudflare.com/client/v4/graphql"
_QUERY = """
query ($account: String!, $site: String!, $since: Time!, $until: Time!, $limit: Int!) {
  viewer {
    accounts(filter: {accountTag: $account}) {
      rumPageloadEventsAdaptiveGroups(
        filter: {AND: [{siteTag: $site}, {datetime_geq: $since}, {datetime_leq: $until}]}
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


def default_site_tag() -> str:
    settings = json.loads(
        Path(__file__).with_name("rtd_portal_assets").joinpath("settings.json").read_text(encoding="utf-8")
    )
    return str(settings.get("analytics_beacon_token") or "")


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
    parser.add_argument("--site-tag", default="", help="override the site tag (default: portal settings beacon token)")
    parser.add_argument("--json", action="store_true", help="print raw rows as JSON instead of Markdown")
    args = parser.parse_args(argv)

    token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
    site = args.site_tag or default_site_tag()
    missing = [name for name, value in (
        ("CLOUDFLARE_API_TOKEN", token), ("CLOUDFLARE_ACCOUNT_ID", account), ("site tag", site),
    ) if not value]
    if missing:
        print(f"missing: {', '.join(missing)} (token needs Account Analytics: Read)", file=sys.stderr)
        return 2

    until = datetime.now(timezone.utc).replace(microsecond=0)
    since = until - timedelta(days=args.days)
    payload = fetch(token=token, variables={
        "account": account, "site": site, "limit": 1000,
        "since": since.isoformat().replace("+00:00", "Z"),
        "until": until.isoformat().replace("+00:00", "Z"),
    })
    rows = rows_from_payload(payload)
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print(markdown_report(rows, since=since.date().isoformat(), until=until.date().isoformat(), top=args.top))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
