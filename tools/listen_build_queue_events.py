from __future__ import annotations

import json
from typing import Any, Callable


def event_field_value_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip()
    if not text:
        return False
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = text
    if isinstance(parsed, bool):
        return parsed
    if isinstance(parsed, (int, float)):
        return bool(parsed)
    return str(parsed).strip().lower() in {"1", "true", "y", "yes", "checked"}


def event_requests_immediate_build(
    payload: dict[str, Any],
    *,
    event_type: str,
    file_type: str,
    base_token: str,
    table_id: str,
    immediate_field_id: str,
    event_field_value_truthy: Callable[[Any], bool] = event_field_value_truthy,
) -> bool:
    header = payload.get("header")
    event = payload.get("event")
    if not isinstance(header, dict) or not isinstance(event, dict):
        return False
    if str(header.get("event_type") or "").strip() != event_type:
        return False
    if str(event.get("file_token") or "").strip() != base_token:
        return False
    if str(event.get("file_type") or "").strip() != file_type:
        return False
    if str(event.get("table_id") or "").strip() != table_id:
        return False

    action_list = event.get("action_list", [])
    if not isinstance(action_list, list):
        return False
    for action in action_list:
        if not isinstance(action, dict):
            continue
        action_name = str(action.get("action") or "").strip()
        if action_name not in {"record_added", "record_edited"}:
            continue
        after_value = action.get("after_value", [])
        if not isinstance(after_value, list):
            continue
        for field_change in after_value:
            if not isinstance(field_change, dict):
                continue
            if str(field_change.get("field_id") or "").strip() != immediate_field_id:
                continue
            if event_field_value_truthy(field_change.get("field_value")):
                return True
    return False
