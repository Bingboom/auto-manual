"""Local durable pending message for the hand-run intelligence loop.

The pending message is written before its intake candidate and any network call.
It retains the original content, day and idempotency key until an acknowledged
send. Runtime state lives outside the business checkout; it is never published.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from . import push
from .events import CONTENT_DIR, EVENTS_FILE, content_hash, validated_cases
from .files import write_json

STATE_ENV = "EXTERNAL_INTEL_STATE_DIR"
SCHEMA = "external-intel-pending-push/v1"


def state_path(knowledge: Path) -> Path:
    root = Path(os.environ.get(STATE_ENV, str(Path.home() / ".cache" / "auto-manual" / "external-intel")))
    checkout = hashlib.sha256(str(knowledge.resolve()).encode()).hexdigest()[:24]
    return root.expanduser() / checkout / "pending.json"


def destination(chat: str, cli: str, identity: str) -> str:
    """Bind a retry to its original transport without persisting configuration values."""
    return content_hash({"chat": chat, "cli": cli, "identity": identity})


def _byte_hash(value: bytes | None) -> str | None:
    return hashlib.sha256(value).hexdigest() if value is not None else None


def message(*, content: dict, today: str, snapshot: str, chat: str, cli: str, identity: str,
            intake: bytes | None = None, before: bytes | None = None) -> dict:
    return {"schema_version": SCHEMA, "content": content, "today": today,
            "events_snapshot_id": snapshot, "idempotency_key": push.idempotency_key(chat, content, today),
            "destination_sha256": destination(chat, cli, identity),
            "intake": intake.decode("utf-8") if intake is not None else None,
            "before_sha256": _byte_hash(before)}


def load(knowledge: Path) -> dict | None:
    path = state_path(knowledge)
    if not path.exists():
        return None
    try:
        job = json.loads(path.read_bytes())
        if not isinstance(job, dict) or job.get("schema_version") != SCHEMA:
            raise ValueError("unknown pending push format")
        for field in ("today", "events_snapshot_id", "idempotency_key", "destination_sha256"):
            if not isinstance(job[field], str) or not job[field]:
                raise ValueError("missing pending push metadata")
        push.preview(job["content"])
        if job["intake"] is not None:
            validated_cases(json.loads(job["intake"]))
        if job["before_sha256"] is not None and not isinstance(job["before_sha256"], str):
            raise ValueError("invalid pending intake identity")
    except (ValueError, KeyError, TypeError) as exc:
        raise ValueError("pending push is invalid; preserve it and inspect the runtime state") from exc
    return job


def save(knowledge: Path, job: dict) -> None:
    path = state_path(knowledge)
    if path.exists():
        raise ValueError("a pending push must be delivered before another is prepared")
    write_json(path, job)


def apply_intake(knowledge: Path, job: dict, write) -> bool:
    """Recover the candidate before sending, without overwriting a later operator edit."""
    if job["intake"] is None:
        return False
    path = knowledge / CONTENT_DIR / EVENTS_FILE
    current = path.read_bytes() if path.exists() else None
    payload = job["intake"].encode("utf-8")
    if _byte_hash(current) == _byte_hash(payload):
        return False
    if _byte_hash(current) != job["before_sha256"]:
        raise ValueError("events.json differs from both the pending candidate and its parent")
    write(path, payload)
    return True


def acknowledge(knowledge: Path, job: dict) -> None:
    if load(knowledge) != job:
        raise ValueError("pending push changed during delivery; preserve it")
    state_path(knowledge).unlink()
