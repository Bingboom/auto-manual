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
    index: dict[str, dict[str, Any]] = {}
    for row in _read_csv(root / SPEC_MASTER_FILE):
        for base in _SPEC_MASTER_VALUE_BASES:
            column = f"{base}_{lang}"
            _add(
                index,
                row.get(column),
                {
                    "table": "Spec_Master",
                    "field": column,
                    "document_key": (row.get("document_key") or "").strip(),
                    "row_key": (row.get("Row_key") or "").strip(),
                    "slot_key": (row.get("Slot_key") or "").strip(),
                },
            )
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


def classify_data_origin(text: str | None, value_index: dict[str, dict[str, Any]] | None) -> dict[str, Any] | None:
    """Return the source reference if ``text`` exactly matches a data value, else None."""

    if not value_index:
        return None
    return value_index.get(_normalize(text))
