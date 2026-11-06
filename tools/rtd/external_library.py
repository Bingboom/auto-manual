"""Opt-in demo page: a competitor library and an industry library, and how they stay maintained.

Reads ``external-library/library.json`` from the business knowledge snapshot. The
page shows where each piece of content comes from, which department owns it,
what scheduled jobs would gather and remind, and what is overdue as of the
snapshot's own date, so a fixed sample always reads the same. It is a
demonstration: nothing here fetches data or runs a job. A missing snapshot drops
the page; a malformed one raises ValueError naming the item.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlsplit

PAGE = "research/external-library"
TEMPLATE = "external_library.html"
CONTENT_DIR = "external-library"
SNAPSHOT = "library.json"
SCHEMA = "external-library/v1"
DUE_SOON_DAYS = 7
PIPELINE = ("采集", "提取要点", "比对去重", "待审核", "审核入库", "复核与催办")
SOURCE_KINDS = {"public": "公开渠道", "internal": "内部报告", "paid": "付费数据", "tool": "处理工具"}
SOURCE_STATUSES = {"in_use": "在用", "candidate": "候选，未接入"}
LIBRARIES = {"competitor": "竞品资料库", "industry": "行业资料文库", "both": "两个资料库"}
JOB_STATUSES = {"demo": "示例运行", "pending": "待接入"}
END_STATUSES = ("done", "in_progress", "waiting")
DOC_STATUSES = ("pending_review", "reviewed")
# To-do order: what is already late first, then what waits on a reviewer, then what is coming up.
_URGENCY = {"overdue": 0, "stale": 1, "pending": 2, "due-soon": 3}
_ID = re.compile(r"[a-z][a-z0-9-]*")
_RUN_AT = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}")


def _text(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"external library needs text for {where}")
    return value


def _texts(value: Any, where: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"external library needs a list for {where}")
    return [_text(item, where) for item in value]


def _date(value: Any, where: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError(f"external library needs an ISO date for {where}") from None


def _ids(items: Any, where: str) -> dict[str, dict]:
    if not isinstance(items, list) or not items:
        raise ValueError(f"external library needs {where}")
    found: dict[str, dict] = {}
    for item in items:
        key = item.get("id") if isinstance(item, dict) else None
        if not isinstance(key, str) or not _ID.fullmatch(key) or key in found:
            raise ValueError(f"external library {where} need unique lower-case ids")
        found[key] = item
    return found


def _url(value: Any, where: str) -> str:
    if value in (None, ""):
        return ""
    parts = urlsplit(value) if isinstance(value, str) else None
    if parts is None or parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        raise ValueError(f"external library link must be a public HTTPS URL: {where}")
    return value


def _sources(data: dict) -> dict[str, dict]:
    sources = _ids(data.get("sources"), "sources")
    for key, source in sources.items():
        for field in ("name", "gives", "method"):
            _text(source.get(field), f"source {key} {field}")
        if source.get("kind") not in SOURCE_KINDS or source.get("status") not in SOURCE_STATUSES:
            raise ValueError(f"external library source {key} has an unknown kind or status")
        libraries = source.get("libraries")
        if not isinstance(libraries, list) or not libraries or not set(libraries) <= {"competitor", "industry"}:
            raise ValueError(f"external library source {key} needs its libraries")
    return sources


def _finding(finding: Any, sources: dict, where: str) -> dict:
    if not isinstance(finding, dict) or finding.get("source") not in sources:
        raise ValueError(f"external library finding needs a known source: {where}")
    return {"label": _text(finding.get("label"), where), "value": _text(finding.get("value"), where),
            "source_name": sources[finding["source"]]["name"],
            "checked_on": _date(finding.get("checked_on"), where).isoformat()}


def _metric(row: Any, where: str) -> dict:
    counts = [row.get(key) if isinstance(row, dict) else None for key in ("visits", "reviews")]
    rating = row.get("rating") if isinstance(row, dict) else None
    if any(type(count) is not int or count < 0 for count in counts) \
            or not isinstance(rating, (int, float)) or isinstance(rating, bool) or not 0 <= rating <= 5:
        raise ValueError(f"external library metrics need counts and a 0-5 rating: {where}")
    return {"week": _text(row.get("week"), where), "visits": f"{counts[0]:,}", "reviews": counts[1],
            "rating": f"{rating:.1f}"}


def _end_state(end: dict, refresh_days: int, as_of: dt.date, where: str) -> tuple[str, str, str]:
    """``(state, badge, date note)`` of one end as of the snapshot date."""
    status = end["status"]
    if status == "waiting":
        return "waiting", "等样机", ""
    if status == "in_progress":
        due = _date(end.get("due"), where)
        days = (due - as_of).days
        if days < 0:
            return "overdue", f"逾期 {-days} 天", f"期限 {due.isoformat()}"
        state = "due-soon" if days <= DUE_SOON_DAYS else "in-progress"
        return state, "今天到期" if days == 0 else (f"{days} 天后到期" if state == "due-soon" else "进行中"), \
            f"期限 {due.isoformat()}"
    updated = _date(end.get("updated_on"), where)
    late = (as_of - updated).days - refresh_days
    if late > 0:
        return "stale", "需更新", f"{updated.isoformat()} 更新，已超出更新周期 {late} 天"
    return "done", "已入库", f"{updated.isoformat()} 更新"


def _end(end: Any, dimension: dict, sources: dict, as_of: dt.date, where: str) -> dict:
    if not isinstance(end, dict) or end.get("status") not in END_STATUSES:
        raise ValueError(f"external library needs a known status for {where}")
    state, badge, note = _end_state(end, dimension["refresh_days"], as_of, where)
    findings = end.get("findings") or []
    if not isinstance(findings, list):
        raise ValueError(f"external library findings must be a list: {where}")
    return {"id": dimension["id"], "name": dimension["name"], "department": dimension["department_name"],
            "deliverable": dimension["deliverable"], "owner": end.get("owner") or "", "state": state,
            "label": badge, "note": note,
            "findings": [_finding(item, sources, where) for item in findings],
            "metrics": [_metric(row, where) for row in end.get("metrics") or []],
            "empty": "样机到货后开始" if state == "waiting" else "报告未提交"}


def _dimensions(competitor: dict, departments: dict, sources: dict) -> list[dict]:
    dimensions = _ids(competitor.get("dimensions"), "competitor dimensions")
    views = []
    for key, dimension in dimensions.items():
        refresh = dimension.get("refresh_days")
        if dimension.get("department") not in departments or type(refresh) is not int or refresh <= 0:
            raise ValueError(f"external library dimension {key} needs a department and refresh days")
        if not set(_texts(dimension.get("sources"), f"dimension {key}")) <= set(sources):
            raise ValueError(f"external library dimension {key} names an unknown source")
        views.append({"id": key, "name": _text(dimension.get("name"), key), "refresh_days": refresh,
                      "department_name": departments[dimension["department"]],
                      "deliverable": _text(dimension.get("deliverable"), key),
                      "covers": _texts(dimension.get("covers"), key),
                      "source_names": [sources[source]["name"] for source in dimension["sources"]]})
    return views


def _flow(competitor: dict) -> list[dict]:
    flow = competitor.get("flow")
    if not isinstance(flow, list) or not flow:
        raise ValueError("external library needs the sample flow")
    steps = [{"name": _text(step.get("name") if isinstance(step, dict) else None, "flow step"),
              "note": _text(step.get("note"), "flow step note")} for step in flow]
    if len({step["name"] for step in steps}) != len(steps):
        raise ValueError("external library flow steps need unique names")
    return steps


def _oa_text(oa: Any, where: str) -> str:
    if not isinstance(oa, dict) or not oa.get("applied_on"):
        return "尚未发起样机采购"
    applied = _date(oa["applied_on"], where).isoformat()
    if oa.get("arrived_on"):
        return f"OA 采购 {applied} 发起，样机 {_date(oa['arrived_on'], where).isoformat()} 到货"
    return f"OA 采购 {applied} 发起，样机未到货"


def _product(key: str, product: dict, context: dict) -> dict:
    names = [step["name"] for step in context["flow"]]
    if product.get("stage") not in names:
        raise ValueError(f"external library product {key} needs a stage from the flow")
    ends = product.get("ends")
    dimensions = context["dimensions"]
    if not isinstance(ends, dict) or set(ends) != {dimension["id"] for dimension in dimensions}:
        raise ValueError(f"external library product {key} needs one entry for each end")
    at = names.index(product["stage"])
    last = at == len(names) - 1
    steps = [{"name": name, "state": "done" if index < at or last else ("current" if index == at else "todo")}
             for index, name in enumerate(names)]
    return {"id": key, "name": _text(product.get("name"), key), "brand": _text(product.get("brand"), key),
            "segment": _text(product.get("segment"), key), "stage": product["stage"], "steps": steps,
            "oa": _oa_text(product.get("oa"), key),
            "ends": [_end(ends[dimension["id"]], dimension, context["sources"], context["as_of"],
                          f"{key} {dimension['id']}") for dimension in dimensions]}


def _document(key: str, document: dict, kinds: dict, sources: dict, as_of: dt.date) -> dict:
    if document.get("kind") not in kinds or document.get("source") not in sources \
            or document.get("status") not in DOC_STATUSES:
        raise ValueError(f"external library document {key} needs a known kind, source and status")
    published = document.get("published_on")
    view = {"id": key, "kind": document["kind"], "title": _text(document.get("title"), key),
            "region": _text(document.get("region"), key), "publisher": _text(document.get("publisher"), key),
            "published_on": _date(published, key).isoformat() if published else "",
            "points": _texts(document.get("points"), key), "owner": _text(document.get("owner"), key),
            "source_name": sources[document["source"]]["name"], "url": _url(document.get("url"), key),
            "review_by": ""}
    if document["status"] == "pending_review":
        return {**view, "state": "pending", "label": "待审核"}
    review_by = _date(document.get("review_by"), key)
    late = review_by < as_of
    return {**view, "review_by": review_by.isoformat(), "state": "stale" if late else "done",
            "label": "需复核" if late else "已入库"}


def _industry(industry: Any, departments: dict, sources: dict, as_of: dt.date) -> dict:
    if not isinstance(industry, dict) or industry.get("department") not in departments \
            or not isinstance(industry.get("kinds"), dict) or not industry["kinds"]:
        raise ValueError("external library needs the industry department and document kinds")
    refresh = industry.get("refresh_days")
    if type(refresh) is not int or refresh <= 0:
        raise ValueError("external library needs the industry refresh days")
    kinds = {key: _text(label, f"kind {key}") for key, label in industry["kinds"].items()}
    documents = [_document(key, document, kinds, sources, as_of)
                 for key, document in _ids(industry.get("documents"), "industry documents").items()]
    groups = [{"name": label, "documents": [doc for doc in documents if doc["kind"] == key]} for key, label in kinds.items()]
    return {"department": departments[industry["department"]], "refresh_days": refresh,
            "kinds": list(kinds.values()), "documents": documents,
            "source_names": [source["name"] for source in sources.values()
                             if "industry" in source["libraries"] and source["status"] == "in_use"],
            "groups": [group for group in groups if group["documents"]]}


def _schedule(schedule: Any) -> tuple[list[dict], list[dict]]:
    if not isinstance(schedule, dict):
        raise ValueError("external library needs the schedule")
    jobs = _ids(schedule.get("jobs"), "jobs")
    views = []
    for key, job in jobs.items():
        if job.get("library") not in LIBRARIES or job.get("status") not in JOB_STATUSES:
            raise ValueError(f"external library job {key} needs a known library and status")
        views.append({"id": key, "name": _text(job.get("name"), key), "cadence": _text(job.get("cadence"), key),
                      "notify": _text(job.get("notify"), key), "steps": _texts(job.get("steps"), key),
                      "status": job["status"], "status_label": JOB_STATUSES[job["status"]],
                      "library_label": LIBRARIES[job["library"]]})
    runs = []
    for run in schedule.get("runs") or []:
        if not isinstance(run, dict) or run.get("job") not in jobs or not _RUN_AT.fullmatch(str(run.get("at"))):
            raise ValueError("external library runs need a known job and a 'YYYY-MM-DD HH:MM' time")
        runs.append({"at": run["at"], "job": jobs[run["job"]]["name"], "result": _text(run.get("result"), "run")})
    return views, sorted(runs, key=lambda run: run["at"], reverse=True)


def _source_views(sources: dict, products: list[dict], documents: list[dict]) -> list[dict]:
    counts = dict.fromkeys(sources, 0)
    names = {source["name"]: key for key, source in sources.items()}
    for item in [finding for product in products for end in product["ends"] for finding in end["findings"]] + documents:
        counts[names[item["source_name"]]] += 1
    return [{"id": key, "name": source["name"], "gives": source["gives"], "method": source["method"],
             "kind": SOURCE_KINDS[source["kind"]], "status": source["status"],
             "status_label": SOURCE_STATUSES[source["status"]], "count": counts[key],
             "libraries": "、".join(LIBRARIES[name] for name in source["libraries"])} for key, source in sources.items()]


def _todos(products: list[dict], industry: dict) -> list[dict]:
    todos = [{"state": end["state"], "label": end["label"], "what": f"{product['name']} · {end['deliverable']}",
              "who": f"{end['department']} {end['owner']}".strip(), "note": end["note"]}
             for product in products for end in product["ends"] if end["state"] in _URGENCY]
    todos += [{"state": doc["state"], "label": doc["label"], "what": f"行业资料 · {doc['title']}",
               "who": f"{industry['department']} {doc['owner']}", "note": f"复核日期 {doc['review_by']}" if doc["review_by"] else "新资料等待审核"}
              for doc in industry["documents"] if doc["state"] in _URGENCY]
    return sorted(todos, key=lambda todo: (_URGENCY[todo["state"]], todo["what"]))


def library_context(knowledge_root: Path | None) -> dict | None:
    """The page context, or None without a snapshot; a malformed snapshot raises ValueError."""
    path = knowledge_root / CONTENT_DIR / SNAPSHOT if knowledge_root is not None else None
    if path is None or not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA:
        raise ValueError(f"external library snapshot needs schema_version {SCHEMA}")
    departments = data.get("departments")
    if not isinstance(departments, dict) or not departments:
        raise ValueError("external library needs departments")
    departments = {key: _text(name, f"department {key}") for key, name in departments.items()}
    as_of, sources = _date(data.get("as_of"), "as_of"), _sources(data)
    competitor = data.get("competitor") if isinstance(data.get("competitor"), dict) else {}
    context = {"as_of": as_of, "sources": sources, "flow": _flow(competitor),
               "dimensions": _dimensions(competitor, departments, sources)}
    products = [_product(key, product, context) for key, product in _ids(competitor.get("products"), "products").items()]
    industry = _industry(data.get("industry"), departments, sources, as_of)
    jobs, runs = _schedule(data.get("schedule"))
    todos = _todos(products, industry)
    ends = [end for product in products for end in product["ends"]]
    return {"sample": data.get("sample") is True, "as_of": as_of.isoformat(), "flow": context["flow"],
            "dimensions": context["dimensions"], "competitors": products, "industry": industry,
            "sources": _source_views(sources, products, industry["documents"]), "pipeline": list(PIPELINE),
            "jobs": jobs, "runs": runs, "todos": todos, "rules": _texts(data.get("rules"), "rules"),
            "summary": {"competitors": len(products), "ends_done": sum(end["state"] in ("done", "stale") for end in ends),
                        "ends_total": len(ends), "documents": len(industry["documents"]), "todos": len(todos)}}
