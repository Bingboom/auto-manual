"""Reusable validation primitives for versioned Overview instances."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Callable, Mapping

from tools.component_specs.model import ComponentSpecError


def number_list(value: Any, *, length: int, field: str) -> list[float]:
    if (
        not isinstance(value, list)
        or len(value) != length
        or any(
            isinstance(item, bool) or not isinstance(item, (int, float))
            for item in value
        )
    ):
        raise ComponentSpecError(f"{field} must contain {length} numbers")
    return [float(item) for item in value]


def point_list(value: Any, *, field: str) -> list[list[float]]:
    if not isinstance(value, list) or len(value) < 2:
        raise ComponentSpecError(f"{field} must contain at least two points")
    return [
        number_list(point, length=2, field=f"{field}[{index}]")
        for index, point in enumerate(value)
    ]


def non_empty(value: Any, *, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ComponentSpecError(f"{field} must be a non-empty string")
    return text


def resolved_overview_instance_issues(
    payload: Mapping[str, Any],
    *,
    validator: Callable[[str, Any], dict[str, Any]],
) -> list[str]:
    """Validate one fully materialized target instance for frozen IR replay."""

    if not isinstance(payload, Mapping):
        return ["resolved overview instance must be a mapping"]
    instance_id = str(payload.get("instance_id") or "").strip()
    if not instance_id:
        return ["resolved overview instance requires instance_id"]
    if "extends" in payload:
        return ["resolved overview instance cannot retain extends"]
    try:
        validator(instance_id, payload)
    except ComponentSpecError as exc:
        return [str(exc)]
    return []


def overview_instance_sha256(instance: Mapping[str, Any]) -> str:
    """Return the canonical identity of one resolved Overview instance."""

    encoded = json.dumps(
        instance,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


__all__ = [
    "non_empty",
    "number_list",
    "overview_instance_sha256",
    "point_list",
    "resolved_overview_instance_issues",
]
