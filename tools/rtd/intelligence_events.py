"""External intelligence intake: collected first, complete without internal products.

Events live in the business knowledge snapshot at ``external-intel/events.json``,
beside the ``market-policy`` records they may join by ID. An event states what
happened, its sources and verification, the decision it asks for and who
decides; nothing here reads product data. ``product_lens`` is an optional
research rule that a separate step may evaluate against product knowledge.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlsplit

from tools.rtd.market_policy import market_context

SCHEMA_VERSION = "external-intel/v1"
INTAKE_SCHEMA = "external-intel-events/v1"
CONTENT_DIR = "external-intel"
EVENTS_FILE = "events.json"
_ID = re.compile(r"[a-z][a-z0-9-]*")
_STATUSES = {"verified", "unverified", "demand"}
_KINDS = {"policy", "market", "competitor"}
_CASE_KEYS = {"id", "title", "kind", "market", "occurred_on", "source_kind", "source_record_id",
              "product_lens", "revisions"}
_REVISION_KEYS = {"revision", "recorded_on", "reason", "decision_question", "decision_owner", "decide_by",
                  "hypotheses", "unknowns", "review"}
# Only an external event states its own facts; a policy event reads them from its record.
_EXTERNAL_KEYS = {"status", "summary", "boundary", "sources"}
_REVIEW_KEYS = {"status", "decision", "reviewed_by", "reviewed_on"}
_LENS_KEYS = {"catalog_markets", "market_mapping_note", "rule"}
RULE_KEYS = ("categories", "required_capabilities", "required_facts")


def content_hash(value: Any) -> str:
    """Hash canonical JSON, independent of formatting and object key order."""
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _text(value: Any, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"external event needs non-empty {label}")


def _texts(value: Any, label: str, *, required: bool = True) -> None:
    if not isinstance(value, list) or (required and not value):
        raise ValueError(f"external event needs a list of {label}")
    for item in value:
        _text(item, label)


def _date(value: Any, label: str) -> None:
    _text(value, label)
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"external event needs ISO {label}") from exc
    if parsed.isoformat() != value:
        raise ValueError(f"external event needs ISO {label}")


def _fields(record: Any, allowed: set[str], label: str) -> None:
    """Unknown fields fail: a revision must not be able to replace an event's identity or rule."""
    if not isinstance(record, dict):
        raise ValueError(f"external event {label} must be an object")
    if unknown := sorted(set(record) - allowed):
        raise ValueError(f"external event {label} has unknown fields: {', '.join(unknown)}")


def _sources(sources: Any) -> None:
    if not isinstance(sources, list):
        raise ValueError("external event sources must be a list")
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("external event sources must be objects")
        for key in ("kind", "title", "url", "note"):
            _text(source.get(key), f"source {key}")
        parts = urlsplit(source["url"])
        if parts.scheme != "https" or not parts.netloc or parts.username or parts.password:
            raise ValueError("external event source needs a public HTTPS URL")
        _date(source.get("checked_on"), "source checked_on")
        if source.get("published_on") is not None:
            _date(source["published_on"], "source published_on")


def _review(review: Any) -> None:
    _fields(review, _REVIEW_KEYS, "review")
    if review.get("status") not in {"pending", "reviewed"}:
        raise ValueError("external event review must be pending or reviewed")
    if review["status"] == "reviewed":
        _text(review.get("decision"), "human review decision")
        _text(review.get("reviewed_by"), "human reviewer")
        _date(review.get("reviewed_on"), "human review reviewed_on")
    elif any(review.get(field) is not None for field in ("decision", "reviewed_by", "reviewed_on")):
        raise ValueError("pending external event cannot carry human review details")


def _review_details(review: dict) -> dict:
    """Normalize pending metadata without manufacturing an operator or decision."""
    return {key: review.get(key) for key in ("decision", "reviewed_by", "reviewed_on")}


def _revision(revision: Any, expected: int, external: bool) -> None:
    _fields(revision, _REVISION_KEYS | (_EXTERNAL_KEYS if external else set()), f"revision {expected}")
    if type(revision.get("revision")) is not int or revision["revision"] != expected:
        raise ValueError("external event revisions must be consecutive, starting at 1")
    _date(revision.get("recorded_on"), "revision recorded_on")
    for key in ("reason", "decision_question"):
        _text(revision.get(key), key)
    if revision.get("decision_owner") is not None:
        _text(revision["decision_owner"], "decision_owner")
    if revision.get("decide_by") is not None:
        _date(revision["decide_by"], "decide_by")
    for key in ("hypotheses", "unknowns"):
        _texts(revision.get(key, []), key, required=False)
    _review(revision.get("review"))
    if external:
        for key in ("summary", "boundary"):
            _text(revision.get(key), key)
        if revision.get("status") not in _STATUSES:
            raise ValueError("unknown external event verification status")
        _sources(revision.get("sources"))
        if revision["status"] == "verified" and not any(s["kind"] == "official" for s in revision["sources"]):
            raise ValueError("verified external events need an official source")


def _lens(lens: Any) -> None:
    """An optional research rule over product knowledge; the event stands without it."""
    _fields(lens, _LENS_KEYS, "product_lens")
    _texts(lens.get("catalog_markets"), "product_lens catalog_markets")
    _text(lens.get("market_mapping_note"), "product_lens market_mapping_note")
    _fields(lens.get("rule"), set(RULE_KEYS), "product_lens rule")
    for field in RULE_KEYS:
        _texts(lens["rule"].get(field), f"product_lens {field}")


def _case(case: Any, ids: set[str]) -> None:
    _fields(case, _CASE_KEYS, "entry")
    key = case.get("id")
    if not isinstance(key, str) or not _ID.fullmatch(key) or key in ids:
        raise ValueError("external event ids must be unique lower-case ids")
    ids.add(key)
    for field in ("title", "market"):
        _text(case.get(field), field)
    if case.get("kind") not in _KINDS:
        raise ValueError("unknown external event kind")
    _date(case.get("occurred_on"), "occurred_on")
    source_kind = case.get("source_kind")
    if source_kind == "market_policy":
        _text(case.get("source_record_id"), "source_record_id")
    elif source_kind == "external_event":
        if "source_record_id" in case:
            raise ValueError("only market_policy events join a policy record")
    else:
        raise ValueError("unknown external event intake source")
    if "product_lens" in case:
        _lens(case["product_lens"])
    revisions = case.get("revisions")
    if not isinstance(revisions, list) or not revisions:
        raise ValueError("external event needs revisions")
    for expected, revision in enumerate(revisions, 1):
        _revision(revision, expected, source_kind == "external_event")


def validated_cases(data: Any) -> list[dict]:
    """The intake entries of a parsed events file; malformed intake raises ValueError."""
    if (not isinstance(data, dict) or data.get("schema_version") != INTAKE_SCHEMA
            or not isinstance(data.get("events"), list)):
        raise ValueError(f"external event intake needs {INTAKE_SCHEMA} with an events list")
    ids: set[str] = set()
    for case in data["events"]:
        _case(case, ids)
    return data["events"]


def _policy(record: dict | None) -> dict:
    if record is None:
        return {"status": "missing", "summary": "尚未加载关联的市场政策记录。",
                "sources": [], "boundary": "缺少业务政策快照，不能把录入记录当作已核实政策。",
                "checked_on": None, "policy_record_sha256": None}
    return {"status": record["status"], "summary": record["change"], "sources": [
        {**ref, "checked_on": record["reviewed"]} for ref in record["sources"]],
        "boundary": record.get("boundary", ""), "checked_on": record["reviewed"],
        "policy_record_sha256": content_hash(record)}


def _history(case: dict) -> list[dict]:
    """Intake revisions are historical authoring records, never invented evaluations."""
    rows = []
    for revision in case["revisions"]:
        rows.append({
            "event_id": case["id"], "revision": revision["revision"],
            "recorded_on": revision["recorded_on"], "reason": revision["reason"],
            "summary": revision["decision_question"],
            "evidence_refs": [s["url"] for s in revision.get("sources", [])],
            "review_status": revision["review"]["status"], "content_sha256": content_hash(revision),
            **_review_details(revision["review"]),
        })
    return rows


def _event(case: dict, policies: dict[str, dict], source: dict) -> dict:
    """Built field by field from the case and its latest revision; nothing else can overwrite it."""
    latest = case["revisions"][-1]
    event = {
        "id": case["id"], "title": case["title"], "kind": case["kind"], "market": case["market"],
        "occurred_on": case["occurred_on"], "source_kind": case["source_kind"],
        "source_record_id": case.get("source_record_id"),
        "revision": latest["revision"], "recorded_on": latest["recorded_on"], "reason": latest["reason"],
        "decision": {"question": latest["decision_question"], "owner": latest.get("decision_owner"),
                     "due_on": latest.get("decide_by")},
        "hypotheses": list(latest.get("hypotheses", [])), "unknowns": list(latest.get("unknowns", [])),
        "review": {"status": latest["review"]["status"], **_review_details(latest["review"])},
        "product_lens": deepcopy(case.get("product_lens")),
        "source": {**source, "locator": f"events/{case['id']}"},
    }
    if case["source_kind"] == "market_policy":
        event.update(_policy(policies.get(case["source_record_id"])))
    else:
        event.update(status=latest["status"], summary=latest["summary"], boundary=latest["boundary"],
                     sources=deepcopy(latest["sources"]), checked_on=latest["recorded_on"],
                     policy_record_sha256=None)
    event["history"] = _history(case)
    event["content_sha256"] = content_hash(event)
    return event


def load_events(knowledge_root: Path | None) -> dict:
    """The intake snapshot. No file is an empty intake; malformed content raises ValueError.

    Policy events join existing ``market-policy`` records by ID and never copy
    policy facts into the intake.
    """
    path = knowledge_root / CONTENT_DIR / EVENTS_FILE if knowledge_root is not None else None
    events: list[dict] = []
    source = None
    if path is not None and path.is_file():
        payload = path.read_bytes()
        cases = validated_cases(json.loads(payload))
        policies = {record["id"]: record for record in market_context(knowledge_root)["records"]}
        source = {"path": f"{CONTENT_DIR}/{EVENTS_FILE}", "sha256": hashlib.sha256(payload).hexdigest()}
        events = [_event(case, policies, source) for case in cases]
    result = {"schema_version": SCHEMA_VERSION, "source": source, "events": events,
              "history": [row for event in events for row in event["history"]]}
    return {**result, "snapshot_id": content_hash(result)}


def snapshot_changes(previous: list[dict], current: list[dict], keys: tuple[str, ...]) -> list[dict]:
    """Rows added, removed or changed between two snapshots, by identity ``keys``."""
    before = {tuple(row[key] for key in keys): row for row in previous}
    after = {tuple(row[key] for key in keys): row for row in current}
    changes = []
    for identity in sorted(before.keys() | after.keys()):
        old, new = before.get(identity), after.get(identity)
        old_hash, new_hash = content_hash(old), content_hash(new)
        if old_hash != new_hash:
            changes.append(dict(zip(keys, identity, strict=True)) | {
                "previous_sha256": old_hash, "current_sha256": new_hash,
                "previous_status": old.get("status") if old else None,
                "current_status": new.get("status") if new else None,
            })
    return changes


def compare_event_snapshots(previous: dict, current: dict) -> dict:
    """A new comparison receipt; both snapshots stay untouched and review stays human."""
    if any(item.get("schema_version") != SCHEMA_VERSION for item in (previous, current)):
        raise ValueError(f"comparison requires two {SCHEMA_VERSION} snapshots")
    return {
        "previous_snapshot_id": previous["snapshot_id"], "current_snapshot_id": current["snapshot_id"],
        "event_changes": snapshot_changes(previous["events"], current["events"], ("id",)),
        "review_status": "pending",
    }
