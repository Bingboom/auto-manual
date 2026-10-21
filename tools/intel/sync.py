"""Sync the 外部情报 Feishu table into the external event intake, append-only.

One table row is one external event, in the columns of ``COLUMNS``. Each sync
compares a row with the latest revision of its event in
``external-intel/events.json`` and appends a revision only when the row's facts
or its human judgment changed; earlier revisions are never rewritten. A
judgment (人工判断, 复核人, 复核日期) belongs to the facts it judges, not the
date it was synced. Reusing the same judgment after facts change leaves the
event pending, even on the same day; an explicit judgment edit reconfirms it.

A row that cannot be used keeps its event's last good state and is reported,
and an event whose row disappeared is kept and reported, so rows are fixed in
the table and nothing is deleted by omission. Only a table without the
columns, an incomplete read, an invalid existing intake or a sync dated before
its newest revision stops a sync. Rows never set or clear ``product_lens``; it
stays maintained in the repository.
"""
from __future__ import annotations

from copy import deepcopy
import datetime as dt
import hashlib
import re
from typing import Any

from .digest import safe_external_url
from .events import INTAKE_SCHEMA, content_hash, validated_cases
from .feishu import complete_rows

# Business dates are China Standard Time, which has no daylight saving time.
BUSINESS_TZ = dt.timezone(dt.timedelta(hours=8), "Asia/Shanghai")

ID, TITLE, KIND, MARKET, OCCURRED = "事件ID", "标题", "类型", "市场", "发生日期"
SOURCE_KIND, POLICY_ID, STATUS = "来源类型", "政策记录ID", "来源状态"
SUMMARY, BOUNDARY, SOURCES = "发生了什么", "适用边界", "来源"
QUESTION, OWNER, DUE, HYPOTHESES, UNKNOWNS = "需要决策", "决策人", "截止日期", "可能影响", "待核实"
DECISION, REVIEWER, REVIEWED, REASON = "人工判断", "复核人", "复核日期", "变更说明"
COLUMNS = (ID, TITLE, KIND, MARKET, OCCURRED, SOURCE_KIND, POLICY_ID, STATUS, SUMMARY, BOUNDARY, SOURCES,
           QUESTION, OWNER, DUE, HYPOTHESES, UNKNOWNS, DECISION, REVIEWER, REVIEWED, REASON)

# Option names the field spec lists, and the codes they mean; ``_ALIASES`` maps other accepted spellings.
KINDS = {"政策": "policy", "市场": "market", "竞品": "competitor"}
SOURCE_KINDS = {"外部事件": "external_event", "市场政策记录": "market_policy"}
STATUSES = {"已核实": "verified", "未核实": "unverified", "需求": "demand"}
SOURCE_TYPES = {"官方": "official", "二手": "brief"}
_ALIASES = {"政策变化": "政策", "市场变化": "市场", "竞品动态": "竞品", "事件要点已核实": "已核实",
            "待核实": "未核实", "待核实线索": "未核实", "业务需求": "需求", "业务需求依据": "需求",
            "官方来源": "官方", "二手资料": "二手", "媒体": "二手"}
SOURCE_LINE = "类型 | 标题 | 链接 | 说明 | 核实日期 [| 发布日期]"

_EVENT_ID = re.compile(r"[a-z][a-z0-9-]*")
_WRITTEN_DATE = re.compile(r"(\d{4})\s*[-/.年]\s*(\d{1,2})\s*[-/.月]\s*(\d{1,2})")
_FACTS = ("decision_question", "decision_owner", "decide_by", "hypotheses", "unknowns")
_EXTERNAL_FACTS = ("status", "summary", "boundary", "sources")
_STATED = (STATUS, SUMMARY, BOUNDARY, SOURCES)


def business_today() -> str:
    return dt.datetime.now(BUSINESS_TZ).date().isoformat()


def derived_id(record_id: str) -> str:
    """The event id of a row whose 事件ID is blank: stable for the row, unique in practice."""
    return "ev-" + hashlib.sha256(record_id.encode("utf-8")).hexdigest()[:10]


# --- cells ------------------------------------------------------------------------------


def cell_text(value: Any) -> str:
    """A cell as text: rich-text segments concatenate, options and people join with 、, links give URLs."""
    if value is None or isinstance(value, bool):
        return ""
    if isinstance(value, list):
        if value and all(isinstance(item, dict) and "text" in item for item in value):
            return "".join(str(item.get("link") or item.get("text") or "") for item in value)
        return "、".join(text for text in (cell_text(item) for item in value) if text)
    if isinstance(value, dict):
        return str(value.get("link") or value.get("text") or value.get("name") or "") or cell_text(value.get("value"))
    return str(value)


def _line(value: Any) -> str:
    return " ".join(cell_text(value).split())


def _lines(value: Any) -> list[str]:
    return [" ".join(line.split()) for line in cell_text(value).splitlines() if line.strip()]


def _written_date(text: str) -> str | None:
    match = _WRITTEN_DATE.search(text)
    try:
        return dt.date(*map(int, match.groups())).isoformat() if match else None
    except ValueError:
        return None


def _epoch_date(milliseconds: float) -> str:
    try:
        return dt.datetime.fromtimestamp(milliseconds / 1000, BUSINESS_TZ).date().isoformat()
    except (OverflowError, OSError) as exc:
        raise ValueError("date out of range") from exc


def cell_date(value: Any) -> str | None:
    """The ISO date of a date cell: epoch milliseconds read in business time, or a written date.

    An empty cell is ``None``; anything else that is not a date raises ValueError.
    """
    if isinstance(value, list) and len(value) == 1:
        value = value[0]
    if isinstance(value, bool):
        raise ValueError("not a date")
    if isinstance(value, (int, float)):
        return _epoch_date(value)
    text = _line(value)
    if not text:
        return None
    parsed = _epoch_date(int(text)) if text.isdigit() else _written_date(text)
    if parsed is None:
        raise ValueError("not a date")
    return parsed


def _choice(value: Any, options: dict[str, str]) -> str | None:
    text = _line(value)
    text = _ALIASES.get(text, text)
    return options.get(text) or (text if text in options.values() else None)


# --- rows -------------------------------------------------------------------------------


def _date(row: dict, column: str, problems: list[str], *, required: bool = False) -> str | None:
    try:
        value = cell_date(row.get(column))
    except ValueError:
        problems.append(f"{column}不是日期")
        return None
    if value is None and required:
        problems.append(f"缺少{column}")
    return value


def _entry(row: dict, problems: list[str]) -> dict:
    entry = {"title": _line(row.get(TITLE)), "kind": _choice(row.get(KIND), KINDS),
             "market": _line(row.get(MARKET)), "occurred_on": _date(row, OCCURRED, problems, required=True),
             "source_kind": _choice(row.get(SOURCE_KIND), SOURCE_KINDS)}
    problems += [f"缺少{column}" for column, key in ((TITLE, "title"), (MARKET, "market")) if not entry[key]]
    if entry["kind"] is None:
        problems.append(f"{KIND}应为{'、'.join(KINDS)}之一")
    if entry["source_kind"] is None:
        problems.append(f"{SOURCE_KIND}应为{'、'.join(SOURCE_KINDS)}之一")
    policy = _line(row.get(POLICY_ID))
    if entry["source_kind"] == "market_policy":
        entry["source_record_id"] = policy
        if not policy:
            problems.append(f"市场政策记录需要填写{POLICY_ID}")
    elif policy:
        problems.append(f"只有市场政策记录才填写{POLICY_ID}")
    return entry


def _source(line: str, problems: list[str]) -> dict | None:
    parts = [part.strip() for part in re.split(r"[|｜]", line)]
    if len(parts) not in (5, 6) or not all(parts):
        problems.append(f"来源每行写作“{SOURCE_LINE}”：{line[:40]}")
        return None
    kind = _choice(parts[0], SOURCE_TYPES)
    url = safe_external_url(parts[2])
    checked, published = _written_date(parts[4]), _written_date(parts[5]) if len(parts) == 6 else None
    if kind is None or not url or checked is None or (len(parts) == 6 and published is None):
        problems.append(f"来源类型应为{'、'.join(SOURCE_TYPES)}，链接为 HTTPS，日期写作 2026-10-21：{line[:40]}")
        return None
    source = {"kind": kind, "title": parts[1], "url": url}
    if published:
        source["published_on"] = published
    return {**source, "checked_on": checked, "note": parts[3]}


def _external_facts(row: dict, problems: list[str]) -> dict:
    status = _choice(row.get(STATUS), STATUSES)
    if status is None:
        problems.append(f"{STATUS}应为{'、'.join(STATUSES)}之一")
    facts = {"status": status, "summary": _line(row.get(SUMMARY)), "boundary": _line(row.get(BOUNDARY))}
    problems += [f"缺少{column}" for column, key in ((SUMMARY, "summary"), (BOUNDARY, "boundary"))
                 if not facts[key]]
    sources = [source for line in _lines(row.get(SOURCES)) if (source := _source(line, problems))]
    if status == "verified" and not any(source["kind"] == "official" for source in sources):
        problems.append("已核实的事件至少需要一条官方来源")
    return {**facts, "sources": sources}


def _facts(row: dict, source_kind: str | None, problems: list[str]) -> dict:
    facts = {"decision_question": _line(row.get(QUESTION)), "decision_owner": _line(row.get(OWNER)) or None,
             "decide_by": _date(row, DUE, problems), "hypotheses": _lines(row.get(HYPOTHESES)),
             "unknowns": _lines(row.get(UNKNOWNS))}
    if not facts["decision_question"]:
        problems.append(f"缺少{QUESTION}")
    if source_kind == "external_event":
        return {**_external_facts(row, problems), **facts}
    if source_kind == "market_policy" and any(_line(row.get(column)) for column in _STATED):
        problems.append(f"市场政策记录的事实来自政策快照，请清空{'、'.join(_STATED)}")
    return facts


def _judgment(row: dict, problems: list[str]) -> dict | None:
    parts = {"decision": _line(row.get(DECISION)), "reviewed_by": _line(row.get(REVIEWER)),
             "reviewed_on": _date(row, REVIEWED, problems)}
    if not any(parts.values()):
        return None
    if not all(parts.values()):
        problems.append(f"{DECISION}、{REVIEWER}和{REVIEWED}要一起填写")
        return None
    return parts


def read_row(row: dict) -> tuple[dict, list[str]]:
    """A row as intake parts, and why it cannot be used (in Chinese, for the table's owners)."""
    problems: list[str] = []
    entry = _entry(row, problems)
    parts = {"requested_id": _line(row.get(ID)), "entry": entry,
             "facts": _facts(row, entry["source_kind"], problems),
             "judgment": _judgment(row, problems), "reason": _line(row.get(REASON))}
    return parts, problems


class TableShapeError(RuntimeError):
    """The table lacks columns of ``COLUMNS``; the message names them and nothing else."""


def read_table(run, base_token: str, table_id: str) -> list[tuple[str, dict]]:
    """Every non-blank row of the 外部情报 table; a table without the columns stops the sync."""
    header, rows = complete_rows(run, base_token, table_id)
    missing = [column for column in COLUMNS if column not in header]
    if missing:
        raise TableShapeError(f"the 外部情报 table is missing columns: {', '.join(missing)}")
    return [(record_id, row) for record_id, row in rows if any(_line(value) for value in row.values())]


# --- revisions --------------------------------------------------------------------------


def _review(judgment: dict | None, since: str) -> dict:
    if judgment and judgment["reviewed_on"] >= since:
        return {"status": "reviewed", **judgment}
    return {"status": "pending", "decision": None}


def _facts_of(revision: dict, external: bool) -> dict:
    keys = _FACTS + (_EXTERNAL_FACTS if external else ())
    return {key: revision.get(key, [] if key in ("hypotheses", "unknowns") else None) for key in keys}


def _facts_since(case: dict) -> str:
    """Review-only revisions never move the date of the facts being judged."""
    external = case["source_kind"] == "external_event"
    facts, since = None, case["revisions"][0]["recorded_on"]
    for revision in case["revisions"]:
        current = _facts_of(revision, external)
        if current != facts:
            facts, since = current, revision["recorded_on"]
    return since


def _seen_judgment(case: dict) -> str:
    """Recover legacy intake conservatively; new revisions record the exact observed input."""
    latest = case["revisions"][-1]
    if "intake_judgment_sha256" in latest:
        return latest["intake_judgment_sha256"]
    external = case["source_kind"] == "external_event"
    for revision in reversed(case["revisions"]):
        review = revision["review"]
        if review["status"] == "reviewed":
            if latest["review"]["status"] == "reviewed" or _facts_of(revision, external) != _facts_of(latest, external):
                return content_hash({key: review[key] for key in ("decision", "reviewed_by", "reviewed_on")})
            break
    return content_hash(None)


def _revision(number: int, today: str, reason: str, facts: dict, review: dict, judgment: dict | None) -> dict:
    return {"revision": number, "recorded_on": today, "reason": reason, **facts, "review": review,
            "intake_judgment_sha256": content_hash(judgment)}


def _apply(case: dict | None, parts: dict, *, event_id: str, record_id: str, today: str) -> tuple[dict, str]:
    """The case after its row, and what changed: added, revised, judged, reopened, relabelled or unchanged."""
    facts, judgment = parts["facts"], parts["judgment"]
    if case is None:
        review = _review(judgment, today)
        revision = _revision(1, today, parts["reason"] or "从飞书多维表首次录入", facts, review, judgment)
        return {"id": event_id, **parts["entry"], "intake_record_id": record_id, "revisions": [revision]}, "added"
    head = {key: value for key, value in case.items() if key != "revisions"}
    updated = {**head, **parts["entry"], "intake_record_id": record_id, "revisions": deepcopy(case["revisions"])}
    latest = case["revisions"][-1]
    same_judgment = content_hash(judgment) == _seen_judgment(case)
    if _facts_of(latest, case["source_kind"] == "external_event") != facts:
        review = _review(None if same_judgment else judgment, today)
        change = "revised"
    else:
        if same_judgment:
            return updated, "unchanged" if updated == case else "relabelled"
        review = _review(judgment, _facts_since(case))
        change = "judged" if review["status"] == "reviewed" else "reopened"
    reason = parts["reason"] if parts["reason"] and parts["reason"] != latest["reason"] else \
        {"revised": "飞书多维表更新", "judged": "录入人工判断", "reopened": "撤回人工判断"}[change]
    updated["revisions"].append(_revision(len(case["revisions"]) + 1, today, reason, facts, review, judgment))
    return updated, change


def _target(record_id: str, requested: str, by_row: dict, by_id: dict,
            present: set[str]) -> tuple[str, dict | None, str]:
    """``(event id, existing case, problem)`` for one row.

    A row adopts, by its 事件ID, a hand-written event or one whose row is no longer in the table.
    """
    bound = by_row.get(record_id)
    if bound is not None:
        problem = f"{ID}已固定为 {bound['id']}，请恢复或清空" if requested and requested != bound["id"] else ""
        return bound["id"], bound, problem
    if requested and not _EVENT_ID.fullmatch(requested):
        return requested, None, f"{ID}只用小写字母、数字和连字符，并以字母开头"
    event_id = requested or derived_id(record_id)
    existing = by_id.get(event_id)
    if existing is not None and existing.get("intake_record_id") in present:
        return event_id, None, f"{ID} {event_id} 已属于另一行"
    return event_id, existing, ""


def _immutable(case: dict | None, entry: dict) -> str:
    if case is None or (case["source_kind"], case.get("source_record_id")) == \
            (entry["source_kind"], entry.get("source_record_id")):
        return ""
    return f"已录入事件不能修改{SOURCE_KIND}或{POLICY_ID}；如需改变，请新建一行"


def _validation_problem(case: dict) -> str:
    try:
        validated_cases({"schema_version": INTAKE_SCHEMA, "events": [case]})
    except ValueError as exc:
        return f"未通过事件校验：{exc}"
    return ""


def _row_result(record_id: str, row: dict, target: tuple, *, duplicate: bool, today: str):
    """``(case or None, change, title, problems, parts)`` for one row."""
    event_id, case, problem = target
    parts, problems = read_row(row)
    problems += [text for text in (problem, _immutable(case, parts["entry"])) if text]
    if duplicate:
        problems.append(f"{ID} {event_id} 在表中重复")
    title = parts["entry"]["title"] or (case or {}).get("title", "")
    if problems:
        return None, "", title, problems, parts
    result, change = _apply(case, parts, event_id=event_id, record_id=record_id, today=today)
    failure = _validation_problem(result)
    return (None, "", title, [failure], parts) if failure else (result, change, title, [], parts)


def _notices(case: dict, parts: dict, policy_ids: set[str] | None) -> list[str]:
    """What a used row still needs: a judgment older than the revision it should judge, an unknown policy."""
    notices = []
    latest = case["revisions"][-1]
    if parts["judgment"] and latest["review"]["status"] == "pending":
        since = _facts_since(case)
        if parts["judgment"]["reviewed_on"] < since:
            notices.append(f"{DECISION}早于修订日期 {since}，未计入；仍然适用请把{REVIEWED}改为 {since} 或之后")
        else:
            notices.append(f"事实已变化，原{DECISION}未重新确认；请更新判断内容或复核日期后再同步")
    policy = parts["entry"].get("source_record_id")
    if policy and policy_ids is not None and policy not in policy_ids:
        notices.append(f"{POLICY_ID} {policy} 不在市场政策快照中，页面会显示来源资料缺失")
    return notices


def _note(record_id: str, event_id: str, title: str, message: str = "") -> dict:
    return {"record_id": record_id, "event_id": event_id, "title": title, "message": message}


def _targets(rows: list[tuple[str, dict]], by_row: dict, by_id: dict) -> tuple[set[str], dict, dict[str, int]]:
    """The rows' record ids, each row's target and how many usable rows claim each event id."""
    present = {record_id for record_id, _ in rows}
    targets = {record_id: _target(record_id, _line(row.get(ID)), by_row, by_id, present) for record_id, row in rows}
    counts: dict[str, int] = {}
    for event_id, _, problem in targets.values():
        counts[event_id] = counts.get(event_id, 0) + (not problem)
    return present, targets, counts


def _gone(by_row: dict, present: set[str], updated: dict) -> list[dict]:
    """Events kept although their row left the table and no other row took them."""
    return [_note(record_id, case["id"], case["title"], "多维表中已找不到这一行，事件按上次状态保留")
            for record_id, case in by_row.items() if record_id not in present and case["id"] not in updated]


CHANGES = ("added", "revised", "judged", "reopened", "relabelled")


def merge(previous: dict | None, rows: list[tuple[str, dict]], *, today: str,
          policy_ids: set[str] | None = None) -> tuple[dict, dict]:
    """``(intake document, report)`` after applying table ``rows`` to the ``previous`` intake.

    The report lists each row's change (``CHANGES``), the rows not used (``problems``), what
    used rows still need (``notices``) and the events kept although their row is gone
    (``gone``); ``unchanged`` counts the rest. Raises ValueError for an invalid ``previous``
    intake or a ``today`` before its newest revision.
    """
    cases = deepcopy(validated_cases(previous)) if previous else []
    if any(revision["recorded_on"] > today for case in cases for revision in case["revisions"]):
        raise ValueError("sync date precedes the newest recorded revision")
    by_row = {case["intake_record_id"]: case for case in cases if "intake_record_id" in case}
    by_id = {case["id"]: case for case in cases}
    present, targets, counts = _targets(rows, by_row, by_id)
    report: dict[str, Any] = {key: [] for key in (*CHANGES, "problems", "notices")}
    report["unchanged"] = 0
    updated: dict[str, dict] = {}
    added: list[dict] = []
    for record_id, row in rows:
        event_id, case, _ = targets[record_id]
        result, change, title, problems, parts = _row_result(
            record_id, row, targets[record_id], duplicate=counts[event_id] > 1, today=today)
        if result is None:
            report["problems"].append(_note(record_id, event_id, title, "；".join(problems)))
            continue
        if case is None:
            added.append(result)
        else:
            updated[case["id"]] = result
        if change == "unchanged":
            report["unchanged"] += 1
        else:
            report[change].append(_note(record_id, event_id, title))
        report["notices"] += [_note(record_id, event_id, title, text) for text in _notices(result, parts, policy_ids)]
    report["gone"] = _gone(by_row, present, updated)
    document = {"schema_version": INTAKE_SCHEMA, "events": [updated.get(case["id"], case) for case in cases] + added}
    validated_cases(document)
    return document, report
