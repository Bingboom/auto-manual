#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pre-ingest completeness gate for spec-sheet intake.

Before structured candidates are written to the source tables, verify they are
*complete* against a reference target (the same product's already-ingested
sibling — e.g. JE-2000E_US for JE-2000E_JP, or the JP sibling for a new JP
manual). Catches the silent gaps that the per-field extractor cannot see on its
own: missing logical rows (a whole port/section absent), missing required
fields, and region/structure count mismatches.

Pure + deterministic so it can run as a hard gate in the ingest flow and in
unit tests. The reference is supplied by the caller (read from the formal table),
keeping this module free of any network dependency.
"""
from __future__ import annotations

import collections
from dataclasses import dataclass, field
from typing import Any, Iterable

# Identity fields a candidate row must carry to be ingestable (value may still be
# pending human confirmation — that is a separate gate, not completeness).
IDENTITY_FIELDS = ("Section", "Row_key", "label", "document_key", "Source_lang", "Page", "Line_order")


def _norm(v: Any) -> str:
    return str(v if v is not None else "").strip()


def logical_key(row: dict[str, Any], *, section_key: str = "Section") -> tuple[str, str, str, str]:
    """A row's structural identity: (Row_key, Slot_key, Section, Line_order).

    Section + Line_order are part of the key because the same Row_key legitimately
    repeats (dc_expansion_port across INPUT/OUTPUT sections; a multi-line
    storage_temperature), and dropping them would hide a real missing row.
    """
    line = _norm(row.get("Line_order")).split(".")[0] or "1"
    return (_norm(row.get("Row_key")), _norm(row.get("Slot_key")),
            _norm(row.get(section_key) or row.get("Section")), line)


@dataclass
class CompletenessReport:
    field_gaps: list[tuple[str, list[str]]] = field(default_factory=list)   # (label, missing fields)
    missing_rows: list[tuple[str, str, str, str]] = field(default_factory=list)  # ref keys absent in candidates
    extra_rows: list[tuple[str, str, str, str]] = field(default_factory=list)    # candidate keys absent in ref
    candidate_count: int = 0
    reference_count: int = 0

    @property
    def passed(self) -> bool:
        return not self.field_gaps and not self.missing_rows and not self.extra_rows

    def summary(self) -> str:
        if self.passed:
            return f"✅ complete: {self.candidate_count} rows cover reference ({self.reference_count})"
        bits = []
        if self.field_gaps:
            bits.append(f"{len(self.field_gaps)} rows missing required fields")
        if self.missing_rows:
            bits.append(f"{len(self.missing_rows)} reference rows missing from candidates")
        if self.extra_rows:
            bits.append(f"{len(self.extra_rows)} extra candidate rows not in reference")
        return "⚠️ incomplete: " + "; ".join(bits)


def check_completeness(
    candidates: Iterable[dict[str, Any]],
    reference: Iterable[dict[str, Any]],
    *,
    required_fields: tuple[str, ...] = IDENTITY_FIELDS,
    candidate_section_key: str = "Section",
    reference_section_key: str = "Section",
) -> CompletenessReport:
    """Compare candidate rows against a reference row set.

    ``required_fields`` are checked non-empty per candidate (identity by default;
    pass ``IDENTITY_FIELDS + ("value",)`` to also require a filled value).
    Reference rows whose logical key is absent from the candidates are reported as
    ``missing_rows`` — the gap the per-field extractor cannot see.
    """
    cands = list(candidates)
    refs = list(reference)
    rep = CompletenessReport(candidate_count=len(cands), reference_count=len(refs))

    for row in cands:
        miss = [f for f in required_fields if not _norm(row.get(f))]
        if miss:
            rep.field_gaps.append((_norm(row.get("label")) or _norm(row.get("Row_key")) or "?", miss))

    cand_keys = collections.Counter(logical_key(r, section_key=candidate_section_key) for r in cands)
    ref_keys = collections.Counter(logical_key(r, section_key=reference_section_key) for r in refs)
    rep.missing_rows = sorted(k for k in ref_keys if k not in cand_keys)
    rep.extra_rows = sorted(k for k in cand_keys if k not in ref_keys)
    return rep
