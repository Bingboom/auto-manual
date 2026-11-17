"""Snapshot cells: the matrix's chosen value per product × parameter (× test condition), for pages that only display.

The private site's product pages show one value per product and parameter. Choosing it is the matrix's job
(`matrix._rank`, `matrix._cell`), so the snapshot carries the choice instead of each page writing its own rule:
rejected and superseded facts take no part; verified facts come first, then the source type's rank, then the newest
record. Component facts (条件 `组件:…`) never enter a cell. A test condition such as STC gets a cell of its own;
any other condition (a cycle count's "to 70% capacity", a printed qualifier) shares the main cell, as in the matrix.
"""
from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from typing import Any

from tools.product_matrix_base.matrix import (
    COMPONENT, EXCLUDED_STATES, NUMERIC, _cell, _number, _rank, _state, skip_reason,
)
from tools.product_matrix_base.stage import _text

TEST_CONDITION = re.compile(r"\b(STC|NOCT|BNPI)\b")  # solar test conditions: each gets its own cell


def value_id(fact_key: str) -> str:
    """An opaque, stable id for a fact (its key carries edition labels that do not leave Feishu)."""
    return hashlib.sha256(fact_key.encode("utf-8")).hexdigest()[:12]


def cell_condition(condition: str) -> str | None:
    """The cell a fact's condition opens: the test condition's name, or None for the main cell."""
    found = TEST_CONDITION.search(condition or "")
    return found.group(1) if found else None


def _one(facts: list[dict[str, Any]], attribute: dict[str, Any], by_source: dict[str, dict[str, Any]],
         source_id) -> dict[str, Any]:
    ranked = sorted(facts, key=lambda f: _rank(f, by_source))
    best = ranked[0]
    unit = _text(attribute.get("规范单位"))
    numeric = _text(attribute.get("值类型")) in NUMERIC
    display = _cell(best, numeric, unit)
    reason = skip_reason(best, unit) if numeric else ""
    return {"display": None if display is None else str(display),
            "number": None if skip_reason(best, unit) else _number(best.get("数值")),
            "text": _text(best.get("文本值")) or None, "unit": unit,
            "printed": _text(best.get("原文")) or None, "printed_unit": _text(best.get("原单位")) or None,
            "source": source_id(_text(best.get("来源键"))), "value": value_id(_text(best.get("事实键"))),
            "verified": _state(best) == "已核实",
            "sources_disagree": len({(_text(f.get("数值")), _text(f.get("文本值"))) for f in ranked}) > 1,
            "conflict": any(bool(f.get("冲突")) for f in ranked),
            "candidates": [value_id(_text(f.get("事实键"))) for f in ranked],
            "empty_reason": (reason or "无值") if display is None else None}


def build_cells(facts: list[dict[str, Any]], attributes: list[dict[str, Any]], sources: list[dict[str, Any]],
                source_id) -> list[dict[str, Any]]:
    """One cell per (product, enabled parameter, test condition) that has at least one taking-part fact."""
    enabled = {a["属性键"]: a for a in attributes if _text(a.get("状态")) in ("", "启用")}
    by_source = {_text(s.get("来源键")): s for s in sources}
    groups: dict[tuple[str, str, str | None], list[dict[str, Any]]] = defaultdict(list)
    for fact in facts:
        condition = _text(fact.get("条件"))
        key = _text(fact.get("属性键"))
        if condition.startswith(COMPONENT) or _state(fact) in EXCLUDED_STATES or key not in enabled:
            continue
        groups[(_text(fact.get("产品键")), key, cell_condition(condition))].append(fact)
    return [{"product": product, "parameter": key, "condition": condition,
             **_one(found, enabled[key], by_source, source_id)}
            for (product, key, condition), found in sorted(groups.items(), key=lambda g: (g[0][0], g[0][1], g[0][2] or ""))]


__all__ = ["TEST_CONDITION", "build_cells", "cell_condition", "value_id"]
