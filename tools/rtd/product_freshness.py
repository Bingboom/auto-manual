"""How fresh the 产品矩阵 pages' data is, judged at build time without access to the base.

The product pages (产品矩阵, 产品对比, 参数表, 产品档案) show three times and, when the data may be out of date, a
warning. They come from the snapshot's header (``read_at``; ``built_at`` and ``source_modified_at`` since schema
v1.2) and from ``status.json`` beside it, which the sync check (``tools/product_matrix_base/sync.py``) writes. The
status counts only while it describes the snapshot on disk (the same ``read_at``): a snapshot replaced without a
check is judged by its own read time.

The page warns when:

- the snapshot was last confirmed equal to the base (its read, or a later successful check) more than the
  registry's ``stale_after_days`` ago;
- the last check found the base ahead of the snapshot (``behind``), or the base's latest fact record time is newer
  than the snapshot's;
- the last check failed (the page keeps the last good data).

A check that has stopped running shows as the first warning: nothing confirms the snapshot any more.

Private role only, like the snapshot: ``tools/rtd/portal.py`` calls this for the product pages, which the
manuals-only (public) role never builds.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any
from urllib.parse import quote

from tools.product_matrix_base.publish import BRANCH as REFRESH_BRANCH
from tools.product_matrix_base.sync import STATUS_FILE, STATUS_SCHEMA, parse_time, read_json
from tools.rtd.product_library import SNAPSHOT

DEFAULT_LIMIT = 7  # used only when the source registry cannot be read
CST = dt.timezone(dt.timedelta(hours=8))
UNKNOWN_BUILD = "未记录（旧版快照）"
NO_SUCCESS = "无记录"
REFRESH_WORKFLOW_URL = "https://github.com/Bingboom/Hello-Docs/actions/workflows/workspace-data-refresh.yml"
REFRESH_PR_URL = f"https://github.com/Bingboom/Hello-Docs/pulls?q=is%3Apr+is%3Aopen+head%3A{quote(REFRESH_BRANCH, safe='')}"


def _shown(moment: dt.datetime | None) -> str:
    return moment.astimezone(CST).strftime("%Y-%m-%d %H:%M") if moment else ""


def _day(moment: dt.datetime) -> str:
    return moment.astimezone(CST).strftime("%Y-%m-%d")


def stale_limit(registry: dict[str, dict[str, Any]] | None) -> int:
    """The product_matrix domain's stale_after_days from the source registry."""
    try:
        return int((registry or {})["product_matrix"]["stale_after_days"])
    except (KeyError, TypeError, ValueError):
        return DEFAULT_LIMIT


def load_status(knowledge_dir: Path) -> dict[str, Any] | None:
    status = read_json(knowledge_dir / SNAPSHOT.parent / STATUS_FILE)
    return status if status and status.get("schema") == STATUS_SCHEMA else None


def _status_warnings(status: dict[str, Any], snapshot: dict[str, Any]) -> list[str]:
    checked = parse_time(status.get("checked_at"))
    when = _shown(checked) or "时间未记录"
    warnings = []
    if status.get("status") == "behind":
        reason = str((status.get("lag") or {}).get("reason") or "")
        warnings.append(f"飞书已有更新，页面数据落后（检查于 {when}）" + (f"：{reason}" if reason else ""))
    elif status.get("status") == "failed":
        warnings.append(f"最近一次同步检查失败（{when}），页面沿用上次成功的数据")
    newer = parse_time((status.get("source") or {}).get("source_modified_at"))
    known = parse_time(snapshot.get("source_modified_at"))
    if newer and known and newer > known and status.get("status") != "behind":
        warnings.append(f"飞书有更晚的事实记录（{_shown(newer)}），快照还没有包含")
    return warnings


def freshness(snapshot: dict[str, Any], status: dict[str, Any] | None, *, today: dt.date, limit: int) -> dict[str, Any]:
    """The pages' times and warnings for ``snapshot``; ``status`` is ignored unless it describes this snapshot."""
    read = parse_time(snapshot.get("read_at"))
    built = parse_time(snapshot.get("built_at"))
    applies = bool(status) and (status.get("snapshot") or {}).get("read_at") == snapshot.get("read_at")
    success = parse_time(status.get("last_success")) if applies and status else None
    confirmed = max((moment for moment in (read, success) if moment), default=None)
    warnings: list[str] = []
    if confirmed is None:
        warnings.append("读不到快照的读取时间，无法判断数据是否最新")
    elif (today - confirmed.astimezone(CST).date()).days > limit:
        warnings.append(f"已超过 {limit} 天没有确认与飞书一致（最近确认 {_day(confirmed)}）")
    if applies and status:
        warnings += _status_warnings(status, snapshot)
    return {"read_at": _shown(read) or "未记录", "built_at": _shown(built) or UNKNOWN_BUILD,
            "last_success": _shown(success) or NO_SUCCESS, "warnings": warnings, "stale": bool(warnings),
            "limit": limit, "refresh_url": REFRESH_WORKFLOW_URL, "review_pr_url": REFRESH_PR_URL}


def freshness_context(knowledge_dir: Path, snapshot: dict[str, Any] | None, *, today: dt.date,
                      registry: dict[str, dict[str, Any]] | None) -> dict[str, Any] | None:
    """The pages' freshness block, or None without a snapshot (the pages then show no figures at all)."""
    if snapshot is None:
        return None
    return freshness(snapshot, load_status(knowledge_dir), today=today, limit=stale_limit(registry))


__all__ = ["DEFAULT_LIMIT", "NO_SUCCESS", "REFRESH_PR_URL", "REFRESH_WORKFLOW_URL", "UNKNOWN_BUILD", "freshness",
           "freshness_context", "load_status", "stale_limit"]
