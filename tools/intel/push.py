"""Push the decision digest to a Feishu group as one post message.

The message is built from the digest's structured ``items``, never from its
CommonMark ``text``. Every intake string is a literal text element and only a
validated HTTPS link becomes a link element, so table text cannot add markup,
mentions or links. Pending decisions are grouped as overdue, due within seven
days and the rest; judged events are counted. When a sync report is given, the
judgments that sync recorded and the rows it could not use are listed too, so
the group sees what to fill in and what to fix.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re

from .digest import STATUS_LABELS, safe_external_url

DUE_SOON_DAYS = 7
MAX_LISTED = 20
MAX_TEXT = 200
RECORD_PLACEHOLDER = "{record_id}"
GROUPS = (("overdue", "已逾期"), ("due_soon", f"{DUE_SOON_DAYS} 天内到期"), ("pending", "待决策"))
_RECORD_ID = re.compile(r"rec[0-9A-Za-z]+")


def _plain(value: object) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= MAX_TEXT else text[:MAX_TEXT - 1] + "…"


def _text(value: object, *, bold: bool = False) -> dict:
    element = {"tag": "text", "text": str(value)}
    return {**element, "style": ["bold"]} if bold else element


def check_record_url(template: str) -> str:
    """A record link template: HTTPS with one ``{record_id}``, or "" when none is configured."""
    if template and (template.count(RECORD_PLACEHOLDER) != 1
                     or not safe_external_url(template.replace(RECORD_PLACEHOLDER, "rec0"))):
        raise ValueError(f"record URL must be an HTTPS link containing {RECORD_PLACEHOLDER} once")
    return template


def record_link(template: str, record_id: object) -> str:
    if not template or not isinstance(record_id, str) or not _RECORD_ID.fullmatch(record_id):
        return ""
    return safe_external_url(template.replace(RECORD_PLACEHOLDER, record_id))


def _links(*pairs: tuple[str, str]) -> list[dict]:
    elements: list[dict] = []
    for label, href in pairs:
        if href:
            elements += [_text(" · ")] if elements else [_text("  ")]
            elements.append({"tag": "a", "text": label, "href": href})
    return elements


def group_of(item: dict, today: str) -> str:
    """``reviewed`` or the pending group of a digest item on ``today``."""
    if item["review"]["status"] == "reviewed":
        return "reviewed"
    due = item["decision"]["due_on"]
    soon = (dt.date.fromisoformat(today) + dt.timedelta(days=DUE_SOON_DAYS)).isoformat()
    if due and due < today:
        return "overdue"
    return "due_soon" if due and due <= soon else "pending"


def _item(item: dict, record_url: str) -> list[list[dict]]:
    decision = item["decision"]
    lines = [
        [_text("• "), _text(f"[{_plain(item['market'])}] {_plain(item['title'])}", bold=True)],
        [_text(f"  需要决策：{_plain(decision['question'])}")],
        [_text(f"  决策人：{_plain(decision['owner']) or '待指派'} · 截止：{decision['due_on'] or '未设定'} · "
               f"{STATUS_LABELS.get(item['verification'], '来源状态未知')}")],
    ]
    links = _links(("去填写判断", record_link(record_url, item.get("record_id"))),
                   ("查看详情", safe_external_url(item.get("url"))))
    return lines + ([links] if links else [])


def _section(title: str, count: int) -> list[dict]:
    return [_text(f"【{title}（{count}）】", bold=True)]


def _pending(digest: dict, today: str, record_url: str) -> list[list[dict]]:
    grouped: dict[str, list[dict]] = {key: [] for key, _ in GROUPS}
    for item in digest["items"]:
        group = group_of(item, today)
        if group != "reviewed":
            grouped[group].append(item)
    lines: list[list[dict]] = []
    listed = 0
    for key, title in GROUPS:
        shown = grouped[key][:max(MAX_LISTED - listed, 0)]
        if grouped[key]:
            lines.append(_section(title, len(grouped[key])))
            lines += [line for item in shown for line in _item(item, record_url)]
        if len(shown) < len(grouped[key]):
            lines.append([_text(f"  另有 {len(grouped[key]) - len(shown)} 条未列出，见完整列表")])
        listed += len(shown)
    return lines


def _sync_lines(digest: dict, report: dict, record_url: str) -> list[list[dict]]:
    reviews = {item["event_id"]: item["review"] for item in digest["items"]}
    lines: list[list[dict]] = []
    changed = [note for key in ("added", "revised", "judged") for note in report.get(key, [])]
    judged = [note for note in changed if reviews.get(note["event_id"], {}).get("status") == "reviewed"]
    if judged:
        lines.append(_section("本次同步录入的人工判断", len(judged)))
        for note in judged[:MAX_LISTED]:
            review = reviews[note["event_id"]]
            lines.append([_text(f"• {_plain(note['title'])}：{_plain(review['decision'])}"
                                f"（{_plain(review['reviewed_by'])}，{review['reviewed_on']}）")])
    fixes = [*report.get("problems", []), *report.get("notices", []),
             *({**note, "record_id": None} for note in report.get("gone", []))]
    if fixes:
        lines.append(_section("需处理的表格行", len(fixes)))
        for note in fixes[:MAX_LISTED]:
            title = _plain(note["title"]) or "（未填标题）"
            lines.append([_text(f"• {title}：{_plain(note['message'])}"),
                          *_links(("去修改", record_link(record_url, note.get("record_id"))))])
        if len(fixes) > MAX_LISTED:
            lines.append([_text(f"  另有 {len(fixes) - MAX_LISTED} 行未列出")])
    return lines


def post_content(digest: dict, *, today: str, record_url: str = "", page_url: str = "",
                 report: dict | None = None) -> dict | None:
    """The Feishu post message for ``digest`` on ``today``; ``None`` when nothing needs anyone."""
    pending = sum(group_of(item, today) != "reviewed" for item in digest["items"])
    sync = _sync_lines(digest, report, record_url) if report else []
    if not pending and not sync:
        return None
    overdue = sum(group_of(item, today) == "overdue" for item in digest["items"])
    counts = digest["counts"]
    lines = [[_text(f"待决策 {pending} 条（已逾期 {overdue}）· 已有人工判断 {counts['reviewed']} 条 · "
                    f"共 {counts['events']} 条")]]
    lines += _pending(digest, today, record_url) + sync
    if href := safe_external_url(page_url):
        lines.append([_text("完整列表："), {"tag": "a", "text": "外部情报", "href": href}])
    return {"zh_cn": {"title": f"外部情报待决策 · {today}", "content": lines}}


def preview(content: dict) -> str:
    """The message as plain text, links shown after their label, for a dry run."""
    post = content["zh_cn"]
    lines = [post["title"], ""]
    for line in post["content"]:
        lines.append("".join(element["text"] + (f" <{element['href']}>" if element["tag"] == "a" else "")
                             for element in line))
    return "\n".join(lines)


def idempotency_key(chat_id: str, content: dict, today: str) -> str:
    """One key per chat, content and day (Feishu keeps a key for an hour; at most 50 characters)."""
    body = json.dumps({"chat": chat_id, "content": content}, ensure_ascii=False, sort_keys=True)
    return f"ei-{today.replace('-', '')}-{hashlib.sha256(body.encode('utf-8')).hexdigest()[:16]}"


def send(run, *, chat_id: str, content: dict, key: str) -> dict:
    """Send ``content`` to ``chat_id`` through ``run`` (lark-cli, as the bot); the receipt names no chat."""
    payload = run(["im", "+messages-send", "--chat-id", chat_id, "--msg-type", "post",
                   "--content", json.dumps(content, ensure_ascii=False, sort_keys=True), "--idempotency-key", key,
                   "--format", "json"])
    data = payload.get("data") if isinstance(payload, dict) else None
    message_id = data.get("message_id") if isinstance(data, dict) else None
    return {"status": "sent", "message_id": message_id if isinstance(message_id, str) else None,
            "idempotency_key": key}
