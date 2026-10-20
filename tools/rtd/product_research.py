"""Read-only presentation of product research contracts; no new fact extraction."""
from __future__ import annotations

from copy import deepcopy
import re
from urllib.parse import unquote, urlsplit

PAGE = "research/product-intelligence"
TEMPLATE = "product_research.html"
_ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]*")
SOURCE_LABELS = {
    "published_manual": "已发布说明书",
    "curated_configuration": "人工配置／分类",
    "capability_registry": "能力登记表",
    "rule_inference": "规则推导",
    "external_event": "外部事件",
    "external_source": "外部来源",
    "market_policy": "市场政策资料",
    "official": "官方来源",
    "brief": "二手资料",
}
STATUS_LABELS = {
    "verified": "事件要点已核实", "unverified": "待核实线索",
    "demand": "业务需求依据", "missing": "来源资料缺失",
}
ASSOCIATION_LABELS = {"candidate": "候选关联", "unknown": "证据不足", "excluded": "暂不关联"}
DIMENSION_LABELS = {
    "market": "市场范围", "category": "产品分类", "capability": "功能能力",
    "evidence": "证据支持", "verification": "来源核实",
}
SPEC_LABELS = {
    "capacity_wh": "电池容量", "ac_output_w": "AC 额定输出", "ac_surge_w": "AC 峰值输出",
    "weight_kg": "重量", "cycle_life": "循环寿命", "solar_peak_w": "太阳能峰值功率",
    "ip_rating": "防护等级", "output_w": "输出功率",
}


def _text(value: object, fallback: str = "") -> str:
    return str(value) if value is not None and str(value).strip() else fallback


def _local_route(value: object) -> str:
    """Accept only a catalog's literal, relative HTML route, never a URL."""
    if not isinstance(value, str) or not value or any(c.isspace() for c in value):
        return ""
    if "\\" in value or unquote(value) != value or any(ord(c) < 32 for c in value):
        return ""
    try:
        parts = urlsplit(value)
    except ValueError:
        return ""
    if parts.scheme or parts.netloc or parts.query or parts.fragment or value.startswith("/"):
        return ""
    if any(segment in {"", ".", ".."} for segment in value.split("/")):
        return ""
    return value if value.endswith(".html") else ""


def _external_url(value: object) -> str:
    if not isinstance(value, str) or any(c.isspace() or ord(c) < 32 for c in value) or "\\" in value:
        return ""
    try:
        parts = urlsplit(value)
        return value if (
            parts.scheme == "https" and parts.hostname
            and parts.username is None and parts.password is None
        ) else ""
    except ValueError:
        return ""


def _reference(record: dict, routes: set[str]) -> dict:
    """An evidence file path stays text; only the published-route allowlist links."""
    url = record.get("url")
    local = _local_route(url)
    return {
        "source_type": _text(record.get("source_type"), "unknown"),
        "source_label": SOURCE_LABELS.get(record.get("source_type"), "来源类型未标明"),
        "page": local[:-5] if local in routes else "",
        "path": _text(record.get("path")),
        "locator": _text(record.get("locator"), "未提供精确定位"),
        "quote": _text(record.get("quote")),
        "sha256": _text(record.get("sha256")),
        "missing_link": not (local and local in routes),
    }


def _fact(label: str, record: dict) -> dict:
    state = record.get("state")
    value = record.get("value")
    display = "未知"
    if state == "known" and value is not None:
        display = ("是" if value else "否") if isinstance(value, bool) else _text(value)
        if record.get("unit"):
            display = f"{display} {record['unit']}"
    return {
        "label": label, "value": display,
        "source_label": SOURCE_LABELS.get(record.get("source_type"), "来源类型未标明"),
        "reason": _text(record.get("reason")),
        "state": "known" if state == "known" and value is not None else "unknown",
    }


def _unknown(value: object) -> str:
    """Knowledge unknowns identify a field; association unknowns are already prose."""
    if not isinstance(value, dict):
        return _text(value, "尚待核实。")
    field = _text(value.get("field"), "未知字段")
    field = field.removeprefix("specifications.").removeprefix("capabilities.")
    label = {**SPEC_LABELS, "category": "产品分类", "language": "语言范围",
             "version": "发布版本", "capabilities": "能力登记"}.get(field, field)
    return f"{label}：{_text(value.get('reason'), '缺少可核实的资料。')}"


def _reason_view(reason: dict) -> dict:
    return {
        "dimension": DIMENSION_LABELS.get(reason.get("dimension"), "关联依据"),
        "state": reason.get("state") if reason.get("state") in {"match", "unknown", "no_match"} else "unknown",
        "state_label": {"match": "符合", "unknown": "待核实", "no_match": "不符合"}.get(reason.get("state"), "待核实"),
        "source_label": SOURCE_LABELS.get(reason.get("source_type"), "来源类型未标明"),
        "message": _text(reason.get("message")),
    }


def _product_facts(product: dict) -> list[dict]:
    facts = []
    if product.get("category"):
        facts.append(_fact("产品分类", product["category"]))
    for key, record in (product.get("specifications") or {}).items():
        facts.append(_fact(SPEC_LABELS.get(key, key), record))
    for key, record in (product.get("capabilities") or {}).items():
        facts.append(_fact(key, record))
    return facts


def _product_view(association: dict, product: dict | None, routes: set[str]) -> dict:
    product = product or {}
    source = product.get("source") or {}
    route = _local_route(source.get("url"))
    unknowns = list(dict.fromkeys(
        _unknown(value) for value in [*association.get("unknowns", []), *product.get("unknowns", [])]
    ))
    if not product:
        unknowns.append("当前产品知识快照没有该产品变体，无法核对其发布证据。")
    return {
        "id": _text(association.get("product_id")),
        "model": _text(product.get("model") or association.get("model"), "型号未标明"),
        "name": _text(product.get("name") or association.get("name"), "产品名称未标明"),
        "market": _text(product.get("region") or association.get("market"), "市场未知"),
        "language": _text(product.get("language") or association.get("language"), "语言未知"),
        "version": _text(product.get("version") or association.get("version"), "版本未知"),
        "page": route[:-5] if route in routes else "",
        "status": association["status"], "status_label": ASSOCIATION_LABELS[association["status"]],
        "association_source_label": SOURCE_LABELS.get(association.get("source_type"), "规则推导"),
        "provenance": association.get("provenance") or {},
        "reasons": [_reason_view(reason) for reason in association.get("reasons", [])],
        "facts": _product_facts(product),
        "evidence": [_reference(record, routes) for record in association.get("evidence", [])],
        "hypotheses": association.get("hypotheses", []), "unknowns": unknowns,
        "source": {key: _text(source.get(key), "未记录")
                   for key in ("route", "manual", "sha256", "built_at", "git_ref", "language_scope")},
    }


def _history_view(event: dict) -> list[dict]:
    return [{
        "revision": _text(row.get("revision"), "未记录"),
        "recorded_on": _text(row.get("recorded_on"), "日期未记录"),
        "summary": _text(row.get("summary")),
        "reason": _text(row.get("reason")),
        "review_label": "已人工复核" if row.get("review_status") == "reviewed" else "待人工复核",
        "review_decision": _text(row.get("decision")) if row.get("review_status") == "reviewed" else "",
        "reviewed_by": _text(row.get("reviewed_by")) if row.get("review_status") == "reviewed" else "",
        "reviewed_on": _text(row.get("reviewed_on")) if row.get("review_status") == "reviewed" else "",
        "content_sha256": _text(row.get("content_sha256")),
        "evidence_refs": [{"url": _external_url(url), "label": _text(url)}
                          for url in row.get("evidence_refs", [])],
    } for row in event.get("history", [])]


def _event_view(event: dict) -> dict:
    review = event.get("review") or {}
    return {
        **event, "status_label": STATUS_LABELS[event["status"]],
        "kind_label": {"policy": "政策变化", "market": "市场变化", "competitor": "竞品动态"}.get(
            event.get("kind"), "外部事件"),
        "review_label": "已人工复核" if review.get("status") == "reviewed" else "待人工复核",
        "review_decision": _text(review.get("decision"), "尚未记录人工判断。"),
        "reviewed_by": _text(review.get("reviewed_by")) if review.get("status") == "reviewed" else "",
        "human_reviewed_on": _text(review.get("reviewed_on")) if review.get("status") == "reviewed" else "",
        "source_label": SOURCE_LABELS.get(event.get("source_kind"), "外部资料"),
        "sources": [{
            **source, "safe_url": _external_url(source.get("url")),
            "kind_label": SOURCE_LABELS.get(source.get("kind"), "参考来源"),
        } for source in event.get("sources", [])],
        "candidates": [], "unknown_products": [], "excluded_products": [],
        "history": _history_view(event),
    }


def _event_views(records: list[dict]) -> list[dict]:
    """Validate event identities before building safe page anchors and labels."""
    events = []
    event_ids = set()
    for event in records:
        key = event["id"]
        if not isinstance(key, str) or not _ID.fullmatch(key) or key in event_ids:
            raise ValueError("research page event ids must be unique safe identifiers")
        event_ids.add(key)
        if event.get("status") not in STATUS_LABELS:
            raise ValueError("research page has an unknown event status")
        events.append(_event_view(event))
    return events


def research_page_context(knowledge: dict, research: dict) -> dict:
    """Adapt matching snapshots without mutating contracts or inferring new facts."""
    if knowledge.get("schema_version") != "product-knowledge/v1":
        raise ValueError("research page needs product-knowledge/v1")
    if research.get("schema_version") != "product-intelligence/v1":
        raise ValueError("research page needs product-intelligence/v1")
    if not knowledge.get("content_sha256") or research.get("knowledge_snapshot_id") != knowledge["content_sha256"]:
        raise ValueError("research page knowledge snapshot does not match")
    # All payloads remain caller-owned, including nested hypothesis/history lists.
    knowledge, research = deepcopy(knowledge), deepcopy(research)
    products = {product["id"]: product for product in knowledge["products"]}
    routes = {route for product in products.values()
              if (route := _local_route((product.get("source") or {}).get("url")))}
    events = _event_views(research["events"])
    by_event = {event["id"]: event for event in events}
    groups = {"candidate": "candidates", "unknown": "unknown_products", "excluded": "excluded_products"}
    for association in research["associations"]:
        if association.get("event_id") not in by_event or association.get("status") not in groups:
            raise ValueError("research page association has unknown event or status")
        view = _product_view(association, products.get(association.get("product_id")), routes)
        by_event[association["event_id"]][groups[association["status"]]].append(view)
    for event in events:
        event["association_count"] = sum(len(event[key]) for key in groups.values())
    return {
        "research_events": events,
        "research_markets": sorted({_text(event.get("market"), "市场未知") for event in events}),
        "research_snapshot": _text(research.get("snapshot_id"), "未记录"),
        "knowledge_snapshot": knowledge["content_sha256"],
        "knowledge_warnings": [_text(warning) for warning in knowledge.get("warnings", [])],
        "has_products": bool(products),
        "research_summary": {
            "events": len(events),
            "candidates": sum(len(event["candidates"]) for event in events),
            "unknown": sum(len(event["unknown_products"]) for event in events),
            "pending": sum(event["review_label"] == "待人工复核" for event in events),
        },
    }
