"""Push-ready decision digest of external events; it reads no product data.

A delivery channel (a Feishu bot, an email, a person pasting it) sends this
digest: one item per event, pending decisions first, each with what happened,
its verification and sources, the decision it asks for, who decides and by
when. Building the digest never sends anything. ``items`` keeps every field
structured for channel adapters; ``text`` is CommonMark whose intake text is
collapsed to one line and has its Markdown punctuation escaped.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from tools.rtd.intelligence_events import SCHEMA_VERSION as EVENTS_SCHEMA, content_hash

SCHEMA_VERSION = "external-intel-digest/v1"
KIND_LABELS = {"policy": "政策变化", "market": "市场变化", "competitor": "竞品动态"}
STATUS_LABELS = {
    "verified": "事件要点已核实", "unverified": "待核实线索",
    "demand": "业务需求依据", "missing": "来源资料缺失",
}
_MARKDOWN = re.compile(r"([\\`*_\[\]<>])")


def safe_external_url(value: object) -> str:
    """A public HTTPS URL that is safe as a link or bare text, else ""."""
    if not isinstance(value, str) or any(c.isspace() or ord(c) < 32 or c in '\\<>"`' for c in value):
        return ""
    try:
        parts = urlsplit(value)
        return value if (
            parts.scheme == "https" and parts.hostname
            and parts.username is None and parts.password is None
        ) else ""
    except ValueError:
        return ""


def _plain(value: object) -> str:
    """Literal one-line text: no line breaks, links, emphasis or markup from the intake."""
    return _MARKDOWN.sub(r"\\\1", " ".join(str(value).split()))


def _item(event: dict, page: str, base_url: str) -> dict:
    anchor = f"{page}.html#event-{event['id']}"
    review = event["review"]
    return {
        "event_id": event["id"], "title": event["title"], "kind": event["kind"], "market": event["market"],
        "occurred_on": event["occurred_on"], "recorded_on": event["recorded_on"], "revision": event["revision"],
        "verification": event["status"], "summary": event["summary"], "boundary": event.get("boundary") or "",
        "sources": [{"kind": source.get("kind"), "title": source.get("title"),
                     "url": safe_external_url(source.get("url")) or None} for source in event["sources"]],
        "decision": dict(event["decision"]),
        "review": {key: review.get(key) for key in ("status", "decision", "reviewed_by", "reviewed_on")},
        "hypotheses": list(event["hypotheses"]), "open_questions": list(event["unknowns"]),
        "page": anchor, "url": f"{base_url}/{anchor}" if base_url else None,
        "event_sha256": event["content_sha256"],
    }


def _message(item: dict) -> str:
    decision, review = item["decision"], item["review"]
    lines = [
        f"### {_plain(item['title'])}",
        f"- 市场：{_plain(item['market'])} · {KIND_LABELS.get(item['kind'], '外部事件')} · "
        f"{STATUS_LABELS.get(item['verification'], '来源状态未知')}",
        f"- 发生／生效：{item['occurred_on']} · 最近录入：{item['recorded_on']}（修订 {item['revision']}）",
        f"- 需要决策：{_plain(decision['question'])}",
        f"- 决策人：{_plain(decision['owner']) if decision['owner'] else '待指派'} · "
        f"截止：{decision['due_on'] or '未设定'}",
        f"- 外部发生了什么：{_plain(item['summary'])}",
    ]
    if item["boundary"]:
        lines.append(f"- 适用边界：{_plain(item['boundary'])}")
    lines += [f"- 来源：{_plain(source['title'] or '来源')} {source['url'] or '（无安全可用的链接）'}"
              for source in item["sources"]] or ["- 来源：尚未提供"]
    lines += [f"- 可能影响（未证实）：{_plain(text)}" for text in item["hypotheses"]]
    lines += [f"- 待核实：{_plain(text)}" for text in item["open_questions"]]
    if review["status"] == "reviewed":
        lines.append(f"- 人工判断：{_plain(review['decision'])}（{_plain(review['reviewed_by'])}，"
                     f"{review['reviewed_on']}）")
    else:
        lines.append("- 人工判断：待决策")
    lines.append(f"- 详情：{item['url'] or item['page']}")
    return "\n".join(lines)


def _text(digest: dict) -> str:
    pending = [item for item in digest["items"] if item["review"]["status"] != "reviewed"]
    decided = [item for item in digest["items"] if item["review"]["status"] == "reviewed"]
    counts = digest["counts"]
    parts = [
        "# 外部情报决策摘要",
        f"事件 {counts['events']} 条 · 待决策 {counts['pending']} 条 · 快照 {digest['events_snapshot_id'][:12]}",
    ]
    for title, items in (("待决策", pending), ("已有人工判断", decided)):
        if items:
            parts += [f"## {title}（{len(items)}）", *(item["message"] for item in items)]
    if not digest["items"]:
        parts.append("暂未录入外部事件。")
    return "\n\n".join(parts) + "\n"


def decision_order(events: list[dict]) -> list[dict]:
    """Pending judgments first, then by due date (none last), latest record and ID; the page uses it too."""
    ordered = sorted(events, key=lambda event: event["id"])
    ordered.sort(key=lambda event: event["recorded_on"], reverse=True)
    ordered.sort(key=lambda event: ((event.get("review") or {}).get("status") == "reviewed",
                                    (event.get("decision") or {}).get("due_on") is None,
                                    (event.get("decision") or {}).get("due_on") or ""))
    return ordered


def decision_digest(intel: dict, *, page: str, base_url: str = "") -> dict:
    """One item per event in decision order; building it never sends anything."""
    if intel.get("schema_version") != EVENTS_SCHEMA:
        raise ValueError(f"decision digest needs {EVENTS_SCHEMA}")
    items = [_item(event, page, base_url) for event in decision_order(intel["events"])]
    for item in items:
        item["message"] = _message(item)
    pending = sum(item["review"]["status"] != "reviewed" for item in items)
    digest = {"schema_version": SCHEMA_VERSION, "events_snapshot_id": intel["snapshot_id"],
              "counts": {"events": len(items), "pending": pending, "reviewed": len(items) - pending},
              "items": items}
    digest["text"] = _text(digest)
    return {**digest, "snapshot_id": content_hash(digest)}
