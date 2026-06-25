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
SPEC_MASTER_TABLE = "Spec_Master"
PAGE_PLACEHOLDERS_SOURCE_TABLE = "Page_Placeholders_Source"

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


def _page_tokens(value: str | None) -> set[str]:
    return {
        token.strip().lower()
        for token in re.split(r"[,;/]+", value or "")
        if token.strip()
    }


def _spec_origin_table(row: dict[str, str]) -> str:
    # Spec_Master.csv is the merged render snapshot. Source-side sync splits real
    # specification rows from page placeholder rows; preserve that split in source_ref
    # so F6 can write a page value back to Page_Placeholders_Source, not Spec_Master.
    tokens = _page_tokens(row.get("Page"))
    if tokens and "specifications" not in tokens:
        return PAGE_PLACEHOLDERS_SOURCE_TABLE
    return SPEC_MASTER_TABLE


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
        table = _spec_origin_table(row)
        base_ref = {
            "table": table,
            "document_key": (row.get("document_key") or "").strip(),
            "row_key": (row.get("Row_key") or "").strip(),
            "slot_key": (row.get("Slot_key") or "").strip(),
            # Fallback disambiguators for an ambiguous (document_key, Row_key, Slot_key):
            # Line_order separates a multi-line row (storage_temperature ×3); Section
            # separates a same-Line_order input-vs-output port (dc_expansion_port).
            # Carried on every ref; used only when the primary key is ambiguous
            # (see source_record_index._resolve_fallback).
            "line_order": (row.get("Line_order") or "").strip(),
            "section": (row.get("Section") or "").strip(),
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


# Cell / sub-value boundaries: a markdown pipe, a ``<br/>``, or an HTML table
# cell/row boundary tag (``<td>``, ``</tr>``, ``<table>``, ``<col/>`` …). A real
# cloud-doc SPECIFICATIONS table arrives as HTML (``<table>…<td>value</td>…``),
# not markdown pipes, so the splitter must cut on table tags too — otherwise a
# spec-cell edit is one opaque blob that never reaches the value index.
_CELL_SPLIT_RE = re.compile(
    r"<br\s*/?>|</?(?:table|thead|tbody|tfoot|tr|td|th|caption|colgroup|col)[^>]*>|\|",
    re.IGNORECASE,
)
# Any residual inline tag inside a cell is stripped so the cell text stays intact
# (``<b>Car:</b> 11 V`` -> ``Car: 11 V``).
_TAG_RE = re.compile(r"<[^>]+>")
# Only sub-split text that actually carries cell structure; a bare value or a
# prose paragraph (no pipe / ``<br/>`` / HTML table tag) is never sub-split.
_TABLE_HINT_RE = re.compile(r"\||<(?:br|table|tr|td|th)\b", re.IGNORECASE)


def split_cells(text: str | None) -> list[str]:
    """Atomic, tag-stripped, normalized cell / sub-value parts of a (possibly
    markdown- or HTML-) table text, in document order.

    Returns ``[]`` for plain text with no cell structure, so a bare value or a
    prose paragraph is never sub-split. Shared with the F6 write path
    (``source_table_sync._atomic_values``) so cell detection for *resolution* and
    for *new-value extraction* stay byte-identical.
    """

    norm = _normalize(text)
    if not norm or not _TABLE_HINT_RE.search(norm):
        return []
    parts: list[str] = []
    for raw in _CELL_SPLIT_RE.split(norm):
        cand = _normalize(_TAG_RE.sub(" ", raw))
        if cand:
            parts.append(cand)
    return parts


def _value_candidates(text: str | None) -> list[str]:
    """Atomic value candidates from a delta's normalized text.

    The whole text first (a bare value or a body-copy paragraph), then — when the
    delta carries table structure — each cell / ``<br/>``-joined / HTML ``<td>``
    sub-value. A real cloud-doc delta arrives at row/paragraph granularity (a
    markdown ``| value <br/> value | label |`` row or an HTML ``<table>`` block),
    not as a bare cell, so a contained-value match is what lets the value index
    resolve it deterministically. Feed this the **normalized** text so cells
    compare cleanly against the snapshot CSV values.
    """

    norm = _normalize(text)
    if not norm:
        return []
    candidates = [norm]
    seen = {norm}
    for cand in split_cells(norm):
        if cand not in seen:
            seen.add(cand)
            candidates.append(cand)
    return candidates


def classify_data_origin(text: str | None, value_index: dict[str, dict[str, Any]] | None) -> dict[str, Any] | None:
    """Return the source reference if ``text`` resolves to a data value, else None.

    Matches the whole normalized text first, then — for a table-row delta — each cell
    / ``<br/>``-joined sub-value, so a ``| value <br/> value | label |`` row resolves
    to its source value (the cloud-doc delta granularity is a whole row, not a bare cell).

    A value that maps to **more than one source row** is marked ``ambiguous`` by
    ``build_value_index``; that candidate is **skipped** (never resolved to an
    arbitrary slot), but a *different* uniquely-resolvable cell in the same table
    row can still match — e.g. a shared label like ``1 × AC Input`` (ambiguous
    across sibling docs) is skipped while the unique spec cell that changed
    resolves. If no candidate resolves uniquely, it abstains (returns None).
    """

    if not value_index:
        return None
    for candidate in _value_candidates(text):
        hit = value_index.get(candidate)
        if hit is None:
            continue
        if hit.get("ambiguous"):
            # This candidate value is in >1 source row — no unique slot. SKIP it and
            # keep scanning: another cell in the same table row may resolve uniquely
            # (a shared label such as "1 × AC Input" precedes the unique spec cell
            # that actually changed). The ambiguous value itself is never resolved, so
            # the "don't guess a slot" guarantee holds; and the F6 write path
            # (_resolve_written_value) abstains unless the matched cell is the one that
            # changed, so matching a unique *unchanged* cell stays safe.
            continue
        # Carry the exact matched value (a bare cell value for a table-row delta,
        # or the whole text for a body-copy/bare match) so the F6 write path can
        # extract the corresponding NEW cell value instead of writing the whole row.
        return {**hit, "matched_value": candidate}
    return None
