"""Token/copy resolution value index (Milestone F, PR F2).

Lightweight build-time provenance (see
``code-as-doc/architecture/Feishu_Cloud_Doc_Backport_Design.md`` §5.1 R8): index
every localized data value in the snapshot back to its source row so the backport
can recognize a reviewer-changed span as **Class D** (data-origin) deterministically
instead of guessing with a heuristic.

The index is derived from the snapshot CSVs the build already consumes
(``Spec_Master.csv`` per-language value columns and ``Localized_Copy.csv`` per-
language text columns), so it needs no build-engine change and stays deterministic
and CI-friendly.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

SPEC_MASTER_FILE = "Spec_Master.csv"
LOCALIZED_COPY_FILE = "Localized_Copy.csv"

# Per-row localized value columns in Spec_Master are ``<base>_<lang>``.
_SPEC_MASTER_VALUE_BASES = ("Value", "Param", "Row_label")

_WS_RE = re.compile(r"\s+")


def _normalize(text: str | None) -> str:
    return _WS_RE.sub(" ", (text or "").strip())


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _add(index: dict[str, dict[str, Any]], value: str | None, source_ref: dict[str, Any]) -> None:
    key = _normalize(value)
    if not key:
        return
    existing = index.get(key)
    if existing is not None:
        # Same value string in more than one source row: still data-origin, but the
        # exact source_ref is no longer certain.
        existing["ambiguous"] = True
        return
    index[key] = dict(source_ref)


def build_value_index(snapshot_root: Path, lang: str) -> dict[str, dict[str, Any]]:
    """Map every localized data value (normalized) to its source reference.

    ``lang`` is the value-column suffix (e.g. ``fr``, ``es``, ``de``, ``it``,
    ``uk``). Unknown columns simply contribute nothing.
    """

    root = Path(snapshot_root)
    want_lang = str(lang or "").strip().lower()
    index: dict[str, dict[str, Any]] = {}
    for row in _read_csv(root / SPEC_MASTER_FILE):
        base_ref = {
            "table": "Spec_Master",
            "document_key": (row.get("document_key") or "").strip(),
            "row_key": (row.get("Row_key") or "").strip(),
            "slot_key": (row.get("Slot_key") or "").strip(),
        }
        # A source-language review (e.g. US-en) has its values in <base>_source — the real
        # Spec_Master carries Value_source plus localized columns but no Value_en. Index
        # the source column too when this row's Source_lang IS the requested language, so
        # a source-language spec edit is still recognized as Class D (not just localized).
        is_source_lang = bool(want_lang) and _normalize(row.get("Source_lang")).lower() == want_lang
        for base in _SPEC_MASTER_VALUE_BASES:
            _add(index, row.get(f"{base}_{lang}"), {**base_ref, "field": f"{base}_{lang}"})
            if is_source_lang:
                _add(index, row.get(f"{base}_source"), {**base_ref, "field": f"{base}_source"})
    for row in _read_csv(root / LOCALIZED_COPY_FILE):
        column = f"text_{lang}"
        _add(
            index,
            row.get(column),
            {
                "table": "Localized_Copy",
                "field": column,
                "copy_key": (row.get("copy_key") or "").strip(),
                # Carry the rendered lang + the copy's source language so the F6
                # write path can map a source-language edit back to the authoring
                # Manual_Copy_Source.source_text, and abstain on translations.
                "lang": str(lang or "").strip(),
                "source_lang": (row.get("Source_lang") or "").strip(),
            },
        )
    return index


_CELL_SPLIT_RE = re.compile(r"<br\s*/?>|\|", re.IGNORECASE)


def _value_candidates(text: str | None) -> list[str]:
    """Atomic value candidates from a delta's normalized text.

    The whole text first (a bare value or a body-copy paragraph), then — when the
    delta carries table structure — each cell and ``<br/>``-joined sub-value. A real
    cloud-doc delta arrives at row/paragraph granularity (``| value <br/> value |
    label |``), not as a bare cell, so a contained-value match is what lets the value
    index resolve it deterministically. Feed this the **normalized** (markdown-stripped)
    text so cells compare cleanly against the snapshot CSV values.
    """

    norm = _normalize(text)
    if not norm:
        return []
    candidates = [norm]
    if "|" in norm or "<br" in norm.lower():
        seen = {norm}
        for part in _CELL_SPLIT_RE.split(norm):
            cand = _normalize(part)
            if cand and cand not in seen:
                seen.add(cand)
                candidates.append(cand)
    return candidates


def classify_data_origin(text: str | None, value_index: dict[str, dict[str, Any]] | None) -> dict[str, Any] | None:
    """Return the source reference if ``text`` resolves to a data value, else None.

    Matches the whole normalized text first, then — for a table-row delta — each cell
    / ``<br/>``-joined sub-value, so a ``| value <br/> value | label |`` row resolves
    to its source value (the cloud-doc delta granularity is a whole row, not a bare cell).
    """

    if not value_index:
        return None
    for candidate in _value_candidates(text):
        hit = value_index.get(candidate)
        if hit is not None:
            # Carry the exact matched value (a bare cell value for a table-row delta,
            # or the whole text for a body-copy/bare match) so the F6 write path can
            # extract the corresponding NEW cell value instead of writing the whole row.
            return {**hit, "matched_value": candidate}
    return None
