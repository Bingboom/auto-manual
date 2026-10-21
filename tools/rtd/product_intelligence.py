"""Optional product lens: explainable research candidates for events that ask for one.

The lens reads two finished snapshots, external events and product knowledge,
and writes neither. Only an event with a ``product_lens`` is evaluated, and its
rule terms must exist in the knowledge vocabulary; otherwise the lens reports
the problem instead of silently matching nothing. Events never depend on it.
"""
from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

from tools.product_knowledge import REGISTRY_PATH
from tools.rtd.intelligence_events import SCHEMA_VERSION as EVENTS_SCHEMA, content_hash, snapshot_changes
from tools.rtd.product_matrix import number

SCHEMA_VERSION = "product-intelligence/v1"
ENGINE_VERSION = "3"
_SHA256 = re.compile(r"[0-9a-f]{64}")
# (rule field, knowledge vocabulary key, label) for every rule term the lens checks.
_TERMS = (("categories", "categories", "产品分类"), ("required_capabilities", "capabilities", "能力登记列"),
          ("required_facts", "facts", "手册数值事实"))


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
    evidence = [entry for entry in fact.get("evidence", [])
                if _registry_evidence(entry, product, name)]
    if (fact.get("state") != "known" or type(fact.get("value")) is not bool
            or fact.get("source_type") != "capability_registry" or not evidence):
        return _reason("capability", "unknown", "capability_registry",
                       f"当前市场没有可判定且带来源指纹的「{name}」登记。"), []
    state = "match" if fact["value"] else "no_match"
    return _reason("capability", state, "capability_registry",
                   f"当前市场能力登记「{name}」={'true' if fact['value'] else 'false'}；登记不等于手册认证。"), evidence


def _registry_evidence(entry: dict, product: dict, name: str) -> bool:
    return (
        entry.get("source_type") == "capability_registry"
        and entry.get("path") == REGISTRY_PATH
        and entry.get("locator") == f"{product['model']}_{product['region']}/{name}"
        and bool(_SHA256.fullmatch(str(entry.get("sha256", ""))))
        and bool(entry.get("quote"))
    )


def _manual_evidence(entry: dict, source: dict) -> bool:
    """The variant's selected source binds its evidence; another market cannot lend a quote."""
    return (
        entry.get("source_type") == "published_manual"
        and bool(_SHA256.fullmatch(str(source.get("sha256", ""))))
        and entry.get("sha256") == source["sha256"]
        and bool(source.get("route")) and bool(source.get("manual"))
        and entry.get("path") == f"{source['route']}/{source['manual']}"
        and bool(source.get("url")) and entry.get("url") == source["url"]
        and bool(entry.get("quote"))
    )


def _manual_fact(product: dict, key: str) -> tuple[dict, list[dict]]:
    fact = product.get("specifications", {}).get(key, {})
    evidence = [entry for entry in fact.get("evidence", [])
                if _manual_evidence(entry, product.get("source", {}))]
    value = fact.get("value")
    present = (fact.get("state") == "known" and fact.get("source_type") == "published_manual"
               and type(value) in (int, float) and value > 0 and bool(evidence))
    if not present:
        return _reason("evidence", "unknown", "published_manual",
                       f"本市场、本语言发布手册尚未提供可追溯的 {key} 正值证据。"), []
    unit = f" {fact['unit']}" if fact.get("unit") else ""
    return _reason("evidence", "match", "published_manual",
                   f"发布手册直接事实：{key}={number(value)}{unit}。"), evidence


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
    lens = event["product_lens"]
    region = product["region"]
    market_match = region in lens["catalog_markets"]
    reasons = [_reason(
        "market", "match" if market_match else "no_match", "curated_configuration",
        f"发布变体市场 {region}；研究目录范围 {'、'.join(lens['catalog_markets'])}。{lens['market_mapping_note']}",
    ), _category(product, lens["rule"]), _verification(event)]
    evidence = list(product.get("category", {}).get("evidence", []))
    for name in lens["rule"]["required_capabilities"]:
        reason, refs = _capability(product, name)
        reasons.append(reason)
        evidence.extend(refs)
    for key in lens["rule"]["required_facts"]:
        reason, refs = _manual_fact(product, key)
        reasons.append(reason)
        evidence.extend(refs)
    evidence = _deduplicate(evidence)
    return {
        "source_type": "rule_inference",
        "event_id": event["id"], "product_id": product["id"], "model": product["model"],
        "name": product.get("name", product["model"]), "market": region,
        "language": product["language"], "version": product.get("version"), "status": _status(reasons),
        "reasons": reasons, "evidence": evidence,
        "provenance": {
            "engine_version": ENGINE_VERSION, "rule_sha256": content_hash(lens["rule"]),
            "rule_source": {**event["source"], "locator": f"{event['source']['locator']}/product_lens"},
            "event_sha256": event["content_sha256"], "product_sha256": content_hash(product),
            "evidence_sha256": content_hash(evidence),
        },
        "unknowns": [reason["message"] for reason in reasons if reason["state"] == "unknown"],
    }


def _problems(rule: dict, vocabulary: dict) -> list[str]:
    """Rule terms this snapshot cannot evaluate; a vocabulary the snapshot lacks is not checked."""
    problems = []
    for field, key, label in _TERMS:
        known = vocabulary.get(key) or []
        problems += [f"规则引用的{label}「{term}」不在当前产品知识快照中，可能拼写有误或已改名。"
                     for term in rule[field] if known and term not in known]
    return problems


def product_lens_context(knowledge: dict, intel: dict) -> dict:
    """Pure build-time derivation over two snapshots; it never changes intake or product sources."""
    if knowledge.get("schema_version") != "product-knowledge/v1":
        raise ValueError("product lens requires product-knowledge/v1")
    if not knowledge.get("content_sha256") or not isinstance(knowledge.get("products"), list):
        raise ValueError("product lens requires a bound product knowledge snapshot")
    if intel.get("schema_version") != EVENTS_SCHEMA or not intel.get("snapshot_id"):
        raise ValueError(f"product lens requires a bound {EVENTS_SCHEMA} snapshot")
    lenses, associations = [], []
    for event in intel["events"]:
        if event.get("product_lens") is None:
            continue
        problems = _problems(event["product_lens"]["rule"], knowledge.get("vocabulary") or {})
        lenses.append({"event_id": event["id"], "status": "invalid" if problems else "evaluated",
                       "problems": problems})
        if not problems:
            associations += [evaluate_association(event, product) for product in knowledge["products"]]
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION, "engine_version": ENGINE_VERSION,
        "knowledge_snapshot_id": knowledge["content_sha256"], "events_snapshot_id": intel["snapshot_id"],
        "lenses": lenses, "associations": associations,
    }
    result["snapshot_id"] = content_hash(result)
    return result


def compare_lens_snapshots(previous: dict, current: dict) -> dict:
    """A new comparison receipt; both historical snapshots remain untouched and review stays human."""
    if any(item.get("schema_version") != SCHEMA_VERSION for item in (previous, current)):
        raise ValueError(f"comparison requires two {SCHEMA_VERSION} snapshots")
    return {
        "previous_snapshot_id": previous["snapshot_id"], "current_snapshot_id": current["snapshot_id"],
        "knowledge_changed": previous["knowledge_snapshot_id"] != current["knowledge_snapshot_id"],
        "events_changed": previous["events_snapshot_id"] != current["events_snapshot_id"],
        "lens_changes": snapshot_changes(previous["lenses"], current["lenses"], ("event_id",)),
        "association_changes": snapshot_changes(previous["associations"], current["associations"],
                                                ("event_id", "product_id")),
        "review_status": "pending",
    }
