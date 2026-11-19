"""Stage the matrix base's rows from an extraction, and load them with read-back.

``stage_rows`` turns an extraction (``extract.py``) into the rows the 产品, 属性, 来源 and 事实 tables would hold:
products and sources from the selected editions, the dictionary as 属性, and every value as one 事实 row marked 候选.
``load`` compares the staged keys with the live tables, creates only the rows whose key is absent (an existing row is
never changed: a fact that changes is a new row under a new source key), and reads every written row back.

The tool writes no verification state other than 候选 and leaves 当前值, 冲突, 生效起 and every field people own empty.
"""
from __future__ import annotations

import json
import re
from collections import Counter
import subprocess
import time
from collections.abc import Callable, Iterable
from datetime import datetime, timezone, timedelta
from typing import Any

TABLES = ("产品", "属性", "来源", "事实")
PRIMARY = {"产品": "产品键", "属性": "属性键", "来源": "来源键", "事实": "事实键", "矩阵": "产品键"}
BATCH = 100  # the CLI accepts at most 200 rows per batch-create; stay well inside it
CANDIDATE = "候选"
BRAND = ["未知"]
NO_CONDITION = "-"
CST = timezone(timedelta(hours=8))
SOURCE_TYPE = "网页说明书"
UNKNOWN_DATE_BASIS = "未知"
VALUE_TYPES = {"number": "数值", "integer": "整数", "boolean": "布尔", "text": "文本", "range": "范围"}


class LoadError(RuntimeError):
    """The live base cannot take the staged rows as they are."""


class PartialWrite(LoadError):
    """A write stopped partway; ``report`` holds the read-back of what reached the base."""

    def __init__(self, message: str, report: dict[str, Any]):
        super().__init__(message)
        self.report = report


def product_key(model: str, market: str) -> str:
    return f"{model}/{market}"


def fact_key(product: str, attribute: str, condition: str, source: str) -> str:
    return f"{product}|{attribute}|{condition or NO_CONDITION}|{source}"


def _stamp(moment: datetime) -> str:
    return moment.astimezone(CST).strftime("%Y-%m-%d %H:%M:%S")


# --- the live base ----------------------------------------------------------------------------------------------

Runner = Callable[[list[str]], dict[str, Any]]


def lark_runner(base_token: str, *, profile: str | None = None, identity: str = "bot",
                lark_cli: str = "lark-cli") -> Runner:
    """Run one ``lark-cli base`` subcommand against the base and return its JSON."""
    def run(args: list[str]) -> dict[str, Any]:
        command = [lark_cli, *(["--profile", profile] if profile else []), "base", *args,
                   "--as", identity, "--base-token", base_token, "--format", "json"]
        done = subprocess.run(command, capture_output=True, text=True, check=False)
        for text in (done.stdout, done.stdout + done.stderr):
            if "{" in text:
                try:
                    return json.loads(text[text.index("{"):])
                except ValueError:
                    continue
        # Never echo raw output: a failed read can print row data (project numbers included).
        return {"ok": False, "error": {"code": f"exit {done.returncode}",
                                       "message": f"lark-cli gave no JSON (exit {done.returncode})"}}
    return run


def _check(result: dict[str, Any], what: str, *, sensitive: bool = False) -> dict[str, Any]:
    """The call's data, or a LoadError. ``sensitive``: the payload carries a project number, so the CLI's own error
    text (which can echo the payload) is replaced by its error code or type."""
    if not result.get("ok"):
        error = result.get("error") or {}
        if sensitive:
            code = error.get("code") or error.get("type") or error.get("subtype") or "unknown"
            raise LoadError(f"{what} failed (lark-cli error {code}; details withheld: the payload carries project data)")
        raise LoadError(f"{what} failed: {error.get('message') or 'no detail'}")
    return result.get("data") or {}


def table_ids(run: Runner) -> dict[str, str]:
    data = _check(run(["+table-list"]), "table list")
    return {t["name"]: t.get("id") or t.get("table_id") for t in data.get("tables") or data.get("items") or []}


def fields(run: Runner, table_id: str, *, sensitive: bool = False) -> dict[str, dict[str, Any]]:
    data = _check(run(["+field-list", "--table-id", table_id, "--limit", "200"]), "field list", sensitive=sensitive)
    return {f["name"]: f for f in data.get("fields") or data.get("items") or []}


FIELDS_PER_READ = 50  # the CLI projects at most 50 fields per record list


def read_rows(run: Runner, table_id: str, names: list[str], *, sensitive: bool = False) -> list[dict[str, Any]]:
    """Every row of a table with the named fields, read 50 fields at a time and merged by record id.

    ``sensitive``: the rows carry project numbers, so a failed read reports only the CLI's error code.
    """
    if len(names) <= FIELDS_PER_READ:
        return _read_rows(run, table_id, names, sensitive)
    merged: dict[str, dict[str, Any]] = {}
    for start in range(0, len(names), FIELDS_PER_READ):
        for row in _read_rows(run, table_id, names[start:start + FIELDS_PER_READ], sensitive):
            merged.setdefault(row["_record_id"], {}).update(row)
    return list(merged.values())


def _read_rows(run: Runner, table_id: str, names: list[str], sensitive: bool = False) -> list[dict[str, Any]]:
    """Every row of a table (paged, 200 at a time), as {"_record_id", field: value} for the named fields."""
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    offset = 0
    while True:
        args = ["+record-list", "--table-id", table_id, "--limit", "200", "--offset", str(offset)]
        for name in names:
            args += ["--field-id", name]
        data = _check(run(args), "record list", sensitive=sensitive)
        columns = data.get("fields") or []
        values = data.get("data") or []
        ids = data.get("record_id_list") or []
        if ids and ids[0] in seen:  # a CLI that ignores the offset would page forever
            raise LoadError("record list repeated a page; the offset is not honoured")
        seen.update(ids)
        for record_id, cells in zip(ids, values, strict=False):
            rows.append({"_record_id": record_id, **dict(zip(columns, cells, strict=False))})
        if len(values) < 200:
            break
        offset += 200
    return rows


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "".join(_text(v) for v in value)
    if isinstance(value, dict):
        return str(value.get("text") or value.get("name") or value.get("value") or "")
    return str(value)


def _instant(value: Any) -> int | None:
    """A datetime cell as whole seconds since the epoch: written as Beijing-time text, read back as ISO text or ms."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return int(value // 1000)
    text = _text(value).strip()
    if not text:
        return None
    try:
        moment = datetime.fromisoformat(text.replace(" ", "T", 1) if "T" not in text else text)
    except ValueError:
        return None
    return int((moment if moment.tzinfo else moment.replace(tzinfo=CST)).timestamp())


_MOMENT = re.compile(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})(?:[ T](\d{1,2}):(\d{2})(?::(\d{2}))?)?"
                     r"(?:\.\d+)?\s*(?:\(?(?:GMT|UTC)?([+-]\d{1,2})(?::?(\d{2}))?\)?|(Z))?")


SKU_TIME_FIELD = "SKU 最早创建时间（本市场）"  # 产品 formula: earliest PLM SKU creation in the product's market
# PLM holds SKU creation times from its data load in late 2023: an earlier-or-equal time is only an upper bound for when
# the product existed, never its start (operator, 2026-11-17).
PLM_LOADED_UNTIL = datetime(2023, 12, 31, 23, 59, 59, tzinfo=CST)
SERIAL_LIMIT = 10_000_000  # below this a number is a spreadsheet day serial, above it epoch milliseconds
_SERIAL = re.compile(r"\d{4,6}(?:\.\d+)?")
_SERIAL_EPOCH = datetime(1899, 12, 30, tzinfo=CST)


EARLIEST_PLAUSIBLE = datetime(2015, 1, 1, tzinfo=CST)


def _plausible(seconds: int | None) -> int | None:
    """A product time only between 2015 and tomorrow; anything else (text "2024" read as a 1905 serial, a mistyped
    year) is treated as no value rather than shown."""
    if seconds is None or seconds < EARLIEST_PLAUSIBLE.timestamp() or seconds > time.time() + 86400:
        return None
    return seconds


def _serial(days: float) -> int:
    """A formula's date as a spreadsheet day serial (days since 1899-12-30, Beijing time) to epoch seconds."""
    return round((_SERIAL_EPOCH + timedelta(days=days)).timestamp())


def _moment(match: re.Match[str]) -> int | None:
    """One matched date text as epoch seconds (no offset: Beijing time); None for an impossible date."""
    year, month, day, hour, minute, second, sign_hours, offset_minutes, zulu = match.groups()
    hours = 0 if zulu else (int(sign_hours) if sign_hours else 8)
    sign = -1 if sign_hours and sign_hours.startswith("-") else 1
    zone = timezone(timedelta(hours=hours, minutes=sign * int(offset_minutes or 0)))
    try:
        moment = datetime(int(year), int(month), int(day), int(hour or 0), int(minute or 0), int(second or 0),
                          tzinfo=zone)
    except ValueError:
        return None
    return int(moment.timestamp())


def earliest(value: Any) -> int | None:
    """The earliest moment in a lookup or formula cell, as epoch seconds.

    Such a cell may hold one value or several (a lookup's raw values come back as a list, or as text joined by commas
    like ``2024/07/30 10:00 (GMT+8),2025/...``), each as epoch milliseconds or date text; text without an offset is
    Beijing time. A formula field that yields a date comes back as a day serial such as ``45893.4375``.
    """
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _plausible(_serial(value) if value < SERIAL_LIMIT else int(value // 1000))
    if isinstance(value, str) and _SERIAL.fullmatch(value.strip()):
        return _plausible(_serial(float(value)))
    if isinstance(value, list):
        found = [m for m in (earliest(v) for v in value) if m is not None]
        return min(found) if found else None
    text = value.get("value") if isinstance(value, dict) and "value" in value else _text(value)
    if not isinstance(text, str):
        return earliest(text)
    moments = [m for m in (_plausible(_moment(match)) for match in _MOMENT.finditer(text)) if m is not None]
    return min(moments) if moments else None


def same(want: Any, have: Any, kind: str) -> bool:
    """Whether a read-back cell holds the written value (datetime to the second; select: same option names)."""
    if kind == "datetime":
        return _instant(want) is not None and _instant(want) == _instant(have)
    if kind == "checkbox":
        return bool(want) == bool(have)
    if kind == "number":
        try:
            return abs(float(want) - float(have)) < 1e-9
        except (TypeError, ValueError):
            return False
    if kind == "select" and isinstance(want, list):
        names = [_text(v) for v in (have if isinstance(have, list) else [have])]
        return sorted(want) == sorted(n for n in names if n)
    return _text(want).strip() == _text(have).strip()


def preflight(staged: dict[str, list[dict[str, Any]]], schema: dict[str, dict[str, dict[str, Any]]]) -> list[str]:
    """Problems that would make a write fail or land wrong: unknown fields, select values with no option."""
    problems = []
    for table, rows in staged.items():
        known = schema.get(table)
        if known is None:
            problems.append(f"{table}: table is missing in the base")
            continue
        for row in rows:
            for name, value in row.items():
                field = known.get(name)
                if field is None:
                    problems.append(f"{table}.{name}: field is missing in the base")
                    continue
                if field.get("type") == "select":
                    options = {o.get("name") for o in field.get("options") or []}
                    for item in value if isinstance(value, list) else [value]:
                        if item not in options:
                            problems.append(f"{table}.{name}: no option {item!r}")
    return sorted(set(problems))


WEB_SOURCE = "web"


def provenance(staged: dict[str, list[dict[str, Any]]], live_sources: Iterable[dict[str, Any]],
               targets: Iterable[dict[str, Any]]) -> list[str]:
    """Refusals for staged rows whose values do not trace to a published Web manual.

    Every 事实 must name a 来源键 present in the staged or live 来源 rows; every such 来源 row must be a 网页说明书
    whose key is ``web/<型号>/<市场>/<语言>/<版本>`` of a publication in the publish manifest. Other kinds of source
    (specification sheets, PLM) need a check of their own before they may be loaded.
    """
    published = {f"{WEB_SOURCE}/{t['model']}/{t['region']}/{t['lang']}/{t.get('version') or 'unversioned'}"
                 for t in targets}
    sources = {_text(r.get("来源键")): r for r in live_sources}
    sources.update({row["来源键"]: row for row in staged.get("来源", [])})
    cited = {f.get("来源键") for f in staged.get("事实", [])}
    problems = []
    for key in sorted(({r["来源键"] for r in staged.get("来源", [])} | cited) & set(sources)):
        kind = _text(sources[key].get("来源类型"))
        if kind != SOURCE_TYPE:
            problems.append(f"来源 {key}: kind {kind!r} has no provenance check")
        elif key not in published:
            problems.append(f"来源 {key}: not a publication in the publish manifest")
    unknown = sorted(str(key) for key in cited if key not in sources)
    problems += [f"事实 cites 来源 {key}, which is neither staged nor in the base" for key in unknown]
    return problems


def _payload(rows: list[dict[str, Any]], records_shape: bool) -> dict[str, Any]:
    if records_shape:
        return {"create_records": rows}
    names = sorted({name for row in rows for name in row})
    return {"fields": names, "rows": [[row.get(name) for name in names] for row in rows]}


def records_shape(lark_cli: str = "lark-cli") -> bool:
    """Whether this lark-cli takes ``{"create_records": [...]}`` (newer) rather than ``{"fields", "rows"}``."""
    done = subprocess.run([lark_cli, "base", "+record-batch-create", "--help"], capture_output=True, text=True,
                          check=False)
    return "create_records" in done.stdout


EXCLUDE = "不收录"  # a product a person keeps out: its row stays in 产品 so the loader never adds it back


def require_exclude_field(run: Runner, products_table: str) -> None:
    """Stop unless 产品 has the 不收录 field: without it every excluded product would silently come back."""
    if EXCLUDE not in fields(run, products_table, sensitive=True):
        raise LoadError(f"产品 has no {EXCLUDE} field (renamed or deleted?); excluded products would return")


def excluded_products(run: Runner, ids: dict[str, str]) -> set[str]:
    """Product keys marked 不收录 in 产品; a missing 不收录 field stops (LoadError), as for the matrix and snapshot."""
    if "产品" not in ids:
        return set()
    require_exclude_field(run, ids["产品"])
    return {_text(r.get("产品键")) for r in read_rows(run, ids["产品"], ["产品键", EXCLUDE], sensitive=True)
            if r.get(EXCLUDE)}


def _owner(table: str, row: dict[str, Any]) -> str:
    if table == "来源":
        return f"{_text(row.get('型号'))}/{_text(row.get('市场'))}"
    return _text(row.get("产品键"))


def without_excluded(staged: dict[str, list[dict[str, Any]]],
                     excluded: set[str]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, int]]:
    """The staged rows minus every 产品, 来源 and 事实 row of an excluded product, and how many were left out."""
    kept = {table: [row for row in rows if _owner(table, row) not in excluded] for table, rows in staged.items()}
    return kept, {table: len(staged[table]) - len(kept[table]) for table in staged if len(staged[table]) != len(kept[table])}


def plan(run: Runner, staged: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Per table: rows staged, keys already in the base (left untouched), rows to create; plus preflight problems."""
    ids = table_ids(run)
    excluded = excluded_products(run, ids)
    staged, skipped = without_excluded(staged, excluded)
    schema = {table: fields(run, ids[table]) for table in staged if table in ids}
    result: dict[str, Any] = {"tables": {}, "problems": preflight(staged, schema), "ids": ids, "schema": schema,
                              "excluded": sorted(excluded), "skipped": skipped, "staged": staged}
    for table, rows in staged.items():
        if table not in ids:
            continue
        primary = PRIMARY[table]
        compared = [name for name in COMPARED.get(table, ()) if name in result["schema"].get(table, {})]
        extra = [n for n in ("核实状态", "备注") if table == "事实" and n in result["schema"].get(table, {})]
        live = {_text(r.get(primary)): r for r in read_rows(run, ids[table], [primary, *compared, *extra])}
        create = [row for row in rows if row[primary] not in live]
        kinds = {name: (result["schema"][table].get(name) or {}).get("type", "text") for name in compared}
        result["tables"][table] = {"staged": len(rows), "existing": len(rows) - len(create),
                                   "rows_before": len(live), "create": create,
                                   "differ": _differences(rows, live, primary, compared, kinds)}
    return result


# Fields whose staged value is compared with the live row of the same key (time stamps, batch and notes are not).
COMPARED = {"事实": ("原文", "数值", "文本值", "原单位", "限定", "条件", "来源位置"),
            "来源": ("来源类型", "型号", "市场", "语言", "版本", "页面或文件", "文件哈希"),
            "产品": ("型号", "市场", "品牌")}


def _differences(rows: list[dict[str, Any]], live: dict[str, dict[str, Any]], primary: str, compared: list[str],
                 kinds: dict[str, str]) -> list[dict[str, Any]]:
    """Existing rows whose compared fields hold something other than what is staged now."""
    found = []
    for row in rows:
        have = live.get(row[primary])
        if have is None:
            continue
        changed = {name: {"live": have.get(name), "staged": row.get(name)} for name in compared
                   if not _equal_cell(row.get(name), have.get(name), kinds[name])}
        if changed:
            found.append({"key": row[primary], "record_id": have["_record_id"], "fields": changed,
                          "state": _text(have.get("核实状态")), "remark": _text(have.get("备注"))})
    return found


def _equal_cell(want: Any, have: Any, kind: str) -> bool:
    if want in (None, "", []) or have in (None, "", []):
        return want in (None, "", []) and have in (None, "", [])
    return same(want, have, kind)


# The only fields an in-place correction may change (operator, 2026-11-16), and the only one it may empty: a wrong
# unit read from a power row is cleared, never a printed text value.
CORRECTABLE = ("文本值", "原单位")
CLEARABLE = ("原单位",)


def correction_plan(planned: dict[str, Any]) -> dict[str, list]:
    """Which differing 事实 rows may be corrected in place, and which need a person's decision (and why)."""
    info = planned["tables"].get("事实") or {"differ": []}
    allowed, decide = [], []
    for item in info["differ"]:
        outside = sorted(set(item["fields"]) - set(CORRECTABLE))
        emptied = sorted(n for n, v in item["fields"].items() if v["staged"] in (None, "", []) and n not in CLEARABLE)
        if item["state"] != CANDIDATE:
            decide.append({"key": item["key"], "reason": f"核实状态为 {item['state'] or '空'}，不是候选"})
        elif outside:
            decide.append({"key": item["key"], "reason": f"差异含白名单以外的字段：{'、'.join(outside)}"})
        elif emptied:
            decide.append({"key": item["key"], "reason": f"修正会清空：{'、'.join(emptied)}"})
        else:
            allowed.append(item)
    return {"correct": allowed, "decide": decide}


def _current_states(run: Runner, table_id: str, items: list[dict[str, Any]]) -> dict[str, str]:
    wanted = {item["record_id"] for item in items}
    return {r["_record_id"]: _text(r.get("核实状态")) for r in read_rows(run, table_id, ["事实键", "核实状态"])
            if r["_record_id"] in wanted}


def correct(run: Runner, planned: dict[str, Any], batch: str, *, settle: float = 3.0,
            sleep: Callable[[float], None] = time.sleep) -> dict[str, Any]:
    """Correct 事实 rows in place whose printed source is unchanged but whose reading changed.

    Only rows whose differences lie within CORRECTABLE and which are still 候选 — checked again right before the
    write — are corrected: new values, the new batch label and a note of the old values; 原文 and 核实状态 stay.
    Everything else is reported for a person, never touched. A failed write still reads back what it changed.
    """
    chosen = correction_plan(planned)
    table_id = planned["ids"]["事实"]
    states = _current_states(run, table_id, chosen["correct"])
    decide = list(chosen["decide"])
    corrected: list[tuple[dict[str, Any], dict[str, Any]]] = []
    failure = None
    for item in chosen["correct"]:
        if states.get(item["record_id"]) != CANDIDATE:
            decide.append({"key": item["key"], "reason": "写入前复查：已不是候选"})
            continue
        note = "；".join(f"{name} 原为「{_text(v['live'])}」" for name, v in item["fields"].items())
        patch = {name: v["staged"] if v["staged"] not in ("", []) else None for name, v in item["fields"].items()}
        patch.update({"写入批次": batch, "备注": f"{item['remark']}；{batch} 修正：{note}".lstrip("；")})
        try:
            _check(run(["+record-upsert", "--table-id", table_id, "--record-id", item["record_id"], "--json",
                        json.dumps(patch, ensure_ascii=False)]), f"事实 correct {item['key']}", sensitive=True)
        except LoadError as exc:
            failure = exc
            break
        corrected.append((item, patch))
    sleep(settle)
    report = _correction_read_back(run, planned, corrected, decide)
    if failure:
        raise PartialWrite(f"{failure}; the corrections made so far were read back", {"事实": report})
    return report


def _correction_read_back(run: Runner, planned: dict[str, Any], corrected: list[tuple[dict, dict]],
                          decide: list[dict[str, Any]]) -> dict[str, Any]:
    table_id = planned["ids"]["事实"]
    names = sorted({"事实键", *(n for _item, patch in corrected for n in patch)})
    back = {r["_record_id"]: r for r in read_rows(run, table_id, names)} if corrected else {}
    kinds = {name: (planned["schema"]["事实"].get(name) or {}).get("type", "text") for name in names}
    mismatched = [f"{item['key']} · {name}" for item, patch in corrected for name, value in patch.items()
                  if not _equal_cell(value, back.get(item["record_id"], {}).get(name), kinds.get(name, "text"))]
    fields = Counter(name for item, _patch in corrected for name in item["fields"])
    return {"corrected": len(corrected), "keys": [item["key"] for item, _patch in corrected], "fields": dict(fields),
            "needs_decision": decide, "mismatched": mismatched}


def write(run: Runner, planned: dict[str, Any], *, use_records_shape: bool, settle: float = 3.0,
          sleep: Callable[[float], None] = time.sleep) -> dict[str, Any]:
    """Create the planned rows in batches, then read every one back by its key and compare each written field."""
    if planned["problems"]:
        raise LoadError("preflight problems; nothing written: " + "; ".join(planned["problems"][:10]))
    report: dict[str, Any] = {}
    failure = None
    for table in TABLES:
        info = planned["tables"].get(table)
        if not info or not info["create"] or failure:
            continue
        report[table] = {"requested": len(info["create"]), "sent": 0}
        for start in range(0, len(info["create"]), BATCH):
            chunk = info["create"][start:start + BATCH]
            payload = json.dumps(_payload(chunk, use_records_shape), ensure_ascii=False)
            try:
                _check(run(["+record-batch-create", "--table-id", planned["ids"][table], "--json", payload]),
                       f"{table} batch create")
            except LoadError as exc:
                failure = exc
                break
            report[table]["sent"] += len(chunk)
    sleep(settle)
    _read_back(run, planned, report)
    if failure:
        raise PartialWrite(f"{failure}; what reached the base was read back", report)
    return report


def _read_back(run: Runner, planned: dict[str, Any], report: dict[str, Any]) -> None:
    """Read every planned row of each table written to back by its key and compare each written field."""
    for table, entry in report.items():
        info = planned["tables"][table]
        primary = PRIMARY[table]
        names = sorted({name for row in info["create"] for name in row})
        kinds = {name: (planned["schema"][table].get(name) or {}).get("type", "text") for name in names}
        back = {_text(r.get(primary)): r for r in read_rows(run, planned["ids"][table], names)}
        missing, mismatched, record_ids = [], [], {}
        for row in info["create"]:
            got = back.get(row[primary])
            if got is None:
                missing.append(row[primary])
                continue
            record_ids[row[primary]] = got["_record_id"]
            for name, value in row.items():
                if not same(value, got.get(name), kinds[name]):
                    mismatched.append(f"{row[primary]} · {name}")
        entry.update({"read_back": len(record_ids), "missing": missing, "mismatched": mismatched,
                      "rows_after": len(back), "record_ids": record_ids})


__all__ = ["LoadError", "PartialWrite", "PRIMARY", "TABLES", "correct", "fact_key", "lark_runner", "plan", "preflight",
           "correction_plan", "product_key", "provenance", "read_rows", "records_shape", "same", "write"]
