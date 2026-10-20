"""Versioned research intake; policy facts remain owned by the business snapshot."""
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

SCHEMA_VERSION = "product-intelligence-cases/v1"
_ID = re.compile(r"[a-z][a-z0-9-]*")
_STATUSES = {"verified", "unverified", "demand"}


def content_hash(value: Any) -> str:
    """Hash canonical JSON, independent of formatting and object key order."""
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _text(value: Any, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"research case needs non-empty {label}")


def _texts(value: Any, label: str, *, required: bool = True) -> None:
    if not isinstance(value, list) or (required and not value):
        raise ValueError(f"research case needs a list of {label}")
    for item in value:
        _text(item, label)


def _date(value: Any, label: str) -> None:
    _text(value, label)
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"research case needs ISO {label}") from exc
    if parsed.isoformat() != value:
        raise ValueError(f"research case needs ISO {label}")


def _sources(sources: Any) -> None:
    if not isinstance(sources, list):
        raise ValueError("research sources must be a list")
    for source in sources:
        for key in ("kind", "title", "url", "note"):
            _text(source.get(key), f"source {key}")
        parts = urlsplit(source["url"])
        if parts.scheme != "https" or not parts.netloc or parts.username or parts.password:
            raise ValueError("research source needs a public HTTPS URL")
        _date(source.get("checked_on"), "source checked_on")
        if source.get("published_on") is not None:
            _date(source["published_on"], "source published_on")


def _review(review: Any) -> None:
    if not isinstance(review, dict) or review.get("status") not in {"pending", "reviewed"}:
        raise ValueError("research review must be pending or reviewed")
    if review["status"] == "reviewed":
        _text(review.get("decision"), "human review decision")
        _text(review.get("reviewed_by"), "human reviewer")
        _date(review.get("reviewed_on"), "human review reviewed_on")
    elif any(review.get(field) is not None for field in ("decision", "reviewed_by", "reviewed_on")):
        raise ValueError("pending research cannot carry human review details")


def _review_details(review: dict) -> dict:
    """Normalize pending metadata without manufacturing an operator or decision."""
    return {key: review.get(key) for key in ("decision", "reviewed_by", "reviewed_on")}


def _revision(revision: dict, expected: int, external: bool) -> None:
    if type(revision.get("revision")) is not int or revision["revision"] != expected:
        raise ValueError("research revisions must be consecutive, starting at 1")
    _date(revision.get("recorded_on"), "revision recorded_on")
    for key in ("reason", "research_question"):
        _text(revision.get(key), key)
    for key in ("hypotheses", "unknowns"):
        _texts(revision.get(key), key)
    _review(revision.get("review"))
    if external:
        for key in ("summary", "boundary"):
            _text(revision.get(key), key)
        if revision.get("status") not in _STATUSES:
            raise ValueError("unknown research source verification status")
        _sources(revision.get("sources"))
        if revision["status"] == "verified" and not any(s["kind"] == "official" for s in revision["sources"]):
            raise ValueError("verified research events need an official source")


def _case(case: dict, ids: set[str]) -> None:
    key = case.get("id")
    if not isinstance(key, str) or not _ID.fullmatch(key) or key in ids:
        raise ValueError("research case ids must be unique lower-case ids")
    ids.add(key)
    for field in ("title", "market", "market_mapping_note"):
        _text(case.get(field), field)
    if case.get("kind") not in {"policy", "market", "competitor"}:
        raise ValueError("unknown research case kind")
    _date(case.get("occurred_on"), "occurred_on")
    _texts(case.get("catalog_markets"), "catalog markets")
    source_kind = case.get("source_kind")
    if source_kind not in {"market_policy", "external_event"}:
        raise ValueError("unknown research intake source")
    if source_kind == "market_policy":
        _text(case.get("source_record_id"), "source_record_id")
    rule = case.get("rule", {})
    for field in ("categories", "required_capabilities", "required_facts"):
        _texts(rule.get(field), field)
    revisions = case.get("revisions")
    if not isinstance(revisions, list) or not revisions:
        raise ValueError("research case needs revisions")
    for expected, revision in enumerate(revisions, 1):
        _revision(revision, expected, source_kind == "external_event")


def _validated_cases(data: dict) -> list[dict]:
    if data.get("schema_version") != SCHEMA_VERSION or not isinstance(data.get("cases"), list):
        raise ValueError(f"research intake needs {SCHEMA_VERSION}")
    ids: set[str] = set()
    for case in data["cases"]:
        _case(case, ids)
    return data["cases"]


def load_cases(path: Path) -> list[dict]:
    """Malformed intake fails visibly, instead of silently promoting incomplete evidence."""
    return _validated_cases(json.loads(path.read_text(encoding="utf-8")))


def _policy(record: dict | None) -> dict:
    if record is None:
        return {"status": "missing", "summary": "尚未加载关联的市场政策记录。",
                "sources": [], "boundary": "缺少业务政策快照，不能把研究配置当作已核实政策。",
                "reviewed_on": None, "policy_record_sha256": None}
    return {"status": record["status"], "summary": record["change"], "sources": [
        {**ref, "checked_on": record["reviewed"]} for ref in record["sources"]],
        "boundary": record.get("boundary", ""), "reviewed_on": record["reviewed"],
        "policy_record_sha256": content_hash(record)}


def _history(case: dict) -> list[dict]:
    """Intake revisions are historical authoring records, never invented evaluations."""
    rows = []
    for revision in case["revisions"]:
        rows.append({
            "event_id": case["id"], "revision": revision["revision"],
            "recorded_on": revision["recorded_on"], "reason": revision["reason"],
            "summary": revision["research_question"],
            "evidence_refs": [s["url"] for s in revision.get("sources", [])],
            "review_status": revision["review"]["status"], "content_sha256": content_hash(revision),
            **_review_details(revision["review"]),
        })
    return rows


def _event(case: dict, policies: dict[str, dict], rule_source: dict) -> dict:
    latest = deepcopy(case["revisions"][-1])
    keys = ("id", "title", "kind", "market", "catalog_markets", "market_mapping_note",
            "occurred_on", "source_kind", "rule")
    event = {key: deepcopy(case[key]) for key in keys}
    event.update(latest)
    event["review"] = {"status": latest["review"]["status"], **_review_details(latest["review"])}
    event["source_record_id"] = case.get("source_record_id")
    event["reviewed_on"] = latest["recorded_on"]
    if case["source_kind"] == "market_policy":
        event.update(_policy(policies.get(case["source_record_id"])))
        event["unknowns"].append("EU 目录范围只用于研究筛选，不能证明在该国家销售或满足当地并网要求。")
    event["history"] = _history(case)
    event["rule_source"] = rule_source
    event["content_sha256"] = content_hash(event)
    return event


def load_events(knowledge_root: Path | None, cases_path: Path) -> list[dict]:
    """Join by existing policy ID; never copy policy facts into an engineering fallback."""
    records = market_context(knowledge_root)["records"] if knowledge_root is not None else []
    policies = {record["id"]: record for record in records}
    payload = cases_path.read_bytes()
    cases = _validated_cases(json.loads(payload))
    source = {
        "source_type": "curated_configuration",
        "path": cases_path.name,
        "sha256": hashlib.sha256(payload).hexdigest(),
    }
    try:
        source["path"] = cases_path.resolve().relative_to(Path(__file__).resolve().parents[2]).as_posix()
    except ValueError:
        pass
    return [_event(case, policies, {**source, "locator": f"cases/{case['id']}/rule"}) for case in cases]
