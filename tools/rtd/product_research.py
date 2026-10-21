"""Read-only presentation of external events as a navigable index.

Every event is one row in decision order (the digest's): what it is, the
decision it asks for, who decides and by when. Its details (what happened,
sources, open questions, human judgment, revisions) open under the row. A
product lens appears only inside an event that configured one, and its absence
or failure never hides the event. No new facts are extracted here.
"""
from __future__ import annotations

from copy import deepcopy
import re
from urllib.parse import unquote, urlsplit

from tools.rtd.decision_digest import KIND_LABELS, STATUS_LABELS, decision_order, safe_external_url
from tools.rtd.intelligence_events import SCHEMA_VERSION as EVENTS_SCHEMA
from tools.rtd.product_matrix import number

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
LENS_LABELS = {
    "not_configured": "未配置产品视角", "unavailable": "产品视角暂不可用",
    "invalid": "产品视角规则需修正", "evaluated": "已按规则计算",
}
_GROUPS = {"candidate": "candidates", "unknown": "unknown_products", "excluded": "excluded_products"}


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


def _display(value: object) -> str:
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, (int, float)):
        return number(value)
    return _text(value)


def _fact(label: str, record: dict) -> dict:
    state = record.get("state")
    value = record.get("value")
    display = "未知"
    if state == "known" and value is not None:
        display = _display(value)
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


def _identity(association: dict, product: dict, routes: set[str]) -> dict:
    route = _local_route((product.get("source") or {}).get("url"))
    return {
        "id": _text(association.get("product_id")),
        "model": _text(product.get("model") or association.get("model"), "型号未标明"),
        "name": _text(product.get("name") or association.get("name"), "产品名称未标明"),
        "market": _text(product.get("region") or association.get("market"), "市场未知"),
        "language": _text(product.get("language") or association.get("language"), "语言未知"),
        "version": _text(product.get("version") or association.get("version"), "版本未知"),
        "page": route[:-5] if route in routes else "",
        "status": association["status"], "status_label": ASSOCIATION_LABELS[association["status"]],
    }


def _product_view(association: dict, product: dict | None, routes: set[str]) -> dict:
    """A candidate's full card: reasons, evidence, gaps and the variant's published source."""
    product = product or {}
    source = product.get("source") or {}
    unknowns = list(dict.fromkeys(
        _unknown(value) for value in [*association.get("unknowns", []), *product.get("unknowns", [])]
    ))
    if not product:
        unknowns.append("当前产品知识快照没有该产品变体，无法核对其发布证据。")
    return {
        **_identity(association, product, routes),
        "association_source_label": SOURCE_LABELS.get(association.get("source_type"), "规则推导"),
        "provenance": association.get("provenance") or {},
        "reasons": [_reason_view(reason) for reason in association.get("reasons", [])],
        "facts": _product_facts(product),
        "evidence": [_reference(record, routes) for record in association.get("evidence", [])],
        "unknowns": unknowns,
        "source": {key: _text(source.get(key), "未记录")
                   for key in ("route", "manual", "sha256", "built_at", "git_ref", "language_scope")},
    }


def _compact_view(association: dict, product: dict | None, routes: set[str]) -> dict:
    """An unknown or excluded variant as one row: which conditions failed or lack evidence."""
    view = _identity(association, product or {}, routes)
    view["reasons"] = [_reason_view(reason) for reason in association.get("reasons", [])
                       if reason.get("state") != "match"]
    return view


def _history_view(event: dict) -> list[dict]:
    return [{
        "revision": _text(row.get("revision"), "未记录"),
        "recorded_on": _text(row.get("recorded_on"), "日期未记录"),
        "summary": _text(row.get("summary")),
        "reason": _text(row.get("reason")),
        "review_label": "已人工判断" if row.get("review_status") == "reviewed" else "待人工判断",
        "review_decision": _text(row.get("decision")) if row.get("review_status") == "reviewed" else "",
        "reviewed_by": _text(row.get("reviewed_by")) if row.get("review_status") == "reviewed" else "",
        "reviewed_on": _text(row.get("reviewed_on")) if row.get("review_status") == "reviewed" else "",
        "content_sha256": _text(row.get("content_sha256")),
        "evidence_refs": [{"url": safe_external_url(url), "label": _text(url)}
                          for url in row.get("evidence_refs", [])],
    } for row in event.get("history", [])]


def _event_view(event: dict) -> dict:
    review = event.get("review") or {}
    decision = event.get("decision") or {}
    reviewed = review.get("status") == "reviewed"
    return {
        **event, "anchor": f"event-{event['id']}",
        "status_label": STATUS_LABELS[event["status"]],
        "kind_label": KIND_LABELS.get(event.get("kind"), "外部事件"),
        "review_state": "reviewed" if reviewed else "pending",
        "review_label": "已人工判断" if reviewed else "待人工判断",
        "review_decision": _text(review.get("decision"), "尚未记录人工判断。"),
        "reviewed_by": _text(review.get("reviewed_by")) if reviewed else "",
        "human_reviewed_on": _text(review.get("reviewed_on")) if reviewed else "",
        "decision_question": _text(decision.get("question"), "尚未提出决策问题。"),
        "decision_owner": _text(decision.get("owner"), "待指派"),
        "decision_due": _text(decision.get("due_on"), "未设定"),
        "source_label": SOURCE_LABELS.get(event.get("source_kind"), "外部资料"),
        "sources": [{
            **source, "safe_url": safe_external_url(source.get("url")),
            "kind_label": SOURCE_LABELS.get(source.get("kind"), "参考来源"),
        } for source in event.get("sources", [])],
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


def _lens_state(event: dict, entry: dict | None, lens_problem: str) -> dict:
    lens = event.get("product_lens")
    if lens is None:
        state, message = "not_configured", ""
    elif entry is None:
        state, message = "unavailable", _text(lens_problem, "产品知识快照不可用，暂不计算产品关联。")
    else:
        state, message = entry["status"], ""
    return {
        "state": state, "label": LENS_LABELS[state], "message": message,
        "problems": list(entry.get("problems", [])) if entry else [],
        "note": _text((lens or {}).get("market_mapping_note")),
        "candidates": [], "unknown_products": [], "excluded_products": [],
    }


def _bound_lens(intel: dict, lens: dict | None, knowledge: dict | None) -> dict:
    """Lens entries by event, after checking that the lens was computed from these two snapshots."""
    if lens is None:
        return {}
    if lens.get("schema_version") != "product-intelligence/v1":
        raise ValueError("research page needs product-intelligence/v1")
    if not knowledge or knowledge.get("schema_version") != "product-knowledge/v1":
        raise ValueError("research page needs the product-knowledge/v1 snapshot its lens used")
    if (not knowledge.get("content_sha256") or lens.get("knowledge_snapshot_id") != knowledge["content_sha256"]
            or lens.get("events_snapshot_id") != intel.get("snapshot_id")):
        raise ValueError("research page lens snapshot does not match")
    return {entry["event_id"]: entry for entry in lens.get("lenses", [])}


def _attach(events: list[dict], associations: list[dict], products: dict[str, dict]) -> None:
    """Group each association under its event's evaluated lens: candidates in full, others compact."""
    routes = {route for product in products.values()
              if (route := _local_route((product.get("source") or {}).get("url")))}
    by_event = {event["id"]: event for event in events}
    for association in associations:
        event = by_event.get(association.get("event_id"))
        if event is None or event["lens"]["state"] != "evaluated" or association.get("status") not in _GROUPS:
            raise ValueError("research page association has unknown event, lens or status")
        product = products.get(association.get("product_id"))
        view = (_product_view if association["status"] == "candidate" else _compact_view)(
            association, product, routes)
        event["lens"][_GROUPS[association["status"]]].append(view)


def research_page_context(intel: dict, *, lens: dict | None = None, knowledge: dict | None = None,
                          lens_problem: str = "", downloads: tuple = ()) -> dict:
    """Adapt matching snapshots without mutating contracts or inferring new facts."""
    if intel.get("schema_version") != EVENTS_SCHEMA:
        raise ValueError(f"research page needs {EVENTS_SCHEMA}")
    # All payloads remain caller-owned, including nested hypothesis/history lists.
    intel, lens, knowledge = deepcopy(intel), deepcopy(lens), deepcopy(knowledge)
    entries = _bound_lens(intel, lens, knowledge)
    events = _event_views(decision_order(intel["events"]))
    for event in events:
        event["lens"] = _lens_state(event, entries.get(event["id"]), lens_problem)
    _attach(events, (lens or {}).get("associations", []),
            {product["id"]: product for product in (knowledge or {}).get("products", [])})
    return {
        "research_events": events,
        "research_markets": sorted({_text(event.get("market"), "市场未知") for event in events}),
        "events_snapshot": _text(intel.get("snapshot_id"), "未记录"),
        "lens_snapshot": _text((lens or {}).get("snapshot_id")),
        "knowledge_snapshot": _text((knowledge or {}).get("content_sha256")),
        "knowledge_warnings": [_text(warning) for warning in (knowledge or {}).get("warnings", [])],
        "research_downloads": [{"label": label, "path": path} for label, path in downloads],
        "research_summary": {
            "events": len(events),
            "pending": sum(event["review_state"] == "pending" for event in events),
            "reviewed": sum(event["review_state"] == "reviewed" for event in events),
            "verified": sum(event["status"] == "verified" for event in events),
        },
    }
