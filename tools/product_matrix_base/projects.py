"""Fill 产品.项目号（仅飞书） from the 网页文档 table of the same base, inside Feishu only.

A product gets a project only when its 型号 maps to exactly one 项目号 in 网页文档 and its own field is still empty;
a product mapped to several projects or to none is left for a person. Project codes are read and written by this tool
but never printed, logged or put in a report: the summary names products and counts, not codes.
"""
from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from tools.product_matrix_base.stage import LoadError, Runner, _check, _text, read_rows, table_ids

PRODUCTS = "产品"
CATALOG = "网页文档"
FIELD = "项目号（仅飞书）"


def plan(run: Runner) -> dict[str, Any]:
    ids = table_ids(run)
    if PRODUCTS not in ids or CATALOG not in ids:
        raise LoadError(f"the base needs the {PRODUCTS} and {CATALOG} tables")
    projects: dict[str, set[str]] = defaultdict(set)
    for row in read_rows(run, ids[CATALOG], ["型号", "项目号"]):
        model, project = _text(row.get("型号")).strip(), _text(row.get("项目号")).strip()
        if model and project:
            projects[model].add(project)
    products = read_rows(run, ids[PRODUCTS], ["产品键", "型号", FIELD])
    result: dict[str, Any] = {"table_id": ids[PRODUCTS], "products": len(products), "filled": [], "fill": [],
                              "ambiguous": [], "unknown": []}
    used: set[str] = set()
    for product in sorted(products, key=lambda p: _text(p.get("产品键"))):
        key, found = _text(product.get("产品键")), projects.get(_text(product.get("型号")).strip(), set())
        used |= found
        if _text(product.get(FIELD)).strip():
            result["filled"].append(key)
        elif len(found) == 1:
            result["fill"].append({"key": key, "record_id": product["_record_id"], "value": next(iter(found))})
        else:
            result["ambiguous" if found else "unknown"].append(key)
    result["projects"] = len(used)
    return result


def write(run: Runner, planned: dict[str, Any], *, settle: float = 3.0,
          sleep: Callable[[float], None] = time.sleep) -> dict[str, Any]:
    """Write each resolved project into its product's empty field, then read every one back."""
    sent = 0
    for item in planned["fill"]:
        _check(run(["+record-upsert", "--table-id", planned["table_id"], "--record-id", item["record_id"],
                    "--json", __import__("json").dumps({FIELD: item["value"]}, ensure_ascii=False)]),
               f"{PRODUCTS} {item['key']}")
        sent += 1
    sleep(settle)
    back = {r["_record_id"]: _text(r.get(FIELD)) for r in read_rows(run, planned["table_id"], ["产品键", FIELD])}
    problems = [item["key"] for item in planned["fill"] if back.get(item["record_id"]) != item["value"]]
    return {"sent": sent, "matched": len(planned["fill"]) - len(problems), "problems": problems}


def summary(planned: dict[str, Any]) -> dict[str, Any]:
    """The plan as product keys only: safe to keep in a report file."""
    return {"products": planned["products"], "projects": planned["projects"], "filled": planned["filled"],
            "fill": [item["key"] for item in planned["fill"]], "ambiguous": planned["ambiguous"],
            "unknown": planned["unknown"]}


__all__ = ["plan", "summary", "write"]
