"""A Markdown view of the intake that Obsidian and llm_wiki can open.

The view follows the LLM Wiki layout (a project root holding ``purpose.md`` and
``schema.md``, and a ``wiki/`` folder with ``index.md``, ``overview.md``, an
append-only ``log.md`` and one page per entity) but none of its code. Every page
under ``wiki/`` is rebuilt from the snapshot, so edits there are overwritten:
facts change in the table, not in the view. ``purpose.md`` and ``schema.md`` are
written by people and only created from a template when missing.

Pages carry no build date, so an unchanged intake regenerates byte for byte and
``plan`` can tell a stale view. Links are ``[[file name|title]]`` because
llm_wiki resolves links by file name, so every page name is unique; frontmatter
values are JSON, which is valid YAML. Intake text is escaped so table input
cannot add links, tags, embeds or math, and only validated HTTPS URLs become
links. Product data never appears in the view.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from .digest import KIND_LABELS, STATUS_LABELS, decision_order, safe_external_url
from .files import write_atomic

WIKI_DIR = "wiki"
EVENT_DIR, MARKET_DIR = "events", "markets"
AGGREGATES = ("index", "overview", "log")
TEMPLATE_NAMES = ("purpose", "schema")
_MARKUP = re.compile(r"([\\`*_\[\]<>|~$%=#])")
_BULLET_START = re.compile(r"^([-+])(\s)")
_NUMBER_START = re.compile(r"^(\d+)([.)])(\s)")
_SOURCE_KINDS = {"official": "官方来源", "brief": "二手资料"}
# A link title shows as plain text, so markup characters become full-width look-alikes.
_ALIAS = str.maketrans("\\`*_[]<>|~$%=#", "＼｀＊＿［］＜＞｜～＄％＝＃")
_SLUG = re.compile(r"[^0-9a-z\u3400-\u9fff]+")
_STATE = {"pending": "待决策", "reviewed": "已人工判断"}


def _inline(value: object) -> str:
    """One line of literal text: no markup, links, tags, math or comments from the intake."""
    text = _MARKUP.sub(r"\\\1", " ".join(str(value or "").split()))
    return _NUMBER_START.sub(r"\1\\\2\3", _BULLET_START.sub(r"\\\1\2", text))


def _link(name: str, title: object) -> str:
    return f"[[{name}|{' '.join(str(title or name).split()).translate(_ALIAS)}]]"


def _frontmatter(fields: dict) -> list[str]:
    return ["---", *(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in fields.items()), "---", ""]


def market_page(market: str) -> str:
    """The page name of a market; markets that differ only in case or punctuation share it."""
    slug = _SLUG.sub("-", market.strip().lower()).strip("-")
    return "market-" + (slug or hashlib.sha256(market.encode("utf-8")).hexdigest()[:8])


def _due(decision: dict) -> str:
    return decision["due_on"] or "未设定"


def _owner(decision: dict) -> str:
    return _inline(decision["owner"]) if decision["owner"] else "待指派"


def _source(source: dict) -> str:
    title, url = _inline(source.get("title") or "来源"), safe_external_url(source.get("url"))
    kind = source.get("kind")
    facts = [label for label in (_SOURCE_KINDS.get(kind) or _inline(kind),
                                 f"核实 {_inline(source['checked_on'])}" if source.get("checked_on") else "",
                                 f"发布 {_inline(source['published_on'])}" if source.get("published_on") else "")
             if label]
    text = f"[{title}](<{url}>)" if url else f"{title}（链接不可用）"
    note = f" — {_inline(source['note'])}" if source.get("note") else ""
    return f"- {text}" + (f"（{' · '.join(facts)}）" if facts else "") + note


def _bullets(title: str, items: list) -> list[str]:
    return ["", f"## {title}", "", *(f"- {_inline(item)}" for item in items)] if items else []


def _judgment(review: dict) -> list[str]:
    if review["status"] != "reviewed":
        return ["", "## 人工判断", "", "待人工判断。"]
    return ["", "## 人工判断", "", f"> {_inline(review['decision'])}", ">",
            f"> — {_inline(review['reviewed_by'])}，{_inline(review['reviewed_on'])}"]


def _revisions(event: dict) -> list[str]:
    rows = [f"| {row['revision']} | {row['recorded_on']} | {_inline(row['reason'])} | "
            f"{_STATE.get(row['review_status'], row['review_status'])} |" for row in event["history"]]
    return ["", "## 修订记录", "", "| 修订 | 记录日 | 原因 | 判断 |", "| --- | --- | --- | --- |", *rows]


def _event_page(event: dict, market: str) -> str:
    decision, review = event["decision"], event["review"]
    sources = [url for url in (safe_external_url(source.get("url")) for source in event["sources"]) if url]
    fields = {"type": "event", "id": event["id"], "title": event["title"], "kind": event["kind"],
              "market": event["market"], "verification": event["status"], "decision_state": review["status"],
              "owner": decision["owner"], "due_on": decision["due_on"], "occurred_on": event["occurred_on"],
              "created": event["history"][0]["recorded_on"], "updated": event["recorded_on"],
              "revision": event["revision"], "record_id": event.get("intake_record_id"),
              "policy_record": event.get("source_record_id"), "tags": ["external-intel", event["kind"]],
              "related": [market], "sources": sources}
    meta = [KIND_LABELS.get(event["kind"], "外部事件"), _link(market, event["market"]),
            STATUS_LABELS.get(event["status"], "来源状态未知"), f"发生／生效 {event['occurred_on']}"]
    lines = [*_frontmatter(fields), f"# {_inline(event['title'])}", "", " · ".join(meta),
             "", "## 需要决策", "", _inline(decision["question"]), "",
             f"- 决策人：{_owner(decision)}", f"- 截止：{_due(decision)}", f"- 状态：{_STATE[review['status']]}",
             "", "## 发生了什么", "", _inline(event["summary"])]
    if event.get("boundary"):
        lines += ["", "## 适用边界", "", _inline(event["boundary"])]
    lines += ["", "## 来源", "", *([_source(source) for source in event["sources"]] or ["- 尚未提供"])]
    lines += _bullets("可能影响（未证实）", event["hypotheses"]) + _bullets("待核实", event["unknowns"])
    return "\n".join(lines + _judgment(review) + _revisions(event)) + "\n"


def _entry(event: dict) -> str:
    """One catalog line: the event, its market and what is asked of whom by when."""
    decision, review = event["decision"], event["review"]
    if review["status"] == "reviewed":
        state = f"判断：{_inline(review['decision'])}（{_inline(review['reviewed_by'])}，{review['reviewed_on']}）"
    else:
        state = f"截止 {_due(decision)} · 决策人 {_owner(decision)}"
    return f"- {_link(event['id'], event['title'])} — {_inline(event['market'])} · " \
           f"{KIND_LABELS.get(event['kind'], '外部事件')} · {state}"


def _market_page(name: str, markets: list[str], events: list[dict]) -> str:
    pending = [event for event in events if event["review"]["status"] != "reviewed"]
    judged = [event for event in events if event["review"]["status"] == "reviewed"]
    title = " / ".join(markets)
    fields = {"type": "market", "title": title, "markets": markets, "events": len(events),
              "pending": len(pending), "related": [event["id"] for event in events]}
    lines = [*_frontmatter(fields), f"# 市场 · {_inline(title)}"]
    for heading, group in (("待决策", pending), ("已人工判断", judged)):
        if group:
            lines += ["", f"## {heading}（{len(group)}）", "", *(_entry(event) for event in group)]
    timeline = sorted(((row["recorded_on"], event, row) for event in events for row in event["history"]),
                      key=lambda item: (item[0], item[1]["id"], item[2]["revision"]), reverse=True)
    lines += ["", "## 修订时间线", "", *(f"- {day} · {_link(event['id'], event['title'])} 修订 {row['revision']}："
                                       f"{_inline(row['reason'])}" for day, event, row in timeline)]
    return "\n".join(lines) + "\n"


def _markets(events: list[dict]) -> dict[str, tuple[list[str], list[dict]]]:
    grouped: dict[str, tuple[list[str], list[dict]]] = {}
    for event in decision_order(events):
        names, members = grouped.setdefault(market_page(event["market"]), ([], []))
        if event["market"] not in names:
            names.append(event["market"])
        members.append(event)
    return {name: (sorted(names), members) for name, (names, members) in sorted(grouped.items())}


def _counts(events: list[dict]) -> tuple[int, int]:
    pending = sum(event["review"]["status"] != "reviewed" for event in events)
    return pending, len(events) - pending


def _index(events: list[dict], markets: dict) -> str:
    lines = [*_frontmatter({"type": "index", "title": "外部情报索引", "events": len(events)}),
             "# 外部情报索引", "",
             "由 `python -m tools.intel wiki` 从 `events.json` 生成，请勿手改：下次生成会覆盖。"
             f"目的与范围见 {_link('purpose', '目的与范围')}，页面约定见 {_link('schema', '页面约定')}。"]
    for kind, label in KIND_LABELS.items():
        group = sorted((event for event in events if event["kind"] == kind),
                       key=lambda event: (event["market"], event["occurred_on"], event["id"]))
        if group:
            lines += ["", f"## {label}（{len(group)}）", "", *(_entry(event) for event in group)]
    lines += ["", f"## 市场（{len(markets)}）", ""]
    lines += [f"- {_link(name, ' / '.join(names))} — {len(members)} 个事件" for name, (names, members) in markets.items()]
    lines += ["", "## 其他页面", "", f"- {_link('overview', '概览')} · {_link('log', '更新日志')}"]
    return "\n".join(lines) + "\n"


def _overview(intel: dict, events: list[dict], markets: dict) -> str:
    pending, reviewed = _counts(events)
    latest = max((event["recorded_on"] for event in events), default=None)
    source = (intel.get("source") or {}).get("sha256")
    fields = {"type": "overview", "title": "外部情报概览", "events": len(events), "pending": pending,
              "reviewed": reviewed, "updated": latest, "source_sha256": source}
    lines = [*_frontmatter(fields), "# 外部情报概览", "",
             f"共 {len(events)} 个事件 · 待决策 {pending} · 已人工判断 {reviewed} · 最近修订 {latest or '无'} · "
             f"{_link('index', '索引')} · {_link('log', '更新日志')} · {_link('purpose', '目的与范围')}"]
    open_events = [event for event in decision_order(events) if event["review"]["status"] != "reviewed"]
    if open_events:
        lines += ["", "## 待决策", ""]
        for event in open_events:
            lines += [_entry(event), f"  - 需要决策：{_inline(event['decision']['question'])}"]
    judged = sorted((event for event in events if event["review"]["status"] == "reviewed"),
                    key=lambda event: (event["review"]["reviewed_on"], event["id"]), reverse=True)
    if judged:
        lines += ["", "## 人工判断", "", *(_entry(event) for event in judged)]
    if markets:
        lines += ["", "## 市场", ""]
        lines += [f"- {_link(name, ' / '.join(names))}：{len(members)} 个事件，待决策 {_counts(members)[0]}"
                  for name, (names, members) in markets.items()]
    return "\n".join(lines) + "\n"


def _log(events: list[dict]) -> str:
    entries = sorted(((row, event) for event in events for row in event["history"]),
                     key=lambda item: (item[0]["recorded_on"], item[1]["id"], item[0]["revision"]), reverse=True)
    lines = [*_frontmatter({"type": "log", "title": "外部情报更新日志"}), "# 外部情报更新日志", "",
             "按记录日倒序，每条修订一项；`grep \"^## \\[\" log.md` 可列出全部条目。"]
    for row, event in entries:
        action = "录入" if row["revision"] == 1 else "修订"
        lines += ["", f"## [{row['recorded_on']}] {action} | {_inline(event['title'])} · r{row['revision']}",
                  f"{_inline(row['reason'])} · {_STATE.get(row['review_status'], row['review_status'])} · "
                  f"{_link(event['id'], '详情')}"]
    return "\n".join(lines) + "\n"


def _check_names(events: list[dict], markets: dict) -> None:
    names = [event["id"] for event in events] + list(markets) + list(AGGREGATES) + list(TEMPLATE_NAMES)
    if repeated := sorted({name for name in names if names.count(name) > 1}):
        raise ValueError(f"wiki page names collide: {', '.join(repeated)}; rename the event")


def wiki_pages(intel: dict) -> dict[str, str]:
    """``{path under the external-intel folder: Markdown}`` for every generated page."""
    events = sorted(intel["events"], key=lambda event: event["id"])
    markets = _markets(events)
    _check_names(events, markets)
    market_of = {event["id"]: name for name, (_, members) in markets.items() for event in members}
    pages = {f"{WIKI_DIR}/index.md": _index(events, markets),
             f"{WIKI_DIR}/overview.md": _overview(intel, events, markets), f"{WIKI_DIR}/log.md": _log(events)}
    pages.update({f"{WIKI_DIR}/{EVENT_DIR}/{event['id']}.md": _event_page(event, market_of[event["id"]])
                  for event in events})
    pages.update({f"{WIKI_DIR}/{MARKET_DIR}/{name}.md": _market_page(name, names, members)
                  for name, (names, members) in markets.items()})
    return pages


PURPOSE = """---
type: "purpose"
title: "外部情报的目的与范围"
---
# 外部情报的目的与范围

由团队维护。写清为什么收集外部情报、要回答哪些问题、关注哪些市场与竞品、谁来决定。
视图生成只在缺少本文件时创建这份模板，不会覆盖；Obsidian、llm_wiki 和 AI 助手读它来理解这个知识库。

## 目标

-

## 关键问题

-

## 范围

- 市场：
- 竞品：
- 不收集：

## 决策人与节奏

-
"""

SCHEMA = """---
type: "schema"
title: "外部情报页面约定"
---
# 外部情报页面约定

`wiki/` 下的页面由 `python -m tools.intel wiki` 从 `events.json` 生成，不要手改：
事实在飞书「外部情报」表里修改，同步后重新生成。本文件和 `purpose.md` 由人维护。

| 类型 | 位置 | 内容 |
| --- | --- | --- |
| event | `wiki/events/<事件ID>.md` | 一个外部事件：需要的决策、发生了什么、来源、人工判断和修订记录 |
| market | `wiki/markets/market-<市场>.md` | 一个市场的事件，待决策在前 |
| index | `wiki/index.md` | 按类型列出全部事件和市场 |
| overview | `wiki/overview.md` | 待决策、最近的人工判断和各市场数量 |
| log | `wiki/log.md` | 每条修订一项，按记录日倒序 |

- 链接写作 `[[文件名|标题]]`，文件名在整个视图内唯一。
- frontmatter 的值是 JSON 写法：事件页有 `kind`、`market`、`verification`、`decision_state`、
  `owner`、`due_on`、`related`（所属市场页）和 `sources`（来源链接）。
- 视图只含外部事件，不含产品数据；产品关联只在研究页面的附录里。
"""


def templates() -> dict[str, str]:
    """The human-owned files, created only when missing."""
    return {"purpose.md": PURPOSE, "schema.md": SCHEMA}


def _managed(root: Path) -> set[str]:
    return {path.relative_to(root).as_posix() for folder in (EVENT_DIR, MARKET_DIR)
            for path in (root / WIKI_DIR / folder).glob("*.md")}


def plan(root: Path, pages: dict[str, str]) -> dict[str, list[str]]:
    """What a write would change under ``root`` (the external-intel folder)."""
    changed = sorted(path for path, text in pages.items()
                     if not (root / path).is_file() or (root / path).read_bytes() != text.encode("utf-8"))
    stale = sorted(_managed(root) - set(pages))
    missing = sorted(name for name in templates() if not (root / name).exists())
    return {"write": changed, "delete": stale, "templates": missing}


def apply(root: Path, pages: dict[str, str], changes: dict[str, list[str]]) -> None:
    """Write the changed pages, remove stale ones and create missing templates; nothing else is touched."""
    for path in changes["write"]:
        write_atomic(root / path, pages[path].encode("utf-8"))
    for path in changes["delete"]:
        (root / path).unlink()
    for name in changes["templates"]:
        write_atomic(root / name, templates()[name].encode("utf-8"))
