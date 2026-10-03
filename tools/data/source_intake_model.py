from __future__ import annotations

import hashlib
import json
import re
from typing import Any


CANDIDATE_SCHEMA_VERSION = "source-intake-candidates/v1"
REPORT_SCHEMA_VERSION = "source-intake-report/v1"

TARGET_SPEC_MASTER = "Spec_Master"
TARGET_PAGE_PLACEHOLDERS = "Page_Placeholders_Source"
TARGET_MANUAL_COPY = "Manual_Copy_Source"
TARGET_SPEC_FOOTNOTES = "Spec_Footnotes"
TARGET_SPEC_NOTES = "Spec_Notes"

UPDATE_CAPABLE_TABLES = frozenset(
    {
        TARGET_SPEC_MASTER,
        TARGET_PAGE_PLACEHOLDERS,
        TARGET_MANUAL_COPY,
    }
)

SPEC_TEXT_FIELDS = (
    "Row_label_source",
    "Row_label_footnote_refs",
    "Param_source",
    "Param_footnote_refs",
    "Value_source",
    "Value_footnote_refs",
)
MANUAL_COPY_TEXT_FIELDS = ("source_text", "notes")
FOOTNOTE_TEXT_FIELDS = ("Text_en", "Text_fr", "Text_es", "Text_de", "Text_it", "Text_uk", "Text_ja", "Text_pt-BR")
NOTE_TEXT_FIELDS = FOOTNOTE_TEXT_FIELDS


def normalize_space(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\r\n", "\n").replace("\r", "\n")).strip()


def candidate_hash(payload: dict[str, Any]) -> str:
    stable = {
        "target_table": payload.get("target_table"),
        "business_key": payload.get("business_key") or {},
        "fields": payload.get("fields") or {},
        "source_evidence": payload.get("source_evidence") or {},
    }
    raw = json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def delta_hash(candidate: dict[str, Any], field: str, old_value: Any, new_value: Any) -> str:
    stable = {
        "candidate_hash": candidate.get("candidate_hash"),
        "target_table": candidate.get("target_table"),
        "business_key": candidate.get("business_key") or {},
        "field": field,
        "old_value": normalize_space(old_value),
        "new_value": normalize_space(new_value),
    }
    raw = json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def compact_dict(values: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value not in (None, "", [], {})}


def page_is_specifications(value: Any) -> bool:
    tokens = {
        token.strip().casefold()
        for token in re.split(r"[,;/]+", str(value or "").replace("；", ";").replace("，", ","))
        if token.strip()
    }
    return not tokens or "specifications" in tokens or "specification" in tokens or "specs" in tokens
