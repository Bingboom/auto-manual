"""Is the committed product-matrix snapshot still what the base holds? The sync check and its status file.

``check`` reads the base the way ``build_snapshot`` does, compares the content (``snapshot.content_digest``: the
schema and every list, not the times) with the committed ``snapshot.json``, and returns the status document that
``status.json`` beside it holds:

- ``current``: the base and the snapshot agree; ``last_success`` becomes this check's time.
- ``behind``: they differ (the base has changed since the snapshot was read, or the snapshot's schema is older);
  ``lag.reason`` says how. With ``refresh`` the check keeps the snapshot it just read instead (``refreshed``).
- ``failed``: the base could not be read; the previous ``last_success`` stays, the reason is the error type only
  (a CLI's error text can carry row data).

The status carries times, content hashes and counts only: never a project number, key, token or table id. The
portal (``tools/rtd/product_freshness.py``) reads it at build time, without access to the base. Contract:
``code-as-doc/dev/product_matrix_base.md`` §6.1.
"""
from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
from typing import Any

from tools.product_matrix_base import snapshot
from tools.product_matrix_base.stage import LoadError, Runner

STATUS_SCHEMA = "hello-docs-product-matrix-status/v1"
STATUS_FILE = "status.json"
KIND = "product_matrix"
RESUME = "python -m tools.product_matrix_base check --out docs/knowledge/product-matrix --write --refresh"
# A check that only confirms the snapshot again is committed when the committed confirmation is this old, so the
# portal's last successful sync stays inside the registry's stale_after_days without a commit per day.
CONFIRM_AFTER_DAYS = 3
FAILED_MESSAGE = "读取飞书产品矩阵失败，页面沿用上次的快照；重跑检查即可，无需改动飞书。"


def stamp(moment: dt.datetime) -> str:
    return moment.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_time(value: Any) -> dt.datetime | None:
    """An ISO time from a snapshot or status (``...Z`` or with an offset; a bare date is UTC midnight)."""
    text = str(value or "").strip()
    if not text:
        return None
    try:
        moment = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return moment if moment.tzinfo else moment.replace(tzinfo=dt.timezone.utc)


def execution_url() -> str:
    repo, run = os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_RUN_ID", "")
    return f"https://github.com/{repo}/actions/runs/{run}" if repo and run else "local"


def read_json(path: Path) -> dict[str, Any] | None:
    """A JSON object from ``path``; None when it is absent or unreadable."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def header(document: dict[str, Any] | None) -> dict[str, Any] | None:
    """What the status records of a snapshot: its schema, times and content hash."""
    if document is None:
        return None
    return {"schema": document.get("schema"), "read_at": document.get("read_at"),
            "built_at": document.get("built_at"), "source_modified_at": document.get("source_modified_at"),
            "content_sha256": snapshot.content_digest(document)}


def _counts(committed: dict[str, Any], candidate: dict[str, Any]) -> str:
    old, new = committed.get("counts") or {}, candidate.get("counts") or {}
    names = {"products": "产品", "values": "主产品值", "component_values": "组件值", "sources": "来源", "cells": "单元格",
             "parameters": "参数"}
    moved = [f"{label} {old.get(key)}→{new.get(key)}" for key, label in names.items() if old.get(key) != new.get(key)]
    return "，".join(moved)


def lag(committed: dict[str, Any] | None, candidate: dict[str, Any]) -> str:
    """Why the committed snapshot is behind the base just read, or "" when it is not."""
    if committed is None:
        return "还没有可读的已提交快照"
    if committed.get("schema") != candidate.get("schema"):
        return f"快照结构 {committed.get('schema')} 早于当前的 {candidate.get('schema')}"
    if snapshot.content_digest(committed) == snapshot.content_digest(candidate):
        return ""
    newer = parse_time(candidate.get("source_modified_at"))
    known = parse_time(committed.get("source_modified_at"))
    reason = "飞书产品矩阵的内容与已提交快照不同"
    if newer and (known is None or newer > known):
        reason = f"飞书有更晚的事实记录（{stamp(newer)}），内容与已提交快照不同"
    moved = _counts(committed, candidate)
    return f"{reason}（{moved}）" if moved else reason


def check(run: Runner, committed: dict[str, Any] | None, previous: dict[str, Any] | None, *, now: dt.datetime,
          refresh: bool = False, execution: str = "local") -> tuple[dict[str, Any], dict[str, Any] | None]:
    """The status of this check, and the snapshot to write (only when ``refresh`` and the base moved on)."""
    status: dict[str, Any] = {
        "schema": STATUS_SCHEMA, "kind": KIND, "checked_at": stamp(now), "execution": execution, "resume": RESUME,
        "status": "failed", "stage": "source-read", "last_success": (previous or {}).get("last_success") or None,
        "snapshot": header(committed), "source": None,
        "lag": {"behind": None, "reason": "本次未能读取飞书，无法判断快照是否落后"}}
    try:
        candidate = snapshot.build_snapshot(run, now=now)
    except (LoadError, OSError, ValueError, KeyError, TypeError) as exc:
        status.update(error_type=type(exc).__name__, message=FAILED_MESSAGE)
        return status, None
    status["stage"] = "compared"
    status["source"] = {"source_modified_at": candidate.get("source_modified_at"),
                        "content_sha256": snapshot.content_digest(candidate)}
    reason = lag(committed, candidate)
    if not reason:
        status.update(status="current", last_success=stamp(now), lag={"behind": False, "reason": "快照与飞书一致"})
        return status, None
    if refresh:
        status.update(status="refreshed", stage="snapshot-built", last_success=stamp(now), snapshot=header(candidate),
                      lag={"behind": False, "reason": f"已按飞书重读快照：{reason}"})
        return status, candidate
    status.update(status="behind", lag={"behind": True, "reason": reason})
    return status, None


def verdict(status: dict[str, Any]) -> str:
    """refreshed reads as current: after a refresh the snapshot and the base agree."""
    value = str(status.get("status") or "")
    return "current" if value == "refreshed" else value


def worth_committing(status: dict[str, Any], committed: dict[str, Any] | None) -> bool:
    """Whether ``status`` should replace the committed status: a new verdict, new content, or an old confirmation.

    A repeated failure, or a repeated confirmation of the same content, stays in the run's logs (no
    timestamp-only commits) until the committed confirmation is ``CONFIRM_AFTER_DAYS`` old.
    """
    if committed is None:
        return True
    def same(key: str) -> bool:
        return (status.get(key) or {}).get("content_sha256") == (committed.get(key) or {}).get("content_sha256")
    if verdict(status) != verdict(committed) or status.get("error_type") != committed.get("error_type"):
        return True
    if not (same("snapshot") and same("source")):
        return True
    if status.get("status") == "failed":
        return False
    new, old = parse_time(status.get("last_success")), parse_time(committed.get("last_success"))
    return new is not None and (old is None or (new - old).days >= CONFIRM_AFTER_DAYS)


__all__ = ["CONFIRM_AFTER_DAYS", "KIND", "RESUME", "STATUS_FILE", "STATUS_SCHEMA", "check", "execution_url", "header",
           "lag", "parse_time", "read_json", "stamp", "verdict", "worth_committing"]
