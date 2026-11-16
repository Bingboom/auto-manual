"""Generate the 矩阵 table from the facts in the base: one row per 产品键, one column per attribute with a value.

Each cell is the best current value for that product and attribute: the newest 已核实 fact; when none is verified, the
newest 候选 from the highest-ranked source. Component facts (条件 ``组件:…``) and facts a person rejected or
superseded never fill a cell. Attributes whose value type is numeric get a number column in the canonical unit (the
unit is in the column name), so the table sorts and filters; a numeric fact without a number leaves its cell empty and
is listed, never shown as text. A number cell cannot carry an "unverified" marker, so each row counts its verified,
candidate and conflicting values instead.

Rows are matched by 产品键: absent rows are created, changed rows updated, nothing is deleted. 生成时间 changes only
with the row, so a second run over unchanged facts has nothing to write.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from tools.product_matrix_base.stage import (
    LoadError, Runner, _check, _stamp, _text, fields, read_rows, same, table_ids,
)

MATRIX = "矩阵"
FIELD_LIMIT = 300  # Feishu Bitable: fields per table
IDENTITY = ("产品键", "型号", "市场", "品牌", "商品简称", "产品类别", "产品系列", "容量档")
COUNTS = ("已核实数", "候选数", "冲突数", "组件事实数", "空缺数值数")
STAMP = "生成时间"
NUMERIC = {"数值", "整数"}
NO_UNIT = {"", "count", "date", "currency", "当地货币"}
EXCLUDED_STATES = {"已驳回", "已取代"}
COMPONENT = "组件:"
# Printed units a canonical unit's number may come from (the loader already converted the number).
CONVERTS = {("kg", "g"), ("kg", "lbs"), ("kg", "lb"), ("mm", "cm"), ("mm", "in"), ("mm", "m"), ("Wh", "kWh"),
            ("W", "kW"), ("次", "cycles"), ("cycles", "次"), ("h", "min"), ("year", "month")}
SOURCE_RANK = {"网页说明书": 0, "印刷说明书": 1, "规格书": 2, "官网": 3, "其他": 4}


def column_name(attribute: dict[str, Any], taken: set[str]) -> str:
    """The attribute's readable column: its Chinese name, with the canonical unit for a numeric one."""
    name = _text(attribute.get("中文名")) or attribute["属性键"]
    unit = _text(attribute.get("规范单位"))
    if _text(attribute.get("值类型")) in NUMERIC and unit not in NO_UNIT:
        name = f"{name}（{unit}）"
    if name in taken:
        name = f"{name}（说明书）"
    return f"{name}·{attribute['属性键']}" if name in taken else name


def _state(fact: dict[str, Any]) -> str:
    return _text(fact.get("核实状态")) or "候选"


def _rank(fact: dict[str, Any], sources: dict[str, dict[str, Any]]) -> tuple:
    """Sort key, best first: verified, then the source type's rank, then the newest record."""
    source = sources.get(_text(fact.get("来源键")), {})
    verified = _state(fact) == "已核实"
    return (not verified, SOURCE_RANK.get(_text(source.get("来源类型")), 9), -_epoch(fact.get("记录时间")))


def _epoch(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return datetime.fromisoformat(_text(value)).timestamp()
    except ValueError:
        return 0.0


def _number(value: Any) -> float | int | None:
    if value in (None, ""):
        return None
    number = float(value)
    return int(number) if number.is_integer() else number


def skip_reason(fact: dict[str, Any], unit: str) -> str:
    """Why a number column cannot take this fact ('' when it can)."""
    if _number(fact.get("数值")) is None:
        return "无数值"
    printed = _text(fact.get("原单位"))
    if printed and unit not in NO_UNIT and printed != unit and (unit, printed) not in CONVERTS:
        return "单位与列不符"
    return ""


def _cell(fact: dict[str, Any], numeric: bool, unit: str) -> Any:
    if numeric:
        return None if skip_reason(fact, unit) else _number(fact.get("数值"))
    text = _text(fact.get("文本值"))
    if text and bare_range(fact):
        return printed(fact) or None  # a power row that prints no watts: show what it prints, not a voltage range
    if text:
        return f"{text} {unit}" if unit not in NO_UNIT and re.fullmatch(r"[-\d.~×x ]+", text) else text
    number = _number(fact.get("数值"))
    if number is None:
        return None
    return f"{number} {unit}".strip() if unit not in NO_UNIT else str(number)


def _group(facts: list[dict[str, Any]]) -> tuple[dict[tuple[str, str], list[dict[str, Any]]], Counter[str]]:
    """Main-product facts by (产品键, 属性键), leaving out rejected and superseded ones; component facts counted."""
    main: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    components: Counter[str] = Counter()
    for fact in facts:
        product = _text(fact.get("产品键"))
        if _text(fact.get("条件")).startswith(COMPONENT):
            components[product] += 1
        elif _state(fact) not in EXCLUDED_STATES:
            main[(product, _text(fact.get("属性键")))].append(fact)
    return main, components


def _columns(attributes: list[dict[str, Any]], with_value: set[str]) -> list[dict[str, Any]]:
    """One column per enabled attribute that has a value, in the dictionary's order."""
    enabled = sorted((a for a in attributes if _text(a.get("状态")) in ("", "启用") and a["属性键"] in with_value),
                     key=lambda a: _number(a.get("排序")) or 0)
    columns, taken = [], set(IDENTITY) | set(COUNTS) | {STAMP}
    for attribute in enabled:
        name = column_name(attribute, taken)
        taken.add(name)
        columns.append({"name": name, "key": attribute["属性键"], "unit": _text(attribute.get("规范单位")),
                        "type": "number" if _text(attribute.get("值类型")) in NUMERIC else "text"})
    return columns


def _row(product: dict[str, Any], columns: list[dict[str, Any]], main: dict, components: Counter,
         by_source: dict[str, dict[str, Any]], empty: list[dict[str, Any]]) -> dict[str, Any]:
    key = _text(product.get("产品键"))
    row: dict[str, Any] = {name: _text(product.get(name)) for name in IDENTITY}
    counts: Counter[str] = Counter({"组件事实数": components[key]})
    for column in columns:
        candidates = sorted(main.get((key, column["key"]), []), key=lambda f: _rank(f, by_source))
        if not candidates:
            continue
        best = candidates[0]
        counts["冲突数"] += any(bool(f.get("冲突")) for f in candidates)
        value = _cell(best, column["type"] == "number", column["unit"])
        if value is None:
            counts["空缺数值数"] += 1
            empty.append({"产品键": key, "属性键": column["key"], "事实键": _text(best.get("事实键")),
                          "原因": skip_reason(best, column["unit"]) if column["type"] == "number" else "无值",
                          "原文": _text(best.get("原文"))[:120]})
            continue
        row[column["name"]] = value
        counts["已核实数" if _state(best) == "已核实" else "候选数"] += 1
    row.update({name: counts[name] for name in COUNTS})
    return {k: v for k, v in row.items() if v not in (None, "")}


def build(products: list[dict[str, Any]], attributes: list[dict[str, Any]], facts: list[dict[str, Any]],
          sources: list[dict[str, Any]]) -> dict[str, Any]:
    """Columns, rows by 产品键, and the cells left empty with their reason."""
    by_source = {_text(s.get("来源键")): s for s in sources}
    main, components = _group(facts)
    columns = _columns(attributes, {key for _product, key in main})
    empty: list[dict[str, Any]] = []
    rows = {_text(p.get("产品键")): _row(p, columns, main, components, by_source, empty) for p in products}
    return {"columns": columns, "rows": rows, "empty": empty,
            "components": sum(1 for v in components.values() if v)}


def read_base(run: Runner) -> dict[str, Any]:
    ids = table_ids(run)
    missing = [name for name in ("产品", "属性", "来源", "事实", MATRIX) if name not in ids]
    if missing:
        raise LoadError(f"tables missing in the base: {missing}")
    return {
        "ids": ids,
        "products": read_rows(run, ids["产品"], list(IDENTITY)),
        "attributes": read_rows(run, ids["属性"], ["属性键", "中文名", "值类型", "规范单位", "状态", "排序"]),
        "facts": read_rows(run, ids["事实"], ["事实键", "产品键", "属性键", "数值", "文本值", "原单位", "条件",
                                             "核实状态", "来源键", "记录时间", "冲突", "原文"]),
        "sources": read_rows(run, ids["来源"], ["来源键", "来源类型"]),
    }


def _changes(built: dict[str, Any], current: dict[str, dict[str, Any]], names: list[str], have: dict,
             kinds: dict[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    create, update = [], []
    for key, row in built["rows"].items():
        old = current.get(key)
        if old is None:
            create.append(row)
            continue
        changes = {n: row.get(n) for n in names
                   if (n in have and not _equal(row.get(n), old.get(n), kinds[n])) or (n not in have and n in row)}
        if changes:
            update.append({"record_id": old["_record_id"], "key": key, "fields": changes})
    return create, update


def plan(run: Runner, base: dict[str, Any], built: dict[str, Any]) -> dict[str, Any]:
    """Columns to add, rows to create or update (by 产品键), and the matrix columns no attribute fills any more."""
    table_id = base["ids"][MATRIX]
    have = fields(run, table_id)
    wanted = manifest_fields(built)
    add = [f for f in wanted if f["name"] not in have]
    if len(have) + len(add) > FIELD_LIMIT:
        raise LoadError(f"{MATRIX} would hold {len(have) + len(add)} fields, over the limit of {FIELD_LIMIT}")
    names = [f["name"] for f in wanted if f["name"] != STAMP]
    kinds = {f["name"]: f["type"] for f in wanted}
    current = {_text(r.get("产品键")): r for r in read_rows(run, table_id, [n for n in names if n in have])}
    create, update = _changes(built, current, names, have, kinds)
    return {"table_id": table_id, "add": add, "create": create, "update": update, "kinds": kinds,
            "clash": [f["name"] for f in wanted if f["name"] in have and have[f["name"]].get("type") != f["type"]],
            "unused": sorted(set(have) - {f["name"] for f in wanted})}


def _equal(want: Any, have: Any, kind: str) -> bool:
    if want in (None, "") and have in (None, "", []):
        return True
    if want in (None, "") or have in (None, "", []):
        return False
    return same(want, have, kind)


def write(run: Runner, planned: dict[str, Any], *, now: datetime | None = None, settle: float = 3.0,
          sleep: Callable[[float], None] | None = None) -> dict[str, Any]:
    """Add the columns, create and update the rows, then read every row back and compare."""
    if planned["clash"]:
        raise LoadError(f"{MATRIX} columns exist with another type: {planned['clash']}")
    table_id = planned["table_id"]
    for field in planned["add"]:
        _check(run(["+field-create", "--table-id", table_id, "--json", json.dumps(field, ensure_ascii=False)]),
               f"{MATRIX} field {field['name']}")
    stamp = _stamp(now or datetime.now(timezone.utc))
    created = [dict(row, **{STAMP: stamp}) for row in planned["create"]]
    for start in range(0, len(created), 100):
        chunk = created[start:start + 100]
        _check(run(["+record-batch-create", "--table-id", table_id, "--json",
                    json.dumps({"create_records": chunk}, ensure_ascii=False)]), f"{MATRIX} batch create")
    for change in planned["update"]:
        _check(run(["+record-upsert", "--table-id", table_id, "--record-id", change["record_id"], "--json",
                    json.dumps(dict(change["fields"], **{STAMP: stamp}), ensure_ascii=False)]),
               f"{MATRIX} update {change['key']}")
    (sleep or __import__("time").sleep)(settle)
    expected = {row["产品键"]: row for row in created}
    expected.update({c["key"]: c["fields"] for c in planned["update"]})
    names = sorted({n for row in expected.values() for n in row} | {"产品键"})
    back = {_text(r.get("产品键")): r for r in read_rows(run, table_id, names)}
    missing = [key for key in expected if key not in back]
    mismatched = [f"{key} · {name}" for key, row in expected.items() if key in back for name, value in row.items()
                  if name != STAMP and not _equal(value, back[key].get(name), planned["kinds"].get(name, "text"))]
    return {"columns_added": len(planned["add"]), "created": len(created), "updated": len(planned["update"]),
            "missing": missing, "mismatched": mismatched, "rows_after": len(back)}


def drop_unused(run: Runner, planned: dict[str, Any]) -> list[str]:
    """Delete the matrix columns no attribute fills any more, only when every row leaves them empty."""
    if not planned["unused"]:
        return []
    rows = read_rows(run, planned["table_id"], planned["unused"])
    filled = sorted({name for row in rows for name in planned["unused"] if row.get(name) not in (None, "", [])})
    if filled:
        raise LoadError(f"{MATRIX} columns to drop still hold values: {filled}")
    for name in planned["unused"]:
        _check(run(["+field-delete", "--table-id", planned["table_id"], "--field-id", name, "--yes"]),
               f"{MATRIX} drop {name}")
    return list(planned["unused"])


def manifest_fields(built: dict[str, Any]) -> list[dict[str, str]]:
    """The 矩阵 table's fields as the schema manifest lists them."""
    return [{"name": n, "type": "text"} for n in IDENTITY] + \
        [{"name": c["name"], "type": c["type"]} for c in built["columns"]] + \
        [{"name": n, "type": "number"} for n in COUNTS] + [{"name": STAMP, "type": "datetime"}]


def filled_cells(built: dict[str, Any]) -> tuple[int, int]:
    """Filled attribute cells and possible ones (products × attribute columns)."""
    names = {c["name"] for c in built["columns"]}
    filled = sum(1 for row in built["rows"].values() for name in row if name in names)
    return filled, len(built["rows"]) * len(names)


def bare_range(fact: dict[str, Any]) -> bool:
    """A text value that is only a numeric range, read from a row that is not a temperature (the seed batch stores
    the voltage range of a power row that prints no watts this way)."""
    return (fact.get("数值") in (None, "") and bool(re.fullmatch(r"-?[\d.]+~-?[\d.]+", _text(fact.get("文本值"))))
            and "temp" not in _text(fact.get("属性键")))


def printed(fact: dict[str, Any]) -> str:
    """The printed value of a fact's 原文 (after its label)."""
    text = _text(fact.get("原文"))
    return text.split(": ", 1)[1] if ": " in text and not text.startswith("派生") else text


def defect_rows(facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Main-product facts whose text value is such a bare range."""
    return [f for f in facts if bare_range(f) and not _text(f.get("条件")).startswith(COMPONENT)]


__all__ = ["skip_reason", "bare_range", "build", "column_name", "defect_rows", "drop_unused", "filled_cells", "manifest_fields", "plan", "read_base", "write"]
