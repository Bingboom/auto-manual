"""Market-policy records that ``market_policy`` events join by ID.

A policy event takes its status, summary, sources and boundary from a record in
``<knowledge_root>/market-policy/records.json`` instead of stating them itself.
This reader checks only the shape that join needs and is never stricter than the
portal's reader of the same file (``reviewed`` is free text there, for example).
A host that validates more passes its own records to ``events.load_events``.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

POLICY_DIR = "market-policy"
POLICY_FILE = "records.json"
_STATUSES = {"verified", "unverified", "demand"}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _record_problem(record: Any) -> str:
    if not isinstance(record, dict) or not _text(record.get("id")):
        return "a market-policy record needs an id"
    key = record["id"]
    if record.get("status") not in _STATUSES:
        return f"market-policy record {key} has an unknown status"
    if not _text(record.get("change")) or not _text(record.get("reviewed")):
        return f"market-policy record {key} needs a change and a reviewed note"
    if not isinstance(record.get("boundary", ""), str):
        return f"market-policy record {key} needs a text boundary"
    sources = record.get("sources")
    if not isinstance(sources, list) or not all(isinstance(source, dict) for source in sources):
        return f"market-policy record {key} needs a list of source objects"
    return ""


def read_policies(knowledge_root: Path | None) -> list[dict]:
    """The policy records under ``knowledge_root``; none there is an empty list, a malformed file raises ValueError."""
    path = knowledge_root / POLICY_DIR / POLICY_FILE if knowledge_root is not None else None
    if path is None or not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    records = data.get("records") if isinstance(data, dict) else None
    if not isinstance(records, list):
        raise ValueError(f"{POLICY_DIR}/{POLICY_FILE} needs a records list")
    for record in records:
        if problem := _record_problem(record):
            raise ValueError(problem)
    return records
