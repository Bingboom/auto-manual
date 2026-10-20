"""Explainable research candidates over the read-only product knowledge contract."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from tools.rtd.intelligence_events import content_hash, load_events

SCHEMA_VERSION = "product-intelligence/v1"
CASES = Path(__file__).resolve().parents[1] / "rtd_portal_assets" / "product_intelligence_cases.json"


def _reason(dimension: str, state: str, source_type: str, message: str) -> dict:
    return {"dimension": dimension, "state": state, "source_type": source_type, "message": message}


def _category(product: dict, rule: dict) -> dict:
    fact = product.get("category", {})
    if fact.get("state") != "known" or fact.get("value") is None:
        return _reason("category", "unknown", "curated_configuration", "产品分类缺失，无法判定研究范围。")
    accepted = fact["value"] in rule["categories"]
    return _reason("category", "match" if accepted else "no_match", "curated_configuration",
                   f"人工配置分类 {fact['value']}；规则范围：{'、'.join(rule['categories'])}。")


def _capability(product: dict, name: str) -> tuple[dict, list[dict]]:
    fact = product.get("capabilities", {}).get(name, {})
    if fact.get("state") != "known" or type(fact.get("value")) is not bool:
        return _reason("capability", "unknown", "capability_registry",
                       f"当前市场没有可判定的「{name}」登记。"), []
    state = "match" if fact["value"] else "no_match"
    return _reason("capability", state, "capability_registry",
                   f"当前市场能力登记「{name}」={'true' if fact['value'] else 'false'}；登记不等于手册认证。"), fact.get("evidence", [])


def _manual_fact(product: dict, key: str) -> tuple[dict, list[dict]]:
    fact = product.get("specifications", {}).get(key, {})
    evidence = [entry for entry in fact.get("evidence", [])
                if entry.get("source_type") == "published_manual" and entry.get("sha256") and entry.get("quote")]
    value = fact.get("value")
    present = (fact.get("state") == "known" and type(value) in (int, float) and value > 0 and bool(evidence))
    if not present:
        return _reason("evidence", "unknown", "published_manual",
                       f"本市场、本语言发布手册尚未提供可追溯的 {key} 正值证据。"), []
    return _reason("evidence", "match", "published_manual",
                   f"发布手册直接事实：{key}={value} {fact.get('unit') or ''}。"), evidence


def _status(reasons: list[dict]) -> str:
    states = {reason["state"] for reason in reasons}
    if "no_match" in states:
        return "excluded"
    return "unknown" if "unknown" in states else "candidate"


def _verification(event: dict) -> dict:
    verified = event["status"] == "verified"
    return _reason("verification", "match" if verified else "unknown", "external_source",
                   f"外部事件来源状态：{event['status']}。来源核实不代表产品适用性或研究结论获批。")


def _deduplicate(evidence: list[dict]) -> list[dict]:
    return list({content_hash(entry): deepcopy(entry) for entry in evidence}.values())


def evaluate_association(event: dict, product: dict) -> dict:
    """All dimensions are required; missing evidence remains distinct from explicit false."""
    region = product["region"]
    market_match = region in event["catalog_markets"]
    reasons = [_reason(
        "market", "match" if market_match else "no_match", "curated_configuration",
        f"发布变体市场 {region}；研究目录范围 {'、'.join(event['catalog_markets'])}。{event['market_mapping_note']}",
    ), _category(product, event["rule"]), _verification(event)]
    evidence = list(product.get("category", {}).get("evidence", []))
    for name in event["rule"]["required_capabilities"]:
        reason, refs = _capability(product, name)
        reasons.append(reason)
        evidence.extend(refs)
    for key in event["rule"]["required_facts"]:
        reason, refs = _manual_fact(product, key)
        reasons.append(reason)
        evidence.extend(refs)
    state = _status(reasons)
    return {
        "event_id": event["id"], "product_id": product["id"], "model": product["model"],
        "name": product.get("name", product["model"]), "market": region,
        "language": product["language"], "version": product.get("version"), "status": state,
        "reasons": reasons, "evidence": _deduplicate(evidence),
        "hypotheses": deepcopy(event["hypotheses"]) if state == "candidate" else [],
        "unknowns": [reason["message"] for reason in reasons if reason["state"] == "unknown"]
        + deepcopy(event["unknowns"]),
    }


def research_context(knowledge: dict, knowledge_root: Path | None, *, cases_path: Path | None = None) -> dict:
    """Pure build-time derivation. Rebuilding never changes intake, policy or product sources."""
    if knowledge.get("schema_version") != "product-knowledge/v1":
        raise ValueError("research requires product-knowledge/v1")
    if not knowledge.get("content_sha256") or not isinstance(knowledge.get("products"), list):
        raise ValueError("research requires a bound product knowledge snapshot")
    events = load_events(knowledge_root, cases_path or CASES)
    associations = [evaluate_association(event, product) for event in events for product in knowledge["products"]]
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION, "engine_version": "1",
        "knowledge_snapshot_id": knowledge["content_sha256"], "events": events,
        "associations": associations, "history": [row for event in events for row in event["history"]],
    }
    result["snapshot_id"] = content_hash(result)
    return result


def _changes(previous: list[dict], current: list[dict], keys: tuple[str, ...]) -> list[dict]:
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


def compare_research_snapshots(previous: dict, current: dict) -> dict:
    """A new comparison receipt; both historical snapshots remain untouched and review stays human."""
    if any(item.get("schema_version") != SCHEMA_VERSION for item in (previous, current)):
        raise ValueError("comparison requires two product-intelligence/v1 snapshots")
    return {
        "previous_snapshot_id": previous["snapshot_id"], "current_snapshot_id": current["snapshot_id"],
        "knowledge_changed": previous["knowledge_snapshot_id"] != current["knowledge_snapshot_id"],
        "event_changes": _changes(previous["events"], current["events"], ("id",)),
        "association_changes": _changes(previous["associations"], current["associations"], ("event_id", "product_id")),
        "review_status": "pending",
    }
