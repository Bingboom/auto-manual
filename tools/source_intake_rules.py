#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Field-mapping rule engine for spec-sheet -> structured-data intake.

A 产品规格书 (product spec sheet) lists values under Chinese field names; this
module maps each to a canonical ``Row_key`` and applies a deterministic,
**region-aware** value transform (US manuals use dual imperial/metric units;
JP/EU use metric). The rules are data (a list of :class:`FieldRule`, typically
synced from the ``规格书字段映射规则`` Bitable) so new spec sheets are handled by
adding rules, not code.

Pure + deterministic by design (exact-or-needs-review): a value a rule cannot
transform is returned with status ``needs_review`` for a human, never guessed.
Cell splitting is shared with the cloud-doc backport via
:func:`tools.token_resolution_map.split_cells` so markdown/HTML tables parse
identically on both the intake and backport sides.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

from tools.token_resolution_map import split_cells

# Transform op vocabulary (the ``取值规则`` column of the rule table):
OPS = frozenset({"passthrough", "default", "capacity", "weight", "dims_mm_to_cm",
                 "temp", "cycle_life", "dc12", "manual", "exclude"})

# Result statuses:
DIRECT = "direct"            # ✅ value used as-is (passthrough / default)
TRANSFORMED = "transformed"  # 🔧 deterministically reformatted from the raw
NEEDS_REVIEW = "needs_review"  # ⚠️ human must supply/confirm the value
EXCLUDED = "excluded"        # field deliberately not manual-facing

_WS_RE = re.compile(r"\s+")


def _clean(text: Any) -> str:
    return _WS_RE.sub(" ", str(text or "").strip())


def display_width(text: str) -> int:
    """East-Asian display width (full-width CJK counts as 2) — used for RST title
    underlines and any width-sensitive rendering."""
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in text)


@dataclass(frozen=True)
class FieldRule:
    """One spec-field -> Row_key mapping with a transform op."""
    row_key: str
    section: str
    label: str
    spec_field: str
    op: str = "manual"
    default: str = ""
    manual_facing: bool = True
    slot_key: str = ""
    line_order: int = 1

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "FieldRule":
        lo = str(d.get("Line_order") or d.get("line_order") or "1").split(".")[0]
        mf = d.get("manual_facing")
        return FieldRule(
            row_key=_clean(d.get("Row_key") or d.get("row_key")),
            section=_clean(d.get("章节") or d.get("Section") or d.get("section")),
            label=_clean(d.get("行标签") or d.get("Row_label") or d.get("label")),
            spec_field=_clean(d.get("规格书字段") or d.get("spec_field")),
            op=(_clean(d.get("取值规则") or d.get("op")) or "manual"),
            default=_clean(d.get("默认值") or d.get("default")),
            manual_facing=bool(mf) if mf is not None else True,
            slot_key=_clean(d.get("Slot_key") or d.get("slot_key")),
            line_order=int(lo) if lo.isdigit() else 1,
        )


def _num(raw: str, pattern: str, flags: int = 0) -> str | None:
    m = re.search(pattern, raw, flags)
    return m.group(1) if m else None


def apply_op(op: str, raw: str | None, default: str, region: str,
             *, parts: list[str] | None = None) -> tuple[str | None, str]:
    """Apply a transform op to a raw spec value. Returns ``(value, status)``.

    ``region`` of ``US`` yields dual imperial/metric units for weight/dimensions/
    temperature; any other region yields metric only. A value that cannot be
    produced deterministically returns ``(proposal_or_None, NEEDS_REVIEW)``.
    """
    us = (region or "").upper() == "US"
    if op == "exclude":
        return None, EXCLUDED
    if op == "default":
        return (default or None), DIRECT
    raw = _clean(raw)
    if not raw:
        # default already handled; everything else needs the raw value
        return (default or None), (DIRECT if default else NEEDS_REVIEW)
    if op == "passthrough":
        return ((parts[0] if parts else raw)), DIRECT
    if op == "capacity":
        wh = _num(raw, r"([\d.]+)\s*Wh"); v = _num(raw, r"([\d.]+)\s*V"); ah = _num(raw, r"([\d.]+)\s*Ah")
        if wh and v and ah:
            return f"{wh} Wh ({ah} Ah / {v} V DC)", TRANSFORMED
    elif op == "weight":
        kg = _num(raw, r"([\d.]+)\s*Kg", re.I)
        if kg:
            if us:
                return f"About {round(float(kg) * 2.20462, 2)} lbs/{kg} kg", TRANSFORMED
            return f"About {kg} kg", TRANSFORMED
    elif op == "dims_mm_to_cm":
        mm = [int(x) for x in re.findall(r"(\d+)\s*mm", raw)]
        if len(mm) >= 3:
            cm = " × ".join(f"{x / 10:g}" for x in mm[:3]) + " cm"
            if us:
                inch = " × ".join(f"{x / 25.4:.1f}" for x in mm[:3]) + " in"
                return f"{inch} / {cm}", TRANSFORMED
            return cm, TRANSFORMED
    elif op == "temp":
        m = re.search(r"(-?\d+)\s*[~\-–]\s*(-?\d+)\s*℃", raw)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            def f(c: int) -> int: return round(c * 9 / 5 + 32)
            # the charge/discharge split stays a human decision -> needs_review
            return ((f"{f(lo)} °F to {f(hi)} °F / {lo} °C to {hi} °C" if us
                     else f"{lo} °C to {hi} °C"), NEEDS_REVIEW)
    elif op == "cycle_life":
        n = _num(raw, r"(\d+)\s*Cycles", re.I)
        if n:
            return f"{n} cycles to 70%+ capacity", TRANSFORMED
    elif op == "dc12":
        m = re.search(r"(\d+)\s*V.*?(\d+)\s*A", raw)
        if m:
            return f"{m.group(1)} V⎓{m.group(2)} A max.", TRANSFORMED
    elif op == "manual":
        return raw, NEEDS_REVIEW
    # op recognised but the raw didn't match the expected shape -> abstain
    return raw, NEEDS_REVIEW


# --- spec-sheet text scanning (pdftotext output: label line then value line(s)) ---

_LABEL_HINT = ("客户型号", "制造商型号", "型号", "额定容量", "放电容量", "循环寿命",
               "储存环境温度", "工作环境温度", "工作环境湿度", "污染等级", "防护等级",
               "产品重量", "充电时间", "充电输入", "交流输出", "直流扩容", "车充输出",
               "USBC", "USBA", "Table")


def _norm(s: str) -> str:
    return _WS_RE.sub("", s or "")


def _base_field(s: str) -> str:
    return _norm(re.sub(r"[〔(（].*?[〕)）]$", "", s or ""))


def find_field_value(lines: list[str], spec_field: str, *, headers: set[str]) -> tuple[str | None, list[str]]:
    """Locate a spec-field header in pdftotext lines, return ``(value, parts)``.

    The value is taken from the same line (after ``:``/``：``) or the following
    non-empty, non-header lines (a label may be paired with a sibling header in a
    2-column table, so leading headers are skipped). ``headers`` is the set of
    normalised field/label names that mark a boundary.
    """
    bf = _base_field(spec_field)
    if not bf:
        return None, []

    def is_label(ln: str) -> bool:
        n = _norm(ln)
        return any(n == h or n.startswith(h) for h in headers) or ln.strip().endswith((":", "："))

    for i, ln in enumerate(lines):
        n = _norm(ln)
        if n == bf or n.startswith(bf):
            after = re.split(r"[:：]", ln, 1)
            if len(after) == 2 and after[1].strip():
                return after[1].strip(), [after[1].strip()]
            vals: list[str] = []
            j = i + 1
            while j < len(lines) and len(vals) < 2:
                t = lines[j].strip(); j += 1
                if not t:
                    continue
                if is_label(t):
                    if vals:
                        break
                    continue
                vals.append(t)
            if vals:
                return " ".join(vals), vals
    return None, []


def extract_candidates(text: str, rules: list[FieldRule], *, region: str,
                       document_key: str, source_lang: str = "en") -> list[dict[str, Any]]:
    """Apply the rule set to spec-sheet text -> candidate rows (one per manual-facing rule)."""
    lines = [ln.rstrip() for ln in (text or "").splitlines()]
    headers = {_base_field(r.spec_field) for r in rules} | {_norm(h) for h in _LABEL_HINT}
    headers.discard("")
    out: list[dict[str, Any]] = []
    for r in rules:
        if r.op == "exclude" or not r.manual_facing:
            continue
        raw, parts = (None, [])
        if r.op != "default":
            raw, parts = find_field_value(lines, r.spec_field, headers=headers)
        value, status = apply_op(r.op, raw, r.default, region, parts=parts or None)
        out.append({
            "Row_key": r.row_key, "Section": r.section, "label": r.label,
            "Slot_key": r.slot_key, "Line_order": r.line_order,
            "value": value, "status": status, "spec_field": r.spec_field,
            "raw": raw or "", "document_key": document_key, "Source_lang": source_lang,
            "Page": "specifications",
        })
    return out
