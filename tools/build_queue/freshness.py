from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


_RESULT_PART_RE = re.compile(r"\s*\|\s*")


@dataclass(frozen=True)
class QueueResultMetadata:
    status: str = ""
    version: str = ""
    workflow_action: str = ""
    built_at: datetime | None = None


@dataclass(frozen=True)
class QueueFreshness:
    build_started_at: datetime | None = None
    result_built_at: datetime | None = None
    result_is_fresh: bool | None = None
    freshness_status: str = "not_requested"


def parse_queue_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return _aware_utc(value)
    if isinstance(value, (int, float)):
        return _from_epoch_number(float(value))
    text = str(value or "").strip()
    if not text:
        return None
    if re.fullmatch(r"\d+(?:\.\d+)?", text):
        return _from_epoch_number(float(text))
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        return _aware_utc(datetime.fromisoformat(normalized))
    except ValueError:
        return None


def parse_result_metadata(result: str) -> QueueResultMetadata:
    text = str(result or "").strip()
    if not text:
        return QueueResultMetadata()
    parts = [part.strip() for part in _RESULT_PART_RE.split(text) if part.strip()]
    status = parts[0].lower() if parts else ""
    values: dict[str, str] = {}
    for part in parts[1:]:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        values[key.strip().lower()] = value.strip()
    return QueueResultMetadata(
        status=status,
        version=values.get("version", ""),
        workflow_action=values.get("workflow_action", ""),
        built_at=parse_queue_timestamp(values.get("built_at")),
    )


def compute_freshness(
    *,
    result: str,
    build_started_at: Any = None,
    fresh_since: Any = None,
) -> QueueFreshness:
    started_at = parse_queue_timestamp(build_started_at)
    result_meta = parse_result_metadata(result)
    since = parse_queue_timestamp(fresh_since)
    if since is None:
        return QueueFreshness(
            build_started_at=started_at,
            result_built_at=result_meta.built_at,
            result_is_fresh=None,
            freshness_status="not_requested",
        )
    if result_meta.built_at is not None:
        is_fresh = result_meta.built_at >= since
        if is_fresh:
            normalized_status = result_meta.status.lower()
            if normalized_status.startswith("success"):
                status = "fresh_success"
            elif normalized_status.startswith("failed") or normalized_status.startswith("failure"):
                status = "fresh_failure"
            else:
                status = "fresh_result"
        else:
            status = "stale_result"
        return QueueFreshness(
            build_started_at=started_at,
            result_built_at=result_meta.built_at,
            result_is_fresh=is_fresh,
            freshness_status=status,
        )
    if started_at is not None and started_at >= since:
        return QueueFreshness(
            build_started_at=started_at,
            result_built_at=None,
            result_is_fresh=None,
            freshness_status="writeback_pending",
        )
    return QueueFreshness(
        build_started_at=started_at,
        result_built_at=None,
        result_is_fresh=False if result else None,
        freshness_status="pending" if not result else "stale_result",
    )


def isoformat_timestamp(value: datetime | None) -> str:
    if value is None:
        return ""
    return _aware_utc(value).isoformat(timespec="seconds")


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _from_epoch_number(value: float) -> datetime | None:
    if value <= 0:
        return None
    seconds = value / 1000 if value > 10_000_000_000 else value
    try:
        return datetime.fromtimestamp(seconds, tz=timezone.utc)
    except (OSError, OverflowError, ValueError):
        return None
