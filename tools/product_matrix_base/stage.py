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
import subprocess
import time
from collections.abc import Callable, Iterable
from datetime import datetime, timezone, timedelta
from typing import Any

TABLES = ("产品", "属性", "来源", "事实")
PRIMARY = {"产品": "产品键", "属性": "属性键", "来源": "来源键", "事实": "事实键", "矩阵": "产品键"}
BATCH = 100  # the CLI accepts at most 200 rows per batch-create; stay well inside it
CANDIDATE = "候选"
BRAND = "自有"
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


def _location(row: dict[str, Any] | None) -> str:
    if not row:
        return ""
    where = f"{row['section']} · 表{row['table']} 行{row['row']}" if row["table"] else f"{row['section']} · 行{row['row']}"
    return f"{where} · #{row['anchor']}" if row.get("anchor") else where


def _name(title: str, model: str) -> str:
    from tools.rtd.product_matrix import display_name

    return display_name(title, model) if title else ""


def _name_field(name: str) -> str:
    """Which 名称 column a catalog name belongs in, by its script: kana is Japanese, other CJK Chinese."""
    if re.search(r"[\u3040-\u30ff]", name):
        return "名称_ja"
    if re.search(r"[\u4e00-\u9fff]", name):
        return "名称_zh"
    return "名称_en" if name else ""


def select_editions(extraction: dict[str, Any], models: Iterable[str] | None, markets: Iterable[str] | None
                    ) -> list[dict[str, Any]]:
    wanted_models = set(models or [])
    wanted_markets = set(markets or [])
    return [e for e in extraction["editions"]
            if (not wanted_models or e["model"] in wanted_models) and (not wanted_markets or e["market"] in wanted_markets)]


def _product_row(edition: dict[str, Any], entry: dict[str, Any], recorded: str) -> dict[str, Any]:
    key = product_key(edition["model"], edition["market"])
    return {"产品键": key, "型号": edition["model"], "市场": edition["market"], "品牌": BRAND,
            "商品简称": entry.get("short"), "产品类别": entry.get("category"), "产品系列": entry.get("series"),
            "容量档": entry.get("capacity"), "共用说明书于": entry.get("pages_of"), "最后更新": recorded}


def _attribute_row(attribute: dict[str, Any]) -> dict[str, Any]:
    return {"属性键": attribute["key"], "中文名": attribute["label"], "英文名": attribute.get("label_en"),
            "分组": attribute["group"], "值类型": VALUE_TYPES[attribute["type"]], "规范单位": attribute.get("unit"),
            "定义": attribute.get("definition"), "适用类别": list(attribute.get("applies_to") or []),
            "说明书通常写": bool(attribute.get("manual_usual")), "标签别名": "\n".join(attribute.get("labels") or []),
            "竞情字段名": attribute.get("competitor_field"), "状态": attribute.get("status") or "启用",
            "排序": attribute["order"]}


def _source_row(edition: dict[str, Any], recorded: str) -> dict[str, Any]:
    built = str(edition.get("built_at") or "")[:10]
    return {"来源键": edition["source_key"], "来源类型": SOURCE_TYPE, "型号": edition["model"],
            "市场": edition["market"], "语言": edition["language"], "版本": edition.get("version"),
            "版本日期依据": UNKNOWN_DATE_BASIS, "页面或文件": edition["page"], "文件哈希": edition.get("sha256"),
            "读取时间": recorded, "备注": f"网页构建时间 {built}" if built else None}


def _fact_row(edition: dict[str, Any], fact: dict[str, Any], recorded: str) -> dict[str, Any]:
    product = product_key(edition["model"], edition["market"])
    condition = fact.get("condition") or ""
    return {"事实键": fact_key(product, fact["attribute"], condition, edition["source_key"]),
            "产品键": product, "属性键": fact["attribute"], "来源键": edition["source_key"],
            "原文": f"{fact['label']}: {fact['quote_text']}", "数值": fact.get("number"), "文本值": fact.get("text"),
            "原单位": fact.get("original_unit"), "限定": fact.get("qualifier") or "无", "条件": condition,
            "来源位置": _location(fact.get("row")), "记录时间": recorded, "核实状态": CANDIDATE}


def _filled(row: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in row.items() if v not in ("", None, [])}


def stage_rows(extraction: dict[str, Any], catalog_models: dict[str, Any], *, models: Iterable[str] | None = None,
               markets: Iterable[str] | None = None, attributes: Iterable[str] | None = None,
               now: datetime | None = None) -> dict[str, list[dict[str, Any]]]:
    """The rows each table would hold for the selected products, keyed by their primary field."""
    recorded = _stamp(now or datetime.now(timezone.utc))
    dictionary = extraction["attributes"]
    keep = set(attributes or [a["key"] for a in dictionary])
    editions = select_editions(extraction, models, markets)
    products: dict[str, dict[str, Any]] = {}
    for edition in editions:
        row = products.setdefault(product_key(edition["model"], edition["market"]),
                                  _product_row(edition, catalog_models.get(edition["model"]) or {}, recorded))
        name = _name(edition.get("catalog_name") or "", edition["model"])
        if name and not row.get(_name_field(name)):
            row[_name_field(name)] = name
    staged = {
        "产品": list(products.values()),
        "属性": [_attribute_row(a) for a in dictionary if a["key"] in keep],
        "来源": [_source_row(edition, recorded) for edition in editions],
        "事实": [_fact_row(edition, fact, recorded) for edition in editions for fact in edition["facts"]
                 if fact["attribute"] in keep],
    }
    return {table: [_filled(row) for row in rows] for table, rows in staged.items()}


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


def plan(run: Runner, staged: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Per table: rows staged, keys already in the base (left untouched), rows to create; plus preflight problems."""
    ids = table_ids(run)
    schema = {table: fields(run, ids[table]) for table in staged if table in ids}
    result: dict[str, Any] = {"tables": {}, "problems": preflight(staged, schema), "ids": ids, "schema": schema}
    for table, rows in staged.items():
        if table not in ids:
            continue
        primary = PRIMARY[table]
        existing = {_text(r.get(primary)) for r in read_rows(run, ids[table], [primary])}
        create = [row for row in rows if row[primary] not in existing]
        result["tables"][table] = {"staged": len(rows), "existing": len(rows) - len(create),
                                   "rows_before": len(existing), "create": create}
    return result


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


__all__ = ["LoadError", "PartialWrite", "provenance", "PRIMARY", "TABLES", "fact_key", "lark_runner", "plan", "preflight", "product_key",
           "read_rows", "records_shape", "same", "stage_rows", "write"]
