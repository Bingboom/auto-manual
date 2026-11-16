"""Stage the matrix base's rows from an extraction, and load them with read-back.

``stage_rows`` turns an extraction (``extract.py``) into the rows the 产品, 属性, 来源 and 事实 tables would hold:
products and sources from the selected editions, the dictionary as 属性, and every value as one 事实 row marked 候选.
``load`` compares the staged keys with the live tables, creates only the rows whose key is absent (an existing row is
never changed: a fact that changes is a new row under a new source key), and reads every written row back.

The tool writes no verification state other than 候选 and leaves 当前值, 冲突, 生效起 and every field people own empty.
"""
from __future__ import annotations

import json
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
        return {"ok": False, "error": {"message": (done.stdout + done.stderr)[:200]}}
    return run


def _check(result: dict[str, Any], what: str) -> dict[str, Any]:
    if not result.get("ok"):
        message = (result.get("error") or {}).get("message") or "no detail"
        raise LoadError(f"{what} failed: {message}")
    return result.get("data") or {}


def table_ids(run: Runner) -> dict[str, str]:
    data = _check(run(["+table-list"]), "table list")
    return {t["name"]: t.get("id") or t.get("table_id") for t in data.get("tables") or data.get("items") or []}


def fields(run: Runner, table_id: str) -> dict[str, dict[str, Any]]:
    data = _check(run(["+field-list", "--table-id", table_id, "--limit", "200"]), "field list")
    return {f["name"]: f for f in data.get("fields") or data.get("items") or []}


FIELDS_PER_READ = 50  # the CLI projects at most 50 fields per record list


def read_rows(run: Runner, table_id: str, names: list[str]) -> list[dict[str, Any]]:
    """Every row of a table with the named fields, read 50 fields at a time and merged by record id."""
    if len(names) <= FIELDS_PER_READ:
        return _read_rows(run, table_id, names)
    merged: dict[str, dict[str, Any]] = {}
    for start in range(0, len(names), FIELDS_PER_READ):
        for row in _read_rows(run, table_id, names[start:start + FIELDS_PER_READ]):
            merged.setdefault(row["_record_id"], {}).update(row)
    return list(merged.values())


def _read_rows(run: Runner, table_id: str, names: list[str]) -> list[dict[str, Any]]:
    """Every row of a table (paged, 200 at a time), as {"_record_id", field: value} for the named fields."""
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    offset = 0
    while True:
        args = ["+record-list", "--table-id", table_id, "--limit", "200", "--offset", str(offset)]
        for name in names:
            args += ["--field-id", name]
        data = _check(run(args), "record list")
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


def correct(run: Runner, planned: dict[str, Any], batch: str, *, settle: float = 3.0,
            sleep: Callable[[float], None] = time.sleep) -> dict[str, Any]:
    """Correct 事实 rows in place whose printed source is unchanged but whose reading changed.

    Only rows still 候选 (nobody has verified them) are corrected; each gets the new values, the new batch label and
    a note of the old values; 原文 and 核实状态 are left as they are. Other rows are reported, never touched.
    """
    info = planned["tables"].get("事实") or {"differ": []}
    table_id = planned["ids"]["事实"]
    corrected, skipped = [], []
    for item in info["differ"]:
        if item["state"] != CANDIDATE or "原文" in item["fields"]:
            skipped.append(item["key"])
            continue
        note = "；".join(f"{name} 原为「{_text(v['live'])}」" for name, v in item["fields"].items())
        patch = {name: v["staged"] if v["staged"] not in ("", []) else None for name, v in item["fields"].items()}
        patch.update({"写入批次": batch, "备注": f"{item['remark']}；{batch} 修正：{note}".lstrip("；")})
        _check(run(["+record-upsert", "--table-id", table_id, "--record-id", item["record_id"], "--json",
                    json.dumps(patch, ensure_ascii=False)]), f"事实 correct {item['key']}")
        corrected.append((item, patch))
    sleep(settle)
    names = sorted({"事实键", *(n for _item, patch in corrected for n in patch)})
    back = {r["_record_id"]: r for r in read_rows(run, table_id, names)}
    kinds = {name: (planned["schema"]["事实"].get(name) or {}).get("type", "text") for name in names}
    mismatched = [f"{item['key']} · {name}" for item, patch in corrected for name, value in patch.items()
                  if not _equal_cell(value, back.get(item["record_id"], {}).get(name), kinds.get(name, "text"))]
    return {"corrected": len(corrected), "skipped": skipped, "mismatched": mismatched}


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
           "product_key", "provenance", "read_rows", "records_shape", "same", "write"]
