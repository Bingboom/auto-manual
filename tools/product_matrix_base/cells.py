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
import unicodedata
from decimal import Decimal
from collections import defaultdict
from typing import Any

from tools.product_matrix_base.matrix import (
    COMPONENT, EXCLUDED_STATES, NO_UNIT, NUMERIC, _cell, _number, _rank, _state, skip_reason,
)
from tools.product_matrix_base.stage import LoadError, _text

# Solar test conditions, each with its own cell. Bounded by non-letters, not \b: 「STC条件」 must match too.
TEST_CONDITION = re.compile(r"(?<![A-Za-z])(STC|NOCT|BNPI)(?![A-Za-z])", re.IGNORECASE)


def value_id(fact_key: str) -> str:
    """An opaque, stable id for a fact (its key carries edition labels that do not leave Feishu)."""
    return hashlib.sha256(fact_key.encode("utf-8")).hexdigest()[:12]


def cell_condition(condition: str) -> str | None:
    """The cell a fact's condition opens: the test condition's name, or None for the main cell."""
    found = TEST_CONDITION.search(condition or "")
    return found.group(1).upper() if found else None


DERIVED = re.compile(r"^派生[:：]\s*")  # the loader's marker on a value derived from several printed rows


def split_derived(original: Any) -> tuple[str | None, bool]:
    """A fact's 原文 for pages: the text without the loader's 「派生:」 marker, and whether it was derived."""
    text = _text(original)
    if not text:
        return None, False
    found = DERIVED.match(text)
    return (text[found.end():] or None, True) if found else (text, False)


def _plain(number: Any) -> str:
    """A number in plain decimal notation (never 1e-07), without trailing zeros."""
    if isinstance(number, float):
        text = format(Decimal(repr(number)), "f")  # the shortest exact digits, without an exponent
        return text.rstrip("0").rstrip(".") if "." in text else text
    return str(number)


def display_text(value: Any, numeric: bool, unit: str) -> str | None:
    """What a page shows: the matrix cell, with the parameter's unit after a number (the matrix keeps the unit in its
    column name); integers without ".0". Text never carries the loader's 「派生:」 marker: a derived power row that
    prints no watts reaches here as its 原文, marker included."""
    if value is None:
        return None
    if numeric:
        number = _plain(_number(value))
        return f"{number} {unit}" if unit not in NO_UNIT else number
    return split_derived(str(value))[0]


def compare_key(text: Any) -> str | None:
    """The form two printed values are compared in: NFKC (₄ = 4, full width = half width), no spaces, lower case.
    Pages compare cells by it; they still show `display` as printed."""
    value = _text(text)
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value)).lower() if value else None


def _same_value(fact: dict[str, Any]) -> tuple[Any, str]:
    """A fact's value for comparison: the number as a number (100 equals 100.0), and the text."""
    try:
        number = _number(fact.get("数值"))
    except (TypeError, ValueError):
        number = _text(fact.get("数值"))
    return (number, compare_key(fact.get("文本值")) or "")


def _one(facts: list[dict[str, Any]], attribute: dict[str, Any], by_source: dict[str, dict[str, Any]],
         source_id) -> dict[str, Any]:
    ranked = sorted(facts, key=lambda f: _rank(f, by_source))
    best = ranked[0]
    unit = _text(attribute.get("规范单位"))
    numeric = _text(attribute.get("值类型")) in NUMERIC
    display = _cell(best, numeric, unit)
    reason = skip_reason(best, unit) if numeric else ""
    shown = display_text(display, numeric, unit)
    return {"display": shown, "compare": compare_key(shown),
            "number": None if skip_reason(best, unit) else _number(best.get("数值")),
            "text": _text(best.get("文本值")) or None, "unit": unit,
            "printed": split_derived(best.get("原文"))[0], "derived": split_derived(best.get("原文"))[1],
            "printed_unit": _text(best.get("原单位")) or None,
            "source": source_id(_text(best.get("来源键"))), "value": value_id(_text(best.get("事实键"))),
            "verified": _state(best) == "已核实",
            "sources_disagree": len({_same_value(f) for f in ranked}) > 1,  # within this cell only
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


class SnapshotReferenceError(LoadError):
    """The snapshot's references do not resolve; `rows` names the base rows behind it (fact and source keys only)."""

    def __init__(self, message: str, rows: list[tuple[str, str, str]] | None = None):
        super().__init__(message)
        self.rows = rows or []


def _takes_part(fact: dict[str, Any]) -> bool:
    return not _text(fact.get("条件")).startswith(COMPONENT) and _state(fact) not in EXCLUDED_STATES


def reference_rows(facts: list[dict[str, Any]], sources: list[dict[str, Any]],
                   chosen: set[str]) -> list[tuple[str, str, str]]:
    """The base rows behind a failed check: facts sharing a key, and cell-chosen facts whose source row is gone.

    Only rows that cause the failure: every fact for duplicate ids (component values carry ids too), and for missing
    sources only the facts a cell chose (`chosen`, by value id). Keys only, no project numbers; they carry edition
    labels and free condition text, so they are printed locally and never written to a file."""
    seen: dict[str, int] = defaultdict(int)
    for fact in facts:
        seen[_text(fact.get("事实键"))] += 1
    known = {_text(s.get("来源键")) for s in sources}
    rows = [("同键事实", key, "") for key, count in sorted(seen.items()) if count > 1]
    rows += sorted(("来源行缺失", _text(f.get("事实键")), _text(f.get("来源键"))) for f in facts
                   if _takes_part(f) and _text(f.get("来源键")) not in known
                   and value_id(_text(f.get("事实键"))) in chosen)
    return rows


def check_references(document: dict[str, Any]) -> None:
    """Stop before writing unless every id is unique and every cell's value, candidates and source resolve.

    Counts only in the message: ids and keys stay in the file."""
    values = [v["id"] for v in document.get("values", []) + document.get("component_values", [])]
    known = set(values)
    sources = {s["id"] for s in document.get("sources", [])}
    duplicate = len(values) - len(known)
    unresolved = sum(1 for c in document.get("cells", []) for i in [c["value"], *c["candidates"]] if i not in known)
    repeated = sum(len(c["candidates"]) - len(set(c["candidates"])) for c in document.get("cells", []))
    sourceless = sum(1 for c in document.get("cells", []) if c["source"] not in sources)
    if duplicate or unresolved or repeated or sourceless:
        raise SnapshotReferenceError(f"snapshot references do not resolve: {duplicate} duplicate value ids, {unresolved} unresolved "
                        f"cell values, {repeated} repeated candidates, {sourceless} cells whose source has no row")


__all__ = ["DERIVED", "compare_key", "SnapshotReferenceError", "TEST_CONDITION", "split_derived", "build_cells", "cell_condition", "check_references", "display_text",
           "reference_rows", "value_id"]
